#!/usr/bin/env python3
"""
Add Master role to the user system
Master role has all Paid User privileges plus access to Phase 3.1 personality features
"""

import sqlite3
from datetime import datetime

def add_master_role():
    print("🔧 Adding Master Role to User System")
    print("=" * 60)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Display current user roles
    print("\n📋 Current User Roles:")
    print("-" * 60)
    cursor.execute('''
        SELECT id, username, user_role 
        FROM users 
        ORDER BY id
    ''')
    
    for row in cursor.fetchall():
        user_id, username, role = row
        icon = "👑" if role == "administrator" else "💎" if role == "paid" else "⭐" if role == "master" else "👤"
        print(f"{icon} {username:20s} - {role:15s} (ID: {user_id})")
    
    # Ask which user to promote to Master
    print("\n" + "=" * 60)
    print("ℹ️  Master Role Features:")
    print("   ✅ All Paid User privileges (unlimited messages)")
    print("   ✅ Access to Phase 3.1 Personality Insights Dashboard")
    print("   ✅ View personality interpretations and analytics")
    print("   ✅ Enhanced personality assessment tools")
    print("\n❌ Does NOT include:")
    print("   ❌ Admin panel access")
    print("   ❌ User management")
    print("   ❌ System administration")
    print("=" * 60)
    
    user_input = input("\nEnter username to promote to Master (or 'skip' to skip): ").strip()
    
    if user_input.lower() != 'skip' and user_input:
        cursor.execute('''
            UPDATE users 
            SET user_role = 'master' 
            WHERE username = ?
        ''', (user_input,))
        
        if cursor.rowcount > 0:
            print(f"✅ {user_input} is now a Master user!")
        else:
            print(f"⚠️  User '{user_input}' not found")
    
    conn.commit()
    
    # Display updated roles
    print("\n" + "=" * 60)
    print("👥 Updated User Roles:")
    print("=" * 60)
    
    cursor.execute('''
        SELECT id, username, user_role 
        FROM users 
        ORDER BY 
            CASE user_role 
                WHEN 'administrator' THEN 1
                WHEN 'master' THEN 2
                WHEN 'paid' THEN 3
                ELSE 4
            END,
            id
    ''')
    
    for row in cursor.fetchall():
        user_id, username, role = row
        if role == "administrator":
            icon = "👑"
            desc = "Full system access"
        elif role == "master":
            icon = "⭐"
            desc = "Paid + Personality Features"
        elif role == "paid":
            icon = "💎"
            desc = "Unlimited messages"
        else:
            icon = "👤"
            desc = "Limited access"
        
        print(f"{icon} {username:20s} - {role:15s} ({desc})")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 Master Role System Setup Complete!")
    print("=" * 60)
    print("\n📋 Role Hierarchy:")
    print("   1. 👑 Administrator - Full system access, all features")
    print("   2. ⭐ Master        - Paid privileges + Personality insights")
    print("   3. 💎 Paid User     - Unlimited messages")
    print("   4. 👤 Guest         - Limited messages")
    print("\n✅ Database updated successfully!")

if __name__ == "__main__":
    add_master_role()
