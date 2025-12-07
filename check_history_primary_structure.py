"""Check history_primary table structure and fix if needed"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 80)
print("CHECKING HISTORY_PRIMARY TABLE")
print("=" * 80)
print()

# Get schema
cursor.execute('PRAGMA table_info(history_primary)')
columns = cursor.fetchall()

print("📋 Current Schema:")
col_names = []
for col in columns:
    col_names.append(col[1])
    print(f"   {col[1]:30} {col[2]:15} {'NOT NULL' if col[3] else ''}")
print()

# Check if 'role' column exists
if 'role' in col_names:
    print("✅ 'role' column exists")
elif 'message' in col_names:
    print("⚠️  Has 'message' column but no 'role' column")
elif 'user_message' in col_names:
    print("⚠️  Has 'user_message' column but no 'role' column")
    print("   Structure is: user_message + assistant_response (separate columns)")
    print()
    print("   TraitInference expects: message + role columns")
    print()
    print("   Options:")
    print("   1. Add message and role columns")
    print("   2. Modify TraitInference to use user_message column")
print()

# Sample data
print("📊 Sample Data (first 3 rows):")
cursor.execute('SELECT * FROM history_primary LIMIT 3')
rows = cursor.fetchall()

for i, row in enumerate(rows, 1):
    print(f"\nRow {i}:")
    for col_name, value in zip(col_names, row):
        if isinstance(value, str) and len(value) > 60:
            value = value[:60] + "..."
        print(f"   {col_name:25} {value}")

print()

# Count messages per user
print("📊 Message count per user:")
if 'user_id' in col_names:
    cursor.execute('SELECT user_id, COUNT(*) as count FROM history_primary GROUP BY user_id')
    for row in cursor.fetchall():
        print(f"   User {row[0]}: {row[1]} rows")

conn.close()
