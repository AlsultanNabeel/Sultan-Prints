import logging
import os
from datetime import datetime, timedelta
from PIL import Image
import secrets
from werkzeug.utils import secure_filename
from flask import current_app

# إعداد اللوجينج
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, f'app_{datetime.now().strftime("%Y-%m-%d")}.log'),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_event(message, level='info'):
    if level == 'info':
        logging.info(message)
    elif level == 'warning':
        logging.warning(message)
    elif level == 'error':
        logging.error(message)
    else:
        logging.debug(message)

# تنظيف الملفات المؤقتة/غير المستخدمة
def cleanup_old_uploads(days=7):
    """يحذف الملفات الأقدم من عدد أيام محدد (افتراضي 7 أيام) من مجلد uploads/custom"""
    UPLOAD_FOLDER = os.path.join(current_app.root_path, '..', 'static/uploads/custom')
    now = datetime.now()
    deleted = 0
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_time > timedelta(days=days):
                os.remove(file_path)
                deleted += 1
    log_event(f"تم حذف {deleted} ملف مرفوع قديم من {UPLOAD_FOLDER}")
    return deleted

def save_image(file, folder='designs'):
    """حفظ صورة مرفوعة وإرجاع اسم الملف"""
    if not file:
        return None
    
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(file.filename)
    filename = random_hex + file_ext
    
    upload_path = os.path.join(current_app.root_path, '..', 'static/uploads', folder)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    
    file_path = os.path.join(upload_path, filename)
    
    # حفظ الصورة وتحجيمها إذا لزم الأمر
    i = Image.open(file)
    
    # إذا كانت الصورة كبيرة جدًا، قم بتحجيمها
    if max(i.size) > 1200:
        i.thumbnail((1200, 1200))
    
    i.save(file_path)
    
    # إرجاع المسار النسبي للصورة
    return os.path.join('uploads', folder, filename)

def allowed_file(filename):
    """التحقق من امتداد الملف مسموح به"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def inject_settings():
    """
    Injects site-wide settings into the context of all templates.
    """
    from app.models import Setting
    try:
        # Query all settings and convert them to a dictionary
        settings_list = Setting.query.all()
        settings_dict = {setting.key: setting.value for setting in settings_list}
        return dict(settings=settings_dict)
    except Exception as e:
        # In case the database is not ready yet (e.g., during migrations)
        log_event(f"Could not inject settings: {e}", level='warning')
        return dict(settings={}) 