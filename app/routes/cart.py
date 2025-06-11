from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort, current_app, jsonify
from app.models import Product, Cart, CartItem, Design, Order, OrderItem
from app.forms import CheckoutForm
from app import db
import uuid, os, json
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from datetime import datetime
from app.utils import get_or_create_cart, calculate_cart_total
from app.services.discounts import DiscountManager
from app.utils.email_utils import send_email

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.app_context_processor
def inject_cart_count():
    """
    Injects an accurate cart count into all templates on every request.
    This is the definitive source of truth for the cart count.
    """
    if 'cart_id' in session:
        cart = Cart.query.filter_by(session_id=session['cart_id']).first()
        if cart:
            # Perform an efficient count directly in the database
            total_items = db.session.query(db.func.sum(CartItem.quantity)).filter(CartItem.cart_id == cart.id).scalar() or 0
            session['cart_count'] = total_items # Keep session in sync
            return dict(cart_count=total_items)
            
    # If there's no cart or no cart_id, the count is 0
    if 'cart_count' not in session:
        session['cart_count'] = 0
    return dict(cart_count=session.get('cart_count', 0))

def get_or_create_cart():
    cart_id = session.get('cart_id')
    if cart_id:
        cart = Cart.query.filter_by(session_id=cart_id).first()
        if cart:
            return cart
    session_id = str(uuid.uuid4())
    cart = Cart(session_id=session_id)
    db.session.add(cart)
    db.session.commit()
    session['cart_id'] = session_id
    return cart

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
    current_app.logger.info(f"Form data received: {request.form}")

    product_id = request.form.get('product_id', type=int)
    if not product_id:
        current_app.logger.error("No product_id in form data.")
        return {'message': 'Product ID is missing.'}, 400
        
    product = Product.query.get_or_404(product_id)
    current_app.logger.info(f"Product found: {product.name}")

    is_from_product_page = 'size' in request.form or 'color' in request.form
    current_app.logger.info(f"Is from product page? {is_from_product_page}")

    try:
        requires_size = product.sizes and json.loads(product.sizes)
        requires_color = product.colors and product.colors.strip()
        current_app.logger.info(f"Requires size? {bool(requires_size)}. Requires color? {bool(requires_color)}")
    except json.JSONDecodeError:
        requires_size = False # If sizes is not valid JSON, treat as not requiring size.
        current_app.logger.warning(f"Product {product.id} has invalid JSON in 'sizes' field.")


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
    # This is a simplified version of the original checkout logic
    cart = Cart.query.filter_by(session_id=session.get('cart_id')).first()
    if not cart or not cart.items.all():
        flash('سلة التسوق فارغة.', 'info')
        return redirect(url_for('main.index'))

    form = CheckoutForm()
    
    # Calculation logic to be used for both POST and GET
    products_total = sum(item.product.price * item.quantity for item in cart.items if item.product)
    shipping_cost = 50.0 if products_total <= 500 else 0.0
    final_total = products_total + shipping_cost

    if form.validate_on_submit():
        # Get discount from session if available
        discount_code = session.get('discount_code')
        discount_amount = session.get('discount_amount', 0)

        # Recalculate final total with discount
        final_total_with_discount = products_total + shipping_cost - discount_amount

        # Order creation logic with discount
        order = Order(
            customer_name=form.name.data,
            customer_phone=form.phone.data,
            customer_email=form.email.data,
            address=form.address.data,
            payment_method=form.payment_method.data,
            total_amount=final_total_with_discount,
            discount_code=discount_code,
            discount_amount=discount_amount
        )
        
        db.session.add(order)

        # ... (rest of order creation logic like saving items and clearing cart) ...
        # Clear cart and discount from session
        session.pop('cart_id', None)
        session.pop('cart_count', None)
        session.pop('discount_code', None)
        session.pop('discount_amount', None)

        db.session.commit()

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

    return render_template(
        'cart/checkout.html',
        form=form,
        cart_items=cart.items,
        products_total=products_total,
        shipping_cost=shipping_cost,
        final_total=final_total,
        vodafone_number=current_app.config.get('VODAFONE_CASH_NUMBER')
    )

@cart_bp.route('/order_confirmation/<order_number>')
def order_confirmation(order_number):
    order = Order.query.filter_by(reference=order_number).first_or_404()
    return render_template('cart/order_confirmation.html', order=order)

@cart_bp.route('/apply_coupon', methods=['POST'])
def apply_coupon():
    """Applies a coupon to the cart."""
    code = request.json.get('coupon_code')
    if not code:
        return jsonify({'error': 'لم يتم تقديم رمز القسيمة'}), 400

    cart = get_or_create_cart()
    if not cart.items:
        return jsonify({'error': 'سلة التسوق فارغة'}), 400

    products_total = sum(item.product.price * item.quantity for item in cart.items if item.product)
    
    discount_amount, message = DiscountManager.validate_coupon(code, products_total)
    
    if discount_amount > 0:
        session['discount_code'] = code
        session['discount_amount'] = discount_amount
        return jsonify({
            'success': True,
            'message': message,
            'discount_amount': discount_amount,
            'new_total': products_total - discount_amount
        })
    else:
        session.pop('discount_code', None)
        session.pop('discount_amount', None)
        return jsonify({'success': False, 'error': message}), 400

# يمكن إضافة مسارات add_to_cart و remove_from_cart لاحقًا بنفس النمط مع حماية قوية