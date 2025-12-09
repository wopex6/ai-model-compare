#!/usr/bin/env python3
"""
Database Update Script
Updates the integrated_users.db database for PythonAnywhere deployment
"""

import sqlite3
import json
from datetime import datetime

def update_database():
    """Update database with any necessary schema or data changes"""
    
    print("="*60)
    print("  Database Update for PythonAnywhere")
    print("="*60)
    print()
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    updates_made = []
    
    # 1. Check if Smart Response tables exist
    print("1. Checking Smart Response tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interaction_history'")
    if not cursor.fetchone():
        print("   ⚠️  Creating interaction_history table...")
        cursor.execute('''
            CREATE TABLE interaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response_type TEXT NOT NULL,
                character TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        updates_made.append("Created interaction_history table")
    else:
        print("   ✅ interaction_history table exists")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_learning_profiles'")
    if not cursor.fetchone():
        print("   ⚠️  Creating user_learning_profiles table...")
        cursor.execute('''
            CREATE TABLE user_learning_profiles (
                user_id INTEGER PRIMARY KEY,
                profile_data TEXT,
                interaction_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        updates_made.append("Created user_learning_profiles table")
    else:
        print("   ✅ user_learning_profiles table exists")
    
    # 2. Check AI Budget tables
    print("\n2. Checking AI Budget tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage_log'")
    if not cursor.fetchone():
        print("   ⚠️  Creating ai_usage_log table...")
        cursor.execute('''
            CREATE TABLE ai_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                call_type TEXT NOT NULL,
                character TEXT,
                user_id INTEGER,
                user_role TEXT,
                success BOOLEAN,
                tokens INTEGER,
                cost REAL,
                response_time REAL,
                error TEXT,
                context_length INTEGER,
                metadata TEXT
            )
        ''')
        updates_made.append("Created ai_usage_log table")
    else:
        print("   ✅ ai_usage_log table exists")
    
    # 3. Check Dual-Layer History tables
    print("\n3. Checking Dual-Layer History tables...")
    required_tables = ['history_primary', 'history_secondary', 'history_progress']
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if cursor.fetchone():
            print(f"   ✅ {table} table exists")
        else:
            print(f"   ⚠️  {table} table missing")
    
    # 4. Check user_sessions for character_id column
    print("\n4. Checking user_sessions table...")
    cursor.execute("PRAGMA table_info(user_sessions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'character_id' not in columns:
        print("   ⚠️  Adding character_id column to user_sessions...")
        try:
            cursor.execute("ALTER TABLE user_sessions ADD COLUMN character_id TEXT")
            updates_made.append("Added character_id column to user_sessions")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e):
                print(f"   ❌ Error: {e}")
    else:
        print("   ✅ character_id column exists")
    
    # 5. Verify critical data
    print("\n5. Verifying database content...")
    
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"   📊 Users: {user_count}")
    
    cursor.execute("SELECT COUNT(*) FROM history_primary")
    msg_count = cursor.fetchone()[0]
    print(f"   📊 Messages: {msg_count}")
    
    cursor.execute("SELECT COUNT(*) FROM interaction_history")
    interaction_count = cursor.fetchone()[0]
    print(f"   📊 Smart Response interactions: {interaction_count}")
    
    cursor.execute("SELECT COUNT(*) FROM ai_usage_log")
    ai_count = cursor.fetchone()[0]
    print(f"   📊 AI usage logs: {ai_count}")
    
    # 6. Optimize database
    print("\n6. Optimizing database...")
    cursor.execute("VACUUM")
    cursor.execute("ANALYZE")
    print("   ✅ Database optimized")
    updates_made.append("Database optimized (VACUUM + ANALYZE)")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    # Summary
    print("\n" + "="*60)
    print("  Update Summary")
    print("="*60)
    
    if updates_made:
        print("\n✅ Updates applied:")
        for update in updates_made:
            print(f"   - {update}")
    else:
        print("\n✅ Database is already up to date!")
        print("   No changes needed.")
    
    print(f"\n📊 Database statistics:")
    print(f"   - {user_count} users")
    print(f"   - {msg_count} messages")
    print(f"   - {interaction_count} smart response interactions")
    print(f"   - {ai_count} AI usage logs")
    
    print("\n✅ Database ready for PythonAnywhere!")
    print()
    
    return len(updates_made) > 0

if __name__ == "__main__":
    try:
        updated = update_database()
        
        if updated:
            print("📋 Next steps:")
            print("   1. Run: .\\upload_database_to_pythonanywhere.ps1")
            print("   2. Upload the database to PythonAnywhere")
            print("   3. Reload your web app")
        else:
            print("📋 To upload to PythonAnywhere:")
            print("   1. Run: .\\upload_database_to_pythonanywhere.ps1")
            print("   2. Choose option 1 for manual upload")
            print("   3. Upload via Files tab")
            print("   4. Reload web app")
        
        print()
        
    except Exception as e:
        print(f"\n❌ Error updating database: {e}")
        import traceback
        traceback.print_exc()
