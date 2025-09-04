from flask import Blueprint, request, jsonify, current_app
from mysql.connector import Error
from config.database import get_db_connection
import jwt

field_zone_bp = Blueprint('field_zone', __name__)

# ==================== HELPER FUNCTIONS ====================

def get_current_user():
    """ดึงข้อมูลผู้ใช้จาก JWT token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        return None

def require_auth():
    """ตรวจสอบ authentication และคืนค่า user หรือ error response"""
    if request.method == "OPTIONS":
        # ยกเว้น preflight ไม่ต้องเช็ค token
        return {"system": "preflight"}, None, None
    
    user = get_current_user()
    if not user:
        return None, jsonify({
            'success': False,
            'error': 'unauthorized',
            'message': 'Authentication required'
        }), 401
    return user, None, None

# ==================== FIELDS ROUTES ====================

@field_zone_bp.route('/fields', methods=['GET'])
def get_fields():
    """API: ดึงรายชื่อแปลงของผู้ใช้ (ตามสคีมา table: field)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        # ไม่มีคอลัมน์ latitude/longitude ใน table field ตามสคีมาใหม่
        cursor.execute("""
            SELECT field_id, field_name, size_square_meter, created_at
            FROM field
            WHERE user_id = %s
            ORDER BY field_name
        """, (user['user_id'],))
        fields = cursor.fetchall()

        # แนบจำนวนจุด (vertex) ของแต่ละแปลง (optional)
        if fields:
            field_ids = [f['field_id'] for f in fields]
            format_strings = ','.join(['%s'] * len(field_ids))
            cursor.execute(f"""
                SELECT field_id, COUNT(*) AS vertex_count
                FROM field_point
                WHERE field_id IN ({format_strings})
                GROUP BY field_id
            """, field_ids)
            vc_map = {row['field_id']: row['vertex_count'] for row in cursor.fetchall()}
            for f in fields:
                f['vertex_count'] = vc_map.get(f['field_id'], 0)

        return jsonify({'success': True, 'data': fields})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@field_zone_bp.route('/fields/<int:field_id>/zones', methods=['GET'])
def get_zones(field_id):
    """API: ดึงข้อมูลโซนในแปลง (table: zone)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        # ตรวจสอบว่าแปลงนี้เป็นของผู้ใช้
        cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
        field_row = cursor.fetchone()
        if not field_row or field_row['user_id'] != user['user_id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        cursor.execute("""
            SELECT z.zone_id, z.zone_name, z.num_trees,
                   (SELECT COUNT(*) FROM history WHERE zone_id = z.zone_id) AS inspection_count
            FROM zone z
            WHERE z.field_id = %s
            ORDER BY z.zone_name
        """, (field_id,))
        zones = cursor.fetchall()
        return jsonify({'success': True, 'data': zones})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@field_zone_bp.route('/fields', methods=['POST'])
def create_field():
    """API: สร้างแปลงใหม่ (รับ vertices หลายจุด → บันทึกที่ field_point)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json() if request.is_json else request.form
        field_name = data.get('field_name')
        size_square_meter = data.get('size_square_meter')
        vertices = data.get('vertices', [])  # list ของ {latitude/lat, longitude/lng}

        if not field_name or not size_square_meter:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO field (field_name, size_square_meter, user_id)
                VALUES (%s, %s, %s)
            """, (field_name, size_square_meter, user['user_id']))
            # จากนั้น loop บันทึก vertices -> field_point(field_id, latitude, longitude, point_order)

            conn.commit()
            field_id = cursor.lastrowid

            # บันทึกหลายพิกัดของแปลง (ถ้ามี) → field_point(point_order)
            if isinstance(vertices, list) and vertices:
                vals = []
                order = 1
                for v in vertices:
                    lat = v.get('latitude') or v.get('lat')
                    lng = v.get('longitude') or v.get('lng')
                    if lat is None or lng is None:
                        continue
                    vals.append((field_id, float(lat), float(lng), order))
                    order += 1
                if vals:
                    cursor.executemany("""
                        INSERT INTO field_point (field_id, latitude, longitude, point_order)
                        VALUES (%s, %s, %s, %s)
                    """, vals)
                    conn.commit()

            return jsonify({'success': True, 'field_id': field_id, 'message': 'สร้างแปลงสำเร็จ'})
        except Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/fields/<int:field_id>', methods=['GET'])
def get_field_details(field_id):
    """API: ดึงรายละเอียดแปลง + จุด field_point"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT field_id, field_name, size_square_meter, created_at
            FROM field
            WHERE field_id = %s AND user_id = %s
        """, (field_id, user['user_id']))
        field_row = cursor.fetchone()
        if not field_row:
            return jsonify({'success': False, 'error': 'Field not found'}), 404

        cursor.execute("""
            SELECT point_id, point_order, latitude, longitude
            FROM field_point
            WHERE field_id = %s
            ORDER BY point_order ASC
        """, (field_id,))
        field_row['vertices'] = cursor.fetchall()

        return jsonify({'success': True, 'data': field_row})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@field_zone_bp.route('/fields/<int:field_id>', methods=['PUT'])
def update_field(field_id):
    """API: อัปเดตแปลง (แทนที่ vertices ทั้งชุด)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        field_name = data.get('field_name')
        size_square_meter = data.get('size_square_meter')
        vertices = data.get('vertices', [])  # list

        if not field_name or not size_square_meter:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()

            # ตรวจสิทธิ์
            cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
            owner = cursor.fetchone()
            if not owner or owner[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงแปลงนี้'}), 403

            cursor.execute("""
                UPDATE field 
                SET field_name = %s, size_square_meter = %s
                WHERE field_id = %s
            """, (field_name, size_square_meter, field_id))
            conn.commit()

            # แทนที่ vertices
            cursor.execute("DELETE FROM field_point WHERE field_id = %s", (field_id,))
            if isinstance(vertices, list) and vertices:
                vals = []
                order = 1
                for v in vertices:
                    lat = v.get('latitude') or v.get('lat')
                    lng = v.get('longitude') or v.get('lng')
                    if lat is None or lng is None:
                        continue
                    vals.append((field_id, float(lat), float(lng), order))
                    order += 1
                if vals:
                    cursor.executemany("""
                        INSERT INTO field_point (field_id, latitude, longitude, point_order)
                        VALUES (%s, %s, %s, %s)
                    """, vals)
            conn.commit()

            return jsonify({'success': True, 'message': 'อัปเดตแปลงสำเร็จ'})
        except Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@field_zone_bp.route('/fields/<int:field_id>', methods=['DELETE'])
def delete_field(field_id):
    """API: ลบแปลง (กันไม่ให้ลบถ้ายังมีโซนอยู่)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        # ตรวจสิทธิ์
        cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
        owner = cursor.fetchone()
        if not owner or owner[0] != user['user_id']:
            return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงแปลงนี้'}), 403

        # กันลบถ้ามีโซน
        cursor.execute("SELECT COUNT(*) FROM zone WHERE field_id = %s", (field_id,))
        zone_count = cursor.fetchone()[0]
        if zone_count > 0:
            return jsonify({'success': False, 'error': 'ไม่สามารถลบแปลงที่มีโซนอยู่ได้ กรุณาลบโซนก่อน'}), 400

        cursor.execute("DELETE FROM field WHERE field_id = %s", (field_id,))
        conn.commit()

        return jsonify({'success': True, 'message': 'ลบแปลงสำเร็จ'})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ==================== ZONES ROUTES ====================

@field_zone_bp.route('/zones', methods=['POST'])
def create_zone():
    """API: สร้างโซนใหม่ (รับ marks หลายรายการได้)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json() if request.is_json else request.form
        field_id = data.get('field_id')
        zone_name = data.get('zone_name')
        num_trees = data.get('num_trees')
        marks = data.get('marks', [])  # list ของ {tree_no, latitude, longitude}

        if not field_id or not zone_name:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

        # ถ้ามี marks → ใช้จำนวน marks เป็น num_trees
        if isinstance(marks, list) and marks:
            num_trees = len(marks)
        if num_trees is None:
            num_trees = 0
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()

            # ตรวจสิทธิ์เข้าถึง field
            cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
            owner = cursor.fetchone()
            if not owner or owner[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงแปลงนี้'}), 403

            # บันทึกโซน (schema zone ไม่มี lat/lng)
            cursor.execute("""
                INSERT INTO zone (zone_name, num_trees, field_id)
                VALUES (%s, %s, %s)
            """, (zone_name, num_trees, field_id))
            conn.commit()
            zone_id = cursor.lastrowid

            # เพิ่ม marks (ถ้ามี)
            inserted = 0
            if isinstance(marks, list) and marks:
                vals = []
                for i, m in enumerate(marks, start=1):
                    tn = m.get('tree_no', i)
                    lat = m.get('latitude')
                    lng = m.get('longitude')
                    if lat is None or lng is None:
                        continue
                    vals.append((zone_id, int(tn), float(lat), float(lng)))
                if vals:
                    cursor.executemany("""
                        INSERT INTO mark_zone (zone_id, tree_no, latitude, longitude)
                        VALUES (%s, %s, %s, %s)
                    """, vals)
                    conn.commit()
                    inserted = len(vals)

                # sync num_trees
                cursor.execute("SELECT COUNT(*) FROM mark_zone WHERE zone_id = %s", (zone_id,))
                count = cursor.fetchone()[0]
                cursor.execute("UPDATE zone SET num_trees = %s WHERE zone_id = %s", (count, zone_id))
                conn.commit()

            return jsonify({
                'success': True,
                'zone_id': zone_id,
                'inserted_marks': inserted,
                'message': 'สร้างโซนสำเร็จ'
            })
        except Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/zones/<int:zone_id>', methods=['GET'])
def get_zone_details(zone_id):
    """API: ดึงรายละเอียดโซน"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT z.zone_id, z.zone_name, z.num_trees, z.field_id,
                   (SELECT COUNT(*) FROM history WHERE zone_id = z.zone_id) AS inspection_count
            FROM zone z
            JOIN field f ON z.field_id = f.field_id
            WHERE z.zone_id = %s AND f.user_id = %s
        """, (zone_id, user['user_id']))
        zone_row = cursor.fetchone()
        if not zone_row:
            return jsonify({'success': False, 'error': 'Zone not found'}), 404
        return jsonify({'success': True, 'data': zone_row})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@field_zone_bp.route('/zones/<int:zone_id>', methods=['PUT'])
def update_zone(zone_id):
    """API: อัปเดตโซน (schema zone ไม่มี lat/lng)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    try:
        data = request.get_json()
        zone_name = data.get('zone_name')
        num_trees = data.get('num_trees')

        if not zone_name or num_trees is None:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()

            # ตรวจสิทธิ์
            cursor.execute("""
                SELECT f.user_id FROM zone z
                JOIN field f ON z.field_id = f.field_id
                WHERE z.zone_id = %s
            """, (zone_id,))
            result = cursor.fetchone()
            if not result or result[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

            cursor.execute("""
                UPDATE zone 
                SET zone_name = %s, num_trees = %s
                WHERE zone_id = %s
            """, (zone_name, num_trees, zone_id))
            conn.commit()

            return jsonify({'success': True, 'message': 'อัปเดตโซนสำเร็จ'})
        except Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/zones/<int:zone_id>', methods=['DELETE'])
def delete_zone(zone_id):
    """API: ลบโซน (กันลบถ้ามี history)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()

        # ตรวจสิทธิ์
        cursor.execute("""
            SELECT f.user_id FROM zone z
            JOIN field f ON z.field_id = f.field_id
            WHERE z.zone_id = %s
        """, (zone_id,))
        result = cursor.fetchone()
        if not result or result[0] != user['user_id']:
            return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

        # กันลบถ้ามีประวัติการตรวจสอบ
        cursor.execute("SELECT COUNT(*) FROM history WHERE zone_id = %s", (zone_id,))
        history_count = cursor.fetchone()[0]
        if history_count > 0:
            return jsonify({'success': False, 'error': 'ไม่สามารถลบโซนที่มีประวัติการตรวจสอบแล้ว'}), 400

        cursor.execute("DELETE FROM zone WHERE zone_id = %s", (zone_id,))
        conn.commit()

        return jsonify({'success': True, 'message': 'ลบโซนสำเร็จ'})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ==================== MARK ZONE ROUTES ====================

@field_zone_bp.route('/zones/<int:zone_id>/marks', methods=['GET'])
def get_marks(zone_id):
    """API: ดึง mark (ต้นไม้) ของโซน (table: mark_zone)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # ตรวจสิทธิ์โซน
        cursor.execute("""
            SELECT f.user_id FROM zone z
            JOIN field f ON z.field_id = f.field_id
            WHERE z.zone_id = %s
        """, (zone_id,))
        owner = cursor.fetchone()
        if not owner or owner['user_id'] != user['user_id']:
            return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

        cursor.execute("""
            SELECT mark_id, tree_no, latitude, longitude
            FROM mark_zone
            WHERE zone_id = %s
            ORDER BY tree_no ASC, mark_id ASC
        """, (zone_id,))
        marks = cursor.fetchall()

        return jsonify({'success': True, 'data': marks, 'count': len(marks)})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@field_zone_bp.route('/zones/<int:zone_id>/marks', methods=['POST'])
def create_mark(zone_id):
    """API: เพิ่ม mark (รองรับเดี่ยว/หลายรายการ)"""
    user, error_response, status_code = require_auth()
    if error_response:
        return error_response, status_code

    try:
        data = request.get_json(force=True) or {}
        marks = data.get('marks')  # ถ้ามีคือ bulk
        tree_no = data.get('tree_no')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not marks and (tree_no is None or latitude is None or longitude is None):
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()

            # ตรวจสิทธิ์โซน
            cursor.execute("""
                SELECT f.user_id FROM zone z
                JOIN field f ON z.field_id = f.field_id
                WHERE z.zone_id = %s
            """, (zone_id,))
            owner = cursor.fetchone()
            if not owner or owner[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

            inserted = 0
            if isinstance(marks, list) and marks:
                vals = []
                for i, m in enumerate(marks, start=1):
                    tn = m.get('tree_no', i)
                    lat = m.get('latitude')
                    lng = m.get('longitude')
                    if lat is None or lng is None:
                        continue
                    vals.append((zone_id, int(tn), float(lat), float(lng)))
                if vals:
                    cursor.executemany("""
                        INSERT INTO mark_zone (zone_id, tree_no, latitude, longitude)
                        VALUES (%s, %s, %s, %s)
                    """, vals)
                    inserted = len(vals)
            else:
                cursor.execute("""
                    INSERT INTO mark_zone (zone_id, tree_no, latitude, longitude)
                    VALUES (%s, %s, %s, %s)
                """, (zone_id, tree_no, latitude, longitude))
                inserted = 1

            conn.commit()

            # sync num_trees
            cursor.execute("SELECT COUNT(*) FROM mark_zone WHERE zone_id = %s", (zone_id,))
            count = cursor.fetchone()[0]
            cursor.execute("UPDATE zone SET num_trees = %s WHERE zone_id = %s", (count, zone_id))
            conn.commit()

            return jsonify({
                'success': True,
                'inserted': inserted,
                'num_trees': count,
                'message': 'เพิ่ม mark สำเร็จ'
            })
        except Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
