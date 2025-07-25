# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Elastic Email Configuration
ELASTIC_EMAIL_API_KEY = os.getenv("ELASTIC_EMAIL_API_KEY", "CD0ABCFF3149695B1DD566CC69FC428FE3C0E5F8D59E04CAAB3FA63A268A69197DB91E1DDAFB7EE3C64B308EED201A1B")
ELASTIC_EMAIL_FROM = os.getenv("ELASTIC_EMAIL_FROM", "your_verified_sender@yourdomain.com")
ELASTIC_EMAIL_URL = "https://api.elasticemail.com/v4/emails"

# Other configurations can be added here
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./book_platform.db")
