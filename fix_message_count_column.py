#!/usr/bin/env python3
"""
Fix: Add message_count column to inferred_personality table
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

def fix_column():
    print("=" * 60)
    print("FIX: Add message_count column to inferred_personality")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inferred_personality'")
        if not cursor.fetchone():
            print("❌ Table inferred_personality does not exist")
            print("Creating table...")
            cursor.execute('''
                CREATE TABLE inferred_personality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    openness REAL NOT NULL DEFAULT 0.5,
                    conscientiousness REAL NOT NULL DEFAULT 0.5,
                    extraversion REAL NOT NULL DEFAULT 0.5,
                    agreeableness REAL NOT NULL DEFAULT 0.5,
                    neuroticism REAL NOT NULL DEFAULT 0.5,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    message_count INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("✅ Table created with message_count column")
            return
        
        # Check existing columns
        cursor.execute('PRAGMA table_info(inferred_personality)')
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        if 'message_count' in columns:
            print("✅ message_count column already exists")
            return
        
        # Add the column
        print("Adding message_count column...")
        cursor.execute('ALTER TABLE inferred_personality ADD COLUMN message_count INTEGER DEFAULT 0')
        conn.commit()
        print("✅ message_count column added successfully!")
        
        # Verify
        cursor.execute('PRAGMA table_info(inferred_personality)')
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated columns: {columns}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    fix_column()
