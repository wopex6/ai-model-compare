#!/usr/bin/env python3
"""
Fix password to match exactly what browser is sending: ".///"
"""

import sqlite3
import bcrypt
from integrated_database import IntegratedDatabase

def fix_password():
    print("🔧 Fixing password to match browser input: './//'")
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # The browser is sending ".///" (3 characters)
    correct_password = ".///"
    password_hash = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update the password
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'Ken'))
    conn.commit()
    
    print(f"✅ Password updated to: '{correct_password}' (length: {len(correct_password)})")
    
    # Test authentication
    db = IntegratedDatabase()
    user = db.authenticate_user('Ken', correct_password)
    
    if user:
        print(f"✅ Authentication test SUCCESS: {user}")
    else:
        print(f"❌ Authentication test FAILED")
    
    conn.close()
    
    # Also test via direct API call
    import requests
    try:
        response = requests.post('http://localhost:5000/api/auth/login', 
                               json={'username': 'Ken', 'password': correct_password}, 
                               timeout=5)
        print(f"🌐 API test - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ API login SUCCESS!")
        else:
            print(f"❌ API login failed: {response.text}")
    except Exception as e:
        print(f"⚠️  API test error: {e}")

if __name__ == "__main__":
    fix_password()
    print(f"\n🎉 Password fixed!")
    print(f"✅ Use: Username='Ken', Password='.///'")
    print(f"🌐 Try login at: http://localhost:5000/multi-user")
