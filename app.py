"""
NexaAI — AI-Driven Skill Gap Platform
Flask Backend — MySQL with SQLite fallback
"""

import os
import json
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
from werkzeug.middleware.proxy_fix import ProxyFix

# ── Google Gemini AI ───────────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDBHsJMFA75VjCfIVEniToTdJ53Uw7QkHw')
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash')
    GEMINI_AVAILABLE = True
    print('[NexaAI] Gemini AI initialized successfully')
except Exception as e:
    GEMINI_AVAILABLE = False
    GEMINI_MODEL = None
    print(f'[NexaAI] Gemini AI not available: {e}')

# ── Utils ──────────────────────────────────────────────────────────────
from utils.resume_parser   import parse_resume, extract_skills_from_text, parse_resume_structured
from utils.skill_analyzer  import analyze_skills, get_role_list, get_ats_suggestions, ROLE_REQUIREMENTS
from utils.ai_service      import (
    get_diagnostic_questions,
    get_learning_path,
    get_interview_questions,
    evaluate_answer,
)

# ═══════════════════════════════════════════════════════════════════════
# Database Mode — MySQL only
# ═══════════════════════════════════════════════════════════════════════
import mysql.connector
from mysql.connector import Error as DbError
from urllib.parse import urlparse

def _parse_mysql_url(url):
    """Parse mysql://user:pass@host:port/dbname into a config dict."""
    try:
        p = urlparse(url)
        return {
            'host':     p.hostname or 'localhost',
            'port':     p.port or 3306,
            'user':     p.username or 'root',
            'password': p.password or '',
            'database': (p.path or '/nexaai').lstrip('/'),
        }
    except Exception:
        return {}

# Support MYSQL_URL / DATABASE_URL (Railway single-variable format)
# e.g.  MYSQL_URL=mysql://user:pass@host:3306/railway
_db_url = os.environ.get('MYSQL_URL') or os.environ.get('DATABASE_URL') or ''
if _db_url.startswith('mysql'):
    _url_cfg = _parse_mysql_url(_db_url)
else:
    _url_cfg = {}

# Detect if running on Railway (it auto-injects these)
_on_railway_early = bool(
    os.environ.get('RAILWAY_ENVIRONMENT') or
    os.environ.get('RAILWAY_SERVICE_ID') or
    os.environ.get('RAILWAY_PROJECT_ID')
)

# Railway MySQL plugin internal hostname (services in same project)
_railway_mysql_host = 'mysql.railway.internal' if _on_railway_early else 'localhost'

MYSQL_CONFIG = {
    'host':     (_url_cfg.get('host')
                 or os.environ.get('MYSQL_HOST')
                 or os.environ.get('MYSQLHOST')
                 or os.environ.get('DB_HOST')
                 or _railway_mysql_host),
    'port':     int(_url_cfg.get('port')
                    or os.environ.get('MYSQL_PORT')
                    or os.environ.get('MYSQLPORT')
                    or os.environ.get('DB_PORT', 3306)),
    'user':     (_url_cfg.get('user')
                 or os.environ.get('MYSQL_USER')
                 or os.environ.get('MYSQLUSER')
                 or os.environ.get('DB_USER', 'root')),
    'password': (_url_cfg.get('password')
                 or os.environ.get('MYSQL_PASSWORD')
                 or os.environ.get('MYSQLPASSWORD')
                 or os.environ.get('MYSQL_ROOT_PASSWORD')
                 or os.environ.get('DB_PASSWORD', '')),
    'database': (_url_cfg.get('database')
                 or os.environ.get('MYSQL_DATABASE')
                 or os.environ.get('MYSQLDATABASE')
                 or os.environ.get('DB_NAME', 'railway')),
    'autocommit':      False,
    'charset':         'utf8mb4',
    'connect_timeout': 5,
}
print(f'[NexaAI] MySQL target: {MYSQL_CONFIG["host"]}:{MYSQL_CONFIG["port"]}/{MYSQL_CONFIG["database"]} (user={MYSQL_CONFIG["user"]})')

# ═══════════════════════════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder='.', static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.environ.get('SECRET_KEY', 'nexaai-dev-secret-2024')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
CORS(app, supports_credentials=True, origins='*')

# On Railway (HTTPS) cookies need Secure+SameSite=None
# Locally (HTTP) use Lax so sessions still work
_on_railway = bool(
    os.environ.get('RAILWAY_ENVIRONMENT') or
    os.environ.get('RAILWAY_SERVICE_ID') or
    os.environ.get('RAILWAY_PROJECT_ID') or
    os.environ.get('RAILWAY_STATIC_URL')
)
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
    """Return a MySQL connection."""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return _Conn(conn, is_sqlite=False)
    except Exception as e:
        print(f'[ERROR] MySQL connection failed: {e}')
        return None


def _sql(mysql_sql):
    """Return MySQL SQL as-is (MySQL-only mode)."""
    return mysql_sql


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
        db_type = 'MySQL'
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
        return jsonify({'error': 'Server is starting up, please try again in a few seconds.'}), 503

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
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Please enter both email and password'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Server is starting up, please try again in a few seconds.'}), 503

    cursor = conn.cursor()

    try:
        cursor.execute('SELECT id, name, email, password, role FROM users WHERE email=%s', (data['email'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'No account found with this email address'}), 401
        
        user_id, name, email, password_hash, role = user[0], user[1], user[2], user[3], user[4]
        
        if not check_password_hash(password_hash, data['password']):
            return jsonify({'error': 'Incorrect password. Please try again or use "Forgot password?"'}), 401
        
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
        return jsonify({'error': 'Login failed. Please try again'}), 500
    
    finally:
        cursor.close()
        conn.close()


@app.route('/api/db-status', methods=['GET'])
def db_status():
    """Diagnostic: show DB config and connection status (no passwords)."""
    status = {
        'host':     MYSQL_CONFIG['host'],
        'port':     MYSQL_CONFIG['port'],
        'user':     MYSQL_CONFIG['user'],
        'database': MYSQL_CONFIG['database'],
        'connected': False,
        'tables': [],
        'user_count': 0,
        'error': None,
    }
    try:
        conn = get_db()
        if not conn:
            status['error'] = 'get_db() returned None'
            return jsonify(status), 500
        cur = conn.cursor()
        cur.execute('SHOW TABLES')
        status['tables'] = [r[0] for r in cur.fetchall()]
        cur.execute('SELECT COUNT(*) FROM users') if 'users' in status['tables'] else None
        row = cur.fetchone() if 'users' in status['tables'] else None
        status['user_count'] = row[0] if row else 0
        status['connected'] = True
        cur.close()
        conn.close()
    except Exception as e:
        status['error'] = str(e)
    return jsonify(status), 200 if status['connected'] else 500


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
    except Exception as e:
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
        cursor.execute('SELECT id, name FROM users WHERE email = %s', (email,))
        
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
        
        cursor.execute(
            'UPDATE users SET password = %s WHERE id = %s',
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
    return jsonify({'ok': True}), 200


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
    VALID_ROLES = list(ROLE_REQUIREMENTS.keys())
    
    if request.method == 'POST':
        data = request.get_json()
        role = data.get('role', 'ai')
    else:
        role = request.args.get('role', 'ai')
    
    # Validate role
    if role not in VALID_ROLES:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400
    
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


# ═══════════════════════════════════════════════════════════════════════
# AI Chatbot (Gemini)
# ═══════════════════════════════════════════════════════════════════════

def _local_chat_fallback(user_message, user_name='User'):
    """Return a lightweight career-focused fallback response when AI provider is unavailable."""
    msg = (user_message or '').strip().lower()

    if msg in {'hi', 'hii', 'hello', 'hey', 'good morning', 'good evening'}:
        return (
            f"Hi {user_name}! I can help with AI/ML skill planning, resume tips, interview prep, "
            "and learning roadmaps. Tell me your current level and target role."
        )

    ai_ml_keywords = [
        'ai', 'ml', 'machine learning', 'deep learning', 'data science',
        'nlp', 'computer vision', 'genai', 'llm'
    ]
    if any(k in msg for k in ai_ml_keywords):
        return (
            "Great choice. To build strong AI/ML skills, follow this order: "
            "1) Python + SQL basics, 2) Statistics and probability, "
            "3) Machine learning with scikit-learn, 4) Deep learning with PyTorch/TensorFlow, "
            "5) Projects (NLP/CV), 6) Resume + GitHub portfolio. "
            "Share your current skill level and I will create a 30-day plan."
        )

    return (
        "I can assist with career and skill growth: skill-gap guidance, learning paths, "
        "resume optimization, and interview preparation. Ask me about a role, topic, or study plan."
    )

@app.route('/api/chat', methods=['POST'])
@require_login
def chat_with_ai():
    """Chat with AI assistant powered by Google Gemini"""
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    conversation_history = data.get('history', [])
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    if len(user_message) > 2000:
        return jsonify({'error': 'Message too long (max 2000 characters)'}), 400
    
    if not GEMINI_AVAILABLE:
        return jsonify({
            'response': _local_chat_fallback(user_message, session.get('user_name', 'User')),
            'success': True,
            'fallback': True
        }), 200
    
    try:
        # Build context with user info and conversation history
        user_name = session.get('user_name', 'User')
        
        system_prompt = f"""You are NexaAI Assistant, a helpful career and skills advisor for the NexaAI platform.
Your role is to help users with:
- Career guidance and skill development advice
- Resume writing and optimization tips
- Interview preparation and practice
- Technical questions related to their learning path
- Job search strategies

Be friendly, professional, and concise. Keep responses under 200 words unless the user asks for more detail.
The user's name is {user_name}. Address them by name occasionally to be personable.

If asked about topics unrelated to career/skills/learning, politely redirect the conversation to career-related topics."""

        # Build conversation context
        messages = [system_prompt]
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            role = "User" if msg.get('role') == 'user' else "Assistant"
            messages.append(f"{role}: {msg.get('content', '')}")
        messages.append(f"User: {user_message}")
        
        full_prompt = "\n\n".join(messages)
        
        # Generate response
        response = GEMINI_MODEL.generate_content(full_prompt)
        ai_response = (getattr(response, 'text', None) or '').strip()

        if not ai_response:
            ai_response = _local_chat_fallback(user_message, user_name)
        
        return jsonify({
            'response': ai_response,
            'success': True
        }), 200
        
    except Exception as e:
        print(f'[ERROR] Chat error: {e}')
        return jsonify({
            'response': _local_chat_fallback(user_message, session.get('user_name', 'User')),
            'success': True,
            'fallback': True
        }), 200


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
    """Create a Stripe payment intent"""
    data = request.get_json()
    plan_id = data.get('plan_id', '')
    amount = data.get('amount', 0)
    
    # Stripe requires amount in cents
    amount_cents = int(amount * 100)
    
    try:
        import stripe
        # Test mode key (safe to commit - it's public)
        stripe.api_key = 'sk_test_51QzLxXP8bBGx9e1EYourTestKeyHere'  # Replace with your test key
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency='inr',  # Change to 'usd' if needed
            metadata={
                'user_id': session['user_id'],
                'plan_id': plan_id
            }
        )
        
        return jsonify({
            'success': True,
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
            'amount': amount,
            'plan_id': plan_id
        }), 200
        
    except Exception as e:
        print(f'[NexaAI] Stripe error: {e}')
        # Fallback to demo mode if Stripe not installed
        import uuid
        return jsonify({
            'success': True,
            'client_secret': f'demo_{uuid.uuid4().hex}',
            'payment_intent_id': f'pi_demo_{uuid.uuid4().hex[:12]}',
            'amount': amount,
            'plan_id': plan_id,
            'demo_mode': True
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
# Resume Maker — Parse Old Resume
# ═══════════════════════════════════════════════════════════════════════

@app.route('/api/parse-old-resume', methods=['POST'])
@require_login
def parse_old_resume():
    """Parse an uploaded old resume and return structured data for the AI Resume Maker."""
    file = request.files.get('resume') or request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'No file uploaded'}), 400

    filename = file.filename
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ('pdf', 'docx', 'txt'):
        return jsonify({'error': 'Only PDF, DOCX or TXT files are supported'}), 400

    safe_name = secure_filename(filename)
    filepath  = os.path.join(app.config['UPLOAD_FOLDER'], 'maker_' + safe_name)
    file.save(filepath)

    try:
        result = parse_resume_structured(filepath, filename)
        if not result:
            return jsonify({'error': 'Could not extract content from the file. '
                            'Try a text-based PDF or DOCX (not scanned images).'}), 422
        return jsonify(result), 200
    except Exception as e:
        print(f'[ERROR] parse-old-resume: {e}')
        return jsonify({'error': 'Parsing failed — please try a DOCX file for best results'}), 500
    finally:
        try:
            os.remove(filepath)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
# AI Resume Maker
# ═══════════════════════════════════════════════════════════════════════

def _generate_summary(role_title, skills, matching):
    top = (matching or skills)[:4]
    skills_str = ', '.join(top) if top else 'modern technologies'
    templates = [
        f"Results-driven {role_title} with expertise in {skills_str}. Proven track record of delivering high-impact solutions and driving measurable outcomes through innovative technical approaches and strong cross-functional collaboration.",
        f"Dynamic {role_title} specializing in {skills_str}. Passionate about leveraging cutting-edge technologies to solve complex problems and deliver scalable, production-ready solutions in fast-paced environments.",
        f"Experienced {role_title} proficient in {skills_str}. Adept at building end-to-end solutions, collaborating across teams, and driving continuous improvement through data-driven decision-making and best engineering practices.",
    ]
    import random as _r
    return _r.choice(templates)


def _enhance_bullet(bullet):
    verbs = ['Developed', 'Built', 'Implemented', 'Designed', 'Led', 'Optimized',
             'Delivered', 'Increased', 'Reduced', 'Improved', 'Automated', 'Architected']
    import random as _r
    if bullet and not any(bullet.startswith(v) for v in verbs):
        bullet = f"{_r.choice(verbs)} {bullet[0].lower()}{bullet[1:]}"
    return bullet


@app.route('/api/generate-resume', methods=['POST'])
@require_login
def generate_resume():
    data = request.get_json() or {}
    target_role    = data.get('target_role', 'ai')
    personal       = data.get('personal', {})
    experience     = data.get('experience', [])
    education      = data.get('education', [])
    user_skills    = data.get('skills', [])
    custom_summary = data.get('summary', '').strip()
    exp_years      = data.get('experience_years') or 0
    try:
        exp_years = float(exp_years)
    except Exception:
        exp_years = 0

    role_data  = ROLE_REQUIREMENTS.get(target_role, ROLE_REQUIREMENTS['ai'])
    role_title = role_data['title']
    req        = role_data['required_skills']

    all_required = []
    for cat_skills in req.values():
        all_required.extend(cat_skills)

    user_lower    = [s.lower().strip() for s in user_skills]
    matching      = [s for s in all_required if any(s in u or u in s for u in user_lower)]
    missing       = [s for s in all_required if s not in matching]

    # Auto-add top missing keywords to skills to push ATS score over 91
    ats_boost = [s.title() for s in missing[:6]]
    all_skills = list(user_skills) + ats_boost

    # Categorize
    tech_keys  = [s.lower() for s in req.get('technical', [])]
    tool_keys  = [s.lower() for s in req.get('tools', [])]
    soft_keys  = [s.lower() for s in req.get('soft_skills', [])]

    tech_skills = [s for s in all_skills if s.lower().strip() in tech_keys]
    tool_skills = [s for s in all_skills if s.lower().strip() in tool_keys]
    soft_skills_list = [s for s in all_skills if s.lower().strip() in soft_keys]
    other       = [s for s in all_skills if s not in tech_skills + tool_skills + soft_skills_list]

    summary = custom_summary or _generate_summary(role_title, user_skills, matching)

    enhanced_exp = []
    for exp in experience:
        e = dict(exp)
        e['bullets'] = [_enhance_bullet(b) for b in exp.get('bullets', [])]
        enhanced_exp.append(e)

    # ATS score calculation (always 91-98)
    kw_score     = min(40, 20 + len(matching) * 2)
    struct_score = 20 if enhanced_exp and education else (15 if enhanced_exp or education else 10)
    summary_sc   = 10
    contact_sc   = 8 if personal.get('email') else 5
    fmt_sc       = 15
    skill_sc     = min(10, len(user_skills))
    raw_score    = kw_score + struct_score + summary_sc + contact_sc + fmt_sc + skill_sc
    ats_score    = max(91, min(98, raw_score))

    # Smart Format: < 9 years = 1 Page, 9+ years = 2 Pages (Senior format)
    two_page = exp_years >= 9

    return jsonify({
        'resume': {
            'personal': personal,
            'summary':  summary,
            'experience': enhanced_exp,
            'education':  education,
            'skills': {
                'technical': tech_skills + other,
                'tools':     tool_skills,
                'soft':      soft_skills_list,
            },
            'role_title':     role_title,
            'experience_years': exp_years,
            'two_page':       two_page,
        },
        'ats_score':        ats_score,
        'matched_keywords': len(matching),
        'total_keywords':   len(all_required),
        'role_title':       role_title,
        'two_page':         two_page,
    }), 200


@app.route('/api/last-analysis', methods=['GET'])
@require_login
def last_analysis():
    """Return the user's most recent skill gap analysis from DB"""
    user_id = session['user_id']
    conn = get_db()
    if not conn:
        return jsonify({'analysis': None}), 200
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT role, missing_skills, priority_areas, created_at FROM skill_gaps WHERE user_id=%s ORDER BY id DESC LIMIT 1',
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'analysis': None}), 200
        role_key = row[0]
        # Re-run analysis with stored skills to get full picture
        cursor.execute(
            'SELECT extracted_skills FROM resumes WHERE user_id=%s ORDER BY id DESC LIMIT 1',
            (user_id,)
        )
        resume_row = cursor.fetchone()
        student_skills = []
        if resume_row and resume_row[0]:
            try:
                student_skills = json.loads(resume_row[0])
            except Exception:
                pass
        gap_analysis = analyze_skills(student_skills, role_key)
        return jsonify({'analysis': gap_analysis}), 200
    except Exception as e:
        print(f'[ERROR] last-analysis: {e}')
        return jsonify({'analysis': None}), 200
    finally:
        cursor.close()
        conn.close()


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
# Startup — run init_db in background so gunicorn starts immediately
# (avoids healthcheck failure when MySQL is slow to accept connections)
# ═══════════════════════════════════════════════════════════════════════

import threading

print('\n' + '='*70)
print(' NexaAI — AI-Driven Skill Gap Platform')
print(' Starting...')
print('='*70)

def _startup():
    import time
    print(f'[NexaAI] DB init starting — host={MYSQL_CONFIG["host"]} db={MYSQL_CONFIG["database"]} user={MYSQL_CONFIG["user"]}')
    # Retry up to 8 times with 5-second gaps so Railway MySQL has time to start
    for attempt in range(1, 9):
        try:
            conn = get_db()
            if conn:
                conn.close()
                init_db()
                print('[NexaAI] Database ready — all tables and admin user created.')
                return
            print(f'[NexaAI] DB not ready (attempt {attempt}/8), retrying in 5s...')
        except Exception as e:
            print(f'[NexaAI] DB init error attempt {attempt}: {e}')
        time.sleep(5)
    print(f'[NexaAI] ERROR: Could not connect to MySQL at {MYSQL_CONFIG["host"]} after 8 attempts.')
    print('[NexaAI] On Railway: add variable MYSQL_URL = ${{MySQL.MYSQL_URL}} to this service.')

threading.Thread(target=_startup, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════
# Main (direct run only — gunicorn uses the module directly)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=not _on_railway, host='0.0.0.0', port=port, use_reloader=False)
