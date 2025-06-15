# wsgi.py
"""
نقطة دخول خادم الويب WSGI (مثل Gunicorn أو uWSGI)
يستخدم هذا الملف للنشر في بيئة الإنتاج

مثال التشغيل:
gunicorn wsgi:app -w 4 -b 0.0.0.0:5000
"""
import os
from app import create_app

# The 'app' object will be discovered by Gunicorn
app = create_app(os.getenv('FLASK_CONFIG') or 'config.Config') 
