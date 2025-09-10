# utils/db.py
import os
import hashlib
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
from contextlib import contextmanager

try:
    from flask import current_app, has_app_context
except Exception:
    # เผื่อใช้ไฟล์นี้นอก Flask
    current_app = None
    def has_app_context(): return False

# ====== ENV CONFIG ======
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "dbcocoa")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

# ====== LOGGER ======
def _log(level: str, msg: str):
    if has_app_context() and current_app:
        getattr(current_app.logger, level.lower(), current_app.logger.info)(msg)
    else:
        print(f"[DB:{level.upper()}] {msg}")

# ====== CONNECTION POOL ======
_pool: pooling.MySQLConnectionPool | None = None

def _init_pool():
    global _pool
    if _pool is not None:
        return
    cfg = dict(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        autocommit=False,    # ให้โค้ดฝั่ง route เป็นคน commit/rollback
        use_pure=True,
    )
    _pool = pooling.MySQLConnectionPool(
        pool_name="dbcocoa_pool",
        pool_size=DB_POOL_SIZE,
        **cfg
    )
    _log("info", f"MySQL pool created: host={DB_HOST}:{DB_PORT}, db={DB_NAME}, size={DB_POOL_SIZE}")

def _ensure_utf8mb4(conn: mysql.connector.MySQLConnection):
    # บางเวอร์ชันมี set_charset_collation, บางเวอร์ชันต้อง SET NAMES
    try:
        conn.set_charset_collation("utf8mb4", "utf8mb4_unicode_ci")
    except Exception:
        try:
            cur = conn.cursor()
            cur.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute("SET character_set_connection = 'utf8mb4'")
            cur.execute("SET collation_connection = 'utf8mb4_unicode_ci'")
            cur.close()
        except Exception as e:
            _log("warning", f"Cannot enforce utf8mb4 on connection: {e}")

def get_db_connection() -> mysql.connector.MySQLConnection | None:
    """คืน MySQL connection 1 ตัวจาก pool (หรือสร้างเดี่ยวถ้า pool ใช้ไม่ได้)"""
    try:
        _init_pool()
        conn = _pool.get_connection() if _pool else mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME, autocommit=False, use_pure=True
        )
        _ensure_utf8mb4(conn)
        return conn
    except Error as e:
        _log("error", f"เกิดข้อผิดพลาดในการเชื่อมต่อ MySQL: {getattr(e,'msg',str(e))}")
        return None

@contextmanager
def db_cursor(dict: bool = True, commit: bool = True):
    """
    ใช้แบบ:
    with db_cursor(dict=True) as (cur, conn):
        cur.execute("SELECT ...")
        rows = cur.fetchall()
    """
    conn = get_db_connection()
    if conn is None:
        # ทำให้ผู้เรียกตรวจจับได้
        raise RuntimeError("Cannot get MySQL connection")

    cur = conn.cursor(dictionary=dict)
    try:
        yield cur, conn
        if commit:
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

# ====== HELPERS ======
def hash_password(password: str) -> str:
    """เข้ารหัสรหัสผ่านด้วย SHA-256 (แนะนำให้ไปใช้ bcrypt/argon2 สำหรับ production)"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def allowed_file(filename: str) -> bool:
    """ตรวจสอบนามสกุลไฟล์ที่อนุญาต"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
