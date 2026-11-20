import os
from dotenv import load_dotenv

# Explicitly load .env from the project directory
basedir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(basedir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'eventease-super-secret-key-2025-portfolio')
    
    # Primary Database Engine: 'mysql' (default)
    DB_ENGINE = os.environ.get('DB_ENGINE', 'mysql').lower()
    
    # MySQL Database Settings (Loaded strictly from environment variables without hardcoded passwords)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'eventease_db')
    
    # Optional SQLite DB Path (Used ONLY when DB_ENGINE=sqlite is explicitly requested)
    SQLITE_DB_PATH = os.path.join(basedir, 'eventease.db')
    
    # Application settings
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'images', 'banners')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Session lifetime
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
