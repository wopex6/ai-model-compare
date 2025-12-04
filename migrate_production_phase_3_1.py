#!/usr/bin/env python3
"""
Production Database Migration - Phase 3.1
Safely updates database schema for personality features and master role
Run this ONCE on production database
"""

import sqlite3
import os
from datetime import datetime

def backup_database(db_path):
    """Create a backup before migration"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f"📦 Creating backup: {backup_path}")
    
    # Copy database file
    import shutil
    shutil.copy2(db_path, backup_path)
    
    print(f"✅ Backup created successfully")
    return backup_path

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def check_table_exists(cursor, table):
    """Check if a table exists"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

def migrate_production_database():
    print("🚀 Phase 3.1 Production Database Migration")
    print("=" * 70)
    
    db_path = 'integrated_users.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please ensure you're in the correct directory.")
        return False
    
    # Step 1: Backup
    print("\n📋 Step 1: Creating Backup")
    print("-" * 70)
    backup_path = backup_database(db_path)
    
    # Step 2: Connect and check
    print("\n🔍 Step 2: Checking Database Schema")
    print("-" * 70)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    changes_needed = []
    changes_made = []
    
    # Check for user_role column
    if not check_column_exists(cursor, 'users', 'user_role'):
        changes_needed.append("Add 'user_role' column to users table")
    else:
        print("✅ 'user_role' column exists in users table")
    
    # Check for personality_interpretations table
    if not check_table_exists(cursor, 'personality_interpretations'):
        changes_needed.append("Create 'personality_interpretations' table")
    else:
        print("✅ 'personality_interpretations' table exists")
    
    # Check for message_usage table
    if not check_table_exists(cursor, 'message_usage'):
        changes_needed.append("Create 'message_usage' table")
    else:
        print("✅ 'message_usage' table exists")
    
    # Check for history_secondary updates
    has_personality_cols = all([
        check_column_exists(cursor, 'history_secondary', 'personality_interpretation'),
        check_column_exists(cursor, 'history_secondary', 'personality_confidence'),
        check_column_exists(cursor, 'history_secondary', 'personality_source')
    ])
    
    if not has_personality_cols:
        changes_needed.append("Add personality columns to history_secondary table")
    else:
        print("✅ Personality columns exist in history_secondary table")
    
    # Step 3: Apply migrations
    if changes_needed:
        print(f"\n⚠️  {len(changes_needed)} change(s) needed:")
        for i, change in enumerate(changes_needed, 1):
            print(f"   {i}. {change}")
        
        response = input("\n❓ Apply these changes? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("❌ Migration cancelled")
            conn.close()
            return False
        
        print("\n🔧 Step 3: Applying Migrations")
        print("-" * 70)
        
        try:
            # Migration 1: Add user_role column if needed
            if "Add 'user_role' column" in changes_needed:
                print("📝 Adding user_role column...")
                cursor.execute('''
                    ALTER TABLE users 
                    ADD COLUMN user_role TEXT DEFAULT 'guest'
                ''')
                
                # Set existing users based on email
                cursor.execute('''
                    UPDATE users 
                    SET user_role = 'administrator' 
                    WHERE email LIKE '%@admin%' OR username = 'Wai Tse'
                ''')
                
                cursor.execute('''
                    UPDATE users 
                    SET user_role = 'paid' 
                    WHERE username = 'AutoTest' OR email LIKE '%@test%'
                ''')
                
                changes_made.append("✅ Added user_role column and set initial roles")
                print("   ✅ Done")
            
            # Migration 2: Create personality_interpretations table if needed
            if "Create 'personality_interpretations' table" in changes_needed:
                print("📝 Creating personality_interpretations table...")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS personality_interpretations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_id TEXT,
                        conversation_id INTEGER,
                        character TEXT,
                        raw_message TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        interpretation TEXT NOT NULL,
                        emotional_impact TEXT,
                        recommended_approach TEXT,
                        confidence REAL NOT NULL,
                        personality_source TEXT NOT NULL,
                        personality_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_personality_user 
                    ON personality_interpretations(user_id, created_at DESC)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_personality_conversation 
                    ON personality_interpretations(conversation_id)
                ''')
                
                changes_made.append("✅ Created personality_interpretations table with indexes")
                print("   ✅ Done")
            
            # Migration 3: Create message_usage table if needed
            if "Create 'message_usage' table" in changes_needed:
                print("📝 Creating message_usage table...")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS message_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        message_count INTEGER DEFAULT 0,
                        UNIQUE(user_id, date),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                changes_made.append("✅ Created message_usage table")
                print("   ✅ Done")
            
            # Migration 4: Add personality columns to history_secondary if needed
            if "Add personality columns to history_secondary table" in changes_needed:
                print("📝 Adding personality columns to history_secondary...")
                
                if not check_column_exists(cursor, 'history_secondary', 'personality_interpretation'):
                    cursor.execute('''
                        ALTER TABLE history_secondary 
                        ADD COLUMN personality_interpretation TEXT
                    ''')
                
                if not check_column_exists(cursor, 'history_secondary', 'personality_confidence'):
                    cursor.execute('''
                        ALTER TABLE history_secondary 
                        ADD COLUMN personality_confidence REAL
                    ''')
                
                if not check_column_exists(cursor, 'history_secondary', 'personality_source'):
                    cursor.execute('''
                        ALTER TABLE history_secondary 
                        ADD COLUMN personality_source TEXT
                    ''')
                
                changes_made.append("✅ Added personality columns to history_secondary")
                print("   ✅ Done")
            
            # Commit all changes
            conn.commit()
            print("\n💾 All changes committed successfully")
            
        except Exception as e:
            print(f"\n❌ Error during migration: {e}")
            conn.rollback()
            print("🔄 Changes rolled back")
            print(f"📦 Restore from backup: {backup_path}")
            conn.close()
            return False
    
    else:
        print("\n✅ Database is already up to date - no migration needed")
    
    # Step 4: Display statistics
    print("\n📊 Step 4: Database Statistics")
    print("-" * 70)
    
    # Count users by role
    cursor.execute('''
        SELECT user_role, COUNT(*) 
        FROM users 
        GROUP BY user_role
    ''')
    
    print("\n👥 Users by Role:")
    for role, count in cursor.fetchall():
        icon = "👑" if role == "administrator" else "⭐" if role == "master" else "💎" if role == "paid" else "👤"
        print(f"   {icon} {role:15s}: {count} user(s)")
    
    # Count interpretations
    if check_table_exists(cursor, 'personality_interpretations'):
        cursor.execute('SELECT COUNT(*) FROM personality_interpretations')
        interp_count = cursor.fetchone()[0]
        print(f"\n🧠 Personality Interpretations: {interp_count}")
    
    conn.close()
    
    # Step 5: Next steps
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    
    if changes_made:
        print("\n📝 Changes Applied:")
        for change in changes_made:
            print(f"   {change}")
    
    print("\n🎯 Next Steps:")
    print("   1. ✅ Database is ready for Phase 3.1 features")
    print("   2. 🔧 Run 'python add_master_role.py' to promote users to Master")
    print("   3. 🚀 Start your application: python app.py")
    print("   4. 🧪 Test the Personality Insights Dashboard")
    
    print(f"\n💾 Backup Location: {backup_path}")
    print("   (Keep this backup safe for at least 7 days)")
    
    return True

if __name__ == "__main__":
    try:
        success = migrate_production_database()
        if success:
            print("\n🎉 Migration completed successfully!")
        else:
            print("\n⚠️  Migration did not complete")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
