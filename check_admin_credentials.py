#!/usr/bin/env python3
"""Check administrator account details"""

from integrated_database import IntegratedDatabase
import bcrypt

db = IntegratedDatabase()

# Get administrator user
users = db.get_all_users_stats()
admin = [u for u in users if u['username'] == 'administrator']

if admin:
    admin = admin[0]
    print(f"\n✅ Administrator account found:")
    print(f"   Username: {admin['username']}")
    print(f"   Email: {admin['email']}")
    print(f"   Role: {admin['role']}")
    print(f"   ID: {admin['id']}")
    
    # Test password
    print(f"\n🔐 Testing password 'admin123'...")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', ('administrator',))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        stored_hash = result[0]
        test_password = 'admin123'
        
        if bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8')):
            print(f"   ✅ Password 'admin123' is CORRECT")
        else:
            print(f"   ❌ Password 'admin123' is WRONG")
            print(f"   💡 Try checking the password in the database")
    
    # Check if role is exactly 'administrator'
    if admin['role'] == 'administrator':
        print(f"\n✅ Role is correct: 'administrator'")
    else:
        print(f"\n❌ Role is '{admin['role']}' (should be 'administrator')")
else:
    print("\n❌ No administrator account found!")
