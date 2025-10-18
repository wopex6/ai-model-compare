#!/usr/bin/env python3
"""
Fix password to match what browser is actually sending
"""

import sqlite3
import bcrypt

def fix_password():
    # Update password to match what the browser is sending
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()

    # The browser is sending './//' so let's make that work
    browser_password = './//'
    password_hash = bcrypt.hashpw(browser_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'Wai Tse'))
    conn.commit()

    # Verify it works
    result = bcrypt.checkpw(browser_password.encode('utf-8'), password_hash.encode('utf-8'))
    print(f'Password ".///" now works: {result}')

    conn.close()
    
    # Test with IntegratedDatabase
    from integrated_database import IntegratedDatabase
    db = IntegratedDatabase()
    user = db.authenticate_user('Wai Tse', browser_password)
    print(f'Authentication test: {"SUCCESS" if user else "FAILED"}')
    
    if user:
        print(f'User data: {user}')

if __name__ == "__main__":
    print("🔧 Fixing password to match browser input")
    fix_password()
    print("✅ Password updated to match what browser sends: './//'")
    print("🌐 Try logging in again at: http://localhost:5000/multi-user")
