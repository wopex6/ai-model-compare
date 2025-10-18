import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM ai_conversations WHERE session_id = ?', ('session_25_20251018_205138_895418_4060',))
count = cursor.fetchone()[0]

if count == 0:
    print("✅ Conversation successfully deleted from database!")
else:
    print(f"❌ Conversation still exists ({count} entries)")

conn.close()
