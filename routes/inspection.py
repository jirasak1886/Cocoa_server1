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

# ========== โควตา “กี่รอบก็ได้ แต่รอบละไม่เกิน 5 รูป” ==========
MAX_IMAGES_PER_ROUND = 5

# ---------- helpers ----------
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
    """คืน (user_payload, error_tuple_or_None) เสมอ"""
    if request.method == 'OPTIONS':
        return None, ('', 204)
    u = _get_user()
    if not u:
        return None, (jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Authentication required'
        }), 401)
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
    # ให้ ENV มีลำดับความสำคัญสูงสุด
    env_root = os.environ.get('UPLOAD_ROOT', '').strip()
    if env_root:
        return Path(env_root)
    # ค่าเริ่มต้น: โฟลเดอร์ upload (ตามที่ตกลง)
    return Path(current_app.root_path) / 'upload'

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def _ext_ok(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTS

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

    # รองรับการ “เริ่มรอบใหม่” ทันที: ส่ง new_round=true (body หรือ query ก็ได้)
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

        # ตรวจว่า field เป็นของ user
        cur.execute("SELECT user_id FROM field WHERE field_id=%s", (field_id,))
        owner = cur.fetchone()
        if not owner:
            return jsonify({'success': False, 'error': 'field_not_found'}), 404
        if owner['user_id'] != uid:
            return jsonify({'success': False, 'error': 'forbidden'}), 403

        # หา "รอบที่เปิดอยู่"
        cur.execute("""
            SELECT inspection_id, round_no
            FROM zone_inspection
            WHERE field_id=%s AND zone_id=%s AND status=%s
            ORDER BY inspection_id DESC LIMIT 1
        """, (field_id, zone_id, STATUS_OPEN))
        exist = cur.fetchone()

        if exist and not new_round:
            # พฤติกรรมเดิม: idempotent (ยกเลิกรอบใหม่ ใช้รอบเดิม)
            return jsonify({
                'success': True, 'idempotent': True,
                'inspection_id': exist['inspection_id'], 'round_no': exist['round_no']
            })

        # ถ้ามีรอบค้างอยู่ และผู้ใช้ขอ new_round ให้ปิดรอบเดิมก่อน (กันมีหลาย pending)
        if exist and new_round:
            cur.execute("""
                UPDATE zone_inspection
                   SET status=%s
                 WHERE inspection_id=%s AND status=%s
            """, (STATUS_DONE, exist['inspection_id'], STATUS_OPEN))
            conn.commit()

        # สร้างรอบใหม่: round_no = MAX(round_no) + 1
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

        # ตรวจสิทธิ์ + สถานะรอบ
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

        # นับรูปใน "รอบนี้"
        cur.execute("SELECT COUNT(*) AS c FROM zone_inspection_image WHERE inspection_id=%s", (inspection_id,))
        already = cur.fetchone()['c'] or 0

        # โควตาต่อรอบ (≤ 5)
        remain = max(0, MAX_IMAGES_PER_ROUND - already)
        if remain == 0:
            return jsonify({
                'success': False,
                'error': 'quota_full',
                'exist': already,
                'max': MAX_IMAGES_PER_ROUND
            }), 400

        saved = []
        root = _uploads_root()
        folder = root / 'inspections' / str(inspection_id)
        _ensure_dir(folder)

        # รับไฟล์จาก multipart (ทุก field รวมกัน)
        files = list(request.files.values())
        will_save = files[:remain]
        skipped = max(0, len(files) - len(will_save))

        for f in will_save:
            filename = f.filename or ''
            if not filename or not _ext_ok(filename):
                return jsonify({'success': False, 'error': 'unsupported_media'}), 415

            # ตรวจขนาดไฟล์ (ถ้าวัดได้)
            try:
                f.seek(0, os.SEEK_END); size = f.tell(); f.seek(0)
            except Exception:
                size = None
            if size is not None and size > MAX_FILE_BYTES:
                return jsonify({'success': False, 'error': 'payload_too_large'}), 413

            # เซฟไฟล์ไปที่ /upload/inspections/<inspection_id>/
            ext = filename.rsplit('.', 1)[-1].lower()
            ts  = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            safe_name = f"{inspection_id}_{ts}.{ext}"
            path = folder / safe_name
            f.save(str(path))

            rel_path = str(path.relative_to(root))
            meta = {"original_name": filename, "saved_name": safe_name, "saved_at_utc": ts}
            cur.execute("""
                INSERT INTO zone_inspection_image(inspection_id, image_path, captured_at, meta)
                VALUES(%s, %s, NOW(), %s)
            """, (inspection_id, rel_path, json.dumps(meta, ensure_ascii=False)))
            saved.append({'file': safe_name, 'path': rel_path})

        conn.commit()
        quota_remain = MAX_IMAGES_PER_ROUND - (already + len(saved))
        return jsonify({
            'success': True,
            'saved': saved,
            'quota_remain': quota_remain,
            'skipped': skipped
        })

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

        # โควตาเพื่อให้ client แสดงผลได้ชัดเจน
        used = len(images)
        quota = {
            'max': MAX_IMAGES_PER_ROUND,
            'used': used,
            'remain': max(0, MAX_IMAGES_PER_ROUND - used),
        }

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

        # map class -> nutrient_code (แก้ให้ตรงกับ labels ของโมเดล)
        CLASS_TO_NUTRIENT = {
            'nitrogen_def': 'N', 'phosphorus_def': 'P',
            'potassium_def': 'K', 'magnesium_def': 'Mg',
            'N': 'N', 'P': 'P', 'K': 'K', 'Mg': 'Mg',
        }

        def severity_from_conf(conf_pct: float) -> str:
            if conf_pct >= 85: return 'severe'
            if conf_pct >= 65: return 'moderate'
            return 'mild'

        agg = {}  # code -> {'max_conf': float, 'max_sev': str}
        for item in results:
            preds = item.get('preds') or []
            for p in preds:
                label = str(p.get('class', '')).strip()
                conf  = float(p.get('confidence') or 0.0) * 100.0
                code  = CLASS_TO_NUTRIENT.get(label) or CLASS_TO_NUTRIENT.get(label.lower())
                if not code:
                    continue
                sev = severity_from_conf(conf)
                if code not in agg or conf > agg[code]['max_conf']:
                    agg[code] = {'max_conf': conf, 'max_sev': sev}

        cur.execute("DELETE FROM zone_inspection_finding WHERE inspection_id=%s", (inspection_id,))
        for code, stat in agg.items():
            cur.execute("""
                INSERT INTO zone_inspection_finding(inspection_id, nutrient_code, severity, confidence, notes)
                VALUES(%s, %s, %s, %s, %s)
            """, (inspection_id, code, stat['max_sev'], round(stat['max_conf'], 2), None))

        conn.commit()
        return jsonify({'success': True, 'warnings': []})
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

# ---------- recommendations: patch status ----------
@inspection_bp.route('/recommendations/<int:rec_id>', methods=['PATCH', 'PUT', 'OPTIONS'])
def patch_recommendation(rec_id):
    user, err = _authz()
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

# ---------- history ----------
@inspection_bp.route('/history', methods=['GET', 'OPTIONS'])
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

# ---------- list ----------
@inspection_bp.route('', methods=['GET', 'OPTIONS'])
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
        if zone_id:  where.append("zi.zone_id = %s");  params.append(zone_id)
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
