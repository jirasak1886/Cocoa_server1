from flask import Blueprint, request, jsonify, current_app
from mysql.connector import Error
from config.database import get_db_connection, hash_password
import jwt, bcrypt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# ==================== PASSWORD HELPERS ====================
def _bcrypt_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _bcrypt_check(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

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

def _get_payload():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None

def _user_exists(username=None, user_tel=None, exclude_user_id=None):
    """เช็คซ้ำ username หรือเบอร์ (ยกเว้น user_id ของตัวเองเวลาปรับปรุงโปรไฟล์)"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        clauses, params = [], []
        if username:
            clauses.append("username = %s")
            params.append(username)
        if user_tel:
            clauses.append("user_tel = %s")
            params.append(user_tel)
        if not clauses:
            return False
        sql = "SELECT user_id FROM users WHERE (" + " OR ".join(clauses) + ")"
        if exclude_user_id:
            sql += " AND user_id <> %s"
            params.append(exclude_user_id)
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
            SELECT user_id, username, name, user_tel, user_password
            FROM users WHERE username=%s
        """, (username,))
        user = cur.fetchone()
        if not user:
            return None

        db_pass = user["user_password"]

        # ✅ case 1: bcrypt
        if db_pass.startswith("$2b$") or db_pass.startswith("$2a$"):
            if _bcrypt_check(password, db_pass):
                return user
            return None

        # ✅ case 2: sha256 legacy
        if len(db_pass) == 64 and all(c in "0123456789abcdef" for c in db_pass.lower()):
            if db_pass == hash_password(password):
                # migrate เป็น bcrypt
                new_hash = _bcrypt_hash(password)
                cur.execute("UPDATE users SET user_password=%s WHERE user_id=%s", (new_hash, user["user_id"]))
                conn.commit()
                return user
            return None

        # ✅ case 3: plain legacy
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

def register_user(username, user_tel, password, name):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        hashed = _bcrypt_hash(password)  # ✅ always bcrypt
        cur.execute("""
            INSERT INTO users (username, user_tel, user_password, name)
            VALUES (%s,%s,%s,%s)
        """, (username, user_tel, hashed, name))
        conn.commit()
        return cur.lastrowid
    except Error as e:
        current_app.logger.error(f"Registration error: {e}")
        conn.rollback()
        return None
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

def generate_token(user_data):
    now = datetime.utcnow()
    payload = {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'name': user_data.get('name', ''),
        'exp': now + timedelta(days=30),
        'iat': now
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

        token = generate_token(user)
        current_app.logger.info(f"Login successful for user: {username}")
        return _add_cors(jsonify({
            'success': True,
            'message': 'เข้าสู่ระบบสำเร็จ',
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'name': user.get('name', ''),
                'user_tel': user.get('user_tel')
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
        username = (data.get('username') or '').strip()
        user_tel = (data.get('user_tel') or '').strip()
        password = (data.get('password') or '').strip()
        confirm = (data.get('confirm_password') or '').strip()
        name = (data.get('name') or '').strip()

        if not all([username, user_tel, password, confirm, name]):
            return _add_cors(jsonify({
                'success': False,
                'error': 'missing_fields',
                'message': 'กรุณากรอกข้อมูลให้ครบทุกช่อง'
            })), 400
        if len(username) < 3:
            return _add_cors(jsonify({'success': False, 'error': 'username_too_short', 'message': 'ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร'})), 400
        if len(user_tel) < 10:
            return _add_cors(jsonify({'success': False, 'error': 'phone_invalid', 'message': 'เบอร์โทรศัพท์ไม่ถูกต้อง'})), 400
        if password != confirm:
            return _add_cors(jsonify({'success': False, 'error': 'password_mismatch', 'message': 'รหัสผ่านไม่ตรงกัน'})), 400
        if len(password) < 6:
            return _add_cors(jsonify({'success': False, 'error': 'password_too_short', 'message': 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'})), 400
        if _user_exists(username=username, user_tel=user_tel):
            return _add_cors(jsonify({'success': False, 'error': 'user_exists', 'message': 'ชื่อผู้ใช้หรือเบอร์โทรศัพท์นี้มีอยู่แล้ว'})), 409

        new_id = register_user(username, user_tel, password, name)
        if not new_id:
            return _add_cors(jsonify({'success': False, 'error': 'registration_failed', 'message': 'เกิดข้อผิดพลาดในการลงทะเบียน'})), 500

        return _add_cors(jsonify({
            'success': True,
            'message': 'ลงทะเบียนสำเร็จ!',
            'data': {'user_id': new_id, 'username': username, 'name': name}
        })), 201
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        return _add_cors(jsonify({'success': False, 'error': 'server_error', 'message': 'เกิดข้อผิดพลาดในระบบ'})), 500

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return _preflight()
    return _add_cors(jsonify({'success': True, 'message': 'ออกจากระบบเรียบร้อยแล้ว'})), 200

@auth_bp.route('/validate', methods=['GET', 'OPTIONS'])
def validate():
    if request.method == 'OPTIONS':
        return _preflight()
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'missing_token', 'message': 'Token is required'})), 401
    token = auth.split(' ')[1]
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return _add_cors(jsonify({
            'success': True,
            'authenticated': True,
            'user': {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'name': payload.get('name', '')
            },
            'token_expires': datetime.fromtimestamp(payload['exp']).isoformat()
        })), 200
    except jwt.ExpiredSignatureError:
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'token_expired', 'message': 'Token has expired'})), 401
    except jwt.InvalidTokenError:
        return _add_cors(jsonify({'success': False, 'authenticated': False, 'error': 'invalid_token', 'message': 'Token is invalid'})), 401

# ---------- Profile ----------
@auth_bp.route('/profile', methods=['GET', 'PUT', 'OPTIONS'])
def profile():
    if request.method == 'OPTIONS':
        return _preflight()

    payload = _get_payload()
    if not payload:
        return _add_cors(jsonify({'success': False, 'error': 'unauthorized', 'message': 'Authentication required'})), 401

    user_id = payload['user_id']
    conn = get_db_connection()
    if not conn:
        return _add_cors(jsonify({'success': False, 'error': 'db_failed', 'message': 'Database connection failed'})), 500

    try:
        cur = conn.cursor(dictionary=True)
        if request.method == 'GET':
            cur.execute("SELECT user_id, username, name, user_tel FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                return _add_cors(jsonify({'success': False, 'error': 'not_found', 'message': 'User not found'})), 404
            return _add_cors(jsonify({'success': True, 'data': row})), 200

        # PUT: update profile
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        name = (data.get('name') or '').strip()
        user_tel = (data.get('user_tel') or '').strip()

        if not any([username, name, user_tel]):
            return _add_cors(jsonify({'success': False, 'error': 'nothing_to_update', 'message': 'ไม่มีข้อมูลสำหรับอัปเดต'})), 400

        if (username or user_tel) and _user_exists(username=username or None, user_tel=user_tel or None, exclude_user_id=user_id):
            return _add_cors(jsonify({'success': False, 'error': 'duplicate', 'message': 'ชื่อผู้ใช้หรือเบอร์โทรซ้ำกับผู้ใช้อื่น'})), 409

        fields, params = [], []
        if username:
            fields.append("username=%s"); params.append(username)
        if name:
            fields.append("name=%s"); params.append(name)
        if user_tel:
            fields.append("user_tel=%s"); params.append(user_tel)
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

    payload = _get_payload()
    if not payload:
        return _add_cors(jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Authentication required'
        })), 401

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
        if db_pass.startswith("$2b$") and _bcrypt_check(current_password, db_pass):
            valid = True
        elif len(db_pass) == 64 and db_pass == hash_password(current_password):
            valid = True
        elif current_password == db_pass:
            valid = True

        if not valid:
            return _add_cors(jsonify({'success': False, 'error': 'wrong_password', 'message': 'รหัสผ่านเดิมไม่ถูกต้อง'})), 400

        # update new password with bcrypt
        new_hash = _bcrypt_hash(new_password)
        cur.execute("UPDATE users SET user_password=%s WHERE user_id=%s", (new_hash, user_id))
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
