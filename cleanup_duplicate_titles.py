#!/usr/bin/env python3
"""
Clean up conversations with duplicate titles and timestamps
(These have different session_ids but same title/created_at)
"""

import sqlite3

def cleanup_title_duplicates():
    print("🧹 Cleaning up conversations with duplicate titles...")
    print("=" * 60)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Find conversations with same user_id, title, and created_at
    cursor.execute('''
        SELECT user_id, title, created_at, COUNT(*) as count
        FROM ai_conversations
        GROUP BY user_id, title, created_at
        HAVING COUNT(*) > 1
    ''')
    
    duplicate_groups = cursor.fetchall()
    
    if not duplicate_groups:
        print("✅ No title/timestamp duplicates found - database is clean!")
        conn.close()
        return
    
    print(f"\nFound {len(duplicate_groups)} groups of duplicate conversations")
    print("\n⚠️  WARNING: This will DELETE conversations with duplicate titles!")
    print("   It will keep the conversation with the LOWEST ID (oldest) of each group.")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        conn.close()
        return
    
    deleted_count = 0
    
    for user_id, title, created_at, count in duplicate_groups:
        print(f"\n🔧 Processing: User {user_id}, Title '{title}', Created {created_at}")
        print(f"   Found {count} duplicates")
        
        # Get all conversations with this user_id, title, and created_at
        cursor.execute('''
            SELECT id, session_id
            FROM ai_conversations
            WHERE user_id = ? AND title = ? AND created_at = ?
            ORDER BY id ASC
        ''', (user_id, title, created_at))
        
        rows = cursor.fetchall()
        
        # Keep the first (lowest ID), delete the rest
        keep_id = rows[0][0]
        print(f"   ✅ Keeping ID {keep_id} (session: {rows[0][1][:30]}...)")
        
        for row in rows[1:]:
            delete_id = row[0]
            print(f"   ❌ Deleting ID {delete_id} (session: {row[1][:30]}...)")
            
            cursor.execute('DELETE FROM ai_conversations WHERE id = ?', (delete_id,))
            deleted_count += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Cleanup complete! Deleted {deleted_count} duplicate conversations.")
    print("=" * 60)

if __name__ == "__main__":
    cleanup_title_duplicates()
