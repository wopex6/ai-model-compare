#!/usr/bin/env python3
"""
Clean up duplicate chat conversations in the database
Keeps the oldest one of each duplicate set
"""

import sqlite3

def cleanup_duplicates():
    print("🧹 Cleaning up duplicate chats...")
    print("=" * 60)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Find duplicate session_ids
    cursor.execute('''
        SELECT session_id, COUNT(*) as count
        FROM ai_conversations
        GROUP BY session_id
        HAVING COUNT(*) > 1
    ''')
    
    duplicate_sessions = cursor.fetchall()
    
    if not duplicate_sessions:
        print("✅ No duplicates found - database is clean!")
        conn.close()
        return
    
    print(f"\nFound {len(duplicate_sessions)} duplicate session_ids")
    print("\n⚠️  WARNING: This will DELETE duplicate conversations!")
    print("   It will keep the oldest conversation of each duplicate set.")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        conn.close()
        return
    
    deleted_count = 0
    
    for session_id, count in duplicate_sessions:
        print(f"\n🔧 Processing session: {session_id} ({count} duplicates)")
        
        # Get all conversations with this session_id
        cursor.execute('''
            SELECT id, created_at, title
            FROM ai_conversations
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (session_id,))
        
        rows = cursor.fetchall()
        
        # Keep the first (oldest) one, delete the rest
        keep_id = rows[0][0]
        print(f"   ✅ Keeping ID {keep_id} (created: {rows[0][1]})")
        
        for row in rows[1:]:
            delete_id = row[0]
            print(f"   ❌ Deleting ID {delete_id} (created: {row[1]})")
            
            cursor.execute('DELETE FROM ai_conversations WHERE id = ?', (delete_id,))
            deleted_count += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Cleanup complete! Deleted {deleted_count} duplicate conversations.")
    print("=" * 60)

if __name__ == "__main__":
    cleanup_duplicates()
