"""
Migration script to create analytics tables on the server.
Run this on PythonAnywhere to initialize the analytics database.
"""
import sqlite3
import os

DB_PATH = 'integrated_users.db'

def migrate():
    print("Creating analytics tables...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create user_activity_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            action_data TEXT,
            page TEXT,
            session_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ user_activity_log table created")
    
    # Create conversation_analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            character_id TEXT,
            message_count INTEGER DEFAULT 0,
            avg_message_length REAL,
            session_duration_seconds INTEGER,
            sentiment_score REAL,
            topics TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ conversation_analytics table created")
    
    # Create daily_stats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL UNIQUE,
            total_users INTEGER DEFAULT 0,
            active_users INTEGER DEFAULT 0,
            new_users INTEGER DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            total_ai_calls INTEGER DEFAULT 0,
            avg_session_duration INTEGER DEFAULT 0,
            top_characters TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ daily_stats table created")
    
    # Add missing columns to existing tables (safe - ignores if exists)
    try:
        cursor.execute('ALTER TABLE user_activity_log ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
        print("✓ Added created_at column to user_activity_log")
    except:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE conversation_analytics ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
        print("✓ Added created_at column to conversation_analytics")
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE daily_stats ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
        print("✓ Added created_at column to daily_stats")
    except:
        pass
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity_log(user_id)')
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_date ON user_activity_log(created_at)')
    except:
        pass  # Index creation may fail if column doesn't exist
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation_analytics(user_id)')
    print("✓ Indexes created")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Analytics tables migration complete!")

if __name__ == "__main__":
    migrate()
