#!/usr/bin/env python3
"""Quick database inspection script"""

import sqlite3
import os

def check_database(db_path):
    """Check database structure and content"""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"📊 Database: {db_path}")
    print(f"📏 Size: {size_mb:.2f} MB")
    print(f"{'='*60}\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"📋 Tables ({len(tables)}):")
        print("-" * 60)
        
        for (table_name,) in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_count = len(columns)
            
            print(f"\n✅ {table_name}")
            print(f"   Rows: {count:,}")
            print(f"   Columns: {col_count}")
            
            # Show first few column names
            col_names = [col[1] for col in columns[:5]]
            if len(columns) > 5:
                col_names_str = ', '.join(col_names) + f', ... (+{len(columns)-5} more)'
            else:
                col_names_str = ', '.join(col_names)
            print(f"   Schema: {col_names_str}")
            
            # Show sample data for key tables
            if table_name == 'users' and count > 0:
                cursor.execute("SELECT id, username, created_at FROM users ORDER BY id DESC LIMIT 3")
                users = cursor.fetchall()
                print(f"   Recent users:")
                for uid, uname, created in users:
                    print(f"     - {uid}: {uname} (created: {created})")
            
            elif table_name == 'user_sessions' and count > 0:
                cursor.execute("SELECT DISTINCT character_id FROM user_sessions")
                chars = cursor.fetchall()
                print(f"   Characters: {', '.join([c[0] for c in chars])}")
            
            elif table_name == 'user_messages' and count > 0:
                cursor.execute("SELECT COUNT(*) as msg_count, character_id FROM user_messages GROUP BY character_id ORDER BY msg_count DESC LIMIT 3")
                char_msgs = cursor.fetchall()
                print(f"   Messages by character:")
                for msg_count, char_id in char_msgs:
                    print(f"     - {char_id}: {msg_count} messages")
        
        conn.close()
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    # Check main databases
    databases = [
        'integrated_users.db',
        'integrated_database.db',
        'integrated_chat.db',
        'smart_response.db'
    ]
    
    for db in databases:
        if os.path.exists(db):
            check_database(db)
        else:
            print(f"⏭️  Skipping {db} (not found)")
