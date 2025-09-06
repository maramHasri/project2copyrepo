import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from OTPconfig import GMAIL_USER, GMAIL_APP_PASSWORD
import random

def generate_otp(length=6):
#generate otp    
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def send_otp_email_gmail(to_email: str, otp_code: str):
    #Send otp email 
    
    #  professional HTML email template
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
        # Connect to  server
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

def send_password_reset_email(to_email: str, reset_token: str):
    """Send password reset email with reset token"""
    
    # Simple HTML email template for password reset
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Password Reset Request</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .token-code {{ font-size: 24px; font-weight: bold; text-align: center; color: #007bff; padding: 20px; background-color: #f8f9fa; border-radius: 5px; margin: 20px 0; word-break: break-all; border: 2px solid #007bff; }}
            .instructions {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🔐 Password Reset Request</h2>
            </div>
            <p>Hello!</p>
            <p>You have requested to reset your password for your Book Platform account.</p>
            <p><strong>Your password reset token is:</strong></p>
            <div class="token-code">{reset_token}</div>
            
            <div class="instructions">
                <p><strong>How to reset your password:</strong></p>
                <ol>
                    <li>Copy the reset token above</li>
                    <li>Go to your app and find the "Reset Password" option</li>
                    <li>Paste the token and enter your new password</li>
                    <li>Submit the form to complete the reset</li>
                </ol>
            </div>
            
            <p><strong>Important:</strong></p>
            <ul>
                <li>This token will expire in 5 days</li>
                <li>Do not share this token with anyone</li>
                <li>If you didn't request this reset, please ignore this email</li>
                <li>Your password will remain unchanged until you complete the reset process</li>
            </ul>
            <div class="footer">
                <p>This email was sent from Book Platform</p>
                <p>If you have any questions, please contact our support team</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    Password Reset Request
    
    Hello!
    
    You have requested to reset your password for your Book Platform account.
    
    Your password reset token is:
    
    {reset_token}
    
    How to reset your password:
    1. Copy the reset token above
    2. Go to your app and find the "Reset Password" option
    3. Paste the token and enter your new password
    4. Submit the form to complete the reset
    
    Important:
    - This token will expire in 5 days
    - Do not share this token with anyone
    - If you didn't request this reset, please ignore this email
    - Your password will remain unchanged until you complete the reset process
    
    This email was sent from Book Platform
    If you have any questions, please contact our support team
    """
    
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = "🔐 Password Reset Token - Book Platform"
    message["From"] = f"Book Platform <{GMAIL_USER}>"
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
        print(f"Error sending password reset email via Gmail SMTP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send password reset email: {str(e)}")