import random
import string
import smtplib
from email.mime.text import MIMEText

def is_valid_email(email):
    """Check if email is from allowed domains"""
    return email.endswith("@rit.edu") or email.endswith("@g.rit.edu")

def generate_verification_code(length=6):
    """Generate a random numeric verification code"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(to_email, code):
    """Send verification email with code"""
    from_email = "noreply@unifamily.com"
    subject = "Unifamily Email Verification"
    body = f"Your verification code is: {code}"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    
    try:
        with smtplib.SMTP('localhost', 1025) as server:
            server.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False