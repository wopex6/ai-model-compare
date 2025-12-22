import sqlite3
from datetime import datetime

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 80)
print("FINDING COORDINATOR MESSAGES")
print("=" * 80)

# First, find all tables
cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table'
    ORDER BY name
''')
tables = cursor.fetchall()
print(f"\nAll tables in database:")
for t in tables:
    print(f"  - {t[0]}")

# Check ai_conversations structure
print("\n" + "=" * 80)
print("AI_CONVERSATIONS TABLE STRUCTURE")
print("=" * 80)
cursor.execute("PRAGMA table_info(ai_conversations)")
columns = cursor.fetchall()
print("Columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Get recent ai_conversations for coordinator
print("\n" + "=" * 80)
print("RECENT COORDINATOR MESSAGES (ai_conversations)")
print("=" * 80)
cursor.execute('''
    SELECT id, message, response, timestamp, character_id
    FROM ai_conversations
    WHERE user_id = 66 AND character_id = 'coordinator'
    ORDER BY timestamp DESC
    LIMIT 10
''')
rows = cursor.fetchall()
if rows:
    print(f"\nFound {len(rows)} messages:")
    for row in rows:
        print(f"\nID: {row[0]}, Character: {row[4]}, Time: {row[3]}")
        print(f"  User: {row[1][:80] if row[1] else 'None'}...")
        print(f"  AI: {row[2][:80] if row[2] else 'None'}...")
else:
    print("No messages found")

# Check for domain character tables
print("\n" + "=" * 80)
print("DOMAIN CHARACTER TABLES")
print("=" * 80)
domain_tables = [t[0] for t in tables if 'domain' in t[0].lower()]
for table in domain_tables:
    print(f"\nTable: {table}")
    cursor.execute(f"PRAGMA table_info({table})")
    cols = cursor.fetchall()
    print(f"  Columns: {[c[1] for c in cols]}")
    
    # Try to count records
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = 66")
        count = cursor.fetchone()[0]
        print(f"  Records for user 66: {count}")
        
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = 66 ORDER BY timestamp DESC LIMIT 3")
            rows = cursor.fetchall()
            print(f"  Recent records:")
            for row in rows:
                print(f"    {row}")
    except Exception as e:
        print(f"  Error: {e}")

conn.close()
