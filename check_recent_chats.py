import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT id, session_id, title, created_at 
    FROM ai_conversations 
    WHERE user_id = 23 
    ORDER BY id DESC 
    LIMIT 20
''')

print("Most recent 20 conversations:")
print("=" * 80)
for row in cursor.fetchall():
    print(f"ID: {row[0]:4d} | Session: {row[1]:50s} | Title: {row[2]}")

conn.close()
