# Sultan Prints - دليل البدء السريع

## 🚀 تشغيل المشروع محلياً

### المتطلبات الأساسية
- Python 3.9+
- MySQL (XAMPP)
- Git

### خطوات التثبيت

1. **استنساخ المشروع**
```bash
git clone <repository-url>
cd Sultan-Prints-openmanus
```

2. **إنشاء البيئة الافتراضية**
```bash
python3 -m venv venv
source venv/bin/activate  # على macOS/Linux
```

3. **تثبيت المتطلبات**
```bash
pip install -r requirements.txt
```

4. **إعداد قاعدة البيانات**
```bash
# تأكد من تشغيل XAMPP MySQL
mysql -u root -p
CREATE DATABASE sultan_prints CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit
```

5. **إعداد ملف البيئة**
```bash
cp .env-example .env
# قم بتعديل ملف .env حسب إعداداتك
```

6. **تشغيل الهجرات**
```bash
flask db upgrade
```

7. **تشغيل التطبيق**
```bash
# للتطوير
./run_development.sh

# أو مباشرة
source venv/bin/activate
FLASK_ENV=development flask run --host=0.0.0.0 --port=8000
```

## 📧 إعداد البريد الإلكتروني

المشروع يستخدم Mailerlite لإرسال رسائل البريد الإلكتروني:

1. **إعداد Gmail App Password**
   - اذهب إلى إعدادات Google Account
   - فعّل Two-Factor Authentication
   - أنشئ App Password للبريد الإلكتروني

2. **تحديث ملف .env**
```env
MAIL_USERNAME=ohnabeel@gmail.com
MAIL_PASSWORD=your-app-password-here
MAIL_DEFAULT_SENDER=ohnabeel@gmail.com
```

## 🔐 بيانات تسجيل دخول المدير

- **البريد الإلكتروني**: admin@tshirtshop.com
- **كلمة المرور**: superadmin123

## 🌐 الوصول للموقع

- **الموقع الرئيسي**: http://localhost:8000
- **لوحة التحكم**: http://localhost:8000/admin
- **المنتجات**: http://localhost:8000/products
- **التصميم المخصص**: http://localhost:8000/custom-design
- **التواصل**: http://localhost:8000/contact

## 🛠️ الميزات المتاحة

### للمستخدمين
- ✅ تصفح المنتجات
- ✅ التصميم المخصص
- ✅ سلة التسوق
- ✅ تتبع الطلبات
- ✅ نموذج التواصل
- ✅ صفحات ثابتة (من نحن، الخصوصية، إلخ)

### للمدير
- ✅ إدارة المنتجات
- ✅ إدارة الطلبات
- ✅ إدارة التصاميم المخصصة
- ✅ إدارة الصفحات
- ✅ إدارة الإعدادات
- ✅ نظام التنبيهات بالبريد الإلكتروني

## 📱 الميزات المتقدمة

- **نظام البريد الإلكتروني**: إشعارات تلقائية للطلبات
- **الأمان**: حماية CSRF، إدارة الجلسات الآمنة
- **التصميم المتجاوب**: يعمل على جميع الأجهزة
- **إدارة المخزون**: تتبع الكميات المتوفرة
- **نظام المحافظات**: إدارة مناطق التوصيل

## 🚀 النشر على DigitalOcean

المشروع جاهز للنشر على DigitalOcean App Platform:

1. **رفع الكود إلى GitHub**
2. **ربط المستودع مع DigitalOcean**
3. **إعداد متغيرات البيئة**
4. **تشغيل التطبيق**

## 📞 الدعم

إذا واجهت أي مشاكل:
1. تحقق من تشغيل XAMPP MySQL
2. تأكد من صحة إعدادات ملف .env
3. تحقق من سجلات الخطأ في Terminal

---

**تم تطوير هذا المشروع بواسطة فريق Sultan Prints** 🎨 