from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import random

app = Flask(__name__)
CORS(app) 

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ojasvi0811",
        database="campusos"
    )

# --- 1. Dashboard Stats ---
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        stats = {}
        cursor.execute("SELECT COUNT(*) as count FROM students")
        stats['students'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM events")
        stats['events'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM clubs")
        stats['clubs'] = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM participations")
        stats['registrations'] = cursor.fetchone()['count']
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# --- 2. Authentication ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    type = data.get('type')
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if type == 'student':
            cursor.execute("SELECT * FROM students WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user:
                return jsonify({"success": True, "user": user})
        elif type == 'admin':
            cursor.execute("SELECT * FROM admins WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
            if user:
                return jsonify({"success": True, "user": user})
                
        return jsonify({"success": False, "error": "Invalid credentials"})
    finally:
        cursor.close()
        conn.close()

# --- 3. Student Routes ---
@app.route('/api/register_student', methods=['POST'])
def register_student():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        student_id = "STU" + str(random.randint(1000, 9999))
        sql = "INSERT INTO students (id, name, email, phone, department, year, college, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (student_id, data['name'], data['email'], data['phone'], data['department'], data['year'], data['college'], data['password'])
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"success": True, "message": "Registered successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT s.id, s.name, s.email, s.department, s.college, s.year,
               GROUP_CONCAT(e.name SEPARATOR ', ') as registered_events
        FROM students s
        LEFT JOIN participations p ON s.id = p.student_id
        LEFT JOIN events e ON p.event_id = e.id
        GROUP BY s.id
    """
    cursor.execute(sql)
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "students": students})

@app.route('/api/delete_student/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "message": "Student deleted."})

# --- 4. Event Routes ---
@app.route('/api/events', methods=['GET'])
def get_events():
    club_id = request.args.get('club_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if club_id:
        cursor.execute("SELECT * FROM events WHERE club_id = %s ORDER BY date", (club_id,))
    else:
        cursor.execute("SELECT * FROM events ORDER BY date")
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "events": events})

@app.route('/api/add_event', methods=['POST'])
def add_event():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        event_id = "EVT" + str(random.randint(1000, 9999))
        sql = "INSERT INTO events (id, name, date, venue, fee, club_id, club_name) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (event_id, data['name'], data['date'], data['venue'], data['fee'], data['club_id'], data['club_name'])
        cursor.execute(sql, val)
        conn.commit()
        return jsonify({"success": True, "message": "Event created!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/delete_event/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "message": "Event deleted."})

@app.route('/api/register_event', methods=['POST'])
def register_event():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        reg_id = "REG" + str(random.randint(10000, 99999))
        cursor.execute("INSERT INTO participations (id, student_id, event_id) VALUES (%s, %s, %s)", (reg_id, data['student_id'], data['event_id']))
        conn.commit()
        return jsonify({"success": True, "message": "Successfully registered for event!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/my_registrations/<student_id>', methods=['GET'])
def get_my_registrations(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """SELECT p.status, p.registered_at, e.name as event_name, e.date as event_date, e.venue 
             FROM participations p JOIN events e ON p.event_id = e.id 
             WHERE p.student_id = %s"""
    cursor.execute(sql, (student_id,))
    regs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"success": True, "registrations": regs})

# --- 5. NEW ANALYTICS ROUTE ---
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    club_id = request.args.get('club_id')
    role = request.args.get('role')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    analytics_data = {"departments": [], "events": []}
    
    try:
        # Dept Data
        if role == 'superadmin':
            cursor.execute("SELECT s.department as label, COUNT(p.id) as count FROM participations p JOIN students s ON p.student_id = s.id GROUP BY s.department")
        else:
            cursor.execute("SELECT s.department as label, COUNT(p.id) as count FROM participations p JOIN students s ON p.student_id = s.id JOIN events e ON p.event_id = e.id WHERE e.club_id = %s GROUP BY s.department", (club_id,))
        analytics_data['departments'] = cursor.fetchall()
        
        # Event Data
        if role == 'superadmin':
            cursor.execute("SELECT e.name as label, COUNT(p.id) as count FROM participations p JOIN events e ON p.event_id = e.id GROUP BY e.id, e.name")
        else:
            cursor.execute("SELECT e.name as label, COUNT(p.id) as count FROM participations p JOIN events e ON p.event_id = e.id WHERE e.club_id = %s GROUP BY e.id, e.name", (club_id,))
        analytics_data['events'] = cursor.fetchall()
        
        return jsonify({"success": True, "data": analytics_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("🚀 CampusOS Backend running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)