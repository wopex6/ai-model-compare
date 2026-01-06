#!/usr/bin/env python3
"""
Fix: Add missing columns to inferred_personality table
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

def fix_columns():
    print("=" * 60)
    print("FIX: Ensure inferred_personality table has all columns")
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
            print("✅ Table created with all columns")
            return
        
        # Check existing columns
        cursor.execute('PRAGMA table_info(inferred_personality)')
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Existing columns: {columns}")
        
        # Add missing columns
        columns_to_add = [
            ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('message_count', 'INTEGER DEFAULT 0'),
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                try:
                    print(f"Adding {col_name} column...")
                    cursor.execute(f'ALTER TABLE inferred_personality ADD COLUMN {col_name} {col_type}')
                    conn.commit()
                    print(f"✅ {col_name} column added")
                except sqlite3.OperationalError as e:
                    if 'duplicate column' in str(e).lower():
                        print(f"✅ {col_name} column already exists")
                    else:
                        print(f"⚠️ Could not add {col_name}: {e}")
            else:
                print(f"✅ {col_name} column already exists")
        
        # Verify final schema
        cursor.execute('PRAGMA table_info(inferred_personality)')
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\nFinal columns: {columns}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    fix_columns()
