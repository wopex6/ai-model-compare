#!/usr/bin/env python3
"""
Test user roles and message limits
"""

from integrated_database import IntegratedDatabase
import sqlite3

def test_user_roles():
    print("🧪 Testing User Roles & Message Limits")
    print("=" * 60)
    
    db = IntegratedDatabase()
    
    # Get all users
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, user_role FROM users')
    users = cursor.fetchall()
    conn.close()
    
    print("\n📋 Testing Each User:")
    print("=" * 60)
    
    for user_id, username, role in users:
        print(f"\n👤 {username} (ID: {user_id}, Role: {role})")
        
        # Get user role
        fetched_role = db.get_user_role(user_id)
        print(f"   Role check: {fetched_role}")
        
        # Get message usage
        usage = db.get_message_usage(user_id)
        print(f"   Usage: {usage}")
        
        # Check if can send
        can_send, reason = db.can_send_message(user_id)
        print(f"   Can send: {can_send}")
        if reason:
            print(f"   Reason: {reason}")
        
        # For guest users, test the limit
        if role == 'guest':
            print(f"\n   Testing limit for {username}:")
            for i in range(3):
                can_send, reason = db.can_send_message(user_id)
                if can_send:
                    db.increment_message_count(user_id)
                    usage = db.get_message_usage(user_id)
                    print(f"   Message {i+1}: Sent (Remaining: {usage['remaining']})")
                else:
                    print(f"   Message {i+1}: BLOCKED - {reason}")
    
    print("\n" + "=" * 60)
    print("✅ User Roles Test Complete!")

if __name__ == "__main__":
    test_user_roles()
