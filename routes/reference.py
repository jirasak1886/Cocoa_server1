# routes/reference.py
from flask import Blueprint, jsonify
from config.database import get_db_connection  # ใช้ตัวเดียวกับ inspection.py

reference_bp = Blueprint("reference", __name__, url_prefix="/api/reference")

# ---------- Helpers ----------
def _normalize_label(val):
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("normal", "nomal"):
        return "ปกติ"
    return val

# ---------- Routes ----------
@reference_bp.get("/health")
def health():
    return jsonify({"service": "reference", "status": "ok"}), 200

@reference_bp.get("/nutrients")
def get_nutrients():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT nutrient_code, nutrient_name, common_symptoms, diagnostic_notes
            FROM nutrient_deficiency
            ORDER BY nutrient_code ASC
        """)
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
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": f"{e.__class__.__name__}: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

@reference_bp.get("/fertilizers")
def get_fertilizers():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT fertilizer_id, fert_name, formulation, description
            FROM fertilizer
            ORDER BY fertilizer_id ASC
        """)
        rows = cur.fetchall() or []
        data = []
        for r in rows:
            name = _normalize_label(r.get("fert_name"))
            data.append({
                "id": r.get("fertilizer_id"),
                "name": name or r.get("fert_name"),
                "formulation": r.get("formulation"),
                "description": r.get("description"),
            })
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": f"{e.__class__.__name__}: {e}"}), 500
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

@reference_bp.get("/all")
def get_all():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
    try:
        cur = conn.cursor(dictionary=True)

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

        cur.execute("""
            SELECT fertilizer_id, fert_name, formulation, description
            FROM fertilizer
            ORDER BY fertilizer_id ASC
        """)
        f_rows = cur.fetchall() or []
        fertilizers = []
        for r in f_rows:
            name = _normalize_label(r.get("fert_name"))
            fertilizers.append({
                "id": r.get("fertilizer_id"),
                "name": name or r.get("fert_name"),
                "formulation": r.get("formulation"),
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
