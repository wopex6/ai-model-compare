#!/usr/bin/env python3
"""
Check for duplicate chat conversations in the database
"""

import sqlite3
from collections import Counter

def check_duplicates():
    print("🔍 Checking for duplicate chats in database...")
    print("=" * 60)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Check for duplicate session_ids
    cursor.execute('''
        SELECT session_id, COUNT(*) as count
        FROM ai_conversations
        GROUP BY session_id
        HAVING COUNT(*) > 1
    ''')
    
    duplicate_sessions = cursor.fetchall()
    
    if duplicate_sessions:
        print("\n❌ DUPLICATE SESSION IDs FOUND:")
        for session_id, count in duplicate_sessions:
            print(f"   Session: {session_id} appears {count} times")
            
            # Show details
            cursor.execute('''
                SELECT id, user_id, title, created_at
                FROM ai_conversations
                WHERE session_id = ?
            ''', (session_id,))
            
            print(f"   Details:")
            for row in cursor.fetchall():
                print(f"     - ID: {row[0]}, User: {row[1]}, Title: {row[2]}, Created: {row[3]}")
    else:
        print("\n✅ No duplicate session_ids found")
    
    print("\n" + "=" * 60)
    
    # Check for conversations with same title and timestamp (likely duplicates)
    cursor.execute('''
        SELECT user_id, title, created_at, COUNT(*) as count
        FROM ai_conversations
        GROUP BY user_id, title, created_at
        HAVING COUNT(*) > 1
    ''')
    
    duplicate_titles = cursor.fetchall()
    
    if duplicate_titles:
        print("\n⚠️  CONVERSATIONS WITH SAME TITLE AND TIMESTAMP:")
        for user_id, title, created_at, count in duplicate_titles:
            print(f"   User: {user_id}, Title: {title}, Created: {created_at}")
            print(f"   Appears {count} times (likely duplicates)")
    else:
        print("\n✅ No conversations with identical title+timestamp")
    
    print("\n" + "=" * 60)
    
    # Show total conversation count per user
    cursor.execute('''
        SELECT user_id, COUNT(*) as total_chats
        FROM ai_conversations
        GROUP BY user_id
    ''')
    
    print("\n📊 Total conversations per user:")
    for user_id, total in cursor.fetchall():
        print(f"   User {user_id}: {total} conversations")
    
    conn.close()
    print("\n" + "=" * 60)
    print("✅ Diagnostic complete!")
    
    if duplicate_sessions or duplicate_titles:
        print("\n💡 To clean up duplicates, you can:")
        print("   1. Run: python cleanup_duplicate_chats.py")
        print("   2. Or manually delete duplicates from the database")

if __name__ == "__main__":
    check_duplicates()
