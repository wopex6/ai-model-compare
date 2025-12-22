import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 60)
print("GREETING MESSAGES IN MESSAGES TABLE")
print("=" * 60)

cursor.execute('''
    SELECT m.id, m.sender_type, m.content, m.timestamp, m.metadata 
    FROM messages m 
    JOIN ai_conversations c ON m.conversation_id = c.id 
    WHERE c.user_id = 66 AND c.character_id = 'coordinator' 
    AND m.metadata LIKE '%automated_greeting%'
    ORDER BY m.timestamp DESC 
    LIMIT 5
''')

rows = cursor.fetchall()
print(f"\nFound {len(rows)} greeting messages stored in messages table:")
for row in rows:
    print(f"\nTime: {row[3]}")
    print(f"Content: {row[2][:80]}...")
    print(f"Metadata: {row[4][:60]}...")

conn.close()
