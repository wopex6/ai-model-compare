"""
Manually send verification email to a specific user
"""

from integrated_database import IntegratedDatabase
from email_service import EmailService
import sys

db = IntegratedDatabase()
email_service = EmailService()

print("\n" + "=" * 80)
print("📧 SEND VERIFICATION EMAIL")
print("=" * 80)

# Get user input
username = input("\nEnter username: ").strip()

if not username:
    print("❌ Username required")
    exit(1)

# Get user from database
import sqlite3
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('SELECT id, username, email, email_verified FROM users WHERE username = ?', (username,))
user = cursor.fetchone()
conn.close()

if not user:
    print(f"❌ User '{username}' not found")
    exit(1)

user_id, username, email, verified = user

print(f"\n👤 User Found:")
print(f"   ID: {user_id}")
print(f"   Username: {username}")
print(f"   Email: {email}")
print(f"   Verified: {'✅ Yes' if verified else '❌ No'}")

if verified:
    print("\n✅ This user is already verified!")
    response = input("\nSend verification email anyway? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled")
        exit(0)

# Generate verification code
verification_code = db.create_verification_code(user_id)

print(f"\n🔐 Generated verification code: {verification_code}")
print(f"📤 Sending email to: {email}")

# Send email
success = email_service.send_verification_code(email, username, verification_code)

if success:
    print("\n✅ VERIFICATION EMAIL SENT!")
    print(f"\n📬 Check inbox: {email}")
    print("   Subject: Email Verification - AI ChatChat")
    print(f"   Code: {verification_code}")
    print("   Expires: In 1 hour")
else:
    print("\n❌ Failed to send email")
    print("   Check your email credentials in .env")

print("=" * 80)
