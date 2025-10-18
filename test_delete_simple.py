#!/usr/bin/env python3
from integrated_database import IntegratedDatabase
import sqlite3

db = IntegratedDatabase()

# Get a test conversation
conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT session_id, user_id, title 
    FROM ai_conversations 
    ORDER BY id DESC
    LIMIT 1
""")

result = cursor.fetchone()
conn.close()

if not result:
    print("❌ No conversations found")
else:
    session_id, user_id, title = result
    print(f"Testing delete on:")
    print(f"  Session: {session_id}")
    print(f"  User: {user_id}")
    print(f"  Title: {title}")
    
    try:
        success = db.delete_conversation(session_id, user_id)
        if success:
            print("\n✅ Delete succeeded!")
        else:
            print("\n❌ Delete failed - not found or unauthorized")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
