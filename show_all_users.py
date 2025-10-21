"""
Show all users with their email addresses
"""

from integrated_database import IntegratedDatabase

db = IntegratedDatabase()

import sqlite3
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT id, username, email, user_role, email_verified, created_at
    FROM users
    ORDER BY created_at DESC
''')

users = cursor.fetchall()
conn.close()

print("\n" + "=" * 80)
print("📋 ALL USERS IN DATABASE")
print("=" * 80)
print()

if users:
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<15} {'Verified':<10}")
    print("-" * 80)
    
    for user in users:
        user_id, username, email, role, verified, created = user
        verified_str = "✅ Yes" if verified else "❌ No"
        print(f"{user_id:<5} {username:<20} {email:<30} {role:<15} {verified_str:<10}")
    
    print()
    print(f"Total users: {len(users)}")
else:
    print("No users found")

print("=" * 80)
