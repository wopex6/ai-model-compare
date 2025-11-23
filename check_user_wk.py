"""Check if user WK exists and has assessment history"""

from integrated_database import IntegratedDatabase
import json

db = IntegratedDatabase()

print("\n" + "="*80)
print("CHECKING USER 'WK' AND ASSESSMENT HISTORY")
print("="*80)

# Search for user by username
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute("SELECT id, username, email FROM users WHERE username = ?", ('WK',))
user_row = cursor.fetchone()

if user_row:
    user_id, username, email = user_row
    print(f"\n✅ User WK found!")
    print(f"   User ID: {user_id}")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    
    # Get profile
    cursor.execute('''
        SELECT first_name, last_name, bio, preferences
        FROM user_profiles WHERE user_id = ?
    ''', (user_id,))
    
    profile_row = cursor.fetchone()
    
    if profile_row:
        first_name, last_name, bio, prefs_json = profile_row
        print(f"\n📊 Profile found:")
        print(f"   Name: {first_name} {last_name}")
        print(f"   Bio: {bio}")
        
        # Parse preferences
        prefs = json.loads(prefs_json) if prefs_json else {}
        
        # Check for assessment data
        assessment_history = prefs.get('assessment_history', [])
        jung_types = prefs.get('jung_types', {})
        big_five = prefs.get('big_five', {})
        assessment_completed = prefs.get('assessment_completed_at', None)
        
        print(f"\n📈 Assessment Data:")
        print(f"   Completed at: {assessment_completed}")
        print(f"   Jung Types: {jung_types}")
        print(f"   Big Five: {big_five}")
        print(f"   History entries: {len(assessment_history)}")
        
        if assessment_history:
            print(f"\n✅ Assessment History ({len(assessment_history)} entries):")
            for i, assessment in enumerate(assessment_history, 1):
                print(f"\n  Assessment #{i}:")
                print(f"    Timestamp: {assessment.get('timestamp')}")
                print(f"    Jung Types: {assessment.get('jung_types')}")
                print(f"    Big Five: {assessment.get('big_five')}")
        else:
            print("\n❌ No assessment history found!")
            
            if assessment_completed:
                print("   ⚠️  User has assessment_completed_at but NO history!")
                print("   This means the history wasn't saved properly.")
            else:
                print("   User WK has NOT completed the personality assessment yet.")
    else:
        print("\n❌ Profile not found!")
else:
    print("\n❌ User WK not found in database!")
    print("\nSearching all users...")
    
    cursor.execute("SELECT id, username, email FROM users")
    users = cursor.fetchall()
    
    print(f"\nFound {len(users)} users:")
    for user_id, username, email in users:
        print(f"  - {username} (ID: {user_id}, Email: {email})")

conn.close()

print("\n" + "="*80)
print("CHECK COMPLETE")
print("="*80 + "\n")
