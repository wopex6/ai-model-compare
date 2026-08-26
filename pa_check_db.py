import sqlite3
import json
import re

conn = sqlite3.connect('pa_integrated_users.db')
c = conn.cursor()

c.execute('SELECT id, username, user_role FROM users')
users = c.fetchall()
print('Users:', users)

wai_ids = [u[0] for u in users if 'wai' in u[1].lower()]
print('Wai Tse user IDs:', wai_ids)

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [t[0] for t in c.fetchall()])

c.execute('SELECT id, user_id, title, conversation_data FROM ai_conversations')
convs = c.fetchall()
print('Total conversations:', len(convs))
for cid, uid, title, data in convs:
    print('  conv', cid, 'user', uid, 'title:', title)

c.execute('SELECT id, conversation_id, content FROM messages')
msgs = c.fetchall()
print('Total messages:', len(msgs))

health_keywords = ['dr. health', 'dr health', 'health', 'medical', 'report', 'lab']
health_msgs = [(m[0], m[1], m[2][:200] if m[2] else '') for m in msgs if m[2] and any(k in m[2].lower() for k in health_keywords)]
print('Health-related messages:', len(health_msgs))
for m in health_msgs[:20]:
    print('  msg', m[0], 'conv', m[1], ':', m[2])

if 'health_uploaded_documents' in [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'") ]:
    c.execute('SELECT id, user_id, filename, file_path FROM health_uploaded_documents')
    print('Health uploaded documents:', c.fetchall())

if 'health_profiles' in [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
    c.execute('SELECT id, user_id FROM health_profiles')
    print('Health profiles:', c.fetchall())

c.execute('SELECT id, title, conversation_data FROM ai_conversations WHERE user_id=1')
print('--- Wai Tse conversations (full data preview) ---')
for cid, title, data in c.fetchall():
    print(f'Conversation {cid}: {title}')
    try:
        print(json.dumps(json.loads(data or '{}'), indent=2, ensure_ascii=False)[:1500])
    except Exception as e:
        print('Error parsing JSON:', e)

c.execute("PRAGMA table_info(conversations)")
print('conversations schema:', c.fetchall())
c.execute('SELECT id, user_id, title, content FROM conversations WHERE user_id=1')
print('--- Wai Tse conversations table ---')
for row in c.fetchall():
    print(row)

conn.close()
