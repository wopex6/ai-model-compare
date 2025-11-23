#!/usr/bin/env python3
"""
Database Schema Verification & Migration Script
Checks all tables and columns against expected schema
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / 'integrated_users.db'

# Expected schema for all tables
EXPECTED_SCHEMA = {
    'users': {
        'id': 'INTEGER',
        'username': 'TEXT',
        'email': 'TEXT',
        'password_hash': 'TEXT',
        'user_role': 'TEXT',
        'created_at': 'DATETIME',
        'is_deleted': 'INTEGER',
        'email_verified': 'INTEGER',
        'verification_token': 'TEXT'
    },
    'user_profiles': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'full_name': 'TEXT',
        'bio': 'TEXT',
        'avatar_url': 'TEXT',
        'timezone': 'TEXT',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME'
    },
    'conversations': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'title': 'TEXT',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME'
    },
    'messages': {
        'id': 'INTEGER',
        'conversation_id': 'INTEGER',
        'role': 'TEXT',
        'content': 'TEXT',
        'timestamp': 'DATETIME',
        'model_used': 'TEXT'
    },
    'ai_conversations': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'character_type': 'TEXT',
        'conversation_data': 'TEXT',
        'created_at': 'DATETIME',
        'updated_at': 'DATETIME'
    },
    'message_usage': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'message_id': 'INTEGER',
        'provider': 'TEXT',
        'model': 'TEXT',
        'prompt_tokens': 'INTEGER',
        'completion_tokens': 'INTEGER',
        'total_tokens': 'INTEGER',
        'estimated_cost': 'REAL',
        'timestamp': 'DATETIME'
    },
    'user_interactions': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'interaction_type': 'TEXT',
        'interaction_data': 'TEXT',
        'timestamp': 'DATETIME'
    },
    'psychology_traits': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'trait_name': 'TEXT',
        'trait_value': 'REAL',
        'assessed_at': 'DATETIME'
    },
    'psychology_sessions': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'session_data': 'TEXT',
        'current_question': 'INTEGER',
        'is_complete': 'INTEGER',
        'started_at': 'DATETIME',
        'completed_at': 'DATETIME',
        'last_updated': 'DATETIME'
    },
    'admin_messages': {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'sender_type': 'TEXT',
        'message': 'TEXT',
        'is_read': 'INTEGER',
        'timestamp': 'DATETIME',
        'file_url': 'TEXT',
        'file_name': 'TEXT',
        'file_size': 'INTEGER',
        'reply_to': 'INTEGER'
    }
}

def get_current_schema(conn):
    """Get current database schema"""
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = {}
        for col in cursor.fetchall():
            # col = (cid, name, type, notnull, dflt_value, pk)
            columns[col[1]] = col[2]
        schema[table] = columns
    
    return schema

def verify_and_migrate():
    """Verify schema and apply migrations if needed"""
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)
    print(f"📁 Database: {DB_PATH}")
    print()
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_schema = get_current_schema(conn)
    
    print("🔍 Checking all tables and columns...")
    print()
    
    missing_tables = []
    missing_columns = {}
    extra_tables = []
    
    # Check for missing tables and columns
    for table_name, expected_columns in EXPECTED_SCHEMA.items():
        if table_name not in current_schema:
            missing_tables.append(table_name)
            print(f"❌ MISSING TABLE: {table_name}")
        else:
            current_columns = current_schema[table_name]
            table_missing_cols = []
            
            for col_name, col_type in expected_columns.items():
                if col_name not in current_columns:
                    table_missing_cols.append((col_name, col_type))
            
            if table_missing_cols:
                missing_columns[table_name] = table_missing_cols
                print(f"⚠️  TABLE {table_name}: Missing {len(table_missing_cols)} column(s)")
                for col_name, col_type in table_missing_cols:
                    print(f"     - {col_name} ({col_type})")
            else:
                print(f"✅ TABLE {table_name}: All columns present")
    
    # Check for extra tables (not in expected schema)
    for table_name in current_schema:
        if table_name not in EXPECTED_SCHEMA and not table_name.startswith('sqlite_'):
            extra_tables.append(table_name)
    
    if extra_tables:
        print()
        print(f"ℹ️  Extra tables (not in expected schema): {', '.join(extra_tables)}")
    
    print()
    print("=" * 80)
    
    # Apply migrations if needed
    if missing_tables or missing_columns:
        print("🔧 APPLYING MIGRATIONS...")
        print("=" * 80)
        print()
        
        try:
            # Create missing tables
            for table_name in missing_tables:
                print(f"📝 Creating table: {table_name}")
                # This would need specific CREATE TABLE statements
                # For now, just report
                print(f"   ⚠️  Table creation requires specific schema - run init_db()")
            
            # Add missing columns
            for table_name, cols in missing_columns.items():
                print(f"📝 Adding columns to {table_name}:")
                for col_name, col_type in cols:
                    try:
                        # Determine default value based on type
                        default = "NULL"
                        if col_type == 'INTEGER' and 'default' not in col_name.lower():
                            default = "0"
                        elif col_type == 'TEXT':
                            default = "NULL"
                        
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT {default}")
                        print(f"   ✅ Added: {col_name} ({col_type})")
                    except Exception as e:
                        print(f"   ❌ Failed to add {col_name}: {e}")
            
            conn.commit()
            print()
            print("✅ Migration complete!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            return False
    else:
        print("✅ ALL TABLES AND COLUMNS ARE UP TO DATE!")
        print("=" * 80)
    
    print()
    print("📊 SCHEMA SUMMARY:")
    print(f"   Total tables expected: {len(EXPECTED_SCHEMA)}")
    print(f"   Total tables found: {len(current_schema)}")
    print(f"   Missing tables: {len(missing_tables)}")
    print(f"   Tables with missing columns: {len(missing_columns)}")
    print(f"   Extra tables: {len(extra_tables)}")
    print()
    
    conn.close()
    return True

if __name__ == "__main__":
    print()
    print("🚀 Starting database schema verification...")
    print()
    
    success = verify_and_migrate()
    
    if success:
        print("=" * 80)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 80)
        print()
        print("If any migrations were applied, reload your web app:")
        print("   touch /var/www/trabcd_pythonanywhere_com_wsgi.py")
        print()
    else:
        print("=" * 80)
        print("❌ VERIFICATION FAILED")
        print("=" * 80)
