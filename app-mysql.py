"""
ResumeAI - Career Intelligence Platform
Main Flask Application with MySQL Database
"""
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error, pooling
import os
import json
from datetime import datetime, timedelta
import re
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utility modules
from resume_parser import parse_resume, extract_skills_from_text
from skill_analyzer import analyze_skill_gap, get_role_requirements
from ai_service import generate_interview_feedback, generate_learning_path

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'resumeai-secret-key-change-in-production')
CORS(app, supports_credentials=True)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# MySQL Configuration
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'resumeai'),
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Create connection pool for better performance
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="resumeai_pool",
        pool_size=5,
        pool_reset_session=True,
        **MYSQL_CONFIG
    )
    print("✅ MySQL Connection Pool created successfully!")
except Error as e:
    print(f"❌ Error creating connection pool: {e}")
    connection_pool = None

# ============== Database Functions ==============

def get_db():
    """Get database connection from pool"""
    try:
        if connection_pool:
            return connection_pool.get_connection()
        else:
            return mysql.connector.connect(**MYSQL_CONFIG)
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def dict_cursor(cursor, data):
    """Convert MySQL cursor result to dictionary"""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in data]

def init_db():
    """Initialize MySQL database with tables"""
    conn = get_db()
    if not conn:
        print("❌ Failed to connect to MySQL!")
        return
    
    cursor = conn.cursor()
    
    try:
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        cursor.execute(f"USE {MYSQL_CONFIG['database']}")
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_role (role)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Resumes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                raw_text LONGTEXT,
                parsed_data LONGTEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Skills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_skills (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                resume_id INT,
                skill_name VARCHAR(255) NOT NULL,
                category VARCHAR(50),
                proficiency INT DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_skill_name (skill_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Skill Gap Analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_analysis (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                target_role VARCHAR(100) NOT NULL,
                match_score INT,
                skills_have TEXT,
                skills_missing TEXT,
                skills_priority TEXT,
                tech_score INT,
                tools_score INT,
                soft_score INT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_target_role (target_role)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Diagnostic Tests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnostic_tests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                skill_name VARCHAR(255) NOT NULL,
                question TEXT NOT NULL,
                options TEXT,
                correct_answer VARCHAR(255),
                difficulty VARCHAR(50) DEFAULT 'medium',
                INDEX idx_skill_name (skill_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Test Results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                skill_name VARCHAR(255) NOT NULL,
                score INT,
                total_questions INT,
                taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Interview Sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                target_role VARCHAR(100),
                questions_answered INT DEFAULT 0,
                total_score INT DEFAULT 0,
                feedback TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Learning Progress
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                skill_name VARCHAR(255) NOT NULL,
                resource_type VARCHAR(100),
                resource_url TEXT,
                completed TINYINT DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                plan_type VARCHAR(50) NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                payment_id VARCHAR(255),
                payment_method VARCHAR(50),
                status VARCHAR(50) DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                payment_id VARCHAR(255) UNIQUE,
                payment_method VARCHAR(50),
                status VARCHAR(50) DEFAULT 'pending',
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_payment_id (payment_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # Create default admin user if not exists
        cursor.execute('SELECT id FROM users WHERE email = %s', ('admin@resumeai.com',))
        if not cursor.fetchone():
            admin_password = generate_password_hash('admin123')
            cursor.execute(
                'INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)',
                ('Admin', 'admin@resumeai.com', admin_password, 'admin')
            )
            print("✅ Default admin created - Email: admin@resumeai.com, Password: admin123")
        
        conn.commit()
        print("✅ Database initialized successfully!")
        
    except Error as e:
        print(f"❌ Error initializing database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============== Routes ==============

@app.route('/')
def index():
    """Serve the enhanced HTML file"""
    return send_from_directory('.', 'index-enhanced.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

# ---------- Authentication Routes ----------

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if email exists
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Create user
        hashed_password = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
            (name, email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        # Set session
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        session['user_role'] = 'student'
        
        return jsonify({
            'success': True,
            'user': {'id': user_id, 'name': name, 'email': email, 'role': 'student'}
        })
        
    except Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('SELECT id, name, email, password, role FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Set session
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        })
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/user', methods=['GET'])
def get_user():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    return jsonify({
        'success': True,
        'user': {
            'id': session['user_id'],
            'name': session['user_name'],
            'email': session['user_email'],
            'role': session.get('user_role', 'student')
        }
    })

# ---------- Resume Routes ----------

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """Upload and parse resume"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. Use PDF, DOC, or DOCX'}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Save file
        filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse resume
        raw_text, parsed_data = parse_resume(filepath)
        
        # Save to database
        cursor.execute(
            'INSERT INTO resumes (user_id, filename, raw_text, parsed_data) VALUES (%s, %s, %s, %s)',
            (session['user_id'], filename, raw_text, json.dumps(parsed_data))
        )
        resume_id = cursor.lastrowid
        
        # Save extracted skills
        for skill in parsed_data.get('skills', []):
            cursor.execute(
                'INSERT INTO user_skills (user_id, resume_id, skill_name, category) VALUES (%s, %s, %s, %s)',
                (session['user_id'], resume_id, skill['name'], skill.get('category', 'technical'))
            )
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'resume_id': resume_id,
            'parsed_data': parsed_data
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------- Skill Analysis Routes ----------

@app.route('/api/analyze-skills', methods=['POST'])
def analyze_skills():
    """Analyze skill gap for a target role"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.json
    target_role = data.get('target_role', 'ai')
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user's skills from latest resume
        cursor.execute('''
            SELECT DISTINCT skill_name, category FROM user_skills 
            WHERE user_id = %s 
            ORDER BY id DESC
        ''', (session['user_id'],))
        user_skills = [{'name': row['skill_name'], 'category': row['category']} for row in cursor.fetchall()]
        
        if not user_skills:
            return jsonify({'success': False, 'error': 'No resume uploaded yet. Please upload your resume first.'}), 400
        
        # Get role requirements and analyze gap
        analysis = analyze_skill_gap(user_skills, target_role)
        
        # Save analysis
        cursor.execute('''
            INSERT INTO skill_analysis 
            (user_id, target_role, match_score, skills_have, skills_missing, skills_priority, tech_score, tools_score, soft_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            session['user_id'],
            target_role,
            analysis['match_score'],
            json.dumps(analysis['skills_have']),
            json.dumps(analysis['skills_missing']),
            json.dumps(analysis['skills_priority']),
            analysis['tech_score'],
            analysis['tools_score'],
            analysis['soft_score']
        ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/role-requirements/<role>', methods=['GET'])
def get_role_reqs(role):
    """Get skill requirements for a role"""
    requirements = get_role_requirements(role)
    return jsonify({'success': True, 'requirements': requirements})

# ---------- Payment Routes ----------

@app.route('/api/payment/plans', methods=['GET'])
def get_payment_plans():
    """Get available subscription plans"""
    plans = [
        {
            'id': 'basic',
            'name': 'Basic',
            'price': 499,
            'duration': '1 month',
            'features': [
                'Resume Analysis',
                'Skill Gap Report',
                '5 Mock Interviews',
                'Basic Learning Path',
                'Email Support'
            ]
        },
        {
            'id': 'pro',
            'name': 'Professional',
            'price': 999,
            'duration': '3 months',
            'features': [
                'Everything in Basic',
                'Unlimited Mock Interviews',
                'AI Interview Feedback',
                'Personalized Learning Path',
                'Priority Support',
                'ATS Resume Optimization'
            ],
            'popular': True
        },
        {
            'id': 'premium',
            'name': 'Premium',
            'price': 1999,
            'duration': '6 months',
            'features': [
                'Everything in Professional',
                'One-on-One Mentorship',
                'Company-Specific Preparation',
                'Project Review & Guidance',
                '24/7 Support',
                'Placement Assistance',
                'Certificate of Completion'
            ]
        }
    ]
    return jsonify({'success': True, 'plans': plans})

@app.route('/api/payment/create-order', methods=['POST'])
def create_payment_order():
    """Create payment order"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.json
    plan_id = data.get('plan_id')
    amount = data.get('amount')
    
    # Generate unique payment ID
    payment_id = f"PAY_{secrets.token_hex(8).upper()}"
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        # Create payment record
        cursor.execute(
            'INSERT INTO payments (user_id, amount, payment_id, status) VALUES (%s, %s, %s, %s)',
            (session['user_id'], amount, payment_id, 'pending')
        )
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'order_id': payment_id,
            'amount': amount,
            'currency': 'INR'
        })
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/payment/verify', methods=['POST'])
def verify_payment():
    """Verify and complete payment"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.json
    payment_id = data.get('payment_id')
    plan_id = data.get('plan_id')
    payment_method = data.get('payment_method', 'razorpay')
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Update payment status
        cursor.execute(
            'UPDATE payments SET status = %s, payment_method = %s WHERE payment_id = %s',
            ('completed', payment_method, payment_id)
        )
        
        # Get payment amount
        cursor.execute('SELECT amount FROM payments WHERE payment_id = %s', (payment_id,))
        payment = cursor.fetchone()
        
        if payment:
            amount = payment['amount']
            
            # Create subscription
            duration_map = {'basic': 30, 'pro': 90, 'premium': 180}
            duration_days = duration_map.get(plan_id, 30)
            end_date = datetime.now() + timedelta(days=duration_days)
            
            cursor.execute('''
                INSERT INTO subscriptions (user_id, plan_type, amount, payment_id, payment_method, end_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (session['user_id'], plan_id, amount, payment_id, payment_method, end_date))
            
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment verified successfully',
            'subscription_active': True
        })
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/subscription/status', methods=['GET'])
def get_subscription_status():
    """Get user subscription status"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT plan_type, end_date, status 
            FROM subscriptions 
            WHERE user_id = %s AND status = 'active'
            ORDER BY end_date DESC LIMIT 1
        ''', (session['user_id'],))
        
        subscription = cursor.fetchone()
        
        if subscription:
            return jsonify({
                'success': True,
                'has_subscription': True,
                'plan': subscription['plan_type'],
                'end_date': subscription['end_date'].isoformat() if subscription['end_date'] else None,
                'status': subscription['status']
            })
        else:
            return jsonify({
                'success': True,
                'has_subscription': False
            })
            
    finally:
        cursor.close()
        conn.close()

# ---------- Admin Routes ----------

@app.route('/api/admin/analytics', methods=['GET'])
def get_admin_analytics():
    """Get analytics for admin dashboard"""
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Total users
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "student"')
        total_users = cursor.fetchone()['count']
        
        # Resumes analyzed
        cursor.execute('SELECT COUNT(*) as count FROM resumes')
        total_resumes = cursor.fetchone()['count']
        
        # Total revenue
        cursor.execute('SELECT SUM(amount) as total FROM payments WHERE status = "completed"')
        result = cursor.fetchone()
        total_revenue = float(result['total']) if result['total'] else 0
        
        # Active subscriptions
        cursor.execute('SELECT COUNT(*) as count FROM subscriptions WHERE status = "active"')
        active_subs = cursor.fetchone()['count']
        
        # Average match score by role
        cursor.execute('''
            SELECT target_role, AVG(match_score) as avg_score, COUNT(*) as count
            FROM skill_analysis
            GROUP BY target_role
        ''')
        role_stats = cursor.fetchall()
        
        # Recent users
        cursor.execute('''
            SELECT id, name, email, created_at FROM users 
            WHERE role = "student"
            ORDER BY created_at DESC LIMIT 10
        ''')
        recent_users = cursor.fetchall()
        
        # Revenue by plan
        cursor.execute('''
            SELECT plan_type, COUNT(*) as count, SUM(amount) as revenue
            FROM subscriptions
            WHERE status = "active"
            GROUP BY plan_type
        ''')
        revenue_by_plan = cursor.fetchall()
        
        # Common skill gaps
        cursor.execute('''
            SELECT skills_missing FROM skill_analysis
            ORDER BY analyzed_at DESC LIMIT 100
        ''')
        all_missing = []
        for row in cursor.fetchall():
            missing = json.loads(row['skills_missing'])
            all_missing.extend(missing)
        
        # Count frequency
        skill_gaps = {}
        for skill in all_missing:
            skill_gaps[skill] = skill_gaps.get(skill, 0) + 1
        
        common_gaps = sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_users': total_users,
                'total_resumes': total_resumes,
                'total_revenue': total_revenue,
                'active_subscriptions': active_subs,
                'role_stats': role_stats,
                'common_skill_gaps': common_gaps,
                'recent_users': recent_users,
                'revenue_by_plan': revenue_by_plan
            }
        })
        
    finally:
        cursor.close()
        conn.close()

@app.route('/api/user-stats', methods=['GET'])
def get_user_stats():
    """Get user statistics for dashboard"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Count resumes
        cursor.execute('SELECT COUNT(*) as count FROM resumes WHERE user_id = %s', (session['user_id'],))
        resumes_count = cursor.fetchone()['count']
        
        # Get latest match score
        cursor.execute('''
            SELECT match_score FROM skill_analysis 
            WHERE user_id = %s 
            ORDER BY analyzed_at DESC LIMIT 1
        ''', (session['user_id'],))
        result = cursor.fetchone()
        match_score = result['match_score'] if result else None
        
        # Count skills
        cursor.execute('SELECT COUNT(DISTINCT skill_name) as count FROM user_skills WHERE user_id = %s', (session['user_id'],))
        skills_count = cursor.fetchone()['count']
        
        # Count interviews
        cursor.execute('SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = %s', (session['user_id'],))
        interviews_count = cursor.fetchone()['count']
        
        return jsonify({
            'success': True,
            'stats': {
                'resumes': resumes_count,
                'match_score': match_score,
                'skills': skills_count,
                'interviews': interviews_count
            }
        })
        
    finally:
        cursor.close()
        conn.close()

# ============== Initialize and Run ==============

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting ResumeAI Server with MySQL Database")
    print("="*60 + "\n")
    
    # Initialize database
    init_db()
    
    print("\n" + "="*60)
    print("✅ Server is ready!")
    print("📱 Access the application at: http://localhost:5000")
    print("🔐 Admin Login: admin@resumeai.com / admin123")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
