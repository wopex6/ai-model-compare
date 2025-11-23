"""
Check if WK4's personality data was saved to database
"""

from integrated_database import IntegratedDatabase
import json

db = IntegratedDatabase()

print("\n" + "="*80)
print("CHECKING WK4 DATABASE DATA")
print("="*80)

# Check if user exists
user = db.get_user_by_username('wk4')
if user:
    print(f"\n✅ User found in database:")
    print(f"   ID: {user['id']}")
    print(f"   Username: {user['username']}")
    print(f"   Email: {user['email']}")
    
    user_id = user['id']
    
    # Check user profile
    print(f"\n📊 Checking user profile...")
    profile = db.get_user_profile(user_id)
    if profile:
        print(f"   ✅ Profile exists")
        print(f"   Username: {profile.get('username')}")
        
        # Check preferences
        prefs = profile.get('preferences', {})
        print(f"\n🧠 Preferences data:")
        print(f"   Keys in preferences: {list(prefs.keys())}")
        
        if 'jung_types' in prefs:
            print(f"\n   ✅ Jung Types found:")
            print(f"      {json.dumps(prefs['jung_types'], indent=6)}")
        else:
            print(f"   ❌ No jung_types in preferences")
        
        if 'big_five' in prefs:
            print(f"\n   ✅ Big Five found:")
            print(f"      {json.dumps(prefs['big_five'], indent=6)}")
        else:
            print(f"   ❌ No big_five in preferences")
        
        if 'assessment_completed_at' in prefs:
            print(f"\n   ✅ Assessment completed at: {prefs['assessment_completed_at']}")
        else:
            print(f"   ❌ No assessment_completed_at")
        
        if 'assessment_history' in prefs:
            history = prefs['assessment_history']
            print(f"\n   ✅ Assessment history: {len(history)} entries")
        else:
            print(f"   ❌ No assessment_history")
    else:
        print(f"   ❌ No profile found")
    
    # Check psychology traits table
    print(f"\n🎯 Checking psychology_traits table...")
    traits = db.get_psychology_traits(user_id)
    if traits:
        print(f"   ✅ Found {len(traits)} traits:")
        for trait in traits[:10]:  # Show first 10
            print(f"      - {trait['trait_name']}: {trait['trait_value']}")
    else:
        print(f"   ❌ No traits in psychology_traits table")
    
else:
    print(f"\n❌ User 'wk4' not found in database")

print("\n" + "="*80)

# Also check JSON file
print("\nChecking JSON file...")
import os
json_file = "personality_profiles/wk4_profile.json"
if os.path.exists(json_file):
    print(f"✅ JSON file exists: {json_file}")
    with open(json_file, 'r') as f:
        data = json.load(f)
    print(f"   Keys: {list(data.keys())}")
    print(f"   Communication style: {data.get('communication_style')}")
    print(f"   Assessment stage: {data.get('assessment_stage')}")
    print(f"   Confidence level: {data.get('confidence_level')}")
else:
    print(f"❌ JSON file not found: {json_file}")

print("="*80)
