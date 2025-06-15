#!/bin/bash
# remove_unnecessary_files.sh
# سكريبت لحذف كل ما ليس له لزوم في المشروع بشكل تلقائي

# تعيين مسار المشروع
PROJECT_DIR=$(pwd)
echo "🔍 بدء فحص وتنظيف المشروع في: $PROJECT_DIR"

# وظيفة لعرض النص بالألوان
print_color() {
    case $1 in
        "red") echo -e "\033[0;31m$2\033[0m" ;;
        "green") echo -e "\033[0;32m$2\033[0m" ;;
        "yellow") echo -e "\033[0;33m$2\033[0m" ;;
        "blue") echo -e "\033[0;34m$2\033[0m" ;;
    esac
}

# تم تعديل طريقة التأكيد لتكون تلقائية
perform_delete() {
    print_color "yellow" "🗑️ جاري حذف $1..."
    # يتم التنفيذ مباشرة
    eval "$2"
    if [ $? -eq 0 ]; then
        print_color "green" "✅ تم الحذف بنجاح"
    else
        print_color "red" "❌ حدث خطأ أثناء الحذف"
    fi
}

# 1. حذف ملفات __pycache__ وملفات .pyc
echo ""
print_color "blue" "🧹 تنظيف ملفات Python المؤقتة..."
pycache_count=$(find $PROJECT_DIR -name "__pycache__" | wc -l)
pyc_count=$(find $PROJECT_DIR -name "*.pyc" | wc -l)

if [ $pycache_count -gt 0 ] || [ $pyc_count -gt 0 ]; then
    print_color "yellow" "تم العثور على $pycache_count مجلد __pycache__ و $pyc_count ملف .pyc"
    perform_delete "ملفات __pycache__ و .pyc" "find $PROJECT_DIR -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; find $PROJECT_DIR -name '*.pyc' -type f -delete"
else
    print_color "green" "✅ لم يتم العثور على ملفات Python مؤقتة"
fi

# 2. حذف جميع ملفات السجلات
echo ""
print_color "blue" "🧹 حذف جميع ملفات السجلات..."
log_files=$(find $PROJECT_DIR -name "*.log")
log_count=$(echo "$log_files" | grep -v '^$' | wc -l)

if [ $log_count -gt 0 ]; then
    print_color "yellow" "تم العثور على $log_count ملف سجل:"
    echo "$log_files"
    perform_delete "ملفات السجلات" "find $PROJECT_DIR -name '*.log' -exec rm -f {} \;"
else
    print_color "green" "✅ لم يتم العثور على ملفات سجلات"
fi

# 3. التحقق من ملفات الترحيل (migrations) غير الضرورية
echo ""
print_color "blue" "🧹 فحص ملفات الترحيل..."
remove_migration_file="/Users/nabeelalsultan/OpenManus/Sultan-Prints-openmanus/migrations/versions/20240608_remove.py"

if [ -f "$remove_migration_file" ]; then
    print_color "yellow" "تم العثور على ملف ترحيل قد يكون غير ضروري:"
    echo "$remove_migration_file"
    perform_delete "ملف الترحيل غير الضروري" "rm -f $remove_migration_file"
else
    print_color "green" "✅ لم يتم العثور على ملفات ترحيل غير ضرورية"
fi

# 4. فحص وحذف جميع الملفات الفارغة
echo ""
print_color "blue" "🧹 حذف جميع الملفات الفارغة..."
empty_files=$(find $PROJECT_DIR -type f -not -path "*/\.*" -not -path "*/venv/*" -size 0)
empty_count=$(echo "$empty_files" | grep -v '^$' | wc -l)

if [ $empty_count -gt 0 ]; then
    print_color "yellow" "تم العثور على $empty_count ملف فارغ:"
    echo "$empty_files"
    perform_delete "جميع الملفات الفارغة" "find $PROJECT_DIR -type f -not -path '*/\.*' -not -path '*/venv/*' -size 0 -delete"
else
    print_color "green" "✅ لم يتم العثور على ملفات فارغة"
fi

# 5. تنظيف جميع الملفات المؤقتة في مجلد static
echo ""
print_color "blue" "🧹 تنظيف جميع الملفات المؤقتة في مجلد static..."
# حذف جميع الصور والملفات في static/uploads باستثناء المجلدات
if [ -d "$PROJECT_DIR/static/uploads" ]; then
    temp_count=$(find $PROJECT_DIR/static/uploads -type f | wc -l)
    if [ $temp_count -gt 0 ]; then
        print_color "yellow" "تم العثور على $temp_count ملف في مجلد التحميلات"
        perform_delete "جميع ملفات التحميل المؤقتة" "find $PROJECT_DIR/static/uploads -type f -delete"
    else
        print_color "green" "✅ لم يتم العثور على ملفات في مجلد التحميلات"
    fi
fi

# 6. حذف ملفات النسخ الاحتياطي والملفات المؤقتة
echo ""
print_color "blue" "🧹 حذف ملفات النسخ الاحتياطي والملفات المؤقتة..."
backup_files=$(find $PROJECT_DIR -name "*~" -o -name "*.bak" -o -name "*.tmp" -o -name "*.swp" -o -name "*.swo")
backup_count=$(echo "$backup_files" | grep -v '^$' | wc -l)

if [ $backup_count -gt 0 ]; then
    print_color "yellow" "تم العثور على $backup_count ملف نسخ احتياطي أو مؤقت:"
    echo "$backup_files"
    perform_delete "ملفات النسخ الاحتياطي والملفات المؤقتة" "find $PROJECT_DIR -name '*~' -o -name '*.bak' -o -name '*.tmp' -o -name '*.swp' -o -name '*.swo' -delete"
else
    print_color "green" "✅ لم يتم العثور على ملفات نسخ احتياطي أو ملفات مؤقتة"
fi

# 7. حذف مجلدات .git الفرعية (إذا وجدت)
echo ""
print_color "blue" "🧹 فحص مجلدات .git الفرعية..."
subgit_dirs=$(find $PROJECT_DIR -path "$PROJECT_DIR/.git" -prune -o -name ".git" -type d -print)
subgit_count=$(echo "$subgit_dirs" | grep -v '^$' | wc -l)

if [ $subgit_count -gt 0 ]; then
    print_color "yellow" "تم العثور على $subgit_count مجلد .git فرعي:"
    echo "$subgit_dirs"
    perform_delete "مجلدات .git الفرعية" "find $PROJECT_DIR -path '$PROJECT_DIR/.git' -prune -o -name '.git' -type d -exec rm -rf {} \;"
else
    print_color "green" "✅ لم يتم العثور على مجلدات .git فرعية"
fi

# 8. حذف سكريبت cleanup.sh إذا كان موجوداً (لأنه تم دمجه في هذا السكريبت)
echo ""
print_color "blue" "🧹 فحص سكريبت cleanup.sh..."
if [ -f "$PROJECT_DIR/cleanup.sh" ]; then
    print_color "yellow" "تم العثور على سكريبت cleanup.sh (تم دمجه في هذا السكريبت)"
    perform_delete "سكريبت cleanup.sh" "rm -f $PROJECT_DIR/cleanup.sh"
else
    print_color "green" "✅ لم يتم العثور على سكريبت cleanup.sh"
fi

# 9. حذف ملفات DS_Store (ملفات نظام macOS)
echo ""
print_color "blue" "🧹 حذف ملفات DS_Store..."
ds_files=$(find $PROJECT_DIR -name ".DS_Store")
ds_count=$(echo "$ds_files" | grep -v '^$' | wc -l)

if [ $ds_count -gt 0 ]; then
    print_color "yellow" "تم العثور على $ds_count ملف .DS_Store:"
    echo "$ds_files"
    perform_delete "ملفات .DS_Store" "find $PROJECT_DIR -name '.DS_Store' -delete"
else
    print_color "green" "✅ لم يتم العثور على ملفات .DS_Store"
fi

# 10. حذف ملف .blackboxrules (ملف فارغ غير مستخدم)
echo ""
print_color "blue" "🧹 فحص ملف .blackboxrules..."
if [ -f "$PROJECT_DIR/.blackboxrules" ] && [ ! -s "$PROJECT_DIR/.blackboxrules" ]; then
    print_color "yellow" "تم العثور على ملف .blackboxrules فارغ"
    perform_delete "ملف .blackboxrules" "rm -f $PROJECT_DIR/.blackboxrules"
else
    print_color "green" "✅ ملف .blackboxrules غير موجود أو غير فارغ"
fi

# 11. حذف مجلد .continue (مرتبط بأدوات تطوير GitHub Copilot)
echo ""
print_color "blue" "🧹 فحص مجلد .continue..."
if [ -d "$PROJECT_DIR/.continue" ]; then
    print_color "yellow" "تم العثور على مجلد .continue (مرتبط بأدوات GitHub Copilot)"
    perform_delete "مجلد .continue" "rm -rf $PROJECT_DIR/.continue"
else
    print_color "green" "✅ مجلد .continue غير موجود"
fi

# النهاية
echo ""
print_color "green" "🎉 تم الانتهاء من تنظيف المشروع بشكل كامل"
echo "تم حذف كل ما ليس له لزوم في المشروع"
