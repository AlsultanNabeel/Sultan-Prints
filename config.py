import os
from datetime import timedelta

class Config:
    # Basic Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secure-secret-key-for-development'
    
    # Database configuration
    # Use Render's DATABASE_URL in production, otherwise fall back to local MySQL for development
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        # On Render, DATABASE_URL is for PostgreSQL, but SQLAlchemy needs 'postgresql://'
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = db_url or 'mysql+pymysql://root:password@localhost/tshirt_store?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    
    # Session Config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    # Only use secure cookies in production (when FLASK_ENV is 'production')
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Email Config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'ohnabeel@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = 'ohnabeel@gmail.com'
    
    # Payment Config
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    VODAFONE_CASH_NUMBER = '01023820614'
    
    # Admin Credentials (Load from environment variables, with fallback for development)
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@tshirtshop.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'superadmin123')
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
    }