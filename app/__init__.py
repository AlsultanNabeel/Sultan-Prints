import os
import pymysql
from flask import Flask
from config import Config
from .extensions import db
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

pymysql.install_as_MySQLdb()

migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register CLI commands
    from . import commands
    commands.init_app(app)

    # Context Processors
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