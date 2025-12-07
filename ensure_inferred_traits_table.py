"""
Ensure inferred_traits table exists
Run this once to create the table if it doesn't exist
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

def ensure_inferred_traits_table():
    """Create inferred_traits table if it doesn't exist"""
    
    print("=" * 80)
    print("ENSURING INFERRED_TRAITS TABLE EXISTS")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='inferred_traits'
        ''')
        
        exists = cursor.fetchone() is not None
        
        if exists:
            print("✅ inferred_traits table already exists")
            
            # Check structure
            cursor.execute('PRAGMA table_info(inferred_traits)')
            columns = cursor.fetchall()
            print(f"   Columns: {len(columns)}")
            for col in columns:
                print(f"      - {col[1]} ({col[2]})")
        else:
            print("📦 Creating inferred_traits table...")
            
            # Create table
            cursor.execute('''
                CREATE TABLE inferred_traits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    openness REAL NOT NULL DEFAULT 0.5,
                    conscientiousness REAL NOT NULL DEFAULT 0.5,
                    extraversion REAL NOT NULL DEFAULT 0.5,
                    agreeableness REAL NOT NULL DEFAULT 0.5,
                    neuroticism REAL NOT NULL DEFAULT 0.5,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    message_count INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            print("✅ inferred_traits table created successfully")
        
        print()
        
        # Check for sample data
        cursor.execute('SELECT COUNT(*) FROM inferred_traits')
        count = cursor.fetchone()[0]
        print(f"📊 Current records: {count}")
        
        if count > 0:
            cursor.execute('''
                SELECT user_id, confidence, message_count, last_updated
                FROM inferred_traits
            ''')
            for row in cursor.fetchall():
                print(f"   User {row[0]}: confidence={row[1]:.2f}, messages={row[2]}, updated={row[3]}")
        
        print()
        print("=" * 80)
        print("✅ COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    ensure_inferred_traits_table()
