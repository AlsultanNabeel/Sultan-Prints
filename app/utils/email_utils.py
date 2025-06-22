import os
from mailerlite import MailerLiteApi
from flask import current_app, render_template

def send_email_mailerlite(recipient_email, subject, template, **kwargs):
    """
    Custom function to send email using MailerLite.
    """
    api_key = current_app.config.get('MAILERLITE_API_KEY')
    if not api_key:
        current_app.logger.error("MAILERLITE_API_KEY is not set.")
        return

    # Initialize MailerLite API
    client = MailerLiteApi(api_key)

    try:
        html_content = render_template(template + '.html', **kwargs)
        text_content = render_template(template + '.txt', **kwargs)

        # Email data
        email_data = {
            "to": [{
                "email": recipient_email,
            }],
            "from": {
                "email": current_app.config.get('MAIL_DEFAULT_SENDER', 'no-reply@yourdomain.com'),
                "name": "Sultan Prints"
            },
            "subject": subject,
            "html": html_content,
            "text": text_content
        }

        # Send email via MailerLite API
        client.emails.create(email_data)
        current_app.logger.info(f"Email sent to {recipient_email} via MailerLite.")

    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipient_email} via MailerLite: {e}")