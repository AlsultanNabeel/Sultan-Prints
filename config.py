import os
from datetime import timedelta
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# DEBUG: طباعة المتغيرات البيئية (فقط في بيئة التطوير)
if os.environ.get('FLASK_ENV', 'development') == 'development':
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
    # إعدادات أساسية
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # إعدادات البريد الإلكتروني (MailerSend فقط)
    MAILERSEND_API_KEY = os.environ.get('MAILERSEND_API_KEY')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    
    # إعدادات المشرف
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # إعدادات DigitalOcean Spaces
    SPACES_KEY = os.environ.get('SPACES_KEY')
    SPACES_SECRET = os.environ.get('SPACES_SECRET')
    SPACES_BUCKET_NAME = os.environ.get('SPACES_BUCKET_NAME')
    SPACES_REGION = os.environ.get('SPACES_REGION', 'fra1')
    SPACES_CDN_DOMAIN = os.environ.get('SPACES_CDN_DOMAIN')  # اختياري - إذا كنت تستخدم CDN
    
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/sultan_prints'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # إعدادات الأمان
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = os.environ.get('REMEMBER_COOKIE_HTTPONLY', 'True').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600)))
    
    # رؤوس الأمان
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https:; script-src 'self' 'unsafe-inline' https:; font-src 'self' https:;"
    }
    
    # إعدادات التطبيق
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif').split(','))
    
    # إعدادات النسخ الاحتياطي
    ENABLE_AUTO_BACKUP = os.environ.get('ENABLE_AUTO_BACKUP', 'False').lower() == 'true'
    BACKUP_BUCKET = os.environ.get('BACKUP_BUCKET')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 7))
    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', '0 3 * * *')  # يومياً في الساعة 3 صباحاً
    
    # إعدادات Stripe (إذا كنت تستخدمه)
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    @staticmethod
    def init_app(app):
        """تهيئة إضافية للتطبيق"""
        # إنشاء المجلدات المطلوبة
        for folder in ['static/uploads/custom', 'static/uploads/designs', 'static/uploads/products', 'logs']:
            os.makedirs(folder, exist_ok=True)
        
        # إعداد تسجيل الأخطاء
        if not app.debug:
            import logging
            from logging.handlers import RotatingFileHandler
            
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler('logs/sultan_prints.log',
                                             maxBytes=10240,
                                             backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Sultan Prints startup')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/sultanprints_local'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/sultan_prints_test'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # إعدادات إضافية للإنتاج
        # تم حذف إعدادات SMTPHandler لأننا نستخدم MailerSend API فقط

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}