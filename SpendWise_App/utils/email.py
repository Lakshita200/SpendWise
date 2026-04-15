import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from ..config import settings


def generate_verification_code(length: int = 6) -> str:
    """Generate a random 6-digit verification code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_reset_code(length: int = 32) -> str:
    """Generate a random alphanumeric reset token"""
    return secrets.token_urlsafe(length)


def send_verification_email(email: str, verification_code: str) -> bool:
    """Send verification code to user's email"""
    try:
        subject = "Verify Your SpendWise Email"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #7c9cbf; margin-bottom: 20px;">Welcome to SpendWise!</h2>
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        Thank you for registering. Please verify your email address to get started.
                    </p>
                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 6px; text-align: center; margin-bottom: 20px;">
                        <p style="color: #666; margin-bottom: 10px; font-size: 14px;">Your verification code is:</p>
                        <p style="color: #7c9cbf; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 0;">
                            {verification_code}
                        </p>
                    </div>
                    <p style="color: #666; font-size: 14px; margin-bottom: 10px;">
                        This code will expire in <strong>10 minutes</strong>.
                    </p>
                    <p style="color: #999; font-size: 12px;">
                        If you didn't register for SpendWise, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(email, subject, html_content)
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def send_password_reset_email(email: str, reset_code: str) -> bool:
    """Send password reset link to user's email"""
    try:
        subject = "Reset Your SpendWise Password"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #7c9cbf; margin-bottom: 20px;">Password Reset Request</h2>
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        We received a request to reset your password. Use the code below to reset it.
                    </p>
                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 6px; text-align: center; margin-bottom: 20px;">
                        <p style="color: #666; margin-bottom: 10px; font-size: 14px;">Your reset code is:</p>
                        <p style="color: #7c9cbf; font-size: 18px; font-weight: bold; word-break: break-all; margin: 0; font-family: monospace;">
                            {reset_code}
                        </p>
                    </div>
                    <p style="color: #666; font-size: 14px; margin-bottom: 10px;">
                        This code will expire in <strong>1 hour</strong>.
                    </p>
                    <p style="color: #999; font-size: 12px;">
                        If you didn't request a password reset, please ignore this email and your password will remain unchanged.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return send_email(email, subject, html_content)
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Internal function to send email via SMTP"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
        msg["To"] = to_email
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, "html"))
        
        # Connect to SMTP server and send
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def get_verification_code_expiry() -> datetime:
    """Get expiry time for verification code (10 minutes from now)"""
    return datetime.now(timezone.utc) + timedelta(minutes=10)


def get_reset_token_expiry() -> datetime:
    """Get expiry time for reset token (1 hour from now)"""
    return datetime.now(timezone.utc) + timedelta(hours=1)
