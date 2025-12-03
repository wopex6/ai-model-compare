"""
Database Migration Script for Phase 3: Personality Integration
Safely updates production database schema with Phase 3 changes
"""

import sqlite3
import sys
from datetime import datetime

print("="*70)
print("DATABASE MIGRATION: Phase 3 Personality Integration")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

DB_PATH = 'integrated_users.db'

def check_table_exists(cursor, table_name):
    """Check if a table exists"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

try:
    # Connect to database
    print("📂 Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print(f"✓ Connected to {DB_PATH}")
    print()
    
    # MIGRATION 1: Create personality_interpretations table
    print("MIGRATION 1: personality_interpretations table")
    print("-" * 70)
    
    if check_table_exists(cursor, 'personality_interpretations'):
        print("ℹ️  Table already exists - skipping")
    else:
        print("Creating personality_interpretations table...")
        cursor.execute('''
            CREATE TABLE personality_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                event_type TEXT NOT NULL,
                raw_event TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                emotional_impact TEXT,
                recommended_approach TEXT,
                confidence REAL NOT NULL,
                traits_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_personality_interp_user 
            ON personality_interpretations(user_id, created_at DESC)
        ''')
        
        conn.commit()
        print("✓ Table created with index")
    
    print()
    
    # MIGRATION 2: Add columns to history_secondary
    print("MIGRATION 2: history_secondary table columns")
    print("-" * 70)
    
    columns_to_add = [
        ('personality_interpretation', 'TEXT', None),
        ('interpretation_confidence', 'REAL', '0.0'),
        ('personality_traits_used', 'TEXT', None)
    ]
    
    for col_name, col_type, default_value in columns_to_add:
        if check_column_exists(cursor, 'history_secondary', col_name):
            print(f"ℹ️  Column '{col_name}' already exists - skipping")
        else:
            print(f"Adding column '{col_name}' ({col_type})...")
            default_clause = f"DEFAULT {default_value}" if default_value else ""
            cursor.execute(f'''
                ALTER TABLE history_secondary 
                ADD COLUMN {col_name} {col_type} {default_clause}
            ''')
            conn.commit()
            print(f"✓ Column '{col_name}' added")
    
    print()
    
    # MIGRATION 3: Verify explicit_context has original_confidence column (Phase 2)
    print("MIGRATION 3: Verify Phase 2 schema (explicit_context)")
    print("-" * 70)
    
    if check_column_exists(cursor, 'explicit_context', 'original_confidence'):
        print("✓ explicit_context.original_confidence exists")
    else:
        print("Adding original_confidence column...")
        cursor.execute('''
            ALTER TABLE explicit_context 
            ADD COLUMN original_confidence REAL DEFAULT 1.0
        ''')
        conn.commit()
        print("✓ Column added")
    
    print()
    
    # VERIFICATION: Check all expected tables and columns
    print("VERIFICATION: Schema Validation")
    print("-" * 70)
    
    # Check Phase 2 tables
    phase2_tables = [
        'pattern_suggestions',
        'pattern_statistics',
        'pattern_analysis_jobs',
        'explicit_context_archive',
        'archival_statistics'
    ]
    
    print("\nPhase 2 Tables:")
    for table in phase2_tables:
        exists = check_table_exists(cursor, table)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
    
    # Check Phase 3 tables
    print("\nPhase 3 Tables:")
    exists = check_table_exists(cursor, 'personality_interpretations')
    status = "✓" if exists else "✗"
    print(f"  {status} personality_interpretations")
    
    # Check Phase 3 columns
    print("\nPhase 3 Columns (history_secondary):")
    for col_name, _, _ in columns_to_add:
        exists = check_column_exists(cursor, 'history_secondary', col_name)
        status = "✓" if exists else "✗"
        print(f"  {status} {col_name}")
    
    print()
    
    # Count records
    print("Database Statistics:")
    print("-" * 70)
    
    tables_to_count = [
        'users',
        'explicit_context',
        'personality_interpretations',
        'history_primary',
        'history_secondary'
    ]
    
    for table in tables_to_count:
        if check_table_exists(cursor, table):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")
    
    conn.close()
    
    print()
    print("="*70)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps:")
    print("  1. Restart the application: python app.py")
    print("  2. Test Phase 3 features")
    print("  3. Verify personality interpretation is working")
    print()
    
except Exception as e:
    print()
    print("="*70)
    print("❌ MIGRATION FAILED")
    print("="*70)
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
