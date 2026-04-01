"""
Quick MySQL connection test
Run: python test_mysql.py
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded .env file")
except ImportError:
    print("⚠ python-dotenv not installed, using system env vars")
    print("  Run: pip install python-dotenv")

import mysql.connector
from mysql.connector import Error

# Get credentials from environment
config = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'resumeai'),
}

print(f"\nConnecting to MySQL...")
print(f"  Host: {config['host']}:{config['port']}")
print(f"  User: {config['user']}")
print(f"  Database: {config['database']}")

try:
    conn = mysql.connector.connect(**config)
    if conn.is_connected():
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"\n✓ MySQL Connected Successfully!")
        print(f"  Server Version: {version}")
        
        # Check if database exists
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if tables:
            print(f"  Tables: {', '.join([t[0] for t in tables])}")
        else:
            print("  No tables yet (will be created on first run)")
        
        cursor.close()
        conn.close()
        print("\n✅ MySQL connection test PASSED!")
        print("   You can now run: python app.py")
except Error as e:
    print(f"\n❌ MySQL Connection FAILED!")
    print(f"   Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Is MySQL server running?")
    print("  2. Check your .env file has correct credentials")
    print("  3. Make sure the database 'resumeai' exists:")
    print("     mysql -u root -p -e 'CREATE DATABASE IF NOT EXISTS resumeai;'")
