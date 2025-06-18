import os
import logging
from app import create_app
from app.extensions import db
from flask_migrate import Migrate, upgrade

# إعداد تسجيل الأخطاء
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.FileHandler('app_error.log'),
        logging.StreamHandler()
    ]
)

try:
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    migrate = Migrate(app, db)
except Exception as e:
    logging.error(f"Error during app initialization: {str(e)}")
    raise

# ✅ نضيف هذا الشرط لتطبيق التهجير عند التشغيل
if __name__ == '__main__':
    # نعلق تطبيق التهجير مؤقتاً لحل مشكلة 20240608_remove
    # with app.app_context():
    #     print("🔄 Running automatic database upgrade...")
    #     upgrade()
    #     print("✅ Database upgrade completed.")
    app.run(debug=True, port=5001)
