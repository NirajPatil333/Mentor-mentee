"""
Email dispatch service for account verification and password reset notifications.
Supports standard SMTP with TLS, with graceful fallback in development.
Never logs raw tokens or credentials in production logs.
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
    """
    Sends an email using configured SMTP settings.
    Returns True if successfully sent via SMTP, False on error or if SMTP is unconfigured.
    Never exposes sensitive credentials or raw tokens in logs.
    """
    if not Config.MAIL_SERVER or not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        logger.warning(
            f"SMTP is not configured in backend/.env (MAIL_SERVER, MAIL_USERNAME, or MAIL_PASSWORD missing). "
            f"Cannot send real email to '{to_email}'."
        )
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = Config.MAIL_DEFAULT_SENDER
        msg['To'] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=10) as server:
            if Config.MAIL_USE_TLS:
                server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email successfully delivered to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {type(e).__name__}")
        return False


def send_verification_email(to_email: str, recipient_name: str, raw_token: str) -> bool:
    """
    Sends account verification email with an expiring verification link.
    """
    verify_url = f"{Config.FRONTEND_URL}/verify-email?token={raw_token}"
    subject = "Verify Your Account - Mentor-Mentee Platform"
    
    text_content = (
        f"Hello {recipient_name},\n\n"
        f"Thank you for registering. Please verify your email address by opening the following link:\n"
        f"{verify_url}\n\n"
        f"This link is valid for 24 hours.\n\n"
        f"If you did not create this account, please ignore this email."
    )

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb;">Welcome to Mentor-Mentee Platform</h2>
        <p>Hello <strong>{recipient_name}</strong>,</p>
        <p>Thank you for signing up. Please verify your email address to activate your account:</p>
        <div style="margin: 24px 0;">
          <a href="{verify_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
            Verify Email Address
          </a>
        </div>
        <p style="font-size: 13px; color: #64748b;">Or copy and paste this link into your browser:<br/>
          <a href="{verify_url}" style="color: #2563eb;">{verify_url}</a>
        </p>
        <p style="font-size: 12px; color: #94a3b8; margin-top: 24px;">This verification link will expire in 24 hours. If you did not create an account, no further action is required.</p>
      </body>
    </html>
    """
    return send_email(to_email, subject, html_content, text_content)


def send_password_reset_email(to_email: str, recipient_name: str, raw_token: str) -> bool:
    """
    Sends password reset email with a single-use expiring reset link.
    """
    reset_url = f"{Config.FRONTEND_URL}/reset-password?token={raw_token}"
    subject = "Password Reset Request - Mentor-Mentee Platform"

    text_content = (
        f"Hello {recipient_name},\n\n"
        f"We received a request to reset your password. Click the link below to set a new password:\n"
        f"{reset_url}\n\n"
        f"This link is valid for 15 minutes and can only be used once.\n\n"
        f"If you did not request a password reset, you can safely ignore this email."
    )

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2563eb;">Password Reset Request</h2>
        <p>Hello <strong>{recipient_name}</strong>,</p>
        <p>We received a request to reset the password for your Mentor-Mentee Platform account.</p>
        <div style="margin: 24px 0;">
          <a href="{reset_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
            Reset Password
          </a>
        </div>
        <p style="font-size: 13px; color: #64748b;">Or copy and paste this link into your browser:<br/>
          <a href="{reset_url}" style="color: #2563eb;">{reset_url}</a>
        </p>
        <p style="font-size: 12px; color: #94a3b8; margin-top: 24px;">This reset link will expire in 15 minutes and can only be used once. If you did not request this change, please ignore this email.</p>
      </body>
    </html>
    """
    return send_email(to_email, subject, html_content, text_content)
