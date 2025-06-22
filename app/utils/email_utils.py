import os
from mailersend import emails
from flask import current_app, render_template

def send_email_mailerlite(recipient_email, subject, template, **kwargs):
    """
    Custom function to send email using MailerSend for transactional emails.
    """
    api_key = current_app.config.get('MAILERSEND_API_KEY')
    if not api_key:
        current_app.logger.error("MAILERSEND_API_KEY is not set.")
        return

    # Initialize MailerSend client
    mailer = emails.NewEmail(api_key)

    # Define an empty dict to populate with mail values
    mail_body = {}

    try:
        html_content = render_template(template + '.html', **kwargs)
        text_content = render_template(template + '.txt', **kwargs)

        mail_from = {
            "email": current_app.config.get('MAIL_DEFAULT_SENDER', 'no-reply@yourdomain.com'),
            "name": "Sultan Prints"
        }

        recipients = [
            {
                "email": recipient_email,
            }
        ]

        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)
        mailer.set_subject(subject, mail_body)
        mailer.set_html_content(html_content, mail_body)
        mailer.set_plaintext_content(text_content, mail_body)

        # Send email via MailerSend API
        mailer.send(mail_body)
        current_app.logger.info(f"Email sent to {recipient_email} via MailerSend.")

    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipient_email} via MailerSend: {e}")

# Note: The function name "send_email_mailerlite" is kept to avoid having to refactor 
# every single function call across the application at this stage.
# It now sends via MailerSend.