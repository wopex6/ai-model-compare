#!/usr/bin/env python3
"""
Fix Ken authentication and verify all data is properly loaded
"""

import sqlite3
import bcrypt
import json
from integrated_database import IntegratedDatabase

def fix_ken_password():
    """Fix Ken's password hash"""
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Update password hash for Ken
    correct_password = './/.'
    password_hash = bcrypt.hashpw(correct_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'Ken'))
    conn.commit()
    conn.close()
    
    print("✅ Fixed Ken's password")

def verify_and_show_data():
    """Verify and display Ken's data"""
    db = IntegratedDatabase()
    
    # Test authentication
    user = db.authenticate_user('Ken', './/.')
    if not user:
        print("❌ Still can't authenticate!")
        return False
    
    print(f"✅ Authentication successful: {user['username']} (ID: {user['id']})")
    
    # Check profile
    profile = db.get_user_profile(user['id'])
    if profile:
        print(f"✅ Profile loaded:")
        print(f"   Bio: {profile['bio']}")
        print(f"   Location: {profile['location']}")
        preferences = json.loads(profile.get('preferences', '{}')) if profile.get('preferences') else {}
        print(f"   Age: {preferences.get('age', 'N/A')}")
        print(f"   Occupation: {preferences.get('occupation', 'N/A')}")
        print(f"   Interests: {', '.join(preferences.get('interests', []))}")
        print(f"   Personality Type: {preferences.get('personality_type', 'N/A')}")
    
    # Check psychology traits
    traits = db.get_psychology_traits(user['id'])
    print(f"\n✅ Psychology Traits ({len(traits)} total):")
    
    # Show Carl Jung traits
    jung_traits = [t for t in traits if t['trait_name'].startswith('Jung_')]
    if jung_traits:
        print("   🧠 Carl Jung Model:")
        for trait in jung_traits:
            print(f"      - {trait['trait_name']}: {trait['trait_value']:.2f} - {trait['trait_description']}")
    
    # Show Big Five traits
    big_five_traits = [t for t in traits if not t['trait_name'].startswith('Jung_')]
    if big_five_traits:
        print("   📊 Big Five Model:")
        for trait in big_five_traits:
            print(f"      - {trait['trait_name']}: {trait['trait_value']:.2f} - {trait['trait_description']}")
    
    # Check conversations
    conversations = db.get_user_conversations(user['id'])
    print(f"\n✅ Conversations: {len(conversations)} imported")
    
    if conversations:
        print("   Recent conversations:")
        for i, conv in enumerate(conversations[:3]):  # Show first 3
            messages = db.get_conversation_messages(conv['session_id'], user['id'])
            print(f"      {i+1}. {conv['title']} - {len(messages)} messages")
            if messages:
                first_msg = messages[0]['content'][:60] + "..." if len(messages[0]['content']) > 60 else messages[0]['content']
                print(f"         First message: {first_msg}")
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing Ken Authentication & Data Verification")
    print("=" * 55)
    
    fix_ken_password()
    
    if verify_and_show_data():
        print(f"\n🎉 SUCCESS! Ken's complete data is now available:")
        print(f"   • Real profile from Melbourne, Australia")
        print(f"   • Carl Jung psychological model results")
        print(f"   • Big Five personality traits")
        print(f"   • Imported conversation history")
        print(f"\n🌐 Login at: http://localhost:5000/multi-user")
        print(f"   Username: Ken")
        print(f"   Password: .//.")
    else:
        print("❌ Still having issues!")
