# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Create extension instances
db = SQLAlchemy()
csrf = CSRFProtect()