#!/usr/bin/env python3
"""
Setup the correct password based on what you're actually typing
"""

import sqlite3
import bcrypt
from integrated_database import IntegratedDatabase

def setup_password():
    print("🔧 Setting up password to match your input")
    print("=" * 40)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Test both 3-character and 4-character passwords
    passwords_to_test = [
        ('.///', '3 characters: period + 3 slashes'),
        ('.///', '4 characters: period + 2 slashes + period')
    ]
    
    for pwd, description in passwords_to_test:
        print(f"\nTesting: {description}")
        print(f"Password: '{pwd}' (length: {len(pwd)})")
        
        # Create password hash
        password_hash = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Delete and recreate user
        cursor.execute('DELETE FROM users WHERE username = ?', ('Ken',))
        cursor.execute('''
            INSERT INTO users (username, email, password_hash) 
            VALUES (?, ?, ?)
        ''', ('Ken', 'trabcd@yahoo.com', password_hash))
        conn.commit()
        
        # Test authentication
        db = IntegratedDatabase()
        user = db.authenticate_user('Ken', pwd)
        
        if user:
            print(f"✅ SUCCESS! Password '{pwd}' works")
            print(f"   User: {user}")
            
            # Also test that the profile data is there
            profile = db.get_user_profile(user['id'])
            traits = db.get_psychology_traits(user['id'])
            conversations = db.get_user_conversations(user['id'])
            
            print(f"   Profile: {'✅' if profile else '❌'}")
            print(f"   Psychology traits: {len(traits)} traits")
            print(f"   Conversations: {len(conversations)} conversations")
            
            conn.close()
            return pwd
        else:
            print(f"❌ FAILED: Password '{pwd}' doesn't work")
    
    conn.close()
    return None

if __name__ == "__main__":
    working_password = setup_password()
    
    if working_password:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Working password: '{working_password}'")
        print(f"🌐 Login at: http://localhost:5000/multi-user")
        print(f"   Username: Ken")
        print(f"   Password: {working_password}")
    else:
        print(f"\n❌ Could not set up working password")
        
    # Start the server
    print(f"\n🚀 Starting server...")
    import subprocess
    subprocess.Popen(['python', 'app.py'])
