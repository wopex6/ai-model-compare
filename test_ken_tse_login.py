#!/usr/bin/env python3
"""Test Ken login credentials"""

import sqlite3
import bcrypt

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Get Ken's password hash
cursor.execute('SELECT username, email, user_role, password_hash FROM users WHERE username = ?', ('Ken',))
result = cursor.fetchone()

if result:
    username, email, role, password_hash = result
    print("=" * 50)
    print("KEN TSE ACCOUNT:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Role: {role}")
    
    # Test password '123'
    test_password = '123'
    print(f"\n🔐 Testing password '{test_password}'...")
    
    if bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8')):
        print(f"   ✅ Password '{test_password}' is CORRECT")
    else:
        print(f"   ❌ Password '{test_password}' is WRONG")

conn.close()
