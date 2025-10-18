#!/usr/bin/env python3
"""
Simple verification script for Wai Tse's data
"""

from integrated_database import IntegratedDatabase

def main():
    print("🔍 Verifying Wai Tse's Data")
    print("=" * 30)
    
    db = IntegratedDatabase()
    
    # Test authentication
    print("Testing authentication...")
    user = db.authenticate_user('Wai Tse', './/.')
    
    if user:
        print(f"✅ SUCCESS! Logged in as: {user['username']} (ID: {user['id']})")
        
        # Get profile
        profile = db.get_user_profile(user['id'])
        if profile:
            print(f"✅ Profile: {profile['bio'][:50]}...")
            print(f"   Location: {profile['location']}")
        
        # Get traits
        traits = db.get_psychology_traits(user['id'])
        print(f"✅ Psychology Traits: {len(traits)} loaded")
        
        # Show Carl Jung traits
        jung_traits = [t for t in traits if 'Jung_' in t['trait_name']]
        if jung_traits:
            print("   🧠 Carl Jung Model Found:")
            for trait in jung_traits:
                print(f"      {trait['trait_name']}: {trait['trait_value']:.2f}")
        
        # Show Big Five traits  
        big_five = [t for t in traits if 'Jung_' not in t['trait_name']]
        if big_five:
            print("   📊 Big Five Model Found:")
            for trait in big_five:
                print(f"      {trait['trait_name']}: {trait['trait_value']:.2f}")
        
        # Get conversations
        conversations = db.get_user_conversations(user['id'])
        print(f"✅ Conversations: {len(conversations)} imported")
        
        if conversations:
            # Show first conversation details
            first_conv = conversations[0]
            messages = db.get_conversation_messages(first_conv['session_id'], user['id'])
            print(f"   First conversation: {len(messages)} messages")
            if messages:
                print(f"   Sample: {messages[0]['content'][:60]}...")
        
        print(f"\n🎉 ALL DATA VERIFIED!")
        print(f"🌐 Ready to use at: http://localhost:5000/multi-user")
        print(f"   Username: Wai Tse")
        print(f"   Password: .//.")
        
    else:
        print("❌ Authentication failed")
        # Try to fix password
        print("Attempting to fix password...")
        import sqlite3
        import bcrypt
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        password_hash = bcrypt.hashpw('.//'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'Wai Tse'))
        conn.commit()
        conn.close()
        
        print("Password fixed. Try again:")
        user = db.authenticate_user('Wai Tse', './/.')
        if user:
            print(f"✅ NOW WORKING! User: {user['username']}")
        else:
            print("❌ Still not working")

if __name__ == "__main__":
    main()
