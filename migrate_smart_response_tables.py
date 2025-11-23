#!/usr/bin/env python3
"""
Migration: Add Smart Response System Tables
Creates tables for user learning profiles and interaction history
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

def create_smart_response_tables():
    """Create tables for smart response system"""
    print("=" * 80)
    print("MIGRATION: Smart Response System Tables")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Table 1: User Learning Profiles
        print("📝 Creating user_learning_profiles table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_learning_profiles (
                user_id INTEGER PRIMARY KEY,
                profile_data TEXT,  -- JSON with learning data
                interaction_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("   ✅ user_learning_profiles table created!")
        
        # Table 2: Interaction History
        print("📝 Creating interaction_history table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT,
                response_type TEXT,  -- 'quick_reply' or 'full_ai'
                character TEXT,
                satisfaction_score REAL,  -- 0.0 to 1.0
                satisfaction_signals TEXT,  -- JSON array
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("   ✅ interaction_history table created!")
        
        # Create indexes for performance
        print()
        print("📝 Creating indexes...")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_learning_profiles_updated 
            ON user_learning_profiles(last_updated)
        ''')
        print("   ✅ Index on user_learning_profiles.last_updated")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interaction_history_user 
            ON interaction_history(user_id)
        ''')
        print("   ✅ Index on interaction_history.user_id")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interaction_history_timestamp 
            ON interaction_history(timestamp)
        ''')
        print("   ✅ Index on interaction_history.timestamp")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interaction_history_character 
            ON interaction_history(character)
        ''')
        print("   ✅ Index on interaction_history.character")
        
        conn.commit()
        
        print()
        print("=" * 80)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 80)
        print()
        
        # Verify tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('user_learning_profiles', 'interaction_history')
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print("📊 Smart Response Tables:")
        for table in tables:
            print(f"   ✅ {table[0]}")
        
        print()
        print("🎉 Smart Response System ready to learn!")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n🚀 Adding Smart Response System tables...")
    print()
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Run this script in the project root directory")
        exit(1)
    
    success = create_smart_response_tables()
    
    if success:
        print("=" * 80)
        print("✅ COMPLETE! Restart your Flask app to use the new system.")
        print("=" * 80)
        print()
    else:
        print("❌ Migration failed!")
