import os
from app import create_app
from app.extensions import db
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'app.config.Config')
migrate = Migrate(app, db) 