#!/usr/bin/env python3
"""
Quick verification script to check if production database is ready for Phase 3.1
"""

import sqlite3
import os

def verify_production_ready():
    print("🔍 Phase 3.1 Production Readiness Check")
    print("=" * 60)
    
    db_path = 'integrated_users.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    all_passed = True
    
    # Check 1: user_role column
    print("\n✓ Checking user_role column...")
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'user_role' in columns:
        print("  ✅ user_role column exists")
    else:
        print("  ❌ user_role column missing")
        all_passed = False
    
    # Check 2: Master/Admin users
    print("\n✓ Checking for Master/Admin users...")
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_role IN ('master', 'administrator')")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"  ✅ Found {count} Master/Admin user(s)")
        cursor.execute("SELECT username, user_role FROM users WHERE user_role IN ('master', 'administrator')")
        for username, role in cursor.fetchall():
            icon = "👑" if role == "administrator" else "⭐"
            print(f"     {icon} {username} ({role})")
    else:
        print("  ⚠️  No Master/Admin users found")
        print("     Run: python add_master_role.py")
    
    # Check 3: personality_interpretations table
    print("\n✓ Checking personality_interpretations table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='personality_interpretations'")
    if cursor.fetchone():
        print("  ✅ personality_interpretations table exists")
        cursor.execute("SELECT COUNT(*) FROM personality_interpretations")
        count = cursor.fetchone()[0]
        print(f"     📊 Contains {count} interpretation(s)")
    else:
        print("  ❌ personality_interpretations table missing")
        all_passed = False
    
    # Check 4: message_usage table
    print("\n✓ Checking message_usage table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message_usage'")
    if cursor.fetchone():
        print("  ✅ message_usage table exists")
    else:
        print("  ❌ message_usage table missing")
        all_passed = False
    
    # Check 5: history_secondary personality columns
    print("\n✓ Checking history_secondary personality columns...")
    cursor.execute("PRAGMA table_info(history_secondary)")
    columns = [row[1] for row in cursor.fetchall()]
    personality_cols = ['personality_interpretation', 'personality_confidence', 'personality_source']
    missing = [col for col in personality_cols if col not in columns]
    
    if not missing:
        print("  ✅ All personality columns exist")
    else:
        print(f"  ❌ Missing columns: {', '.join(missing)}")
        all_passed = False
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ PRODUCTION READY!")
        print("=" * 60)
        print("\n🎯 Next steps:")
        print("   1. Ensure Master/Admin users are configured")
        print("   2. Start application: python app.py")
        print("   3. Test Personality Insights Dashboard")
        return True
    else:
        print("❌ NOT READY - Migration needed")
        print("=" * 60)
        print("\n🔧 Run migration:")
        print("   python migrate_production_phase_3_1.py")
        return False

if __name__ == "__main__":
    verify_production_ready()
