"""
PRODUCTION DATABASE CHECKER
Run this on production to see what schema changes are needed
"""
import sqlite3
import sys

def check_production_database():
    """Check production database for required tables and columns"""
    
    try:
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Cannot connect to database: {e}")
        return False
    
    print("="*70)
    print("🔍 PRODUCTION DATABASE CHECK")
    print("="*70 + "\n")
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Found {len(existing_tables)} tables\n")
    
    # Required tables for AI Usage Monitor
    required_tables = {
        'users': {
            'description': 'User accounts',
            'required_columns': ['id', 'username', 'email', 'user_role'],
            'critical': True
        },
        'ai_usage_log': {
            'description': 'AI call tracking',
            'required_columns': ['id', 'timestamp', 'user_id', 'call_type', 'success', 
                               'is_background', 'is_automated', 'estimated_cost'],
            'critical': True
        },
        'ai_usage_patterns': {
            'description': 'Unusual usage patterns',
            'required_columns': ['id', 'detected_at', 'pattern_type'],
            'critical': False
        },
        'ai_budget_notifications': {
            'description': 'Budget notifications',
            'required_columns': ['id', 'timestamp', 'user_id', 'notification_type'],
            'critical': False
        }
    }
    
    missing_tables = []
    tables_with_missing_columns = []
    all_good = True
    
    for table_name, info in required_tables.items():
        status_icon = "✅" if info['critical'] else "ℹ️"
        
        if table_name in existing_tables:
            # Table exists, check columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            missing_columns = [col for col in info['required_columns'] if col not in columns]
            
            if missing_columns:
                print(f"⚠️  {table_name}")
                print(f"   {info['description']}")
                print(f"   Status: EXISTS but missing columns: {', '.join(missing_columns)}")
                tables_with_missing_columns.append((table_name, missing_columns))
                if info['critical']:
                    all_good = False
            else:
                print(f"{status_icon} {table_name}")
                print(f"   {info['description']}")
                print(f"   Status: OK ({len(columns)} columns)")
        else:
            print(f"❌ {table_name}")
            print(f"   {info['description']}")
            print(f"   Status: MISSING")
            missing_tables.append(table_name)
            if info['critical']:
                all_good = False
        print()
    
    # Summary
    print("="*70)
    print("📋 SUMMARY")
    print("="*70 + "\n")
    
    if all_good:
        print("✅ ALL CRITICAL TABLES AND COLUMNS PRESENT")
        print("   AI Usage Monitor should work correctly!")
        print()
    else:
        print("❌ MISSING CRITICAL SCHEMA ELEMENTS\n")
        
        if missing_tables:
            print(f"🔴 Missing Tables ({len(missing_tables)}):")
            for table in missing_tables:
                print(f"   - {table}")
            print()
        
        if tables_with_missing_columns:
            print(f"🟡 Tables Missing Columns ({len(tables_with_missing_columns)}):")
            for table, columns in tables_with_missing_columns:
                print(f"   - {table}: {', '.join(columns)}")
            print()
        
        print("="*70)
        print("🔧 RECOMMENDED ACTION")
        print("="*70 + "\n")
        print("Run this command to create all missing tables:")
        print("   python migrate_all_tables.py\n")
        print("Then restart Flask:")
        print("   # The AI Budget Manager will initialize ai_usage_log on startup\n")
        print("If user_role column is missing from users table, you'll need to:")
        print("   1. Add it manually, OR")
        print("   2. Run migrate_all_tables.py (safer)\n")
    
    # Show what users exist
    print("="*70)
    print("👥 PRODUCTION USERS")
    print("="*70 + "\n")
    
    try:
        cursor.execute("SELECT username, user_role, email FROM users ORDER BY username")
        users = cursor.fetchall()
        print(f"Found {len(users)} users:\n")
        for username, role, email in users[:10]:  # Show first 10
            role_badge = f"[{role}]" if role else "[no role]"
            print(f"   {username:<20} {role_badge:<20} {email}")
        if len(users) > 10:
            print(f"   ... and {len(users)-10} more")
    except Exception as e:
        print(f"⚠️  Cannot query users: {e}")
        print("   (user_role column might be missing)")
    
    print()
    conn.close()
    
    return all_good

if __name__ == '__main__':
    success = check_production_database()
    sys.exit(0 if success else 1)
