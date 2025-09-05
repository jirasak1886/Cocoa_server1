import mysql.connector
from mysql.connector import Error
from flask import current_app
import hashlib

def get_db_connection():
    """สร้างการเชื่อมต่อกับ MySQL database"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="dbcocoa"
        )
        if connection.is_connected():
            return connection
    except Error as e:
        current_app.logger.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ MySQL: {e}")
        return None

def hash_password(password):
    """เข้ารหัสรหัสผ่านด้วย SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def allowed_file(filename):
    """ตรวจสอบนามสกุลไฟล์ที่อนุญาต"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS