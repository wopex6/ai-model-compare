"""
List all users in the database
"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'integrated_users.db')

def list_users():
    """List all users in the database"""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📊 Database: {db_path}")
    print(f"📋 Tables in database: {[t[0] for t in tables]}\n")
    
    cursor.execute('''
        SELECT id, username, email, created_at 
        FROM users 
        ORDER BY created_at DESC
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    print("=" * 80)
    print("📋 ALL USERS IN DATABASE")
    print("=" * 80)
    print(f"Total users: {len(users)}\n")
    
    if users:
        print(f"{'ID':<5} {'Username':<30} {'Email':<35} {'Created'}")
        print("-" * 80)
        for user in users:
            user_id, username, email, created_at = user
            print(f"{user_id:<5} {username:<30} {email:<35} {created_at}")
    else:
        print("No users found in database.")
    
    print("=" * 80)

if __name__ == "__main__":
    list_users()
