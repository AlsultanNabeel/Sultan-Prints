import os
import pymysql
from flask import Flask, session
from config import Config
from .extensions import db, csrf
from flask_migrate import Migrate, upgrade
from flask_mail import Mail
from markupsafe import escape, Markup
from datetime import datetime
import uuid

pymysql.install_as_MySQLdb()

migrate = Migrate()
mail = Mail()

def nl2br(value):
    """Converts newlines in a string to HTML <br> tags."""
    if not isinstance(value, str):
        return value
    escaped_value = escape(value)
    return Markup(escaped_value.replace('\\n', '<br>\\n'))

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config_class)

    # إعدادات أمان إضافية للتطبيق
    # محتوى الأمان
    @app.after_request
    def add_security_headers(response):
        # إضافة رؤوس الأمان التي تم تكوينها
        headers = app.config.get('SECURITY_HEADERS', {})
        for header, value in headers.items():
            response.headers[header] = value
        
        # منع تخزين مؤقت للصفحات المصادقة
        if 'admin_logged_in' in session:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '-1'
        
        return response

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # --- BEGIN MODIFICATION ---
    # محاولة تطبيق تحديثات قاعدة البيانات عند بدء التشغيل
    # هذا مهم للمنصات مثل DigitalOcean App Platform
    # حيث قد لا يتم تشغيل 'flask db upgrade' بشكل منفصل.
    # نعلق هذا الجزء مؤقتاً لحل مشكلة 20240608_remove
    # with app.app_context():
    #     print("INFO: Attempting to apply database migrations...")
    #     try:
    #         upgrade() # هذا هو أمر flask_migrate.upgrade
    #         print("INFO: Database migrations check/apply completed.")
    #     except Exception as e:
    #         # تسجيل الخطأ، ولكن السماح للتطبيق بالاستمرار في البدء.
    #         # قد تمنع أخطاء الترحيل الحرجة التطبيق من العمل بشكل صحيح.
    #         print(f"WARNING: Error applying database migrations: {e}")
    #         print("WARNING: The application will continue starting, but some features might not work if migrations failed.")
    # --- END MODIFICATION ---

    csrf.init_app(app)
    mail.init_app(app)

    # Register custom Jinja filter
    app.jinja_env.filters['nl2br'] = nl2br

    # Register CLI commands
    from . import commands
    commands.init_app(app)

    # Context Processors
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}
    
    # مُعالج طلب قبل بداية الطلبات
    @app.before_request
    def before_request():
        # توليد معرّف جلسة جديد عند عدم وجوده
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
            
        # تجديد معرّف الجلسة لمنع هجمات fixation
        if not session.get('_fresh', False):
            # استبدال session.regenerate() لأنها غير موجودة في الإصدار الحالي من Flask
            # نقوم بوضع علامة على الجلسة بأنها تم تعديلها
            session.modified = True
            # نضع علامة جديدة للتحقق من حداثة الجلسة
            session['_fresh'] = True
            
        # إضافة تاريخ آخر نشاط للجلسة
        session['last_active'] = datetime.utcnow()
        
    from .utils import inject_settings, inject_cart_item_count
    app.context_processor(inject_settings)
    app.context_processor(inject_cart_item_count)

    # Blueprints
    from .routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .routes.cart import cart_bp as cart_blueprint
    app.register_blueprint(cart_blueprint)

    return app