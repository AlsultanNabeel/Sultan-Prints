from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from app.models import Product, Design, Order, OrderStatus, Setting, Page, Announcement, FAQ, Governorate
from app.forms import ProductForm, AdminLoginForm, OrderStatusForm, SettingsForm, PageForm, AnnouncementForm, FAQForm, DiscountForm, GovernorateForm
from app import db
from app.services.discounts import Discount
from app.utils import save_image
import os
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
    return session.get('admin_logged_in', False)

def admin_login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not admin_logged_in():
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin/login', methods=['GET', 'POST'])
def login():
    if admin_logged_in():
        return redirect(url_for('admin.products'))
    form = AdminLoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        #  استخدام القيم من الإعدادات
        admin_email_from_config = current_app.config.get('ADMIN_EMAIL')
        admin_password_from_config = current_app.config.get('ADMIN_PASSWORD')

        # Validate configuration values
        if not admin_email_from_config or not isinstance(admin_email_from_config, str) or \
           not admin_password_from_config or not isinstance(admin_password_from_config, str):
            
            log_event(
                "Admin login configuration error: ADMIN_EMAIL or ADMIN_PASSWORD is missing, not a string, or empty in config.", 
                level='error'
            )
            flash('خطأ في إعدادات النظام. يرجى التواصل مع مسؤول الموقع.', 'danger') 
            return render_template('admin/login.html', form=form)

        # Perform comparison (case-insensitive email, case-sensitive password)
        if email.lower() == admin_email_from_config.lower() and password == admin_password_from_config:
            session['admin_logged_in'] = True
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('admin.products'))
        else:
            flash('بيانات الدخول غير صحيحة', 'danger')
    return render_template('admin/login.html', form=form)

@admin.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('تم تسجيل الخروج بنجاح', 'success')
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
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('تم حذف المنتج بنجاح', 'success')
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
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

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

@admin.route('/admin/discounts')
@admin_login_required
def discounts():
    form = DiscountForm()
    now = datetime.utcnow()
    
    active_discounts = Discount.query.filter(
        Discount.is_active == True,
        Discount.end_date >= now
    ).order_by(Discount.end_date.asc()).all()
    
    inactive_discounts = Discount.query.filter(
        (Discount.is_active == False) | (Discount.end_date < now)
    ).order_by(Discount.end_date.desc()).all()

    return render_template(
        'admin/discounts.html', 
        active_discounts=active_discounts, 
        inactive_discounts=inactive_discounts,
        form=form
    )

@admin.route('/admin/discounts/add', methods=['POST'])
@admin_login_required
def add_discount_api():
    form = DiscountForm(request.form)
    if form.validate():
        try:
            # تحويل تاريخ البدء إلى كائن datetime (بداية اليوم)
            parsed_start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d')
            
            # تحويل تاريخ الانتهاء إلى كائن datetime (نهاية اليوم المحدد)
            parsed_end_date_day_start = datetime.strptime(form.end_date.data, '%Y-%m-%d')
            parsed_end_date = parsed_end_date_day_start + timedelta(days=1) - timedelta(microseconds=1)

            new_discount = Discount(
                code=form.code.data.upper(),
                type=form.type.data,
                value=form.value.data,
                min_purchase=form.min_purchase.data if form.min_purchase.data is not None else None,
                max_discount=form.max_discount.data if form.max_discount.data is not None else None,
                usage_limit=form.usage_limit.data if form.usage_limit.data is not None else None,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                is_active=form.is_active.data # استخدام القيمة من الفورم
            )
            db.session.add(new_discount)
            db.session.commit()
            # إرجاع رسالة نجاح مع بيانات الكوبون المضاف إذا أردت عرضها في الواجهة
            return jsonify({
                'success': True, 
                'message': 'تم إضافة الكوبون بنجاح',
                'discount': {
                    'id': new_discount.id,
                    'code': new_discount.code,
                    'type': new_discount.type,
                    'value': new_discount.value,
                    'start_date': new_discount.start_date.strftime('%Y-%m-%d'),
                    'end_date': new_discount.end_date.strftime('%Y-%m-%d %H:%M:%S'), # عرض الوقت للتأكيد
                    'is_active': new_discount.is_active
                }
            }), 200
        except ValueError as ve: # لالتقاط أخطاء تنسيق التاريخ
            db.session.rollback()
            current_app.logger.error(f"Error adding discount due to date format: {ve}")
            return jsonify({'success': False, 'message': f'خطأ في تنسيق التاريخ: {ve}. يرجى استخدام YYYY-MM-DD.'}), 400
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding discount: {e}")
            return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500
    else:
        # جمع الأخطاء من النموذج
        errors = {field.name: field.errors[0] for field in form if field.errors}
        return jsonify({'success': False, 'message': 'بيانات غير صالحة', 'errors': errors}), 400

@admin.route('/admin/deactivate_discount/<int:discount_id>', methods=['POST'])
@admin_login_required
def deactivate_discount(discount_id):
    discount = Discount.query.get_or_404(discount_id)
    discount.is_active = False
    db.session.commit()
    flash('تم تعطيل كود الخصم', 'success')
    return redirect(url_for('admin.discounts'))

@admin.route('/admin/')
def admin_home():
    return redirect(url_for('admin.products'))

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