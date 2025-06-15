from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from app.models import Product, Order, OrderItem, Cart, CartItem, Design, Governorate # Added Cart, CartItem, Design, Governorate
from app.extensions import db, csrf # For db.session and csrf
from app.forms import CheckoutForm # For CheckoutForm
import uuid, os, json
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from datetime import datetime
from app.utils import get_or_create_cart, calculate_cart_total
from app.utils.email_utils import send_email
from flask import current_app # Add this import for logging

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

def get_or_create_cart():
    """
    الحصول على سلة التسوق الحالية أو إنشاء واحدة جديدة
    
    يقوم بالتحقق من وجود معرف سلة في الجلسة
    إذا كان موجوداً، يحاول استرداد السلة من قاعدة البيانات
    إذا لم يكن موجوداً أو لم يتم العثور على السلة، يقوم بإنشاء سلة جديدة
    
    Returns:
        Cart: كائن سلة التسوق
    """
    try:
        cart_id = session.get('cart_id')
        if cart_id:
            cart = Cart.query.filter_by(session_id=cart_id).first()
            if cart:
                # تحديث وقت الإنشاء للسلة لمنع انتهاء صلاحيتها
                cart.created_at = datetime.utcnow()
                db.session.commit()
                return cart
                
        # إنشاء معرّف جلسة جديد وسلة جديدة
        session_id = str(uuid.uuid4())
        cart = Cart(session_id=session_id)
        db.session.add(cart)
        db.session.commit()
        session['cart_id'] = session_id
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

@cart_bp.route('/cart')
def cart():
    cart = get_or_create_cart()
    cart_items = []
    total = 0
    items_removed = False

    for item in list(cart.items):
        product = Product.query.get(item.product_id)
        
        if not product:
            db.session.delete(item)
            items_removed = True
            continue
            
        design = Design.query.get(item.design_id) if item.design_id else None
        subtotal = product.price * item.quantity
        cart_items.append({
            'id': item.id,
            'product': product,
            'design': design,
            'custom_design_path': item.custom_design_path,
            'quantity': item.quantity,
            'size': item.size,
            'color': item.color,
            'subtotal': subtotal
        })
        total += subtotal
    
    if items_removed:
        db.session.commit()
        flash('تمت إزالة بعض المنتجات من سلتك لأنها لم تعد متوفرة.', 'warning')
        
    return render_template('cart/cart.html', cart_items=cart_items, total=total)

@cart_bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    current_app.logger.info("--- Add to Cart Fired ---")
    
    try:
        current_app.logger.info(f"Form data received: {request.form}")

        product_id = request.form.get('product_id', type=int)
        if not product_id:
            current_app.logger.error("No product_id in form data.")
            return jsonify({
                'success': False,
                'message': 'معرّف المنتج مفقود.'
            }), 400
            
        product = Product.query.get_or_404(product_id)
        if not product.in_stock:
            return jsonify({
                'success': False,
                'message': 'هذا المنتج غير متوفر حالياً في المخزون.'
            }), 400
            
        current_app.logger.info(f"Product found: {product.name}")

        is_from_product_page = 'size' in request.form or 'color' in request.form
        current_app.logger.info(f"Is from product page? {is_from_product_page}")

        # التحقق من وجود خيارات المقاس واللون
        try:
            requires_size = product.sizes and json.loads(product.sizes)
            requires_color = product.colors and product.colors.strip()
        except json.JSONDecodeError:
            requires_size = False  # If sizes is not valid JSON, treat as not requiring size.
            current_app.logger.warning(f"Product {product.id} has invalid JSON in 'sizes' field.")
            
        current_app.logger.info(f"Requires size? {bool(requires_size)}. Requires color? {bool(requires_color)}")

        if (requires_size or requires_color) and not is_from_product_page:
            current_app.logger.info("Redirecting to product page because options are required.")
            flash('الرجاء تحديد خيارات المنتج أولاً.', 'info')
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {'redirect': url_for('main.product_detail', product_id=product.id)}, 400
            return redirect(url_for('main.product_detail', product_id=product.id))

        size = request.form.get('size')
        color = request.form.get('color')
        current_app.logger.info(f"Size selected: {size}. Color selected: {color}")

        if is_from_product_page:
            if requires_size and not size:
                current_app.logger.warning("Validation failed: Size is required but not provided.")
                flash('يجب اختيار المقاس.', 'danger')
                return redirect(url_for('main.product_detail', product_id=product.id))
            if requires_color and not color:
                current_app.logger.warning("Validation failed: Color is required but not provided.")
                flash('يجب اختيار اللون.', 'danger')
                return redirect(url_for('main.product_detail', product_id=product.id))
                
        final_size = size if size else 'Standard'
        final_color = color if color else 'Default'
        quantity = request.form.get('quantity', 1, type=int)

        cart = get_or_create_cart()
        current_app.logger.info(f"Using cart with session_id: {cart.session_id}")

        existing_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id, size=final_size, color=final_color).first()

        if existing_item:
            current_app.logger.info(f"Found existing item (ID: {existing_item.id}). Increasing quantity.")
            existing_item.quantity += quantity
        else:
            current_app.logger.info("No existing item found. Creating new CartItem.")
            new_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity, size=final_size, color=final_color)
            db.session.add(new_item)
        
        try:
            db.session.commit()
            current_app.logger.info("Database commit successful.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error on commit: {e}")
            return {'message': 'Database error.'}, 500

        total_items = db.session.query(db.func.sum(CartItem.quantity)).filter(CartItem.cart_id == cart.id).scalar() or 0
        session['cart_count'] = total_items
        current_app.logger.info(f"Cart update complete. New total items: {total_items}")

        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {'message': 'تمت إضافة المنتج بنجاح!', 'cart_count': total_items}, 200
        
        flash('تمت إضافة المنتج بنجاح!', 'success')
        return redirect(url_for('cart.cart'))
            
    except Exception as e:
        current_app.logger.error(f"Error adding product to cart: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إضافة المنتج إلى السلة'
        }), 500

@cart_bp.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart = get_or_create_cart()
    cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not cart_item:
        return {'message': 'لم يتم العثور على العنصر'}, 404
    db.session.delete(cart_item)
    db.session.commit()
    
    # إعادة حساب العدد الإجمالي بعد الحذف
    total_items = sum(item.quantity for item in cart.items)
    session['cart_count'] = total_items
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'message': 'تم حذف المنتج بنجاح', 'cart_count': total_items}, 200
    
    flash('تم حذف المنتج من سلة التسوق', 'success')
    return redirect(url_for('cart.cart'))

@cart_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = Cart.query.filter_by(session_id=session.get('cart_id')).first()
    if not cart or not cart.items.all():
        flash('سلة التسوق فارغة.', 'info')
        return redirect(url_for('main.index'))

    form = CheckoutForm()
    governorates = Governorate.query.order_by(Governorate.name.asc()).all()
    # إضافة خيار افتراضي واحد فقط للمحافظة
    form.governorate.choices = [('', 'اختر المحافظة')] + [(g.id, f"{g.name} (+{g.delivery_fee:.2f} ج.م)") for g in governorates]

    products_total = sum(item.product.price * item.quantity for item in cart.items if item.product)
    # Delivery fee will be determined after governorate selection
    delivery_fee = 0.0 
    final_total = products_total # Initially, final_total is just products_total

    if form.validate_on_submit():
        selected_governorate_id = form.governorate.data
        selected_governorate = Governorate.query.get(selected_governorate_id)
        if not selected_governorate:
            flash('الرجاء اختيار محافظة صحيحة.', 'danger')
            return render_template('cart/checkout.html', cart=cart, form=form, products_total=products_total, delivery_fee=0, final_total=products_total)

        delivery_fee = selected_governorate.delivery_fee
        final_total = products_total + delivery_fee

        # Order creation logic without discount
        order_data = {
            'customer_name': form.name.data,
            'customer_email': form.email.data,
            'customer_phone': form.phone.data,
            'address': form.address.data,
            'governorate_id': selected_governorate_id,
            'delivery_fee': delivery_fee,
            'payment_method': form.payment_method.data,
            'total_amount': final_total, # Save the final total including delivery
        }
        
        # إنشاء الطلب بدون archived لتجنب مشاكل قاعدة البيانات
        order = Order(**order_data)
        
        db.session.add(order)
        db.session.flush()  # حتى يتوفر order.id

        # تحويل عناصر السلة إلى عناصر الطلب
        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.product.name if cart_item.product else '',
                color=cart_item.color or 'غير محدد',
                size=cart_item.size or 'غير محدد',
                quantity=cart_item.quantity,
                price=cart_item.product.price if cart_item.product else 0
            )
            db.session.add(order_item)

        db.session.commit()

        # Clear cart from session
        session.pop('cart_id', None)
        session.pop('cart_count', None)

        # Send emails after successful commit
        try:
            # Send order confirmation email to the customer
            subject = f"تأكيد طلبك من Sultan Prints (رقم الطلب: #{order.reference})"
            email_body = render_template(
                'emails/order_confirmation_customer.html', 
                order=order
            )
            send_email(
                to_email=order.customer_email,
                subject=subject,
                body_html=email_body
            )
            current_app.logger.info(f"Order confirmation email sent for order {order.reference} to {order.customer_email}")

            # Send notification email to admin
            admin_email = current_app.config.get('ADMIN_EMAIL')
            if admin_email:
                admin_subject = f"طلب جديد على المتجر! رقم الطلب: #{order.reference}"
                admin_body = render_template(
                    'emails/order_notification_admin.html',
                    order=order
                )
                send_email(
                    to_email=admin_email,
                    subject=admin_subject,
                    body_html=admin_body
                )
                current_app.logger.info(f"Admin notification sent for order {order.reference}")
            else:
                current_app.logger.warning("ADMIN_EMAIL not set, skipping admin notification.")

        except Exception as e:
            current_app.logger.error(f"Failed to send email for order {order.reference}: {e}")
        
        flash('تم استلام طلبك بنجاح!', 'success')
        return redirect(url_for('cart.order_confirmation', order_number=order.reference))

    # For GET request, or if form validation fails
    # Delivery fee is 0 initially, will be updated by JS
    # Final total for display is initially just products_total
    return render_template('cart/checkout.html', cart=cart, form=form, products_total=products_total, delivery_fee=0, final_total=products_total)

@cart_bp.route('/order_confirmation/<order_number>')
def order_confirmation(order_number):
    order = Order.query.filter_by(reference=order_number).first_or_404()
    return render_template('cart/order_confirmation.html', order=order)

@cart_bp.route('/get_delivery_fee/<int:governorate_id>')
def get_delivery_fee(governorate_id):
    governorate = Governorate.query.get(governorate_id)
    if governorate:
        return jsonify({'delivery_fee': governorate.delivery_fee, 'name': governorate.name})
    return jsonify({'error': 'Governorate not found'}), 404

@cart_bp.route('/update_quantity', methods=['POST'])
def update_quantity():
    """
    تحديث كمية المنتج في سلة التسوق عبر AJAX
    """
    try:
        item_id = request.form.get('item_id', type=int)
        quantity = request.form.get('quantity', type=int)
        
        if not item_id or not quantity:
            return jsonify({
                'success': False,
                'message': 'بيانات غير صالحة'
            }), 400
            
        # تحديد الحد الأدنى والأقصى للكمية
        if quantity < 1:
            quantity = 1
        elif quantity > 10:
            quantity = 10
            
        # التحقق من وجود سلة للمستخدم
        cart = get_or_create_cart()
        if not cart:
            return jsonify({
                'success': False,
                'message': 'خطأ في السلة'
            }), 400
            
        # البحث عن العنصر في السلة
        cart_item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
        if not cart_item:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود في السلة'
            }), 404
            
        # تحديث الكمية
        cart_item.quantity = quantity
        db.session.commit()
        
        # حساب إجمالي المنتج وإجمالي السلة
        product = Product.query.get(cart_item.product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'المنتج غير موجود'
            }), 404
            
        subtotal = product.price * quantity
        total_amount, _ = calculate_cart_total(cart)
        
        return jsonify({
            'success': True,
            'subtotal': f"{subtotal:.2f} جنيه",
            'total': f"{total_amount:.2f} جنيه",
            'quantity': quantity
        })
    except Exception as e:
        current_app.logger.error(f"Error updating cart quantity: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث السلة'
        }), 500