# server.py
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS, cross_origin
import os, logging, jwt
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

# ===== Base routes =====
from routes.auth import auth_bp
from routes.field_zone import field_zone_bp

app = Flask(__name__)

# ==================== CONFIG ====================
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "dev-secret-key")
JWT_EXPIRY_DAYS = int(os.environ.get("JWT_EXPIRY_DAYS", "30"))
# จำกัด payload ใหญ่สุด (รวม multipart) — 20MB ตามค่าเริ่มต้น
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get("MAX_CONTENT_LENGTH_BYTES", str(20 * 1024 * 1024)))

# ===== Absolute paths =====
APP_ROOT = Path(app.root_path)

# UPLOAD_ROOT (เผยแพร่ให้ blueprint อื่นใช้)
env_upload = os.environ.get('UPLOAD_ROOT', '').strip()
UPLOAD_FOLDER = (Path(env_upload) if env_upload else (APP_ROOT / 'static' / 'uploads')).expanduser()
UPLOAD_FOLDER = UPLOAD_FOLDER.resolve(strict=False)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
os.environ['UPLOAD_ROOT'] = str(UPLOAD_FOLDER)

# Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info(f"[BOOT] UPLOAD_ROOT = {UPLOAD_FOLDER}")

# CORS
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    expose_headers=["Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
)

# ==================== OPTIONAL BLUEPRINTS ====================
inspection_bp = None
bp_detect = None
reference_bp = None

try:
    from routes.inspection import inspection_bp as _inspection_bp
    inspection_bp = _inspection_bp
    logger.info("✅ Loaded routes.inspection successfully")
except Exception as e:
    logger.error(f"❌ Failed to load routes.inspection: {e}")

try:
    from routes.detect import bp_detect as _bp_detect
    bp_detect = _bp_detect
    logger.info("✅ Loaded routes.detect successfully")
except Exception as e:
    logger.warning(f"⚠️ routes.detect not loaded: {e}")

try:
    from routes.reference import reference_bp as _reference_bp
    reference_bp = _reference_bp
    logger.info("✅ Loaded routes.reference successfully")
except Exception as e:
    logger.warning(f"⚠️ routes.reference not loaded: {e}")

# ==================== JWT HELPERS ====================
def generate_token(user_data):
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
    try:
        return jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired"); return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}"); return None

def get_token_from_header():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return ('', 204)
        token = get_token_from_header()
        if not token:
            return jsonify({'success': False, 'error': 'missing_token', 'message': 'Token is required'}), 401
        payload = verify_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'invalid_token', 'message': 'Token is invalid or expired'}), 401
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated

# ==================== MIDDLEWARE ====================
@app.before_request
def before_request():
    if request.endpoint in ['static', 'health_check', 'index', 'list_routes']:
        return
    logger.debug(f"=== REQUEST {request.method} {request.url} ===")

@app.after_request
def after_request(response):
    if request.method == 'OPTIONS':
        response.status_code = 204
        response.data = b''
    return response

# ==================== BLUEPRINTS REGISTRATION ====================
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(field_zone_bp, url_prefix='/api')

if inspection_bp is not None:
    app.register_blueprint(inspection_bp, url_prefix='/api/inspections')
    logger.info("✅ Registered inspection_bp at /api/inspections")
else:
    logger.error("❌ inspection_bp is None - routes will not be available!")

if bp_detect is not None:
    app.register_blueprint(bp_detect, url_prefix='/api/detect')
    logger.info("✅ Registered bp_detect at /api/detect")

if reference_bp is not None:
    app.register_blueprint(reference_bp, url_prefix='/api')
    logger.info("✅ Registered reference_bp at /api")

# ==================== ROUTES ====================
@app.route('/health', methods=['GET'])
@cross_origin(origins="*")
def health_check():
    return jsonify({
        'status': 'OK',
        'message': 'Server is running',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'auth_type': 'JWT Token Only',
        'token_expiry_days': JWT_EXPIRY_DAYS,
        'upload_root': str(UPLOAD_FOLDER),
        # ไม่ตรวจ/โหลดโมเดลที่นี่แล้ว — ตรวจผ่าน /api/detect/labels แทน
        'has_inspection_routes': inspection_bp is not None,
        'blueprints_loaded': {
            'inspection': inspection_bp is not None,
            'detect': bp_detect is not None,
            'reference': reference_bp is not None,
        }
    })

@app.route('/', methods=['GET'])
@cross_origin(origins="*")
def index():
    endpoints = {
        'auth': '/api/auth',
        'authLogin': '/api/auth/login',
        'authRegister': '/api/auth/register',
        'authValidate': '/api/auth/validate',
        'health': '/health',
        'fields': '/api/fields',
        'fieldDetail': '/api/fields/{field_id}',
        'fieldZones': '/api/fields/{field_id}/zones',
        'zones': '/api/zones',
        'zoneDetail': '/api/zones/{zone_id}',
        'marks': '/api/zones/{zone_id}/marks',
    }

    has_inspection = inspection_bp is not None
    if has_inspection:
        endpoints.update({
            'inspections': '/api/inspections',
            'inspectionDetail': '/api/inspections/{inspection_id}',
            'inspectionStart': '/api/inspections/start',
            'inspectionImages': '/api/inspections/{inspection_id}/images',
            'inspectionAnalyze': '/api/inspections/{inspection_id}/analyze',
            'inspectionHistory': '/api/inspections/history',
            'inspectionRecommendations': '/api/inspections/{inspection_id}/recommendations',
            'recommendationPatch': '/api/inspections/recommendations/{rec_id}',
        })

    has_detect = bp_detect is not None
    if has_detect:
        endpoints.update({
            'detect': '/api/detect',
            'detectLabels': '/api/detect/labels',  # ใช้ endpoint นี้เพื่อเช็คโมเดล
        })

    has_reference = reference_bp is not None
    if has_reference:
        endpoints.update({'nutrients': '/api/nutrients', 'fertilizers': '/api/fertilizers'})

    token_expiry_days = int(current_app.config.get('JWT_EXPIRY_DAYS', 30))

    return jsonify({
        'message': 'Cocoa Farm Management API',
        'version': '2.0.0',
        'auth_type': 'JWT Token Authentication',
        'token_expiry_days': token_expiry_days,
        'endpoints': endpoints,
        'blueprints_status': {
            'inspection': 'loaded' if has_inspection else 'not_loaded',
            'detect': 'loaded' if has_detect else 'not_loaded',
            'reference': 'loaded' if has_reference else 'not_loaded',
        },
        'notes': 'Model loading & checking are handled in /api/detect/* routes.'
    })

@app.route('/api/test/protected', methods=['GET'])
@require_auth
def protected_test():
    user = request.current_user
    return jsonify({
        'success': True,
        'message': f'Hello {user["username"]}! This is a protected endpoint.',
        'user_id': user['user_id'],
        'token_expires': datetime.fromtimestamp(user['exp']).isoformat()
    })

@app.route('/routes', methods=['GET'])
@cross_origin(origins="*")
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        view_func = app.view_functions.get(rule.endpoint)
        protected = (getattr(view_func, '__name__', '') == 'decorated')
        routes.append({
            'endpoint': rule.endpoint,
            'methods': sorted(list(rule.methods)),
            'url': str(rule),
            'protected': protected
        })
    return jsonify({'routes': routes})

@app.route('/api/user/info', methods=['GET'])
@require_auth
def get_user_info():
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
@app.errorhandler(400)
def bad_request(error): return jsonify({'success': False, 'error': 'bad_request', 'message': 'Bad request'}), 400
@app.errorhandler(401)
def unauthorized_error(error): return jsonify({'success': False, 'error': 'unauthorized', 'message': 'JWT Token required'}), 401
@app.errorhandler(403)
def forbidden_error(error): return jsonify({'success': False, 'error': 'forbidden', 'message': 'Access denied'}), 403
@app.errorhandler(404)
def not_found(error): return jsonify({'success': False, 'error': 'not_found', 'message': 'Endpoint not found'}), 404
@app.errorhandler(500)
def internal_error(error): return jsonify({'success': False, 'error': 'server_error', 'message': 'Internal server error'}), 500

# ==================== MAIN ====================
if __name__ == '__main__':
    logger.info("Starting Flask server with JWT-only authentication...")
    logger.info(f"JWT token expiry: {JWT_EXPIRY_DAYS} days")
    logger.info(f"UPLOAD_ROOT={UPLOAD_FOLDER}")

    logger.info("Blueprint status:")
    logger.info(f"  - inspection_bp: {'✅ LOADED' if inspection_bp is not None else '❌ FAILED'}")
    logger.info(f"  - bp_detect: {'✅ LOADED' if bp_detect is not None else '⚠️ NOT LOADED'}")
    logger.info(f"  - reference_bp: {'✅ LOADED' if reference_bp is not None else '⚠️ NOT LOADED'}")

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=True, threaded=True, use_reloader=False)
