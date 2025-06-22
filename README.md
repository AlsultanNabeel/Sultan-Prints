# Sultan Prints - متجر سلطان برينتس

متجر إلكتروني متكامل لبيع الملابس المطبوعة بتصاميم جاهزة ومخصصة، مبني بتقنية Flask.

## 🚀 المميزات

- **إدارة المنتجات**: إضافة وتعديل وحذف المنتجات مع الصور والألوان والمقاسات
- **التصاميم المخصصة**: نظام لرفع وتتبع التصاميم المخصصة للعملاء
- **نظام الطلبات**: إدارة كاملة للطلبات مع تتبع الحالة
- **أكواد الخصم**: نظام إدارة أكواد الخصم مع التحقق من الصلاحية
- **إدارة المحافظات**: إدارة رسوم التوصيل حسب المحافظة
- **نظام الدفع**: دعم الدفع عند الاستلام وفودافون كاش
- **لوحة تحكم شاملة**: إدارة كاملة للموقع من لوحة تحكم واحدة
- **نظام الإعلانات**: إعلانات متحركة في أعلى الموقع
- **الأسئلة الشائعة**: إدارة الأسئلة الشائعة
- **الصفحات الديناميكية**: إمكانية إنشاء وتعديل صفحات المحتوى

## 🛠️ التقنيات المستخدمة

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Email**: Flask-Mail
- **File Upload**: Pillow, boto3 (DigitalOcean Spaces)
- **Testing**: pytest, Playwright
- **Production**: Gunicorn

## 📋 المتطلبات

- Python 3.9+
- PostgreSQL
- pip

## 🔧 التثبيت والتشغيل

### 1. استنساخ المشروع
```bash
git clone <repository-url>
cd Sultan-Prints-openmanus
```

### 2. إنشاء البيئة الافتراضية
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. إعداد المتغيرات البيئية
أنشئ ملف `.env` في المجلد الرئيسي:
```env
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/sultan_prints

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-admin-password

# Email
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# DigitalOcean Spaces (اختياري)
SPACES_KEY=your-spaces-key
SPACES_SECRET=your-spaces-secret
SPACES_BUCKET_NAME=your-bucket-name
SPACES_REGION=fra1
```

### 5. إعداد قاعدة البيانات
```bash
flask db upgrade
```

### 6. تشغيل التطبيق
```bash
python manage.py
```

## 🐳 التشغيل باستخدام Docker

### 1. بناء الصورة
```bash
docker build -t sultan-prints .
```

### 2. تشغيل الحاوية
```bash
docker run -p 8080:8080 --env-file .env sultan-prints
```

## 📁 هيكل المشروع

```
Sultan-Prints-openmanus/
├── app/
│   ├── routes/          # مسارات التطبيق
│   ├── utils/           # أدوات مساعدة
│   ├── models.py        # نماذج قاعدة البيانات
│   ├── forms.py         # نماذج الإدخال
│   └── __init__.py      # تهيئة التطبيق
├── templates/           # قوالب HTML
├── static/              # الملفات الثابتة
├── migrations/          # ترحيلات قاعدة البيانات
├── scripts/             # سكريبتات مساعدة
├── logs/                # ملفات السجلات
├── config.py            # إعدادات التطبيق
├── manage.py            # تشغيل التطبيق
├── wsgi.py              # نقطة دخول الإنتاج
└── requirements.txt     # متطلبات Python
```

## 🔐 الأمان

- حماية CSRF في جميع النماذج
- تسجيل دخول آمن للأدمن
- رؤوس أمان مضافة تلقائياً
- تسجيل أحداث الأمان
- حماية من هجمات fixation للجلسات
- تحقق من صلاحية الملفات المرفوعة

## 📧 الإعدادات المطلوبة للنشر

### 1. متغيرات البيئة الإلزامية
- `SECRET_KEY`: مفتاح سري قوي
- `DATABASE_URL`: رابط قاعدة البيانات
- `ADMIN_EMAIL`: بريد الأدمن
- `ADMIN_PASSWORD`: كلمة مرور الأدمن

### 2. متغيرات البريد الإلكتروني
- `MAIL_USERNAME`: بريد المرسل
- `MAIL_PASSWORD`: كلمة مرور التطبيق
- `MAIL_DEFAULT_SENDER`: بريد المرسل الافتراضي

### 3. متغيرات التخزين السحابي (اختياري)
- `SPACES_KEY`: مفتاح DigitalOcean Spaces
- `SPACES_SECRET`: السر الخاص بـ Spaces
- `SPACES_BUCKET_NAME`: اسم البكت
- `SPACES_REGION`: المنطقة

## 🚀 النشر على الإنتاج

### باستخدام Gunicorn
```bash
gunicorn --bind 0.0.0.0:8080 --workers 4 wsgi:app
```

### باستخدام Docker
```bash
docker run -d -p 8080:8080 --env-file .env sultan-prints
```

## 📞 الدعم

للاستفسارات والدعم الفني، يرجى التواصل عبر:
- البريد الإلكتروني: support@sultanprints.com
- الهاتف: +20 123 456 789

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT.

---

**تم تطوير هذا المشروع بواسطة فريق سلطان برينتس** 🎨

## 🧪 الاختبارات

### اختبارات الوحدة
```bash
python -m pytest tests/
```

### اختبارات واجهة المستخدم (E2E) باستخدام Playwright
لتشغيل اختبارات واجهة المستخدم، قم بتنفيذ:

```bash
# تثبيت متصفحات Playwright
playwright install

# تشغيل الاختبارات
cd tests_e2e
pytest

# أو استخدام السكريبت التلقائي
./run_e2e_tests.sh
```

لمزيد من المعلومات حول اختبارات Playwright، راجع [ملف الإرشادات](/tests_e2e/README.md).