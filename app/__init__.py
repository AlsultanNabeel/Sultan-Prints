import os
from flask import Flask, session, request, redirect
from config import Config
from .extensions import db, csrf
from flask_migrate import Migrate, upgrade
from flask_mail import Mail
from markupsafe import escape, Markup
from datetime import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config
from app.utils.security import setup_security_monitoring
import logging
from logging.handlers import RotatingFileHandler

migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

def nl2br(value):
    """Converts newlines in a string to HTML <br> tags."""
    if not isinstance(value, str):
        return value
    escaped_value = escape(value)
    return Markup(escaped_value.replace('\\n', '<br>\\n'))

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config[config_name])

    # إعدادات أمان إضافية للتطبيق
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
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # إعداد تسجيل الأخطاء
    if not app.debug and not app.testing:
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
    
    # تفعيل نظام المراقبة الأمنية
    setup_security_monitoring(app)

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
        # إعادة توجيه من sultanprints.studio إلى www.sultanprints.studio
        if request.host == 'sultanprints.studio':
            new_url = request.url.replace('sultanprints.studio', 'www.sultanprints.studio', 1)
            return redirect(new_url, code=301)
        
        # إجبار HTTPS في حالة دخل بدون SSL (إذا ما اشتغل من DigitalOcean)
        if not request.is_secure:
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)
        
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

    # تفعيل النسخ الاحتياطي التلقائي
    if app.config.get('ENABLE_AUTO_BACKUP', False):
        try:
            from scripts.backup import DatabaseBackup
            backup = DatabaseBackup()
            backup.schedule_backups()
            app.logger.info('تم تفعيل النسخ الاحتياطي التلقائي')
        except ImportError as e:
            app.logger.warning(f'لم يتم تفعيل النسخ الاحتياطي التلقائي: {str(e)}')

    return app