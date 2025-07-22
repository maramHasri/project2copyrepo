"""
Configuration file for the Book Platform
Set your ElasticEmail SMTP credentials and other settings here
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# ElasticEmail SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.elasticemail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "meesama89434@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "39D39145216E1880624E303C3950403A6AF6")
FROM_EMAIL = os.getenv("FROM_EMAIL", "meesama89434@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "Book Platform")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./book_platform.db")

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "N93qNdu1uEX7oKM3ZQnHdV02TIuRt4umLG07eV4JhzI")

# Email Configuration Status
def check_email_config():
    """Check if email configuration is properly set up"""
    if SMTP_PASSWORD == "your_elasticemail_password_here":
        return False, "ElasticEmail password not configured"
    return True, "Email configuration ready"

if __name__ == "__main__":
    print("📧 Email Configuration Check")
    print("=" * 40)
    
    is_configured, message = check_email_config()
    
    if is_configured:
        print("✅ " + message)
        print(f"📧 SMTP Server: {SMTP_SERVER}")
        print(f"📧 SMTP Port: {SMTP_PORT}")
        print(f"📧 Username: {SMTP_USERNAME}")
        print(f"📧 From Email: {FROM_EMAIL}")
        print(f"📧 From Name: {FROM_NAME}")
    else:
        print("❌ " + message)
        print("\n🔧 To fix this:")
        print("1. Create a .env file with:")
        print("   SMTP_SERVER=smtp.elasticemail.com")
        print("   SMTP_PORT=2525")
        print("   SMTP_USERNAME=meesama89434@gmail.com")
        print("   SMTP_PASSWORD=your_actual_password")
        print("   FROM_EMAIL=meesama89434@gmail.com")
        print("   FROM_NAME=Book Platform")
        print("\n2. Or set the environment variables directly") 