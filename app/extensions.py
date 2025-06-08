# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_mail import Mail

# Create extension instances
db = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail() 