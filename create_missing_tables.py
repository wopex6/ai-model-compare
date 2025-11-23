#!/usr/bin/env python3
"""
Create Missing Tables: conversations and psychology_sessions
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'integrated_users.db'

def create_missing_tables():
    """Create the two missing tables"""
    print("=" * 80)
    print("CREATING MISSING TABLES")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check and create conversations table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'")
        if not cursor.fetchone():
            print("📝 Creating table: conversations")
            cursor.execute('''
                CREATE TABLE conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            print("   ✅ conversations table created!")
        else:
            print("✅ conversations table already exists")
        
        # Check and create psychology_sessions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='psychology_sessions'")
        if not cursor.fetchone():
            print("📝 Creating table: psychology_sessions")
            cursor.execute('''
                CREATE TABLE psychology_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_data TEXT,
                    current_question INTEGER DEFAULT 0,
                    is_complete INTEGER DEFAULT 0,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            print("   ✅ psychology_sessions table created!")
        else:
            print("✅ psychology_sessions table already exists")
        
        # Create indexes for better performance
        print()
        print("📝 Creating indexes...")
        
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)')
            print("   ✅ Index on conversations.user_id")
        except:
            pass
        
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_psychology_sessions_user ON psychology_sessions(user_id)')
            print("   ✅ Index on psychology_sessions.user_id")
        except:
            pass
        
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_psychology_sessions_complete ON psychology_sessions(is_complete)')
            print("   ✅ Index on psychology_sessions.is_complete")
        except:
            pass
        
        conn.commit()
        
        print()
        print("=" * 80)
        print("✅ ALL MISSING TABLES CREATED!")
        print("=" * 80)
        print()
        
        # Verify
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("📊 Current Tables:")
        for i, table in enumerate(tables, 1):
            if not table.startswith('sqlite_'):
                print(f"   {i}. {table}")
        
        print()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n🚀 Creating missing database tables...")
    print()
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        exit(1)
    
    success = create_missing_tables()
    
    if success:
        print("=" * 80)
        print("✅ COMPLETE! Reload your web app:")
        print("   touch /var/www/trabcd_pythonanywhere_com_wsgi.py")
        print("=" * 80)
        print()
    else:
        print("❌ Failed to create tables")
