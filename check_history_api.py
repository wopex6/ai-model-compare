import sqlite3
import json

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 80)
print("RAW MESSAGES FOR COORDINATOR (user 66)")
print("=" * 80)

# Get messages from the messages table 
cursor.execute('''
    SELECT m.id, m.sender_type, m.content, m.timestamp, c.character_id
    FROM messages m
    JOIN ai_conversations c ON m.conversation_id = c.id
    WHERE c.user_id = 66 AND c.character_id = 'coordinator'
    ORDER BY m.timestamp DESC
    LIMIT 15
''')

rows = cursor.fetchall()
print(f"\nFound {len(rows)} messages:")
for row in rows:
    msg_id, sender_type, content, timestamp, character_id = row
    print(f"\nID: {msg_id}, Sender: {sender_type}, Time: {timestamp}")
    print(f"  Content: {content[:60] if content else 'None'}...")

# Simulate how app.py pairs them
print("\n" + "=" * 80)
print("PAIRED HISTORY (as sent to frontend)")
print("=" * 80)

# Get messages in ASC order for pairing
cursor.execute('''
    SELECT m.id, m.sender_type, m.content, m.timestamp
    FROM messages m
    JOIN ai_conversations c ON m.conversation_id = c.id
    WHERE c.user_id = 66 AND c.character_id = 'coordinator'
    ORDER BY m.timestamp ASC
''')

messages = cursor.fetchall()
history = []
for msg in messages:
    history.append({
        'id': msg[0],
        'user_message': msg[2] if msg[1] == 'user' else '',
        'ai_response': msg[2] if msg[1] == 'assistant' else '',
        'timestamp': msg[3],
        'sender_type': msg[1]
    })

# Group consecutive user/assistant messages into pairs
paired_history = []
i = 0
while i < len(history):
    entry = {'id': None, 'user_message': '', 'ai_response': '', 'timestamp': ''}
    
    # Get user message
    if i < len(history) and history[i].get('user_message'):
        entry['user_message'] = history[i]['user_message']
        entry['timestamp'] = history[i]['timestamp']
        entry['id'] = history[i]['id']
        i += 1
    
    # Get assistant response
    if i < len(history) and history[i].get('ai_response'):
        entry['ai_response'] = history[i]['ai_response']
        if not entry['timestamp']:
            entry['timestamp'] = history[i]['timestamp']
        if not entry['id']:
            entry['id'] = history[i]['id']
        i += 1
    
    if entry['user_message'] or entry['ai_response']:
        paired_history.append(entry)

print(f"\nPaired into {len(paired_history)} entries:")
for i, entry in enumerate(paired_history[-5:], 1):  # Last 5
    print(f"\nEntry {i}:")
    print(f"  Timestamp: {entry['timestamp']}")
    print(f"  User: {entry['user_message'][:50] if entry['user_message'] else 'EMPTY'}...")
    print(f"  AI: {entry['ai_response'][:50] if entry['ai_response'] else 'EMPTY'}...")

conn.close()
