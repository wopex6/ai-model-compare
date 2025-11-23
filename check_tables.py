import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if specific tables exist
important_tables = [
    'messages',
    'ai_conversations',
    'user_interactions',
    'admin_messages',
    'personality_assessments',
    'psychology_traits',
    'user_profiles',
    'email_verification_codes'
]

print("\nChecking important tables:")
existing = [t[0] for t in tables]
for table in important_tables:
    status = "✅ EXISTS" if table in existing else "❌ MISSING"
    print(f"  {table}: {status}")

conn.close()
