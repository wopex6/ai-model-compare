import sqlite3
from datetime import datetime

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 80)
print("COORDINATOR CONVERSATION HISTORY FOR USER 66")
print("=" * 80)

# Check ai_conversations table
cursor.execute('''
    SELECT id, user_message, ai_response, timestamp, character_id
    FROM ai_conversations
    WHERE user_id = 66 AND character_id = 'coordinator'
    ORDER BY timestamp DESC
    LIMIT 20
''')

rows = cursor.fetchall()
if rows:
    print(f"\nFound {len(rows)} messages in ai_conversations:")
    for row in rows:
        print(f"\nID: {row[0]}, Time: {row[3]}")
        print(f"  User: {row[1][:60] if row[1] else 'None'}...")
        print(f"  AI: {row[2][:60] if row[2] else 'None'}...")
else:
    print("\nNo messages found in ai_conversations")

# Check if there's a domain_characters table
cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name LIKE '%domain%'
''')
tables = cursor.fetchall()
print(f"\n\nDomain-related tables: {[t[0] for t in tables]}")

# Try to find the correct table for domain character messages
for table_name in [t[0] for t in tables]:
    print(f"\n\nChecking table: {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"Columns: {[c[1] for c in columns]}")
    
    # Try to get recent messages
    try:
        cursor.execute(f'''
            SELECT * FROM {table_name}
            WHERE user_id = 66
            ORDER BY timestamp DESC
            LIMIT 5
        ''')
        rows = cursor.fetchall()
        if rows:
            print(f"Found {len(rows)} recent messages")
            for row in rows:
                print(f"  {row}")
    except Exception as e:
        print(f"  Error querying: {e}")

conn.close()
