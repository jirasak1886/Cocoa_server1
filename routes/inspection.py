# routes/inspection.py
from flask import Blueprint, request, jsonify, current_app
from config.database import get_db_connection
from mysql.connector import Error
from datetime import datetime, date, timedelta
from pathlib import Path
import jwt, os, json

from routes.detect import predict_on_paths  # ใช้โมเดลจาก detect.py

inspection_bp = Blueprint('inspection', __name__)

STATUS_OPEN = 'pending'
STATUS_DONE = 'completed'

ALLOWED_EXTS = {'jpg', 'jpeg', 'png', 'bmp', 'webp'}
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_IMAGES_PER_ROUND = 5

# ---------- helpers (auth / io) ----------
def _get_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ')[1]
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None

def _user_id(u):
    if not isinstance(u, dict):
        return None
    return u.get('user_id') or u.get('sub') or u.get('uid')

def _authz():
    if request.method == 'OPTIONS':
        return None, ('', 204)
    u = _get_user()
    if not u:
        return None, (jsonify({'success': False,'error': 'unauthorized','message': 'Authentication required'}), 401)
    return u, None

def _ensure_json():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return {}

def _parse_yyyy_mm_dd(s):
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        return None

def _normalize_range(dfrom_str, dto_str):
    start_dt = end_dt = None
    dfrom = _parse_yyyy_mm_dd(dfrom_str) if dfrom_str else None
    dto   = _parse_yyyy_mm_dd(dto_str)   if dto_str else None
    if dfrom:
        start_dt = datetime.combine(dfrom, datetime.min.time())
    if dto:
        end_dt = datetime.combine(dto + timedelta(days=1), datetime.min.time()) - timedelta(seconds=1)
    return start_dt, end_dt

def _uploads_root() -> Path:
    env_root = os.environ.get('UPLOAD_ROOT', '').strip()
    if env_root:
        return Path(env_root)
    return Path(current_app.root_path) / 'static' / 'uploads'

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def _ext_ok(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTS

# ---------- NORMALIZE / WHITELIST สำหรับผลโมเดล ----------
# เจอ "nomal" หรือ "normal" หรือ "healthy" ให้ถือว่า "ปกติ" → ไม่ INSERT finding
NORMAL_TOKENS = {"normal", "nomal", "healthy", "none"}
CODE_ALIASES = {
    "n": "N", "nitrogen": "N",
    "p": "P", "phosphorus": "P",
    "k": "K", "potassium": "K",
    "mg": "Mg", "magnesium": "Mg",
}

def _load_valid_codes() -> set:
    conn = get_db_connection()
    if not conn:
        return set()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT nutrient_code FROM nutrient_deficiency")
        return {r["nutrient_code"] for r in (cur.fetchall() or [])}
    except Exception:
        return set()
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

def _to_nutrient_code(label, valid_codes: set) -> str | None:
    if not label:
        return None
    s = str(label).strip()
    if s.lower() in NORMAL_TOKENS:
        return None  # ปกติ → ไม่ INSERT
    if s.lower() in CODE_ALIASES:
        s = CODE_ALIASES[s.lower()]
    s = s.strip()
    return s if s in valid_codes else None

# ---------- RULE-BASED RECOMMENDATIONS: ใช้ fertilizer จริง ----------
def _upsert_recommendations(cur, inspection_id: int, agg: dict):
    """
    agg: {'K': {'max_conf': 92.1, 'max_sev': 'severe'}, 'Mg': {...}, ...}
    อัปเดต zone_inspection_recommendation โดยพยายามผูกกับ fertilizer.fertilizer_id
    """
    cur.execute("SELECT fertilizer_id, fert_name, formulation, description FROM fertilizer")
    ferts = cur.fetchall() or []

    def _norm(s):
        return (s or '').strip().lower()

    def _match_fertilizer_id(code: str):
        code = (code or '').strip()
        if not code:
            return None
        for r in ferts:
            r_form = _norm(r.get("formulation"))
            r_name = _norm(r.get("fert_name"))

            if code == "N":
                if r_form == "46-0-0": return r["fertilizer_id"]
                if "urea" in r_name or "ยูเรีย" in r_name: return r["fertilizer_id"]
            elif code == "P":
                if r_form == "18-46-0": return r["fertilizer_id"]  # DAP
                if "dap" in r_name: return r["fertilizer_id"]
                if "ฟอสเฟต" in r_name or "ฟอสฟอรัส" in r_name: return r["fertilizer_id"]
            elif code == "K":
                if r_form == "0-0-60": return r["fertilizer_id"]  # MOP
                if "mop" in r_name or "โพแทสเซียมคลอไรด์" in r_name: return r["fertilizer_id"]
            elif code == "Mg":
                if "โดโลไม" in r_name or "dolomite" in r_name: return r["fertilizer_id"]
                if "แมกนีเซียม" in r_name or "magnesium" in r_name: return r["fertilizer_id"]
                if "kieserite" in r_name or "คีเซอร์" in r_name: return r["fertilizer_id"]
        return None

    FALLBACK_TEXT = {
        'K': 'เสริมโพแทสเซียมและควบคุมความชื้น/ความเค็มของดิน',
        'Mg': 'ให้แมกนีเซียมพ่นทางใบหรือใส่ทางดิน',
        'N': 'เสริมไนโตรเจน เพิ่มอินทรียวัตถุและจัดการน้ำให้สม่ำเสมอ',
        'P': 'เสริมฟอสฟอรัส ช่วยระบบรากและการแตกยอด',
    }
    RATE = { 'K': '10–20 กก./ไร่', 'Mg': '10–25 กก./ไร่', 'N': '5–10 กก./ไร่', 'P': '5–10 กก./ไร่' }
    METHOD = { 'K': 'หว่านรอบโคน/คลุกดิน', 'Mg': 'หว่าน + รดน้ำ/พ่นใบ', 'N': 'แบ่งใส่หลายครั้ง', 'P': 'คลุกดิน/รองก้นหลุม' }

    for code, stat in agg.items():
        fert_id = _match_fertilizer_id(code)

        rec_text = FALLBACK_TEXT.get(code, '')
        rate = RATE.get(code)
        method = METHOD.get(code)

        if fert_id is not None:
            try:
                row = next(r for r in ferts if r["fertilizer_id"] == fert_id)
                desc = (row.get("description") or "").strip()
                if desc:
                    rec_text = desc
            except StopIteration:
                pass

        cur.execute("""
            SELECT recommendation_id
            FROM zone_inspection_recommendation
            WHERE inspection_id=%s AND nutrient_code=%s
            ORDER BY recommendation_id DESC
            LIMIT 1
        """, (inspection_id, code))
        exist = cur.fetchone()

        if exist:
            cur.execute("""
                UPDATE zone_inspection_recommendation
                   SET fertilizer_id=%s,
                       recommendation_text=%s,
                       rate_per_area=%s,
                       application_method=%s,
                       status=COALESCE(status,'suggested')
                 WHERE recommendation_id=%s
            """, (fert_id, rec_text, rate, method, exist['recommendation_id']))
        else:
            cur.execute("""
                INSERT INTO zone_inspection_recommendation(
                    inspection_id, fertilizer_id, nutrient_code,
                    recommendation_text, rate_per_area, application_method,
                    status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (inspection_id, fert_id, code, rec_text, rate, method, 'suggested'))

# ---------- start round ----------
@inspection_bp.route('/start', methods=['POST', 'OPTIONS'])
def start_round():
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    body = _ensure_json()
    field_id = body.get('field_id')
    zone_id  = body.get('zone_id')
    notes    = (body.get('notes') or '').strip() or None

    new_round = body.get('new_round')
    if new_round is None:
        qv = (request.args.get('new_round') or '').strip().lower()
        new_round = qv in ('1', 'true', 'yes')
    else:
        new_round = bool(new_round)

    if not field_id or not zone_id:
        return jsonify({'success': False, 'error': 'missing_params'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500

    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT user_id FROM field WHERE field_id=%s", (field_id,))
        owner = cur.fetchone()
        if not owner:
            return jsonify({'success': False, 'error': 'field_not_found'}), 404
        if owner['user_id'] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403

        cur.execute("""
            SELECT inspection_id, round_no
            FROM zone_inspection
            WHERE field_id=%s AND zone_id=%s AND status=%s
            ORDER BY inspection_id DESC LIMIT 1
        """, (field_id, zone_id, STATUS_OPEN))
        exist = cur.fetchone()

        if exist and not new_round:
            return jsonify({
                'success': True, 'idempotent': True,
                'inspection_id': exist['inspection_id'], 'round_no': exist['round_no']
            })

        if exist and new_round:
            cur.execute("""
                UPDATE zone_inspection
                   SET status=%s
                 WHERE inspection_id=%s AND status=%s
            """, (STATUS_DONE, exist['inspection_id'], STATUS_OPEN))
            conn.commit()

        cur.execute("""
            SELECT MAX(round_no) AS max_round
            FROM zone_inspection
            WHERE field_id=%s AND zone_id=%s
        """, (field_id, zone_id))
        maxr = cur.fetchone()['max_round'] or 0
        next_round = int(maxr) + 1

        cur.execute("""
            INSERT INTO zone_inspection(field_id, zone_id, round_no, status, notes, inspected_at)
            VALUES(%s, %s, %s, %s, %s, NOW())
        """, (field_id, zone_id, next_round, STATUS_OPEN, notes))
        conn.commit()
        new_id = cur.lastrowid
        return jsonify({
            'success': True, 'idempotent': False,
            'inspection_id': new_id, 'round_no': next_round
        })

    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- upload images ----------
@inspection_bp.route('/<int:inspection_id>/images', methods=['POST', 'OPTIONS'])
def upload_images(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    if not request.files:
        return jsonify({'success': False, 'error': 'no_files', 'message': 'No files in multipart/form-data'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500

    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT zi.inspection_id, zi.field_id, zi.zone_id, zi.status, f.user_id
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            WHERE zi.inspection_id = %s
        """, (inspection_id,))
        it = cur.fetchone()
        if not it:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if it['user_id'] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403
        if it['status'] != STATUS_OPEN:
            return jsonify({'success': False, 'error': 'closed_round'}), 400

        cur.execute("SELECT COUNT(*) AS c FROM zone_inspection_image WHERE inspection_id=%s", (inspection_id,))
        already = cur.fetchone()['c'] or 0

        remain = max(0, MAX_IMAGES_PER_ROUND - already)
        if remain == 0:
            return jsonify({'success': False, 'error': 'quota_full', 'exist': already, 'max': MAX_IMAGES_PER_ROUND}), 400

        saved = []
        root = _uploads_root()
        folder = root / 'inspections' / str(inspection_id)
        _ensure_dir(folder)

        files = list(request.files.values())
        will_save = files[:remain]
        skipped = max(0, len(files) - len(will_save))

        for f in will_save:
            filename = f.filename or ''
            if not filename or not _ext_ok(filename):
                return jsonify({'success': False, 'error': 'unsupported_media'}), 415

            try:
                f.seek(0, os.SEEK_END); size = f.tell(); f.seek(0)
            except Exception:
                size = None
            if size is not None and size > MAX_FILE_BYTES:
                return jsonify({'success': False, 'error': 'payload_too_large'}), 413

            ext = filename.rsplit('.', 1)[-1].lower()
            ts  = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            safe_name = f"{inspection_id}_{ts}.{ext}"
            path = folder / safe_name
            f.save(str(path))

            rel_path = str(path.relative_to(root)).replace('\\', '/')
            meta = {"original_name": filename, "saved_name": safe_name, "saved_at_utc": ts}
            cur.execute("""
                INSERT INTO zone_inspection_image(inspection_id, image_path, captured_at, meta)
                VALUES(%s, %s, NOW(), %s)
            """, (inspection_id, rel_path, json.dumps(meta, ensure_ascii=False)))
            saved.append({'file': safe_name, 'path': rel_path})

        conn.commit()
        quota_remain = MAX_IMAGES_PER_ROUND - (already + len(saved))
        return jsonify({'success': True, 'saved': saved, 'quota_remain': quota_remain, 'skipped': skipped})

    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- inspection detail ----------
@inspection_bp.route('/<int:inspection_id>', methods=['GET', 'OPTIONS'])
def get_detail(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500

    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT zi.*, z.zone_name, f.field_name, f.user_id
            FROM zone_inspection zi
            JOIN zone  z ON zi.zone_id  = z.zone_id
            JOIN field f ON zi.field_id = f.field_id
            WHERE zi.inspection_id = %s
        """, (inspection_id,))
        head = cur.fetchone()
        if not head:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if head['user_id'] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403

        cur.execute("""
            SELECT image_id, image_path, captured_at, meta
            FROM zone_inspection_image
            WHERE inspection_id = %s
            ORDER BY image_id
        """, (inspection_id,))
        images = cur.fetchall()

        cur.execute("""
            SELECT finding_id, nutrient_code, severity, confidence, notes
            FROM zone_inspection_finding
            WHERE inspection_id = %s
            ORDER BY finding_id
        """, (inspection_id,))
        findings = cur.fetchall()

        used = len(images)
        quota = {'max': MAX_IMAGES_PER_ROUND, 'used': used, 'remain': max(0, MAX_IMAGES_PER_ROUND - used)}

        return jsonify({'success': True, 'data': {
            'inspection': head, 'images': images, 'findings': findings, 'warnings': [], 'quota': quota
        }})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- analyze (call model from detect.py) ----------
@inspection_bp.route('/<int:inspection_id>/analyze', methods=['POST', 'OPTIONS'])
def run_analyze(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT zi.*, f.user_id
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            WHERE zi.inspection_id = %s
        """, (inspection_id,))
        it = cur.fetchone()
        if not it:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if it['user_id'] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403

        cur.execute("SELECT image_path FROM zone_inspection_image WHERE inspection_id=%s", (inspection_id,))
        imgs = [r['image_path'] for r in cur.fetchall()]
        if not imgs:
            return jsonify({'success': False, 'error': 'no_images'}), 400

        root = _uploads_root()
        abs_paths = [str((root / rel).resolve()) for rel in imgs]

        # เรียกโมเดล
        results = predict_on_paths(abs_paths, conf_thres=0.25)

        valid_codes = _load_valid_codes()

        # map ชื่อคลาสจากโมเดล → โค้ดย่อ
        CLASS_ALIASES = {
            'Magnesium':  'Mg',
            'Nitrogen':   'N',
            'Phosphorus': 'P',
            'Potassium':  'K',
        }

        def severity_from_conf(conf_pct: float) -> str:
            if conf_pct >= 85: return 'severe'
            if conf_pct >= 65: return 'moderate'
            return 'mild'

        agg = {}          # code -> {'max_conf': float, 'max_sev': str}
        skipped_normal = 0
        unknown_labels = []

        for item in results:
            for p in (item.get('preds') or []):
                raw_label = str(p.get('class', '')).strip()
                label_for_code = CLASS_ALIASES.get(raw_label, raw_label)
                code = _to_nutrient_code(label_for_code, valid_codes)
                if code is None:
                    if raw_label.lower() in NORMAL_TOKENS:
                        skipped_normal += 1
                    else:
                        unknown_labels.append(raw_label)
                    continue
                conf_pct = float(p.get('confidence') or 0.0) * 100.0
                sev = severity_from_conf(conf_pct)
                if code not in agg or conf_pct > agg[code]['max_conf']:
                    agg[code] = {'max_conf': conf_pct, 'max_sev': sev}

        # เคลียร์ finding เดิม
        cur.execute("DELETE FROM zone_inspection_finding WHERE inspection_id=%s", (inspection_id,))

        if not agg:
            conn.commit()
            return jsonify({
                'success': True,
                'warnings': [],
                'results': results,
                'findings': [],
                'skipped_normal': skipped_normal,
                'unknown_labels': unknown_labels
            })

        # INSERT findings ใหม่
        findings = []
        for code, stat in agg.items():
            findings.append({
                'nutrient_code': code,
                'severity': stat['max_sev'],
                'confidence': round(stat['max_conf'], 2),
                'notes': None
            })
            cur.execute("""
                INSERT INTO zone_inspection_finding(inspection_id, nutrient_code, severity, confidence, notes)
                VALUES(%s, %s, %s, %s, %s)
            """, (inspection_id, code, stat['max_sev'], round(stat['max_conf'], 2), None))

        # อัปเดตคำแนะนำผูกกับ fertilizer จริง
        _upsert_recommendations(cur, inspection_id, agg)

        conn.commit()
        return jsonify({
            'success': True,
            'warnings': [],
            'results': results,
            'findings': findings,
            'skipped_normal': skipped_normal,
            'unknown_labels': unknown_labels
        })

    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- recommendations: list ----------
@inspection_bp.route('/<int:inspection_id>/recommendations', methods=['GET', 'OPTIONS'])
def get_recommendations(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT f.user_id
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            WHERE zi.inspection_id = %s
        """, (inspection_id,))
        own = cur.fetchone()
        if not own:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if own['user_id'] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403

        cur.execute("""
            SELECT r.recommendation_id, r.inspection_id, r.fertilizer_id, r.nutrient_code,
                   r.recommendation_text, r.rate_per_area, r.application_method,
                   r.status, r.applied_date, r.created_at,
                   fert.fert_name, fert.formulation,
                   nd.nutrient_name
            FROM zone_inspection_recommendation r
            LEFT JOIN fertilizer fert ON r.fertilizer_id = fert.fertilizer_id
            LEFT JOIN nutrient_deficiency nd ON r.nutrient_code = nd.nutrient_code
            WHERE r.inspection_id = %s
            ORDER BY r.recommendation_id
        """, (inspection_id,))
        rows = cur.fetchall()
        return jsonify({'success': True, 'data': rows, 'count': len(rows)})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- recommendations: patch ----------
@inspection_bp.route('/recommendations/<int:rec_id>', methods=['PATCH', 'PUT', 'OPTIONS'])
def patch_recommendation(rec_id):
    user, err = _authz().__iter__() if False else _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    body = _ensure_json()
    status = (body.get('status') or '').strip().lower()
    applied_date = body.get('applied_date')

    if status not in ('suggested', 'applied', 'skipped'):
        return jsonify({'success': False, 'error': 'bad_status'}), 400

    if status == 'applied':
        if applied_date:
            d = _parse_yyyy_mm_dd(applied_date)
            if not d:
                return jsonify({'success': False, 'error': 'bad_date_format'}), 400
        else:
            applied_date = date.today().strftime('%Y-%m-%d')
    else:
        applied_date = None

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT f.user_id
            FROM zone_inspection_recommendation r
            JOIN zone_inspection zi ON r.inspection_id = zi.inspection_id
            JOIN field f ON zi.field_id = f.field_id
            WHERE r.recommendation_id = %s
        """, (rec_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if row[0] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403

        cur.execute("""
            UPDATE zone_inspection_recommendation
               SET status = %s, applied_date = %s
             WHERE recommendation_id = %s
        """, (status, applied_date, rec_id))
        conn.commit()
        return jsonify({'success': True})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- (ทางเลือก) BACKFILL API: เติมคำแนะนำจาก findings เดิม ----------
@inspection_bp.route('/<int:inspection_id>/recommendations/backfill', methods=['POST', 'OPTIONS'])
def backfill_recommendations(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500
    try:
        cur = conn.cursor(dictionary=True)

        # สิทธิ์เจ้าของ
        cur.execute("""
            SELECT f.user_id
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            WHERE zi.inspection_id = %s
        """, (inspection_id,))
        own = cur.fetchone()
        if not own:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        if own['user_id'] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403

        # รวมผลล่าสุดของแต่ละ nutrient_code
        cur.execute("""
            SELECT nutrient_code,
                   MAX(confidence) AS max_conf,
                   SUBSTRING_INDEX(
                       GROUP_CONCAT(severity ORDER BY confidence DESC SEPARATOR ','), ',', 1
                   ) AS max_sev
            FROM zone_inspection_finding
            WHERE inspection_id = %s
            GROUP BY nutrient_code
        """, (inspection_id,))
        agg_rows = cur.fetchall()
        agg = {r['nutrient_code']: {'max_conf': float(r['max_conf'] or 0.0),
                                    'max_sev': r['max_sev'] or 'moderate'} for r in agg_rows}

        _upsert_recommendations(cur, inspection_id, agg)

        conn.commit()
        return jsonify({'success': True, 'updated_codes': list(agg.keys())})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- history (คืนค่าเชิงสถิติ) ----------
# รองรับทั้ง /history และ /history/ เพื่อกัน redirect 308 บาง client
@inspection_bp.route('/history', methods=['GET', 'OPTIONS'], strict_slashes=False)
@inspection_bp.route('/history/', methods=['GET'], strict_slashes=False)
def inspection_history():
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    group = (request.args.get('group') or 'month').lower()
    if group not in ('month', 'year'):
        group = 'month'

    field_id = request.args.get('field_id', type=int)
    zone_id  = request.args.get('zone_id', type=int)
    start_dt, end_dt = _normalize_range(request.args.get('from'), request.args.get('to'))
    bucket_sql = "DATE_FORMAT(zi.inspected_at, '%Y-%m')" if group == 'month' else "DATE_FORMAT(zi.inspected_at, '%Y')"

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500
    try:
        cur = conn.cursor(dictionary=True)

        where = ["f.user_id = %s"]; params = [uid]
        if start_dt:
            where.append("zi.inspected_at >= %s"); params.append(start_dt.strftime('%Y-%m-%d %H:%M:%S'))
        if end_dt:
            where.append("zi.inspected_at <= %s"); params.append(end_dt.strftime('%Y-%m-%d %H:%M:%S'))
        if field_id:
            where.append("zi.field_id = %s"); params.append(field_id)
        if zone_id:
            where.append("zi.zone_id = %s"); params.append(zone_id)
        W = " AND ".join(where)

        cur.execute(f"""
            SELECT {bucket_sql} AS bucket, COUNT(*) AS inspections
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            WHERE {W}
            GROUP BY bucket
            ORDER BY bucket
        """, params)
        buckets = cur.fetchall()

        cur.execute(f"""
            SELECT {bucket_sql} AS bucket, COUNT(*) AS findings
            FROM zone_inspection zi
            JOIN zone_inspection_finding zif ON zif.inspection_id = zi.inspection_id
            JOIN field f ON zi.field_id = f.field_id
            WHERE {W}
            GROUP BY bucket
            ORDER BY bucket
        """, params)
        fcounts = {r['bucket']: r['findings'] for r in cur.fetchall()}

        cur.execute(f"""
            SELECT zif.nutrient_code, COUNT(*) AS cnt
            FROM zone_inspection zi
            JOIN zone_inspection_finding zif ON zif.inspection_id = zi.inspection_id
            JOIN field f ON zi.field_id = f.field_id
            WHERE {W}
            GROUP BY zif.nutrient_code
            ORDER BY cnt DESC
            LIMIT 5
        """, params)
        top = cur.fetchall()

        for b in buckets:
            b['findings'] = fcounts.get(b['bucket'], 0)

        return jsonify({'success': True, 'group': group, 'buckets': buckets, 'top_nutrients': top})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- list (หน้าแรกของ /api/inspections) ----------
@inspection_bp.route('', methods=['GET', 'OPTIONS'], strict_slashes=False)
@inspection_bp.route('/', methods=['GET'], strict_slashes=False)
def list_inspections():
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    page = max(1, int(request.args.get('page', 1)))
    size = min(100, max(1, int(request.args.get('page_size', 20))))
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    field_id = request.args.get('field_id', type=int)
    zone_id = request.args.get('zone_id', type=int)

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'db_failed'}), 500
    try:
        cur = conn.cursor(dictionary=True)

        where = ["f.user_id = %s"]; params = [uid]
        if year:     where.append("YEAR(zi.inspected_at) = %s"); params.append(year)
        if month:    where.append("MONTH(zi.inspected_at) = %s"); params.append(month)
        if field_id: where.append("zi.field_id = %s"); params.append(field_id)
        if zone_id:  where.append("zi.zone_id = %s"); params.append(zone_id)
        W = " AND ".join(where)

        cur.execute(f"""
            SELECT COUNT(*) AS c
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            WHERE {W}
        """, params)
        total = cur.fetchone()['c']

        cur.execute(f"""
            SELECT zi.inspection_id, zi.field_id, zi.zone_id,
                   zi.round_no, zi.inspected_at, zi.status, zi.notes,
                   z.zone_name, f.field_name,
                   (SELECT COUNT(*) FROM zone_inspection_image i WHERE i.inspection_id = zi.inspection_id) AS images,
                   (SELECT COUNT(*) FROM zone_inspection_finding fi WHERE fi.inspection_id = zi.inspection_id) AS findings,
                   (SELECT COUNT(*) FROM zone_inspection_recommendation r WHERE r.inspection_id = zi.inspection_id) AS recs
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            JOIN zone z   ON zi.zone_id  = z.zone_id
            WHERE {W}
            ORDER BY zi.inspected_at DESC, zi.inspection_id DESC
            LIMIT %s OFFSET %s
        """, params + [size, (page - 1) * size])
        rows = cur.fetchall()

        return jsonify({'success': True, 'data': rows, 'page': page, 'page_size': size, 'total': total})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass
