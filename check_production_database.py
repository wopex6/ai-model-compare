#!/usr/bin/env python3
"""
Check Production Database - Verify all tables exist
Compares local and production database schemas
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

def get_all_tables(cursor):
    """Get all table names from database"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return {row[0] for row in cursor.fetchall()}

def get_all_indexes(cursor):
    """Get all index names from database"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='index' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return {row[0] for row in cursor.fetchall()}

def check_database():
    """Check what tables should exist"""
    
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)
    print()
    
    # Expected tables from all systems
    EXPECTED_TABLES = {
        # Core user system (integrated_database.py)
        'users',
        'user_profiles',
        'psychology_traits',
        'ai_conversations',
        'messages',
        'user_interactions',
        'admin_messages',
        
        # Smart Response System (migrate_smart_response_tables.py)
        'user_learning_profiles',
        'interaction_history',
        
        # Dual-Layer History (smart_response/dual_layer_history.py)
        'history_primary',
        'history_secondary',
        'history_progress',
        
        # Explicit Context (smart_response/explicit_context_handler.py)
        'explicit_context',
        
        # Personality Trends (smart_response/personality_trend_analyzer.py)
        'inferred_traits',
        
        # Conversation Context (smart_response/conversation_context.py)
        'conversation_context',
        'conversation_topics',
        'followup_suggestions',
        
        # AI Budget Manager (smart_response/ai_budget_manager.py)
        'ai_usage_log',
        'ai_usage_patterns',
        'ai_budget_notifications',
    }
    
    # Expected indexes
    EXPECTED_INDEXES = {
        # Smart Response indexes
        'idx_learning_profiles_updated',
        'idx_interaction_history_user',
        'idx_interaction_history_timestamp',
        'idx_interaction_history_character',
        
        # Admin messages indexes
        'idx_admin_messages_user',
        'idx_admin_messages_read',
        
        # Dual-layer history indexes
        'idx_history_primary_user',
        'idx_history_primary_timestamp',
        'idx_history_secondary_user',
        'idx_history_secondary_primary',
        'idx_history_progress_user',
        
        # Explicit context indexes
        'idx_explicit_context_user',
        'idx_explicit_context_active',
        'idx_explicit_context_timestamp',
        
        # Other common indexes (may vary)
        'idx_messages_conversation',
    }
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        print("   This script must be run in the project directory")
        return None, None, None, None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get actual tables and indexes
        actual_tables = get_all_tables(cursor)
        actual_indexes = get_all_indexes(cursor)
        
        # Find missing tables
        missing_tables = EXPECTED_TABLES - actual_tables
        extra_tables = actual_tables - EXPECTED_TABLES
        
        # Find missing indexes
        missing_indexes = EXPECTED_INDEXES - actual_indexes
        
        # Report
        print("📊 DATABASE STATUS:\n")
        
        print(f"✅ Tables Found: {len(actual_tables)}")
        print(f"📋 Expected Tables: {len(EXPECTED_TABLES)}")
        print(f"🔍 Indexes Found: {len(actual_indexes)}")
        print()
        
        if missing_tables:
            print("❌ MISSING TABLES:")
            for table in sorted(missing_tables):
                print(f"   ❌ {table}")
            print()
        else:
            print("✅ ALL EXPECTED TABLES EXIST!\n")
        
        if missing_indexes:
            print("⚠️  MISSING INDEXES (optional but recommended):")
            for index in sorted(missing_indexes):
                print(f"   ⚠️  {index}")
            print()
        else:
            print("✅ ALL EXPECTED INDEXES EXIST!\n")
        
        if extra_tables:
            print("ℹ️  EXTRA TABLES (not in expected list):")
            for table in sorted(extra_tables):
                print(f"   ℹ️  {table}")
            print()
        
        print("=" * 80)
        
        if missing_tables:
            print("❌ DATABASE NEEDS MIGRATION")
            print("=" * 80)
            print()
            print("Run these migration scripts:")
            print()
            
            if any(t in missing_tables for t in ['user_learning_profiles', 'interaction_history']):
                print("  1. python migrate_smart_response_tables.py")
            
            if 'admin_messages' in missing_tables:
                print("  2. python migrate_admin_messages.py")
            
            if any(t in missing_tables for t in ['history_primary', 'history_secondary', 'history_progress',
                                                   'explicit_context', 'inferred_traits', 'conversation_context',
                                                   'conversation_topics', 'followup_suggestions', 'ai_usage_log',
                                                   'ai_usage_patterns', 'ai_budget_notifications']):
                print("  3. Start the app once - it will auto-create Smart Response tables")
            
            print()
        else:
            print("✅ DATABASE IS UP TO DATE!")
            print("=" * 80)
            print()
        
        return actual_tables, missing_tables, actual_indexes, missing_indexes
        
    finally:
        conn.close()

if __name__ == "__main__":
    print()
    check_database()
    print()
