"""Debug script to check database contents"""
from integrated_database import IntegratedDatabase

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

print("\n=== CONVERSATIONS ===")
cursor.execute('''
    SELECT id, user_id, character_id, session_id, title, created_at
    FROM ai_conversations
    ORDER BY created_at DESC
    LIMIT 5
''')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User: {row[1]}, Char: {row[2]}, Session: {row[3]}")
    print(f"  Title: {row[4]}, Created: {row[5]}")

print("\n=== MESSAGES (Last 10) ===")
cursor.execute('''
    SELECT c.character_id, m.sender_type, m.content, m.timestamp, m.metadata
    FROM messages m
    JOIN ai_conversations c ON m.conversation_id = c.id
    ORDER BY m.timestamp DESC
    LIMIT 10
''')
for row in cursor.fetchall():
    print(f"\n{row[0]} | {row[1]} | {row[3]}")
    print(f"  Content: {row[2][:100]}...")
    print(f"  Metadata: {row[4]}")

print("\n=== USER 1 SCIENTIST MESSAGES ===")
messages = db.get_character_messages(user_id=1, character_id='scientist')
print(f"Found {len(messages)} messages:")
for msg in messages:
    print(f"\n{msg['sender_type']} | {msg['timestamp']}")
    print(f"  {msg['content'][:100]}...")

conn.close()
