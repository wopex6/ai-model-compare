import sqlite3
from datetime import datetime

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 60)
print("GREETING SENT AT TIME")
print("=" * 60)
cursor.execute('''
    SELECT id, greeting_type, sent_at, greeting_message 
    FROM automated_greetings 
    WHERE user_id = 66 
    ORDER BY sent_at DESC 
    LIMIT 3
''')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, Type: {row[1]}")
    print(f"Sent at (DB): {row[2]}")
    print(f"Message: {row[3][:60]}...")
    print()

print("=" * 60)
print("LAST INACTIVITY GREETING IN PREFERENCES")
print("=" * 60)
cursor.execute('''
    SELECT last_inactivity_greeting 
    FROM user_greeting_preferences 
    WHERE user_id = 66
''')
result = cursor.fetchone()
print(f"Last inactivity: {result[0] if result else 'None'}")

conn.close()
