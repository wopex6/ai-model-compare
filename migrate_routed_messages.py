"""
Migration: Copy routed user messages from coordinator to domain characters
This fixes the issue where user questions sent through Aria (coordinator) 
don't appear in the domain character's chat history.
"""

import sqlite3
import json
from datetime import datetime

def migrate():
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # List tables to understand structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    # Check ai_conversations structure
    cursor.execute('PRAGMA table_info(ai_conversations)')
    print("\nai_conversations columns:")
    for col in cursor.fetchall():
        print(f"  {col[1]} ({col[2]})")
    
    # Check what data we have
    cursor.execute("""
        SELECT character_id, COUNT(*) as cnt
        FROM ai_conversations
        GROUP BY character_id
    """)
    print("\nConversations by character:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} sessions")
    
    # Look at conversation_data structure for coordinator
    cursor.execute("""
        SELECT session_id, conversation_data 
        FROM ai_conversations 
        WHERE character_id = 'coordinator'
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row:
        print(f"\nCoordinator session: {row[0]}")
        data = json.loads(row[1]) if row[1] else {}
        messages = data.get('messages', [])
        print(f"Messages in coordinator: {len(messages)}")
        for i, msg in enumerate(messages[:5]):
            role = msg.get('role', msg.get('sender_type', 'unknown'))
            content = msg.get('content', '')[:50]
            print(f"  {i}: {role} - {content}...")
    
    # Check messages table structure
    cursor.execute('PRAGMA table_info(messages)')
    print("\nmessages table columns:")
    for col in cursor.fetchall():
        print(f"  {col[1]} ({col[2]})")
    
    # Check messages by character (using conversation_id)
    cursor.execute("""
        SELECT ac.character_id, COUNT(m.id) as msg_count
        FROM ai_conversations ac
        LEFT JOIN messages m ON ac.id = m.conversation_id
        WHERE ac.character_id IS NOT NULL
        GROUP BY ac.character_id
    """)
    print("\nMessages count by character (messages table):")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} messages")
    
    # Look at coordinator messages
    cursor.execute("""
        SELECT m.id, m.sender_type, m.content, m.timestamp
        FROM messages m
        JOIN ai_conversations ac ON ac.id = m.conversation_id
        WHERE ac.character_id = 'coordinator'
        ORDER BY m.timestamp DESC
        LIMIT 10
    """)
    print("\nRecent coordinator messages:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} - {row[2][:60] if row[2] else 'None'}...")
    
    # Look at domain_work messages
    cursor.execute("""
        SELECT m.id, m.sender_type, m.content, m.timestamp
        FROM messages m
        JOIN ai_conversations ac ON ac.id = m.conversation_id
        WHERE ac.character_id = 'domain_work'
        ORDER BY m.timestamp DESC
        LIMIT 10
    """)
    print("\nRecent domain_work messages:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} - {row[2][:60] if row[2] else 'None'}...")
    
    conn.close()
    print("\nMigration analysis complete.")

def run_migration():
    """Actually migrate the missing user messages from coordinator to domain characters"""
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Character name mapping (display name -> character_id)
    char_mapping = {
        'Work Advisor': 'domain_work',
        'Relationship Guide': 'domain_relationships',
        'Mind Wellness': 'domain_mental_health',
        'Body Advisor': 'domain_physical_health',
        'Finance Guide': 'domain_finance',
        'Learning Mentor': 'domain_learning',
        'Creative Muse': 'domain_creativity',
    }
    
    # Get coordinator conversation id
    cursor.execute("""
        SELECT id, user_id FROM ai_conversations WHERE character_id = 'coordinator'
    """)
    coord_row = cursor.fetchone()
    if not coord_row:
        print("No coordinator conversation found")
        return
    
    coord_conv_id = coord_row[0]
    user_id = coord_row[1]
    print(f"Coordinator conversation: {coord_conv_id}, user: {user_id}")
    
    # Get all coordinator messages in order
    cursor.execute("""
        SELECT id, sender_type, content, timestamp
        FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (coord_conv_id,))
    
    coord_messages = cursor.fetchall()
    print(f"Found {len(coord_messages)} coordinator messages")
    
    migrated_count = 0
    
    # Find user messages followed by routed assistant responses
    for i, msg in enumerate(coord_messages):
        msg_id, sender_type, content, timestamp = msg
        
        if sender_type == 'user':
            # Look for next assistant message that's routed (starts with [Character])
            for j in range(i + 1, min(i + 5, len(coord_messages))):
                next_msg = coord_messages[j]
                next_sender, next_content = next_msg[1], next_msg[2]
                
                if next_sender == 'assistant' and next_content and next_content.startswith('['):
                    # Extract character name from [Character Name] prefix
                    bracket_end = next_content.find(']')
                    if bracket_end > 0:
                        char_name = next_content[1:bracket_end]
                        char_id = char_mapping.get(char_name)
                        
                        if char_id:
                            # Get or find the domain character's conversation
                            cursor.execute("""
                                SELECT id FROM ai_conversations 
                                WHERE character_id = ? AND user_id = ?
                            """, (char_id, user_id))
                            domain_conv = cursor.fetchone()
                            
                            if domain_conv:
                                domain_conv_id = domain_conv[0]
                                
                                # Check if this user message already exists
                                cursor.execute("""
                                    SELECT id FROM messages 
                                    WHERE conversation_id = ? AND sender_type = 'user' AND content = ?
                                """, (domain_conv_id, content))
                                
                                existing = cursor.fetchone()
                                if not existing:
                                    # Insert the user message into domain character's history
                                    cursor.execute("""
                                        INSERT INTO messages (conversation_id, sender_type, content, timestamp)
                                        VALUES (?, 'user', ?, ?)
                                    """, (domain_conv_id, content, timestamp))
                                    print(f"✓ Migrated: '{content[:50]}...' -> {char_id}")
                                    migrated_count += 1
                                else:
                                    print(f"  Already exists in {char_id}: '{content[:30]}...'")
                    # Continue to check for more routed responses (don't break)
    
    conn.commit()
    conn.close()
    print(f"\n✅ Migration complete: {migrated_count} messages migrated")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        run_migration()
    else:
        migrate()
        print("\nTo run the migration, use: python migrate_routed_messages.py run")
