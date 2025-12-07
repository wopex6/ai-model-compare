"""
Create inferred_personality table for PersonalityResolver
This is separate from the existing inferred_traits table
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

def create_inferred_personality_table():
    """Create inferred_personality table with Big 5 structure"""
    
    print("=" * 80)
    print("CREATING INFERRED_PERSONALITY TABLE")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='inferred_personality'
        ''')
        
        if cursor.fetchone():
            print("✅ Table already exists")
        else:
            print("📦 Creating inferred_personality table...")
            
            cursor.execute('''
                CREATE TABLE inferred_personality (
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
            print("✅ Table created successfully!")
        
        print()
        
        # Show schema
        cursor.execute('PRAGMA table_info(inferred_personality)')
        columns = cursor.fetchall()
        
        print("📋 Schema:")
        for col in columns:
            print(f"   {col[1]:25} {col[2]}")
        print()
        
        # Check for data
        cursor.execute('SELECT COUNT(*) FROM inferred_personality')
        count = cursor.fetchone()[0]
        
        print(f"📊 Current records: {count}")
        
        if count > 0:
            cursor.execute('''
                SELECT user_id, openness, conscientiousness, extraversion,
                       agreeableness, neuroticism, confidence, message_count
                FROM inferred_personality
            ''')
            for row in cursor.fetchall():
                print(f"   User {row[0]}: O={row[1]:.2f} C={row[2]:.2f} E={row[3]:.2f} A={row[4]:.2f} N={row[5]:.2f} (conf={row[6]:.2f}, msgs={row[7]})")
        
        print()
        print("=" * 80)
        print("✅ READY FOR PERSONALITY RESOLVER")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    create_inferred_personality_table()
