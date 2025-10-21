"""
Test email service to verify if emails can be sent
"""

from email_service import EmailService
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 80)
print("📧 TESTING EMAIL SERVICE")
print("=" * 80)

# Check environment variables
sender = os.getenv('EMAIL_SENDER')
password = os.getenv('EMAIL_PASSWORD')
smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
smtp_port = os.getenv('SMTP_PORT', '587')

print("\n📋 Configuration:")
print(f"   EMAIL_SENDER: {'✅ Set' if sender else '❌ Not set'}")
if sender:
    print(f"   Sender Email: {sender}")
print(f"   EMAIL_PASSWORD: {'✅ Set' if password else '❌ Not set'}")
if password:
    print(f"   Password Length: {len(password)} characters")
print(f"   SMTP Server: {smtp_server}")
print(f"   SMTP Port: {smtp_port}")

if not sender or not password:
    print("\n❌ ERROR: Email credentials not configured!")
    print("\nPlease add to your .env file:")
    print("   EMAIL_SENDER=your-gmail@gmail.com")
    print("   EMAIL_PASSWORD=your-16-char-app-password")
    exit(1)

# Test sending an email
print("\n📤 Testing email sending...")
print(f"   Sending test verification code to: {sender}")

email_service = EmailService()
success = email_service.send_verification_code(
    recipient_email=sender,  # Send to yourself for testing
    username="TestUser",
    verification_code="123456"
)

print()
if success:
    print("✅ EMAIL SENT SUCCESSFULLY!")
    print(f"\n📬 Check your inbox: {sender}")
    print("   Subject: Email Verification - AI ChatChat")
    print("   Code: 123456")
    print("\n⚠️  If you don't see it:")
    print("   1. Check your SPAM/Junk folder")
    print("   2. Wait a few minutes (can be delayed)")
    print("   3. Check Gmail 'All Mail' folder")
else:
    print("❌ EMAIL SENDING FAILED!")
    print("\n🔍 Common issues:")
    print("   1. App Password not enabled (requires 2FA)")
    print("   2. Wrong password or email")
    print("   3. Gmail blocking 'less secure apps'")
    print("   4. Network/firewall issues")

print("=" * 80)
