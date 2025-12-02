#!/usr/bin/env python3
"""
COMPREHENSIVE DATABASE MIGRATION
Creates ALL missing tables and indexes for production deployment

Run this on PythonAnywhere to ensure database is fully up to date.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'integrated_users.db'

def migrate_all_tables():
    """Create all tables and indexes needed for the application"""
    
    print("=" * 80)
    print("COMPREHENSIVE DATABASE MIGRATION")
    print("=" * 80)
    print()
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        tables_created = 0
        indexes_created = 0
        
        # ============================================================
        # CORE USER SYSTEM TABLES
        # ============================================================
        print("📦 CORE USER SYSTEM")
        print("-" * 80)
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ users")
        
        # User profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                first_name TEXT,
                last_name TEXT,
                bio TEXT,
                avatar_url TEXT,
                birth_date DATE,
                location TEXT,
                preferences TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ user_profiles")
        
        # Psychology traits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS psychology_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trait_name TEXT NOT NULL,
                trait_value REAL NOT NULL,
                trait_description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, trait_name)
            )
        ''')
        print("✅ psychology_traits")
        
        # AI conversations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                title TEXT,
                conversation_data TEXT,
                personality_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ ai_conversations")
        
        # Messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'assistant')),
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
            )
        ''')
        print("✅ messages")
        
        # User interactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                interaction_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ user_interactions")
        
        # Admin messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'admin')),
                message TEXT,
                is_read INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_url TEXT,
                file_name TEXT,
                file_size INTEGER,
                reply_to INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (reply_to) REFERENCES admin_messages (id) ON DELETE SET NULL
            )
        ''')
        print("✅ admin_messages")
        
        # ============================================================
        # SMART RESPONSE SYSTEM TABLES
        # ============================================================
        print("\n📦 SMART RESPONSE SYSTEM")
        print("-" * 80)
        
        # User learning profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_learning_profiles (
                user_id INTEGER PRIMARY KEY,
                profile_data TEXT,
                interaction_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ user_learning_profiles")
        
        # Interaction history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT,
                response_type TEXT,
                character TEXT,
                satisfaction_score REAL,
                satisfaction_signals TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ interaction_history")
        
        # ============================================================
        # DUAL-LAYER HISTORY SYSTEM
        # ============================================================
        print("\n📦 DUAL-LAYER HISTORY")
        print("-" * 80)
        
        # Primary layer
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_primary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id TEXT,
                metadata TEXT
            )
        ''')
        print("✅ history_primary")
        
        # Secondary layer
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_secondary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                intent TEXT,
                emotions TEXT,
                topics TEXT,
                progress_indicators TEXT,
                concerns TEXT,
                opportunities TEXT,
                analysis_version INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (primary_id) REFERENCES history_primary(id) ON DELETE CASCADE
            )
        ''')
        print("✅ history_secondary")
        
        # Progress tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                period_start DATE NOT NULL,
                period_end DATE NOT NULL,
                progress_summary TEXT,
                key_milestones TEXT,
                trend_direction TEXT,
                confidence_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ history_progress")
        
        # ============================================================
        # EXPLICIT CONTEXT SYSTEM
        # ============================================================
        print("\n📦 EXPLICIT CONTEXT")
        print("-" * 80)
        
        # Explicit context
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS explicit_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                context_type TEXT NOT NULL,
                context_key TEXT NOT NULL,
                context_value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                active INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                extracted_via TEXT
            )
        ''')
        print("✅ explicit_context")
        
        # ============================================================
        # PERSONALITY TREND ANALYSIS
        # ============================================================
        print("\n📦 PERSONALITY TRENDS")
        print("-" * 80)
        
        # Inferred traits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inferred_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                category TEXT NOT NULL,
                trait TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ inferred_traits")
        
        # ============================================================
        # CONVERSATION CONTEXT
        # ============================================================
        print("\n📦 CONVERSATION CONTEXT")
        print("-" * 80)
        
        # Conversation context
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                context_summary TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ conversation_context")
        
        # Conversation topics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                topic TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ conversation_topics")
        
        # Follow-up suggestions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS followup_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ followup_suggestions")
        
        # ============================================================
        # AI BUDGET MANAGER
        # ============================================================
        print("\n📦 AI BUDGET CONTROL")
        print("-" * 80)
        
        # AI usage log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                character TEXT,
                purpose TEXT,
                cost REAL,
                tokens_used INTEGER,
                success INTEGER,
                error TEXT
            )
        ''')
        print("✅ ai_usage_log")
        
        # AI usage patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pattern_type TEXT,
                severity TEXT,
                description TEXT,
                data TEXT
            )
        ''')
        print("✅ ai_usage_patterns")
        
        # AI budget notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_budget_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT,
                acknowledged INTEGER DEFAULT 0
            )
        ''')
        print("✅ ai_budget_notifications")
        
        # ============================================================
        # INDEXES FOR PERFORMANCE
        # ============================================================
        print("\n📦 CREATING INDEXES")
        print("-" * 80)
        
        # Smart Response indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_learning_profiles_updated 
            ON user_learning_profiles(last_updated)
        ''')
        print("✅ idx_learning_profiles_updated")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interaction_history_user 
            ON interaction_history(user_id)
        ''')
        print("✅ idx_interaction_history_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interaction_history_timestamp 
            ON interaction_history(timestamp)
        ''')
        print("✅ idx_interaction_history_timestamp")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interaction_history_character 
            ON interaction_history(character)
        ''')
        print("✅ idx_interaction_history_character")
        
        # Admin messages indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_admin_messages_user 
            ON admin_messages(user_id)
        ''')
        print("✅ idx_admin_messages_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_admin_messages_read 
            ON admin_messages(is_read)
        ''')
        print("✅ idx_admin_messages_read")
        
        # Dual-layer history indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_history_primary_user 
            ON history_primary(user_id, character)
        ''')
        print("✅ idx_history_primary_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_history_primary_timestamp 
            ON history_primary(timestamp)
        ''')
        print("✅ idx_history_primary_timestamp")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_history_secondary_user 
            ON history_secondary(user_id, character)
        ''')
        print("✅ idx_history_secondary_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_history_secondary_primary 
            ON history_secondary(primary_id)
        ''')
        print("✅ idx_history_secondary_primary")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_history_progress_user 
            ON history_progress(user_id, character)
        ''')
        print("✅ idx_history_progress_user")
        
        # Explicit context indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_explicit_context_user 
            ON explicit_context(user_id, character)
        ''')
        print("✅ idx_explicit_context_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_explicit_context_active 
            ON explicit_context(active)
        ''')
        print("✅ idx_explicit_context_active")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_explicit_context_timestamp 
            ON explicit_context(timestamp)
        ''')
        print("✅ idx_explicit_context_timestamp")
        
        # Messages index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_conversation 
            ON messages(conversation_id)
        ''')
        print("✅ idx_messages_conversation")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 80)
        print()
        print("📊 All tables and indexes created successfully!")
        print("🎉 Database is ready for production!")
        print()
        print("⚠️  IMPORTANT: Reload your web app for changes to take effect!")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print()
    success = migrate_all_tables()
    
    if not success:
        print("=" * 80)
        print("❌ Migration failed! Check errors above.")
        print("=" * 80)
        print()
