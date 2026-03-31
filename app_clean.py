"""
NexaAI — AI-Driven Skill Gap Platform
Flask Backend — Main Application (MySQL Version)
"""

import os
import json
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error

# ── Utils ──────────────────────────────────────────────────────────────
from utils.resume_parser   import parse_resume, extract_skills_from_text
from utils.skill_analyzer  import analyze_skills, get_role_list, get_ats_suggestions, ROLE_REQUIREMENTS
from utils.ai_service      import (
    get_diagnostic_questions,
    get_learning_path,
    get_interview_questions,
    evaluate_answer,
)

# ═══════════════════════════════════════════════════════════════════════
# MySQL Configuration
# ═══════════════════════════════════════════════════════════════════════
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Aryan@2007',
    'database': 'projectnexai_ai',
    'autocommit': False,
    'charset': 'utf8mb4'
}

# ═══════════════════════════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'nexaai-dev-secret-2024')
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_FILE_MB = 5

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_MB * 1024 * 1024


# ═══════════════════════════════════════════════════════════════════════
# MySQL Database
# ═══════════════════════════════════════════════════════════════════════

class DictCursor:
    """Wrapper to make MySQL results accessible like dictionaries"""
    def __init__(self, cursor):
        self.cursor = cursor
        self.description = cursor.description
        
    def fetchone(self):
        row = self.cursor.fetchone()
        if row and self.description:
            return dict(zip([col[0] for col in self.description], row))
        return row
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        if rows and self.description:
            columns = [col[0] for col in self.description]
            return [dict(zip(columns, row)) for row in rows]
        return rows


def get_db():
    """Get MySQL connection"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        print(f'[ERROR] MySQL Connection Failed: {e}')
        return None


def init_db():
    """Initialize database"""
    conn = get_db()
    if not conn:
        print('[ERROR] Cannot connect to MySQL')
        return
    
    cursor = conn.cursor()
    
    try:
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('student','admin') DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255),
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extracted_skills JSON,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_gaps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role VARCHAR(255),
                missing_skills JSON,
                priority_areas JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnostic_tests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                skill_area VARCHAR(255),
                questions JSON,
                answers JSON,
                score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role VARCHAR(255),
                path_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                plan VARCHAR(50),
                amount DECIMAL(10,2),
                status VARCHAR(50),
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(10,2),
                plan VARCHAR(50),
                transaction_id VARCHAR(255),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        
        # Create admin user if not exists
        cursor.execute('SELECT id FROM users WHERE email=%s', ('arynmishra2007@gmail.com',))
        existing = cursor.fetchone()
        if not existing:
            admin_hash = generate_password_hash('Aryan!2007')
            cursor.execute(
                'INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)',
                ('Admin', 'arynmishra2007@gmail.com', admin_hash, 'admin')
            )
            conn.commit()
            print('[NexaAI] Admin user created: arynmishra2007@gmail.com / Aryan!2007')
        
        cursor.close()
        conn.close()
        print('[NexaAI] MySQL Database ready')
    
    except Error as e:
        print(f'[ERROR] Database init failed: {e}')


# ═══════════════════════════════════════════════════════════════════════
# Auth Decorators
# ═══════════════════════════════════════════════════════════════════════

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE id=%s', (session['user_id'],))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result or result[0] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ═══════════════════════════════════════════════════════════════════════
# Auth Routes
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE email=%s', (data['email'],))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        password_hash = generate_password_hash(data['password'])
        cursor.execute(
            'INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)',
            (data['name'], data['email'], password_hash, 'student')
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['user_email'] = data['email']
        session['user_role'] = 'student'
        
        return jsonify({
            'message': 'Registration successful',
            'user': {
                'id': user_id,
                'email': data['email'],
                'name': data['name'],
                'role': 'student'
            }
        }), 201
    
    except Error as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, name, email, password, role FROM users WHERE email=%s', (data['email'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user_id, name, email, password_hash, role = user
        
        if not check_password_hash(password_hash, data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Set session
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_role'] = role
        session.permanent = True
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user_id,
                'email': email,
                'name': name,
                'role': role
            }
        }), 200
    
    except Error as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


@app.route('/api/auth-check', methods=['GET'])
def auth_check():
    """Check if user is logged in"""
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {
                'id': session.get('user_id'),
                'email': session.get('user_email'),
                'role': session.get('user_role')
            }
        }), 200
    
    return jsonify({'logged_in': False}), 200


# ═══════════════════════════════════════════════════════════════════════
# Resume Upload
# ═══════════════════════════════════════════════════════════════════════

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/upload-resume', methods=['POST'])
@require_login
def upload_resume():
    """Upload and parse resume"""
    if 'resume' not in request.files and 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files.get('resume') or request.files.get('file')
    
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse resume
        extracted_data = parse_resume(filepath)
        
        # Store in database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO resumes (user_id, filename, extracted_skills) VALUES (%s,%s,%s)',
            (session['user_id'], filename, json.dumps(extracted_data))
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Resume uploaded successfully',
            'data': extracted_data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════
# Skill Analysis
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/analyze-skills', methods=['POST'])
@require_login
def analyze_skills_route():
    """Analyze skill gaps"""
    data = request.get_json()
    student_skills = data.get('student_skills', [])
    selected_role = data.get('role', '')
    
    if not selected_role:
        return jsonify({'error': 'Please select a role'}), 400
    
    # Get role requirements
    role_skills = ROLE_REQUIREMENTS.get(selected_role, {})
    
    # Analyze gaps
    gap_analysis = analyze_skills(student_skills, role_skills)
    
    # Store in database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO skill_gaps (user_id, role, missing_skills, priority_areas) VALUES (%s,%s,%s,%s)',
        (session['user_id'], selected_role, json.dumps(gap_analysis['missing']), json.dumps(gap_analysis['priority']))
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify(gap_analysis), 200


@app.route('/api/get-roles', methods=['GET'])
def get_roles():
    """Get available roles"""
    return jsonify({'roles': list(ROLE_REQUIREMENTS.keys())}), 200


# ═══════════════════════════════════════════════════════════════════════
# Learning Path
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/learning-path', methods=['POST'])
@require_login
def learning_path():
    """Generate learning path"""
    data = request.get_json()
    gaps = data.get('gaps', [])
    role = data.get('role', '')
    
    path = get_learning_path(gaps, role)
    
    # Store in database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO learning_paths (user_id, role, path_data) VALUES (%s,%s,%s)',
        (session['user_id'], role, json.dumps(path))
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify(path), 200


# ═══════════════════════════════════════════════════════════════════════
# Payment & Subscriptions
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/pricing', methods=['GET'])
def get_pricing():
    """Get pricing plans"""
    return jsonify({
        'plans': [
            {'name': 'Basic', 'price': 499, 'features': ['Resume Analysis', 'Skill Gap Report']},
            {'name': 'Pro', 'price': 999, 'features': ['Resume Analysis', 'Skill Gap Report', 'Learning Path', 'Diagnostic Test']},
            {'name': 'Premium', 'price': 1999, 'features': ['Resume Analysis', 'Skill Gap Report', 'Learning Path', 'Diagnostic Test', 'Mock Interview', 'Interview Questions']}
        ]
    }), 200


@app.route('/api/subscribe', methods=['POST'])
@require_login
def subscribe():
    """Subscribe to plan"""
    data = request.get_json()
    plan = data.get('plan', '')
    
    prices = {'Basic': 499, 'Pro': 999, 'Premium': 1999}
    amount = prices.get(plan, 0)
    
    if not amount:
        return jsonify({'error': 'Invalid plan'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Create subscription
    cursor.execute(
        'INSERT INTO subscriptions (user_id, plan, amount, status) VALUES (%s,%s,%s,%s)',
        (session['user_id'], plan, amount, 'pending')
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({
        'message': 'Subscription created',
        'plan': plan,
        'amount': amount
    }), 201


@app.route('/api/payment-success', methods=['POST'])
@require_login
def payment_success():
    """Mark payment as successful"""
    data = request.get_json()
    transaction_id = data.get('transaction_id', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Update subscription status
    cursor.execute(
        'UPDATE subscriptions SET status=%s WHERE user_id=%s ORDER BY id DESC LIMIT 1',
        ('active', session['user_id'])
    )
    
    # Record payment
    cursor.execute(
        'SELECT plan, amount FROM subscriptions WHERE user_id=%s ORDER BY id DESC LIMIT 1',
        (session['user_id'],)
    )
    sub = cursor.fetchone()
    
    if sub:
        plan, amount = sub
        cursor.execute(
            'INSERT INTO payments (user_id, amount, plan, transaction_id, status) VALUES (%s,%s,%s,%s,%s)',
            (session['user_id'], amount, plan, transaction_id, 'success')
        )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Payment recorded'}), 200


# ═══════════════════════════════════════════════════════════════════════
# Admin Analytics
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/admin/analytics', methods=['GET'])
@require_admin
def admin_analytics():
    """Get admin analytics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total students
    cursor.execute('SELECT COUNT(*) FROM users WHERE role=%s', ('student',))
    total_students = cursor.fetchone()[0]
    
    # Total resumes uploaded
    cursor.execute('SELECT COUNT(*) FROM resumes')
    total_resumes = cursor.fetchone()[0]
    
    # Active subscriptions
    cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE status=%s', ('active',))
    active_subs = cursor.fetchone()[0]
    
    # Total revenue
    cursor.execute('SELECT SUM(amount) FROM payments WHERE status=%s', ('success',))
    result = cursor.fetchone()
    total_revenue = result[0] if result[0] else 0
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'total_students': total_students,
        'total_resumes': total_resumes,
        'active_subscriptions': active_subs,
        'total_revenue': float(total_revenue)
    }), 200


@app.route('/api/admin/students', methods=['GET'])
@require_admin
def admin_students():
    """Get all students"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, created_at FROM users WHERE role=%s', ('student',))
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({'students': students}), 200


# ═══════════════════════════════════════════════════════════════════════
# Static Files
# ═══════════════════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def index():
    return send_from_directory('.', 'index.html')


@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ═══════════════════════════════════════════════════════════════════════
# Error Handlers
# ═══════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return send_from_directory('.', 'index.html')


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('\n' + '='*70)
    print(' NexaAI — AI-Driven Skill Gap Platform')
    print(' Starting Flask Server...')
    print('='*70)
    
    # Initialize database
    init_db()
    
    # Start server
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
