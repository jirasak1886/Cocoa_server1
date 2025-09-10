# routes/field_zone.py
from flask import Blueprint, request, jsonify, current_app
from mysql.connector import Error
from config.database import get_db_connection
import jwt
import json
from decimal import Decimal, InvalidOperation

field_zone_bp = Blueprint('field_zone', __name__)

# ==================== HELPER FUNCTIONS ====================

def get_current_user():
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
    if request.method == "OPTIONS":
        return {"system": "preflight"}, None, None
    user = get_current_user()
    if not user:
        return None, jsonify({'success': False, 'error': 'unauthorized', 'message': 'Authentication required'}), 401
    return user, None, None

def num_or_none(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s == '':
        return None
    try:
        return float(Decimal(s))
    except (InvalidOperation, ValueError):
        return None

def ensure_json():
    if request.is_json:
        return request.get_json(silent=True) or {}
    data = request.form.to_dict(flat=True)
    for k in request.form:
        vals = request.form.getlist(k)
        if len(vals) > 1:
            data[k] = vals
    return data

def coerce_list_vertices(vertices):
    if vertices is None:
        return []
    if isinstance(vertices, str):
        try:
            vertices = json.loads(vertices)
        except json.JSONDecodeError:
            return []
    if not isinstance(vertices, list):
        return []
    out = []
    order = 1
    for v in vertices:
        if not isinstance(v, dict):
            continue
        lat = num_or_none(v.get('latitude') if 'latitude' in v else v.get('lat'))
        lng = num_or_none(v.get('longitude') if 'longitude' in v else v.get('lng'))
        if lat is None or lng is None:
            continue
        out.append({'latitude': lat, 'longitude': lng, 'point_order': order})
        order += 1
    return out

# ==================== FIELDS ROUTES ====================

@field_zone_bp.route('/fields', methods=['GET'])
def get_fields():
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT field_id, field_name, size_square_meter, created_at
            FROM field
            WHERE user_id = %s
            ORDER BY field_name
        """, (user['user_id'],))
        fields = cursor.fetchall()

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

@field_zone_bp.route('/fields', methods=['POST'])
def create_field():
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    try:
        data = ensure_json()
        field_name = (data.get('field_name') or '').strip()
        size_square_meter = num_or_none(data.get('size_square_meter'))
        vertices = coerce_list_vertices(data.get('vertices'))

        if not field_name or size_square_meter is None or size_square_meter <= 0:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

        conn = get_db_connection()
        if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO field (field_name, size_square_meter, user_id)
                VALUES (%s, %s, %s)
            """, (field_name, size_square_meter, user['user_id']))
            field_id = cursor.lastrowid

            if vertices:
                vals = [(field_id, v['latitude'], v['longitude'], v['point_order']) for v in vertices]
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
        current_app.logger.exception("create_field failed")
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/fields/<int:field_id>', methods=['GET'])
def get_field_details(field_id):
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

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
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    try:
        current_app.logger.debug("PUT /fields/%s RAW=%s", field_id, request.get_data(as_text=True))
        data = ensure_json()
        field_name = (data.get('field_name') or '').strip()
        size_square_meter = num_or_none(data.get('size_square_meter'))
        vertices = coerce_list_vertices(data.get('vertices', None))

        if not field_name or size_square_meter is None or size_square_meter <= 0:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

        conn = get_db_connection()
        if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()

            cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Field not found'}), 404
            if row[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงแปลงนี้'}), 403

            cursor.execute("""
                UPDATE field
                SET field_name = %s, size_square_meter = %s
                WHERE field_id = %s
            """, (field_name, size_square_meter, field_id))

            if 'vertices' in data:
                cursor.execute("DELETE FROM field_point WHERE field_id = %s", (field_id,))
                if vertices:
                    vals = [(field_id, v['latitude'], v['longitude'], v['point_order']) for v in vertices]
                    cursor.executemany("""
                        INSERT INTO field_point (field_id, latitude, longitude, point_order)
                        VALUES (%s, %s, %s, %s)
                    """, vals)

            conn.commit()
            return jsonify({'success': True, 'message': 'อัปเดตแปลงสำเร็จ'})
        except Error as e:
            conn.rollback()
            current_app.logger.exception("update_field mysql error")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        current_app.logger.exception("update_field failed (unexpected)")
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/fields/<int:field_id>', methods=['DELETE'])
def delete_field(field_id):
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({'success': False, 'error': 'Field not found'}), 404
        if owner[0] != user['user_id']:
            return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงแปลงนี้'}), 403

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

@field_zone_bp.route('/fields/<int:field_id>/zones', methods=['GET'])
def get_zones_by_field(field_id):
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
        field_row = cursor.fetchone()
        if not field_row or field_row['user_id'] != user['user_id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        cursor.execute("""
            SELECT z.zone_id, z.zone_name, z.num_trees,
                   (SELECT COUNT(*) FROM zone_inspection zi WHERE zi.zone_id = z.zone_id) AS inspection_count
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

# ==================== ZONES ROUTES ====================

@field_zone_bp.route('/zones', methods=['GET'])
def list_zones():
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    field_id = request.args.get('field_id', type=int)
    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cur = conn.cursor(dictionary=True)
        if field_id:
            cur.execute("SELECT user_id FROM field WHERE field_id=%s", (field_id,))
            owner = cur.fetchone()
            if not owner:
                return jsonify({'success': False, 'error': 'Field not found'}), 404
            if owner['user_id'] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงแปลงนี้'}), 403

            cur.execute("""
                SELECT z.zone_id, z.zone_name, z.num_trees, z.field_id,
                       (SELECT COUNT(*) FROM zone_inspection zi WHERE zi.zone_id = z.zone_id) AS inspection_count
                FROM zone z
                WHERE z.field_id = %s
                ORDER BY z.zone_name
            """, (field_id,))
        else:
            cur.execute("""
                SELECT z.zone_id, z.zone_name, z.num_trees, z.field_id,
                       (SELECT COUNT(*) FROM zone_inspection zi WHERE zi.zone_id = z.zone_id) AS inspection_count
                FROM zone z
                JOIN field f ON z.field_id = f.field_id
                WHERE f.user_id = %s
                ORDER BY z.field_id, z.zone_name
            """, (user['user_id'],))
        zones = cur.fetchall()
        return jsonify({'success': True, 'data': zones})
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cur.close()
            conn.close()

@field_zone_bp.route('/zones', methods=['POST'])
def create_zone():
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    try:
        data = ensure_json()
        field_id = num_or_none(data.get('field_id'))
        zone_name = (data.get('zone_name') or '').strip()
        num_trees = num_or_none(data.get('num_trees'))
        marks = data.get('marks', [])

        if not field_id or not zone_name:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

        if isinstance(marks, list) and marks:
            num_trees = len(marks)
        if num_trees is None:
            num_trees = 0

        conn = get_db_connection()
        if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM field WHERE field_id = %s", (field_id,))
            owner = cursor.fetchone()
            if not owner:
                return jsonify({'success': False, 'error': 'Field not found'}), 404
            if owner[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงแปลงนี้'}), 403

            cursor.execute("""
                INSERT INTO zone (zone_name, num_trees, field_id)
                VALUES (%s, %s, %s)
            """, (zone_name, int(num_trees), int(field_id)))
            zone_id = cursor.lastrowid

            inserted = 0
            if isinstance(marks, list) and marks:
                vals = []
                for i, m in enumerate(marks, start=1):
                    if not isinstance(m, dict):
                        continue
                    tn = m.get('tree_no', i)
                    lat = num_or_none(m.get('latitude'))
                    lng = num_or_none(m.get('longitude'))
                    if lat is None or lng is None:
                        continue
                    vals.append((zone_id, int(tn), lat, lng))
                if vals:
                    cursor.executemany("""
                        INSERT INTO mark_zone (zone_id, tree_no, latitude, longitude)
                        VALUES (%s, %s, %s, %s)
                    """, vals)
                    inserted = len(vals)

                cursor.execute("SELECT COUNT(*) FROM mark_zone WHERE zone_id = %s", (zone_id,))
                count = cursor.fetchone()[0]
                cursor.execute("UPDATE zone SET num_trees = %s WHERE zone_id = %s", (count, zone_id))

            conn.commit()
            return jsonify({'success': True, 'zone_id': zone_id, 'inserted_marks': inserted, 'message': 'สร้างโซนสำเร็จ'})
        except Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        current_app.logger.exception("create_zone failed")
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/zones/<int:zone_id>', methods=['GET'])
def get_zone_details(zone_id):
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT z.zone_id, z.zone_name, z.num_trees, z.field_id,
                   (SELECT COUNT(*) FROM zone_inspection zi WHERE zi.zone_id = z.zone_id) AS inspection_count
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
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    try:
        data = ensure_json()
        zone_name = (data.get('zone_name') or '').strip()
        num_trees = num_or_none(data.get('num_trees'))

        if not zone_name or num_trees is None or num_trees < 0:
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

        conn = get_db_connection()
        if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.user_id FROM zone z
                JOIN field f ON z.field_id = f.field_id
                WHERE z.zone_id = %s
            """, (zone_id,))
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Zone not found'}), 404
            if result[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

            cursor.execute("""
                UPDATE zone
                SET zone_name = %s, num_trees = %s
                WHERE zone_id = %s
            """, (zone_name, int(num_trees), zone_id))
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
        current_app.logger.exception("update_zone failed")
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/zones/<int:zone_id>', methods=['DELETE'])
def delete_zone(zone_id):
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.user_id FROM zone z
            JOIN field f ON z.field_id = f.field_id
            WHERE z.zone_id = %s
        """, (zone_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'Zone not found'}), 404
        if result[0] != user['user_id']:
            return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

        cursor.execute("SELECT COUNT(*) FROM zone_inspection WHERE zone_id = %s", (zone_id,))
        insp_count = cursor.fetchone()[0]
        if insp_count > 0:
            return jsonify({'success': False, 'error': 'ไม่สามารถลบโซนที่มีประวัติการตรวจแล้ว'}), 400

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
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)
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
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    try:
        data = ensure_json()
        marks = data.get('marks')  # list => bulk
        tree_no = data.get('tree_no')
        latitude = num_or_none(data.get('latitude'))
        longitude = num_or_none(data.get('longitude'))

        if not marks and (tree_no is None or latitude is None or longitude is None):
            return jsonify({'success': False, 'error': 'กรุณากรอกข้อมูลให้ครบถ้วน'}), 400

        conn = get_db_connection()
        if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.user_id FROM zone z
                JOIN field f ON z.field_id = f.field_id
                WHERE z.zone_id = %s
            """, (zone_id,))
            owner = cursor.fetchone()
            if not owner:
                return jsonify({'success': False, 'error': 'Zone not found'}), 404
            if owner[0] != user['user_id']:
                return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

            inserted = 0
            if isinstance(marks, list) and marks:
                vals = []
                for i, m in enumerate(marks, start=1):
                    if not isinstance(m, dict):
                        continue
                    tn = m.get('tree_no', i)
                    lat = num_or_none(m.get('latitude'))
                    lng = num_or_none(m.get('longitude'))
                    if lat is None or lng is None:
                        continue
                    vals.append((zone_id, int(tn), lat, lng))
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
                """, (zone_id, int(tree_no), latitude, longitude))
                inserted = 1

            cursor.execute("SELECT COUNT(*) FROM mark_zone WHERE zone_id = %s", (zone_id,))
            count = cursor.fetchone()[0]
            cursor.execute("UPDATE zone SET num_trees = %s WHERE zone_id = %s", (count, zone_id))

            conn.commit()
            return jsonify({'success': True, 'inserted': inserted, 'num_trees': count, 'message': 'เพิ่ม mark สำเร็จ'})
        except Error as e:
            conn.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    except Exception as e:
        current_app.logger.exception("create_mark failed")
        return jsonify({'success': False, 'error': str(e)}), 500

@field_zone_bp.route('/zones/<int:zone_id>/marks', methods=['PUT'])
def replace_marks(zone_id):
    """แทนที่ marks ทั้งชุดของโซน (สำหรับหน้าแก้ไขโซนในแอป)"""
    user, error_response, status_code = require_auth()
    if error_response: return error_response, status_code

    data = ensure_json()
    marks = data.get('marks', [])
    if not isinstance(marks, list):
        return jsonify({'success': False, 'error': 'marks ต้องเป็น list'}), 400

    conn = get_db_connection()
    if not conn: return jsonify({'success': False, 'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.user_id FROM zone z
            JOIN field f ON z.field_id = f.field_id
            WHERE z.zone_id = %s
        """, (zone_id,))
        owner = cursor.fetchone()
        if not owner:
            return jsonify({'success': False, 'error': 'Zone not found'}), 404
        if owner[0] != user['user_id']:
            return jsonify({'success': False, 'error': 'ไม่มีสิทธิ์เข้าถึงโซนนี้'}), 403

        # ลบทิ้งทั้งหมดก่อน
        cursor.execute("DELETE FROM mark_zone WHERE zone_id = %s", (zone_id,))

        inserted = 0
        if marks:
            vals = []
            for i, m in enumerate(marks, start=1):
                if not isinstance(m, dict):
                    continue
                tn = int(m.get('tree_no', i))
                lat = num_or_none(m.get('latitude'))
                lng = num_or_none(m.get('longitude'))
                if lat is None or lng is None:
                    continue
                vals.append((zone_id, tn, lat, lng))
            if vals:
                cursor.executemany("""
                    INSERT INTO mark_zone (zone_id, tree_no, latitude, longitude)
                    VALUES (%s, %s, %s, %s)
                """, vals)
                inserted = len(vals)

        cursor.execute("SELECT COUNT(*) FROM mark_zone WHERE zone_id = %s", (zone_id,))
        count = cursor.fetchone()[0]
        cursor.execute("UPDATE zone SET num_trees = %s WHERE zone_id = %s", (count, zone_id))

        conn.commit()
        return jsonify({'success': True, 'inserted': inserted, 'num_trees': count, 'message': 'แทนที่พิกัดสำเร็จ'})
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
