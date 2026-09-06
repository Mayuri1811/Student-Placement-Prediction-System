from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
CORS(app)

# ============================================================
# MYSQL CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "student_placement_db"
}

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():
    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )


# ============================================================
# CURRENT DATE/TIME
# ============================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()

        # ----------------------------------------------------
        # USERS TABLE
        # ----------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME NULL
            )
        """)

        # ----------------------------------------------------
        # STUDENT RECORDS TABLE
        # ----------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_records (
                student_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150),
                gender VARCHAR(20) NOT NULL,
                age INT NOT NULL,
                cgpa DECIMAL(4,2) NOT NULL,
                degree_percentage DECIMAL(5,2) NOT NULL,
                communication_skills TEXT NOT NULL,
                technical_skills TEXT NOT NULL,
                projects_completed INT DEFAULT 0,
                internship_status TINYINT DEFAULT 0,
                student_code VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ----------------------------------------------------
        # PLACEMENT RECORDS TABLE
        # ----------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS placement_records (
                record_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(50) NOT NULL,
                placement_status VARCHAR(30) NOT NULL,
                prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                probability DECIMAL(5,2),
                FOREIGN KEY (student_id)
                REFERENCES student_records(student_id)
                ON DELETE CASCADE
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("==========================================")
        print("MySQL Database initialized successfully")
        print("Database : student_placement_db")
        print("==========================================")

    except Error as e:
        print("Database initialization error:", e)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "Student Placement Prediction System Backend is Running"
    })


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["POST"])
def register():
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}

        full_name = str(data.get("full_name") or data.get("name") or "").strip()
        email = str(data.get("email") or "").strip()
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")

        # Validation
        if not full_name:
            return jsonify({"success": False, "message": "Full name is required."}), 400
        if not email:
            return jsonify({"success": False, "message": "Email is required."}), 400
        if not username:
            return jsonify({"success": False, "message": "Username is required."}), 400
        if not password:
            return jsonify({"success": False, "message": "Password is required."}), 400

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Check Username
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Username already exists."}), 400

        # Check Email
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Email already registered."}), 400

        # Insert User
        cursor.execute("""
            INSERT INTO users (full_name, email, username, password, registration_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (full_name, email, username, password, now()))

        conn.commit()

        return jsonify({"success": True, "message": "Registration successful."}), 201

    except Error as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ============================================================
# STUDENT LOGIN
# ============================================================

@app.route("/login", methods=["POST"])
def login():
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")

        if not username or not password:
            return jsonify({"success": False, "message": "Enter username and password."}), 400

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT user_id, full_name, email, username, registration_date, last_login
            FROM users
            WHERE username = %s AND password = %s
        """, (username, password))

        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "Invalid username or password."}), 401

        login_time = now()
        cursor.execute("UPDATE users SET last_login = %s WHERE user_id = %s", (login_time, user["user_id"]))
        conn.commit()

        user["last_login"] = login_time
        user["name"] = user["full_name"]

        return jsonify({"success": True, "message": "Login successful.", "user": user})

    except Error as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/admin/login", methods=["POST"])
def admin_login():
    try:
        data = request.get_json() or {}
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return jsonify({
                "success": True,
                "message": "Admin login successful.",
                "admin": {
                    "username": ADMIN_USERNAME,
                    "name": "Administrator",
                    "role": "admin"
                }
            })

        return jsonify({"success": False, "message": "Invalid admin username or password."}), 401

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================
# ML PREDICTION RULE ENGINE
# ============================================================

def calculate_prediction(data):
    cgpa = float(data.get("cgpa", 0))
    percentage = float(data.get("percentage", 0))
    communication = str(data.get("communication", "")).lower()
    technical = str(data.get("technical", "")).lower()
    projects = int(data.get("projects", 0))
    internship = int(data.get("internship", 0))

    score = 0

    # CGPA
    if cgpa >= 8: score += 30
    elif cgpa >= 7: score += 24
    elif cgpa >= 6: score += 17
    elif cgpa >= 5: score += 10

    # Percentage
    if percentage >= 80: score += 25
    elif percentage >= 70: score += 20
    elif percentage >= 60: score += 15
    elif percentage >= 50: score += 8

    # Communication
    good_words = ["good", "excellent", "strong", "presentation", "communication", "interview", "gd"]
    comm_points = sum(2 for word in good_words if word in communication)
    score += min(comm_points, 10)

    # Technical Skills
    tech_words = ["python", "java", "c++", "html", "css", "javascript", "js", "sql", "mysql", "machine learning", "flask", "react"]
    tech_points = sum(2 for word in tech_words if word in technical)
    score += min(tech_points, 15)

    # Projects
    if projects >= 4: score += 10
    elif projects >= 2: score += 7
    elif projects >= 1: score += 4

    # Internship
    if internship == 1: score += 10

    # Final Calculation
    probability = max(5, min(99, score))
    prediction = "Placed" if probability >= 55 else "Not Placed"

    return prediction, round(probability, 2)


# ============================================================
# PREDICT ENDPOINT
# ============================================================

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json() or {}
        required = ["name", "student_id", "email", "gender", "age", "cgpa", "percentage", "communication", "technical", "projects", "internship"]

        for field in required:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing field: {field}"}), 400

        prediction, probability = calculate_prediction(data)

        return jsonify({
            "success": True,
            "prediction": prediction,
            "probability": probability,
            "model": "Rule Engine / Heuristic",
            "prediction_date": now()
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Prediction error: {str(e)}"}), 500


# ============================================================
# SAVE STUDENT + PLACEMENT RECORD
# ============================================================

@app.route("/students", methods=["POST"])
def save_student():
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}
        student_id = str(data.get("student_id") or "").strip()

        if not student_id:
            return jsonify({"success": False, "message": "Student ID is required."}), 400

        name = str(data.get("name") or "").strip()
        email = str(data.get("email") or "").strip()
        gender = str(data.get("gender") or "").strip()
        age = int(data.get("age", 0))
        cgpa = float(data.get("cgpa", 0))
        percentage = float(data.get("percentage", 0))
        communication = str(data.get("communication") or "").strip()
        technical = str(data.get("technical") or "").strip()
        projects = int(data.get("projects", 0))
        internship = int(data.get("internship", 0))
        prediction = str(data.get("prediction", "Not Placed"))
        probability = float(data.get("probability", 0))

        conn = get_db()
        cursor = conn.cursor()

        # Insert / Update Student Record
        cursor.execute("""
            INSERT INTO student_records
            (student_id, name, email, gender, age, cgpa, degree_percentage, communication_skills, technical_skills, projects_completed, internship_status, student_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name), email = VALUES(email), gender = VALUES(gender), age = VALUES(age),
                cgpa = VALUES(cgpa), degree_percentage = VALUES(degree_percentage), communication_skills = VALUES(communication_skills),
                technical_skills = VALUES(technical_skills), projects_completed = VALUES(projects_completed),
                internship_status = VALUES(internship_status), student_code = VALUES(student_code)
        """, (student_id, name, email, gender, age, cgpa, percentage, communication, technical, projects, internship, student_id))

        # Refresh Placement Record
        cursor.execute("DELETE FROM placement_records WHERE student_id = %s", (student_id,))
        cursor.execute("""
            INSERT INTO placement_records (student_id, placement_status, prediction_date, probability)
            VALUES (%s, %s, %s, %s)
        """, (student_id, prediction, now(), probability))

        conn.commit()

        return jsonify({"success": True, "message": "Student and prediction saved successfully."})

    except Error as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ============================================================
# GET ALL STUDENTS
# ============================================================

@app.route("/students", methods=["GET"])
def get_students():
    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                p.record_id AS id, s.student_id, s.name, s.email, s.gender, s.age, s.cgpa,
                s.degree_percentage AS percentage, s.communication_skills AS communication,
                s.technical_skills AS technical, s.projects_completed AS projects,
                s.internship_status AS internship, p.placement_status AS prediction,
                p.probability, DATE_FORMAT(p.prediction_date, '%d-%m-%Y %H:%i:%s') AS prediction_date
            FROM student_records s
            LEFT JOIN placement_records p ON s.student_id = p.student_id
            ORDER BY p.prediction_date DESC
        """)

        return jsonify(cursor.fetchall())

    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ============================================================
# GET CURRENT USER STUDENTS
# ============================================================

@app.route("/students/user/<username>", methods=["GET"])
def get_user_students(username):
    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                p.record_id AS id, s.student_id, s.name, s.email, s.gender, s.age, s.cgpa,
                s.degree_percentage AS percentage, s.communication_skills AS communication,
                s.technical_skills AS technical, s.projects_completed AS projects,
                s.internship_status AS internship, p.placement_status AS prediction,
                p.probability, DATE_FORMAT(p.prediction_date, '%d-%m-%Y %H:%i:%s') AS prediction_date
            FROM student_records s
            LEFT JOIN placement_records p ON s.student_id = p.student_id
            INNER JOIN users u ON LOWER(TRIM(u.email)) = LOWER(TRIM(s.email))
            WHERE u.username = %s
            ORDER BY p.prediction_date DESC
        """, (username,))

        return jsonify(cursor.fetchall())

    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ============================================================
# GET REGISTERED USERS - ADMIN
# ============================================================

@app.route("/users", methods=["GET"])
def get_users():
    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                user_id, full_name, email, username,
                DATE_FORMAT(registration_date, '%d-%m-%Y %H:%i:%s') AS registration_date,
                DATE_FORMAT(last_login, '%d-%m-%Y %H:%i:%s') AS last_login
            FROM users
            ORDER BY registration_date DESC
        """)

        users = cursor.fetchall()
        for user in users:
            user["name"] = user["full_name"]

        return jsonify(users)

    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ============================================================
# DELETE STUDENT
# ============================================================

@app.route("/students/<int:record_id>", methods=["DELETE"])
def delete_student(record_id):
    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT student_id FROM placement_records WHERE record_id = %s", (record_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "Record not found."}), 404

        student_id = row[0]
        cursor.execute("DELETE FROM student_records WHERE student_id = %s", (student_id,))
        conn.commit()

        return jsonify({"success": True, "message": "Student record deleted successfully."})

    except Error as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    init_db()

    print("\n==============================================")
    print(" STUDENT PLACEMENT PREDICTION SYSTEM")
    print("==============================================")
    print(" Student URL : http://127.0.0.1:5000")
    print(" Admin       : admin")
    print(" Password    : admin123")
    print("==============================================\n")

    app.run(host="127.0.0.1", port=5000, debug=True)
