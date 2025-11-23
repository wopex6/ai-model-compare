#!/usr/bin/env python3
"""
Migration Script: Add admin_messages table if it doesn't exist
Run this on PythonAnywhere to fix "Failed to send message" error
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'integrated_users.db'

def migrate_admin_messages():
    """Add admin_messages table and related columns"""
    print("=" * 80)
    print("MIGRATION: Adding admin_messages table")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if admin_messages table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='admin_messages'
        """)
        
        if cursor.fetchone():
            print("⚠️  admin_messages table exists - checking for missing columns...")
            
            # Get current columns
            cursor.execute("PRAGMA table_info(admin_messages)")
            columns = {col[1] for col in cursor.fetchall()}
            
            # Check for missing columns
            required_columns = {
                'file_url': 'TEXT',
                'file_name': 'TEXT',
                'file_size': 'INTEGER',
                'reply_to': 'INTEGER'
            }
            
            missing_columns = []
            for col_name, col_type in required_columns.items():
                if col_name not in columns:
                    missing_columns.append((col_name, col_type))
            
            if missing_columns:
                print(f"📝 Adding {len(missing_columns)} missing columns...")
                for col_name, col_type in missing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE admin_messages ADD COLUMN {col_name} {col_type}")
                        print(f"   ✅ Added column: {col_name}")
                    except Exception as e:
                        print(f"   ⚠️  Column {col_name} might already exist: {e}")
                conn.commit()
                print("✅ Missing columns added!")
            else:
                print("✅ All columns exist - table is up to date!")
        else:
            print("📝 Creating admin_messages table...")
            
            # Create admin_messages table
            cursor.execute('''
                CREATE TABLE admin_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'admin')),
                    message TEXT,
                    is_read INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_url TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    reply_to INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (reply_to) REFERENCES admin_messages (id) ON DELETE SET NULL
                )
            ''')
            
            # Create index for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_admin_messages_user 
                ON admin_messages(user_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_admin_messages_read 
                ON admin_messages(is_read)
            ''')
            
            conn.commit()
            print("✅ admin_messages table created successfully!")
        
        # Verify table structure
        cursor.execute("PRAGMA table_info(admin_messages)")
        columns = cursor.fetchall()
        
        print("\n📋 Table Structure:")
        for col in columns:
            print(f"   - {col[1]}: {col[2]}")
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 80)
        print()
        print("🎉 Users can now send messages to admin!")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("\n🚀 Starting database migration...")
    print(f"📁 Database: {DB_PATH}")
    print()
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Make sure you're running this in the correct directory")
        exit(1)
    
    success = migrate_admin_messages()
    
    if success:
        print("✅ Migration successful! Restart your web app to apply changes.")
    else:
        print("❌ Migration failed! Check the error messages above.")
