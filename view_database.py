""" 
View all data stored in MySQL database
Run: python view_database.py
Made By AI(ChatGPT, Claude, Grok)
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import mysql.connector
from mysql.connector import Error

config = {
    'host':     os.environ.get('MYSQL_HOST', 'localhost'),
    'port':     int(os.environ.get('MYSQL_PORT', 3306)),
    'user':     os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'resumeai'),
}

print(f"\nConnecting to MySQL: {config['host']}:{config['port']}/{config['database']}")

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]

    if not tables:
        print("\nNo tables found in the database yet.")
        print("Start the app first so it can create the tables.")
    else:
        print(f"\nTables found: {', '.join(tables)}\n")
        print("=" * 60)

        for table in tables:
            print(f"\n TABLE: {table}")
            print("-" * 60)

            # Get column names
            cursor.execute(f"DESCRIBE `{table}`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"Columns: {', '.join(columns)}")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            print(f"Rows: {count}")

            if count > 0:
                cursor.execute(f"SELECT * FROM `{table}` LIMIT 20")
                rows = cursor.fetchall()
                print()
                # Print header
                col_widths = [max(len(str(col)), 15) for col in columns]
                header = " | ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(columns))
                print(header)
                print("-" * len(header))
                for row in rows:
                    line = " | ".join(str(v)[:col_widths[i]].ljust(col_widths[i]) for i, v in enumerate(row))
                    print(line)
                if count > 20:
                    print(f"  ... and {count - 20} more rows")
            print()

    cursor.close()
    conn.close()

except Error as e:
    print(f"\nMySQL Connection FAILED: {e}")
    print("\nMake sure:")
    print("  1. MySQL server is running")
    print("  2. Your .env file has correct credentials")
    print(f"  3. Database '{config['database']}' exists")
