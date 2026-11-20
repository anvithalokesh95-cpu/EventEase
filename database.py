import os
import sys
import sqlite3
from config import Config

# Try importing pymysql
try:
    import pymysql
    import pymysql.cursors
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False

class DatabaseManager:
    _instance = None

    def __init__(self):
        self.db_type = Config.DB_ENGINE
        self.init_engine()

    def init_engine(self):
        """
        Initializes the primary database connection.
        Enforces MySQL as primary unless explicitly set to another engine via DB_ENGINE.
        Never silently falls back to SQLite on connection or credential errors.
        """
        if self.db_type == 'sqlite':
            print(f"[EventEase DB] Running with explicit SQLite engine at {Config.SQLITE_DB_PATH}")
            return

        # Default / Primary: MySQL
        if not HAS_PYMYSQL:
            raise RuntimeError(
                "[EventEase Database Error] 'pymysql' package is not installed.\n"
                "Please run: pip install pymysql"
            )

        try:
            # 1. Test connection to MySQL server and ensure the target database exists
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                connect_timeout=5
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            conn.close()

            self.db_type = 'mysql'
            print(f"[EventEase DB] Successfully connected to MySQL at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB}")

        except Exception as e:
            error_details = (
                f"\n{'='*75}\n"
                f"[EventEase Database Error] Failed to connect to MySQL database!\n"
                f"{'='*75}\n"
                f"Connection details attempted:\n"
                f"  Host:     {Config.MYSQL_HOST}\n"
                f"  Port:     {Config.MYSQL_PORT}\n"
                f"  User:     {Config.MYSQL_USER}\n"
                f"  Database: {Config.MYSQL_DB}\n"
                f"  Password: {'[EMPTY / NOT SET]' if not Config.MYSQL_PASSWORD else '******** (provided via environment)'}\n\n"
                f"Underlying MySQL Error:\n"
                f"  {e}\n\n"
                f"How to resolve this:\n"
                f"  1. Open your '.env' file in the project root.\n"
                f"  2. Update MYSQL_PASSWORD with your MySQL root or user password:\n"
                f"       MYSQL_PASSWORD=your_actual_mysql_password\n"
                f"  3. Make sure MySQL Server is running on port {Config.MYSQL_PORT}.\n"
                f"  4. If user permissions need updating, log in with 'mysql -u root -p' and run:\n"
                f"       CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
                f"       GRANT ALL PRIVILEGES ON {Config.MYSQL_DB}.* TO '{Config.MYSQL_USER}'@'localhost';\n"
                f"       FLUSH PRIVILEGES;\n"
                f"{'='*75}\n"
            )
            # Do NOT silently fall back to SQLite; raise descriptive error
            raise RuntimeError(error_details) from e

    def get_connection(self):
        """Returns an active database connection for the configured primary engine."""
        if self.db_type == 'mysql':
            return pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
        
        # SQLite connection (only if explicitly configured)
        conn = sqlite3.connect(Config.SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def query(self, sql, params=(), one=False, commit=False):
        """
        Executes parameterized SQL queries safely.
        Returns dictionaries for result rows.
        """
        conn = self.get_connection()
        is_sqlite = (self.db_type == 'sqlite')

        executed_sql = sql
        final_params = list(params)
        if is_sqlite:
            executed_sql = sql.replace('%s', '?')
            from datetime import datetime, date
            for idx, p in enumerate(final_params):
                if isinstance(p, (datetime, date)):
                    final_params[idx] = p.strftime('%Y-%m-%d %H:%M:%S') if isinstance(p, datetime) else p.strftime('%Y-%m-%d')
        
        cursor = conn.cursor()
        try:
            cursor.execute(executed_sql, tuple(final_params))
            
            if commit:
                conn.commit()
                last_id = cursor.lastrowid
                rowcount = cursor.rowcount
                cursor.close()
                conn.close()
                return {'lastrowid': last_id, 'rowcount': rowcount}

            if one:
                row = cursor.fetchone()
                result = dict(row) if row else None
            else:
                rows = cursor.fetchall()
                if is_sqlite:
                    result = [dict(r) for r in rows]
                else:
                    result = list(rows)
            
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            if commit:
                conn.rollback()
            cursor.close()
            conn.close()
            raise e

    def init_database(self):
        """Initializes tables and basic structure depending on db_type."""
        if self.db_type == 'mysql':
            self._init_mysql_tables()
        else:
            self._init_sqlite_tables()

    def _init_mysql_tables(self):
        schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"schema.sql not found at {schema_file}")
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        statements = sql_script.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    pass
        conn.commit()
        cursor.close()
        conn.close()
        print("[EventEase DB] MySQL tables verified/initialized successfully.")

    def _init_sqlite_tables(self):
        conn = sqlite3.connect(Config.SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        sqlite_schema = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            phone TEXT NULL,
            avatar TEXT DEFAULT 'default-avatar.png',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            description TEXT NULL,
            icon TEXT DEFAULT 'fas fa-calendar-alt',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            venue_name TEXT NOT NULL,
            event_date DATETIME NOT NULL,
            banner_image TEXT NOT NULL,
            ticket_price REAL NOT NULL DEFAULT 0.00,
            total_tickets INTEGER NOT NULL,
            available_tickets INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            created_by INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
            FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_code TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            tickets_count INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            booking_status TEXT DEFAULT 'confirmed',
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cancellation_date DATETIME NULL,
            notes TEXT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL UNIQUE,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'credit_card',
            payment_status TEXT DEFAULT 'completed',
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        );
        """
        cursor.executescript(sqlite_schema)
        conn.commit()
        cursor.close()
        conn.close()
        print("[EventEase DB] SQLite tables verified/initialized.")


# Singleton helper
db_manager = DatabaseManager()

def get_db():
    return db_manager.get_connection()

def query_db(query, args=(), one=False, commit=False):
    return db_manager.query(query, args, one=one, commit=commit)

def init_db():
    db_manager.init_database()
