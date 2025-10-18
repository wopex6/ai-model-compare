#!/usr/bin/env python3
"""
Create a dedicated test user for automated testing
"""

import bcrypt
from integrated_database import IntegratedDatabase

def create_test_user():
    print("🤖 Creating Dedicated Test User")
    print("=" * 60)
    
    db = IntegratedDatabase()
    
    # Test user credentials
    username = "AutoTest"
    password = "test123"
    email = "autotest@example.com"
    
    # Check if test user already exists
    existing_user = db.authenticate_user(username, password)
    if existing_user:
        print(f"✅ Test user '{username}' already exists (ID: {existing_user['id']})")
        return existing_user['id']
    
    # Create test user
    try:
        user_id = db.create_user(username, email, password)
        print(f"✅ Created test user: {username} (ID: {user_id})")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        # User might exist, try to get ID
        import sqlite3
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_id = result[0]
            print(f"⚠️  User exists but password may be different. Using ID: {user_id}")
            
            # Fix password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn = sqlite3.connect('integrated_users.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
            conn.commit()
            conn.close()
            print(f"✅ Updated password for test user")
        else:
            return None
    
    # Create test profile
    print("\n📝 Creating test profile...")
    profile_data = {
        'first_name': 'Auto',
        'last_name': 'Test',
        'bio': 'Automated test user for system testing',
        'location': 'Test Environment',
        'preferences': '{"theme": "light", "notifications": true}'
    }
    
    import sqlite3
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Check if profile exists
    cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        print("✅ Profile already exists")
    else:
        cursor.execute('''
            INSERT INTO user_profiles (user_id, first_name, last_name, bio, location, preferences)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, profile_data['first_name'], profile_data['last_name'], 
              profile_data['bio'], profile_data['location'], profile_data['preferences']))
        print("✅ Created test profile")
    
    # Create test psychology traits
    print("\n🧠 Creating test psychology traits...")
    
    test_traits = [
        ('openness', 0.75, 'High openness to experience'),
        ('conscientiousness', 0.65, 'Moderate conscientiousness'),
        ('extraversion', 0.55, 'Balanced extraversion'),
        ('agreeableness', 0.70, 'High agreeableness'),
        ('neuroticism', 0.40, 'Low neuroticism')
    ]
    
    for trait_name, trait_value, description in test_traits:
        cursor.execute('''
            SELECT id FROM psychology_traits 
            WHERE user_id = ? AND trait_name = ?
        ''', (user_id, trait_name))
        
        if cursor.fetchone():
            continue  # Skip if exists
        
        cursor.execute('''
            INSERT INTO psychology_traits (user_id, trait_name, trait_value, trait_description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, trait_name, trait_value, description))
    
    print("✅ Created psychology traits")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 Test User Setup Complete!")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"User ID: {user_id}")
    print("\nThis user is now ready for automated testing.")
    
    return user_id

if __name__ == "__main__":
    create_test_user()
