from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort, current_app
from app.models import Product, Cart, CartItem, Design, Order, OrderItem
from app.forms import CheckoutForm
from app import db
import uuid, os, json
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from datetime import datetime

cart_bp = Blueprint('cart', __name__)

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
    from flask import current_app
    cart = get_or_create_cart()
    if not cart.items:
        flash('سلة التسوق فارغة', 'error')
        return redirect(url_for('cart.cart'))
    
    form = CheckoutForm()
    
    if form.validate_on_submit():
        # --- بداية قسم التحقق من المنتجات والأسعار ---
        validated_order_items_data = []
        current_total_amount = 0

        for item in cart.items:
            product = Product.query.get(item.product_id)
            if not product:
                flash(f"عذرًا، المنتج المرتبط بالعنصر في سلتك لم يعد موجودًا. تم حذفه من سلتك.", "error")
                # إزالة العنصر غير الصالح من السلة
                db.session.delete(item)
                db.session.commit()
                return redirect(url_for('cart.cart')) # العودة للسلة ليراها المستخدم محدثة
            
            if not product.in_stock:
                flash(f"عذرًا، المنتج '{product.name}' غير متوفر حاليًا في المخزون. يرجى إزالته من السلة للمتابعة.", "error")
                return redirect(url_for('cart.cart'))

            # إذا كل شيء تمام، قم بتخزين البيانات المؤكدة
            validated_order_items_data.append({
                'product': product,
                'quantity': item.quantity,
                'color': item.color,
                'size': item.size,
                'price_at_checkout': product.price # السعر المؤكد عند الدفع
            })
            current_total_amount += (product.price * item.quantity)
        # --- نهاية قسم التحقق من المنتجات والأسعار ---

        name = form.name.data
        phone = form.phone.data
        address = form.address.data
        payment_method = form.payment_method.data
        vodafone_receipt_path = None
        
        # --- بداية تعديل: حساب الشحن والإجمالي النهائي ---
        products_total = current_total_amount # هذا هو إجمالي المنتجات فقط
        shipping_cost = 50.0 #  تكلفة الشحن الافتراضية
        if products_total > 500:
            shipping_cost = 0.0
        
        final_order_total = products_total + shipping_cost
        # --- نهاية تعديل: حساب الشحن والإجمالي النهائي ---
        
        if payment_method == 'vodafone_cash' and form.vodafone_receipt.data:
            file = form.vodafone_receipt.data
            # التحقق من الملف تم بالفعل بواسطة FileAllowed في النموذج
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'payments')
            os.makedirs(upload_folder, exist_ok=True)
            # اسم ملف فريد للإيصال
            unique_receipt_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(upload_folder, unique_receipt_filename)
            file.save(file_path)
            vodafone_receipt_path = os.path.join('uploads', 'payments', unique_receipt_filename)
        
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        order = Order(
            reference=order_number,
            customer_name=name,
            customer_phone=phone,
            customer_email=session.get('user_email', 'customer@example.com'),
            address=address,
            payment_method=payment_method,
            vodafone_receipt=vodafone_receipt_path,
            total_amount=final_order_total # استخدام المبلغ الإجمالي النهائي (منتجات + شحن)
        )
        db.session.add(order)
        db.session.flush()
        
        for validated_item_data in validated_order_items_data:
            # البحث عن العنصر الأصلي في السلة للحصول على custom_design_path
            cart_item = CartItem.query.filter_by(
                cart_id=cart.id,
                product_id=validated_item_data['product'].id,
                size=validated_item_data['size'],
                color=validated_item_data['color']
            ).first()
            order_item = OrderItem(
                order_id=order.id,
                product_id=validated_item_data['product'].id,
                product_name=validated_item_data['product'].name,
                quantity=validated_item_data['quantity'],
                color=validated_item_data['color'],
                size=validated_item_data['size'],
                price=validated_item_data['price_at_checkout'],
                # إضافة مسار التصميم المخصص إذا وجد
                custom_design_path=cart_item.custom_design_path if cart_item else None
            )
            db.session.add(order_item)
            
        # Clear the cart (original cart items, not the validated list)
        for item_in_original_cart in cart.items: # Iterating on original cart.items
            db.session.delete(item_in_original_cart)
            
        db.session.commit()
        flash('تم استلام طلبك بنجاح! سنقوم بالتواصل معك لتأكيد الطلب.', 'success')
        return redirect(url_for('cart.order_confirmation', order_number=order.reference))
    
    # تحضير بيانات السلة للعرض في نموذج الدفع (إذا فشل التحقق من الصحة أو للطلب GET)
    cart_items_for_display = []
    current_products_total_for_display = 0 #  إجمالي المنتجات للعرض
    # يجب أن نكون حذرين هنا أيضًا بشأن المنتجات المحذوفة عند عرض صفحة الدفع لأول مرة
    clean_cart_for_display = False
    for item_to_display in list(cart.items): # نسخة من القائمة
        product_for_display = Product.query.get(item_to_display.product_id)
        if not product_for_display:
            db.session.delete(item_to_display) # تنظيف السلة بهدوء
            clean_cart_for_display = True
            continue

        subtotal = product_for_display.price * item_to_display.quantity
        cart_items_for_display.append({
            'product': product_for_display,
            'quantity': item_to_display.quantity,
            'size': item_to_display.size,
            'color': item_to_display.color,
            'subtotal': subtotal
        })
        current_products_total_for_display += subtotal
    
    if clean_cart_for_display:
        db.session.commit()

    # --- بداية تعديل: حساب الشحن والإجمالي للعرض ---
    shipping_cost_for_display = 50.0
    if current_products_total_for_display > 500:
        shipping_cost_for_display = 0.0
    
    final_total_for_display = current_products_total_for_display + shipping_cost_for_display
    # --- نهاية تعديل: حساب الشحن والإجمالي للعرض ---

    if session.get('user_name'):
        form.name.data = session.get('user_name')
    
    vodafone_cash_number = current_app.config.get('VODAFONE_CASH_NUMBER') #  الحصول على الرقم من الإعدادات

    return render_template(
        'cart/checkout.html', 
        form=form, 
        cart_items=cart_items_for_display, 
        products_total=current_products_total_for_display, 
        shipping_cost=shipping_cost_for_display,        
        final_total=final_total_for_display,            
        vodafone_number=vodafone_cash_number #  تمرير الرقم إلى القالب
    )

@cart_bp.route('/order_confirmation/<order_number>')
def order_confirmation(order_number):
    order = Order.query.filter_by(reference=order_number).first_or_404()
    return render_template('cart/order_confirmation.html', order=order)

# يمكن إضافة مسارات add_to_cart و remove_from_cart لاحقًا بنفس النمط مع حماية قوية