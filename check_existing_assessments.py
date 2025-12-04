"""
Check for existing personality assessment data in all locations
"""

import sqlite3
from pathlib import Path
import json

DB_PATH = Path(__file__).parent / 'integrated_users.db'

print("=" * 80)
print("CHECKING FOR EXISTING PERSONALITY ASSESSMENTS")
print("=" * 80)
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Check assessment_history table
print("📊 1. ASSESSMENT_HISTORY TABLE:")
cursor.execute('SELECT * FROM assessment_history')
rows = cursor.fetchall()

if rows:
    cursor.execute('PRAGMA table_info(assessment_history)')
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"   Found {len(rows)} assessment(s)")
    for row in rows:
        data = dict(zip(columns, row))
        print(f"\n   Assessment ID: {data['id']}")
        print(f"   User ID: {data['user_id']}")
        print(f"   Completed: {data['completed_at']}")
        print(f"   Big 5: O={data['openness']:.2f}, C={data['conscientiousness']:.2f}, " +
              f"E={data['extraversion']:.2f}, A={data['agreeableness']:.2f}, N={data['neuroticism']:.2f}")
        if data['notes']:
            print(f"   Notes: {data['notes']}")
else:
    print("   ❌ No assessments found")

print()
print("=" * 80)
print("📊 2. USER_PROFILES.PREFERENCES (OLD STORAGE):")

cursor.execute('''
    SELECT user_id, first_name, last_name, preferences 
    FROM user_profiles 
    WHERE preferences IS NOT NULL AND preferences != '{}'
''')

profiles = cursor.fetchall()

if profiles:
    print(f"   Found {len(profiles)} user profile(s) with preferences")
    for profile in profiles:
        user_id, first_name, last_name, prefs_json = profile
        try:
            prefs = json.loads(prefs_json)
            
            print(f"\n   User: {first_name} {last_name} (ID: {user_id})")
            
            # Check for Jung types
            if 'jung_types' in prefs:
                print(f"   ✅ Has Jung Types:")
                jung = prefs['jung_types']
                for key, value in jung.items():
                    print(f"      {key}: {value}")
            
            # Check for Big 5
            if 'big_five' in prefs:
                print(f"   ✅ Has Big Five:")
                big5 = prefs['big_five']
                for key, value in big5.items():
                    print(f"      {key}: {value}")
            
            # Check for assessment history
            if 'assessment_history' in prefs:
                history = prefs['assessment_history']
                print(f"   ✅ Has assessment history: {len(history)} assessment(s)")
                for i, assessment in enumerate(history, 1):
                    print(f"      #{i}: {assessment.get('timestamp', 'No timestamp')}")
            
            # Check for assessment completed
            if 'assessment_completed_at' in prefs:
                print(f"   ✅ Last assessment: {prefs['assessment_completed_at']}")
        
        except json.JSONDecodeError:
            print(f"   ⚠️  Invalid JSON in preferences")
else:
    print("   ❌ No profiles with preferences found")

print()
print("=" * 80)
print("📊 3. PSYCHOLOGY_TRAITS TABLE:")

try:
    cursor.execute('SELECT * FROM psychology_traits')
    rows = cursor.fetchall()
    
    if rows:
        print(f"   Found {len(rows)} trait(s)")
        for row in rows:
            print(f"   {row}")
    else:
        print("   ❌ No traits found")
except sqlite3.OperationalError:
    print("   ⚠️  Table doesn't exist")

print()
print("=" * 80)
print("SUMMARY:")
print("=" * 80)

# Count total assessments across all sources
cursor.execute('SELECT COUNT(*) FROM assessment_history')
history_count = cursor.fetchone()[0]

cursor.execute('''
    SELECT COUNT(*) FROM user_profiles 
    WHERE preferences LIKE '%big_five%' OR preferences LIKE '%jung_types%'
''')
prefs_count = cursor.fetchone()[0]

print(f"   Assessment History table: {history_count} assessment(s)")
print(f"   User Preferences (old):   {prefs_count} user(s) with assessment data")
print()

if prefs_count > 0:
    print("✅ OLD ASSESSMENT DATA FOUND IN USER_PROFILES!")
    print("   This needs to be migrated to assessment_history table")
    print("   and displayed in the new personality test graphs")
else:
    print("   No old assessment data to migrate")

conn.close()
