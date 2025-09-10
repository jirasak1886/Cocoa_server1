# server.py
from flask import Flask, jsonify, request
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
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get("MAX_CONTENT_LENGTH_BYTES", str(20 * 1024 * 1024)))

# ===== Absolute paths (robust) =====
APP_ROOT = Path(app.root_path)

# UPLOAD_ROOT
env_upload = os.environ.get('UPLOAD_ROOT', '').strip()
UPLOAD_FOLDER = (Path(env_upload) if env_upload else (APP_ROOT / 'static' / 'uploads')).expanduser()
UPLOAD_FOLDER = UPLOAD_FOLDER.resolve(strict=False)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# MODEL_PATH — รองรับหลาย candidate (รวม best (1).pt)
candidates = [
    os.environ.get('MODEL_PATH', '').strip(),      # ENV มาก่อน
    str(APP_ROOT / 'model' / 'best (1).pt'),       # ชื่อไฟล์ของคุณ
    str(APP_ROOT / 'model' / 'best.pt'),           # สำรองชื่อมาตรฐาน
]
MODEL_PATH_ABS = None
for c in candidates:
    if not c:
        continue
    p = Path(c).expanduser().resolve(strict=False)
    if p.is_file():
        MODEL_PATH_ABS = p
        break
if MODEL_PATH_ABS is None:
    MODEL_PATH_ABS = (APP_ROOT / 'model' / 'best (1).pt').expanduser().resolve(strict=False)

# เผยแพร่ให้ blueprint ใช้
os.environ['UPLOAD_ROOT'] = str(UPLOAD_FOLDER)
os.environ['MODEL_PATH']  = str(MODEL_PATH_ABS)

# Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
if MODEL_PATH_ABS.is_file():
    logger.info(f"[BOOT] MODEL_PATH OK: {MODEL_PATH_ABS}")
else:
    logger.error(f"[BOOT] MODEL_PATH not found: {MODEL_PATH_ABS}")

# CORS: เปิดทุกเส้นทาง
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    expose_headers=["Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]  # Added PATCH
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
    logger.error("Make sure routes/inspection.py exists and has no syntax errors")

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
    from functools import wraps
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
    if request.endpoint in ['static', 'health_check', 'health_model', 'index', 'list_routes']:
        return
    logger.debug(f"=== REQUEST {request.method} {request.url} ===")

@app.after_request
def after_request(response):
    if request.method == 'OPTIONS':
        response.status_code = 204
        response.data = b''
    return response

# ==================== BLUEPRINTS REGISTRATION ====================
# Always register base blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(field_zone_bp, url_prefix='/api')

# Register optional blueprints with proper error handling
if inspection_bp is not None:
    app.register_blueprint(inspection_bp, url_prefix='/api/inspections')
    logger.info("✅ Registered inspection_bp at /api/inspections")
else:
    logger.error("❌ inspection_bp is None - routes will not be available!")
    logger.error("Check routes/inspection.py for import errors")

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
        'model_path': str(MODEL_PATH_ABS),
        'has_inspection_routes': inspection_bp is not None,
        'blueprints_loaded': {
            'inspection': inspection_bp is not None,
            'detect': bp_detect is not None,
            'reference': reference_bp is not None,
        }
    })

@app.route('/health/model', methods=['GET'])
@cross_origin(origins="*")
def health_model():
    try:
        from ultralytics import YOLO
        m = YOLO(str(MODEL_PATH_ABS))
        names = getattr(m, 'names', None)
        device = os.environ.get('YOLO_DEVICE', 'auto')
        return jsonify({
            'success': True,
            'model_loaded': True,
            'model_path': str(MODEL_PATH_ABS),
            'num_classes': len(names) if isinstance(names, dict) else None,
            'device': device
        })
    except Exception as e:
        return jsonify({'success': False, 'model_loaded': False, 'error': str(e), 'model_path': str(MODEL_PATH_ABS)}), 500

@app.route('/', methods=['GET'])
@cross_origin(origins="*")
def index():
    endpoints = {
        'auth': '/api/auth',
        'authLogin': '/api/auth/login',
        'authRegister': '/api/auth/register',
        'authValidate': '/api/auth/validate',

        'health': '/health',
        # ใส่ healthModel ก็ต่อเมื่อคุณมี route จริงเท่านั้น
        'healthModel': '/health/model',

        'fields': '/api/fields',
        'fieldDetail': '/api/fields/{field_id}',
        'fieldZones': '/api/fields/{field_id}/zones',

        'zones': '/api/zones',
        'zoneDetail': '/api/zones/{zone_id}',

        'marks': '/api/zones/{zone_id}/marks',
    }

    # แสดงปลายทางของ inspections ถ้ามีโหลด blueprint แล้วจริง
    try:
        has_inspection = inspection_bp is not None  # ต้องมีตัวแปรนี้ในสโคปไฟล์ server.py
    except NameError:
        has_inspection = False

    if has_inspection:
        endpoints.update({
            # core list/detail
            'inspections': '/api/inspections',
            'inspectionDetail': '/api/inspections/{inspection_id}',

            # start / images / analyze (ใช้โดยแอป)
            'inspectionStart': '/api/inspections/start',
            'inspectionImages': '/api/inspections/{inspection_id}/images',
            'inspectionAnalyze': '/api/inspections/{inspection_id}/analyze',

            # history + recommendations
            'inspectionHistory': '/api/inspections/history',
            'inspectionRecommendations': '/api/inspections/{inspection_id}/recommendations',
            'recommendationPatch': '/api/inspections/recommendations/{rec_id}',
        })

    # detect (โมดูลโมเดล)
    try:
        has_detect = bp_detect is not None
    except NameError:
        has_detect = False

    if has_detect:
        endpoints.update({
            'detect': '/api/detect',
            'detectLabels': '/api/detect/labels',
        })

    # reference (พวก nutrients/fertilizers)
    try:
        has_reference = reference_bp is not None
    except NameError:
        has_reference = False

    if has_reference:
        endpoints.update({
            'nutrients': '/api/nutrients',
            'fertilizers': '/api/fertilizers',
        })

    # อ่านวันหมดอายุ token จาก config (fallback = 30)
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
    logger.info(f"MODEL_PATH={MODEL_PATH_ABS}")
    
    # Log blueprint registration status
    logger.info(f"Blueprint status:")
    logger.info(f"  - inspection_bp: {'✅ LOADED' if inspection_bp is not None else '❌ FAILED'}")
    logger.info(f"  - bp_detect: {'✅ LOADED' if bp_detect is not None else '⚠️ NOT LOADED'}")
    logger.info(f"  - reference_bp: {'✅ LOADED' if reference_bp is not None else '⚠️ NOT LOADED'}")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=True, threaded=True, use_reloader=False)