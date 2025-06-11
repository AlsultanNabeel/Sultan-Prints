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
    sender_email = current_app.config.get('MAIL_USERNAME')
    if not sender_email:
        current_app.logger.error("MAIL_USERNAME is not set in config. Cannot send email.")
        return False
    
    if not mail.init_app:
        current_app.logger.error("Flask-Mail is not initialized correctly.")
        return False

    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=body_html,
            sender=(sender_name, sender_email)
        )
        mail.send(msg)
        current_app.logger.info(f"Email sent successfully to {to_email} with subject '{subject}'.")
        return True
    except Exception as e:
        # Log the full error for debugging
        current_app.logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
        return False 