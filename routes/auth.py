# auth.py
from flask import Blueprint, request, jsonify, current_app
from mysql.connector import Error
from config.database import get_db_connection, hash_password
import jwt, bcrypt, re
from datetime import datetime, timedelta, timezone

auth_bp = Blueprint('auth', __name__)

# ==================== PASSWORD HELPERS ====================
def _bcrypt_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _bcrypt_check(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

# ==================== VALIDATION HELPERS ====================
_email_re = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
def _is_email(s: str) -> bool:
    return bool(_email_re.match((s or '').strip()))

# ==================== CORS HELPERS ====================
def _add_cors(resp):
    resp.headers.add('Access-Control-Allow-Origin', '*')
    resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    resp.headers.add('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
    resp.headers.add('Access-Control-Allow-Credentials', 'true')
    return resp

def _preflight():
    resp = jsonify({'status': 'OK'})
    resp.status_code = 204
    return _add_cors(resp)

def _extract_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        return auth_header[7:].strip()
    return None

def _decode_token(token: str):
    return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])

# ===== DB helpers =====
def _has_users_column(column_name: str) -> bool:
    """ตรวจว่าตาราง users มีคอลัมน์นี้หรือไม่ (กันพังเมื่อสคีมายังไม่อัปเกรด)"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SHOW COLUMNS FROM users LIKE %s", (column_name,))
        return cur.fetchone() is not None
    except Exception:
        return False
    finally:
        try:
            if conn.is_connected():
                cur.close()
                conn.close()
        except Exception:
            pass

def _user_exists(username=None, user_tel=None, user_email=None, exclude_user_id=None):
    """เช็คซ้ำ username / เบอร์ / อีเมล (ยกเว้น user_id ของตัวเองเวลาปรับโปรไฟล์)"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        clauses, params = [], []
        if username:
            clauses.append("username = %s"); params.append(username)
        if user_tel:
            clauses.append("user_tel = %s"); params.append(user_tel)
        if user_email:
            clauses.append("user_email = %s"); params.append(user_email)
        if not clauses:
            return False
        sql = "SELECT user_id FROM users WHERE (" + " OR ".join(clauses) + ")"
        if exclude_user_id:
            sql += " AND user_id <> %s"; params.append(exclude_user_id)
        cursor.execute(sql, tuple(params))
        return cursor.fetchone() is not None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ==================== AUTH CORE ====================
def authenticate_user(username, password):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT user_id, username, name, user_tel, user_email, user_password
            FROM users WHERE username=%s
        """, (username,))
        user = cur.fetchone()
        if not user:
            return None

        db_pass = user["user_password"]

        # ✅ bcrypt
        if db_pass.startswith("$2b$") or db_pass.startswith("$2a$"):
            if _bcrypt_check(password, db_pass):
                return user
            return None

        # ✅ sha256 legacy
        if len(db_pass) == 64 and all(c in "0123456789abcdef" for c in db_pass.lower()):
            if db_pass == hash_password(password):
                new_hash = _bcrypt_hash(password)
                cur.execute("UPDATE users SET user_password=%s WHERE user_id=%s", (new_hash, user["user_id"]))
                conn.commit()
                return user
            return None

        # ✅ plain legacy
        if password == db_pass:
            new_hash = _bcrypt_hash(password)
            cur.execute("UPDATE users SET user_password=%s WHERE user_id=%s", (new_hash, user["user_id"]))
            conn.commit()
            return user

        return None
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def register_user(username, user_tel, user_email, password, name):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        hashed = _bcrypt_hash(password)  # ✅ always bcrypt
        if _has_users_column('user_email'):
            cur.execute("""
                INSERT INTO users (username, user_tel, user_email, user_password, name)
                VALUES (%s,%s,%s,%s,%s)
            """, (username, user_tel, user_email, hashed, name))
        else:
            cur.execute("""
                INSERT INTO users (username, user_tel, user_password, name)
                VALUES (%s,%s,%s,%s)
            """, (username, user_tel, hashed, name))
        conn.commit()
        return cur.lastrowid
    except Error as e:
        current_app.logger.error(f"Registration error: {e}")
        try: conn.rollback()
        except Exception: pass
        return None
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def generate_token(user_data):
    # ✅ ใช้ UTC + epoch int เท่านั้น เพื่อเลี่ยงปัญหา naive/aware
    now = datetime.now(timezone.utc)
    payload = {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'name': user_data.get('name', ''),
        'user_tel': user_data.get('user_tel', ''),
        'user_email': user_data.get('user_email', ''),
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(days=30)).timestamp()),
        # 👉 ถ้าคุณอยากกัน revoke แบบเวอร์ชัน ให้ใส่ 'pwd_v' ด้วย (ดูคอมเมนต์ด้านล่างใน /validate)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

# ==================== ROUTES ====================
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return _preflight()
    try:
        data = request.get_json(silent=True) or request.form
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()

        if not username or not password:
            return _add_cors(jsonify({
                'success': False,
                'error': 'missing_fields',
                'message': 'กรุณากรอกชื่อผู้ใช้และรหัสผ่าน'
            })), 400

        user = authenticate_user(username, password)
        if not user:
            return _add_cors(jsonify({
                'success': False,
                'error': 'invalid_credentials',
                'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'
            })), 401

        # ✅ ออก token หลังจาก validate สำเร็จ (ไม่มีการอัปเดตเวลาที่ทำให้เทียบ iat/changed_at เพี้ยน)
        token = generate_token(user)
        current_app.logger.info(f"Login successful for user: {username}")
        return _add_cors(jsonify({
            'success': True,
            'message': 'เข้าสู่ระบบสำเร็จ',
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'name': user.get('name', ''),
                'user_tel': user.get('user_tel'),
                'user_email': user.get('user_email')
            },
            'token': token,
            'expires_in_days': 30
        })), 200
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return _add_cors(jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'เกิดข้อผิดพลาดในระบบ'
        })), 500

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return _preflight()
    try:
        data = request.get_json(silent=True) or request.form
        username    = (data.get('username') or '').strip()
        user_tel    = (data.get('user_tel') or '').strip()
        user_email  = (data.get('user_email') or '').strip().lower()
        password    = (data.get('password') or '').strip()
        confirm     = (data.get('confirm_password') or '').strip()
        name        = (data.get('name') or '').strip()

        # --- validate ---
        if not all([username, user_tel, password, confirm, name, user_email]):
            return _add_cors(jsonify({
                'success': False,
                'error': 'missing_fields',
                'message': 'กรุณากรอกข้อมูลให้ครบทุกช่อง'
            })), 400
        if len(username) < 3:
            return _add_cors(jsonify({'success': False, 'error': 'username_too_short', 'message': 'ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร'})), 400
        if len(user_tel) < 10:
            return _add_cors(jsonify({'success': False, 'error': 'phone_invalid', 'message': 'เบอร์โทรศัพท์ไม่ถูกต้อง'})), 400
        if not _is_email(user_email):
            return _add_cors(jsonify({'success': False, 'error': 'email_invalid', 'message': 'อีเมลไม่ถูกต้อง'})), 400
        if password != confirm:
            return _add_cors(jsonify({'success': False, 'error': 'password_mismatch', 'message': 'รหัสผ่านไม่ตรงกัน'})), 400
        if len(password) < 6:
            return _add_cors(jsonify({'success': False, 'error': 'password_too_short', 'message': 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'})), 400
        if _user_exists(username=username, user_tel=user_tel, user_email=user_email):
            return _add_cors(jsonify({'success': False, 'error': 'user_exists', 'message': 'ชื่อผู้ใช้/เบอร์โทร/อีเมล นี้มีอยู่แล้ว'})), 409

        new_id = register_user(username, user_tel, user_email, password, name)
        if not new_id:
            return _add_cors(jsonify({'success': False, 'error': 'registration_failed', 'message': 'เกิดข้อผิดพลาดในการลงทะเบียน'})), 500

        return _add_cors(jsonify({
            'success': True,
            'message': 'ลงทะเบียนสำเร็จ!',
            'data': {'user_id': new_id, 'username': username, 'name': name, 'user_email': user_email}
        })), 201
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return _add_cors(jsonify({'success': False, 'error': 'server_error', 'message': 'เกิดข้อผิดพลาดในระบบ'})), 500

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return _preflight()
    return _add_cors(jsonify({'success': True, 'message': 'ออกจากระบบเรียบร้อยแล้ว'})), 200

# ==================== VALIDATE (FIXED TZ + EPOCH) ====================
@auth_bp.route('/validate', methods=['GET', 'OPTIONS'])
def validate():
    if request.method == 'OPTIONS':
        return _preflight()

    token = _extract_bearer_token()
    if not token:
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'missing_token', 'message': 'Token is required'})), 401

    try:
        payload = _decode_token(token)
    except jwt.ExpiredSignatureError:
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'token_expired', 'message': 'Token has expired'})), 401
    except jwt.InvalidTokenError:
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'invalid_token', 'message': 'Token is invalid'})), 401

    # ✅ iat/exp เป็น epoch int เสมอ
    token_exp = payload.get('exp')
    token_iat = payload.get('iat')
    try:
        token_exp_dt = datetime.fromtimestamp(int(token_exp), tz=timezone.utc) if token_exp else None
        token_iat_dt = datetime.fromtimestamp(int(token_iat), tz=timezone.utc) if token_iat else None
    except Exception:
        token_exp_dt, token_iat_dt = None, None

    # 🔒 revoke token หากมีการเปลี่ยนรหัสหลังออก token นี้ (เทียบเป็น UTC เท่านั้น)
    conn = get_db_connection()
    if not conn:
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'db_failed', 'message': 'Database connection failed'})), 500

    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        has_pwd_col = _has_users_column('password_changed_at')

        if has_pwd_col:
            # ✅ แปลงเวลาใน SQL ให้เป็น UTC เลย
            cur.execute("""
                SELECT user_id, username, name, user_tel, user_email,
                       CONVERT_TZ(password_changed_at, @@session.time_zone, '+00:00') AS password_changed_at_utc
                FROM users
                WHERE user_id = %s
                LIMIT 1
            """, (payload['user_id'],))
        else:
            cur.execute("""
                SELECT user_id, username, name, user_tel, user_email, NULL AS password_changed_at_utc
                FROM users
                WHERE user_id = %s
                LIMIT 1
            """, (payload['user_id'],))

        row = cur.fetchone()
        if not row:
            return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'not_found', 'message': 'User not found'})), 404

        # --- Password revoke check (UTC vs UTC) ---
        pwd_changed_utc = row.get('password_changed_at_utc')  # type: datetime or None
        if pwd_changed_utc and token_iat_dt:
            # หมายเหตุ: ค่าที่ออกจาก MySQL โดยปกติเป็น naive -> CONVERT_TZ ให้เป็น UTC แล้ว MySQL จะส่งออกมาเป็น datetime "naive"
            # เราจะ treat ว่าเป็น UTC เสมอ:
            pwd_changed_dt = pwd_changed_utc.replace(tzinfo=timezone.utc)
            if pwd_changed_dt > token_iat_dt:
                return _add_cors(jsonify({
                    'success': False, 'authenticated': False,
                    'error': 'token_revoked',
                    'message': 'Password changed; please login again'
                })), 401

        # 👉 ทางเลือกที่แข็งแรงกว่า: ใช้ pwd_version (ดูคอมเมนต์)
        # if 'pwd_v' in payload:
        #     cur.execute("SELECT pwd_version FROM users WHERE user_id=%s", (payload['user_id'],))
        #     vrow = cur.fetchone()
        #     if vrow and int(payload['pwd_v']) != int(vrow['pwd_version'] or 0):
        #         return _add_cors(jsonify({'success': False,'authenticated': False,'error': 'token_revoked'})), 401

        return _add_cors(jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'user_id': row['user_id'],
                'username': row['username'],
                'name': row.get('name', '') or '',
                'user_tel': row.get('user_tel') or '',
                'user_email': row.get('user_email') or ''
            },
            'token_expires': token_exp_dt.isoformat() if token_exp_dt else None
        })), 200

    except Error as e:
        current_app.logger.error(f"/validate DB error: {e}")
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'db_error', 'message': str(e)})), 500
    except Exception as e:
        current_app.logger.exception(f"/validate unexpected error: {e}")
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'server_error', 'message': 'Internal server error'})), 500
    finally:
        try:
            if cur: cur.close()
        except Exception:
            pass
        try:
            if conn and conn.is_connected(): conn.close()
        except Exception:
            pass

# ---------- Profile ----------
@auth_bp.route('/profile', methods=['GET', 'PUT', 'OPTIONS'])
def profile():
    if request.method == 'OPTIONS':
        return _preflight()

    token = _extract_bearer_token()
    if not token:
        return _add_cors(jsonify({'success': False, 'error': 'unauthorized', 'message': 'Authentication required'})), 401
    try:
        payload = _decode_token(token)
    except Exception:
        return _add_cors(jsonify({'success': False, 'error': 'invalid_token', 'message': 'Token invalid'})), 401

    user_id = payload['user_id']
    conn = get_db_connection()
    if not conn:
        return _add_cors(jsonify({'success': False, 'error': 'db_failed', 'message': 'Database connection failed'})), 500

    try:
        cur = conn.cursor(dictionary=True)
        if request.method == 'GET':
            cur.execute("SELECT user_id, username, name, user_tel, user_email FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return _add_cors(jsonify({'success': False, 'error': 'not_found', 'message': 'User not found'})), 404
            return _add_cors(jsonify({'success': True, 'data': row})), 200

        # PUT: update profile
        data = request.get_json(silent=True) or {}
        username   = (data.get('username') or '').strip()
        name       = (data.get('name') or '').strip()
        user_tel   = (data.get('user_tel') or '').strip()
        user_email = (data.get('user_email') or '').strip().lower()

        if not any([username, name, user_tel, user_email]):
            return _add_cors(jsonify({'success': False, 'error': 'nothing_to_update', 'message': 'ไม่มีข้อมูลสำหรับอัปเดต'})), 400

        if user_email and not _is_email(user_email):
            return _add_cors(jsonify({'success': False, 'error': 'email_invalid', 'message': 'อีเมลไม่ถูกต้อง'})), 400

        if (username or user_tel or user_email) and _user_exists(
            username=username or None,
            user_tel=user_tel or None,
            user_email=user_email or None,
            exclude_user_id=user_id
        ):
            return _add_cors(jsonify({'success': False, 'error': 'duplicate', 'message': 'ชื่อผู้ใช้/เบอร์โทร/อีเมล ซ้ำกับผู้ใช้อื่น'})), 409

        fields, params = [], []
        if username:
            fields.append("username=%s"); params.append(username)
        if name:
            fields.append("name=%s"); params.append(name)
        if user_tel:
            fields.append("user_tel=%s"); params.append(user_tel)
        if user_email and _has_users_column('user_email'):
            fields.append("user_email=%s"); params.append(user_email)
        params.append(user_id)

        sql = "UPDATE users SET " + ", ".join(fields) + " WHERE user_id = %s"
        cur.execute(sql, tuple(params))
        conn.commit()
        return _add_cors(jsonify({'success': True, 'message': 'อัปเดตโปรไฟล์สำเร็จ'})), 200
    except Error as e:
        conn.rollback()
        current_app.logger.error(f"Profile update error: {e}")
        return _add_cors(jsonify({'success': False, 'error': 'db_error', 'message': str(e)})), 500
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

# ---------- Change Password ----------
@auth_bp.route('/profile/password', methods=['PUT', 'OPTIONS'])
@auth_bp.route('/change-password', methods=['PUT', 'OPTIONS'])
def change_password():
    if request.method == 'OPTIONS':
        return _preflight()

    token = _extract_bearer_token()
    if not token:
        return _add_cors(jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Authentication required'
        })), 401
    try:
        payload = _decode_token(token)
    except Exception:
        return _add_cors(jsonify({'success': False, 'error': 'invalid_token', 'message': 'Token invalid'})), 401

    data = (request.get_json(silent=True) or request.form or {})
    current_password = (data.get('current_password') or data.get('old_password') or '').strip()
    new_password     = (data.get('new_password') or data.get('password') or '').strip()
    confirm_password = (data.get('confirm_password') or data.get('password_confirmation') or new_password).strip()

    if not current_password or not new_password:
        return _add_cors(jsonify({'success': False, 'error': 'missing_fields', 'message': 'กรุณากรอกข้อมูลให้ครบ'})), 400
    if new_password != confirm_password:
        return _add_cors(jsonify({'success': False, 'error': 'password_mismatch', 'message': 'รหัสผ่านใหม่ไม่ตรงกัน'})), 400
    if len(new_password) < 6:
        return _add_cors(jsonify({'success': False, 'error': 'password_too_short', 'message': 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'})), 400

    user_id = payload['user_id']
    conn = get_db_connection()
    if not conn:
        return _add_cors(jsonify({'success': False, 'error': 'db_failed', 'message': 'Database connection failed'})), 500

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT user_password FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        if not row:
            return _add_cors(jsonify({'success': False, 'error': 'not_found', 'message': 'User not found'})), 404

        db_pass = row["user_password"]

        # verify old password (bcrypt + legacy)
        valid = False
        if (db_pass.startswith("$2b$") or db_pass.startswith("$2a$")) and _bcrypt_check(current_password, db_pass):
            valid = True
        elif len(db_pass) == 64 and db_pass == hash_password(current_password):
            valid = True
        elif current_password == db_pass:
            valid = True

        if not valid:
            return _add_cors(jsonify({'success': False, 'error': 'wrong_password', 'message': 'รหัสผ่านเดิมไม่ถูกต้อง'})), 400

        # update new password with bcrypt + บันทึกเวลาที่เปลี่ยนเป็น UTC
        new_hash = _bcrypt_hash(new_password)
        has_pwd_col = _has_users_column('password_changed_at')

        if has_pwd_col:
            cur.execute("""
                UPDATE users
                SET user_password=%s, password_changed_at=UTC_TIMESTAMP()
                WHERE user_id=%s
            """, (new_hash, user_id))
        else:
            cur.execute("""
                UPDATE users
                SET user_password=%s
                WHERE user_id=%s
            """, (new_hash, user_id))

        # 👉 ถ้าใช้ pwd_version:
        # cur.execute("UPDATE users SET user_password=%s, pwd_version=COALESCE(pwd_version,0)+1 WHERE user_id=%s", (new_hash, user_id))

        conn.commit()
        return _add_cors(jsonify({'success': True, 'message': 'เปลี่ยนรหัสผ่านสำเร็จ'})), 200
    except Error as e:
        conn.rollback()
        current_app.logger.error(f"Change password error: {e}")
        return _add_cors(jsonify({'success': False, 'error': 'db_error', 'message': str(e)})), 500
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()
