#!/usr/bin/env python3
"""
Apply schema migration to PythonAnywhere database
Safely updates database structure without losing data
"""

import sqlite3
import json
import os
from datetime import datetime

def backup_database(db_path):
    """Create backup before migration"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f"📦 Creating backup: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    backup_conn = sqlite3.connect(backup_path)
    
    conn.backup(backup_conn)
    
    backup_conn.close()
    conn.close()
    
    backup_size = os.path.getsize(backup_path) / (1024 * 1024)
    print(f"✅ Backup created ({backup_size:.2f} MB)")
    
    return backup_path

def get_current_schema(db_path):
    """Get current database schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    schema = {}
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get columns for each table
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        schema[table] = {col[1]: col[2] for col in columns}  # {column_name: type}
    
    conn.close()
    return schema

def apply_migration(db_path='databases/production_integrated_users.db', schema_file='database_schema.json'):
    """Apply schema migration"""
    
    print("="*70)
    print("  Schema Migration for PythonAnywhere")
    print("="*70)
    print()
    
    # Check if files exist
    if not os.path.exists(schema_file):
        print(f"❌ Schema file not found: {schema_file}")
        print("   Upload database_schema.json from your local machine")
        return False
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Load target schema
    with open(schema_file, 'r') as f:
        target_schema = json.load(f)
    
    print(f"📋 Target schema: {len(target_schema)} tables")
    
    # Backup database
    backup_path = backup_database(db_path)
    
    # Get current schema
    print("\n🔍 Analyzing current schema...")
    current_schema = get_current_schema(db_path)
    print(f"📋 Current schema: {len(current_schema)} tables")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    changes_made = []
    
    # Check for missing tables
    print("\n🔨 Checking for missing tables...")
    missing_tables = set(target_schema.keys()) - set(current_schema.keys())
    
    if missing_tables:
        print(f"   Found {len(missing_tables)} missing tables")
        for table in missing_tables:
            print(f"   ⚠️  Missing table: {table}")
            changes_made.append(f"Missing table: {table}")
    else:
        print("   ✅ All tables present")
    
    # Check for missing columns in existing tables
    print("\n🔨 Checking for missing columns...")
    columns_to_add = []
    
    for table_name, target_columns in target_schema.items():
        if table_name not in current_schema:
            continue
        
        current_cols = current_schema[table_name]
        
        for col_info in target_columns['columns']:
            col_name = col_info['name']
            col_type = col_info['type']
            
            if col_name not in current_cols:
                columns_to_add.append((table_name, col_name, col_type, col_info))
                print(f"   ⚠️  {table_name}.{col_name} ({col_type}) - MISSING")
    
    if not columns_to_add:
        print("   ✅ All columns present in existing tables")
    
    # Apply column additions
    if columns_to_add:
        print(f"\n📝 Adding {len(columns_to_add)} missing columns...")
        
        for table_name, col_name, col_type, col_info in columns_to_add:
            try:
                # Build ALTER TABLE statement
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                
                # Add constraints
                if col_info.get('default') is not None:
                    alter_sql += f" DEFAULT {col_info['default']}"
                
                print(f"   Adding: {table_name}.{col_name}")
                cursor.execute(alter_sql)
                changes_made.append(f"Added column: {table_name}.{col_name}")
                
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower():
                    print(f"   ✅ {table_name}.{col_name} already exists")
                else:
                    print(f"   ❌ Error adding {table_name}.{col_name}: {e}")
    
    # Create missing tables
    if missing_tables:
        print(f"\n⚠️  WARNING: {len(missing_tables)} tables are missing!")
        print("   These tables should be created by running the application.")
        print("   Missing tables:")
        for table in list(missing_tables)[:5]:
            print(f"     - {table}")
        if len(missing_tables) > 5:
            print(f"     ... and {len(missing_tables) - 5} more")
        print("\n   Run your Flask app once to auto-create missing tables.")
    
    # Commit changes
    if changes_made:
        print("\n💾 Committing changes...")
        conn.commit()
    
    # Optimize database
    print("\n🔧 Optimizing database...")
    cursor.execute("VACUUM")
    cursor.execute("ANALYZE")
    
    conn.close()
    
    # Summary
    print("\n" + "="*70)
    print("  Migration Summary")
    print("="*70)
    print()
    
    if changes_made:
        print("✅ Changes applied:")
        for change in changes_made:
            print(f"   - {change}")
    else:
        print("✅ No changes needed - schema is up to date!")
    
    print(f"\n📦 Backup saved at: {backup_path}")
    print()
    print("✅ Schema migration complete!")
    print()
    print("📋 Next steps:")
    print("   1. Test your application")
    print("   2. If everything works, keep the backup for 7 days")
    print("   3. If something broke, restore from backup:")
    print(f"      cp {backup_path} {db_path}")
    print()
    
    return True

if __name__ == "__main__":
    # Detect if running on PythonAnywhere or locally
    if os.path.exists('/home'):  # Likely PythonAnywhere/Linux
        db_path = 'databases/production_integrated_users.db'
        # Check if running from project directory
        if not os.path.exists('databases'):
            db_path = os.path.expanduser('~/ai-model-compare/databases/production_integrated_users.db')
    else:  # Windows/Local
        db_path = 'integrated_users.db'
    
    schema_file = 'database_schema.json'
    
    print(f"Database: {db_path}")
    print(f"Schema file: {schema_file}")
    print()
    
    if not os.path.exists(schema_file):
        print("❌ database_schema.json not found!")
        print()
        print("To create it:")
        print("  1. On your local machine, run: python export_schema.py")
        print("  2. Upload database_schema.json to PythonAnywhere")
        print("  3. Run this script again")
        print()
    else:
        try:
            apply_migration(db_path, schema_file)
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
