"""
Add is_deleted column to users table for soft delete functionality
"""

from integrated_database import IntegratedDatabase

db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

print("Adding is_deleted column to users table...")

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_deleted' not in columns:
        cursor.execute('''
            ALTER TABLE users 
            ADD COLUMN is_deleted INTEGER DEFAULT 0
        ''')
        conn.commit()
        print("✅ Successfully added is_deleted column")
    else:
        print("✅ is_deleted column already exists")
        
    # Verify
    cursor.execute("PRAGMA table_info(users)")
    print("\nUsers table columns:")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
        
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
