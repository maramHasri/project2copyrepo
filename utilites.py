import random
import string
from email.message import EmailMessage
import aiosmtplib

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

async def send_otp_email(receiver_email: str, otp_code: str):
    message = EmailMessage()
    message["From"] = "your_email@gmail.com"
    message["To"] = receiver_email
    message["Subject"] = "Your OTP Code"
    message.set_content(f"Your OTP code is: {otp_code}")

    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=587,
        start_tls=True,
        username="your_email@gmail.com",
        password="your_email_password"
    )
