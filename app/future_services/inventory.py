from datetime import datetime
from flask import current_app
from flask_mail import Message
from app.services import mail
import json
from app import db
from app.models import Product, Order, OrderItem

class InventoryManager:
    def __init__(self, low_stock_threshold=5):
        self.threshold = low_stock_threshold
    
    def update_stock(self, product_id, quantity_change):
        """Update product stock and check threshold"""
        product = Product.query.get(product_id)
        if not product:
            return False
        
        product.stock += quantity_change
        if product.stock < 0:
            return False
        
        if product.stock <= self.threshold:
            self.send_low_stock_alert(product)
        
        db.session.commit()
        return True
    
    def check_stock_availability(self, items):
        """Check if all items in order are available"""
        for item in items:
            product = Product.query.get(item['product_id'])
            if not product or product.stock < item['quantity']:
                return False
        return True
    
    def process_order(self, order_id):
        """Process order and update inventory"""
        order = Order.query.get(order_id)
        if not order:
            return False
        
        # Check stock availability for all items
        items = OrderItem.query.filter_by(order_id=order_id).all()
        for item in items:
            if not self.update_stock(item.product_id, -item.quantity):
                return False
        
        return True
    
    def send_low_stock_alert(self, product):
        """Send email alert for low stock"""
        msg = Message(
            'تنبيه: انخفاض المخزون',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['ADMIN_EMAIL']]
        )
        msg.html = f"""
        <h3>تنبيه انخفاض المخزون</h3>
        <p>المنتج: {product.name}</p>
        <p>الكمية المتبقية: {product.stock}</p>
        <p>الحد الأدنى: {self.threshold}</p>
        <a href="{current_app.config['BASE_URL']}/admin/products/{product.id}">
            عرض المنتج في لوحة التحكم
        </a>
        """
        mail.send(msg)

class InventoryAnalytics:
    @staticmethod
    def get_low_stock_products():
        """Get all products with low stock"""
        return Product.query.filter(Product.stock <= 5).all()
    
    @staticmethod
    def get_out_of_stock_products():
        """Get all out of stock products"""
        return Product.query.filter(Product.stock == 0).all()
    
    @staticmethod
    def get_stock_movement(product_id, days=30):
        """Get stock movement history for a product"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        movements = OrderItem.query.join(Order).filter(
            OrderItem.product_id == product_id,
            Order.created_at.between(start_date, end_date)
        ).all()
        
        return {
            'total_sold': sum(item.quantity for item in movements),
            'movements': movements
        }
    
    @staticmethod
    def get_popular_products(limit=10):
        """Get most popular products based on sales"""
        return db.session.query(
            Product,
            db.func.sum(OrderItem.quantity).label('total_sold')
        ).join(OrderItem).group_by(Product.id).order_by(
            db.desc('total_sold')
        ).limit(limit).all()

class StockPrediction:
    @staticmethod
    def predict_stock_needs(product_id, days=30):
        """Predict stock needs based on historical data"""
        analytics = InventoryAnalytics()
        movement = analytics.get_stock_movement(product_id, days)
        
        daily_average = movement['total_sold'] / days
        predicted_monthly_need = daily_average * 30
        
        return {
            'daily_average': round(daily_average, 2),
            'predicted_monthly_need': round(predicted_monthly_need, 2),
            'recommended_reorder': round(predicted_monthly_need * 1.2, 0)  # 20% buffer
        }
    
    @staticmethod
    def get_reorder_recommendations():
        """Get reorder recommendations for all products"""
        products = Product.query.all()
        recommendations = []
        
        for product in products:
            if product.stock <= 5:
                prediction = StockPrediction.predict_stock_needs(product.id)
                recommendations.append({
                    'product': product,
                    'current_stock': product.stock,
                    'recommended_order': prediction['recommended_reorder']
                })
        
        return recommendations