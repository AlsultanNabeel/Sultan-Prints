import os
import secrets
import time
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify, abort
from app.models import Product, Design, Order, OrderStatus, Setting, Page, Announcement, FAQ, Governorate, CartItem, OrderItem, PromoCode
from app.forms import ProductForm, AdminLoginForm, OrderStatusForm, SettingsForm, PageForm, AnnouncementForm, FAQForm, GovernorateForm, PromoCodeForm
from app import db
from app.utils import save_image
from app.extensions import csrf
from datetime import datetime, timedelta
import json
from werkzeug.utils import secure_filename
from app.utils import allowed_file, log_event
import shutil

admin = Blueprint('admin', __name__)

# # بيانات الأدمن الثابتة - تم نقلها إلى config.py
# ADMIN_EMAIL = 'admin@tshirtshop.com'
# ADMIN_PASSWORD = 'superadmin123'

def admin_logged_in():
    """
    التحقق من حالة تسجيل دخول المدير
    
    يتحقق من القيمة في الجلسة ويتأكد من صحتها
    كما يفحص وقت انتهاء صلاحية الجلسة
    
    Returns:
        bool: True إذا كان المدير قد سجل دخوله وجلسته لا تزال صالحة
    """
    logged_in = session.get('admin_logged_in', False)
    
    # DEBUG: طباعة حالة الجلسة
    print("=== ADMIN_LOGGED_IN CHECK ===")
    print(f"Session data: {dict(session)}")
    print(f"admin_logged_in from session: {logged_in}")
    print(f"admin_logged_in key exists: {'admin_logged_in' in session}")
    print(f"admin_last_active exists: {'admin_last_active' in session}")
    print(f"Session keys: {list(session.keys())}")
    print("=============================")
    
    # التحقق من وقت آخر نشاط
    last_active = session.get('admin_last_active')
    if logged_in and last_active:
        try:
            # تحويل النص إلى كائن تاريخ إذا كان مخزناً كنص
            if isinstance(last_active, str):
                last_active = datetime.fromisoformat(last_active)
                
            # التحقق من المدة المنقضية (مثلاً ساعة واحدة)
            if datetime.utcnow() - last_active > timedelta(hours=1):
                # انتهت صلاحية الجلسة
                session.pop('admin_logged_in', None)
                print("Session expired - removing admin_logged_in")
                return False
                
            # تحديث وقت آخر نشاط
            session['admin_last_active'] = datetime.utcnow().isoformat()
        except (ValueError, TypeError):
            # حدث خطأ في معالجة الوقت، نعتبر أن المستخدم غير مسجل
            session.pop('admin_logged_in', None)
            print("Error processing time - removing admin_logged_in")
            return False
            
    return logged_in

def admin_login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"=== ADMIN_LOGIN_REQUIRED CHECK ===")
        print(f"Checking admin_logged_in for path: {request.path}")
        is_logged_in = admin_logged_in()
        print(f"admin_logged_in result: {is_logged_in}")
        print("==================================")
        
        if not is_logged_in:
            # تسجيل محاولة الوصول غير المصرح به
            log_event(f"Unauthorized admin access attempt to {request.path} from IP: {request.remote_addr}", level='warning')
            flash('يجب تسجيل الدخول للوصول إلى هذه الصفحة', 'danger')
            # حفظ صفحة الإحالة للعودة إليها بعد تسجيل الدخول
            session['next'] = request.full_path
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin', methods=['GET'])
@admin.route('/admin/', methods=['GET'])
def admin_index():
    if admin_logged_in():
        return redirect(url_for('admin.products'))
    return redirect(url_for('admin.login'))

@admin.route('/admin/home', methods=['GET'])
@admin_login_required
def admin_home():
    return redirect(url_for('admin.products'))

@admin.route('/admin/login', methods=['GET', 'POST'])
def login():
    print("=== LOGIN FUNCTION CALLED ===")
    print(f"Request method: {request.method}")
    print(f"Current session: {dict(session)}")
    print("==============================")
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print("=== DEBUG LOGIN ===")
        print(f"Email entered: {email}")
        print(f"Password entered: {password}")
        
        # الحصول على بيانات المشرف من متغيرات البيئة
        admin_email = current_app.config.get('ADMIN_EMAIL')
        admin_password = current_app.config.get('ADMIN_PASSWORD')
        
        print(f"Admin email from config: {admin_email}")
        print(f"Admin password from config: {admin_password}")
        
        if not admin_email or not admin_password:
            current_app.logger.error("Admin credentials not configured")
            flash('خطأ في إعدادات النظام', 'error')
            return render_template('admin/login.html'), 500
            
        if email and password and email.lower() == admin_email.lower() and password == admin_password:
            session['admin_logged_in'] = True
            session['admin_last_active'] = datetime.utcnow()
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('admin.admin_home'))
        else:
            flash('بيانات الدخول غير صحيحة', 'error')
            
    return render_template('admin/login.html')

@admin.route('/admin/logout')
def logout():
    if 'admin_logged_in' in session:
        log_event(f"Admin logout from IP: {request.remote_addr}", level='info')
        session.pop('admin_logged_in', None)
        
    # إجراءات أمان إضافية عند تسجيل الخروج
    session.clear()  # مسح كل بيانات الجلسة
    flash('تم تسجيل الخروج بنجاح', 'success')
    
    # لمنع هجمات إعادة التوجيه المفتوحة، نتأكد من إعادة التوجيه لعنوان داخلي فقط
    return redirect(url_for('admin.login'))

@admin.route('/admin/products')
@admin_login_required
def products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@admin.route('/admin/add_product', methods=['GET', 'POST'])
@admin_login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        # معالجة رفع الصورة
        image_filename = None
        if form.image.data:
            image_file = form.image.data
            if image_file and allowed_file(image_file.filename):
                image_filename = save_image(image_file, 'products')
                log_event(f"Product image uploaded: {image_filename} for new product by admin.", level='info')
            else:
                if image_file:
                    log_event(f"Product image upload failed (file not allowed): {image_file.filename} for new product by admin.", level='warning')
                
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            features=form.features.data,
            sizes=json.dumps(form.sizes.data),
            colors=','.join(form.colors.data),  # Store as comma-separated string
            material=form.material.data,
            featured=form.featured.data,
            in_stock=form.in_stock.data,  # حفظ حالة "متوفر في المخزون"
            category=form.category.data,
            is_palestine=form.is_palestine.data,
            image=image_filename  # حفظ اسم الصورة
        )
        log_event(f"New product created: {product.name} (ID: temp) by admin. Image: {image_filename}", level='info')
        db.session.add(product)
        db.session.commit()
        log_event(f"New product (ID: {product.id}) committed to DB by admin.", level='info')
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/add_product.html', form=form)

@admin.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        # معالجة رفع الصورة الجديدة
        if form.image.data:
            image_file = form.image.data
            if image_file and allowed_file(image_file.filename):
                image_filename = save_image(image_file, 'products')
                product.image = image_filename
                
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.features = form.features.data
        product.sizes = json.dumps(form.sizes.data)
        product.colors = ','.join(form.colors.data)  # Store as comma-separated string
        product.material = form.material.data
        product.featured = form.featured.data
        product.in_stock = form.in_stock.data  # تحديث حالة "متوفر في المخزون"
        product.category = form.category.data
        product.is_palestine = form.is_palestine.data
        db.session.commit()
        flash('تم تحديث المنتج بنجاح', 'success')
        return redirect(url_for('admin.products'))
    # فك الـ JSON في بايثون قبل تمريرها للقالب
    try:
        form.sizes.data = json.loads(product.sizes) if product.sizes else []
    except Exception:
        form.sizes.data = []
    try:
        form.colors.data = product.colors.split(',') if product.colors else []  # Split comma-separated string
    except Exception:
        form.colors.data = []
    return render_template('admin/edit_product.html', form=form, product=product, sizes=form.sizes.data, colors=form.colors.data)

@admin.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@admin_login_required
@csrf.exempt  # إعفاء هذا المسار من التحقق من CSRF
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    try:
        # حذف عناصر سلة التسوق المرتبطة بالمنتج أولاً
        cart_items = CartItem.query.filter_by(product_id=product_id).all()
        for cart_item in cart_items:
            db.session.delete(cart_item)
        
        # حذف عناصر الطلبات المرتبطة بالمنتج
        order_items = OrderItem.query.filter_by(product_id=product_id).all()
        for order_item in order_items:
            db.session.delete(order_item)
        
        # حذف السجلات من جدول order_product (many-to-many relationship)
        from app.models import order_product
        db.session.execute(
            order_product.delete().where(order_product.c.product_id == product_id)
        )
        
        # حذف ملف صورة المنتج إذا كان موجوداً
        if product.image:
            image_path = os.path.join(current_app.static_folder, product.image)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    current_app.logger.info(f"Deleted product image: {image_path}")
                except Exception as e:
                    current_app.logger.warning(f"Could not delete product image {image_path}: {e}")
        
        # حذف المنتج نفسه
        db.session.delete(product)
        db.session.commit()
        flash('تم حذف المنتج بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المنتج: {str(e)}', 'danger')
        current_app.logger.error(f"Error deleting product {product_id}: {e}")
    
    return redirect(url_for('admin.products'))

# إدارة التصاميم
@admin.route('/admin/designs')
@admin_login_required
def designs():
    designs = Design.query.filter_by(is_default=True).all()
    return render_template('admin/designs.html', designs=designs)

@admin.route('/admin/custom_designs/mark_printed/<path:filename>', methods=['POST'])
@admin_login_required
def mark_design_printed(filename):
    if '..' in filename or filename.startswith('/'):
        flash('اسم ملف غير صالح.', 'danger')
        return redirect(url_for('admin.custom_designs'))

    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'custom_requests')
    printed_folder = os.path.join(upload_folder, 'printed')
    os.makedirs(printed_folder, exist_ok=True)

    source_image_path = os.path.join(upload_folder, filename)
    base_filename, _ = os.path.splitext(filename)
    json_filename = f"{base_filename}.json"
    source_json_path = os.path.join(upload_folder, json_filename)

    dest_image_path = os.path.join(printed_folder, filename)
    dest_json_path = os.path.join(printed_folder, json_filename)

    try:
        if os.path.exists(source_image_path):
            shutil.move(source_image_path, dest_image_path)
        if os.path.exists(source_json_path):
            shutil.move(source_json_path, dest_json_path)
        flash(f'تم نقل التصميم "{filename}" إلى الأرشيف.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error moving design to printed folder: {e}")
        flash('حدث خطأ أثناء نقل التصميم.', 'danger')

    return redirect(url_for('admin.custom_designs'))

@admin.route('/admin/custom_designs')
@admin_login_required
def custom_designs():
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'custom_requests')
    printed_folder = os.path.join(upload_folder, 'printed')
    
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(printed_folder, exist_ok=True)

    def _get_designs_from_path(folder_path, subfolder=''):
        designs = []
        try:
            image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
            for image_file in image_files:
                base_filename, _ = os.path.splitext(image_file)
                json_filename = f"{base_filename}.json"
                json_filepath = os.path.join(folder_path, json_filename)
                
                metadata = {}
                if os.path.exists(json_filepath):
                    try:
                        with open(json_filepath, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except (json.JSONDecodeError, OSError):
                        pass
                
                designs.append({
                    'image_file': image_file,
                    'url_path': os.path.join('uploads/custom_requests', subfolder, image_file).replace('\\', '/'),
                    'metadata': metadata,
                    'mtime': os.path.getmtime(os.path.join(folder_path, image_file))
                })

            designs.sort(key=lambda x: x['mtime'], reverse=True)
        except OSError as e:
            flash(f'لا يمكن الوصول إلى المجلد {folder_path}: {e}', 'danger')
        return designs

    new_designs = _get_designs_from_path(upload_folder)
    printed_designs = _get_designs_from_path(printed_folder, subfolder='printed')

    return render_template('admin/custom_designs.html', new_designs=new_designs, printed_designs=printed_designs)

# إدارة الطلبات
@admin.route('/admin/orders')
@admin_login_required
def orders():
    # Get filter parameters
    status_filter = request.args.get('status')
    payment_method_filter = request.args.get('payment_method')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    show_archived = request.args.get('show_archived', 'false').lower() == 'true'
    
    # Build query
    query = Order.query
    
    if not show_archived:
        query = query.filter(Order.archived == False)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    if payment_method_filter:
        query = query.filter(Order.payment_method == payment_method_filter)
    
    if date_from:
        query = query.filter(Order.created_at >= date_from)
    
    if date_to:
        query = query.filter(Order.created_at <= date_to + ' 23:59:59')
    
    # Order by creation date (newest first)
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, show_archived=show_archived)

@admin.route('/admin/orders/archive/<int:order_id>', methods=['POST'])
@admin_login_required
def archive_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.archived = True
    db.session.commit()
    flash('تم أرشفة الطلب بنجاح', 'success')
    return redirect(url_for('admin.orders'))

@admin.route('/admin/orders/unarchive/<int:order_id>', methods=['POST'])
@admin_login_required
def unarchive_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.archived = False
    db.session.commit()
    flash('تم إلغاء أرشفة الطلب بنجاح', 'success')
    return redirect(url_for('admin.orders'))

@admin.route('/admin/order/<int:order_id>', methods=['GET', 'POST'])
@admin_login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    form = OrderStatusForm()

    if form.validate_on_submit():
        new_status = OrderStatus(
            order_id=order.id,
            status=form.status.data,
            notes=form.notes.data
        )
        # Also update the master status on the order itself
        order.status = form.status.data
        db.session.add(new_status)
        db.session.commit()
        flash('تم تحديث حالة الطلب بنجاح.', 'success')
        return redirect(url_for('admin.order_detail', order_id=order.id))

    status_history = order.status_history.all()
    return render_template('admin/order_detail.html', order=order, form=form, status_history=status_history)

@admin.route('/admin/settings', methods=['GET', 'POST'])
@admin_login_required
def admin_settings():
    form = SettingsForm()
    if form.validate_on_submit():
        # Handle file upload for hero image
        if form.hero_image.data:
            try:
                filename = save_image(form.hero_image.data, 'settings')
                setting = Setting.query.filter_by(key='hero_image').first()
                if setting:
                    setting.value = filename
                else:
                    db.session.add(Setting(key='hero_image', value=filename))
            except Exception as e:
                flash(f'حدث خطأ أثناء تحميل الصورة: {e}', 'danger')

        # Loop through form fields and update settings
        for field in form:
            if field.type != 'FileField' and field.type != 'CSRFTokenField' and field.type != 'SubmitField':
                setting = Setting.query.filter_by(key=field.name).first()
                if setting:
                    setting.value = field.data
                else:
                    db.session.add(Setting(key=field.name, value=field.data))
        
        try:
            db.session.commit()
            flash('تم حفظ الإعدادات بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء حفظ الإعدادات: {e}', 'danger')
            
        return redirect(url_for('admin.admin_settings'))

    # Populate form with existing settings
    settings = Setting.query.all()
    settings_dict = {setting.key: setting.value for setting in settings}
    form.process(data=settings_dict)
    
    hero_image_url = url_for('static', filename=f"uploads/settings/{settings_dict.get('hero_image')}") if settings_dict.get('hero_image') else None

    return render_template('admin/settings.html', form=form, hero_image_url=hero_image_url)


# ===== Manageable Pages =====
@admin.route('/admin/pages')
@admin_login_required
def pages():
    pages = Page.query.all()
    return render_template('admin/pages.html', pages=pages)

@admin.route('/admin/pages/add', methods=['GET', 'POST'])
@admin_login_required
def add_page():
    form = PageForm()
    if form.validate_on_submit():
        new_page = Page(
            title=form.title.data,
            slug=form.slug.data,
            content=form.content.data,
            meta_title=form.meta_title.data,
            meta_description=form.meta_description.data,
            is_published=form.is_published.data
        )
        db.session.add(new_page)
        db.session.commit()
        flash('تم إنشاء الصفحة الجديدة بنجاح!', 'success')
        return redirect(url_for('admin.pages'))
    return render_template('admin/edit_page.html', form=form, title='إضافة صفحة جديدة')

@admin.route('/admin/pages/edit/<int:page_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_page(page_id):
    page = Page.query.get_or_404(page_id)
    form = PageForm(obj=page)
    if form.validate_on_submit():
        page.title = form.title.data
        page.content = form.content.data
        page.meta_title = form.meta_title.data
        page.meta_description = form.meta_description.data
        page.is_published = form.is_published.data
        db.session.commit()
        flash('تم تحديث الصفحة بنجاح!', 'success')
        return redirect(url_for('admin.pages'))
    return render_template('admin/edit_page.html', form=form, page=page, title='تعديل صفحة')

@admin.route('/admin/pages/delete/<int:page_id>', methods=['POST'])
@admin_login_required
def delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    flash('تم حذف الصفحة بنجاح', 'success')
    return redirect(url_for('admin.pages'))

# Announcement Management
@admin.route('/admin/announcements')
@admin_login_required
def announcements():
    all_announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=all_announcements)

@admin.route('/admin/announcements/add', methods=['GET', 'POST'])
@admin_login_required
def add_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        new_announcement = Announcement(
            text=form.text.data,
            is_active=form.is_active.data
        )
        db.session.add(new_announcement)
        db.session.commit()
        flash('تم إضافة الإعلان بنجاح.', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/edit_announcement.html', form=form, title='إضافة إعلان جديد')

@admin.route('/admin/announcements/edit/<int:ann_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_announcement(ann_id):
    announcement = Announcement.query.get_or_404(ann_id)
    form = AnnouncementForm(obj=announcement)
    if form.validate_on_submit():
        announcement.text = form.text.data
        announcement.is_active = form.is_active.data
        db.session.commit()
        flash('تم تحديث الإعلان بنجاح.', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/edit_announcement.html', form=form, title='تعديل الإعلان')

@admin.route('/admin/announcements/delete/<int:ann_id>', methods=['POST'])
@admin_login_required
def delete_announcement(ann_id):
    announcement = Announcement.query.get_or_404(ann_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('تم حذف الإعلان بنجاح.', 'success')
    return redirect(url_for('admin.announcements'))

# FAQ Management
@admin.route('/admin/faqs')
@admin_login_required
def faqs():
    all_faqs = FAQ.query.order_by(FAQ.display_order.asc(), FAQ.id.asc()).all()
    return render_template('admin/faqs.html', faqs=all_faqs)

@admin.route('/admin/faqs/add', methods=['GET', 'POST'])
@admin_login_required
def add_faq():
    form = FAQForm()
    if form.validate_on_submit():
        new_faq = FAQ(
            question=form.question.data,
            answer=form.answer.data,
            is_active=form.is_active.data,
            display_order=form.display_order.data
        )
        db.session.add(new_faq)
        db.session.commit()
        flash('تمت إضافة السؤال بنجاح.', 'success')
        return redirect(url_for('admin.faqs'))
    return render_template('admin/faq_form.html', form=form)

@admin.route('/admin/faqs/edit/<int:faq_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    form = FAQForm(obj=faq)
    if form.validate_on_submit():
        faq.question = form.question.data
        faq.answer = form.answer.data
        faq.is_active = form.is_active.data
        faq.display_order = form.display_order.data
        db.session.commit()
        flash('تم تحديث السؤال بنجاح.', 'success')
        return redirect(url_for('admin.faqs'))
    return render_template('admin/faq_form.html', form=form)

@admin.route('/admin/faqs/delete/<int:faq_id>', methods=['POST'])
@admin_login_required
@csrf.exempt  # إعفاء هذا المسار من التحقق من CSRF
def delete_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    flash('تم حذف السؤال بنجاح.', 'success')
    return redirect(url_for('admin.faqs'))

# Governorate Management
@admin.route('/admin/governorates')
@admin_login_required
def governorates():
    all_governorates = Governorate.query.order_by(Governorate.name.asc()).all()
    form = GovernorateForm()
    return render_template('admin/governorates.html', governorates=all_governorates, form=form)

@admin.route('/admin/governorates/add', methods=['POST'])
@admin_login_required
def add_governorate():
    form = GovernorateForm()
    if form.validate_on_submit():
        try:
            new_governorate = Governorate(
                name=form.name.data,
                delivery_fee=form.delivery_fee.data
            )
            db.session.add(new_governorate)
            db.session.commit()
            flash('تمت إضافة المحافظة بنجاح.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء إضافة المحافظة: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                # Ensure getattr(form, field).label is accessed safely
                label_text = getattr(getattr(form, field), 'label', None)
                field_name = label_text.text if label_text else field
                flash(f"خطأ في حقل {field_name}: {error}", "danger")
    return redirect(url_for('admin.governorates'))

@admin.route('/admin/governorates/edit/<int:gov_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_governorate(gov_id):
    governorate = Governorate.query.get_or_404(gov_id)
    form = GovernorateForm(obj=governorate)
    if form.validate_on_submit():
        try:
            governorate.name = form.name.data
            governorate.delivery_fee = form.delivery_fee.data
            db.session.commit()
            flash('تم تحديث المحافظة بنجاح.', 'success')
            return redirect(url_for('admin.governorates'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تحديث المحافظة: {str(e)}', 'danger')
    return render_template('admin/edit_governorate.html', form=form, governorate=governorate)

@admin.route('/admin/governorates/delete/<int:gov_id>', methods=['POST'])
@admin_login_required
@csrf.exempt  # إعفاء هذا المسار من التحقق من CSRF
def delete_governorate(gov_id):
    governorate = Governorate.query.get_or_404(gov_id)
    try:
        db.session.delete(governorate)
        db.session.commit()
        flash('تم حذف المحافظة بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المحافظة: {str(e)}. قد تكون هناك طلبات مرتبطة بهذه المحافظة.', 'danger')
    return redirect(url_for('admin.governorates'))

@admin.route('/promocodes')
@admin_login_required
def promocodes():
    """صفحة إدارة أكواد الخصم"""
    promocodes = PromoCode.query.order_by(PromoCode.created_at.desc()).all()
    return render_template('admin/promocodes.html', promocodes=promocodes)

@admin.route('/promocodes/add', methods=['GET', 'POST'])
@admin_login_required
def add_promocode():
    """إضافة كود خصم جديد"""
    form = PromoCodeForm()
    if form.validate_on_submit():
        promo_code = PromoCode(
            code=form.code.data.upper(),
            discount_percentage=form.discount_percentage.data,
            max_uses=form.max_uses.data,
            expiration_date=form.expiration_date.data,
            is_active=form.is_active.data,
            created_by_id=current_user.id
        )
        db.session.add(promo_code)
        db.session.commit()
        flash('تم إضافة كود الخصم بنجاح', 'success')
        return redirect(url_for('admin.promocodes'))
    return render_template('admin/promocode_form.html', form=form, title='إضافة كود خصم')

@admin.route('/promocodes/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_promocode(id):
    """تعديل كود خصم"""
    promo_code = PromoCode.query.get_or_404(id)
    form = PromoCodeForm(obj=promo_code)
    form._id = id  # للتحقق من عدم تكرار الكود عند التعديل
    
    if form.validate_on_submit():
        promo_code.code = form.code.data.upper()
        promo_code.discount_percentage = form.discount_percentage.data
        promo_code.max_uses = form.max_uses.data
        promo_code.expiration_date = form.expiration_date.data
        promo_code.is_active = form.is_active.data
        
        db.session.commit()
        flash('تم تحديث كود الخصم بنجاح', 'success')
        return redirect(url_for('admin.promocodes'))
    
    return render_template('admin/promocode_form.html', form=form, title='تعديل كود خصم')

@admin.route('/promocodes/delete/<int:id>', methods=['POST'])
@admin_login_required
def delete_promocode(id):
    """حذف كود خصم"""
    promo_code = PromoCode.query.get_or_404(id)
    if promo_code.orders.count() > 0:
        flash('لا يمكن حذف كود الخصم لأنه مستخدم في طلبات', 'error')
    else:
        db.session.delete(promo_code)
        db.session.commit()
        flash('تم حذف كود الخصم بنجاح', 'success')
    return redirect(url_for('admin.promocodes'))

@admin.route('/promocodes/toggle/<int:id>', methods=['POST'])
@admin_login_required
def toggle_promocode(id):
    """تفعيل/تعطيل كود خصم"""
    promo_code = PromoCode.query.get_or_404(id)
    promo_code.is_active = not promo_code.is_active
    db.session.commit()
    status = 'تفعيل' if promo_code.is_active else 'تعطيل'
    flash(f'تم {status} كود الخصم بنجاح', 'success')
    return redirect(url_for('admin.promocodes'))