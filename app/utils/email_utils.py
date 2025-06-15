import os
from mailerlite import Client
from flask import current_app
from flask_mail import Message
from app import mail

def send_email(to_email, subject, body_html, sender_name='Sultan Prints'):
    """
    Sends an email using the configured Flask-Mail instance.

    Args:
        to_email (str): The recipient's email address.
        subject (str): The subject of the email.
        body_html (str): The HTML content of the email.
        sender_name (str): The name of the sender.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    # التحقق من صحة المدخلات
    if not to_email or not isinstance(to_email, str) or '@' not in to_email:
        current_app.logger.error(f"Invalid email address: {to_email}")
        return False
    
    if not subject or not body_html:
        current_app.logger.error("Email subject or body is empty")
        return False
    
    sender_email = current_app.config.get('MAIL_USERNAME')
    if not sender_email:
        current_app.logger.error("MAIL_USERNAME is not set in config. Cannot send email.")
        return False

    try:
        # إضافة توقيع للبريد الإلكتروني
        email_signature = """
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;">
            <p>مع تحيات فريق سلطان برينتس</p>
            <p><a href="https://sultanprints.com">sultanprints.com</a></p>
        </div>
        """
        
        # إضافة رسالة عدم إعادة الإرسال للأمان
        security_notice = """
        <div style="font-size: 11px; color: #999; margin-top: 20px;">
            <p>هذه رسالة آلية، يرجى عدم الرد عليها مباشرةً. إذا كان لديك أي استفسار، يرجى التواصل معنا من خلال نموذج الاتصال على موقعنا.</p>
        </div>
        """
        
        complete_html = f"{body_html}{email_signature}{security_notice}"
        
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=complete_html,
            sender=(sender_name, sender_email)
        )
        mail.send(msg)
        current_app.logger.info(f"Email sent successfully to {to_email} with subject '{subject}'.")
        return True
    except Exception as e:
        # Log the full error for debugging
        current_app.logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
        return False 