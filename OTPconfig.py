import os
from dotenv import load_dotenv

load_dotenv()

# Gmail  Config
GMAIL_USER = os.getenv("GMAIL_USER", "meesama89434@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "jvou ybak evxp frbm")


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./book_platform.db")
