import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Check table schema
cursor.execute("PRAGMA table_info(explicit_context)")
print("=" * 80)
print("TABLE SCHEMA:")
print("=" * 80)
for row in cursor.fetchall():
    print(row)

print("\n" + "=" * 80)
print("UNIQUE CONSTRAINTS:")
print("=" * 80)
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='explicit_context'")
print(cursor.fetchone()[0])

print("\n" + "=" * 80)
print("ALL MARCUS CONTEXT (including inactive):")
print("=" * 80)

# Check ALL context for marcus (including inactive)
cursor.execute('''
    SELECT id, context_type, context_key, context_value, active, timestamp 
    FROM explicit_context 
    WHERE user_id = 23 AND character = "marcus"
    ORDER BY timestamp DESC
''')

for row in cursor.fetchall():
    id_val, context_type, context_key, context_value, active, timestamp = row
    active_str = "ACTIVE" if active else "inactive"
    print(f"ID={id_val:3d} | {timestamp[:19]} | {context_type:15s}.{context_key:15s} = {context_value[:25]:25s} | {active_str}")

conn.close()
