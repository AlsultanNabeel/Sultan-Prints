import os
import secrets
from PIL import Image
from flask import current_app, session
from ..extensions import db
from ..models import Setting, Cart, Product, CartItem
import uuid
import logging
from .storage import spaces_storage
from datetime import datetime
from werkzeug.utils import secure_filename

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

def save_image(file, folder='designs', is_public=True):
    """
    Saves an uploaded image.
    Tries to save to DigitalOcean Spaces first, falls back to local storage if not configured.
    """
    if not file or not allowed_file(file.filename):
        return None

    # Try saving to DigitalOcean Spaces if configured
    if spaces_storage.bucket_name:
        try:
            image_url = spaces_storage.save_image(file, folder, is_public=is_public)
            if image_url:
                log_event(f"Image uploaded successfully to Spaces: {image_url}", level='info')
                return image_url
            else:
                log_event("Failed to upload image to Spaces, falling back to local storage.", level='warning')
        except Exception as e:
            log_event(f"Error saving image to Spaces, falling back to local: {e}", level='error')
            # Rewind file pointer after read attempt by spaces_storage
            file.seek(0)

    # Fallback to local storage
    try:
        random_hex = secrets.token_hex(16)
        _, f_ext = os.path.splitext(secure_filename(file.filename))
        picture_fn = f"{random_hex}{f_ext}"
        
        # Ensure the target directory exists
        upload_folder_path = os.path.join(current_app.root_path, 'static/uploads', folder)
        os.makedirs(upload_folder_path, exist_ok=True)
        
        picture_path = os.path.join(upload_folder_path, picture_fn)
        
        # Resize and save the image
        output_size = (1200, 1200)
        i = Image.open(file)
        i.thumbnail(output_size, Image.Resampling.LANCZOS)
        i.save(picture_path)

        # Return the relative path for use with url_for
        local_url = f"uploads/{folder}/{picture_fn}"
        log_event(f"Image saved locally: {local_url}", level='info')
        return local_url

    except Exception as e:
        log_event(f"Critical error saving image locally: {e}", level='error')
        return None

def delete_image(image_path):
    """
    Deletes an image, trying Spaces first and falling back to local.
    'image_path' can be a full URL or a relative local path.
    """
    if not image_path:
        return False

    # Attempt to delete from Spaces if it looks like a URL
    if image_path.startswith('http'):
        try:
            if spaces_storage.delete_image(image_path):
                log_event(f"Image deleted successfully from Spaces: {image_path}", level='info')
                return True
            else:
                log_event(f"Could not delete from Spaces (or it was already deleted): {image_path}", level='warning')
                # Do not fall back if it's a URL, as it's not a local file.
                return False
        except Exception as e:
            log_event(f"Error deleting image from Spaces: {e}", level='error')
            return False

    # Fallback to deleting from local storage
    try:
        local_path = os.path.join(current_app.root_path, 'static', image_path)
        if os.path.exists(local_path):
            os.remove(local_path)
            log_event(f"Image deleted successfully from local storage: {local_path}", level='info')
            return True
        else:
            log_event(f"Local image not found for deletion: {local_path}", level='warning')
            return False
    except Exception as e:
        log_event(f"Critical error deleting image locally: {e}", level='error')
        return False

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
    try:
        cart_session_id = session.get('cart_id')
        if cart_session_id:
            cart = Cart.query.filter_by(session_id=cart_session_id).first()
            if cart:
                # تحديث وقت الإنشاء للسلة لمنع انتهاء صلاحيتها
                cart.created_at = datetime.utcnow()
                db.session.commit()
                return cart
        
        # إنشاء معرّف جلسة جديد وسلة جديدة
        new_session_id = str(uuid.uuid4())
        cart = Cart(session_id=new_session_id)
        db.session.add(cart)
        db.session.commit()
        session['cart_id'] = new_session_id
        return cart
    except Exception as e:
        current_app.logger.error(f"Error in get_or_create_cart: {str(e)}", exc_info=True)
        # في حالة حدوث خطأ، نحاول إنشاء سلة جديدة كحل بديل
        try:
            session_id = str(uuid.uuid4())
            cart = Cart(session_id=session_id)
            db.session.add(cart)
            db.session.commit()
            session['cart_id'] = session_id
            return cart
        except Exception as inner_e:
            # في حالة فشل الحل البديل، نسجل الخطأ ونعيد None
            current_app.logger.critical(f"Critical error creating cart: {str(inner_e)}", exc_info=True)
            return None

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