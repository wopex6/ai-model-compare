"""
Check which users need email verification
"""

from integrated_database import IntegratedDatabase
from email_service import EmailService

db = IntegratedDatabase()

import sqlite3
conn = db.get_connection()
cursor = conn.cursor()

# Get unverified users
cursor.execute('''
    SELECT id, username, email, created_at
    FROM users
    WHERE email_verified = 0
    ORDER BY created_at DESC
    LIMIT 10
''')

unverified = cursor.fetchall()
conn.close()

print("\n" + "=" * 80)
print("📋 UNVERIFIED USERS (Need Email Verification)")
print("=" * 80)

if unverified:
    print(f"\nFound {len(unverified)} unverified users:\n")
    
    for user in unverified:
        user_id, username, email, created = user
        print(f"ID: {user_id}")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Created: {created}")
        print("-" * 40)
    
    # Ask if user wants to resend verification emails
    print("\n💡 To resend verification email, use the 'Resend Code' button in the app")
    print("   Or I can create a script to send verification emails to these users")
else:
    print("\n✅ All users are verified!")

print("=" * 80)
