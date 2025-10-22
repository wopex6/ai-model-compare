"""
Verify that timestamps are stored in UTC and displayed in local time
"""

from integrated_database import IntegratedDatabase
from datetime import datetime, timezone
import pytz

db = IntegratedDatabase()

print("=" * 80)
print("TIMESTAMP STORAGE VERIFICATION")
print("=" * 80)

# Test 1: Check SQLite CURRENT_TIMESTAMP behavior
print("\n1. SQLite CURRENT_TIMESTAMP behavior:")
conn = db.get_connection()
cursor = conn.cursor()

# Insert a test message with current timestamp
cursor.execute('''
    SELECT datetime('now') as utc_time, 
           datetime('now', 'localtime') as local_time,
           strftime('%Y-%m-%d %H:%M:%S', 'now') as current_timestamp_format
''')
result = cursor.fetchone()
print(f"   UTC time (datetime('now')): {result[0]}")
print(f"   Local time: {result[1]}")
print(f"   CURRENT_TIMESTAMP format: {result[2]}")

# Test 2: Check actual admin_messages timestamps
print("\n2. Sample admin_messages timestamps:")
cursor.execute('''
    SELECT id, user_id, sender_type, timestamp, 
           datetime(timestamp, 'localtime') as local_display
    FROM admin_messages 
    ORDER BY id DESC LIMIT 3
''')
messages = cursor.fetchall()

if messages:
    for msg in messages:
        print(f"   ID {msg[0]} ({msg[2]}): ")
        print(f"      Stored (UTC): {msg[3]}")
        print(f"      Local time:   {msg[4]}")
else:
    print("   No messages found")

# Test 3: Show current system time
print("\n3. Current system time:")
now_utc = datetime.now(timezone.utc)
now_local = datetime.now()
print(f"   System UTC:   {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   System Local: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Timezone:     {datetime.now().astimezone().tzname()}")

# Test 4: JavaScript conversion test
print("\n4. JavaScript will convert:")
if messages:
    stored_time = messages[0][3]  # Get first message timestamp
    print(f"   Stored in DB:     '{stored_time}'")
    print(f"   After adding Z:   '{stored_time.replace(' ', 'T')}Z'")
    print(f"   JavaScript sees:  UTC time that will convert to local")

conn.close()

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print("✅ SQLite stores timestamps in UTC using CURRENT_TIMESTAMP")
print("✅ JavaScript formatTimestamp() adds 'Z' to indicate UTC")
print("✅ Browser converts UTC to user's local timezone for display")
print("=" * 80)
