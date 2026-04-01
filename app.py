"""
NexaAI — AI-Driven Skill Gap Platform
Flask Backend — MySQL with SQLite fallback
"""

import os
import json
import sqlite3
import tempfile
import random
import string
from datetime import datetime, timedelta
from functools import wraps

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('[NexaAI] Loaded .env file')
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

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
# Database Mode — MySQL if configured, else SQLite
# ═══════════════════════════════════════════════════════════════════════
# Check multiple possible env var names for MySQL host
_MYSQL_HOST = (
    os.environ.get('MYSQL_HOST') or      # Your .env format
    os.environ.get('MYSQLHOST') or       # Railway format
    os.environ.get('DB_HOST')
)
USE_MYSQL = bool(_MYSQL_HOST)

if USE_MYSQL:
    import mysql.connector
    from mysql.connector import Error as DbError
    MYSQL_CONFIG = {
        'host':     _MYSQL_HOST,
        'port':     int(os.environ.get('MYSQL_PORT', os.environ.get('MYSQLPORT', os.environ.get('DB_PORT', 3306)))),
        'user':     os.environ.get('MYSQL_USER', os.environ.get('MYSQLUSER', os.environ.get('DB_USER', 'root'))),
        'password': os.environ.get('MYSQL_PASSWORD', os.environ.get('MYSQLPASSWORD', os.environ.get('DB_PASSWORD', ''))),
        'database': os.environ.get('MYSQL_DATABASE', os.environ.get('MYSQLDATABASE', os.environ.get('DB_NAME', 'resumeai'))),
        'autocommit': False,
        'charset': 'utf8mb4'
    }
    print(f'[NexaAI] Database mode: MySQL ({_MYSQL_HOST}:{MYSQL_CONFIG["port"]}/{MYSQL_CONFIG["database"]})')
else:
    _default_db = os.path.join(os.path.dirname(__file__), 'nexaai.db')
    SQLITE_PATH = os.environ.get('SQLITE_PATH', _default_db)
    print(f'[NexaAI] Database mode: SQLite ({SQLITE_PATH})')

# ═══════════════════════════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'nexaai-dev-secret-2024')
CORS(app, supports_credentials=True, origins='*')

# On Railway (HTTPS) cookies need Secure+SameSite=None
# Locally (HTTP) use Lax so sessions still work
_on_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_SERVICE_ID'))
app.config['SESSION_COOKIE_SAMESITE'] = 'None' if _on_railway else 'Lax'
app.config['SESSION_COOKIE_SECURE']   = _on_railway
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_MB = 5

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_MB * 1024 * 1024


# ═══════════════════════════════════════════════════════════════════════
# Database helpers — works with both MySQL and SQLite
# ═══════════════════════════════════════════════════════════════════════

class _Conn:
    """Unified connection wrapper for MySQL and SQLite."""
    def __init__(self, conn, is_sqlite=False):
        self._conn = conn
        self._is_sqlite = is_sqlite

    def cursor(self):
        if self._is_sqlite:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.cursor()
            return _Cur(cur, is_sqlite=True)
        else:
            cur = self._conn.cursor()
            return _Cur(cur, is_sqlite=False)

    def commit(self):  self._conn.commit()
    def close(self):   self._conn.close()


class _Cur:
    """Unified cursor wrapper returning plain tuples."""
    def __init__(self, cur, is_sqlite=False):
        self._cur = cur
        self._is_sqlite = is_sqlite

    def execute(self, sql, params=()):
        if self._is_sqlite:
            sql = sql.replace('%s', '?')
        self._cur.execute(sql, params)

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return tuple(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [tuple(r) for r in rows]

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    def close(self): self._cur.close()


def get_db():
    """Return a unified DB connection (MySQL or SQLite)."""
    if USE_MYSQL:
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            return _Conn(conn, is_sqlite=False)
        except Exception as e:
            print(f'[ERROR] MySQL failed: {e}')
            return None
    else:
        try:
            conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
            return _Conn(conn, is_sqlite=True)
        except Exception as e:
            print(f'[ERROR] SQLite failed: {e}')
            return None


def _sql(mysql_sql):
    """Return SQLite-compatible SQL from MySQL SQL."""
    if USE_MYSQL:
        return mysql_sql
    sql = mysql_sql
    sql = sql.replace('INT AUTO_INCREMENT PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
    sql = sql.replace("ENUM('student','admin') DEFAULT 'student'", "TEXT DEFAULT 'student'")
    sql = sql.replace('JSON', 'TEXT')
    sql = sql.replace('DECIMAL(10,2)', 'REAL')
    sql = sql.replace('FLOAT', 'REAL')
    sql = sql.replace('VARCHAR(255)', 'TEXT')
    sql = sql.replace('VARCHAR(50)', 'TEXT')
    sql = sql.replace('TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    sql = sql.replace('TIMESTAMP NULL', 'TIMESTAMP')
    # Remove FOREIGN KEY lines for SQLite
    lines = [l for l in sql.split('\n') if 'FOREIGN KEY' not in l and 'REFERENCES' not in l]
    # Remove trailing commas before closing paren
    cleaned = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if stripped.endswith(','):
            rest = '\n'.join(lines[i+1:]).lstrip()
            if rest.startswith(')'):
                stripped = stripped[:-1]
        cleaned.append(stripped)
    return '\n'.join(cleaned)


def init_db():
    """Initialize database tables and admin user."""
    conn = get_db()
    if not conn:
        print('[ERROR] Cannot connect to database')
        return

    cursor = conn.cursor()
    try:
        cursor.execute(_sql('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('student','admin') DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))

        cursor.execute(_sql('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255),
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extracted_skills JSON,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        '''))

        cursor.execute(_sql('''
            CREATE TABLE IF NOT EXISTS skill_gaps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role VARCHAR(255),
                missing_skills JSON,
                priority_areas JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        '''))

        cursor.execute(_sql('''
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
        '''))

        cursor.execute(_sql('''
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role VARCHAR(255),
                path_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        '''))

        cursor.execute(_sql('''
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
        '''))

        cursor.execute(_sql('''
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
        '''))

        conn.commit()

        # Create admin user if not exists
        cursor.execute('SELECT id FROM users WHERE email=%s', ('arynmishra2007@gmail.com',))
        if not cursor.fetchone():
            admin_hash = generate_password_hash('Aryan!2007')
            cursor.execute(
                'INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)',
                ('Admin', 'arynmishra2007@gmail.com', admin_hash, 'admin')
            )
            conn.commit()
            print('[NexaAI] Admin user created')

        cursor.close()
        conn.close()
        db_type = 'MySQL' if USE_MYSQL else 'SQLite'
        print(f'[NexaAI] {db_type} database ready')

    except Exception as e:
        import traceback
        traceback.print_exc()
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
        if not conn:
            return jsonify({'error': 'Database error'}), 500
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
        
        user_id, name, email, password_hash, role = user[0], user[1], user[2], user[3], user[4]
        
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
    
    except Exception as e:
        print(f'[ERROR] Login error: {e}')
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Test database connection and show users"""
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute('SELECT id, email, role FROM users')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Database connected',
            'users': users,
            'user_count': len(users) if users else 0
        }), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


# Store reset codes temporarily (in production, use Redis or database)
password_reset_codes = {}

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset - generates a reset code"""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        if USE_MYSQL:
            cursor.execute('SELECT id, name FROM users WHERE email = %s', (email,))
        else:
            cursor.execute('SELECT id, name FROM users WHERE email = ?', (email,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            # Don't reveal if email exists or not for security
            # But for this demo, we'll be helpful
            return jsonify({'error': 'No account found with this email'}), 404
        
        # Generate 6-digit reset code
        reset_code = ''.join(random.choices(string.digits, k=6))
        
        # Store reset code with expiry (15 minutes)
        password_reset_codes[email] = {
            'code': reset_code,
            'user_id': user[0],
            'expires': datetime.now() + timedelta(minutes=15)
        }
        
        # In production, send email here
        # For now, return the code directly (demo mode)
        print(f'[NexaAI] Password reset code for {email}: {reset_code}')
        
        return jsonify({
            'message': 'Reset code generated',
            'reset_code': reset_code  # Remove this line in production!
        }), 200
        
    except Exception as e:
        print(f'[NexaAI] Forgot password error: {e}')
        return jsonify({'error': 'Failed to process request'}), 500


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset password using reset code"""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    reset_code = data.get('reset_code', '').strip()
    new_password = data.get('new_password', '')
    
    if not email or not reset_code or not new_password:
        return jsonify({'error': 'Email, reset code, and new password are required'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    # Verify reset code
    stored = password_reset_codes.get(email)
    if not stored:
        return jsonify({'error': 'No reset code found. Please request a new one.'}), 400
    
    if stored['code'] != reset_code:
        return jsonify({'error': 'Invalid reset code'}), 400
    
    if datetime.now() > stored['expires']:
        del password_reset_codes[email]
        return jsonify({'error': 'Reset code has expired. Please request a new one.'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Update password
        hashed_password = generate_password_hash(new_password)
        
        if USE_MYSQL:
            cursor.execute(
                'UPDATE users SET password = %s WHERE id = %s',
                (hashed_password, stored['user_id'])
            )
        else:
            cursor.execute(
                'UPDATE users SET password = ? WHERE id = ?',
                (hashed_password, stored['user_id'])
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Remove used reset code
        del password_reset_codes[email]
        
        print(f'[NexaAI] Password reset successful for {email}')
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        print(f'[NexaAI] Password reset error: {e}')
        return jsonify({'error': 'Failed to reset password'}), 500


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


@app.route('/api/test-upload', methods=['POST'])
@require_login
def test_upload():
    """Test upload without parsing"""
    try:
        if 'resume' not in request.files and 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400
        
        file = request.files.get('resume') or request.files.get('file')
        if not file:
            return jsonify({'error': 'No file object'}), 400
        
        filename = secure_filename(file.filename)
        return jsonify({
            'message': 'Test OK',
            'filename': filename,
            'data': {
                'skills': ['python', 'javascript', 'react', 'sql'],
                'name': 'Test User',
                'email': 'test@example.com'
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-resume', methods=['POST'])
@require_login
def upload_resume():
    """Upload and parse resume, then auto-run skill analysis"""
    try:
        # ── 1. Parse the uploaded file ────────────────────────────
        parsed_data = None
        file = request.files.get('resume') or request.files.get('file')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                parsed_data = parse_resume(filepath, filename)
                print(f'[INFO] Parsed resume: {len(parsed_data.get("skills", []))} skills found')
            except Exception as parse_err:
                print(f'[WARN] Resume parse failed: {parse_err}')

        if parsed_data and parsed_data.get('success') and parsed_data.get('skills'):
            skills = parsed_data['skills']
        else:
            skills = []
            if parsed_data is None:
                parsed_data = {'success': True}
            parsed_data.setdefault('name', None)
            parsed_data.setdefault('email', None)
            parsed_data.setdefault('phone', None)
            parsed_data.setdefault('education', None)
            parsed_data.setdefault('experience_years', None)
            parsed_data['skills'] = skills
            parsed_data['skill_count'] = 0
            parsed_data['raw_text_length'] = 0
            parsed_data['raw_text_preview'] = ''

        # ── 2. Save skills to session + database ─────────────────
        session['resume_skills'] = skills
        session.modified = True

        try:
            conn = get_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO resumes (user_id, filename, extracted_skills) VALUES (%s,%s,%s)',
                    (session['user_id'], file.filename if file else 'resume', json.dumps(skills))
                )
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as db_err:
            print(f'[WARN] Could not save resume to DB: {db_err}')

        # ── 3. Auto-run skill gap analysis (default role = ai) ───
        # Use role from request if sent, else default to 'ai'
        selected_role = request.form.get('role', 'ai')
        if selected_role not in ROLE_REQUIREMENTS:
            selected_role = 'ai'

        gap_analysis = analyze_skills(skills, selected_role)

        # Merge gap analysis into the response data so the frontend
        # can use it immediately (sets currentAnalysis properly)
        parsed_data.update(gap_analysis)
        parsed_data['skill_count'] = len(skills)

        return jsonify({
            'message': 'Resume uploaded and analyzed successfully',
            'data': parsed_data
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'upload_resume_exception: {e}'}), 500


@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'ok': True, 'version': 'hotfix-upload-1'}), 200


# ═══════════════════════════════════════════════════════════════════════
# Skill Analysis
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/analyze-skills', methods=['POST'])
@require_login
def analyze_skills_route():
    """Analyze skill gaps"""
    data = request.get_json() or {}
    selected_role = data.get('role', '')

    if not selected_role:
        return jsonify({'error': 'Please select a role'}), 400

    # Get skills from request body, session (set during upload), or DB
    student_skills = data.get('student_skills') or list(session.get('resume_skills', []))
    if not student_skills:
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT extracted_skills FROM resumes WHERE user_id=%s ORDER BY id DESC LIMIT 1',
                (session['user_id'],)
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                try:
                    val = row[0] if isinstance(row, tuple) else row.get('extracted_skills')
                    student_skills = json.loads(val) if val else []
                except Exception:
                    student_skills = []

    # Analyze gaps — pass role key string, not the dict
    gap_analysis = analyze_skills(student_skills, selected_role)

    # Store in database
    try:
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO skill_gaps (user_id, role, missing_skills, priority_areas) VALUES (%s,%s,%s,%s)',
                (session['user_id'], selected_role, json.dumps(gap_analysis.get('skills_missing', [])), json.dumps(gap_analysis.get('skills_priority', [])))
            )
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f'[WARN] Could not save skill gaps: {e}')

    return jsonify(gap_analysis), 200


@app.route('/api/get-roles', methods=['GET'])
def get_roles():
    """Get available roles"""
    return jsonify({'roles': list(ROLE_REQUIREMENTS.keys())}), 200


# ═══════════════════════════════════════════════════════════════════════
# Interview Questions
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/interview-questions', methods=['POST', 'GET'])
@require_login
def interview_questions():
    """Get interview questions for selected role"""
    if request.method == 'POST':
        data = request.get_json()
        role = data.get('role', 'ai')
    else:
        role = request.args.get('role', 'ai')
    
    try:
        questions = get_interview_questions(role)
        return jsonify({
            'role': role,
            'questions': questions or [
                {
                    'id': 1,
                    'question': f'What is your experience with {role}?',
                    'type': 'open',
                    'difficulty': 'easy'
                },
                {
                    'id': 2,
                    'question': f'Describe a project where you used {role} skills.',
                    'type': 'open',
                    'difficulty': 'medium'
                },
                {
                    'id': 3,
                    'question': f'What are the latest trends in {role}?',
                    'type': 'open',
                    'difficulty': 'hard'
                }
            ]
        }), 200
    except Exception as e:
        print(f'[ERROR] Interview questions error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/diagnostic-test/<skill>', methods=['GET'])
@require_login
def diagnostic_test(skill):
    """Get diagnostic test questions for a skill"""
    try:
        questions = get_diagnostic_questions(skill)
        return jsonify({
            'skill': skill,
            'questions': questions or [
                {'id': 1, 'question': f'Explain {skill}', 'options': ['A', 'B', 'C', 'D'], 'correct': 0},
                {'id': 2, 'question': f'How is {skill} used?', 'options': ['A', 'B', 'C', 'D'], 'correct': 1},
            ]
        }), 200
    except Exception as e:
        print(f'[ERROR] Diagnostic test error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate-answer', methods=['POST'])
@require_login
def evaluate_answer_route():
    """Evaluate interview answer"""
    data = request.get_json()
    question = data.get('question', '')
    answer = data.get('answer', '')
    role = data.get('role', 'ai')

    try:
        feedback = evaluate_answer(question, answer, role)
        return jsonify({
            'feedback': feedback,
            'score': feedback.get('score', 0) / 10 if isinstance(feedback, dict) else 0.75
        }), 200
    except Exception as e:
        print(f'[ERROR] Answer evaluation error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/submit-answer', methods=['POST'])
@require_login
def submit_answer_route():
    """Submit and evaluate interview answer (alias used by frontend)"""
    data = request.get_json() or {}
    question = data.get('question', '')
    answer = data.get('answer', '')
    role = data.get('role', 'ai')

    try:
        feedback = evaluate_answer(question, answer, role)
        return jsonify({
            'feedback': feedback,
            'score': feedback.get('score', 0) / 10 if isinstance(feedback, dict) else 0.75
        }), 200
    except Exception as e:
        print(f'[ERROR] Submit answer error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/ats-suggestions', methods=['POST'])
@require_login
def ats_suggestions():
    """Get ATS optimization suggestions"""
    data = request.get_json() or {}
    role = data.get('role', 'ai')
    skills = data.get('skills', [])
    resume_text = data.get('resume_text', '')

    try:
        result = get_ats_suggestions(skills, role, resume_text)
        return jsonify(result), 200
    except Exception as e:
        print(f'[ERROR] ATS suggestions error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/user', methods=['GET'])
@require_login
def get_user():
    """Get current logged-in user info"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, name, email, role FROM users WHERE id=%s', (session['user_id'],))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'User not found'}), 404

        if isinstance(row, tuple):
            user_id, name, email, role = row
        else:
            user_id, name, email, role = row['id'], row['name'], row['email'], row['role']

        return jsonify({
            'user': {'id': user_id, 'name': name, 'email': email, 'role': role}
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/user-stats', methods=['GET'])
@require_login
def user_stats():
    """Get stats for the current user"""
    conn = get_db()
    if not conn:
        return jsonify({'resumes': 0, 'match_score': 0, 'skills': 0, 'interviews': 0}), 200

    cursor = conn.cursor()
    try:
        user_id = session['user_id']

        cursor.execute('SELECT COUNT(*) FROM resumes WHERE user_id=%s', (user_id,))
        resumes = cursor.fetchone()[0]

        cursor.execute('SELECT missing_skills FROM skill_gaps WHERE user_id=%s ORDER BY id DESC LIMIT 1', (user_id,))
        row = cursor.fetchone()
        match_score = 0
        skills = 0
        if row:
            try:
                missing = json.loads(row[0]) if row[0] else []
                skills = len(missing)
            except Exception:
                pass

        cursor.execute('SELECT COUNT(*) FROM diagnostic_tests WHERE user_id=%s', (user_id,))
        interviews = cursor.fetchone()[0]

        return jsonify({
            'resumes': resumes,
            'match_score': match_score,
            'skills': skills,
            'interviews': interviews
        }), 200
    except Exception as e:
        print(f'[ERROR] user-stats error: {e}')
        return jsonify({'resumes': 0, 'match_score': 0, 'skills': 0, 'interviews': 0}), 200
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════════════════════════
# Learning Path
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/learning-path', methods=['POST'])
@require_login
def learning_path():
    """Generate learning path"""
    data = request.get_json() or {}
    # Frontend sends target_role and missing_skills
    role = data.get('target_role') or data.get('role', 'ai')
    gaps = data.get('missing_skills') or data.get('gaps', [])

    try:
        path = get_learning_path(role, gaps)
    except Exception as e:
        print(f'[ERROR] get_learning_path error: {e}')
        return jsonify({'error': str(e)}), 500

    # Store in database
    try:
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO learning_paths (user_id, role, path_data) VALUES (%s,%s,%s)',
                (session['user_id'], role, json.dumps(path))
            )
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f'[WARN] Could not save learning path: {e}')

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


@app.route('/api/payment/create-order', methods=['POST'])
@require_login
def create_payment_order():
    """Create a payment order"""
    data = request.get_json()
    plan_id = data.get('plan_id', '')
    amount = data.get('amount', 0)
    
    # Generate a unique order ID
    import uuid
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'amount': amount,
        'plan_id': plan_id
    }), 200


@app.route('/api/payment/verify', methods=['POST'])
@require_login
def verify_payment():
    """Verify payment and activate subscription"""
    data = request.get_json()
    payment_id = data.get('payment_id', '')
    plan_id = data.get('plan_id', '')
    payment_method = data.get('payment_method', 'card')
    
    # Map plan IDs to prices
    prices = {'basic': 499, 'pro': 999, 'premium': 1999}
    amount = prices.get(plan_id, 0)
    
    if not amount:
        return jsonify({'error': 'Invalid plan'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Create subscription
        cursor.execute(
            'INSERT INTO subscriptions (user_id, plan, amount, status) VALUES (%s,%s,%s,%s)',
            (session['user_id'], plan_id, amount, 'active')
        )
        
        # Record payment
        cursor.execute(
            'INSERT INTO payments (user_id, amount, plan, transaction_id, status) VALUES (%s,%s,%s,%s,%s)',
            (session['user_id'], amount, plan_id, payment_id, 'success')
        )
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Payment verified and subscription activated',
            'plan': plan_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/subscription/status', methods=['GET'])
@require_login
def subscription_status():
    """Get current subscription status"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT plan, status FROM subscriptions WHERE user_id=%s AND status=%s ORDER BY id DESC LIMIT 1',
        (session['user_id'], 'active')
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return jsonify({
            'has_subscription': True,
            'plan': result[0],
            'status': result[1]
        }), 200
    
    return jsonify({
        'has_subscription': False,
        'plan': 'free',
        'status': 'none'
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
# Startup — runs for BOTH gunicorn and direct python app.py
# ═══════════════════════════════════════════════════════════════════════

print('\n' + '='*70)
print(' NexaAI — AI-Driven Skill Gap Platform')
print(' Initializing...')
print('='*70)
init_db()


# ═══════════════════════════════════════════════════════════════════════
# Main (direct run only — gunicorn uses the module directly)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not _on_railway, host='0.0.0.0', port=port, use_reloader=False)
