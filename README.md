# Sultan Prints (متجر سلطان برينتس) 🎨

تطبيق ويب متكامل لمتجر ملابس مخصصة يقدم خدمات طباعة التصاميم المخصصة على الملابس.

## 🌟 المميزات الرئيسية

- 🛍️ **متجر إلكتروني متكامل** مع عرض المنتجات وتفاصيلها
- 🛒 **سلة تسوق ذكية** مع إدارة الكميات والألوان والمقاسات
- 💳 **نظام دفع متكامل** مع دعم Stripe وVodafone Cash
- 🎨 **تخصيص التصاميم** - رفع وتصميم تيشيرتات مخصصة
- 📦 **تتبع الطلبات** مع رموز تتبع فريدة
- 👨‍💼 **لوحة تحكم إدارية** شاملة لإدارة المنتجات والطلبات
- 📧 **نظام تواصل** مع العملاء عبر البريد الإلكتروني
- 💰 **نظام خصومات** وإدارة العروض الترويجية
- 📱 **تصميم متجاوب** يعمل على جميع الأجهزة
- 🔒 **أمان عالي** مع حماية CSRF وإدارة جلسات آمنة

## 🏗️ هيكل المشروع

```
sultan-prints/
├── app/                        # مجلد التطبيق الرئيسي
│   ├── __init__.py             # تهيئة التطبيق
│   ├── commands.py             # أوامر CLI مخصصة
│   ├── extensions.py           # إضافات Flask
│   ├── forms.py                # نماذج WTForms
│   ├── models.py               # نماذج قاعدة البيانات
│   ├── routes/                 # مسارات التطبيق
│   │   ├── admin.py            # مسارات لوحة التحكم
│   │   ├── cart.py             # مسارات سلة التسوق
│   │   └── main.py             # المسارات الرئيسية
│   ├── services/               # خدمات التطبيق
│   │   ├── mail.py             # خدمة البريد الإلكتروني
│   │   └── search.py           # خدمة البحث
│   └── utils/                  # أدوات مساعدة
│       ├── __init__.py         # وظائف عامة
│       └── email_utils.py      # وظائف البريد الإلكتروني
├── migrations/                 # ملفات ترحيل قاعدة البيانات
├── scripts/                    # نصوص مساعدة
├── static/                     # ملفات ثابتة
│   ├── css/                    # أنماط CSS
│   ├── images/                 # صور الموقع
│   ├── js/                     # ملفات JavaScript
│   └── uploads/                # ملفات مرفوعة من المستخدمين
├── templates/                  # قوالب HTML
│   ├── admin/                  # قوالب لوحة التحكم
│   ├── cart/                   # قوالب سلة التسوق
│   ├── emails/                 # قوالب البريد الإلكتروني
│   ├── errors/                 # صفحات الأخطاء
│   ├── main/                   # القوالب الرئيسية
│   └── partials/               # أجزاء قوالب مشتركة
├── config.py                   # إعدادات التطبيق
├── manage.py                   # سكريبت إدارة التطبيق
├── requirements.txt            # متطلبات Python
├── run_dev.sh                  # سكريبت تشغيل التطوير
└── wsgi.py                     # نقطة دخول WSGI للإنتاج
```

## 🚀 متطلبات النظام

- **Python 3.9+** أو أحدث
- **MySQL 5.7+** أو **PostgreSQL 12+**
- **XAMPP** (للتطوير المحلي)
- **Git** لإدارة الإصدارات

## ⚙️ إعداد بيئة التطوير

### 1. استنساخ المشروع
```bash
git clone https://github.com/yourusername/sultan-prints.git
cd sultan-prints
```

### 2. إنشاء البيئة الافتراضية
```bash
python3 -m venv venv
source venv/bin/activate  # لـ Linux/macOS
# أو
venv\Scripts\activate     # لـ Windows
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. إعداد قاعدة البيانات
```bash
# إنشاء قاعدة البيانات في MySQL
mysql -u root -e "CREATE DATABASE sultan_prints CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# تشغيل الترحيلات
flask db upgrade
```

### 5. إعداد ملف البيئة
```bash
cp .env-example .env
# تعديل ملف .env حسب إعداداتك
```

### 6. تشغيل التطبيق
```bash
# باستخدام السكريبت المخصص
chmod +x run_dev.sh
./run_dev.sh

# أو مباشرة
flask run --host=0.0.0.0 --port=8000
```

## 🌐 الوصول للتطبيق

- **الرئيسية**: `http://localhost:8000`
- **لوحة التحكم**: `http://localhost:8000/admin`
  - البريد: `admin@tshirtshop.com`
  - كلمة المرور: `superadmin123`

## 🚀 النشر على DigitalOcean App Platform

### 1. إعداد المتغيرات البيئية
```bash
# في لوحة تحكم DigitalOcean App Platform
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
ADMIN_EMAIL=admin@tshirtshop.com
ADMIN_PASSWORD=your-secure-password
```

### 2. إعداد قاعدة البيانات
- استخدم PostgreSQL في DigitalOcean
- قم بتشغيل الترحيلات تلقائياً

### 3. إعداد الملفات الثابتة
- تأكد من وجود مجلد `static/uploads/`
- إعطاء صلاحيات الكتابة المناسبة

## 🔧 الأوامر المفيدة

```bash
# تشغيل الترحيلات
flask db upgrade

# إنشاء ترحيل جديد
flask db migrate -m "وصف التغييرات"

# تهيئة البيانات الأساسية
flask seed

# تشغيل الاختبارات
python -m pytest

# تنظيف الملفات المؤقتة
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## 🛡️ الأمان

- ✅ حماية CSRF لجميع النماذج
- ✅ إدارة جلسات آمنة
- ✅ حماية من هجمات SQL Injection
- ✅ التحقق من صحة الملفات المرفوعة
- ✅ تشفير كلمات المرور
- ✅ رؤوس أمان HTTP

## 📊 إحصائيات المشروع

- **الملفات**: 50+ ملف Python
- **القوالب**: 30+ قالب HTML
- **المسارات**: 20+ مسار API
- **النماذج**: 10+ نموذج قاعدة بيانات

## 🤝 المساهمة

1. Fork المشروع
2. إنشاء فرع للميزة الجديدة (`git checkout -b feature/AmazingFeature`)
3. Commit التغييرات (`git commit -m 'Add some AmazingFeature'`)
4. Push للفرع (`git push origin feature/AmazingFeature`)
5. فتح Pull Request

## 📝 الترخيص

جميع الحقوق محفوظة © 2025 متجر سلطان برينتس.

## 📞 الدعم

- 📧 البريد الإلكتروني: support@sultanprints.com
- 🌐 الموقع: https://sultanprints.com
- 📱 الواتساب: +966501234567

---

**تم تطوير هذا المشروع بـ ❤️ باستخدام Flask و Python**
