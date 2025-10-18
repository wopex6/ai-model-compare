#!/usr/bin/env python3
"""
Debug authentication issue
"""

import sqlite3
import bcrypt
from integrated_database import IntegratedDatabase

def debug_auth():
    print("🔍 Debugging Authentication Issue")
    print("=" * 40)
    
    # Check database directly
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('Wai Tse',))
    user_data = cursor.fetchone()
    
    if user_data:
        username, stored_hash = user_data
        print(f'✅ User found: "{username}"')
        print(f'   Hash length: {len(stored_hash)}')
        
        # Test different password variations
        passwords_to_test = ['.///', './//.', './/']
        
        for pwd in passwords_to_test:
            try:
                result = bcrypt.checkpw(pwd.encode('utf-8'), stored_hash.encode('utf-8'))
                print(f'   Password "{pwd}" works: {result}')
                if result:
                    print(f'   ✅ CORRECT PASSWORD: "{pwd}"')
            except Exception as e:
                print(f'   Password "{pwd}" error: {e}')
    else:
        print('❌ User not found!')
    
    conn.close()
    
    # Test with IntegratedDatabase class
    print(f"\n🔧 Testing with IntegratedDatabase class:")
    db = IntegratedDatabase()
    
    passwords_to_test = ['.///', './//.', './/']
    for pwd in passwords_to_test:
        user = db.authenticate_user('Wai Tse', pwd)
        print(f'   Password "{pwd}" via DB class: {"✅ SUCCESS" if user else "❌ FAILED"}')
        if user:
            print(f'   User data: {user}')
    
    # Check if there are any other users
    print(f"\n📋 All users in database:")
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email FROM users')
    all_users = cursor.fetchall()
    for user in all_users:
        print(f'   ID: {user[0]}, Username: "{user[1]}", Email: {user[2]}')
    conn.close()

if __name__ == "__main__":
    debug_auth()
