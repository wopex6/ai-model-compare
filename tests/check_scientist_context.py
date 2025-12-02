import sqlite3

db = sqlite3.connect('integrated_users.db')
cursor = db.cursor()

print("\n" + "="*80)
print("RECENT CONTEXT FOR SCIENTIST CHARACTER")
print("="*80)

cursor.execute('''
    SELECT user_id, context_type, context_key, context_value, active, timestamp 
    FROM explicit_context 
    WHERE character="scientist" 
    ORDER BY timestamp DESC 
    LIMIT 10
''')

rows = cursor.fetchall()

if rows:
    for r in rows:
        user_id, ctx_type, ctx_key, ctx_value, active, timestamp = r
        status = "ACTIVE" if active else "inactive"
        print(f"User {user_id}: {ctx_type}.{ctx_key} = {ctx_value[:40]}")
        print(f"  Status: {status}, Time: {timestamp[:19]}")
        print()
else:
    print("NO CONTEXT FOUND FOR SCIENTIST CHARACTER!")
    print("\nThis means the explicit context was NOT extracted during your test.")
    print("Possible reasons:")
    print("1. You tested with a different character")
    print("2. The messages didn't match extraction patterns")
    print("3. The app isn't running or crashed")

db.close()

print("="*80)
