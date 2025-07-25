import os
import requests
from dotenv import load_dotenv

load_dotenv()

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_SENDER = os.getenv("MAILGUN_SENDER")

def send_otp_email(to_email: str, otp_code: str):
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"Dar Al Nashr <{MAILGUN_SENDER}>",
            "to": [to_email],
            "subject": "Your OTP Code",
            "text": f"Your one-time password is: {otp_code}"
        }
    )
    return response 