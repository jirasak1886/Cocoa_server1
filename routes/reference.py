# routes/reference.py
from flask import Blueprint, jsonify, request
from config.database import get_db_connection  # ใช้ตัวเดียวกับ inspection.py

reference_bp = Blueprint("reference", __name__, url_prefix="/api/reference")


# ------------------ helpers ------------------
def _normalize_label(val):
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("normal", "nomal"):
        return "ปกติ"
    return val


def _get_page_args():
    try:
        page = int(request.args.get("page", 1))
    except Exception:
        page = 1
    try:
        page_size = int(request.args.get("page_size", 20))
    except Exception:
        page_size = 20
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    return page, page_size


def _detect_fert_schema(cur):
    """
    คืน mapping ชื่อคอลัมน์ของ fertilizer ตามสคีมาที่มีจริง:
    - id_col:      'fertilizer_id' หรือ 'id'
    - name_col:    'fert_name' หรือ 'name'
    - code_col:    'formulation' หรือ 'code'
    - desc_col:    'description' (ถ้ามี)
    """
    cur.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'fertilizer'
    """)
    cols = {r['COLUMN_NAME'].lower() for r in (cur.fetchall() or [])}

    # โครง A: id, name, code, description ...
    if {'id', 'name'}.issubset(cols):
        return {
            'id_col': 'id',
            'name_col': 'name',
            'code_col': 'code' if 'code' in cols else None,
            'desc_col': 'description' if 'description' in cols else None,
        }

    # โครง B: fertilizer_id, fert_name, formulation, description ...
    return {
        'id_col': 'fertilizer_id' if 'fertilizer_id' in cols else 'id',
        'name_col': 'fert_name' if 'fert_name' in cols else ('name' if 'name' in cols else None),
        'code_col': 'formulation' if 'formulation' in cols else ('code' if 'code' in cols else None),
        'desc_col': 'description' if 'description' in cols else None,
    }


# ------------------ endpoints ------------------
@reference_bp.get("/health")
def health():
    return jsonify({"service": "reference", "status": "ok"}), 200


@reference_bp.get("/nutrients")
def get_nutrients():
    """
    แบ่งหน้าได้ด้วย ?page=&page_size=
    ตอบ: { success, data, page, page_size, total }
    """
    page, page_size = _get_page_args()
    offset = (page - 1) * page_size

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
    try:
        cur = conn.cursor(dictionary=True)

        # นับทั้งหมด
        cur.execute("SELECT COUNT(*) AS total FROM nutrient_deficiency")
        total = int((cur.fetchone() or {}).get('total', 0))

        # ดึงรายการตามหน้า
        cur.execute("""
            SELECT nutrient_code, nutrient_name, common_symptoms, diagnostic_notes
            FROM nutrient_deficiency
            ORDER BY nutrient_code ASC
            LIMIT %s OFFSET %s
        """, (page_size, offset))
        rows = cur.fetchall() or []

        data = []
        for r in rows:
            name = _normalize_label(r.get("nutrient_name"))
            data.append({
                "code": r.get("nutrient_code"),
                "name": name or r.get("nutrient_name"),
                "symptoms": r.get("common_symptoms"),
                "notes": r.get("diagnostic_notes"),
            })
        return jsonify({"success": True, "data": data, "page": page, "page_size": page_size, "total": total})
    except Exception as e:
        return jsonify({"success": False, "error": f"{e.__class__.__name__}: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass


@reference_bp.get("/fertilizers")
def get_fertilizers():
    """
    แบ่งหน้าได้ด้วย ?page=&page_size=
    รองรับสคีมาปุ๋ยหลายแบบ (id/name/code หรือ fertilizer_id/fert_name/formulation)
    ตอบ: { success, data, page, page_size, total }
    """
    page, page_size = _get_page_args()
    offset = (page - 1) * page_size

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
    try:
        cur = conn.cursor(dictionary=True)

        # ตรวจสคีมา
        sch = _detect_fert_schema(cur)
        id_col = sch['id_col']
        name_col = sch['name_col']
        code_col = sch['code_col']  # อาจเป็น formulation หรือ code
        desc_col = sch['desc_col']

        # นับทั้งหมด
        cur.execute("SELECT COUNT(*) AS total FROM fertilizer")
        total = int((cur.fetchone() or {}).get('total', 0))

        # select cols
        select_cols = [f"{id_col} AS fert_id", f"{name_col} AS fert_name"]
        if code_col:
            select_cols.append(f"{code_col} AS form_code")
        else:
            select_cols.append("NULL AS form_code")
        if desc_col:
            select_cols.append(f"{desc_col} AS description")
        else:
            select_cols.append("NULL AS description")

        # ดึงรายการ
        cur.execute(f"""
            SELECT {", ".join(select_cols)}
            FROM fertilizer
            ORDER BY {id_col} ASC
            LIMIT %s OFFSET %s
        """, (page_size, offset))
        rows = cur.fetchall() or []

        data = []
        for r in rows:
            name = _normalize_label(r.get("fert_name"))
            data.append({
                "id": r.get("fert_id"),
                "name": name or r.get("fert_name"),
                # ถ้าเป็น schema A: form_code คือ code, schema B: form_code คือ formulation
                "formulation": r.get("form_code"),
                "description": r.get("description"),
            })
        return jsonify({"success": True, "data": data, "page": page, "page_size": page_size, "total": total})
    except Exception as e:
        return jsonify({"success": False, "error": f"{e.__class__.__name__}: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass


@reference_bp.get("/all")
def get_all():
    """
    ดึงทั้งหมด (ไม่แบ่งหน้า) – ถ้าข้อมูลเยอะมากไม่แนะนำเรียก endpoint นี้บ่อย
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
    try:
        cur = conn.cursor(dictionary=True)

        # nutrients
        cur.execute("""
            SELECT nutrient_code, nutrient_name, common_symptoms, diagnostic_notes
            FROM nutrient_deficiency
            ORDER BY nutrient_code ASC
        """)
        n_rows = cur.fetchall() or []
        nutrients = []
        for r in n_rows:
            name = _normalize_label(r.get("nutrient_name"))
            nutrients.append({
                "code": r.get("nutrient_code"),
                "name": name or r.get("nutrient_name"),
                "symptoms": r.get("common_symptoms"),
                "notes": r.get("diagnostic_notes"),
            })

        # fertilizers (รองรับหลายสคีมา)
        sch = _detect_fert_schema(cur)
        id_col = sch['id_col']
        name_col = sch['name_col']
        code_col = sch['code_col']
        desc_col = sch['desc_col']

        select_cols = [f"{id_col} AS fert_id", f"{name_col} AS fert_name"]
        if code_col:
            select_cols.append(f"{code_col} AS form_code")
        else:
            select_cols.append("NULL AS form_code")
        if desc_col:
            select_cols.append(f"{desc_col} AS description")
        else:
            select_cols.append("NULL AS description")

        cur.execute(f"""
            SELECT {", ".join(select_cols)}
            FROM fertilizer
            ORDER BY {id_col} ASC
        """)
        f_rows = cur.fetchall() or []
        fertilizers = []
        for r in f_rows:
            name = _normalize_label(r.get("fert_name"))
            fertilizers.append({
                "id": r.get("fert_id"),
                "name": name or r.get("fert_name"),
                "formulation": r.get("form_code"),
                "description": r.get("description"),
            })

        return jsonify({"success": True, "data": {
            "nutrients": nutrients, "fertilizers": fertilizers
        }})
    except Exception as e:
        return jsonify({"success": False, "error": f"{e.__class__.__name__}: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass
