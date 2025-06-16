#!/bin/bash
# Sultan Prints Production Server Script
# سكريبت تشغيل خادم الإنتاج لمتجر سلطان برينتس

echo "🚀 بدء تشغيل متجر سلطان برينتس في بيئة الإنتاج..."

# تعيين بيئة التشغيل
export FLASK_ENV=production
export FLASK_APP=wsgi.py

# التحقق من المتغيرات البيئية المطلوبة
if [ -z "$DATABASE_URL" ]; then
    echo "❌ خطأ: متغير DATABASE_URL غير محدد"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "❌ خطأ: متغير SECRET_KEY غير محدد"
    exit 1
fi

# إنشاء المجلدات المطلوبة
echo "📁 إنشاء المجلدات المطلوبة..."
mkdir -p static/uploads/custom static/uploads/designs static/uploads/products logs

# تشغيل الترحيلات
echo "🔄 تشغيل ترحيلات قاعدة البيانات..."
flask db upgrade

# تهيئة البيانات الأساسية إذا لم تكن موجودة
echo "🌱 تهيئة البيانات الأساسية..."
flask seed

# تشغيل الخادم
echo "🌐 تشغيل خادم الإنتاج..."
echo "📍 العنوان: http://0.0.0.0:8080"
echo "🔧 لوحة التحكم: http://0.0.0.0:8080/admin"

# تشغيل Gunicorn مع إعدادات الإنتاج
exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    wsgi:app
