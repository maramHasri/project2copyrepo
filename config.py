# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Gmail SMTP Configuration
GMAIL_USER = os.getenv("GMAIL_USER", "meesama89434@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "jvou ybak evxp frbm")

# Other configurations
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./book_platform.db")
