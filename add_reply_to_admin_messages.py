"""
Migration script to add reply_to column to admin_messages table
"""
import sqlite3
import os

def add_reply_to_column():
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'integrated_users.db')
    
    print(f"🔧 Adding reply_to column to admin_messages table...")
    print(f"Database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(admin_messages)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'reply_to' in columns:
            print("✅ reply_to column already exists")
        else:
            # Add reply_to column
            cursor.execute('''
                ALTER TABLE admin_messages
                ADD COLUMN reply_to INTEGER DEFAULT NULL
            ''')
            conn.commit()
            print("✅ reply_to column added successfully")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(admin_messages)")
        columns = cursor.fetchall()
        print("\n📋 Current admin_messages schema:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        print("\n✨ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    add_reply_to_column()
