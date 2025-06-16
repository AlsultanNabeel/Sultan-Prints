# wsgi.py
"""
نقطة دخول خادم الويب WSGI (مثل Gunicorn أو uWSGI)
يستخدم هذا الملف للنشر في بيئة الإنتاج

مثال التشغيل:
gunicorn wsgi:app -w 4 -b 0.0.0.0:5000
"""
import os
from app import create_app

# تحديد بيئة التشغيل
config_name = os.getenv('FLASK_ENV', 'production')
if config_name == 'development':
    config_name = 'development'
elif config_name == 'testing':
    config_name = 'testing'
else:
    config_name = 'production'

# إنشاء تطبيق Flask
app = create_app(config_name) 
