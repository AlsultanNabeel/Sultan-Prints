import os
from datetime import timedelta
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# DEBUG: طباعة المتغيرات البيئية
print("=== ENVIRONMENT VARIABLES ===")
print(f"SECRET_KEY: {os.environ.get('SECRET_KEY', 'NOT SET')[:20]}...")
print(f"ADMIN_EMAIL: {os.environ.get('ADMIN_EMAIL', 'NOT SET')}")
print(f"ADMIN_PASSWORD: {os.environ.get('ADMIN_PASSWORD', 'NOT SET')}")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT SET')}")
print("=============================")

class Config:
    """
    تكوين التطبيق الرئيسي - يتم استخدامه في جميع بيئات التشغيل
    
    يحتوي على إعدادات Flask، قاعدة البيانات، البريد الإلكتروني، رفع الملفات، إلخ.
    استخدم المتغيرات البيئية للقيم الحساسة مثل المفاتيح السرية وكلمات المرور.
    """
    # إعدادات Flask الأساسية
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # في بيئة التطوير فقط، استخدم مفتاح افتراضي
        if os.environ.get('FLASK_ENV') != 'production':
            SECRET_KEY = 'a-very-secure-secret-key-for-development'
        else:
            raise ValueError("SECRET_KEY environment variable must be set in production")
    
    # Database configuration
    # Use Render's DATABASE_URL in production, otherwise fall back to local MySQL for development
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        # On Render, DATABASE_URL is for PostgreSQL, but SQLAlchemy needs 'postgresql://'
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # لا تكشف بيانات اعتماد قاعدة البيانات في التعليقات البرمجية
    if not db_url and os.environ.get('FLASK_ENV') != 'production':
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/sultan_prints?charset=utf8mb4'
    else:
        SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    
    # إعدادات التطوير والأمان
    SETUP_SECRET_KEY = os.environ.get('SETUP_SECRET_KEY', 'development-setup-key')
    
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
    
    # Mailerlite Configuration
    MAILERLITE_API_KEY = os.environ.get('MAILERLITE_API_KEY')
    MAILERLITE_GROUP_ID = os.environ.get('MAILERLITE_GROUP_ID', 'default_group_id')
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net; connect-src 'self'"
    }
    
    # Setup Secret (للتطوير فقط)
    SETUP_SECRET_KEY = os.environ.get('SETUP_SECRET_KEY') or 'dev-setup-secret-key-change-me'