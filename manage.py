import os
from app import create_app
from app.extensions import db
from flask_migrate import Migrate, upgrade

app = create_app(os.getenv('FLASK_CONFIG') or 'app.config.Config')
migrate = Migrate(app, db)

# ✅ نضيف هذا الشرط لتطبيق التهجير عند التشغيل
if __name__ == '__main__':
    with app.app_context():
        print("🔄 Running automatic database upgrade...")
        upgrade()
        print("✅ Database upgrade completed.")
