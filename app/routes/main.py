from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from app.models import Product, Design, Contact, Order, Page, Setting, Announcement, FAQ
from app.forms import ContactForm
from app import db
import json
import os
import uuid
from werkzeug.utils import secure_filename
from flask_wtf.file import FileAllowed
from datetime import datetime

main = Blueprint('main', __name__, template_folder='../../templates')

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

@main.route('/custom-design')
def custom_design():
    return render_template('main/custom_design.html')

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
        query = query.filter(Product.name.ilike(f'%{search_query}%'))
    
    if category == 'palestine':
        query = query.filter(Product.category.ilike('palestine'))
        title = "منتجات فلسطين"
    elif category == 'trending':
        query = query.filter(Product.is_trending == True)
        title = "المنتجات الرائجة"
    elif category == 'featured':
        query = query.filter(Product.featured == True)
        title = "المنتجات المميزة"
    elif category:
        query = query.filter(Product.category.ilike(f'%{category}%'))
        title = f"منتجات {category}"
    else:
        title = "جميع المنتجات"
    
    if min_price and min_price.isdigit():
        query = query.filter(Product.price >= float(min_price))
    
    if max_price and max_price.isdigit():
        query = query.filter(Product.price <= float(max_price))
    
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
        searched_ref = request.form.get('order_number')
    elif request.method == 'GET':
        searched_ref = request.args.get('order_number')

    if searched_ref:
        order = Order.query.filter_by(reference=searched_ref).first()
        if not order:
            error_message = 'لم يتم العثور على طلب بهذا الرقم. يرجى التأكد من الرقم والمحاولة مرة أخرى.'
            flash(error_message, 'danger')
    
    return render_template('main/track_order.html', order=order, searched_order_number=searched_ref, error_message_for_template=error_message)

@main.route('/setup')
def setup():
    if not current_app.debug:
        return 'غير مسموح في وضع الإنتاج', 403
    db.create_all()
    flash('تم تهيئة جميع الجداول بنجاح!', 'success')
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
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    products = Product.query.filter(Product.name.ilike(f'%{query}%')).limit(5).all()
    suggestions = [{'name': p.name, 'url': url_for('main.product_detail', product_id=p.id)} for p in products]
    
    return jsonify(suggestions)

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