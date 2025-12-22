import sqlite3
from datetime import datetime

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 80)
print("MESSAGES TABLE STRUCTURE")
print("=" * 80)
cursor.execute("PRAGMA table_info(messages)")
columns = cursor.fetchall()
print("Columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n" + "=" * 80)
print("COORDINATOR MESSAGES FOR USER 66")
print("=" * 80)

# Get messages - need to join with ai_conversations to get user_id and character_id
cursor.execute('''
    SELECT m.id, m.sender_type, m.content, m.timestamp, c.character_id, c.user_id
    FROM messages m
    JOIN ai_conversations c ON m.conversation_id = c.id
    WHERE c.user_id = 66 AND c.character_id = 'coordinator'
    ORDER BY m.timestamp DESC
    LIMIT 30
''')

rows = cursor.fetchall()
print(f"\nFound {len(rows)} messages:")
print()

for i, row in enumerate(rows, 1):
    msg_id, sender_type, content, timestamp, character_id, user_id = row
    print(f"{i}. [{timestamp}] {sender_type.upper()}")
    print(f"    {content[:100] if content else 'None'}...")
    print()

# Check for any automated greetings
print("=" * 80)
print("AUTOMATED GREETINGS (should these be in messages?)")
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
    print(f"\n[{row[2]}] {row[1].upper()} GREETING")
    print(f"  {row[3][:100]}...")

conn.close()
