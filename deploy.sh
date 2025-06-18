#!/bin/bash

# Sultan Prints Deployment Script
# سكريبت النشر التلقائي لمتجر سلطان برينتس

set -e  # Exit on any error

echo "🚀 بدء عملية النشر لمتجر سلطان برينتس..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error "ملف .env غير موجود!"
    print_status "يرجى إنشاء ملف .env بناءً على .env.example"
    exit 1
fi

# Load environment variables
print_status "تحميل المتغيرات البيئية..."
source .env

# Check required environment variables
required_vars=("SECRET_KEY" "DATABASE_URL" "ADMIN_EMAIL" "ADMIN_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "المتغير البيئي $var غير محدد!"
        exit 1
    fi
done

print_success "جميع المتغيرات البيئية المطلوبة موجودة"

# Create necessary directories
print_status "إنشاء المجلدات المطلوبة..."
mkdir -p static/uploads/{custom,designs,products,receipts,site,settings}
mkdir -p logs
mkdir -p ssl

# Set proper permissions
print_status "تعيين الصلاحيات..."
chmod -R 755 static/uploads
chmod -R 755 logs

# Install/Update dependencies
print_status "تثبيت/تحديث المتطلبات..."
pip install --upgrade pip
pip install -r requirements.txt

# Database migration
print_status "تشغيل ترحيلات قاعدة البيانات..."
flask db upgrade

# Initialize database if needed
print_status "تهيئة قاعدة البيانات..."
flask seed 2>/dev/null || print_warning "تم تخطي تهيئة قاعدة البيانات (قد تكون موجودة بالفعل)"

# Build Docker image
print_status "بناء صورة Docker..."
docker build -t sultan-prints .

# Stop existing containers
print_status "إيقاف الحاويات الموجودة..."
docker-compose down 2>/dev/null || true

# Start services
print_status "تشغيل الخدمات..."
docker-compose up -d

# Wait for services to be ready
print_status "انتظار جاهزية الخدمات..."
sleep 30

# Health check
print_status "فحص صحة التطبيق..."
if curl -f http://localhost:8080/ > /dev/null 2>&1; then
    print_success "التطبيق يعمل بنجاح!"
else
    print_error "فشل في فحص صحة التطبيق"
    print_status "فحص السجلات..."
    docker-compose logs web
    exit 1
fi

# Final status
print_success "✅ تم النشر بنجاح!"
echo ""
echo "📍 روابط التطبيق:"
echo "   - الموقع الرئيسي: http://localhost:8080"
echo "   - لوحة التحكم: http://localhost:8080/admin"
echo ""
echo "🔧 معلومات إضافية:"
echo "   - سجلات التطبيق: docker-compose logs web"
echo "   - سجلات قاعدة البيانات: docker-compose logs db"
echo "   - إيقاف الخدمات: docker-compose down"
echo ""
print_success "🎉 تم إكمال عملية النشر!" 