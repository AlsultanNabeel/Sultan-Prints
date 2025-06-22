from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from app.models import Product, Order, OrderItem, Cart, CartItem, Design, Governorate, PromoCode # Added PromoCode
from app.extensions import db, csrf # For db.session and csrf
from app.forms import CheckoutForm # For CheckoutForm
import uuid, os, json
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from datetime import datetime
from app.utils import get_or_create_cart, calculate_cart_total, save_image
from app.utils.email_utils import send_email
from flask import current_app # Add this import for logging
from flask_login import login_required

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

def generate_order_number():
    """توليد رقم طلب فريد"""
    import random
    import string
    # توليد رقم طلب من 8 أرقام
    order_number = ''.join(random.choices(string.digits, k=8))
    # التحقق من عدم تكرار الرقم
    while Order.query.filter_by(reference=order_number).first():
        order_number = ''.join(random.choices(string.digits, k=8))
    return order_number

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
    """إنشاء طلب جديد"""
    try:
        cart = get_or_create_cart()
        if not cart or not cart.items:
            flash('سلة المشتريات فارغة', 'warning')
            return redirect(url_for('cart.cart'))
            
        form = CheckoutForm()
        
        # تحميل قائمة المحافظات
        governorates = Governorate.query.order_by(Governorate.name.asc()).all()
        form.governorate_id.choices = [('', 'اختر المحافظة')] + [(g.id, g.name) for g in governorates]
        
        if form.validate_on_submit():
            
            receipt_path = None
            if form.payment_method.data == 'bank_transfer' and form.receipt.data:
                try:
                    receipt_path = save_image(form.receipt.data, folder='receipts', is_public=False)
                    if not receipt_path:
                        flash('حدث خطأ أثناء رفع الإيصال، يرجى المحاولة مرة أخرى.', 'danger')
                        return render_template('cart/checkout.html', form=form, cart_total=calculate_cart_total(), governorates=governorates)
                except Exception as e:
                    current_app.logger.error(f"Receipt upload failed: {e}")
                    flash('حدث خطأ فادح أثناء معالجة الإيصال.', 'danger')
                    return render_template('cart/checkout.html', form=form, cart_total=calculate_cart_total(), governorates=governorates)

            # حساب المجموع الكلي للمنتجات
            products_total = sum(item.product.price * item.quantity for item in cart.items)
            
            # حساب رسوم التوصيل
            governorate = Governorate.query.get(form.governorate_id.data)
            delivery_fee = governorate.delivery_fee if governorate else 0
            
            # حساب الخصم إذا كان هناك كود خصم
            discount_amount = 0
            promo_code_id = None
            if 'promo_code' in session:
                promo_data = session['promo_code']
                discount_amount = promo_data['discount_amount']
                promo_code_id = promo_data['id']
            
            # حساب إجمالي الطلب
            subtotal = products_total + delivery_fee
            final_amount = subtotal - discount_amount
            
            # إنشاء الطلب
            order = Order(
                reference=generate_order_number(),
                customer_name=form.name.data,
                customer_phone=form.phone.data,
                customer_email=form.email.data,
                governorate_id=form.governorate_id.data,
                address=form.address.data,
                delivery_fee=delivery_fee,
                payment_method=form.payment_method.data,
                payment_receipt_path=receipt_path,
                total_amount=subtotal,
                discount_amount=discount_amount,
                final_amount=final_amount,
                promo_code_id=promo_code_id,
                status='pending'
            )
            
            try:
                db.session.add(order)
                db.session.commit()
                
                # إضافة المنتجات للطلب
                for item in cart.items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item.product_id,
                        product_name=item.product.name,  # إضافة اسم المنتج
                        quantity=item.quantity,
                        price=item.product.price,
                        size=item.size,
                        color=item.color,
                        custom_design_path=item.custom_design_path  # إضافة مسار التصميم المخصص
                    )
                    db.session.add(order_item)
                
                # زيادة عدد مرات استخدام كود الخصم
                if promo_code_id:
                    promo_code = PromoCode.query.get(promo_code_id)
                    if promo_code:
                        promo_code.uses_count += 1
                
                db.session.commit()
                
                # تفريغ السلة
                for item in cart.items:
                    db.session.delete(item)
                db.session.commit()
                
                # إزالة كود الخصم من الجلسة
                session.pop('promo_code', None)
                
                # إعادة تعيين عدد العناصر في الجلسة
                session['cart_count'] = 0
                
                flash('تم إنشاء الطلب بنجاح!', 'success')
                return redirect(url_for('cart.order_confirmation', order_number=order.reference))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error saving order: {str(e)}", exc_info=True)
                flash('حدث خطأ أثناء حفظ الطلب', 'error')
                return render_template('cart/checkout.html', form=form), 500

        # حساب المجموع الكلي للمنتجات
        products_total = sum(item.product.price * item.quantity for item in cart.items)
        
        return render_template('cart/checkout.html',
                            form=form,
                            cart_items=cart.items,
                            products_total=products_total or 0)  # إضافة قيمة افتراضية 0
                            
    except Exception as e:
        current_app.logger.error(f"Unexpected error in checkout: {str(e)}", exc_info=True)
        flash('حدث خطأ أثناء تحميل صفحة الدفع', 'error')
        return redirect(url_for('cart.cart'))

@cart_bp.route('/order_confirmation/<order_number>')
def order_confirmation(order_number):
    order = Order.query.filter_by(reference=order_number).first_or_404()
    return render_template('cart/order_confirmation.html', order=order)

@cart_bp.route('/get_delivery_fee/<int:governorate_id>')
def get_delivery_fee(governorate_id):
    governorate = Governorate.query.get(governorate_id)
    if governorate:
        return jsonify({
            'success': True,
            'delivery_fee': governorate.delivery_fee, 
            'name': governorate.name
        })
    return jsonify({
        'success': False,
        'error': 'Governorate not found'
    }), 404

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

@cart_bp.route('/apply-promocode', methods=['POST'])
def apply_promocode():
    """تطبيق كود الخصم على السلة"""
    code = request.form.get('code', '').strip().upper()
    if not code:
        return jsonify({
            'success': False,
            'message': 'يرجى إدخال كود الخصم'
        })

    promo_code = PromoCode.query.filter_by(code=code).first()
    if not promo_code:
        return jsonify({
            'success': False,
            'message': 'كود الخصم غير صحيح'
        })

    if not promo_code.is_valid():
        if not promo_code.is_active:
            message = 'كود الخصم غير نشط'
        elif promo_code.expiration_date < datetime.utcnow():
            message = 'كود الخصم منتهي الصلاحية'
        elif promo_code.max_uses and promo_code.uses_count >= promo_code.max_uses:
            message = 'تم استنفاد الحد الأقصى لاستخدام هذا الكود'
        else:
            message = 'كود الخصم غير صالح'
        
        return jsonify({
            'success': False,
            'message': message
        })

    # حساب إجمالي السلة
    cart = get_or_create_cart()
    total_amount = sum(item.product.price * item.quantity for item in cart.items)
    
    # تطبيق الخصم
    discount_amount = total_amount * (promo_code.discount_percentage / 100)
    final_amount = total_amount - discount_amount

    # تخزين معلومات الكود في الجلسة
    session['promo_code'] = {
        'id': promo_code.id,
        'code': promo_code.code,
        'discount_percentage': promo_code.discount_percentage,
        'discount_amount': discount_amount
    }

    return jsonify({
        'success': True,
        'message': 'تم تطبيق كود الخصم بنجاح',
        'data': {
            'original_amount': total_amount,
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'discount_percentage': promo_code.discount_percentage
        }
    })

@cart_bp.route('/remove-promocode', methods=['POST'])
def remove_promocode():
    """إزالة كود الخصم من السلة"""
    session.pop('promo_code', None)
    cart = get_or_create_cart()
    total_amount = sum(item.product.price * item.quantity for item in cart.items)
    
    return jsonify({
        'success': True,
        'message': 'تم إزالة كود الخصم',
        'data': {
            'original_amount': total_amount,
            'final_amount': total_amount
        }
    })