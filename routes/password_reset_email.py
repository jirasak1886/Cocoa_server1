# routes/password_reset_email.py
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, timezone
from mysql.connector import Error
from config.database import get_db_connection
from services.emailer import send_email
from utils.security_reset import gen_otp, hash_token
import os, jwt, bcrypt

password_reset_email_bp = Blueprint('password_reset_email', __name__)

# ====== CONFIG ======
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
OTP_TTL_MINUTES = int(os.environ.get("RESET_OTP_TTL_MINUTES", "10"))
TEMP_JWT_TTL_MINUTES = int(os.environ.get("RESET_TEMP_JWT_TTL_MINUTES", "15"))
RESET_CHANNEL = "email"

# ====== CORS helper ======
def _add_cors(resp):
    try:
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        resp.headers.add('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
        resp.headers.add('Access-Control-Allow-Credentials', 'true')
    except Exception:
        pass
    return resp

def _no_content():
    from flask import make_response
    resp = make_response('', 204)
    return _add_cors(resp)

# ====== Temp JWT helpers ======
def _issue_temp_jwt(payload: dict, minutes: int = TEMP_JWT_TTL_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=minutes)
    # เก็บ iat/exp เป็น epoch sec เพื่ออ่านง่ายทุกภาษา
    body = {
        **payload,
        'iat': int(now.timestamp()),
        'exp': int(exp.timestamp()),
        'typ': 'reset',
    }
    token = jwt.encode(body, JWT_SECRET, algorithm='HS256')
    current_app.logger.info(f"[RESET] Issued temp JWT (typ=reset) exp in {minutes}m")
    return token

def _verify_temp_jwt(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        if payload.get('typ') != 'reset':
            current_app.logger.warning("[RESET] Temp JWT typ != 'reset'")
            return None
        return payload
    except jwt.ExpiredSignatureError:
        current_app.logger.warning("[RESET] Temp JWT expired")
        return None
    except jwt.InvalidSignatureError:
        current_app.logger.warning("[RESET] Temp JWT invalid signature (secret mismatch?)")
        return None
    except jwt.InvalidTokenError as e:
        current_app.logger.warning(f"[RESET] Temp JWT invalid: {e}")
        return None
    except Exception as e:
        current_app.logger.warning(f"[RESET] Temp JWT decode error: {e}")
        return None

# ====== Endpoints ======

@password_reset_email_bp.route('/api/auth/request-password-reset', methods=['POST', 'OPTIONS'])
def request_password_reset():
    # Preflight
    if request.method == 'OPTIONS':
        return _no_content()

    data = request.get_json(silent=True) or request.form or {}
    identifier = (data.get('identifier') or '').strip().lower()

    if not identifier:
        return _add_cors(jsonify({'ok': False, 'message': 'missing identifier'})), 400

    # หา user จากอีเมล (ถ้าอยากรองรับ username ด้วย เพิ่มเงื่อนไข OR)
    sql = "SELECT user_id, user_email FROM users WHERE user_email = %s LIMIT 1"
    user = None
    try:
        conn = get_db_connection()
        if not conn:
            # ไม่บอก attacker ว่า DB ล่ม — ตอบ ok เสมอ
            current_app.logger.error("[RESET] DB connection failed (request)")
            return _add_cors(jsonify({'ok': True}))
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (identifier,))
        user = cur.fetchone()
    except Error as e:
        current_app.logger.error(f"[RESET] lookup user error: {e}")
        user = None
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

    # ป้องกัน account enumeration → ตอบ ok เสมอ
    if not user:
        current_app.logger.info("[RESET] request for unknown email -> respond ok")
        return _add_cors(jsonify({'ok': True}))

    # สร้าง OTP และแฮชเก็บใน DB
    otp = gen_otp()  # เช่น 6 หลัก
    tok_hash = hash_token(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)

    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(
            "INSERT INTO password_reset_tokens (user_id, token_hash, channel, destination, expires_at) "
            "VALUES (%s,%s,%s,%s,%s)",
            (user['user_id'], tok_hash, RESET_CHANNEL, user['user_email'], expires_at)
        )
        conn.commit()
        current_app.logger.info(f"[RESET] OTP issued for user_id={user['user_id']} exp={expires_at} UTC")
    except Error as e:
        current_app.logger.error(f"[RESET] insert token error: {e}")
        try: conn.rollback()
        except Exception: pass
    finally:
        try: cur.close(); conn.close()
        except Exception: pass

    # ส่งอีเมล (กลืน error)
    try:
        subject = "Cocoa App - รหัสยืนยันรีเซ็ตรหัสผ่าน"
        body = (
            f"รหัสยืนยัน (OTP): {otp}\n"
            f"หมดอายุใน {OTP_TTL_MINUTES} นาที\n\n"
            f"หากไม่ได้เป็นคนขอ ให้เพิกเฉยอีเมลนี้"
        )
        send_email(user['user_email'], subject, body)
        current_app.logger.info(f"[RESET] OTP emailed to {user['user_email']}")
    except Exception as e:
        current_app.logger.warning(f"[RESET] send email failed (swallowed): {e}")

    return _add_cors(jsonify({'ok': True}))

@password_reset_email_bp.route('/api/auth/verify-reset', methods=['POST', 'OPTIONS'])
def verify_reset():
    if request.method == 'OPTIONS':
        return _no_content()

    data = request.get_json(silent=True) or request.form or {}
    identifier = (data.get('identifier') or '').strip().lower()
    otp = (data.get('otp') or '').strip()

    if not identifier or not otp:
        return _add_cors(jsonify({'ok': False, 'message': 'missing fields'})), 400

    # หา user
    sql_user = "SELECT user_id FROM users WHERE user_email = %s LIMIT 1"
    user = None
    try:
        conn = get_db_connection(); cur = conn.cursor(dictionary=True)
        cur.execute(sql_user, (identifier,))
        user = cur.fetchone()
    except Error as e:
        current_app.logger.error(f"[RESET] verify: user lookup error: {e}")
        user = None
    finally:
        try: cur.close(); conn.close()
        except Exception: pass

    if not user:
        # ตอบผิดรวม ๆ
        return _add_cors(jsonify({'ok': False, 'message': 'invalid'})), 400

    tok_hash = hash_token(otp)
    now = datetime.utcnow()
    sql_token = (
        "SELECT id, expires_at, attempts FROM password_reset_tokens "
        "WHERE user_id=%s AND token_hash=%s AND used_at IS NULL "
        "ORDER BY created_at DESC LIMIT 1"
    )
    try:
        conn = get_db_connection(); cur = conn.cursor(dictionary=True)
        cur.execute(sql_token, (user['user_id'], tok_hash))
        token_row = cur.fetchone()
        if not token_row:
            current_app.logger.info("[RESET] verify: token not found")
            return _add_cors(jsonify({'ok': False, 'message': 'invalid_or_expired'})), 400

        if token_row['expires_at'] < now:
            current_app.logger.info("[RESET] verify: token expired")
            cur.execute("UPDATE password_reset_tokens SET attempts=attempts+1 WHERE id=%s", (token_row['id'],))
            conn.commit()
            return _add_cors(jsonify({'ok': False, 'message': 'invalid_or_expired'})), 400

        # mark used
        cur.execute("UPDATE password_reset_tokens SET used_at=%s WHERE id=%s", (now, token_row['id']))
        conn.commit()
        current_app.logger.info(f"[RESET] OTP verified for user_id={user['user_id']}")
    except Error as e:
        current_app.logger.error(f"[RESET] verify DB error: {e}")
        return _add_cors(jsonify({'ok': False, 'message': 'server_error'})), 500
    finally:
        try: cur.close(); conn.close()
        except Exception: pass

    temp_token = _issue_temp_jwt({'user_id': user['user_id']}, minutes=TEMP_JWT_TTL_MINUTES)
    return _add_cors(jsonify({'ok': True, 'temp_token': temp_token}))

@password_reset_email_bp.route('/api/auth/reset-password', methods=['POST', 'OPTIONS'])
def reset_password():
    if request.method == 'OPTIONS':
        return _no_content()

    # --- ตรวจ header ---
    auth_header = request.headers.get('Authorization', '')
    current_app.logger.debug(f"[RESET] Authorization header preview: {auth_header[:32]}...")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return _add_cors(jsonify({'ok': False, 'message': 'missing auth'})), 401

    payload = _verify_temp_jwt(parts[1])
    if not payload or not payload.get('user_id'):
        return _add_cors(jsonify({'ok': False, 'message': 'invalid token'})), 401

    # --- ข้อมูล input ---
    data = request.get_json(silent=True) or request.form or {}
    new_password = (data.get('new_password') or '').strip()
    if len(new_password) < 8:
        return _add_cors(jsonify({'ok': False, 'message': 'weak_password'})), 400

    # --- hash & อัปเดต ---
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    try:
        conn = get_db_connection(); cur = conn.cursor()
        # อัปเดตรหัสผ่าน
        cur.execute("UPDATE users SET user_password=%s, password_changed_at=NOW() WHERE user_id=%s", (hashed, payload['user_id']))
        # ทำให้โทเค็น reset ที่ยังไม่ใช้ “หมดอายุ/ปิดใช้งาน”
        cur.execute(
            "UPDATE password_reset_tokens SET used_at=%s WHERE user_id=%s AND used_at IS NULL",
            (datetime.utcnow(), payload['user_id'])
        )
        conn.commit()
        current_app.logger.info(f"[RESET] Password changed for user_id={payload['user_id']}")
    except Error as e:
        try: conn.rollback()
        except Exception: pass
        current_app.logger.error(f"[RESET] update password error: {e}")
        return _add_cors(jsonify({'ok': False, 'message': 'server_error'})), 500
    finally:
        try: cur.close(); conn.close()
        except Exception: pass

    return _add_cors(jsonify({'ok': True}))
