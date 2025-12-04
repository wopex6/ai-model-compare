"""
Check actual assessment count in database
"""

import sqlite3
from pathlib import Path
import json

DB_PATH = Path(__file__).parent / 'integrated_users.db'

print("=" * 80)
print("CHECKING ASSESSMENT COUNT")
print("=" * 80)
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check assessment_history table
print("📊 ASSESSMENT_HISTORY TABLE:")
cursor.execute('''
    SELECT id, user_id, openness, conscientiousness, extraversion, 
           agreeableness, neuroticism, completed_at, notes
    FROM assessment_history
    ORDER BY user_id, completed_at
''')

rows = cursor.fetchall()
print(f"Total assessments: {len(rows)}")
print()

# Group by user
user_assessments = {}
for row in rows:
    user_id = row[1]
    if user_id not in user_assessments:
        user_assessments[user_id] = []
    user_assessments[user_id].append(row)

for user_id, assessments in user_assessments.items():
    print(f"User {user_id}: {len(assessments)} assessment(s)")
    for i, row in enumerate(assessments, 1):
        print(f"  {i}. ID={row[0]}, Date={row[7]}")
        print(f"     O={row[2]:.2f}, C={row[3]:.2f}, E={row[4]:.2f}, A={row[5]:.2f}, N={row[6]:.2f}")
        if row[8]:
            print(f"     Notes: {row[8][:60]}...")
    print()

# Check for duplicates by date
print("=" * 80)
print("CHECKING FOR DUPLICATES:")
print("=" * 80)
print()

cursor.execute('''
    SELECT user_id, completed_at, COUNT(*) as count
    FROM assessment_history
    GROUP BY user_id, completed_at
    HAVING COUNT(*) > 1
''')

duplicates = cursor.fetchall()
if duplicates:
    print(f"⚠️  Found {len(duplicates)} duplicate entries:")
    for row in duplicates:
        print(f"   User {row[0]}, Date {row[1]}: {row[2]} duplicates")
else:
    print("✅ No duplicates found")

print()

# Check the exact timestamps for user 23
print("=" * 80)
print("USER 23 DETAILED TIMESTAMPS:")
print("=" * 80)
print()

cursor.execute('''
    SELECT id, completed_at, started_at, openness, conscientiousness
    FROM assessment_history
    WHERE user_id = 23
    ORDER BY completed_at
''')

user23_rows = cursor.fetchall()
print(f"User 23 has {len(user23_rows)} assessment(s):")
for row in user23_rows:
    print(f"  ID={row[0]}")
    print(f"    Completed: {row[1]}")
    print(f"    Started:   {row[2]}")
    print(f"    O={row[3]:.2f}, C={row[4]:.2f}")
    print()

conn.close()
