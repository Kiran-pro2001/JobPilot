import os
import smtplib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_login():
    email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    if not email or not password:
        print("❌ Error: Credentials missing in .env")
        return

    # Strip whitespace
    email = email.strip()
    password = password.strip()

    print(f"🔐 Attempting login for: {email}")
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email, password)
            print("✅ SUCCESS! Your credentials are working perfectly.")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print("\n👉 Tip: Generate a new App Password at https://myaccount.google.com/apppasswords")

if __name__ == "__main__":
    test_login()