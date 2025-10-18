#!/usr/bin/env python3
"""
Fix password to the CORRECT original password: ".//." (period + two slashes + period)
"""

import sqlite3
import bcrypt
from integrated_database import IntegratedDatabase

def fix_to_correct_password():
    print("🔧 Fixing to CORRECT original password")
    print("=" * 40)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # The CORRECT original password should be ".//." (4 characters)
    correct_password = ".//."  # period + slash + slash + period
    print(f"Setting CORRECT password: '{correct_password}' (length: {len(correct_password)})")
    print(f"Characters: {[c for c in correct_password]}")
    print(f"ASCII codes: {[ord(c) for c in correct_password]}")
    
    password_hash = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'Ken'))
    conn.commit()
    
    # Test authentication
    db = IntegratedDatabase()
    user = db.authenticate_user('Ken', correct_password)
    
    if user:
        print(f"✅ Authentication test SUCCESS with correct password")
    else:
        print(f"❌ Authentication test FAILED")
    
    conn.close()
    
    print(f"\n🎯 CORRECT CREDENTIALS:")
    print(f"   Username: Ken")
    print(f"   Password: {correct_password}")
    print(f"   (period + slash + slash + period)")

if __name__ == "__main__":
    fix_to_correct_password()
    
    print(f"\n⚠️  IMPORTANT:")
    print(f"   The password is now set to the CORRECT original: './/.'")
    print(f"   You'll need to clear the password field and type: .//.")
    print(f"   (period, slash, slash, period)")
    print(f"\n🌐 Login at: http://localhost:5000/multi-user")
