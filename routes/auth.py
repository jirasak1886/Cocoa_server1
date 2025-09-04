from flask import Blueprint, request, jsonify, current_app
from mysql.connector import Error
from config.database import get_db_connection, hash_password
import jwt
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# ==================== HELPER FUNCTIONS ====================

def check_user_exists(username, user_tel):
    """ตรวจสอบว่า username หรือเบอร์โทรมีอยู่แล้วหรือไม่"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = %s OR user_tel = %s",
                         (username, user_tel))
            result = cursor.fetchone()
            return result is not None
        except Error as e:
            current_app.logger.error(f"เกิดข้อผิดพลาด: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return False

def authenticate_user(username, password):
    """ตรวจสอบการเข้าสู่ระบบ"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            hashed_password = hash_password(password)
            cursor.execute("SELECT user_id, username, name FROM users WHERE username = %s AND user_password = %s",
                         (username, hashed_password))
            result = cursor.fetchone()
            return result
        except Error as e:
            current_app.logger.error(f"เกิดข้อผิดพลาด: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return None

def register_user(username, user_tel, password, name):
    """ลงทะเบียนผู้ใช้ใหม่"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            hashed_password = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, user_tel, user_password, name)
                VALUES (%s, %s, %s, %s)
            """, (username, user_tel, hashed_password, name))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            current_app.logger.error(f"เกิดข้อผิดพลาด: {e}")
            conn.rollback()
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    return None

def generate_token(user_data):
    """สร้าง JWT token สำหรับผู้ใช้"""
    payload = {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'name': user_data.get('name', ''),
        'exp': datetime.utcnow() + timedelta(days=30),  # หมดอายุใน 30 วัน
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token

def add_cors_headers(response):
    """เพิ่ม CORS headers"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# ==================== AUTH ROUTES ====================

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """API: เข้าสู่ระบบ"""
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        return add_cors_headers(response)
    
    try:
        # รับข้อมูลจาก JSON หรือ Form
        username = None
        password = None
        
        if request.is_json:
            data = request.get_json()
            if data:
                username = data.get('username')
                password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        if not username or not password:
            response = jsonify({
                    'success': True,
                'message': 'เข้าสู่ระบบสำเร็จ',
                'token': token,  # ← ย้าย token มาที่ root level
                'user': {        # ← ย้าย user มาที่ root level
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'name': user['name']
                },
                'expires_in_days': 30,
                'data': {  # ← เก็บ data ไว้เพื่อ backward compatibility
                    'user': {
                        'user_id': user['user_id'],
                        'username': user['username'],
                        'name': user['name']
                    },
                    'token': token,
                    'expires_in_days': 30
                }
            })
            return add_cors_headers(response), 400

        # ตรวจสอบการเข้าสู่ระบบ
        user = authenticate_user(username, password)
        
        if user:
            # สร้าง JWT token
            token = generate_token(user)
            
            current_app.logger.info(f"Login successful for user: {username}")
            
            response = jsonify({
                'success': True,
                'message': 'เข้าสู่ระบบสำเร็จ', 
                'data': {
                    'user': {
                        'user_id': user['user_id'],
                        'username': user['username'],
                        'name': user['name']
                    },
                    'token': token,
                    'expires_in_days': 30
                }
            })
            return add_cors_headers(response), 200
        else:
            response = jsonify({
                'success': False, 
                'error': 'invalid_credentials',
                'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'
            })
            return add_cors_headers(response), 401
            
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        response = jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'เกิดข้อผิดพลาดในระบบ'
        })
        return add_cors_headers(response), 500

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    """API: ลงทะเบียน"""
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        return add_cors_headers(response)
    
    try:
        current_app.logger.info(f"Register request from: {request.remote_addr}")
        
        # รับข้อมูลจาก JSON หรือ Form
        username = None
        user_tel = None
        password = None
        confirm_password = None
        name = None
        
        if request.is_json:
            data = request.get_json()
            if data:
                username = data.get('username')
                user_tel = data.get('user_tel')
                password = data.get('password')
                confirm_password = data.get('confirm_password')
                name = data.get('name')
        else:
            username = request.form.get('username')
            user_tel = request.form.get('user_tel')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            name = request.form.get('name')
        
        # Validation
        if not all([username, user_tel, password, confirm_password, name]):
            response = jsonify({
                'success': False, 
                'error': 'missing_fields',
                'message': 'กรุณากรอกข้อมูลให้ครบทุกช่อง'
            })
            return add_cors_headers(response), 400
        
        # Clean input data
        username = username.strip()
        user_tel = user_tel.strip()
        name = name.strip()
        
        # Additional validation
        if len(username) < 3:
            response = jsonify({
                'success': False, 
                'error': 'username_too_short',
                'message': 'ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร'
            })
            return add_cors_headers(response), 400
        
        if len(user_tel) < 10:
            response = jsonify({
                'success': False, 
                'error': 'phone_invalid',
                'message': 'เบอร์โทรศัพท์ไม่ถูกต้อง'
            })
            return add_cors_headers(response), 400
        
        if password != confirm_password:
            response = jsonify({
                'success': False, 
                'error': 'password_mismatch',
                'message': 'รหัสผ่านไม่ตรงกัน'
            })
            return add_cors_headers(response), 400
        
        if len(password) < 6:
            response = jsonify({
                'success': False, 
                'error': 'password_too_short',
                'message': 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'
            })
            return add_cors_headers(response), 400
        
        if check_user_exists(username, user_tel):
            response = jsonify({
                'success': False, 
                'error': 'user_exists',
                'message': 'ชื่อผู้ใช้หรือเบอร์โทรศัพท์นี้มีอยู่แล้ว'
            })
            return add_cors_headers(response), 409
        
        new_user_id = register_user(username, user_tel, password, name)
        if new_user_id:
            current_app.logger.info(f"Registration successful for user: {username}")
            response = jsonify({
                'success': True, 
                'message': 'ลงทะเบียนสำเร็จ!',
                'data': {
                    'user_id': new_user_id,
                    'username': username,
                    'name': name
                }
            })
            return add_cors_headers(response), 201
        else:
            response = jsonify({
                'success': False, 
                'error': 'registration_failed',
                'message': 'เกิดข้อผิดพลาดในการลงทะเบียน'
            })
            return add_cors_headers(response), 500
    
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        response = jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'เกิดข้อผิดพลาดในระบบ'
        })
        return add_cors_headers(response), 500

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """API: ออกจากระบบ (แค่ลบ token ฝั่ง client)"""
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        return add_cors_headers(response)
    
    try:
        # สำหรับ JWT เราไม่ต้องทำอะไรฝั่งเซิร์ฟเวอร์
        # ให้ client ลบ token เอง
        current_app.logger.info("Logout request received")
        
        response = jsonify({
            'success': True, 
            'message': 'ออกจากระบบเรียบร้อยแล้ว'
        })
        return add_cors_headers(response), 200
    
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        response = jsonify({
            'success': False,
            'error': 'server_error',
            'message': 'เกิดข้อผิดพลาดในการออกจากระบบ'
        })
        return add_cors_headers(response), 500

@auth_bp.route('/validate', methods=['GET', 'OPTIONS'])
def validate_token():
    """API: ตรวจสอบ token"""
    
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        return add_cors_headers(response)
    
    try:
        # ดึง token จาก Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            response = jsonify({
                'success': False,
                'authenticated': False,
                'error': 'missing_token',
                'message': 'Token is required'
            })
            return add_cors_headers(response), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # ตรวจสอบ token
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            
            response = jsonify({
                'success': True,
                'authenticated': True,
                'user': {
                    'user_id': payload['user_id'],
                    'username': payload['username'],
                    'name': payload.get('name', '')
                },
                'token_expires': datetime.fromtimestamp(payload['exp']).isoformat()
            })
            return add_cors_headers(response), 200
            
        except jwt.ExpiredSignatureError:
            response = jsonify({
                'success': False,
                'authenticated': False,
                'error': 'token_expired',
                'message': 'Token has expired'
            })
            return add_cors_headers(response), 401
            
        except jwt.InvalidTokenError:
            response = jsonify({
                'success': False,
                'authenticated': False,
                'error': 'invalid_token',
                'message': 'Token is invalid'
            })
            return add_cors_headers(response), 401
    
    except Exception as e:
        current_app.logger.error(f"Token validation error: {e}")
        response = jsonify({
            'success': False,
            'authenticated': False,
            'error': 'server_error',
            'message': 'เกิดข้อผิดพลาดในการตรวจสอบ token'
        })
        return add_cors_headers(response), 500

# ==================== TEST ENDPOINTS ====================

@auth_bp.route('/test-token', methods=['POST', 'OPTIONS'])
def test_token():
    """ทดสอบการสร้าง token"""
    
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        return add_cors_headers(response)
    
    try:
        data = request.get_json() or {}
        username = data.get('username', 'testuser')
        
        # สร้าง test token
        test_user = {
            'user_id': 999,
            'username': username,
            'name': 'Test User'
        }
        
        token = generate_token(test_user)
        
        current_app.logger.info(f"Test token generated for: {username}")
        
        response = jsonify({
            'success': True,
            'message': f'Test token generated for {username}',
            'data': {
                'user': test_user,
                'token': token,
                'expires_in_days': 30
            }
        })
        return add_cors_headers(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Test token error: {str(e)}")
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        return add_cors_headers(response), 500