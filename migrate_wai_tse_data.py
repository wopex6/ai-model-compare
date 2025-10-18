#!/usr/bin/env python3
"""
Migration script to properly import Wai Tse's real profile and conversation data
from the existing system into the integrated multi-user database
"""

import json
import sqlite3
import bcrypt
from pathlib import Path
from datetime import datetime
from integrated_database import IntegratedDatabase

def migrate_wai_tse_data():
    """Migrate Wai Tse's real data from existing files"""
    
    print("🔄 Starting Wai Tse data migration...")
    
    # Initialize integrated database
    db = IntegratedDatabase()
    
    # Load Wai Tse's profile data
    profile_file = Path("user_profiles/eb049813-e28a-4ae6-8c7b-fa80250d0e51.json")
    if not profile_file.exists():
        print("❌ Wai Tse's profile file not found!")
        return False
    
    with open(profile_file, 'r') as f:
        profile_data = json.load(f)
    
    print("✅ Loaded Wai Tse's profile data")
    
    # Delete existing default user if exists
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM users WHERE username = ?', ('Wai Tse',))
    conn.commit()
    
    # Create Wai Tse with real data
    password_hash = bcrypt.hashpw('.//'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT INTO users (username, email, password_hash)
        VALUES (?, ?, ?)
    ''', ('Wai Tse', profile_data['personal_info']['email'], password_hash))
    
    user_id = cursor.lastrowid
    print(f"✅ Created user 'Wai Tse' with ID: {user_id}")
    
    # Create real profile
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
            'occupation': profile_data['personal_info']['occupation']
        })
    ))
    
    print("✅ Created real profile data")
    
    # Create psychology traits from Carl Jung's model AND Big Five
    jung_traits = profile_data['preferences']['jung_types']
    big_five = profile_data['preferences']['big_five']
    
    # Carl Jung traits (converted to 0-1 scale)
    jung_converted = [
        ('Jung_Extraversion_Introversion', (jung_traits['extraversion_introversion'] + 10) / 20, 
         f"Jung model: {jung_traits['extraversion_introversion']:.1f} (negative = introversion)"),
        ('Jung_Sensing_Intuition', (jung_traits['sensing_intuition'] + 10) / 20,
         f"Jung model: {jung_traits['sensing_intuition']:.1f} (negative = sensing, positive = intuition)"),
        ('Jung_Thinking_Feeling', (jung_traits['thinking_feeling'] + 10) / 20,
         f"Jung model: {jung_traits['thinking_feeling']:.1f} (negative = feeling, positive = thinking)"),
        ('Jung_Judging_Perceiving', (jung_traits['judging_perceiving'] + 10) / 20,
         f"Jung model: {jung_traits['judging_perceiving']:.1f} (negative = perceiving, positive = judging)")
    ]
    
    # Big Five traits (already 0-10 scale, convert to 0-1)
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
    
    print(f"✅ Created {len(all_traits)} psychology traits (Jung + Big Five)")
    
    # Find and import conversation data
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
    print(f"🎉 Migration complete! Wai Tse's real data is now available in the integrated system.")
    
    return True

def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    db = IntegratedDatabase()
    
    # Check user
    user = db.authenticate_user('Wai Tse', './/.')
    if not user:
        print("❌ Authentication failed")
        return False
    print(f"✅ User authentication works: {user['username']}")
    
    # Check profile
    profile = db.get_user_profile(user['id'])
    if profile:
        print(f"✅ Profile loaded: {profile['bio'][:50]}...")
    else:
        print("❌ Profile not found")
        return False
    
    # Check traits
    traits = db.get_psychology_traits(user['id'])
    print(f"✅ Psychology traits: {len(traits)} traits loaded")
    for trait in traits[:3]:  # Show first 3
        print(f"   - {trait['trait_name']}: {trait['trait_value']:.2f}")
    
    # Check conversations
    conversations = db.get_user_conversations(user['id'])
    print(f"✅ Conversations: {len(conversations)} conversations loaded")
    
    if conversations:
        # Check messages in first conversation
        messages = db.get_conversation_messages(conversations[0]['session_id'], user['id'])
        print(f"✅ Messages: {len(messages)} messages in first conversation")
    
    print("🎉 Migration verification complete!")
    return True

if __name__ == "__main__":
    print("Wai Tse Data Migration Tool")
    print("=" * 40)
    
    success = migrate_wai_tse_data()
    if success:
        verify_migration()
        print("\n🚀 Ready to use! Login at http://localhost:5000/multi-user")
        print("   Username: Wai Tse")
        print("   Password: .//")
    else:
        print("❌ Migration failed!")
