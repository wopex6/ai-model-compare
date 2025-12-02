"""
Remove UNIQUE constraint from explicit_context table to allow historical tracking.

The UNIQUE(user_id, character, context_type, context_key) constraint was causing
INSERT OR REPLACE to delete old emotional states instead of preserving them.

We need to preserve historical emotions for pattern analysis!
"""
import sqlite3

conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()

print("Creating new table without UNIQUE constraint...")

# Create new table without the UNIQUE constraint
cursor.execute('''
    CREATE TABLE IF NOT EXISTS explicit_context_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        character TEXT NOT NULL,
        
        -- When and what
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        context_type TEXT NOT NULL,
        context_key TEXT NOT NULL,
        context_value TEXT NOT NULL,
        
        -- The actual words user said
        original_statement TEXT NOT NULL,
        
        -- Priority and confidence
        priority TEXT NOT NULL,
        confidence FLOAT DEFAULT 1.0,
        
        -- Lifecycle
        active BOOLEAN DEFAULT 1,
        expires_at TIMESTAMP,
        
        -- Metadata
        extracted_via TEXT
        
        -- NO UNIQUE CONSTRAINT - allow historical tracking!
    )
''')

print("Copying data from old table...")
cursor.execute('''
    INSERT INTO explicit_context_new 
    SELECT * FROM explicit_context
''')

print("Dropping old table...")
cursor.execute('DROP TABLE explicit_context')

print("Renaming new table...")
cursor.execute('ALTER TABLE explicit_context_new RENAME TO explicit_context')

print("Creating index for performance...")
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_explicit_context_lookup 
    ON explicit_context(user_id, character, context_type, active)
''')

conn.commit()
conn.close()

print("\n✓ Done! UNIQUE constraint removed.")
print("✓ Historical context preservation enabled.")
print("✓ Index created for query performance.")
