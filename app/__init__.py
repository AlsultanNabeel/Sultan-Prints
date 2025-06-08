import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, jsonify
from .extensions import db, csrf, mail
from flask_wtf.csrf import CSRFError
import os
from datetime import datetime
import logging
from flask_migrate import Migrate
from flask_cors import CORS
from . import commands
# from .logging_config import setup_logging
# from app.api_docs import swagger_ui_blueprint, api_docs

migrate = Migrate()

def create_app(config_class='app.config.Config'):
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config_class)
    
    # Initialize Flask extensions
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    commands.init_app(app)

    # إعداد اللوجينج
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler(f'logs/app_{datetime.now().strftime("%Y-%m-%d")}.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('تم بدء تشغيل التطبيق')
    
    # تسجيل معالج لأخطاء CSRF
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/csrf_error.html', reason=e.description), 400

    # تمرير السنة الحالية لكل القوالب
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    # Inject site-wide settings into all templates
    from app.utils import inject_settings
    app.context_processor(inject_settings)

    # تسجيل البلوبرنتس
    with app.app_context():
        from app.routes.main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from app.routes.admin import admin as admin_blueprint
        app.register_blueprint(admin_blueprint)

        from app.routes.cart import cart_bp as cart_blueprint
        app.register_blueprint(cart_blueprint)
    
    # from app.api_docs import swagger_ui_blueprint, api_docs
    # # Register Swagger UI blueprint
    # app.register_blueprint(swagger_ui_blueprint)

    # # Route to serve the Swagger JSON spec
    # @app.route('/static/swagger.json')
    # def swagger_spec():
    #     return jsonify(api_docs)

    # تسجيل معالجات الأخطاء
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
        
    return app