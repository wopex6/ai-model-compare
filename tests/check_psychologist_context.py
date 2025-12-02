import sqlite3

db = sqlite3.connect('integrated_users.db')
cursor = db.cursor()

print("\n" + "="*80)
print("RECENT CONTEXT FOR PSYCHOLOGIST CHARACTER (Dr. Elena)")
print("="*80)

cursor.execute('''
    SELECT user_id, context_type, context_key, context_value, active, timestamp 
    FROM explicit_context 
    WHERE character="psychologist" 
    ORDER BY timestamp DESC 
    LIMIT 15
''')

rows = cursor.fetchall()

if rows:
    print(f"\nFound {len(rows)} context entries:\n")
    for r in rows:
        user_id, ctx_type, ctx_key, ctx_value, active, timestamp = r
        status = "ACTIVE" if active else "inactive"
        print(f"User {user_id}: {ctx_type}.{ctx_key} = {ctx_value[:40]}")
        print(f"  Status: {status}, Time: {timestamp[:19]}")
        print()
else:
    print("\n❌ NO CONTEXT FOUND FOR PSYCHOLOGIST CHARACTER!")
    print("\nThis means one of two things:")
    print("1. You tested with a different character")
    print("2. The messages you sent didn't match extraction patterns")
    print("3. The app crashed or didn't extract context")

db.close()

print("="*80)
