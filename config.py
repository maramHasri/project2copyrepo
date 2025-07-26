# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Elastic Email Configuration
ELASTIC_EMAIL_API_KEY = os.getenv("ELASTIC_EMAIL_API_KEY", "")
ELASTIC_EMAIL_FROM = os.getenv("ELASTIC_EMAIL_FROM", "your_verified_sender@yourdomain.com")
ELASTIC_EMAIL_URL = "https://api.elasticemail.com/v4/emails"

# Other configurations
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./book_platform.db")
