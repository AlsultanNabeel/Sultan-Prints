import json
from app.extensions import db
from datetime import datetime, timedelta
import random
import string
import enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

class User(UserMixin, db.Model):
    """نموذج المستخدم"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    phone = db.Column(db.String(32), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy='dynamic')
    # The backref in SupportTicket needs to be unique. 'user' is already used by orders.
    # I'll let the existing 'support_tickets' backref in SupportTicket model handle this.

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class OrderStatus(db.Model):
    __tablename__ = 'order_status'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<OrderStatus {self.id} for Order {self.order_id} - {self.status}>'

class Product(db.Model):
    """نموذج المنتج"""
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    _sizes = db.Column('sizes', db.String(255))
    _colors = db.Column('colors', db.String(255))
    features = db.Column(db.Text, nullable=True)
    material = db.Column(db.String(120))
    featured = db.Column(db.Boolean, default=False)
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(120))
    is_trending = db.Column(db.Boolean, default=False)
    is_palestine = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(32), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    @property
    def sizes(self):
        if self._sizes:
            try:
                return json.loads(self._sizes)
            except json.JSONDecodeError:
                return []
        return []

    @sizes.setter
    def sizes(self, value):
        if isinstance(value, list):
            self._sizes = json.dumps(value)
        elif isinstance(value, str):
            # If it's already a JSON string, just store it
            self._sizes = value

    @property
    def colors(self):
        if self._colors:
            return [color.strip() for color in self._colors.split(',') if color.strip()]
        return []

    @colors.setter
    def colors(self, value):
        if isinstance(value, list):
            self._colors = ','.join(value)
        elif isinstance(value, str):
            self._colors = value

class Governorate(db.Model):
    """نموذج المحافظات"""
    __tablename__ = 'governorates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    delivery_fee = db.Column(db.Float, nullable=False, default=0.0)
    orders = db.relationship('Order', backref='governorate_info', lazy='dynamic') # Renamed backref

    def __repr__(self):
        return f'<Governorate {self.name}>'

class Order(db.Model):
    """نموذج الطلب"""
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(16), unique=True, nullable=False, default=lambda: ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)))
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(32), nullable=False)
    address = db.Column(db.Text, nullable=False) # Detailed address (street, building, etc.)
    governorate_id = db.Column(db.Integer, db.ForeignKey('governorates.id'), nullable=True)
    delivery_fee = db.Column(db.Float, nullable=False, default=0.0)
    payment_method = db.Column(db.String(32), nullable=False)
    vodafone_receipt = db.Column(db.String(255), nullable=True)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    discount_amount = db.Column(db.Float, nullable=False, default=0)  # مبلغ الخصم
    final_amount = db.Column(db.Float, nullable=False, default=0)  # المبلغ النهائي بعد الخصم
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promocodes.id'), nullable=True)
    status = db.Column(db.String(32), default='pending')
    archived = db.Column(db.Boolean, default=False, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade="all, delete-orphan")
    status_history = db.relationship('OrderStatus', backref='order', lazy='dynamic', order_by='OrderStatus.timestamp.desc()', cascade="all, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f'<Order {self.reference}>'

    def calculate_final_amount(self):
        """حساب المبلغ النهائي بعد تطبيق الخصم"""
        self.final_amount = self.total_amount - self.discount_amount
        return self.final_amount

class OrderItem(db.Model):
    """عنصر في الطلب"""
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(16), nullable=False)
    size = db.Column(db.String(8), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    custom_design_path = db.Column(db.String(255), nullable=True)

class Banner(db.Model):
    """شريط الإعلانات"""
    __tablename__ = 'banners'
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(255), nullable=False)
    link_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Design(db.Model):
    """نموذج التصميم"""
    __tablename__ = 'designs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, default=0.0)
    is_default = db.Column(db.Boolean, default=True)  # تصاميم افتراضية أم مخصصة
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Contact(db.Model):
    """نموذج رسائل التواصل"""
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Cart(db.Model):
    """سلة التسوق"""
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade="all, delete-orphan")

class CartItem(db.Model):
    """عنصر في سلة التسوق"""
    __tablename__ = 'cart_item'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    design_id = db.Column(db.Integer, db.ForeignKey('designs.id'), nullable=True)
    custom_design_path = db.Column(db.String(255), nullable=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    size = db.Column(db.String(8), nullable=True)
    color = db.Column(db.String(16), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product')
    design = db.relationship('Design')

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='open')  # open, in_progress, closed
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    responses = db.relationship('TicketResponse', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    user = db.relationship('User', backref=db.backref('support_tickets', lazy=True))

class TicketResponse(db.Model):
    __tablename__ = 'ticket_responses'
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    responder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responder = db.relationship('User', backref='ticket_responses')

class RefundStatus(enum.Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class RefundReason(enum.Enum):
    RETURN = 'return'
    DAMAGED = 'damaged'
    NOT_RECEIVED = 'not_received'
    WRONG_ITEM = 'wrong_item'
    OTHER = 'other'

class Refund(db.Model):
    __tablename__ = 'refunds'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    refund_method = db.Column(db.String(50), nullable=False)
    stripe_refund_id = db.Column(db.String(100), nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order = db.relationship('Order', backref='refunds')
    approver = db.relationship('User', backref='approved_refunds')

class Setting(db.Model):
    """نموذج الإعدادات العامة للموقع"""
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Setting {self.key}>'

class Page(db.Model):
    """نموذج الصفحات القابلة للتعديل"""
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), unique=True, nullable=False) # e.g., 'about-us', 'contact'
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    meta_title = db.Column(db.String(255), nullable=True)
    meta_description = db.Column(db.String(500), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Page {self.title}>'

class Announcement(db.Model):
    """نموذج الإعلانات في الشريط العلوي"""
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Announcement {self.id}: {self.text[:30]}>'

class FAQ(db.Model):
    """نموذج الأسئلة الشائعة"""
    __tablename__ = 'faqs'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<FAQ {self.id}: {self.question[:50]}>'

class PromoCode(db.Model):
    """نموذج أكواد الخصم"""
    __tablename__ = 'promocodes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    discount_percentage = db.Column(db.Float, nullable=False)
    max_uses = db.Column(db.Integer, nullable=True)
    uses_count = db.Column(db.Integer, default=0)
    expiration_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    orders = db.relationship('Order', backref='promo_code', lazy='dynamic')

    def __repr__(self):
        return f'<PromoCode {self.code}>'

    def is_valid(self):
        """التحقق من صلاحية الكود"""
        if not self.is_active:
            return False
        if self.expiration_date < datetime.utcnow():
            return False
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        return True

    def apply_discount(self, total_amount):
        """تطبيق الخصم على المبلغ الإجمالي"""
        if not self.is_valid():
            return total_amount
        discount = total_amount * (self.discount_percentage / 100)
        return total_amount - discount

# Define the association table for the many-to-many relationship
# between Order and Product
order_product = db.Table('order_product',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
)

class CustomDesign(db.Model):
    """نموذج التصميم المخصص"""
    __tablename__ = 'custom_designs'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=True)
    customer_email = db.Column(db.String(120), nullable=True)
    customer_phone = db.Column(db.String(32), nullable=True)
    address = db.Column(db.Text, nullable=True)
    governorate_id = db.Column(db.Integer, db.ForeignKey('governorates.id'), nullable=True)
    design_file = db.Column(db.String(255), nullable=False)
    design_description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='pending')
    archived = db.Column(db.Boolean, default=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    governorate = db.relationship('Governorate', backref='custom_designs')
    order = db.relationship('Order', backref='custom_designs')