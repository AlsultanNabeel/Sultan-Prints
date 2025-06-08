import stripe
from flask import current_app
from datetime import datetime

class PaymentHandler:
    @staticmethod
    def initialize_stripe():
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    @staticmethod
    def create_payment_intent(amount, currency='usd'):
        """Create a payment intent for Stripe checkout"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                payment_method_types=['card'],
            )
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            return {'error': str(e)}
    
    @staticmethod
    def verify_payment(payment_intent_id):
        """Verify that a payment was successful"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent.status == 'succeeded'
        except stripe.error.StripeError:
            return False

class VodafonePayment:
    @staticmethod
    def generate_payment_reference():
        """Generate a unique reference number for Vodafone Cash payment"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"VC{timestamp}"
    
    @staticmethod
    def get_payment_instructions(amount, reference):
        """Get instructions for Vodafone Cash payment"""
        vodafone_number = current_app.config['VODAFONE_CASH_NUMBER']
        return {
            'number': vodafone_number,
            'amount': amount,
            'reference': reference,
            'instructions': [
                f"1. افتح تطبيق فودافون كاش",
                f"2. اختر 'تحويل أموال'",
                f"3. أدخل الرقم: {vodafone_number}",
                f"4. أدخل المبلغ: {amount} جنيه",
                f"5. أدخل رقم المرجع: {reference}",
                "6. أكد العملية وانتظر رسالة التأكيد"
            ]
        } 