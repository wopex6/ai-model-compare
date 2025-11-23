import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Get schema of admin_messages table
cursor.execute("PRAGMA table_info(admin_messages)")
columns = cursor.fetchall()

print("admin_messages table schema:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
