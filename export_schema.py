#!/usr/bin/env python3
"""Export database schema for migration to PythonAnywhere"""

import sqlite3
import json
from datetime import datetime

def export_schema(db_path='integrated_users.db', output_file='database_schema.sql'):
    """Export complete database schema"""
    
    print("="*60)
    print("  Exporting Database Schema")
    print("="*60)
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table creation statements
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    
    tables = cursor.fetchall()
    
    # Get all index creation statements
    cursor.execute("""
        SELECT sql FROM sqlite_master 
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY name
    """)
    
    indexes = cursor.fetchall()
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("-- Database Schema Export\n")
        f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Source: {db_path}\n")
        f.write("-- \n")
        f.write("-- Instructions:\n")
        f.write("-- 1. Upload this file to PythonAnywhere\n")
        f.write("-- 2. Run: python apply_schema_migration.py\n")
        f.write("-- \n\n")
        
        f.write("-- ============================================================\n")
        f.write("-- TABLE DEFINITIONS\n")
        f.write("-- ============================================================\n\n")
        
        for (sql,) in tables:
            if sql:
                f.write(sql + ";\n\n")
        
        if indexes:
            f.write("\n-- ============================================================\n")
            f.write("-- INDEX DEFINITIONS\n")
            f.write("-- ============================================================\n\n")
            
            for (sql,) in indexes:
                if sql:
                    f.write(sql + ";\n\n")
    
    # Create table comparison info
    table_info = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    table_names = [row[0] for row in cursor.fetchall()]
    
    for table_name in table_names:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        table_info[table_name] = {
            'columns': [
                {
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default': col[4],
                    'pk': col[5]
                }
                for col in columns
            ]
        }
    
    # Write table info to JSON
    with open('database_schema.json', 'w', encoding='utf-8') as f:
        json.dump(table_info, f, indent=2)
    
    conn.close()
    
    print(f"✅ Schema exported to: {output_file}")
    print(f"✅ Table info exported to: database_schema.json")
    print()
    print(f"📊 Summary:")
    print(f"   - {len(tables)} tables")
    print(f"   - {len(indexes)} indexes")
    print()
    
    # Show table list
    print("📋 Tables:")
    for table_name in table_names[:10]:
        print(f"   - {table_name}")
    if len(table_names) > 10:
        print(f"   ... and {len(table_names) - 10} more")
    
    print()
    return output_file, len(tables)

if __name__ == "__main__":
    export_schema()
