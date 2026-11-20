"""
EventEase Database Connection Diagnostic Script
Run this script to verify your MySQL configuration:
    python check_db.py
"""
import sys
from config import Config

def test_mysql_connection():
    print("=" * 65)
    print("EventEase - MySQL Connection Diagnostic Tool")
    print("=" * 65)
    print(f"Target Host:     {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
    print(f"Target User:     {Config.MYSQL_USER}")
    print(f"Target Database: {Config.MYSQL_DB}")
    print(f"Password Set:    {'YES' if Config.MYSQL_PASSWORD else 'NO (Empty)'}")
    print("-" * 65)

    try:
        import pymysql
    except ImportError:
        print("[ERROR] 'pymysql' is not installed in the current Python environment.")
        print("Please install it by running: pip install pymysql")
        return False

    # 1. Test Server Connectivity
    try:
        print("[1/3] Connecting to MySQL server...")
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            connect_timeout=4
        )
        print("      ✓ Successfully connected to MySQL server!")
    except pymysql.err.OperationalError as e:
        code, msg = e.args
        print(f"      ✗ Connection failed! Error {code}: {msg}")
        if code == 1045:
            print("\n[ACTION REQUIRED] Access Denied (Error 1045):")
            print("  The password or username in .env does not match MySQL.")
            print("  Please open .env and update MYSQL_PASSWORD with your MySQL root password.")
        elif code == 2003:
            print("\n[ACTION REQUIRED] Can't connect to MySQL server (Error 2003):")
            print(f"  Ensure your MySQL 8.0 service is started and listening on port {Config.MYSQL_PORT}.")
        return False
    except Exception as e:
        print(f"      ✗ Unexpected connection error: {e}")
        return False

    # 2. Check / Create Database
    try:
        print(f"[2/3] Checking database `{Config.MYSQL_DB}`...")
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute(f"USE `{Config.MYSQL_DB}`;")
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]
        print(f"      ✓ Database `{Config.MYSQL_DB}` is ready! Found {len(tables)} tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"      ✗ Database check failed: {e}")
        conn.close()
        return False

    # 3. Test Full App Connection
    try:
        print("[3/3] Initializing schema and seed data...")
        from database import init_db, query_db
        init_db()
        events_count = query_db("SELECT COUNT(*) AS count FROM events", one=True)['count']
        print(f"      ✓ EventEase schema verified. Active events in database: {events_count}")
    except Exception as e:
        print(f"      ✗ Schema verification encountered an error: {e}")
        return False

    print("=" * 65)
    print("SUCCESS: Your MySQL database is properly configured and ready!")
    print("You can now run: python app.py")
    print("=" * 65)
    return True

if __name__ == '__main__':
    success = test_mysql_connection()
    sys.exit(0 if success else 1)
