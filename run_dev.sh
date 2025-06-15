#!/bin/bash

# Sultan Prints Development Server Script
# سكريبت تشغيل خادم التطوير لمتجر سلطان برينتس

echo "🚀 بدء تشغيل متجر سلطان برينتس..."

# التحقق من وجود البيئة الافتراضية
if [ ! -d "venv" ]; then
    echo "❌ البيئة الافتراضية غير موجودة. يتم إنشاؤها..."
    python3 -m venv venv
fi

# تفعيل البيئة الافتراضية
echo "📦 تفعيل البيئة الافتراضية..."
source venv/bin/activate

# تثبيت المتطلبات
echo "📥 تثبيت المتطلبات..."
pip install -r requirements.txt

# التحقق من وجود ملف .env
if [ ! -f ".env" ]; then
    echo "⚠️ ملف .env غير موجود. يتم إنشاؤه..."
    cp .env-example .env
    echo "✅ تم إنشاء ملف .env. يرجى تعديله حسب إعداداتك."
fi

# إنشاء المجلدات المطلوبة
echo "📁 إنشاء المجلدات المطلوبة..."
mkdir -p static/uploads/custom static/uploads/designs static/uploads/products logs

# التحقق من قاعدة البيانات
echo "🗄️ التحقق من قاعدة البيانات..."
if command -v mysql >/dev/null 2>&1; then
    if mysql -u root -e "USE sultan_prints" 2>/dev/null; then
        echo "✅ قاعدة البيانات متاحة"
    else
        echo "⚠️ قاعدة البيانات غير موجودة. يرجى التأكد من تشغيل XAMPP وإنشاء قاعدة البيانات."
    fi
else
    echo "⚠️ MySQL غير متاح. يرجى التأكد من تشغيل XAMPP."
fi

# تشغيل الترحيلات
echo "🔄 تشغيل ترحيلات قاعدة البيانات..."
flask db upgrade

# تشغيل السيرفر
echo "🌐 تشغيل خادم التطوير..."
echo "📍 العنوان: http://localhost:8000"
echo "🔧 لوحة التحكم: http://localhost:8000/admin"
echo "📧 البريد: admin@tshirtshop.com"
echo "🔑 كلمة المرور: superadmin123"
echo ""
echo "اضغط Ctrl+C لإيقاف الخادم"

# تشغيل Flask على المنفذ 8000
FLASK_ENV=development flask run --host=0.0.0.0 --port=8000 