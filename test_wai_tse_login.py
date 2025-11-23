#!/usr/bin/env python3
"""Test Wai Tse login credentials"""

import sqlite3
import bcrypt

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Get Wai Tse's password hash
cursor.execute('SELECT username, email, user_role, password_hash FROM users WHERE username = ?', ('Wai Tse',))
result = cursor.fetchone()

if result:
    username, email, role, password_hash = result
    print("=" * 50)
    print("WAI TSE ACCOUNT:")
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
