"""
Quick MySQL Connection Test
Run this to verify MySQL is working before starting the app
"""

import os
from dotenv import load_dotenv
load_dotenv()

try:
    import mysql.connector
    from mysql.connector import Error
    
    print("🔍 Testing MySQL connection...")
    print(f"   Host: {os.environ.get('MYSQL_HOST', 'localhost')}")
    print(f"   Port: {os.environ.get('MYSQL_PORT', '3306')}")
    print(f"   User: {os.environ.get('MYSQL_USER', 'root')}")
    print(f"   Database: {os.environ.get('MYSQL_DATABASE', 'resumeai')}")
    print()
    
    # Try to connect
    connection = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        database=os.environ.get('MYSQL_DATABASE', 'resumeai')
    )
    
    if connection.is_connected():
        db_info = connection.get_server_info()
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()[0]
        
        print("✅ SUCCESS! MySQL connection working!")
        print(f"   MySQL Server version: {db_info}")
        print(f"   Connected to database: {db_name}")
        print()
        print("🎉 You're ready to run the app with MySQL!")
        
        cursor.close()
        connection.close()
        
except mysql.connector.Error as e:
    print("❌ MySQL Connection Failed!")
    print(f"   Error: {e}")
    print()
    
    if "Access denied" in str(e):
        print("💡 FIX: Check your password in .env file")
        print("   MYSQL_PASSWORD=Aryan@2007")
    elif "Can't connect" in str(e) or "Unknown MySQL server host" in str(e):
        print("💡 FIX: Make sure MySQL server is running")
        print("   - Start MySQL service in Services")
        print("   - Or start XAMPP MySQL")
    elif "Unknown database" in str(e):
        print("💡 FIX: Create the database first")
        print("   Run in MySQL: CREATE DATABASE resumeai;")
    else:
        print("💡 FIX: Check your .env file settings")
        
except ImportError:
    print("❌ mysql-connector-python not installed!")
    print("💡 FIX: Run this command:")
    print("   pip install mysql-connector-python")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
