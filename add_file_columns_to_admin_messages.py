"""
Migration script to add file attachment columns to admin_messages table
Run this once to update the database schema
"""

import sqlite3

def add_file_columns():
    # Try all database files to find admin_messages table
    db_files = ['integrated_chat.db', 'integrated_database.db', 'integrated_users.db']
    
    for db_file in db_files:
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check if admin_messages table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_messages'")
            if cursor.fetchone():
                print(f"Found admin_messages table in {db_file}")
                break
            conn.close()
        except Exception as e:
            print(f"Error checking {db_file}: {e}")
            continue
    else:
        print("admin_messages table not found in any database!")
        return
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(admin_messages)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add file_url column if it doesn't exist
    if 'file_url' not in columns:
        print("Adding file_url column...")
        cursor.execute('''
            ALTER TABLE admin_messages
            ADD COLUMN file_url TEXT
        ''')
        print("✅ file_url column added")
    else:
        print("✅ file_url column already exists")
    
    # Add file_name column if it doesn't exist
    if 'file_name' not in columns:
        print("Adding file_name column...")
        cursor.execute('''
            ALTER TABLE admin_messages
            ADD COLUMN file_name TEXT
        ''')
        print("✅ file_name column added")
    else:
        print("✅ file_name column already exists")
    
    # Add file_size column if it doesn't exist
    if 'file_size' not in columns:
        print("Adding file_size column...")
        cursor.execute('''
            ALTER TABLE admin_messages
            ADD COLUMN file_size INTEGER
        ''')
        print("✅ file_size column added")
    else:
        print("✅ file_size column already exists")
    
    conn.commit()
    conn.close()
    print("\n🎉 Database migration completed successfully!")

if __name__ == '__main__':
    add_file_columns()
