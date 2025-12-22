import sqlite3
from datetime import datetime

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("=" * 60)
print("RECENT USER ACTIVITY LOG")
print("=" * 60)
cursor.execute('''
    SELECT id, user_id, activity_type, last_activity_at 
    FROM user_activity_log 
    ORDER BY last_activity_at DESC 
    LIMIT 20
''')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User: {row[1]}, Type: {row[2]}, Time: {row[3]}")

print("\n" + "=" * 60)
print("RECENT AUTOMATED GREETINGS")
print("=" * 60)
cursor.execute('''
    SELECT id, user_id, greeting_type, sent_at, greeting_message 
    FROM automated_greetings 
    ORDER BY sent_at DESC 
    LIMIT 10
''')
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"ID: {row[0]}, User: {row[1]}, Type: {row[2]}, Time: {row[3]}")
        print(f"  Message: {row[4][:80]}...")
else:
    print("No greetings found in database")

print("\n" + "=" * 60)
print("USER GREETING PREFERENCES")
print("=" * 60)
cursor.execute('''
    SELECT user_id, enabled, preferred_time_hour, inactivity_minutes,
           last_daily_greeting, last_inactivity_greeting
    FROM user_greeting_preferences
''')
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"User: {row[0]}, Enabled: {row[1]}, Preferred Hour: {row[2]}, Inactivity Min: {row[3]}")
        print(f"  Last Daily: {row[4]}, Last Inactivity: {row[5]}")
else:
    print("No preferences found - will use defaults")

print("\n" + "=" * 60)
print("RECENT MESSAGES (17:00-17:40)")
print("=" * 60)
cursor.execute('''
    SELECT id, user_id, user_message, timestamp 
    FROM domain_character_history 
    WHERE timestamp >= '2025-12-21 17:00:00'
    AND timestamp <= '2025-12-21 17:40:00'
    ORDER BY timestamp DESC
''')
for row in cursor.fetchall():
    print(f"ID: {row[0]}, User: {row[1]}, Time: {row[3]}")
    print(f"  Message: {row[2][:80] if row[2] else 'None'}...")

conn.close()
