import sqlite3
from datetime import datetime

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 80)
print("COORDINATOR MESSAGES FOR USER 66")
print("=" * 80)

# Get messages from the messages table (used by integrated_db.get_character_messages)
cursor.execute('''
    SELECT id, sender_type, content, timestamp, session_id
    FROM messages
    WHERE user_id = 66 AND character_id = 'coordinator'
    ORDER BY timestamp DESC
    LIMIT 30
''')

rows = cursor.fetchall()
print(f"\nFound {len(rows)} messages in 'messages' table:")
print()

for i, row in enumerate(rows, 1):
    msg_id, sender_type, content, timestamp, session_id = row
    print(f"{i}. ID: {msg_id}, Type: {sender_type}, Time: {timestamp}")
    print(f"   Content: {content[:80] if content else 'None'}...")
    print()

# Check for any automated greetings that should appear
print("=" * 80)
print("AUTOMATED GREETINGS")
print("=" * 80)
cursor.execute('''
    SELECT id, greeting_type, sent_at, greeting_message
    FROM automated_greetings
    WHERE user_id = 66
    ORDER BY sent_at DESC
    LIMIT 5
''')

greeting_rows = cursor.fetchall()
print(f"\nFound {len(greeting_rows)} automated greetings:")
for row in greeting_rows:
    print(f"\nID: {row[0]}, Type: {row[1]}, Time: {row[2]}")
    print(f"  Message: {row[3][:80]}...")

conn.close()
