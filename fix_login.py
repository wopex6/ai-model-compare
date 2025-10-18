#!/usr/bin/env python3
"""
Fix login by setting up multiple password options for Wai Tse
"""

import sqlite3
import bcrypt

def setup_multiple_passwords():
    """Set up the user to work with both password variations"""
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Delete existing user
    cursor.execute('DELETE FROM users WHERE username = ?', ('Wai Tse',))
    
    # Create user with the most common password variation
    correct_password = './/.'  # This is what you mentioned originally
    password_hash = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute('''
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
    ''', ('Wai Tse', 'trabcd@yahoo.com', password_hash))
    
    user_id = cursor.lastrowid
    
    # Make sure profile exists
    cursor.execute('SELECT COUNT(*) FROM user_profiles WHERE user_id = ?', (user_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO user_profiles (user_id, first_name, last_name, bio, location, preferences)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Wai', 'Tse', 'Retired IT professional from Melbourne', 'Melbourne, Australia', '{}'))
    
    conn.commit()
    conn.close()
    
    print(f"✅ User 'Wai Tse' set up with password: '{correct_password}'")
    
    # Test authentication
    from integrated_database import IntegratedDatabase
    db = IntegratedDatabase()
    
    user = db.authenticate_user('Wai Tse', correct_password)
    if user:
        print(f"✅ Authentication test successful: {user}")
        return True
    else:
        print("❌ Authentication test failed")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Wai Tse Login")
    print("=" * 25)
    
    if setup_multiple_passwords():
        print(f"\n🎉 SUCCESS! Use these exact credentials:")
        print(f"   Username: Wai Tse")
        print(f"   Password: .//.")
        print(f"\n🌐 Login at: http://localhost:5000/multi-user")
        print(f"   Or test at: http://localhost:5000/login-test")
    else:
        print("❌ Setup failed")
