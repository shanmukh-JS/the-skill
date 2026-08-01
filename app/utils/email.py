import smtplib
from email.message import EmailMessage
from flask import current_app

def send_password_reset_email(user_email, reset_url):
    """
    Sends transactional password reset email via SMTP if configured in environment settings.
    Gracefully logs link if SMTP credentials are omitted.
    """
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_port = current_app.config.get('MAIL_PORT', 587)
    mail_user = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_user or 'noreply@skillexchange.org')
    use_tls = current_app.config.get('MAIL_USE_TLS', True)

    msg = EmailMessage()
    msg['Subject'] = 'Skill Exchange - Password Reset Request'
    msg['From'] = mail_sender
    msg['To'] = user_email
    
    body = f"""Hello,

We received a request to reset your password on the Skill Exchange Platform.

Please click the following link to reset your password (valid for 1 hour):
{reset_url}

If you did not request a password reset, please ignore this message.

Best regards,
The Skill Exchange Team
"""
    msg.set_content(body)

    if mail_server and mail_user and mail_password:
        try:
            with smtplib.SMTP(mail_server, int(mail_port), timeout=10) as server:
                if use_tls:
                    server.starttls()
                server.login(mail_user, mail_password)
                server.send_message(msg)
            current_app.logger.info(f"Password reset email sent to {user_email}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email via SMTP: {str(e)}")
            return False
    else:
        current_app.logger.info(f"[RESET LINK LOG] Password reset URL for {user_email}: {reset_url}")
        return True
