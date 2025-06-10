from app import db
from datetime import datetime

class Discount(db.Model):
    __tablename__ = 'discounts'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # percentage, fixed
    value = db.Column(db.Float, nullable=False)
    min_purchase = db.Column(db.Float, nullable=True)
    max_discount = db.Column(db.Float, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    usage_limit = db.Column(db.Integer, nullable=True)
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self, total_amount):
        """Check if discount is valid"""
        now = datetime.utcnow()
        
        # Check basic validity
        if not self.is_active:
            return False, "هذا الكود غير نشط"
        
        if now < self.start_date:
            return False, "لم يبدأ وقت هذا الكود بعد"
        
        if now > self.end_date:
            return False, "انتهت صلاحية هذا الكود"
        
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "تم استنفاد الحد الأقصى لاستخدام هذا الكود"
        
        # Check minimum purchase
        if self.min_purchase and total_amount < self.min_purchase:
            return False, f"الحد الأدنى للطلب {self.min_purchase} جنيه"
        
        return True, "الكود صالح"
    
    def calculate_discount(self, total_amount):
        """Calculate discount amount"""
        if self.type == 'percentage':
            discount = total_amount * (self.value / 100)
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:  # fixed
            discount = self.value
        
        return min(discount, total_amount)  # Don't exceed total amount

class DiscountManager:
    @staticmethod
    def validate_coupon(code, total_amount):
        """Validate a discount code and return the discount amount without applying it."""
        discount = Discount.query.filter_by(code=code.upper()).first()
        if not discount:
            return 0, "كود الخصم غير صالح"
        
        is_valid, message = discount.is_valid(total_amount)
        if not is_valid:
            return 0, message
        
        discount_amount = discount.calculate_discount(total_amount)
        
        return discount_amount, "تم التحقق من الكود بنجاح"

    @staticmethod
    def create_discount(code, type, value, start_date, end_date, **kwargs):
        """Create a new discount"""
        discount = Discount(
            code=code.upper(),
            type=type,
            value=value,
            start_date=start_date,
            end_date=end_date,
            min_purchase=kwargs.get('min_purchase'),
            max_discount=kwargs.get('max_discount'),
            usage_limit=kwargs.get('usage_limit')
        )
        db.session.add(discount)
        db.session.commit()
        return discount
    
    @staticmethod
    def apply_discount(code, total_amount):
        """Apply discount to order"""
        discount = Discount.query.filter_by(code=code.upper()).first()
        if not discount:
            return 0, "كود الخصم غير صالح"
        
        is_valid, message = discount.is_valid(total_amount)
        if not is_valid:
            return 0, message
        
        discount_amount = discount.calculate_discount(total_amount)
        
        # Update usage count
        discount.times_used += 1
        db.session.commit()
        
        return discount_amount, "تم تطبيق الخصم بنجاح"
    
    @staticmethod
    def get_active_discounts():
        """Get all active discounts"""
        now = datetime.utcnow()
        return Discount.query.filter(
            Discount.is_active == True,
            Discount.start_date <= now,
            Discount.end_date >= now
        ).all()
    
    @staticmethod
    def deactivate_discount(code):
        """Deactivate a discount"""
        discount = Discount.query.filter_by(code=code.upper()).first()
        if discount:
            discount.is_active = False
            db.session.commit()
            return True, "تم إلغاء تفعيل كود الخصم"
        return False, "كود الخصم غير موجود" 