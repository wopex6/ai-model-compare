#!/usr/bin/env python3
"""
Test delete functionality and check database tables
"""

import sqlite3

def check_tables():
    print("🔍 Checking database tables...")
    print("=" * 60)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
        
        # Get schema for each table
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"    Columns: {', '.join([col[1] for col in columns])}")
    
    print("\n" + "=" * 60)
    
    # Check if ai_messages table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_messages'")
    if cursor.fetchone():
        print("✅ ai_messages table EXISTS")
        
        # Count messages
        cursor.execute("SELECT COUNT(*) FROM ai_messages")
        count = cursor.fetchone()[0]
        print(f"   Total messages: {count}")
    else:
        print("❌ ai_messages table DOES NOT EXIST")
    
    conn.close()

def test_delete():
    print("\n🧪 Testing delete function...")
    print("=" * 60)
    
    from integrated_database import IntegratedDatabase
    
    db = IntegratedDatabase()
    
    # Get a test conversation
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session_id, user_id, title 
        FROM ai_conversations 
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print("❌ No conversations found to test with")
        return
    
    session_id, user_id, title = result
    print(f"Found test conversation:")
    print(f"  Session ID: {session_id}")
    print(f"  User ID: {user_id}")
    print(f"  Title: {title}")
    
    # Try to delete
    try:
        print("\nAttempting delete...")
        success = db.delete_conversation(session_id, user_id)
        
        if success:
            print("✅ Delete succeeded!")
        else:
            print("❌ Delete failed - conversation not found or unauthorized")
    except Exception as e:
        print(f"❌ Delete error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables()
    
    response = input("\nRun delete test? (yes/no): ")
    if response.lower() == 'yes':
        test_delete()
