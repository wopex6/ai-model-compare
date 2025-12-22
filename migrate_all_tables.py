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
        
        # ============================================================
        # DOMAIN CHARACTER SYSTEM (Phase 1)
        # ============================================================
        print("\n📦 DOMAIN CHARACTER SYSTEM")
        print("-" * 80)
        
        # Domain characters configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS domain_characters (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                domain TEXT NOT NULL,
                threshold_config TEXT,
                style_config TEXT,
                system_prompt TEXT,
                active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ domain_characters")
        
        # Character interpretations (how each character sees context)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_history_id INTEGER,
                character_id TEXT NOT NULL,
                interpretation TEXT,
                concern_level REAL DEFAULT 0.0,
                responded INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (primary_history_id) REFERENCES history_primary(id)
            )
        ''')
        print("✅ character_interpretations")
        
        # Flexible context storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flexible_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                context_type TEXT NOT NULL,
                context_data TEXT NOT NULL,
                source TEXT,
                retention_years INTEGER DEFAULT 10,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ flexible_context")
        
        # Context interpretations per character
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                interpretation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES flexible_context(id) ON DELETE CASCADE
            )
        ''')
        print("✅ context_interpretations")
        
        # ============================================================
        # NOTIFICATION SYSTEM
        # ============================================================
        print("\n📦 NOTIFICATION SYSTEM")
        print("-" * 80)
        
        # Notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                conversation_context TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                delivered_at DATETIME,
                acknowledged_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ notifications")
        
        # User notification preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notification_preferences (
                user_id INTEGER PRIMARY KEY,
                preferences TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ user_notification_preferences")
        
        # ============================================================
        # FEEDBACK SYSTEM EXTENSIONS
        # ============================================================
        print("\n📦 FEEDBACK SYSTEM")
        print("-" * 80)
        
        # User-character preference scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_character_preferences (
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                preference_score REAL DEFAULT 0.0,
                interaction_count INTEGER DEFAULT 0,
                last_interaction DATETIME,
                PRIMARY KEY (user_id, character_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ user_character_preferences")
        
        # User topic preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_topic_preferences (
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                preference TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, topic),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ user_topic_preferences")
        
        # Proactive triggers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proactive_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trigger_type TEXT NOT NULL,
                character_id TEXT,
                trigger_config TEXT,
                last_triggered DATETIME,
                next_scheduled DATETIME,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("✅ proactive_triggers")
        
        # ============================================================
        # AI PROVIDER ERROR LOGGING
        # ============================================================
        print("\n📦 AI PROVIDER ERROR LOGGING")
        print("-" * 80)
        
        # AI provider errors (for admin monitoring)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_provider_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                provider TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT,
                error_code TEXT,
                character_id TEXT,
                user_id INTEGER,
                request_context TEXT,
                stack_trace TEXT,
                resolved INTEGER DEFAULT 0,
                admin_notes TEXT
            )
        ''')
        print("✅ ai_provider_errors")
        
        # Frontend errors (for debugging)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frontend_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                error_type TEXT,
                error_message TEXT,
                stack_trace TEXT,
                url TEXT,
                user_agent TEXT,
                user_id INTEGER,
                additional_context TEXT
            )
        ''')
        print("✅ frontend_errors")
        
        # AI provider error indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_errors_timestamp 
            ON ai_provider_errors(timestamp DESC)
        ''')
        print("✅ idx_ai_errors_timestamp")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_errors_provider 
            ON ai_provider_errors(provider)
        ''')
        print("✅ idx_ai_errors_provider")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_ai_errors_resolved 
            ON ai_provider_errors(resolved)
        ''')
        print("✅ idx_ai_errors_resolved")
        
        # ============================================================
        # MESSAGE VISIBILITY (Single Storage Architecture)
        # ============================================================
        print("\n📦 MESSAGE VISIBILITY")
        print("-" * 80)
        
        # Track which characters can see each message (avoids duplicate storage)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_visibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                history_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                role TEXT DEFAULT 'viewer',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (history_id) REFERENCES history_primary(id)
            )
        ''')
        print("✅ message_visibility")
        
        # Index for fast character history queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_visibility_character 
            ON message_visibility(character_id, history_id)
        ''')
        print("✅ idx_visibility_character")
        
        # Index for finding all characters for a message
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_visibility_history 
            ON message_visibility(history_id)
        ''')
        print("✅ idx_visibility_history")
        
        # ============================================================
        # CONVERSATION HIGHLIGHTS & PINNED MESSAGES
        # ============================================================
        print("\n📦 CONVERSATION HIGHLIGHTS & PINNED MESSAGES")
        print("-" * 80)
        
        # Conversation highlights (save important parts)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_highlights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT,
                message_id INTEGER,
                highlighted_text TEXT NOT NULL,
                full_message TEXT,
                message_role TEXT,
                note TEXT,
                color TEXT DEFAULT 'green',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ conversation_highlights")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_highlights_user 
            ON conversation_highlights(user_id, created_at DESC)
        ''')
        print("✅ idx_highlights_user")
        
        # Pinned messages (like WhatsApp pin feature)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pinned_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message_id INTEGER,
                character_id TEXT,
                message_content TEXT NOT NULL,
                message_role TEXT NOT NULL,
                message_timestamp TEXT,
                pin_note TEXT,
                pinned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                display_order INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ pinned_messages")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pinned_messages_user 
            ON pinned_messages(user_id, display_order, pinned_at DESC)
        ''')
        print("✅ idx_pinned_messages_user")
        
        # Automated greetings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automated_greetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                greeting_type TEXT NOT NULL,
                greeting_message TEXT NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                triggered_by TEXT,
                context_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ automated_greetings")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_greetings_user_sent 
            ON automated_greetings(user_id, sent_at DESC)
        ''')
        print("✅ idx_greetings_user_sent")
        
        # User activity tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                last_activity_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        print("✅ user_activity_log")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_activity_user_time 
            ON user_activity_log(user_id, last_activity_at DESC)
        ''')
        print("✅ idx_activity_user_time")
        
        # ============================================================
        # DOMAIN CHARACTER INDEXES
        # ============================================================
        print("\n📦 DOMAIN CHARACTER INDEXES")
        print("-" * 80)
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_char_interp_history 
            ON character_interpretations(primary_history_id)
        ''')
        print("✅ idx_char_interp_history")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_char_interp_character 
            ON character_interpretations(character_id)
        ''')
        print("✅ idx_char_interp_character")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_flex_context_user 
            ON flexible_context(user_id, context_type)
        ''')
        print("✅ idx_flex_context_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_flex_context_created 
            ON flexible_context(created_at)
        ''')
        print("✅ idx_flex_context_created")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_notifications_user 
            ON notifications(user_id, created_at)
        ''')
        print("✅ idx_notifications_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_proactive_user 
            ON proactive_triggers(user_id, active)
        ''')
        print("✅ idx_proactive_user")
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_proactive_next 
            ON proactive_triggers(next_scheduled)
        ''')
        print("✅ idx_proactive_next")
        
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
