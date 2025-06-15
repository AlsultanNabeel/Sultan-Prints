from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from app.models import Product, Design, Contact, Order, Page, Setting, Announcement, FAQ, CustomDesign, Governorate
from app.forms import ContactForm
from app import db
from app.utils.email_utils import send_email
import json
import os
import uuid
from werkzeug.utils import secure_filename
from flask_wtf.file import FileAllowed
from datetime import datetime
import requests
import random
import string

main = Blueprint('main', __name__, template_folder='../../templates')

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'ai', 'psd'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    featured_products = Product.query.filter_by(featured=True).limit(8).all()
    
    # Fetch all settings into a dictionary
    settings_query = Setting.query.all()
    settings = {setting.key: setting.value for setting in settings_query}
    
    return render_template('main/index.html', 
                           products=featured_products, 
                           settings=settings,
                           # for backward compatibility with existing variables
                           hero_image=settings.get('hero_image'),
                           hero_height=settings.get('hero_height'),
                           about_us_content=settings.get('homepage_about_us_content'),
                           about_products_content=settings.get('homepage_about_products_content'))

@main.route('/custom-design', methods=['GET', 'POST'])
def custom_design():
    if request.method == 'POST':
        if 'design_file' not in request.files:
            flash('يرجى اختيار ملف التصميم', 'error')
            return redirect(request.url)
        
        file = request.files['design_file']
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Save design file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"custom_design_{timestamp}_{filename}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'custom_designs', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            
            # Create custom design record
            custom_design = CustomDesign(
                design_file=filename,
                design_description=request.form.get('description', ''),
                status='pending'
            )
            db.session.add(custom_design)
            db.session.commit()
            
            # Create order for custom design
            order = Order(
                reference=''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
                customer_name=request.form.get('customer_name', ''),
                customer_email=request.form.get('customer_email', ''),
                customer_phone=request.form.get('customer_phone', ''),
                address=request.form.get('address', ''),
                governorate_id=request.form.get('governorate_id'),
                delivery_fee=50.0,  # Fixed delivery fee
                payment_method='vodafone_cash',
                total_amount=600.0,  # Fixed price for custom design
                status='pending'
            )
            db.session.add(order)
            db.session.commit()
            
            # Link custom design to order
            custom_design.order_id = order.id
            db.session.commit()
            
            flash('تم رفع التصميم المخصص بنجاح وإنشاء الطلب', 'success')
            return redirect(url_for('cart.order_confirmation', order_number=order.reference))
        else:
            flash('نوع الملف غير مسموح به', 'error')
    
    governorates = Governorate.query.all()
    return render_template('main/custom_design.html', governorates=governorates)

@main.route('/products')
def products():
    # Get search and filter parameters
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    sort_by = request.args.get('sort_by', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Start with base query
    query = Product.query.filter_by(in_stock=True)
    
    # Apply filters
    if search_query:
        # استخدام الباراميتر الآمن بدلاً من تنسيق السلسلة النصية مباشرة
        query = query.filter(Product.name.ilike(f"%{search_query}%"))
    
    if category == 'palestine':
        query = query.filter(Product.is_palestine == True)
        title = "منتجات فلسطين"
    elif category == 'trending':
        query = query.filter(Product.is_trending == True)
        title = "المنتجات الرائجة"
    elif category == 'featured':
        query = query.filter(Product.featured == True)
        title = "المنتجات المميزة"
    elif category:
        # استخدام الباراميتر الآمن
        query = query.filter(Product.category.ilike(f"%{category}%"))
        title = f"منتجات {category}"
    else:
        title = "جميع المنتجات"
    
    if min_price and min_price.isdigit():
        try:
            query = query.filter(Product.price >= float(min_price))
        except (ValueError, TypeError):
            # تجاهل القيم غير الصالحة
            pass
    
    if max_price and max_price.isdigit():
        try:
            query = query.filter(Product.price <= float(max_price))
        except (ValueError, TypeError):
            # تجاهل القيم غير الصالحة
            pass
    
    # Apply sorting
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())
    
    # Paginate results
    products = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options for sidebar
    categories = db.session.query(Product.category).distinct().filter(
        Product.category.isnot(None), Product.category != ''
    ).all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    price_range = db.session.query(
        db.func.min(Product.price), 
        db.func.max(Product.price)
    ).first()
    
    return render_template('main/products.html', 
                         products=products, 
                         title=title,
                         categories=categories,
                         price_range=price_range,
                         current_filters={
                             'search': search_query,
                             'category': category,
                             'min_price': min_price,
                             'max_price': max_price,
                             'sort_by': sort_by
                         })

@main.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    designs = Design.query.filter_by(is_default=True).all()
    
    try:
        sizes = json.loads(product.sizes) if product.sizes else []
    except (json.JSONDecodeError, TypeError):
        sizes = []

    # Prepare colors for the template
    raw_colors = [c.strip() for c in (product.colors or '').split(',') if c.strip()]
    color_map = {
        'white': ('أبيض', '#FFFFFF'),
        'black': ('أسود', '#000000'),
        'red': ('أحمر', '#FF0000'),
        'blue': ('أزرق', '#0000FF'),
        'green': ('أخضر', '#008000'),
        'yellow': ('أصفر', '#FFFF00'),
        'beige': ('بيج', '#F5F5DC'),
        'gray': ('رمادي', '#808080'),
        'navy': ('كحلي', '#000080'),
        'pink': ('وردي', '#FFC0CB'),
        'purple': ('بنفسجي', '#800080'),
        'brown': ('بني', '#A52A2A'),
        'orange': ('برتقالي', '#FFA500'),
    }
    
    display_colors = []
    for color_val in raw_colors:
        name, hex_code = color_map.get(color_val.lower(), (color_val, '#808080'))
        display_colors.append({
            'value': color_val,
            'name': name,
            'hex': hex_code
        })

    return render_template('main/product_detail.html', 
                           product=product, 
                           designs=designs, 
                           sizes=sizes, 
                           colors=display_colors)

@main.route('/about')
def about():
    # Redirect to the dynamic page
    return redirect(url_for('main.show_page', slug='about-us'))

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    page = Page.query.filter_by(slug='contact-us').first_or_404()
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.display_order.asc()).all()
    if form.validate_on_submit():
        contact_msg = Contact(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            message=form.message.data
        )
        db.session.add(contact_msg)
        db.session.commit()

        # Send email notification to admin
        admin_email = current_app.config.get('ADMIN_EMAIL')
        if admin_email:
            subject = f"رسالة جديدة من صفحة تواصل معنا من {form.name.data}"
            body_html = render_template('emails/contact_notification.html', msg=contact_msg)
            send_email(admin_email, subject, body_html)
        else:
            current_app.logger.warning("ADMIN_EMAIL is not set. Cannot send contact form notification.")

        flash('تم إرسال رسالتك بنجاح، سنتواصل معك قريبًا', 'success')
        return redirect(url_for('main.contact'))
    return render_template('main/contact.html', form=form, page=page, faqs=faqs)

# Dynamic page route
@main.route('/page/<slug>')
def show_page(slug):
    page = Page.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('main/page.html', page=page)

@main.route('/track_order', methods=['GET', 'POST'])
def track_order():
    order = None
    error_message = None
    searched_ref = None

    if request.method == 'POST':
        searched_ref = request.form.get('order_number', '').strip()
    elif request.method == 'GET':
        searched_ref = request.args.get('order_number', '').strip()

    if searched_ref:
        # تحقق من صحة رقم الطلب (يجب أن يكون أبجدي رقمي فقط)
        if not searched_ref.isalnum():
            error_message = 'رقم الطلب غير صالح. يجب أن يحتوي على أحرف وأرقام فقط.'
            flash(error_message, 'danger')
        else:
            # استخدام طريقة آمنة للبحث
            order = Order.query.filter_by(reference=searched_ref).first()
            if not order:
                error_message = 'لم يتم العثور على طلب بهذا الرقم. يرجى التأكد من الرقم والمحاولة مرة أخرى.'
                # تسجيل محاولات البحث الفاشلة لتتبع محاولات الاختراق المحتملة
                current_app.logger.warning(f"Failed order tracking attempt: {searched_ref} from IP: {request.remote_addr}")
                flash(error_message, 'danger')
            else:
                # تسجيل عمليات البحث الناجحة
                current_app.logger.info(f"Successful order tracking: {order.reference}")
    
    return render_template('main/track_order.html', order=order, searched_order_number=searched_ref, error_message_for_template=error_message)

@main.route('/setup')
def setup():
    # منع الوصول في بيئة الإنتاج
    if not current_app.debug:
        current_app.logger.warning(f"Attempted access to /setup in production mode from IP: {request.remote_addr}")
        return abort(404)  # إخفاء المسار تماماً في الإنتاج
        
    # تطلب كلمة مرور أو توكن أمان إضافي حتى في وضع التطوير
    setup_token = request.args.get('token')
    if setup_token != current_app.config.get('SETUP_SECRET_KEY'):
        current_app.logger.warning(f"Unauthorized setup attempt with token: {setup_token} from IP: {request.remote_addr}")
        return 'غير مصرح به', 403
        
    try:
        # استخدم create_all بحذر - ينبغي استخدام migrations بدلاً من ذلك
        db.create_all()
        flash('تم تهيئة جميع الجداول بنجاح!', 'success')
        current_app.logger.info(f"Database tables created successfully by IP: {request.remote_addr}")
        return redirect(url_for('main.index'))
    except Exception as e:
        current_app.logger.error(f"Error in setup: {str(e)}", exc_info=True)
        flash(f'حدث خطأ أثناء تهيئة قاعدة البيانات: {str(e)}', 'danger')
        return redirect(url_for('main.index'))
    return redirect(url_for('main.index'))

@main.route('/upload_custom_design', methods=['POST'])
def upload_custom_design():
    file = request.files.get('design_image')
    details = request.form.get('details', '')
    size = request.form.get('size')
    color = request.form.get('color')

    if file and file.filename:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            flash(f"نوع الملف غير مسموح. الأنواع المسموحة: {', '.join(allowed_extensions)}", 'danger')
            return redirect(url_for('main.index'))

        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'custom_requests')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Save metadata to a corresponding JSON file
        base_filename, _ = os.path.splitext(unique_filename)
        json_filename = f"{base_filename}.json"
        json_filepath = os.path.join(upload_folder, json_filename)
        
        metadata = {
            'original_filename': filename,
            'size': size,
            'color': color,
            'details': details,
            'uploaded_at': datetime.now().isoformat()
        }
        
        try:
            # Save the image
            file.save(file_path)
            
            # Save the metadata
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
                
            log_message = (
                f"New custom design request: \n"
                f"  File: {unique_filename}\n"
                f"  Path: {file_path}\n"
                f"  Size: {size}\n"
                f"  Color: {color}\n"
                f"  Details: {details}"
            )
            current_app.logger.info(log_message)
            flash('تم رفع تصميمك بنجاح! سيتم التواصل معك قريبًا لمناقشة التفاصيل والتكلفة.', 'success')
        except Exception as e:
            current_app.logger.error(f"Error saving custom design: {e}")
            flash('حدث خطأ أثناء حفظ التصميم. يرجى المحاولة مرة أخرى.', 'danger')
            
    else:
        flash('يجب اختيار صورة تصميم لرفعها.', 'danger')
    return redirect(url_for('main.custom_design'))

@main.route('/api/products/quick-view/<int:product_id>')
def product_quick_view(product_id):
    """API endpoint for quick product preview"""
    product = Product.query.get_or_404(product_id)
    try:
        sizes = json.loads(product.sizes) if product.sizes else []
    except (json.JSONDecodeError, TypeError):
        sizes = []
    
    colors = [c.strip() for c in (product.colors or '').split(',') if c.strip()]
    
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'image': url_for('static', filename=product.image or 'images/placeholder.jpg'),
        'sizes': sizes,
        'colors': colors,
        'in_stock': product.in_stock
    })

@main.route('/api/search/suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    try:
        # استخدام طريقة آمنة للبحث
        products = Product.query.filter(
            Product.name.ilike(f"%{query}%")
        ).filter(
            Product.in_stock == True
        ).limit(5).all()
        
        suggestions = [
            {
                'name': p.name, 
                'url': url_for('main.product_detail', product_id=p.id),
                'id': p.id
            } 
            for p in products
        ]
        
        return jsonify(suggestions)
    except Exception as e:
        current_app.logger.error(f"Error in search suggestions: {str(e)}", exc_info=True)
        return jsonify([]), 500

@main.app_context_processor
def inject_global_data():
    """
    Injects global data into all templates.
    """
    # Fetch active announcements
    active_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
    
    # Fetch social media and contact info from settings
    setting_keys = [
        'facebook_url', 'instagram_url', 'twitter_url', 'whatsapp_number', 
        'contact_email', 'phone_number', 'address'
    ]
    settings = Setting.query.filter(Setting.key.in_(setting_keys)).all()
    # Convert to a dictionary for easy access in templates
    site_settings = {setting.key: setting.value for setting in settings}

    return {
        'active_announcements': active_announcements,
        'site_settings': site_settings,
        'now': datetime.utcnow()
    }

@main.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Subscribe to newsletter using Mailerlite API"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'البريد الإلكتروني مطلوب'}), 400
        
        # Mailerlite API configuration
        api_key = current_app.config.get('MAILERLITE_API_KEY')
        group_id = current_app.config.get('MAILERLITE_GROUP_ID', 'default_group_id')
        
        if not api_key:
            current_app.logger.warning("MAILERLITE_API_KEY not configured")
            return jsonify({'success': False, 'message': 'خدمة النشرة البريدية غير متاحة حالياً'}), 503
        
        # Mailerlite API endpoint
        url = f"https://connect.mailerlite.com/api/subscribers"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'email': email,
            'groups': [group_id],
            'status': 'active'
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            # Send welcome email
            welcome_subject = "مرحباً بك في النشرة البريدية - Sultan Prints"
            welcome_body = f"""
            <h2>مرحباً بك في النشرة البريدية!</h2>
            <p>شكراً لك على الاشتراك في نشرتنا البريدية. ستتلقى آخر العروض والتخفيضات مباشرة إلى بريدك الإلكتروني.</p>
            <p>يمكنك إلغاء الاشتراك في أي وقت من خلال الرابط الموجود في نهاية كل رسالة.</p>
            """
            
            send_email(email, welcome_subject, welcome_body)
            
            return jsonify({'success': True, 'message': 'تم الاشتراك بنجاح!'}), 200
        elif response.status_code == 409:
            return jsonify({'success': False, 'message': 'أنت مشترك بالفعل في النشرة البريدية'}), 409
        else:
            current_app.logger.error(f"Mailerlite API error: {response.status_code} - {response.text}")
            return jsonify({'success': False, 'message': 'حدث خطأ أثناء الاشتراك'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Newsletter subscription error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'حدث خطأ في الخادم'}), 500