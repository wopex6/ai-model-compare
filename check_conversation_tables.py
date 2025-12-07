"""Check what conversation/message tables exist"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 80)
print("EXISTING TABLES IN DATABASE")
print("=" * 80)
print()

cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' 
    ORDER BY name
''')

tables = cursor.fetchall()

print(f"Found {len(tables)} tables:")
print()

for table in tables:
    table_name = table[0]
    
    # Count rows
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    
    print(f"📋 {table_name:30} ({count} rows)")

print()
print("=" * 80)
print("CONVERSATION/MESSAGE RELATED TABLES")
print("=" * 80)
print()

# Look for tables with conversation or message in name
message_tables = [t[0] for t in tables if 'message' in t[0].lower() or 'conversation' in t[0].lower() or 'history' in t[0].lower()]

for table_name in message_tables:
    print(f"\n📋 {table_name}:")
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    
    for col in columns:
        print(f"   - {col[1]:25} {col[2]}")
    
    # Show sample data
    cursor.execute(f'SELECT * FROM {table_name} LIMIT 3')
    rows = cursor.fetchall()
    if rows:
        print(f"\n   Sample data ({len(rows)} rows):")
        for row in rows[:2]:
            print(f"   {row}")

conn.close()
