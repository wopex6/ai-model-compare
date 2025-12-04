"""
Deploy Assessment History Migration to Production

This script:
1. Checks if assessment_history table exists
2. Migrates old JSON assessment data to the table
3. Verifies the migration
"""

import sqlite3
from pathlib import Path
import json
from datetime import datetime

# PRODUCTION DATABASE PATH - CHANGE THIS!
PROD_DB_PATH = Path(__file__).parent / 'integrated_users.db'  # Update this path

print("=" * 80)
print("PRODUCTION DEPLOYMENT: Assessment History Migration")
print("=" * 80)
print()

# Confirmation
print(f"⚠️  WARNING: This will modify the production database at:")
print(f"   {PROD_DB_PATH}")
print()
response = input("Are you sure you want to continue? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Deployment cancelled")
    exit(0)

print()
print("Starting deployment...")
print()

conn = sqlite3.connect(PROD_DB_PATH)
cursor = conn.cursor()

# Step 1: Check if table exists
print("📋 Step 1: Checking if assessment_history table exists...")
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='assessment_history'
""")

if cursor.fetchone():
    print("   ✅ Table already exists")
else:
    print("   ⚠️  Table does not exist - creating it...")
    
    # Create the table (from integrated_database.py schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            assessment_version TEXT DEFAULT 'BIG5-v1',
            openness REAL NOT NULL,
            conscientiousness REAL NOT NULL,
            extraversion REAL NOT NULL,
            agreeableness REAL NOT NULL,
            neuroticism REAL NOT NULL,
            completion_time_seconds INTEGER,
            questions_answered INTEGER,
            started_at TIMESTAMP,
            completed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_assessment_history_user 
        ON assessment_history(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_assessment_history_completed 
        ON assessment_history(completed_at)
    ''')
    
    conn.commit()
    print("   ✅ Table created successfully")

print()

# Step 2: Check for existing data
print("📊 Step 2: Checking current data...")
cursor.execute('SELECT COUNT(*) FROM assessment_history')
existing_count = cursor.fetchone()[0]
print(f"   Current records in assessment_history: {existing_count}")

print()

# Step 3: Migrate old JSON data
print("🔄 Step 3: Migrating old assessment data from user_profiles...")

cursor.execute('''
    SELECT user_id, preferences 
    FROM user_profiles 
    WHERE preferences IS NOT NULL AND preferences != ''
''')

profiles_with_prefs = cursor.fetchall()
print(f"   Found {len(profiles_with_prefs)} user profiles with preferences")

migrated_count = 0
skipped_count = 0
error_count = 0

for user_id, prefs_json in profiles_with_prefs:
    try:
        prefs = json.loads(prefs_json) if isinstance(prefs_json, str) else prefs_json
        
        if not isinstance(prefs, dict):
            continue
            
        assessment_history = prefs.get('assessment_history', [])
        
        if not assessment_history:
            continue
        
        print(f"   Processing user {user_id}: {len(assessment_history)} assessment(s)")
        
        for assessment in assessment_history:
            if not isinstance(assessment, dict):
                continue
            
            # Check if already migrated (avoid duplicates)
            completed_at = assessment.get('completed_at', assessment.get('timestamp'))
            
            if completed_at:
                cursor.execute('''
                    SELECT COUNT(*) FROM assessment_history
                    WHERE user_id = ? AND completed_at = ?
                ''', (user_id, completed_at))
                
                if cursor.fetchone()[0] > 0:
                    skipped_count += 1
                    continue
            
            # Extract traits (could be in different formats)
            traits = assessment.get('traits', {})
            if not traits:
                # Try direct keys
                traits = {
                    'openness': assessment.get('openness'),
                    'conscientiousness': assessment.get('conscientiousness'),
                    'extraversion': assessment.get('extraversion'),
                    'agreeableness': assessment.get('agreeableness'),
                    'neuroticism': assessment.get('neuroticism')
                }
            
            # Validate required fields
            if not all([
                traits.get('openness') is not None,
                traits.get('conscientiousness') is not None,
                traits.get('extraversion') is not None,
                traits.get('agreeableness') is not None,
                traits.get('neuroticism') is not None
            ]):
                print(f"      ⚠️  Skipping incomplete assessment")
                skipped_count += 1
                continue
            
            # Insert into assessment_history
            cursor.execute('''
                INSERT INTO assessment_history (
                    user_id, openness, conscientiousness, extraversion,
                    agreeableness, neuroticism, completed_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                traits['openness'],
                traits['conscientiousness'],
                traits['extraversion'],
                traits['agreeableness'],
                traits['neuroticism'],
                completed_at or datetime.now().isoformat(),
                f"Migrated from Insights Dashboard (completed {completed_at})"
            ))
            
            migrated_count += 1
            
    except Exception as e:
        print(f"      ❌ Error processing user {user_id}: {e}")
        error_count += 1

conn.commit()

print()
print(f"   ✅ Migration complete:")
print(f"      - Migrated: {migrated_count} assessments")
print(f"      - Skipped (duplicates): {skipped_count} assessments")
print(f"      - Errors: {error_count} assessments")

print()

# Step 4: Verify
print("✅ Step 4: Verifying deployment...")
cursor.execute('SELECT COUNT(*) FROM assessment_history')
final_count = cursor.fetchone()[0]
print(f"   Total records in assessment_history: {final_count}")
print(f"   New records added: {final_count - existing_count}")

cursor.execute('''
    SELECT user_id, COUNT(*) as count
    FROM assessment_history
    GROUP BY user_id
    ORDER BY count DESC
    LIMIT 5
''')

print()
print("   Top users by assessment count:")
for user_id, count in cursor.fetchall():
    print(f"      User {user_id}: {count} assessment(s)")

conn.close()

print()
print("=" * 80)
print("✅ DEPLOYMENT COMPLETE!")
print("=" * 80)
print()
print("Next steps:")
print("1. Test the /personality-test page")
print("2. Verify history chart shows multiple assessments")
print("3. Monitor server logs for any issues")
