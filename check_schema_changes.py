"""
Check what database schema changes are needed for production deployment
"""
import sqlite3

def check_local_schema():
    """Check what tables exist in local database"""
    conn = sqlite3.connect('integrated_users.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("📊 LOCAL DATABASE SCHEMA:")
    print(f"   Total tables: {len(tables)}\n")
    
    # Critical tables for AI Usage Monitor
    critical_tables = {
        'ai_usage_log': 'AI call tracking (REQUIRED for Monitor)',
        'ai_usage_patterns': 'Unusual pattern detection',
        'ai_budget_notifications': 'Budget notifications',
        'users': 'User accounts',
        'user_learning_profiles': 'Smart response learning',
        'interaction_history': 'Interaction tracking'
    }
    
    print("🔍 CRITICAL TABLES STATUS:\n")
    for table_name, description in critical_tables.items():
        if table_name in tables:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"✅ {table_name}")
            print(f"   {description}")
            print(f"   Columns: {len(columns)}")
            
            # Show key columns for ai_usage_log
            if table_name == 'ai_usage_log':
                col_names = [col[1] for col in columns]
                print(f"   Key columns: {', '.join(col_names[:8])}...")
                
                # Check for is_background and is_automated flags
                if 'is_background' in col_names and 'is_automated' in col_names:
                    print(f"   ✓ Has user/auto call separation flags")
                else:
                    print(f"   ⚠️  Missing is_background/is_automated flags")
                    
        else:
            print(f"❌ {table_name}")
            print(f"   {description}")
            print(f"   STATUS: MISSING - needs migration!")
        print()
    
    # Check users table for user_role column
    if 'users' in tables:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print("🔍 USERS TABLE CHECK:")
        if 'user_role' in columns:
            print("   ✅ user_role column exists")
        else:
            print("   ❌ user_role column MISSING - Monitor will fail!")
        print()
    
    # Show all tables
    print("\n📋 ALL TABLES IN LOCAL DATABASE:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table:<35} {count:>6} rows")
    
    conn.close()
    
    return tables

def list_migration_scripts():
    """List available migration scripts"""
    import os
    
    print("\n\n🔧 AVAILABLE MIGRATION SCRIPTS:\n")
    
    scripts = [
        ('integrated_database.py', 'Base schema (users, profiles, conversations)'),
        ('migrate_all_tables.py', 'Complete schema (ALL tables)'),
        ('migrate_smart_response_tables.py', 'Smart response tables'),
        ('migrate_admin_messages.py', 'Admin messaging'),
        ('smart_response/ai_budget_manager.py', 'AI budget & usage tracking (CRITICAL for Monitor)')
    ]
    
    for script, description in scripts:
        exists = os.path.exists(script)
        status = "✅" if exists else "❌"
        print(f"{status} {script}")
        print(f"   {description}")
        print()

def production_deployment_steps():
    """Show what needs to be done for production"""
    print("\n" + "="*70)
    print("🚀 PRODUCTION DEPLOYMENT CHECKLIST")
    print("="*70 + "\n")
    
    print("📋 DATABASE CHANGES NEEDED FOR AI USAGE MONITOR:\n")
    
    print("1. ✅ USERS TABLE")
    print("   - Need 'user_role' column")
    print("   - Run: migrate_all_tables.py OR check/add manually\n")
    
    print("2. ✅ AI_USAGE_LOG TABLE (CRITICAL)")
    print("   - Tracks all AI calls")
    print("   - Columns: user_id, timestamp, call_type, character,")
    print("             estimated_cost, success, is_background, is_automated")
    print("   - Created by: ai_budget_manager.py initialization")
    print("   - Status: AUTO-CREATED on first Flask run\n")
    
    print("3. ✅ AI_USAGE_PATTERNS TABLE")
    print("   - Tracks unusual usage patterns")
    print("   - Status: AUTO-CREATED on first Flask run\n")
    
    print("4. ✅ AI_BUDGET_NOTIFICATIONS TABLE")
    print("   - Stores budget warnings")
    print("   - Status: AUTO-CREATED on first Flask run\n")
    
    print("⚠️  PRODUCTION DEPLOYMENT STEPS:\n")
    print("1. Pull latest code to production:")
    print("   git pull origin main\n")
    
    print("2. Check if ai_usage_log exists:")
    print("   python -c \"import sqlite3; c=sqlite3.connect('integrated_users.db');")
    print("   print('ai_usage_log' in [r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\\'table\\'')]);\"")
    print()
    
    print("3. If missing, run:")
    print("   python migrate_all_tables.py")
    print("   (This will create ALL missing tables including ai_usage_log)\n")
    
    print("4. Restart Flask:")
    print("   - AI Budget Manager will initialize on startup")
    print("   - This auto-creates ai_usage_log if missing\n")
    
    print("5. Verify Monitor works:")
    print("   http://your-production-domain/admin/ai-usage-monitor")
    print()

if __name__ == '__main__':
    tables = check_local_schema()
    list_migration_scripts()
    production_deployment_steps()
