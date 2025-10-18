#!/usr/bin/env python3
"""
Fix the forward slash password issue and restore original password
"""

import sqlite3
import bcrypt
from integrated_database import IntegratedDatabase
import requests
import json

def fix_slash_password():
    print("🔧 Fixing Forward Slash Password Issue")
    print("=" * 45)
    
    # Your original password
    original_password = ".//."  # period + slash + slash + period
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Update Wai Tse's password
    password_hash = bcrypt.hashpw(original_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'Wai Tse'))
    conn.commit()
    
    print(f"✅ Set password to: '{original_password}'")
    print(f"   Length: {len(original_password)}")
    print(f"   Characters: {list(original_password)}")
    print(f"   ASCII codes: {[ord(c) for c in original_password]}")
    
    # Test database authentication
    db = IntegratedDatabase()
    user = db.authenticate_user('Wai Tse', original_password)
    print(f"\n🔍 Database authentication: {'✅ SUCCESS' if user else '❌ FAILED'}")
    
    # Test API authentication with different encodings
    print(f"\n🔍 API Authentication Tests:")
    
    test_cases = [
        ("Direct", original_password),
        ("URL encoded", original_password.replace('/', '%2F')),
        ("Double escaped", original_password.replace('/', '\\/')),
    ]
    
    for test_name, test_password in test_cases:
        try:
            response = requests.post('http://localhost:5000/api/auth/login', 
                                   json={'username': 'Wai Tse', 'password': test_password}, 
                                   timeout=5)
            result = "✅ SUCCESS" if response.status_code == 200 else f"❌ FAILED ({response.status_code})"
            print(f"   {test_name}: {result}")
            
            if response.status_code == 200:
                print(f"      🎉 WORKING PASSWORD FORMAT: '{test_password}'")
                break
                
        except Exception as e:
            print(f"   {test_name}: ❌ ERROR ({e})")
    
    conn.close()

def create_password_change_function():
    """Create a function to change password from within the app"""
    print(f"\n🔧 Creating password change utility...")
    
    change_script = '''
// Run this in the browser console after logging in with "123"
async function changeToOriginalPassword() {
    const newPassword = ".//";
    
    try {
        const response = await fetch('/api/auth/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                currentPassword: '123',
                newPassword: newPassword
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('✅ Password changed successfully!');
            console.log('New password:', newPassword);
        } else {
            console.log('❌ Password change failed:', result.error);
        }
    } catch (error) {
        console.log('❌ Error:', error);
    }
}

// Call the function
changeToOriginalPassword();
'''
    
    with open('change_password_script.js', 'w') as f:
        f.write(change_script)
    
    print(f"✅ Created change_password_script.js")
    print(f"   You can use this to change password from browser console")

if __name__ == "__main__":
    fix_slash_password()
    create_password_change_function()
    
    print(f"\n💡 SOLUTIONS:")
    print(f"1. 🚀 IMMEDIATE: Use password '123' to login")
    print(f"2. 🔧 IN-APP: Change password in Settings tab to './/.'")
    print(f"3. 🖥️  CONSOLE: Run the script in change_password_script.js")
    print(f"\n🌐 Login at: http://localhost:5000/multi-user")
    
    print(f"\n🔍 ROOT CAUSE:")
    print(f"   Forward slashes in passwords likely have encoding issues")
    print(f"   between frontend JavaScript and backend Flask")
    print(f"   This is a common web development issue with special characters")
