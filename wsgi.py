# wsgi.py
import os
from app import create_app
from flask_migrate import upgrade
from app.extensions import db

# The 'app' object will be discovered by Gunicorn
app = create_app(os.getenv('FLASK_CONFIG') or 'app.config.Config')

# Apply database migrations automatically
with app.app_context():
    try:
        upgrade()
        print("✅ Database upgraded successfully.")
    except Exception as e:
        print(f"❌ Failed to apply migrations: {e}")
