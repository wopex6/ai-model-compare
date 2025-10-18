#!/usr/bin/env python3
"""
Quick restore of Wai Tse's real data
"""

import json
import sqlite3
from pathlib import Path

def quick_restore():
    print("🔄 Quick Restore of Real Data")
    print("=" * 30)
    
    # Load real profile
    profile_file = Path("user_profiles/eb049813-e28a-4ae6-8c7b-fa80250d0e51.json")
    with open(profile_file, 'r') as f:
        profile_data = json.load(f)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Get user ID
    cursor.execute('SELECT id FROM users WHERE username = ?', ('Wai Tse',))
    user_row = cursor.fetchone()
    if not user_row:
        print("❌ User not found")
        return
    
    user_id = user_row[0]
    print(f"✅ Found user ID: {user_id}")
    
    # Update profile
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
            'age': profile_data['personal_info']['age'],
            'occupation': profile_data['personal_info']['occupation'],
            'interests': profile_data['personal_info']['interests'],
            'personality_type': profile_data['preferences']['personality_type'],
            'communication_style': profile_data['preferences']['communication_style']
        })
    ))
    
    print("✅ Updated profile")
    
    # Add Carl Jung traits
    cursor.execute('DELETE FROM psychology_traits WHERE user_id = ?', (user_id,))
    
    jung = profile_data['preferences']['jung_types']
    big_five = profile_data['preferences']['big_five']
    
    traits = [
        # Carl Jung (converted to 0-1 scale)
        ('Jung_Extraversion_Introversion', (jung['extraversion_introversion'] + 10) / 20, 
         f"Carl Jung: {jung['extraversion_introversion']:.1f}"),
        ('Jung_Sensing_Intuition', (jung['sensing_intuition'] + 10) / 20,
         f"Carl Jung: {jung['sensing_intuition']:.1f}"),
        ('Jung_Thinking_Feeling', (jung['thinking_feeling'] + 10) / 20,
         f"Carl Jung: {jung['thinking_feeling']:.1f}"),
        ('Jung_Judging_Perceiving', (jung['judging_perceiving'] + 10) / 20,
         f"Carl Jung: {jung['judging_perceiving']:.1f}"),
        
        # Big Five
        ('Openness', big_five['openness'] / 10, f"Big Five: {big_five['openness']}/10"),
        ('Conscientiousness', big_five['conscientiousness'] / 10, f"Big Five: {big_five['conscientiousness']}/10"),
        ('Extraversion', big_five['extraversion'] / 10, f"Big Five: {big_five['extraversion']}/10"),
        ('Agreeableness', big_five['agreeableness'] / 10, f"Big Five: {big_five['agreeableness']}/10"),
        ('Neuroticism', big_five['neuroticism'] / 10, f"Big Five: {big_five['neuroticism']}/10")
    ]
    
    for trait_name, trait_value, description in traits:
        cursor.execute('''
            INSERT INTO psychology_traits (user_id, trait_name, trait_value, trait_description)
            VALUES (?, ?, ?, ?)
        ''', (user_id, trait_name, trait_value, description))
    
    print(f"✅ Added {len(traits)} psychology traits")
    
    conn.commit()
    conn.close()
    
    print("🎉 Real data restored!")
    print("   • Real profile from Melbourne")
    print("   • Carl Jung psychological results")
    print("   • Big Five personality traits")
    print("\n🚀 Login with: Username='Wai Tse', Password='123'")

if __name__ == "__main__":
    quick_restore()
