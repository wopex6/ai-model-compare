#!/usr/bin/env python3
"""Database Migration - December 18, 2025

Updates for:
1. Personality Context Integrator tables
2. Inferred personality traits
3. Message routing improvements

Safe to run multiple times (idempotent).

Usage on PythonAnywhere:
    cd ~/ai-model-compare
    python migrate_dec18_2025.py --db integrated_users.db --backup
"""

import argparse
import os
import shutil
import sqlite3
from datetime import datetime


def _now_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_database(db_path):
    """Create a backup before migration."""
    backup_path = f"{db_path}.backup_{_now_stamp()}"
    print(f"📦 Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
    print(f"✅ Backup created ({size_mb:.2f} MB)")
    return backup_path


def table_exists(cursor, table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    return column in cols


def run_migration(db_path, do_backup=True):
    """Run all migrations for Dec 18, 2025 updates."""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    if do_backup:
        backup_database(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    changes_made = 0
    
    print("\n🔄 Running migrations for Dec 18, 2025...\n")
    
    # 1. Ensure inferred_personality table exists
    if not table_exists(cursor, 'inferred_personality'):
        print("Creating table: inferred_personality")
        cursor.execute('''
            CREATE TABLE inferred_personality (
                user_id INTEGER PRIMARY KEY,
                openness REAL DEFAULT 0.5,
                conscientiousness REAL DEFAULT 0.5,
                extraversion REAL DEFAULT 0.5,
                agreeableness REAL DEFAULT 0.5,
                neuroticism REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.0,
                sample_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        changes_made += 1
        print("  ✅ Created inferred_personality")
    else:
        print("  ⏭️ inferred_personality already exists")
    
    # 2. Add confidence column if missing
    if table_exists(cursor, 'inferred_personality'):
        if not column_exists(cursor, 'inferred_personality', 'confidence'):
            print("Adding column: inferred_personality.confidence")
            cursor.execute('ALTER TABLE inferred_personality ADD COLUMN confidence REAL DEFAULT 0.0')
            changes_made += 1
            print("  ✅ Added confidence column")
        
        if not column_exists(cursor, 'inferred_personality', 'sample_count'):
            print("Adding column: inferred_personality.sample_count")
            cursor.execute('ALTER TABLE inferred_personality ADD COLUMN sample_count INTEGER DEFAULT 0')
            changes_made += 1
            print("  ✅ Added sample_count column")
    
    # 3. Ensure assessment_history table exists with all columns
    if not table_exists(cursor, 'assessment_history'):
        print("Creating table: assessment_history")
        cursor.execute('''
            CREATE TABLE assessment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                assessment_type TEXT DEFAULT 'big5',
                openness REAL,
                conscientiousness REAL,
                extraversion REAL,
                agreeableness REAL,
                neuroticism REAL,
                raw_answers TEXT,
                completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assessment_user ON assessment_history(user_id)')
        changes_made += 1
        print("  ✅ Created assessment_history")
    else:
        print("  ⏭️ assessment_history already exists")
    
    # 4. Ensure character_id column exists in ai_conversations
    if table_exists(cursor, 'ai_conversations'):
        if not column_exists(cursor, 'ai_conversations', 'character_id'):
            print("Adding column: ai_conversations.character_id")
            cursor.execute('ALTER TABLE ai_conversations ADD COLUMN character_id TEXT')
            changes_made += 1
            print("  ✅ Added character_id column")
        else:
            print("  ⏭️ ai_conversations.character_id already exists")
    
    # 5. Ensure messages table exists
    if not table_exists(cursor, 'messages'):
        print("Creating table: messages")
        cursor.execute('''
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)')
        changes_made += 1
        print("  ✅ Created messages table")
    else:
        print("  ⏭️ messages table already exists")
    
    # 6. Create personality cache table (optional, for future use)
    if not table_exists(cursor, 'personality_cache'):
        print("Creating table: personality_cache")
        cursor.execute('''
            CREATE TABLE personality_cache (
                user_id INTEGER PRIMARY KEY,
                cache_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
            )
        ''')
        changes_made += 1
        print("  ✅ Created personality_cache")
    else:
        print("  ⏭️ personality_cache already exists")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Migration complete! {changes_made} changes made.")
    return True


def main():
    parser = argparse.ArgumentParser(description='Database migration for Dec 18, 2025 updates')
    parser.add_argument('--db', default='integrated_users.db', help='Path to database file')
    parser.add_argument('--backup', action='store_true', default=True, help='Create backup before migration')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    do_backup = not args.no_backup
    
    print("=" * 60)
    print("Database Migration - December 18, 2025")
    print("=" * 60)
    print(f"Database: {args.db}")
    print(f"Backup: {'Yes' if do_backup else 'No'}")
    print()
    
    if not args.yes:
        confirm = input("Proceed with migration? [y/N]: ")
        if confirm.lower() != 'y':
            print("Migration cancelled.")
            return
    
    run_migration(args.db, do_backup)


if __name__ == '__main__':
    main()
