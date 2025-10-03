# routes/inspection.py
from flask import Blueprint, request, jsonify, current_app
from config.database import get_db_connection
from mysql.connector import Error
from datetime import datetime, date, timedelta
from pathlib import Path
import jwt, os, json, re

from routes.detect import predict_on_paths  # ใช้โมเดลจาก detect.py

inspection_bp = Blueprint("inspection", __name__)

STATUS_OPEN = "pending"
STATUS_DONE = "completed"

ALLOWED_EXTS = {"jpg", "jpeg", "png", "bmp", "webp"}
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_IMAGES_PER_ROUND = 5

# ---------- helpers (auth / io) ----------
def _get_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ")[1]
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None

def _user_id(u):
    if not isinstance(u, dict):
        return None
    return u.get("user_id") or u.get("sub") or u.get("uid")

def _authz():
    if request.method == "OPTIONS":
        return None, ("", 204)
    u = _get_user()
    if not u:
        return None, (jsonify({"success": False, "error": "unauthorized", "message": "Authentication required"}), 401)
    return u, None

def _ensure_json():
    if request.is_json:
        return request.get_json(silent=True) or {}
    return {}

def _parse_yyyy_mm_dd(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
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
    env_root = os.environ.get("UPLOAD_ROOT", "").strip()
    if env_root:
        return Path(env_root)
    return Path(current_app.root_path) / "static" / "uploads"

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def _ext_ok(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTS

# ---------- NORMALIZE / WHITELIST ----------
NORMAL_TOKENS = {"normal", "nomal", "healthy", "none"}
CODE_ALIASES = {
    "n": "N", "nitrogen": "N",
    "p": "P", "phosphorus": "P",
    "k": "K", "potassium": "K",
    "mg": "Mg", "magnesium": "Mg",
}

def _load_valid_codes() -> set:
    """พยายามโหลดโค้ดธาตุจาก DB; ถ้าไม่ได้ ให้ใช้ค่า default เพื่อให้ระบบเดินต่อได้"""
    try:
        conn = get_db_connection()
        if not conn:
            return {"N", "P", "K", "MG"}
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT nutrient_code FROM nutrient_deficiency")
        rows = cur.fetchall() or []
        got = {r["nutrient_code"] for r in rows}
        return got if got else {"N", "P", "K", "MG"}
    except Exception:
        return {"N", "P", "K", "MG"}
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
        return None
    if s.lower() in CODE_ALIASES:
        s = CODE_ALIASES[s.lower()]
    s = s.strip()
    return s if s in valid_codes else None

# -------- normalization helpers --------
def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _norm_formula(s: str) -> str:
    t = (s or "")
    t = t.replace("\r", "").replace("\n", "").replace(" ", "")
    t = re.sub(r"[–—−‐]", "-", t)
    t = re.sub(r"-{2,}", "-", t)
    return t.strip().lower()

# ---------- ตรวจสคีมาตาราง fertilizer แบบไดนามิก ----------
def _detect_fert_schema(cur):
    if not cur:
        # ไม่มี cursor → ให้ schema เริ่มต้นเพื่อกัน crash
        return {
            "id_col": "id",
            "name_col": "name",
            "name_th_col": None,
            "code_col": "code",
            "desc_col": None,
            "active_col": None,
        }
    cur.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'fertilizer'
    """)
    cols = {r["COLUMN_NAME"].lower() for r in (cur.fetchall() or [])}

    if {"id", "code", "name"}.issubset(cols):
        return {
            "id_col": "id",
            "name_col": "name",
            "name_th_col": "name_th" if "name_th" in cols else None,
            "code_col": "code",
            "desc_col": "description" if "description" in cols else None,
            "active_col": "is_active" if "is_active" in cols else None,
        }
    return {
        "id_col": "fertilizer_id" if "fertilizer_id" in cols else "id",
        "name_col": "fert_name" if "fert_name" in cols else ("name" if "name" in cols else None),
        "name_th_col": "name_th" if "name_th" in cols else None,
        "code_col": "formulation" if "formulation" in cols else ("code" if "code" in cols else None),
        "desc_col": "description" if "description" in cols else None,
        "active_col": "is_active" if "is_active" in cols else None,
    }

# ---------- ช่วย parse NPK + สแกน inventory ----------
_NPK_RE = re.compile(r'(\d+)-(\d+)-(\d+)', re.IGNORECASE)

def _parse_npk(code: str):
    if not code:
        return None
    s = _norm_formula(code)
    m = _NPK_RE.search(s)
    if not m:
        return None
    try:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        return None

def _fetch_all_fertilizers(cur):
    if not cur:
        return []
    sch = _detect_fert_schema(cur)
    select_cols = [
        f"{sch['id_col']}   AS fert_id",
        f"{sch['name_col']} AS fert_name",
        f"{sch['code_col']} AS formulation",
    ]
    if sch["name_th_col"]:
        select_cols.append(f"{sch['name_th_col']} AS fert_name_th")
    else:
        select_cols.append("NULL AS fert_name_th")
    if sch["desc_col"]:
        select_cols.append(f"{sch['desc_col']} AS fert_description")
    else:
        select_cols.append("NULL AS fert_description")

    where_active = f" WHERE {sch['active_col']} = 1 " if sch["active_col"] else ""
    cur.execute(f"SELECT {', '.join(select_cols)} FROM fertilizer{where_active}")
    return cur.fetchall() or []

def _pick_best_by_component(cur, target: str):
    if not cur:
        return None
    rows = _fetch_all_fertilizers(cur)
    best = None
    best_key = None
    for r in rows:
        formu = (r.get("formulation") or "").strip()
        npk = _parse_npk(formu)
        if not npk:
            continue
        n, p, k = npk
        if target == "K":
            key = (k, -(n+p))
        elif target == "N":
            key = (n, -(p+k))
        else:  # P
            key = (p, -(n+k))
        if (best_key is None) or (key > best_key):
            best_key = key
            best = r
    if best:
        return {**best, "reason": f"เลือกจาก inventory: เน้น {target} สูงสุด"}
    return None

# ---------- เลือกปุ๋ยตาม DB ----------
def _fetch_fert_by_code(cur, code: str):
    if not cur:
        return None
    sch = _detect_fert_schema(cur)
    select_cols = [
        f"{sch['id_col']}   AS fert_id",
        f"{sch['name_col']} AS fert_name",
        f"{sch['code_col']} AS formulation",
    ]
    if sch["name_th_col"]:
        select_cols.append(f"{sch['name_th_col']} AS fert_name_th")
    else:
        select_cols.append("NULL AS fert_name_th")
    if sch["desc_col"]:
        select_cols.append(f"{sch['desc_col']} AS fert_description")
    else:
        select_cols.append("NULL AS fert_description")

    where_active = ""
    if sch["active_col"]:
        where_active = f" AND {sch['active_col']} = 1 "

    sql = f"""
        SELECT {', '.join(select_cols)}
        FROM fertilizer
        WHERE LOWER({sch['code_col']}) = LOWER(%s) {where_active}
        LIMIT 1
    """
    cur.execute(sql, (code,))
    row = cur.fetchone()
    if row:
        return row

    # fallback: เทียบ normalize / ตัวเลข N-P-K
    rows = _fetch_all_fertilizers(cur)
    want = _norm_formula(code)
    for r in rows:
        if _norm_formula(r.get("formulation") or "") == want:
            r.setdefault("fert_name_th", None)
            r.setdefault("fert_description", None)
            return r

    want_npk = _parse_npk(code)
    if want_npk:
        for r in rows:
            r_npk = _parse_npk(r.get("formulation") or "")
            if r_npk and r_npk == want_npk:
                r.setdefault("fert_name_th", None)
                r.setdefault("fert_description", None)
                return r

    return None

# ---------- Virtual recommendation helpers ----------
def __virtual(code: str, name: str | None = None, reason: str = ""):
    """สร้างคำแนะนำแบบไม่มีในคลัง (fert_id=None)"""
    return {
        "fert_id": None,
        "fert_name": (name or code),
        "formulation": code,
        "fert_name_th": None,
        "fert_description": None,
        "reason": (reason or "สูตรนี้เหมาะสมแต่ไม่มีในคลัง (virtual)")
    }

def pick_or_virtual(cur, code: str, name_hint: str | None = None, reason_hint: str | None = None):
    r = _fetch_fert_by_code(cur, code)
    if r:
        if reason_hint:
            r = {**r, "reason": reason_hint}
        return r
    return __virtual(code, name_hint, reason_hint or "สูตรนี้เหมาะสมแต่ไม่พบในคลัง")

def _first_non_none(*vals):
    for v in vals:
        if v is not None:
            return v
    return None

def _find_best_plus_mg(cur, prefer: set[str] | None = None):
    """หา formulation ที่มี +Mg ในคลัง"""
    if not cur:
        return None
    candidates = ["13-13-21+Mg", "15-5-25+Mg", "20-10-10+Mg", "12-12-17+2Mg"]
    scored = []
    for c in candidates:
        r = _fetch_fert_by_code(cur, c)
        if not r:
            continue
        npk = _parse_npk(c)
        score = 0
        if npk and prefer:
            n, p, k = npk
            if "N" in prefer: score += n
            if "P" in prefer: score += p
            if "K" in prefer: score += k
        scored.append((score, r))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]

def _combine(reason: str, *items):
    """
    รวมหลายสูตรให้เป็นคำแนะนำเดียว
    items: dict ที่มาจาก _fetch_fert_by_code / pick_or_virtual / __virtual
    """
    items = [i for i in items if i]
    if not items:
        return __virtual("15-15-15", "Balanced", reason or "fallback")

    name = " + ".join((i.get("fert_name") or i.get("formulation") or "").strip() for i in items)
    formu = " + ".join((i.get("formulation") or i.get("fert_name") or "").strip() for i in items)
    return {
        "fert_id": items[0].get("fert_id"),
        "fert_name": name,
        "formulation": formu,
        "fert_name_th": items[0].get("fert_name_th"),
        "fert_description": items[0].get("fert_description"),
        "reason": reason or "ผสมหลายสูตร"
    }

# ========== ฟังก์ชันหลัก: เลือกปุ๋ยที่เหมาะสม ==========
def _select_overall_fertilizer(cur, agg: dict):
    """
    เลือกปุ๋ยตามธาตุที่ขาดจาก agg = { 'N': {'max_conf':..., 'max_sev':...}, ... }
    ลำดับ: NPK+Mg > NPK > ธาตุเดียว > Mg-ร่วม > คู่ธาตุ > เน้น dominant > balanced
    - ตัดสูตรเดี่ยว (มีเลข 0 สองตำแหน่ง) เช่น 0-0-50, 0-46-0, 46-0-0, 21-0-0 ออกทั้งหมด
    - อนุญาต MgSO4 (Epsom Salt) สำหรับแมกนีเซียมเท่านั้น
    - ถ้าไม่มีในคลัง ให้ virtual เพื่อไม่ตกไป 15-15-15 ตลอด
    """
    def _is_single_salt(code: str) -> bool:
        """True ถ้าเป็นสูตรเดี่ยว (เลข 0 สองตำแหน่ง) เช่น X-0-0 / 0-Y-0 / 0-0-Z"""
        try:
            a, b, c = (int(x) for x in code.split('+')[0].split('-')[:3])
            zeros = sum(v == 0 for v in (a, b, c))
            return zeros >= 2
        except Exception:
            return False

    def _safe_fetch(code: str):
        """ดึงจากคลัง แต่กันสูตรเดี่ยว หากเป็น MgSO4 ให้ผ่าน"""
        if code.upper() == "MGSO4":
            return _fetch_fert_by_code(cur, code) if cur else None
        if _is_single_salt(code):
            return None
        return _fetch_fert_by_code(cur, code) if cur else None

    def pick_or_virtual(cur, code, name, reason=None):
        r = _safe_fetch(code)
        if r:
            if reason: r = {**r, "reason": reason}
            return r
        return __virtual(code, name, reason or "virtual")

    aggU = { (k or '').upper(): v for k, v in (agg or {}).items() if k }
    if not aggU:
        for code in ("15-15-15", "16-16-16", "20-20-20"):
            r = _safe_fetch(code)
            if r: return {**r, "reason": "ปุ๋ยสมดุล (empty-agg fallback)"}
        return __virtual("15-15-15", "Balanced", "ปุ๋ยสมดุล (empty-agg fallback)")

    want = set(aggU.keys())
    num_def = len(want)
    dominant = max(aggU.items(), key=lambda x: x[1].get("max_conf", 0.0))[0]

    # ---------- 1) ขาด NPK + Mg ครบ 4 ----------
    if {"N","P","K","MG"}.issubset(want):
        hit = _first_non_none(
            _safe_fetch("13-13-21+Mg"),
            _safe_fetch("15-5-25+Mg"),
            _find_best_plus_mg(cur, {"N","P","K"}) if cur else None
        )
        if hit:
            return {**hit, "reason": "ครอบคลุม NPK + Mg ในสูตรเดียว"}
        bal = pick_or_virtual(cur, "16-16-16", "Balanced")
        mg  = pick_or_virtual(cur, "MgSO4", "Epsom Salt")
        return _combine("ไม่มีสูตร +Mg ในคลัง → สมดุล + MgSO4", bal, mg)

    # ---------- 2) ธาตุเดียว ----------
    if num_def == 1:
        n = next(iter(want))
        if n == "N":
            # ตัด 46-0-0, 21-0-0 ออก → ใช้ N เด่นแบบผสม
            hit = _first_non_none(
                _safe_fetch("20-10-10"),
                _safe_fetch("25-7-7"),
                _safe_fetch("16-16-8")
            )
            return hit or __virtual("20-10-10", "N-high blend", "แนะนำไนโตรเจนสูง (สูตรผสม)")
        if n == "P":
            # ตัด 0-46-0 ออก แต่ 18-46-0 (มี N) ยังเป็นสูตรผสม (2 ช่อง ≠ 0) ให้คงไว้
            hit = _first_non_none(
                _safe_fetch("18-46-0"),
                _safe_fetch("16-20-0"),  # K=0 แต่มี N+P
                _safe_fetch("12-24-12")
            )
            return hit or __virtual("18-46-0", "DAP", "แนะนำฟอสฟอรัสสูง (สูตรผสม)")
        if n == "K":
            # ตัด 0-0-52, 0-0-50 ออก → ใช้ 13-0-46 (N+K) หรือสูตร K เด่นที่ยังเป็นผสม
            hit = _first_non_none(
                _safe_fetch("13-0-46"),
                _safe_fetch("15-5-25"),
                _safe_fetch("13-13-21")
            )
            return hit or __virtual("13-0-46", "NK blend", "แนะนำโพแทสเซียมสูง (สูตรผสม)")
        if n == "MG":
            # อนุญาต MgSO4
            return pick_or_virtual(cur, "MgSO4", "Epsom Salt", "แก้ขาดแมกนีเซียม")

    # ---------- 3) มี Mg ร่วม (ไม่ครบ NPK) ----------
    if "MG" in want and num_def < 4:
        # 3.1 N + K + Mg
        if want == {"N","K","MG"}:
            kmg = _first_non_none(
                _safe_fetch("15-5-25+Mg"),
                _find_best_plus_mg(cur, {"K","N"}) if cur else None
            )
            urea_like = _safe_fetch("20-10-10") or __virtual("20-10-10", "N-high blend")
            if kmg:
                return _combine("ขาด N,K ร่วม Mg → K+Mg เสริม N", kmg, urea_like)
            k_mix = _first_non_none(
                _safe_fetch("13-0-46"),
                _safe_fetch("15-5-25"),
                _safe_fetch("13-13-21"),
                __virtual("13-0-46", "NK blend")
            )
            mg = pick_or_virtual(cur, "MgSO4", "Epsom Salt")
            return _combine("ขาด N,K ร่วม Mg → K ผสม + MgSO4 + N ผสม", k_mix, mg, urea_like)

        # 3.1 N + P + Mg
        if want == {"N","P","MG"}:
            npm = _first_non_none(
                _safe_fetch("20-10-10+Mg"),
                _find_best_plus_mg(cur, {"N","P"}) if cur else None
            )
            p_mix = _first_non_none(
                _safe_fetch("18-46-0"),
                _safe_fetch("16-20-0"),
                _safe_fetch("12-24-12"),
                __virtual("18-46-0", "DAP")
            )
            if npm:
                return _combine("ขาด N,P ร่วม Mg → สูตร N+P+Mg เสริม P", npm, p_mix)
            mg = pick_or_virtual(cur, "MgSO4", "Epsom Salt")
            return _combine("ขาด N,P ร่วม Mg → P ผสม + MgSO4", p_mix, mg)

        # 3.2 คู่ธาตุเดิมมี Mg
        if want == {"K","MG"}:
            hit = _first_non_none(
                _safe_fetch("15-5-25+Mg"),
                _find_best_plus_mg(cur, {"K"}) if cur else None
            )
            if hit:
                return {**hit, "reason": "ขาด K ร่วม Mg → K สูง + Mg (ในตัว)"}
            k_mix = _first_non_none(
                _safe_fetch("13-0-46"),
                _safe_fetch("15-5-25"),
                __virtual("13-0-46", "NK blend")
            )
            mg = pick_or_virtual(cur, "MgSO4", "Epsom Salt")
            return _combine("ขาด K และ Mg → K ผสม + MgSO4", k_mix, mg)

        if {"P","K"}.issubset(want):
            hit = _first_non_none(
                _safe_fetch("13-13-21+Mg"),
                _find_best_plus_mg(cur, {"P","K"}) if cur else None
            )
            if hit:
                return {**hit, "reason": "ขาด P,K ร่วม Mg → สูตร +Mg ที่เหมาะสม"}

        if "K" in want:
            hit = _first_non_none(
                _safe_fetch("15-5-25+Mg"),
                _find_best_plus_mg(cur, {"K"}) if cur else None
            )
            if hit:
                return {**hit, "reason": "ขาด K ร่วม Mg → K สูง + Mg"}

        # ไม่พบสูตร +Mg เลย → เสริม MgSO4 แยก
        return pick_or_virtual(cur, "MgSO4", "Epsom Salt", "เสริม Mg แยก (ไม่พบสูตร +Mg ในคลัง)")

    # ---------- 4) ขาด NPK (ไม่มี Mg) ----------
    if {"N","P","K"}.issubset(want):
        for code in ("16-16-16", "15-15-15", "20-20-20", "13-13-21"):
            r = _safe_fetch(code)
            if r: return {**r, "reason": "ครอบคลุม NPK (สูตรผสม)"}

    # ---------- 5) คู่ธาตุ (ไม่มี Mg) ----------
    if num_def == 2 and "MG" not in want:
        if want == {"P","K"}:
            hit = _first_non_none(
                _safe_fetch("13-13-21"),
                _safe_fetch("8-24-24")
            )
            return (hit and {**hit, "reason": "ขาด P และ K (สูตรผสม)"}) or \
                   __virtual("13-13-21", "PK blend", "ขาด P และ K")
        if want == {"N","P"}:
            hit = _first_non_none(
                _safe_fetch("20-10-10"),
                _safe_fetch("16-20-0"),
                _safe_fetch("18-46-0")  # ยังถือเป็นผสม (N,P ทั้งคู่ > 0)
            )
            return (hit and {**hit, "reason": "ขาด N และ P (สูตรผสม)"}) or \
                   __virtual("20-10-10", "NP blend", "ขาด N และ P")
        if want == {"N","K"}:
            hit = _first_non_none(
                _safe_fetch("15-5-25"),
                _safe_fetch("13-13-21"),
                _safe_fetch("13-0-46")
            )
            return (hit and {**hit, "reason": "ขาด N และ K (สูตรผสม)"}) or \
                   __virtual("15-5-25", "NK blend", "ขาด N และ K")

    # ---------- Fallback เน้นธาตุโดดเด่น ----------
    if dominant in {"N","P","K"}:
        best = _pick_best_by_component(cur, dominant) if cur else None
        if best and not _is_single_salt(best.get("code","")):
            return {**best, "reason": f"เน้นแก้ {dominant} (ความเชื่อมั่นสูงสุด, สูตรผสม)"}

    # ---------- Fallback สุดท้าย ----------
    for code in ("15-15-15", "16-16-16", "20-20-20"):
        r = _safe_fetch(code)
        if r:
            return {**r, "reason": "ปุ๋ยสมดุล (fallback)"}
    return __virtual("15-15-15", "Balanced", "ปุ๋ยสมดุล (fallback)")


def _upsert_single_recommendation(cur, inspection_id: int, agg: dict):
    choice = _select_overall_fertilizer(cur, agg) or __virtual("15-15-15", "Balanced")
    fert_id = choice.get("fert_id")
    formu   = (choice.get("formulation") or "").strip()
    fname   = (choice.get("fert_name") or "").strip()
    reason  = (choice.get("reason") or "").strip()

    dom_code = max(((k or '').upper(), v.get("max_conf", 0.0)) for k, v in (agg or {}).items())[0]

    cur.execute("DELETE FROM zone_inspection_recommendation WHERE inspection_id=%s", (inspection_id,))

    base = f"แนะนำปุ๋ยสูตร {formu}" if formu else f"แนะนำ {fname}"
    rec_text = f"{base} • {reason}" if reason else base

    cur.execute("""
        INSERT INTO zone_inspection_recommendation(
            inspection_id, fertilizer_id, nutrient_code,
            recommendation_text, rate_per_area, application_method,
            status, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    """, (inspection_id, fert_id, dom_code, rec_text, None, None, "suggested"))

# ---------- helper: extract code from text ----------
_NPK_OR_MG_RE = re.compile(r'(\d{1,2}-\d{1,2}-\d{1,2}(?:\+\s*Mg)?)|MgSO4', re.IGNORECASE)
def _extract_code_from_text(s: str) -> str | None:
    if not s:
        return None
    m = _NPK_OR_MG_RE.search(s)
    return m.group(0) if m else None

# ========== API ROUTES ==========

# ---------- start round ----------
@inspection_bp.route("/start", methods=["POST", "GET", "OPTIONS"])
def start_round():
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    if request.method == "GET":
        field_id = request.args.get("field_id", type=int)
        zone_id  = request.args.get("zone_id", type=int)
        notes    = (request.args.get("notes") or "").strip() or None
        method   = (request.args.get("method") or "manual").strip().lower()
        new_round = (request.args.get("new_round") or "").strip().lower() in ("1", "true", "yes")
    else:
        body = _ensure_json()
        field_id = body.get("field_id")
        zone_id  = body.get("zone_id")
        notes    = (body.get("notes") or "").strip() or None
        method   = (body.get("method") or "manual").strip().lower()
        nr = body.get("new_round")
        if nr is None:
            qv = (request.args.get("new_round") or "").strip().lower()
            new_round = qv in ("1", "true", "yes")
        else:
            new_round = bool(nr)

    if not field_id or not zone_id:
        return jsonify({"success": False, "error": "missing_params"}), 400

    if method not in ("manual", "drone", "satellite"):
        method = "manual"

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500

    try:
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT user_id FROM field WHERE field_id=%s", (field_id,))
        owner = cur.fetchone()
        if not owner:
            return jsonify({"success": False, "error": "field_not_found"}), 404
        if str(owner["user_id"]) != str(uid):
            return jsonify({"success": False, "error": "forbidden"}), 403

        cur.execute("""
            SELECT inspection_id, round_no
            FROM zone_inspection
            WHERE field_id=%s AND zone_id=%s AND status=%s
            ORDER BY inspection_id DESC LIMIT 1
        """, (field_id, zone_id, STATUS_OPEN))
        exist = cur.fetchone()

        if exist and not new_round:
            return jsonify({
                "success": True, "idempotent": True,
                "inspection_id": exist["inspection_id"], "round_no": exist["round_no"]
            })

        if exist and new_round:
            cur.execute("""
                UPDATE zone_inspection
                   SET status=%s
                 WHERE inspection_id=%s AND status=%s
            """, (STATUS_DONE, exist["inspection_id"], STATUS_OPEN))
            conn.commit()

        cur.execute("""
            SELECT MAX(round_no) AS max_round
            FROM zone_inspection
            WHERE field_id=%s AND zone_id=%s
        """, (field_id, zone_id))
        maxr = cur.fetchone()["max_round"] or 0
        next_round = int(maxr) + 1

        cur.execute("""
            INSERT INTO zone_inspection(
                field_id, zone_id, round_no, inspected_at,
                inspector_user_id, method, status, notes
            ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s)
        """, (field_id, zone_id, next_round, uid, method, STATUS_OPEN, notes))
        conn.commit()
        new_id = cur.lastrowid

        return jsonify({
            "success": True, "idempotent": False,
            "inspection_id": new_id, "round_no": next_round
        })

    except Error as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- upload images ----------
@inspection_bp.route("/<int:inspection_id>/images", methods=["POST", "OPTIONS"])
def upload_images(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    files = request.files.getlist("images")
    if not files:
        files = list(request.files.values())

    if not files:
        return jsonify({"success": False, "error": "no_files", "message": "No files in multipart/form-data"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500

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
            return jsonify({"success": False, "error": "not_found"}), 404
        if str(it["user_id"]) != str(uid):
            return jsonify({"success": False, "error": "forbidden"}), 403
        if it["status"] != STATUS_OPEN:
            return jsonify({"success": False, "error": "closed_round"}), 400

        cur.execute("SELECT COUNT(*) AS c FROM zone_inspection_image WHERE inspection_id=%s", (inspection_id,))
        already = cur.fetchone()["c"] or 0
        remain = max(0, MAX_IMAGES_PER_ROUND - already)
        if remain == 0:
            return jsonify({"success": False, "error": "quota_full", "exist": already, "max": MAX_IMAGES_PER_ROUND}), 400

        saved = []
        root = _uploads_root()
        folder = root / "inspections" / str(inspection_id)
        _ensure_dir(folder)

        will_save = files[:remain]
        skipped = max(0, len(files) - len(will_save))

        for f in will_save:
            filename = f.filename or ""
            if not filename or not _ext_ok(filename):
                return jsonify({"success": False, "error": "unsupported_media"}), 415

            try:
                f.seek(0, os.SEEK_END); size = f.tell(); f.seek(0)
            except Exception:
                size = None
            if size is not None and size > MAX_FILE_BYTES:
                return jsonify({"success": False, "error": "payload_too_large"}), 413

            ext = filename.rsplit(".", 1)[-1].lower()
            ts  = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            safe_name = f"{inspection_id}_{ts}.{ext}"
            path = folder / safe_name
            f.save(str(path))

            rel_path = str(path.relative_to(root)).replace("\\", "/")
            meta = {"original_name": filename, "saved_name": safe_name, "saved_at_utc": ts}
            cur.execute("""
                INSERT INTO zone_inspection_image(inspection_id, image_path, captured_at, meta)
                VALUES(%s, %s, NOW(), %s)
            """, (inspection_id, rel_path, json.dumps(meta, ensure_ascii=False)))
            saved.append({"file": safe_name, "path": rel_path})

        conn.commit()
        quota_remain = MAX_IMAGES_PER_ROUND - (already + len(saved))
        return jsonify({"success": True, "saved": saved, "quota_remain": quota_remain, "skipped": skipped})

    except Error as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- inspection detail ----------
@inspection_bp.route("/<int:inspection_id>", methods=["GET", "OPTIONS"])
def get_detail(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500

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
            return jsonify({"success": False, "error": "not_found"}), 404
        if str(head["user_id"]) != str(uid):
            return jsonify({"success": False, "error": "forbidden"}), 403

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
        quota = {"max": MAX_IMAGES_PER_ROUND, "used": used, "remain": max(0, MAX_IMAGES_PER_ROUND - used)}

        return jsonify({"success": True, "data": {
            "inspection": head, "images": images, "findings": findings, "warnings": [], "quota": quota
        }})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- analyze ----------
@inspection_bp.route("/<int:inspection_id>/analyze", methods=["POST", "GET", "OPTIONS"])
def run_analyze(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
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
            return jsonify({"success": False, "error": "not_found"}), 404
        if str(it["user_id"]) != str(uid):
            return jsonify({"success": False, "error": "forbidden"}), 403

        cur.execute("SELECT image_path FROM zone_inspection_image WHERE inspection_id=%s", (inspection_id,))
        imgs = [r["image_path"] for r in cur.fetchall()]
        if not imgs:
            return jsonify({"success": False, "error": "no_images"}), 400

        root = _uploads_root()
        abs_paths = [str((root / rel).resolve()) for rel in imgs]

        results = predict_on_paths(abs_paths, conf_thres=0.25)

        valid_codes = _load_valid_codes()
        CLASS_ALIASES = {
            "Magnesium":  "Mg",
            "Nitrogen":   "N",
            "Phosphorus": "P",
            "Potassium":  "K",
        }

        def severity_from_conf(conf_pct: float) -> str:
            if conf_pct >= 85: return "severe"
            if conf_pct >= 65: return "moderate"
            return "mild"

        agg = {}
        skipped_normal = 0
        unknown_labels = []
        saw_any_pred = False
        saw_any_non_normal = False

        for item in results:
            for p in (item.get("preds") or []):
                saw_any_pred = True
                raw_label = str(p.get("class", "")).strip()
                label_for_code = CLASS_ALIASES.get(raw_label, raw_label)
                code = _to_nutrient_code(label_for_code, valid_codes)
                if code is None:
                    if raw_label.lower() in NORMAL_TOKENS:
                        skipped_normal += 1
                    else:
                        unknown_labels.append(raw_label)
                    continue
                saw_any_non_normal = True
                conf_pct = float(p.get("confidence") or 0.0) * 100.0
                sev = severity_from_conf(conf_pct)
                if code not in agg or conf_pct > agg[code]["max_conf"]:
                    agg[code] = {"max_conf": conf_pct, "max_sev": sev}

        cur.execute("DELETE FROM zone_inspection_finding WHERE inspection_id=%s", (inspection_id,))

        is_all_normal = (saw_any_pred and not saw_any_non_normal)

        if not agg:
            conn.commit()
            return jsonify({
                "success": True,
                "warnings": [], "results": results, "findings": [],
                "skipped_normal": skipped_normal, "unknown_labels": unknown_labels,
                "is_all_normal": is_all_normal,
                "normal_message": "ผลการตรวจ: ใบปกติ ไม่พบอาการขาดธาตุ" if is_all_normal else None
            })

        findings = []
        for code, stat in agg.items():
            findings.append({
                "nutrient_code": code,
                "severity": stat["max_sev"],
                "confidence": round(stat["max_conf"], 2),
                "notes": None
            })
            cur.execute("""
                INSERT INTO zone_inspection_finding(inspection_id, nutrient_code, severity, confidence, notes)
                VALUES(%s, %s, %s, %s, %s)
            """, (inspection_id, code, stat["max_sev"], round(stat["max_conf"], 2), None))

        # upsert recommendation (online)
        _upsert_single_recommendation(cur, inspection_id, agg)

        conn.commit()

        # แนบ offline suggestion เผื่อ UI ต้องการโชว์ทันที
        offline_choice = _select_overall_fertilizer(cur, agg) or __virtual("15-15-15", "Balanced")

        return jsonify({
            "success": True,
            "warnings": [], "results": results, "findings": findings,
            "skipped_normal": skipped_normal, "unknown_labels": unknown_labels,
            "is_all_normal": False, "normal_message": None,
            "offline_recommendation": {
                "formulation": offline_choice.get("formulation"),
                "fert_name":  offline_choice.get("fert_name"),
                "reason":     offline_choice.get("reason")
            }
        })

    except Error as e:
        # หาก DB ผิดพลาด ให้ยังคืนผลพร้อมสูตรแบบ offline ไม่พึ่ง DB
        try:
            offline_choice = _select_overall_fertilizer(None, agg) if 'agg' in locals() else None
            return jsonify({
                "success": True,
                "warnings": ["db_error_upserting_recommendation", str(e)],
                "results": results if 'results' in locals() else [],
                "findings": findings if 'findings' in locals() else [],
                "skipped_normal": skipped_normal if 'skipped_normal' in locals() else 0,
                "unknown_labels": unknown_labels if 'unknown_labels' in locals() else [],
                "is_all_normal": False,
                "normal_message": None,
                "offline_recommendation": (None if not offline_choice else {
                    "formulation": offline_choice.get("formulation"),
                    "fert_name":  offline_choice.get("fert_name"),
                    "reason":     offline_choice.get("reason") or "offline fallback (no database)"
                })
            })
        except Exception:
            return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- recommendations: list ----------
@inspection_bp.route("/<int:inspection_id>/recommendations", methods=["GET", "OPTIONS"])
def get_recommendations(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    conn = get_db_connection()
    if not conn:
        # ไม่มี DB ก็ส่งลิสต์ว่าง (UI ยังสามารถอ่าน offline_recommendation จาก /analyze ได้)
        return jsonify({"success": True, "data": [], "count": 0})

    try:
        cur = conn.cursor(dictionary=True)

        # check ownership
        cur.execute("""
            SELECT f.user_id
            FROM zone_inspection zi
            JOIN field f ON zi.field_id = f.field_id
            WHERE zi.inspection_id = %s
        """, (inspection_id,))
        own = cur.fetchone()
        if not own:
            return jsonify({"success": False, "error": "not_found"}), 404
        if str(own["user_id"]) != str(uid):
            return jsonify({"success": False, "error": "forbidden"}), 403

        sch = _detect_fert_schema(cur)
        fert_id_col   = sch["id_col"]
        fert_name_col = sch["name_col"]
        code_col      = sch["code_col"]
        name_th_col   = sch["name_th_col"]
        desc_col      = sch["desc_col"]

        cur.execute(f"""
            SELECT
                r.recommendation_id, r.inspection_id, r.fertilizer_id, r.nutrient_code,
                r.recommendation_text, r.rate_per_area, r.application_method,
                r.status, r.applied_date, r.created_at,

                fert.{fert_name_col} AS fert_name,
                fert.{code_col}      AS formulation,
                {('fert.'+name_th_col) if name_th_col else 'NULL'} AS fert_name_th,
                {('fert.'+desc_col)    if desc_col    else 'NULL'} AS fert_description,

                nd.nutrient_name AS nutrient_name_th
            FROM zone_inspection_recommendation r
            LEFT JOIN fertilizer fert ON r.fertilizer_id = fert.{fert_id_col}
            LEFT JOIN nutrient_deficiency nd ON r.nutrient_code = nd.nutrient_code
            WHERE r.inspection_id = %s
            ORDER BY r.recommendation_id
        """, (inspection_id,))
        rows = cur.fetchall() or []

        # เติม code (formulation) จากข้อความ ถ้า virtual
        for row in rows:
            if not row.get("formulation"):
                row["formulation"] = _extract_code_from_text(row.get("recommendation_text", ""))

        return jsonify({"success": True, "data": rows, "count": len(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except Exception:
            pass

# ---------- recommendations: patch ----------
@inspection_bp.route("/recommendations/<int:rec_id>", methods=["PATCH", "PUT", "OPTIONS"])
def patch_recommendation(rec_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    body = _ensure_json()
    status = (body.get("status") or "").strip().lower()
    applied_date = body.get("applied_date")

    if status not in ("suggested", "applied", "skipped"):
        return jsonify({"success": False, "error": "bad_status"}), 400

    if status == "applied":
        if applied_date:
            d = _parse_yyyy_mm_dd(applied_date)
            if not d:
                return jsonify({"success": False, "error": "bad_date_format"}), 400
        else:
            applied_date = date.today().strftime("%Y-%m-%d")
    else:
        applied_date = None

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
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
            return jsonify({"success": False, "error": "not_found"}), 404
        if str(row[0]) != str(uid):
            return jsonify({"success": False, "error": "forbidden"}), 403

        cur.execute("""
            UPDATE zone_inspection_recommendation
               SET status = %s, applied_date = %s
             WHERE recommendation_id = %s
        """, (status, applied_date, rec_id))
        conn.commit()
        return jsonify({"success": True})
    except Error as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- backfill ----------
@inspection_bp.route("/<int:inspection_id>/recommendations/backfill", methods=["POST", "OPTIONS"])
def backfill_recommendations(inspection_id):
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
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
            return jsonify({"success": False, "error": "not_found"}), 404
        if str(own["user_id"]) != str(uid):
            return jsonify({"success": False, "error": "forbidden"}), 403

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
        agg = {r["nutrient_code"]: {"max_conf": float(r["max_conf"] or 0.0),
                                    "max_sev": r["max_sev"] or "moderate"} for r in agg_rows}

        _upsert_single_recommendation(cur, inspection_id, agg)

        conn.commit()
        return jsonify({"success": True, "updated_codes": list(agg.keys())})
    except Error as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- history ----------
@inspection_bp.route("/history", methods=["GET", "OPTIONS"], strict_slashes=False)
@inspection_bp.route("/history/", methods=["GET"], strict_slashes=False)
def inspection_history():
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    group = (request.args.get("group") or "month").lower()
    if group not in ("month", "year"):
        group = "month"

    field_id = request.args.get("field_id", type=int)
    zone_id  = request.args.get("zone_id", type=int)
    start_dt, end_dt = _normalize_range(request.args.get("from"), request.args.get("to"))
    bucket_sql = "DATE_FORMAT(zi.inspected_at, '%Y-%m')" if group == "month" else "DATE_FORMAT(zi.inspected_at, '%Y')"

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
    try:
        cur = conn.cursor(dictionary=True)

        where = ["f.user_id = %s"]; params = [uid]
        if start_dt:
            where.append("zi.inspected_at >= %s"); params.append(start_dt.strftime("%Y-%m-%d %H:%M:%S"))
        if end_dt:
            where.append("zi.inspected_at <= %s"); params.append(end_dt.strftime("%Y-%m-%d %H:%M:%S"))
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
        fcounts = {r["bucket"]: r["findings"] for r in cur.fetchall()}

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
            b["findings"] = fcounts.get(b["bucket"], 0)

        return jsonify({"success": True, "group": group, "buckets": buckets, "top_nutrients": top})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass

# ---------- list ----------
@inspection_bp.route("", methods=["GET", "OPTIONS"], strict_slashes=False)
@inspection_bp.route("/", methods=["GET"], strict_slashes=False)
def list_inspections():
    user, err = _authz()
    if err: return err
    uid = _user_id(user)
    if uid is None:
        return jsonify({"success": False, "error": "unauthorized"}), 401

    page = max(1, int(request.args.get("page", 1)))
    size = min(100, max(1, int(request.args.get("page_size", 20))))
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    field_id = request.args.get("field_id", type=int)
    zone_id = request.args.get("zone_id", type=int)

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "error": "db_failed"}), 500
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
        total = cur.fetchone()["c"]

        cur.execute(f"""
            SELECT zi.inspection_id, zi.field_id, zi.zone_id,
                   zi.round_no, zi.inspected_at, zi.status, zi.notes, zi.method,
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

        return jsonify({"success": True, "data": rows, "page": page, "page_size": size, "total": total})
    except Error as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        try:
            cur.close(); conn.close()
        except:
            pass
