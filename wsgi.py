# wsgi.py
import os
from app import create_app

# The 'app' object will be discovered by Gunicorn
app = create_app(os.getenv('FLASK_CONFIG') or 'app.config.Config') 