"""Check the current inferred_traits table structure and data"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 80)
print("CURRENT INFERRED_TRAITS TABLE")
print("=" * 80)
print()

# Get schema
cursor.execute('PRAGMA table_info(inferred_traits)')
columns = cursor.fetchall()

print("📋 Schema:")
for col in columns:
    print(f"   {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else ''} {f'DEFAULT {col[4]}' if col[4] else ''}")
print()

# Get sample data
cursor.execute('SELECT * FROM inferred_traits LIMIT 5')
rows = cursor.fetchall()

print(f"📊 Sample Data ({len(rows)} rows):")
for row in rows:
    print(f"   {row}")
print()

# Check if Big 5 trait columns exist
big5_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
col_names = [col[1] for col in columns]

print("🔍 Checking for Big 5 columns:")
for trait in big5_traits:
    exists = trait in col_names
    print(f"   {trait:20} {'✅' if exists else '❌'}")
print()

conn.close()

print("=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print()
print("The existing inferred_traits table has a different structure.")
print("We need to either:")
print("  1. Create a new table with Big 5 columns (recommended)")
print("  2. Adapt PersonalityResolver to work with existing structure")
print()
print("Let's create a new 'inferred_personality' table with correct structure!")
