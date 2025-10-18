#!/usr/bin/env python3
"""
Restore Wai Tse's real data while keeping the working password '123'
"""

import json
import sqlite3
import bcrypt
from pathlib import Path
from datetime import datetime
from integrated_database import IntegratedDatabase

def restore_real_data():
    """Restore all real data while keeping working password"""
    
    print("🔄 Restoring Wai Tse's Real Data")
    print("=" * 40)
    
    # Load Wai Tse's real profile data
    profile_file = Path("user_profiles/eb049813-e28a-4ae6-8c7b-fa80250d0e51.json")
    if not profile_file.exists():
        print("❌ Wai Tse's profile file not found!")
        return False
    
    with open(profile_file, 'r') as f:
        profile_data = json.load(f)
    
    print("✅ Loaded Wai Tse's real profile data")
    
    # Get current user ID (keep existing user with working password)
    db = IntegratedDatabase()
    user = db.authenticate_user('Wai Tse', '123')
    if not user:
        print("❌ Current user not found! Please ensure login with '123' works first.")
        return False
    
    user_id = user['id']
    print(f"✅ Found existing user with ID: {user_id}")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Update profile with real data
    cursor.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
    cursor.execute('''
        INSERT INTO user_profiles (user_id, first_name, last_name, bio, location, preferences)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id, 
        'Wai', 
        'Tse', 
        profile_data['personal_info']['bio'],
        profile_data['personal_info']['location'],
        json.dumps({
            'communication_style': profile_data['preferences']['communication_style'],
            'interests': profile_data['personal_info']['interests'],
            'topics_of_interest': profile_data['preferences']['topics_of_interest'],
            'personality_type': profile_data['preferences']['personality_type'],
            'learning_style': profile_data['preferences']['learning_style'],
            'goals': profile_data['preferences']['goals'],
            'age': profile_data['personal_info']['age'],
            'occupation': profile_data['personal_info']['occupation'],
            'email': profile_data['personal_info']['email']
        })
    ))
    
    print("✅ Updated profile with real data")
    
    # Clear existing traits and add real psychology traits
    cursor.execute('DELETE FROM psychology_traits WHERE user_id = ?', (user_id,))
    
    # Carl Jung traits (converted to 0-1 scale)
    jung_traits = profile_data['preferences']['jung_types']
    jung_converted = [
        ('Jung_Extraversion_Introversion', (jung_traits['extraversion_introversion'] + 10) / 20, 
         f"Carl Jung: {jung_traits['extraversion_introversion']:.1f} (negative = introversion)"),
        ('Jung_Sensing_Intuition', (jung_traits['sensing_intuition'] + 10) / 20,
         f"Carl Jung: {jung_traits['sensing_intuition']:.1f} (negative = sensing, positive = intuition)"),
        ('Jung_Thinking_Feeling', (jung_traits['thinking_feeling'] + 10) / 20,
         f"Carl Jung: {jung_traits['thinking_feeling']:.1f} (negative = feeling, positive = thinking)"),
        ('Jung_Judging_Perceiving', (jung_traits['judging_perceiving'] + 10) / 20,
         f"Carl Jung: {jung_traits['judging_perceiving']:.1f} (negative = perceiving, positive = judging)")
    ]
    
    # Big Five traits (already 0-10 scale, convert to 0-1)
    big_five = profile_data['preferences']['big_five']
    big_five_converted = [
        ('Openness', big_five['openness'] / 10, f"Big Five: {big_five['openness']}/10 - High intellectual curiosity"),
        ('Conscientiousness', big_five['conscientiousness'] / 10, f"Big Five: {big_five['conscientiousness']}/10 - Well-organized and reliable"),
        ('Extraversion', big_five['extraversion'] / 10, f"Big Five: {big_five['extraversion']}/10 - Moderately social"),
        ('Agreeableness', big_five['agreeableness'] / 10, f"Big Five: {big_five['agreeableness']}/10 - Cooperative nature"),
        ('Neuroticism', big_five['neuroticism'] / 10, f"Big Five: {big_five['neuroticism']}/10 - Emotional stability")
    ]
    
    # Insert all traits
    all_traits = jung_converted + big_five_converted
    for trait_name, trait_value, description in all_traits:
        cursor.execute('''
            INSERT INTO psychology_traits (user_id, trait_name, trait_value, trait_description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, trait_name, trait_value, description))
    
    print(f"✅ Added {len(all_traits)} psychology traits (Carl Jung + Big Five)")
    
    # Clear existing conversations and import real ones
    cursor.execute('DELETE FROM ai_conversations WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM messages WHERE conversation_id IN (SELECT id FROM ai_conversations WHERE user_id = ?)', (user_id,))
    
    # Import conversation data
    conversations_dir = Path("conversations")
    conversation_files = list(conversations_dir.glob("*.json"))
    
    imported_conversations = 0
    imported_messages = 0
    
    for conv_file in conversation_files:
        if conv_file.stat().st_size > 1000:  # Only import substantial conversations
            try:
                with open(conv_file, 'r') as f:
                    conv_data = json.load(f)
                
                if 'messages' in conv_data and len(conv_data['messages']) > 2:
                    session_id = conv_data['session_id']
                    
                    # Create conversation record
                    cursor.execute('''
                        INSERT INTO ai_conversations (user_id, session_id, title, conversation_data, personality_data, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id, 
                        session_id, 
                        f"Imported Chat - {conv_data.get('created_at', 'Unknown')[:10]}", 
                        json.dumps({'messages': conv_data['messages']}),
                        json.dumps({'personality': 'adaptive', 'user_traits': 'imported'}),
                        conv_data.get('created_at', datetime.now().isoformat()),
                        conv_data.get('last_updated', datetime.now().isoformat())
                    ))
                    
                    conversation_id = cursor.lastrowid
                    
                    # Import individual messages
                    for msg in conv_data['messages']:
                        cursor.execute('''
                            INSERT INTO messages (conversation_id, sender_type, content, metadata, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            conversation_id, 
                            msg['role'], 
                            msg['content'], 
                            json.dumps(msg.get('metadata', {})),
                            msg.get('timestamp', datetime.now().isoformat())
                        ))
                        imported_messages += 1
                    
                    imported_conversations += 1
                    
            except Exception as e:
                print(f"⚠️  Skipped {conv_file.name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Imported {imported_conversations} conversations with {imported_messages} messages")
    print(f"🎉 Real data restoration complete!")
    
    return True

def verify_restoration():
    """Verify the restoration was successful"""
    print("\n🔍 Verifying restoration...")
    
    db = IntegratedDatabase()
    
    # Check user (should still work with password '123')
    user = db.authenticate_user('Wai Tse', '123')
    if not user:
        print("❌ Authentication failed")
        return False
    print(f"✅ User authentication still works: {user['username']}")
    
    # Check profile
    profile = db.get_user_profile(user['id'])
    if profile:
        print(f"✅ Real profile loaded:")
        print(f"   Bio: {profile['bio']}")
        print(f"   Location: {profile['location']}")
        preferences = json.loads(profile.get('preferences', '{}'))
        print(f"   Age: {preferences.get('age')}")
        print(f"   Occupation: {preferences.get('occupation')}")
    else:
        print("❌ Profile not found")
        return False
    
    # Check traits
    traits = db.get_psychology_traits(user['id'])
    print(f"✅ Psychology traits: {len(traits)} traits loaded")
    
    # Show Carl Jung traits
    jung_traits = [t for t in traits if 'Jung_' in t['trait_name']]
    if jung_traits:
        print("   🧠 Carl Jung Model:")
        for trait in jung_traits[:2]:  # Show first 2
            print(f"      {trait['trait_name']}: {trait['trait_value']:.2f}")
    
    # Check conversations
    conversations = db.get_user_conversations(user['id'])
    print(f"✅ Conversations: {len(conversations)} conversations loaded")
    
    print("🎉 Restoration verification complete!")
    return True

if __name__ == "__main__":
    print("Wai Tse Real Data Restoration")
    print("=" * 40)
    
    success = restore_real_data()
    if success:
        verify_restoration()
        print("\n🚀 Ready to use! Login credentials unchanged:")
        print("   Username: Wai Tse")
        print("   Password: 123")
        print("   URL: http://localhost:5000/multi-user")
        print("\n✅ Now you have:")
        print("   • Real profile data from Melbourne")
        print("   • Carl Jung psychological model results")
        print("   • Big Five personality traits")
        print("   • Imported conversation history")
    else:
        print("❌ Restoration failed!")
