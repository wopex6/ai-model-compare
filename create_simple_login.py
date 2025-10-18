#!/usr/bin/env python3
"""
Create a simple, working login for Wai Tse
"""

import sqlite3
import bcrypt
from integrated_database import IntegratedDatabase

def create_simple_login():
    print("🔧 Creating simple working login")
    print("=" * 40)
    
    # Use a simple password that definitely works
    simple_password = "123"
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Delete existing user
    cursor.execute('DELETE FROM users WHERE username = ?', ('Wai Tse',))
    
    # Create new user with simple password
    password_hash = bcrypt.hashpw(simple_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
    ''', ('Wai Tse', 'trabcd@yahoo.com', password_hash))
    
    user_id = cursor.lastrowid
    
    # Create basic profile
    cursor.execute('''
        INSERT INTO user_profiles (user_id, first_name, last_name, bio, location, preferences)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, 'Wai', 'Tse', 'Retired IT professional from Melbourne', 'Melbourne, Australia', 
          '{"interests": ["technology", "AI", "programming"]}'))
    
    # Add some psychology traits
    traits = [
        ('Openness', 0.8, 'High openness to new experiences'),
        ('Conscientiousness', 0.7, 'Well-organized and reliable'),
        ('Extraversion', 0.3, 'Introverted preference'),
        ('Agreeableness', 0.6, 'Moderately cooperative'),
        ('Neuroticism', 0.4, 'Emotionally stable')
    ]
    
    for trait_name, trait_value, description in traits:
        cursor.execute('''
            INSERT INTO psychology_traits (user_id, trait_name, trait_value, trait_description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, trait_name, trait_value, description))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created user with simple credentials:")
    print(f"   Username: Wai Tse")
    print(f"   Password: {simple_password}")
    
    # Test authentication
    db = IntegratedDatabase()
    user = db.authenticate_user('Wai Tse', simple_password)
    
    if user:
        print(f"✅ Authentication test SUCCESS: {user}")
        
        # Test profile and traits
        profile = db.get_user_profile(user['id'])
        traits = db.get_psychology_traits(user['id'])
        
        print(f"✅ Profile loaded: {profile['bio'] if profile else 'None'}")
        print(f"✅ Psychology traits: {len(traits)} traits")
        
        return True
    else:
        print(f"❌ Authentication test FAILED")
        return False

if __name__ == "__main__":
    if create_simple_login():
        print(f"\n🎉 SUCCESS! Use these simple credentials:")
        print(f"   Username: Wai Tse")
        print(f"   Password: 123")
        print(f"\n🌐 Login at: http://localhost:5000/multi-user")
        print(f"   (Clear the password field and type: 123)")
    else:
        print(f"\n❌ Failed to create working login")
