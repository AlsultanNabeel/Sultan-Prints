from flask_mail import Mail, Message
from flask import current_app, render_template_string, request
from threading import Thread

mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipient, template, **kwargs):
    """Send email asynchronously"""
    msg = Message(subject,
                 sender=current_app.config['MAIL_DEFAULT_SENDER'],
                 recipients=[recipient])
    
    msg.html = render_template_string(template, **kwargs)
    
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()

def send_order_confirmation(order, user_email):
    """Send order confirmation email"""
    template = """
    <h2>شكراً لطلبك من متجرنا</h2>
    <p>رقم الطلب: {{ order.reference }}</p>
    <h3>تفاصيل الطلب:</h3>
    <ul>
    {% for item in order.order_items %}
        <li>{{ item.product_name }} - الكمية: {{ item.quantity }} - المقاس: {{ item.size|default('N/A') }} - اللون: {{ item.color|default('N/A') }} - السعر: {{ item.price }} جنيه</li>
    {% endfor %}
    </ul>
    <p>المبلغ الإجمالي: {{ order.total_amount }} جنيه</p>
    <p>طريقة الدفع: {{ order.payment_method }}</p>
    
    <h3>عنوان التوصيل:</h3>
    <p>{{ order.customer_name }}<br>
    {{ order.address }}<br>
    {{ order.customer_phone }}</p>
    
    <p>سنقوم بإخطارك عند شحن طلبك.</p>
    """
    
    send_email(
        'تأكيد الطلب - متجر التيشيرتات',
        user_email,
        template,
        order=order
    )

def send_shipping_notification(order, user_email):
    """Send shipping notification email"""
    template = """
    <h2>تم شحن طلبك!</h2>
    <p>رقم الطلب: {{ order.reference }}</p>
    <p>تم شحن طلبك وسيصل قريباً.</p>
    <p>يمكنك تتبع طلبك من خلال حسابك في الموقع.</p>
    """
    
    send_email(
        'تم شحن طلبك - متجر التيشيرتات',
        user_email,
        template,
        order=order
    )

def send_password_reset(user_email, reset_token):
    """Send password reset email"""
    template = """
    <h2>إعادة تعيين كلمة المرور</h2>
    <p>لقد طلبت إعادة تعيين كلمة المرور الخاصة بك.</p>
    <p>اضغط على الرابط التالي لإعادة تعيين كلمة المرور:</p>
    <p><a href="{{ reset_url }}">إعادة تعيين كلمة المرور</a></p>
    <p>إذا لم تطلب إعادة تعيين كلمة المرور، يمكنك تجاهل هذا البريد.</p>
    """
    
    reset_url = f"{request.url_root}reset_password/{reset_token}"
    
    send_email(
        'إعادة تعيين كلمة المرور - متجر التيشيرتات',
        user_email,
        template,
        reset_url=reset_url
    ) 