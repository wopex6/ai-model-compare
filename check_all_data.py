"""Check ALL possible places where assessment might be saved"""

from integrated_database import IntegratedDatabase
import json

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

print("\n" + "="*60)
print("🔍 COMPREHENSIVE DATA CHECK")
print("="*60)

# 1. Check psychology_traits
print("\n1️⃣ PSYCHOLOGY_TRAITS (current assessment):")
cursor.execute("""
    SELECT trait_name, trait_value, updated_at 
    FROM psychology_traits 
    WHERE user_id = 1 
    ORDER BY trait_name
""")
traits = cursor.fetchall()
if traits:
    for trait_name, trait_value, updated_at in traits:
        print(f"   • {trait_name}: {trait_value*100:.1f}% (updated: {updated_at})")
else:
    print("   ❌ No data")

# 2. Check assessment_history
print("\n2️⃣ ASSESSMENT_HISTORY (tracking over time):")
cursor.execute("""
    SELECT id, completed_at, openness, conscientiousness, extraversion, 
           agreeableness, neuroticism, notes
    FROM assessment_history 
    WHERE user_id = 1 
    ORDER BY completed_at DESC
""")
history = cursor.fetchall()
if history:
    for row in history:
        print(f"   Assessment #{row[0]} - {row[1]}")
        print(f"     O:{row[2]*100:.0f}% C:{row[3]*100:.0f}% E:{row[4]*100:.0f}% A:{row[5]*100:.0f}% N:{row[6]*100:.0f}%")
        if row[7]:
            print(f"     Notes: {row[7]}")
else:
    print("   ❌ No data")

# 3. Check user preferences (old JSON system)
print("\n3️⃣ USER_PROFILES.PREFERENCES (old JSON system):")
cursor.execute("""
    SELECT preferences
    FROM user_profiles
    WHERE user_id = 1
""")
result = cursor.fetchone()
if result and result[0]:
    prefs = json.loads(result[0])
    
    # Check for big_five in preferences
    if 'big_five' in prefs:
        print("   Big Five data found:")
        for trait, value in prefs['big_five'].items():
            print(f"   • {trait}: {value*100:.1f}%")
    
    # Check for assessment_history in preferences
    if 'assessment_history' in prefs:
        print(f"\n   Assessment history entries: {len(prefs['assessment_history'])}")
        for i, entry in enumerate(prefs['assessment_history'][-3:], 1):  # Last 3
            print(f"   Entry {i}: {entry.get('timestamp', 'No timestamp')}")
            if 'big_five' in entry:
                bf = entry['big_five']
                print(f"     O:{bf.get('openness',0)*100:.0f}% C:{bf.get('conscientiousness',0)*100:.0f}% E:{bf.get('extraversion',0)*100:.0f}%")
    
    if 'big_five' not in prefs and 'assessment_history' not in prefs:
        print("   ❌ No assessment data in preferences")
else:
    print("   ❌ No preferences data")

# 4. Check for any recent database writes
print("\n4️⃣ DATABASE MODIFICATION TIMES:")
import os
db_path = 'integrated_database.db'
if os.path.exists(db_path):
    mod_time = os.path.getmtime(db_path)
    from datetime import datetime
    mod_datetime = datetime.fromtimestamp(mod_time)
    print(f"   Last modified: {mod_datetime}")
    
    # Check if modified in last hour
    from datetime import timedelta
    now = datetime.now()
    if now - mod_datetime < timedelta(hours=1):
        print(f"   ✅ Modified recently ({(now-mod_datetime).seconds//60} minutes ago)")
    else:
        print(f"   ⚠️  Not modified recently ({(now-mod_datetime).days} days ago)")
else:
    print("   ❌ Database file not found")

conn.close()

print("\n" + "="*60)
print("📋 DIAGNOSIS")
print("="*60)

if history and len(history) > 1:
    print("\n✅ Your new assessment IS saved in history!")
    print("   Run check_recent_assessment.py to see comparison")
elif traits:
    print("\n⚠️  Assessment data exists in psychology_traits but NOT in history")
    print("   Possible causes:")
    print("   1. Server error during save")
    print("   2. Frontend didn't call the new endpoint")
    print("   3. Network issue during submission")
    print("\n   SOLUTION: Retake the assessment OR manually migrate current data")
else:
    print("\n❌ NO assessment data found anywhere!")
    print("   The assessment was likely NOT submitted successfully")
    print("   Possible causes:")
    print("   1. Server was down/crashed")
    print("   2. JavaScript error prevented submission")
    print("   3. Network issue")
    print("\n   SOLUTION: Retake the assessment after fixing server")

print("\n" + "="*60 + "\n")
