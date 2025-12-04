"""
Migrate old assessment data from user_profiles.preferences 
to assessment_history table for graph display
"""

import sqlite3
from pathlib import Path
import json
from datetime import datetime

DB_PATH = Path(__file__).parent / 'integrated_users.db'

print("=" * 80)
print("MIGRATING OLD ASSESSMENT DATA TO HISTORY")
print("=" * 80)
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get users with old assessment data
cursor.execute('''
    SELECT user_id, first_name, last_name, preferences 
    FROM user_profiles 
    WHERE preferences LIKE '%assessment_history%'
''')

users_with_history = cursor.fetchall()

print(f"Found {len(users_with_history)} user(s) with assessment history in preferences")
print()

migrated_count = 0

for user_id, first_name, last_name, prefs_json in users_with_history:
    print(f"📊 User: {first_name} {last_name} (ID: {user_id})")
    
    try:
        prefs = json.loads(prefs_json)
        
        if 'assessment_history' not in prefs:
            print("   ⚠️  No assessment_history found")
            continue
        
        history = prefs['assessment_history']
        print(f"   Found {len(history)} assessment(s) in history")
        
        for i, assessment in enumerate(history, 1):
            # Extract Big 5 data
            if 'big_five' not in assessment:
                print(f"   ⚠️  Assessment #{i} has no Big 5 data, skipping")
                continue
            
            big5 = assessment['big_five']
            timestamp = assessment.get('timestamp', datetime.now().isoformat())
            
            # Convert timestamp format if needed
            try:
                # Try parsing various formats
                if 'Z' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(timestamp)
                completed_at = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check if this assessment already exists
            cursor.execute('''
                SELECT COUNT(*) FROM assessment_history
                WHERE user_id = ? AND completed_at = ?
            ''', (user_id, completed_at))
            
            if cursor.fetchone()[0] > 0:
                print(f"   ⏭️  Assessment #{i} already exists ({completed_at}), skipping")
                continue
            
            # Insert into assessment_history
            try:
                cursor.execute('''
                    INSERT INTO assessment_history
                    (user_id, openness, conscientiousness, extraversion, agreeableness, neuroticism,
                     completed_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    big5.get('openness', 0.5),
                    big5.get('conscientiousness', 0.5),
                    big5.get('extraversion', 0.5),
                    big5.get('agreeableness', 0.5),
                    big5.get('neuroticism', 0.5),
                    completed_at,
                    f'Migrated from Insights Dashboard (completed {completed_at})'
                ))
                
                print(f"   ✅ Migrated assessment #{i} ({completed_at})")
                print(f"      O={big5.get('openness'):.2f}, C={big5.get('conscientiousness'):.2f}, " + 
                      f"E={big5.get('extraversion'):.2f}, A={big5.get('agreeableness'):.2f}, N={big5.get('neuroticism'):.2f}")
                
                migrated_count += 1
                
            except Exception as e:
                print(f"   ❌ Error migrating assessment #{i}: {e}")
        
        print()
        
    except json.JSONDecodeError:
        print("   ❌ Invalid JSON in preferences")
        print()

# Commit changes
conn.commit()

print("=" * 80)
print(f"✅ MIGRATION COMPLETE: {migrated_count} assessment(s) migrated")
print("=" * 80)
print()

# Show updated assessment_history
cursor.execute('''
    SELECT user_id, COUNT(*) as count
    FROM assessment_history
    GROUP BY user_id
''')

print("📊 Assessment History Summary:")
for row in cursor.fetchall():
    print(f"   User {row[0]}: {row[1]} assessment(s)")

conn.close()
