import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Find personality-related tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print("All tables:")
for table in tables:
    print(f"  - {table}")

print("\nPersonality-related tables:")
personality_tables = [t for t in tables if 'personal' in t.lower() or 'trait' in t.lower() or 'psychology' in t.lower()]
for table in personality_tables:
    print(f"\n{table}:")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()
