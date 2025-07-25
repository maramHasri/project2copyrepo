import requests
import json
from config import ELASTIC_EMAIL_API_KEY, ELASTIC_EMAIL_FROM, ELASTIC_EMAIL_URL

def send_otp_email_elastic(to_email: str, otp_code: str):
    """Send OTP email using Elastic Email API"""
    
    headers = {
        "Authorization": f"Bearer {ELASTIC_EMAIL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "Recipients": {
            "To": [to_email]
        },
        "Content": {
            "Subject": "Your OTP Code",
            "From": ELASTIC_EMAIL_FROM,
            "Text": f"Your one-time password is: {otp_code}"
        }
    }
    
    try:
        response = requests.post(
            ELASTIC_EMAIL_URL,
            headers=headers,
            json=payload
        )
        return response
    except Exception as e:
        print(f"Error sending email via Elastic Email: {e}")
        return None

def send_email_elastic(to_email: str, subject: str, text_content: str, html_content: str = None):
    """Send general email using Elastic Email API"""
    
    headers = {
        "Authorization": f"Bearer {ELASTIC_EMAIL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    content = {
        "Subject": subject,
        "From": ELASTIC_EMAIL_FROM,
        "Text": text_content
    }
    
    if html_content:
        content["Html"] = html_content
    
    payload = {
        "Recipients": {
            "To": [to_email]
        },
        "Content": content
    }
    
    try:
        response = requests.post(
            ELASTIC_EMAIL_URL,
            headers=headers,
            json=payload
        )
        return response
    except Exception as e:
        print(f"Error sending email via Elastic Email: {e}")
        return None 