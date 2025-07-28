import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from config import GMAIL_USER, GMAIL_APP_PASSWORD
import random

def generate_otp(length=6):
    """Generate a random OTP code"""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def send_otp_email_gmail(to_email: str, otp_code: str):
    """Send OTP email using Gmail SMTP"""
    
    # Create a more professional HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Your OTP Code</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .otp-code {{ font-size: 32px; font-weight: bold; text-align: center; color: #007bff; padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔐 Your Verification Code</h2>
            </div>
            <p>Hello!</p>
            <p>You have requested a verification code for your Book Platform account.</p>
            <p>Please use the following code to complete your verification:</p>
            <div class="otp-code">{otp_code}</div>
            <p><strong>Important:</strong></p>
            <ul>
                <li>This code will expire in 5 minutes</li>
                <li>Do not share this code with anyone</li>
                <li>If you didn't request this code, please ignore this email</li>
            </ul>
            <div class="footer">
                <p>This email was sent from Book Platform</p>
                <p>If you have any questions, please contact our support team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version for email clients that don't support HTML
    text_content = f"""
    Your Verification Code
    
    أهلا بك!
    
     هذا  رمز التحقق لحسابك في منصة الكتب.
    
    رمز التحقق الخاص بك هو : {otp_code}
    
    ملاحظة:
    - هذا الرمز سينتهي في 5 دقائق
    - لا تشارك هذا الرمز مع أي شخص
    - إذا لم تطلب هذا الرمز، يرجى تجاهل هذه البريد الإلكتروني
    
    هذا البريد الإلكتروني تم إرساله من منصة الفكر
    """
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "🔐 رمز التحقق لحسابك في منصة الكتب"
    message["From"] = f"منصة الفكر <{GMAIL_USER}>"
    message["To"] = to_email
    
    # Attach both HTML and text versions
    text_part = MIMEText(text_content, "plain")
    html_part = MIMEText(html_content, "html")
    
    message.attach(text_part)
    message.attach(html_part)
    
    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, message.as_string())
            return True
    except Exception as e:
        print(f"Error sending email via Gmail SMTP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

def send_email_gmail(to_email: str, subject: str, text_content: str, html_content: str = None):
    """Send general email using Gmail SMTP"""
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"Book Platform <{GMAIL_USER}>"
    message["To"] = to_email
    
    # Attach text version
    text_part = MIMEText(text_content, "plain")
    message.attach(text_part)
    
    # Attach HTML version if provided
    if html_content:
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
    
    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, message.as_string())
            return True
    except Exception as e:
        print(f"Error sending email via Gmail SMTP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}") 