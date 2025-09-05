# app.py (Flask main)
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
import jwt
from datetime import datetime, timedelta
from functools import wraps

# Import routes (ของคุณเอง)
from routes.auth import auth_bp
from routes.field_zone import field_zone_bp


app = Flask(__name__)

# ==================== CONFIG ====================
# JWT: ใช้ค่าคงที่/ENV (ห้ามสุ่มทุกครั้ง ไม่งั้น token เดิมใช้ไม่ได้หลังรีสตาร์ต)
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
JWT_EXPIRY_DAYS = 30  # Token หมดอายุใน 30 วัน

# CORS: อนุญาตทุก origin ใต้ /api/* (สำหรับ DEV)
# - อนุญาต Authorization header
# - ไม่ใช้ cookies/sessions
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    expose_headers=["Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"]
)

# Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Upload Config
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==================== JWT HELPERS ====================
def generate_token(user_data):
    """สร้าง JWT token สำหรับผู้ใช้"""
    now = datetime.utcnow()
    payload = {
        'user_id': user_data['user_id'],
        'username': user_data['username'],
        'name': user_data.get('name', ''),
        'exp': now + timedelta(days=JWT_EXPIRY_DAYS),
        'iat': now
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    logger.info(f"Token generated for user: {user_data['username']}")
    return token


def verify_token(token):
    """ตรวจสอบความถูกต้องของ JWT token"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def get_token_from_header():
    """ดึง token จาก Authorization header"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None


# ==================== AUTH DECORATOR ====================
def require_auth(f):
    """Decorator สำหรับตรวจสอบ JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # OPTIONS ไม่ต้องตรวจ auth (กันเผื่อ route ไหนหลุดมาถึงตรงนี้)
        if request.method == "OPTIONS":
            return ('', 204)

        token = get_token_from_header()
        if not token:
            return jsonify({
                'success': False,
                'error': 'missing_token',
                'message': 'Token is required'
            }), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({
                'success': False,
                'error': 'invalid_token',
                'message': 'Token is invalid or expired'
            }), 401

        # ผูกข้อมูลผู้ใช้กับ request
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated


# ==================== MIDDLEWARE ====================
@app.before_request
def before_request():
    """ทำงานก่อนทุก request"""
    # static/health/index ไม่ต้องทำอะไร
    if request.endpoint in ['static', 'health_check', 'index']:
        return

    logger.debug(f"=== REQUEST {request.method} {request.url} ===")

    # ✅ ให้ OPTIONS (preflight) ผ่านทันที ตอบ 204
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        # เพิ่มหัว CORS ให้ชัวร์
        h = resp.headers
        h['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, HEAD'
        h['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Requested-With, Accept'
        h['Access-Control-Expose-Headers'] = 'Authorization'
        # ถ้ามี Origin จาก localhost/127.0.0.1 ให้สะท้อนกลับ (dev)
        origin = request.headers.get('Origin')
        if origin and (origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:')):
            h['Access-Control-Allow-Origin'] = origin
        return resp  # 204


@app.after_request
def after_request(response):
    """ทำงานหลังจากสร้าง response แล้ว"""
    # เสริม CORS headers ให้ครบ (กันเคสเบราว์เซอร์เข้มงวด)
    origin = request.headers.get('Origin')
    if origin and (origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:')):
        response.headers['Access-Control-Allow-Origin'] = origin

    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, HEAD'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Requested-With, Accept'
    response.headers['Access-Control-Expose-Headers'] = 'Authorization'

    # ถ้าเป็น OPTIONS ให้ตอบ 204 เสมอ (ไม่มี body)
    if request.method == 'OPTIONS':
        response.status_code = 204
        response.data = b''

    return response


# ==================== BLUEPRINTS ====================
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(field_zone_bp, url_prefix='/api')



# ==================== ROUTES ====================
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK',
        'message': 'Server is running',
        'timestamp': datetime.now().isoformat(),
        'auth_type': 'JWT Token Only',
        'token_expiry_days': JWT_EXPIRY_DAYS
    })


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Cocoa Farm Management API',
        'version': '2.0.0',
        'auth_type': 'JWT Token Authentication',
        'token_expiry_days': JWT_EXPIRY_DAYS,
        'endpoints': {
            'auth': '/api/auth',
            'health': '/health',

            'fields': '/api/fields',                     
            'fieldDetail': '/api/fields/{field_id}',     
            'fieldZones': '/api/fields/{field_id}/zones',

            'zones': '/api/zones',                       
            'zoneDetail': '/api/zones/{zone_id}',       
            'marks': '/api/zones/{zone_id}/marks',      

        }

    })



@app.route('/api/test/protected', methods=['GET'])
@require_auth
def protected_test():
    """ทดสอบ endpoint ที่ต้อง JWT authentication"""
    user = request.current_user
    return jsonify({
        'success': True,
        'message': f'Hello {user["username"]}! This is a protected endpoint.',
        'user_id': user['user_id'],
        'token_expires': datetime.fromtimestamp(user['exp']).isoformat()
    })


@app.route('/routes', methods=['GET'])
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            view_func = app.view_functions.get(rule.endpoint)
            # ถ้ามีการ wrap ด้วย decorator มักจะมี __wrapped__
            protected = getattr(view_func, '__wrapped__', None) is not None
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'url': str(rule),
                'protected': protected
            })
    return jsonify({'routes': routes})


@app.route('/api/user/info', methods=['GET'])
@require_auth
def get_user_info():
    """ดึงข้อมูลผู้ใช้จาก JWT token"""
    user = request.current_user
    return jsonify({
        'success': True,
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'name': user.get('name', ''),
            'token_issued_at': datetime.fromtimestamp(user['iat']).isoformat(),
            'token_expires': datetime.fromtimestamp(user['exp']).isoformat(),
            'remaining_days': (datetime.fromtimestamp(user['exp']) - datetime.now()).days
        }
    })


# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'not_found',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'server_error',
        'message': 'Internal server error'
    }), 500


@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({
        'success': False,
        'error': 'unauthorized',
        'message': 'JWT Token required'
    }), 401


@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({
        'success': False,
        'error': 'forbidden',
        'message': 'Access denied'
    }), 403


# ==================== MAIN ====================
if __name__ == '__main__':
    logger.info("Starting Flask server with JWT-only authentication...")
    logger.info(f"JWT token expiry: {JWT_EXPIRY_DAYS} days")
    logger.info("No session management - JWT tokens only")

    app.run(
        host='127.0.0.1',  # ถ้าต้องให้ device ใน LAN เรียกได้ เปลี่ยนเป็น '0.0.0.0'
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False
    )
