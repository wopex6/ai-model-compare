#!/usr/bin/env python3
"""
Add user roles and message limit tracking to the database
"""

import sqlite3
from datetime import datetime

def add_user_roles():
    print("🔧 Adding User Roles System")
    print("=" * 60)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # 1. Add user_role column to users table
    print("\n1️⃣ Adding user_role column...")
    try:
        cursor.execute('''
            ALTER TABLE users 
            ADD COLUMN user_role TEXT DEFAULT 'guest'
        ''')
        print("✅ Added user_role column")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️  user_role column already exists")
        else:
            raise
    
    # 2. Create message_usage table for tracking daily limits
    print("\n2️⃣ Creating message_usage table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            message_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, date)
        )
    ''')
    print("✅ Created message_usage table")
    
    # 3. Set Ken as administrator
    print("\n3️⃣ Setting Ken as administrator...")
    cursor.execute('''
        UPDATE users 
        SET user_role = 'administrator' 
        WHERE username = 'Ken'
    ''')
    
    if cursor.rowcount > 0:
        print("✅ Ken is now an administrator")
    else:
        print("⚠️  Ken user not found")
    
    # 4. Set AutoTest as paid user for testing
    print("\n4️⃣ Setting AutoTest as paid user...")
    cursor.execute('''
        UPDATE users 
        SET user_role = 'paid' 
        WHERE username = 'AutoTest'
    ''')
    
    if cursor.rowcount > 0:
        print("✅ AutoTest is now a paid user")
    else:
        print("⚠️  AutoTest user not found")
    
    # 5. Set all other users as guest (default)
    print("\n5️⃣ Setting other users as guests...")
    cursor.execute('''
        UPDATE users 
        SET user_role = 'guest' 
        WHERE user_role IS NULL
    ''')
    print(f"✅ Updated {cursor.rowcount} users to guest role")
    
    conn.commit()
    
    # 6. Display user roles
    print("\n" + "=" * 60)
    print("👥 Current User Roles:")
    print("=" * 60)
    
    cursor.execute('''
        SELECT id, username, user_role 
        FROM users 
        ORDER BY id
    ''')
    
    for row in cursor.fetchall():
        user_id, username, role = row
        icon = "👑" if role == "administrator" else "💎" if role == "paid" else "👤"
        print(f"{icon} {username:20s} - {role:15s} (ID: {user_id})")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 User Roles System Setup Complete!")
    print("=" * 60)
    print("\n📋 Role Permissions:")
    print("   👑 Administrator - Unlimited messages, full access")
    print("   💎 Paid User     - Unlimited messages")
    print("   👤 Guest         - Limited to 2 messages per day (testing)")
    print("\n✅ Database updated successfully!")

if __name__ == "__main__":
    add_user_roles()
