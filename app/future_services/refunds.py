from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message
import stripe
import enum
from app import db
from app.models import Order, User, Refund
from app.services import mail

class RefundManager:
    @staticmethod
    def request_refund(order_id, amount, reason, refund_method):
        """Request a refund for an order"""
        order = Order.query.get(order_id)
        if not order:
            return None, "الطلب غير موجود"
        
        # Validate refund amount
        if amount > order.total_amount:
            return None, "مبلغ الاسترداد لا يمكن أن يتجاوز قيمة الطلب"
        
        # Check if order already has a pending refund
        existing_refund = Refund.query.filter_by(
            order_id=order_id,
            status='pending'
        ).first()
        if existing_refund:
            return None, "يوجد طلب استرداد معلق بالفعل لهذا الطلب"
        
        # Create refund request
        refund = Refund(
            order_id=order_id,
            amount=amount,
            reason=reason,
            refund_method=refund_method
        )
        db.session.add(refund)
        db.session.commit()
        
        return refund, "تم تقديم طلب الاسترداد بنجاح"
    
    @staticmethod
    def process_refund(refund_id, admin_id, approve=True):
        """Process a refund request"""
        refund = Refund.query.get(refund_id)
        if not refund:
            return False, "طلب الاسترداد غير موجود"
        
        if refund.status != 'pending':
            return False, "لا يمكن معالجة هذا الطلب"
        
        if not approve:
            refund.status = 'rejected'
            refund.approved_by = admin_id
            db.session.commit()
            return True, "تم رفض طلب الاسترداد"
        
        try:
            if refund.refund_method == 'stripe':
                # Process Stripe refund
                stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
                stripe_refund = stripe.Refund.create(
                    payment_intent=refund.order.payment_intent_id,
                    amount=int(refund.amount * 100)  # Convert to cents
                )
                refund.stripe_refund_id = stripe_refund.id
            
            elif refund.refund_method == 'vodafone_cash':
                # Log Vodafone Cash refund for manual processing
                pass
            
            elif refund.refund_method == 'store_credit':
                # Add store credit to user's account
                refund.order.user.store_credit += refund.amount
            
            refund.status = 'completed'
            refund.approved_by = admin_id
            db.session.commit()
            
            return True, "تم معالجة الاسترداد بنجاح"
        
        except Exception as e:
            db.session.rollback()
            return False, f"حدث خطأ أثناء معالجة الاسترداد: {str(e)}"
    
    @staticmethod
    def get_refund_statistics():
        """Get refund statistics"""
        total_refunds = Refund.query.count()
        completed_refunds = Refund.query.filter_by(status='completed').count()
        total_amount = db.session.query(db.func.sum(Refund.amount)).filter_by(status='completed').scalar() or 0
        
        return {
            'total_refunds': total_refunds,
            'completed_refunds': completed_refunds,
            'total_amount': total_amount,
            'average_amount': total_amount / completed_refunds if completed_refunds > 0 else 0
        }
    
    @staticmethod
    def get_pending_refunds():
        """Get all pending refund requests"""
        return Refund.query.filter_by(status='pending').all()
    
    @staticmethod
    def get_refund_history(order_id=None, user_id=None):
        """Get refund history for an order or user"""
        query = Refund.query
        
        if order_id:
            query = query.filter_by(order_id=order_id)
        
        if user_id:
            query = query.join(Order).filter(Order.user_id == user_id)
        
        return query.order_by(Refund.created_at.desc()).all()
    
    @staticmethod
    def send_refund_confirmation(refund):
        """Send refund request confirmation email"""
        msg = Message(
            f'تأكيد طلب استرداد المبلغ #{refund.id}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[refund.order.user.email]
        )
        
        msg.html = f"""
        <h3>تم استلام طلب استرداد المبلغ الخاص بك</h3>
        <p>رقم الطلب: {refund.order.id}</p>
        <p>المبلغ: {refund.amount} ريال</p>
        <p>السبب: {refund.reason}</p>
        <p>الحالة: {refund.status}</p>
        <p>سنقوم بمراجعة طلبك وإبلاغك بالتحديثات.</p>
        """
        
        mail.send(msg)
    
    @staticmethod
    def send_refund_completed(refund):
        """Send refund completion email"""
        msg = Message(
            f'تم اكتمال استرداد المبلغ #{refund.id}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[refund.order.user.email]
        )
        
        msg.html = f"""
        <h3>تم اكتمال عملية استرداد المبلغ</h3>
        <p>رقم الطلب: {refund.order.id}</p>
        <p>المبلغ: {refund.amount} ريال</p>
        <p>سيظهر المبلغ في حسابك خلال 3-5 أيام عمل.</p>
        """
        
        mail.send(msg)
    
    @staticmethod
    def send_refund_failed(refund):
        """Send refund failure email"""
        msg = Message(
            f'فشل في استرداد المبلغ #{refund.id}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[refund.order.user.email]
        )
        
        msg.html = f"""
        <h3>عذراً، حدث خطأ أثناء معالجة طلب استرداد المبلغ</h3>
        <p>رقم الطلب: {refund.order.id}</p>
        <p>المبلغ: {refund.amount} ريال</p>
        <p>سيقوم فريق خدمة العملاء بالتواصل معك قريباً لحل المشكلة.</p>
        """
        
        mail.send(msg)
    
    @staticmethod
    def send_refund_cancelled(refund):
        """Send refund cancellation email"""
        msg = Message(
            f'تم إلغاء طلب استرداد المبلغ #{refund.id}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[refund.order.user.email]
        )
        
        msg.html = f"""
        <h3>تم إلغاء طلب استرداد المبلغ</h3>
        <p>رقم الطلب: {refund.order.id}</p>
        <p>المبلغ: {refund.amount} ريال</p>
        <p>السبب: {refund.reason}</p>
        <p>إذا كان لديك أي استفسارات، يرجى التواصل مع خدمة العملاء.</p>
        """
        
        mail.send(msg) 