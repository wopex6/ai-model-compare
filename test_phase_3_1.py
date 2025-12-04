#!/usr/bin/env python3
"""
Test Phase 3.1 Implementation
Tests Master role and personality features
"""

import sys
import sqlite3

def test_phase_3_1():
    print("=" * 70)
    print("🧪 TESTING PHASE 3.1: MASTER ROLE & PERSONALITY FEATURES")
    print("=" * 70)
    
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Test 1: Check for Master role users
    print("\n1️⃣ Checking for Master Role Users...")
    cursor.execute("SELECT id, username, user_role FROM users WHERE user_role = 'master'")
    master_users = cursor.fetchall()
    
    if master_users:
        print(f"✅ Found {len(master_users)} Master user(s):")
        for user_id, username, role in master_users:
            print(f"   ⭐ {username} (ID: {user_id})")
    else:
        print("⚠️  No Master users found. Run 'python add_master_role.py' to create one.")
    
    # Test 2: Verify database methods exist
    print("\n2️⃣ Checking Database Methods...")
    try:
        from integrated_database import IntegratedDatabase
        db = IntegratedDatabase()
        
        # Test has_personality_access method
        if master_users:
            test_user_id = master_users[0][0]
            has_access = db.has_personality_access(test_user_id)
            if has_access:
                print(f"✅ has_personality_access() working correctly")
            else:
                print(f"❌ has_personality_access() returned False for Master user")
        
        # Test get_personality_profile method
        try:
            profile = db.get_personality_profile(1)
            print(f"✅ get_personality_profile() method exists")
        except Exception as e:
            print(f"❌ get_personality_profile() error: {str(e)}")
        
        # Test get_personality_interpretations method
        try:
            interps = db.get_personality_interpretations(1, limit=5)
            print(f"✅ get_personality_interpretations() method exists")
        except Exception as e:
            print(f"❌ get_personality_interpretations() error: {str(e)}")
        
        # Test get_personality_stats method
        try:
            stats = db.get_personality_stats(1)
            print(f"✅ get_personality_stats() method exists")
        except Exception as e:
            print(f"❌ get_personality_stats() error: {str(e)}")
            
    except Exception as e:
        print(f"❌ Error loading IntegratedDatabase: {str(e)}")
    
    # Test 3: Check for personality interpretations table
    print("\n3️⃣ Checking Personality Interpretations Table...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='personality_interpretations'
    """)
    if cursor.fetchone():
        print("✅ personality_interpretations table exists")
        
        # Check for data
        cursor.execute("SELECT COUNT(*) FROM personality_interpretations")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} interpretations in database")
    else:
        print("⚠️  personality_interpretations table not found")
        print("   This is expected if Phase 3 core hasn't been used yet")
    
    # Test 4: Check for psychology_traits table
    print("\n4️⃣ Checking Psychology Traits Table...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='psychology_traits'
    """)
    if cursor.fetchone():
        print("✅ psychology_traits table exists")
        
        # Check for data
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM psychology_traits")
        count = cursor.fetchone()[0]
        print(f"   📊 {count} user(s) have personality assessments")
    else:
        print("⚠️  psychology_traits table not found")
    
    # Test 5: Check for inferred_traits table
    print("\n5️⃣ Checking Inferred Traits Table...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='inferred_traits'
    """)
    if cursor.fetchone():
        print("✅ inferred_traits table exists")
    else:
        print("⚠️  inferred_traits table not found")
    
    # Test 6: Verify file existence
    print("\n6️⃣ Checking Implementation Files...")
    import os
    
    files_to_check = [
        ('templates/personality_dashboard.html', 'Personality Dashboard'),
        ('static/personality_interpretation_display.js', 'Inline Display Module'),
        ('add_master_role.py', 'Master Role Setup Script'),
        ('PHASE_3_1_IMPLEMENTATION_COMPLETE.md', 'Documentation')
    ]
    
    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            print(f"✅ {description} - Found")
        else:
            print(f"❌ {description} - Missing: {filepath}")
    
    # Test 7: Check app.py for new routes
    print("\n7️⃣ Checking API Routes in app.py...")
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        routes_to_check = [
            ("/personality-dashboard", "Dashboard Route"),
            ("/api/personality/profile", "Profile API"),
            ("/api/personality/interpretations", "Interpretations API"),
            ("/api/personality/stats", "Stats API"),
        ]
        
        for route, description in routes_to_check:
            if route in content:
                print(f"✅ {description} - Found")
            else:
                print(f"❌ {description} - Missing")
                
    except Exception as e:
        print(f"❌ Error reading app.py: {str(e)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    if master_users:
        print("✅ Master role system is active")
        print(f"✅ {len(master_users)} Master user(s) configured")
    else:
        print("⚠️  No Master users yet - run 'python add_master_role.py'")
    
    print("\n📝 Next Steps:")
    print("1. Run 'python add_master_role.py' to create Master users")
    print("2. Login as Master user at http://localhost:5000/chatchat")
    print("3. Look for 'Personality Insights ⭐' button in navbar")
    print("4. Click to access dashboard")
    print("5. Test API endpoints manually or with browser dev tools")
    
    print("\n🔗 URLs to Test:")
    print("   • Dashboard: http://localhost:5000/personality-dashboard")
    print("   • Profile API: http://localhost:5000/api/personality/profile")
    print("   • Interpretations: http://localhost:5000/api/personality/interpretations")
    print("   • Stats API: http://localhost:5000/api/personality/stats")
    
    print("\n" + "=" * 70)
    print("🎉 Phase 3.1 Testing Complete!")
    print("=" * 70)
    
    conn.close()

if __name__ == "__main__":
    try:
        test_phase_3_1()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
