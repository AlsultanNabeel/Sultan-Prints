import os
import secrets
from PIL import Image
from flask import current_app, session
from ..extensions import db
from ..models import Setting, Cart, Product, CartItem
import uuid
import logging

def log_event(message, level='info'):
    """Logs an event using the application's logger."""
    if level == 'info':
        current_app.logger.info(message)
    elif level == 'warning':
        current_app.logger.warning(message)
    elif level == 'error':
        current_app.logger.error(message)
    elif level == 'critical':
        current_app.logger.critical(message)
    else:
        current_app.logger.debug(message)

def allowed_file(filename):
    """Checks if the file extension is allowed."""
    if not filename:
        return False
    try:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    except (IndexError, AttributeError, KeyError):
        # حدثت مشكلة في التحقق من امتداد الملف
        log_event(f"Error checking file extension for: {filename}", level='error')
        return False

def save_image(file, folder='designs'):
    """Saves an uploaded image and returns the filename."""
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(file.filename)
        picture_fn = random_hex + f_ext
        uploads_folder = os.path.join(current_app.static_folder, 'uploads')
        target_folder = os.path.join(uploads_folder, folder)
        picture_path = os.path.join(target_folder, picture_fn)
        
        # التأكد من وجود المجلدات
        os.makedirs(os.path.dirname(picture_path), exist_ok=True)
        
        # التحقق من صحة الصورة قبل الحفظ
        try:
            i = Image.open(file)
            i.verify()  # التحقق من أن الملف هو صورة صالحة
            file.seek(0)  # إعادة تعيين المؤشر بعد التحقق
            
            i = Image.open(file)
            # استخدام LANCZOS للحصول على جودة أفضل
            i.thumbnail((1200, 1200), Image.LANCZOS)
            
            # حفظ بجودة عالية مع الحفاظ على الشفافية للصور PNG
            if f_ext.lower() in ('.png', '.webp'):
                i.save(picture_path, optimize=True)
            else:
                i.save(picture_path, quality=90, optimize=True)
            
            # تسجيل نجاح رفع الصورة
            log_event(f"Image uploaded successfully: {picture_fn} to {folder}", level='info')
            
            return os.path.join('uploads', folder, picture_fn)
        except Exception as e:
            log_event(f"Error processing image: {e}", level='error')
            return None
    except Exception as e:
        log_event(f"Error saving image: {e}", level='error')
        return None

def inject_settings():
    """Injects site-wide settings into all templates."""
    try:
        settings_list = Setting.query.all()
        settings = {setting.key: setting.value for setting in settings_list}
        return dict(settings=settings)
    except Exception:
        return dict(settings={})

def get_or_create_cart():
    """Gets the cart from the session or creates a new one."""
    cart_session_id = session.get('cart_id')
    if cart_session_id:
        cart = Cart.query.filter_by(session_id=cart_session_id).first()
        if cart:
            return cart
    
    new_session_id = str(uuid.uuid4())
    cart = Cart(session_id=new_session_id)
    db.session.add(cart)
    db.session.commit()
    session['cart_id'] = new_session_id
    return cart

def calculate_cart_total(cart):
    """Calculates the total amount and item count for a given cart."""
    total_amount = 0
    total_items = 0
    if not cart:
        return 0, 0
        
    for item in cart.items:
        product = Product.query.get(item.product_id)
        if product and product.in_stock:
            total_amount += product.price * item.quantity
            total_items += item.quantity
    return total_amount, total_items

def inject_cart_item_count():
    """Injects the cart item count into all templates."""
    try:
        cart = get_or_create_cart()
        _, total_items = calculate_cart_total(cart)
        return dict(cart_item_count=total_items)
    except Exception as e:
        # Log the error but don't break the template rendering
        current_app.logger.error(f"Error in inject_cart_item_count: {str(e)}")
        return dict(cart_item_count=0) 