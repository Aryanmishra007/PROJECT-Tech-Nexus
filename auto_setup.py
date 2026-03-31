"""
NexaAI - Auto Setup Script
Automatically creates and initializes the MySQL database with admin user
"""

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
import time

# MySQL Configuration
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Aryan@2007',
}

DB_NAME = 'projectnexai_ai'

def connect_mysql():
    """Connect to MySQL server"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        print(f"[ERROR] MySQL Connection failed: {e}")
        return None

def setup_database():
    """Setup database and tables"""
    conn = connect_mysql()
    if not conn:
        print("[ERROR] Cannot connect to MySQL!")
        print("\nMake sure:")
        print("  1. MySQL is running (Windows Services > MySQL80)")
        print("  2. MySQL credentials are correct")
        print("     Host: 127.0.0.1")
        print("     User: root")
        print("     Password: Aryan@2007")
        return False
    
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*70)
        print(" NexaAI - Auto Database Setup")
        print("="*70)
        
        # Step 1: Drop old database
        print("\n[1/4] Dropping old database...")
        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
            conn.commit()
            print("      [OK] Old database dropped")
        except Error as e:
            print(f"      [WARN] {e}")
        
        # Step 2: Create new database
        print("\n[2/4] Creating fresh database...")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        conn.commit()
        print("      [OK] Database created")
        
        # Step 3: Create tables
        print("\n[3/4] Creating tables...")
        
        tables = [
            '''CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('student','admin') DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            
            '''CREATE TABLE resumes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255),
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extracted_skills JSON,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''',
            
            '''CREATE TABLE skill_gaps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role VARCHAR(255),
                missing_skills JSON,
                priority_areas JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''',
            
            '''CREATE TABLE diagnostic_tests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                skill_area VARCHAR(255),
                questions JSON,
                answers JSON,
                score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''',
            
            '''CREATE TABLE learning_paths (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                role VARCHAR(255),
                path_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''',
            
            '''CREATE TABLE subscriptions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                plan VARCHAR(50),
                amount DECIMAL(10,2),
                status VARCHAR(50),
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )''',
            
            '''CREATE TABLE payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(10,2),
                plan VARCHAR(50),
                transaction_id VARCHAR(255),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )'''
        ]
        
        for i, table_sql in enumerate(tables, 1):
            cursor.execute(table_sql)
        
        conn.commit()
        print(f"      [OK] {len(tables)} tables created")
        
        # Step 4: Create admin user
        print("\n[4/4] Creating admin user...")
        
        admin_email = 'arynmishra2007@gmail.com'
        admin_password = 'Aryan!2007'
        admin_hash = generate_password_hash(admin_password)
        
        cursor.execute(
            'INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)',
            ('Admin', admin_email, admin_hash, 'admin')
        )
        conn.commit()
        
        print(f"      [OK] Admin user created")
        print(f"        Email: {admin_email}")
        print(f"        Password: {admin_password}")
        
        # Verify
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        
        print("\n" + "="*70)
        print(" [SUCCESS] SETUP COMPLETE!")
        print("="*70)
        print(f"\nDatabase: {DB_NAME}")
        print(f"Tables: 7")
        print(f"Users: {count}")
        print(f"\nAdmin Credentials:")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        print("\nNow run: python app.py")
        print("Then open: http://localhost:5000")
        print("\n" + "="*70 + "\n")
        
        return True
    
    except Error as e:
        print(f"\n[ERROR] Setup failed: {e}")
        return False
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = setup_database()
    exit(0 if success else 1)
