-- Database Schema Export
-- Generated: 2025-12-09 22:44:26
-- Source: integrated_users.db
-- 
-- Instructions:
-- 1. Upload this file to PythonAnywhere
-- 2. Run: python apply_schema_migration.py
-- 

-- ============================================================
-- TABLE DEFINITIONS
-- ============================================================

CREATE TABLE admin_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'admin')),
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, file_url TEXT, file_name TEXT, file_size INTEGER, reply_to INTEGER DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

CREATE TABLE ai_budget_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notification_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT 0
            );

CREATE TABLE ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                title TEXT,
                conversation_data TEXT,  -- JSON string for conversation history
                personality_data TEXT,   -- JSON string for personality settings
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, character_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

CREATE TABLE ai_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- What was called
                call_type TEXT NOT NULL,
                character TEXT,
                user_id INTEGER,
                
                -- Cost tracking
                estimated_cost FLOAT NOT NULL,
                
                -- Context
                purpose TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                
                -- Result
                success BOOLEAN,
                error_message TEXT,
                
                -- Flags
                is_background BOOLEAN DEFAULT 0,
                is_automated BOOLEAN DEFAULT 0
            );

CREATE TABLE ai_usage_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Pattern details
                pattern_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                
                -- Data
                call_count INTEGER,
                time_window_minutes INTEGER,
                cost_impact FLOAT,
                
                -- Action taken
                action_taken TEXT,
                resolved_at TIMESTAMP
            );

CREATE TABLE archival_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contexts_archived INTEGER DEFAULT 0,
                contexts_expired INTEGER DEFAULT 0,
                contexts_decayed INTEGER DEFAULT 0,
                oldest_archived_days INTEGER,
                notes TEXT
            );

CREATE TABLE assessment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                assessment_version TEXT DEFAULT 'big5_v1',
                openness REAL,
                conscientiousness REAL,
                extraversion REAL,
                agreeableness REAL,
                neuroticism REAL,
                completion_time_seconds INTEGER,
                questions_answered INTEGER DEFAULT 44,
                started_at DATETIME,
                completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

CREATE TABLE conversation_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                context_type TEXT NOT NULL,
                context_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, character, context_type)
            );

CREATE TABLE conversation_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                topic TEXT NOT NULL,
                first_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mention_count INTEGER DEFAULT 1,
                importance_score FLOAT DEFAULT 0.5
            );

CREATE TABLE "explicit_context" (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        character TEXT NOT NULL,
        
        -- When and what
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        context_type TEXT NOT NULL,
        context_key TEXT NOT NULL,
        context_value TEXT NOT NULL,
        
        -- The actual words user said
        original_statement TEXT NOT NULL,
        
        -- Priority and confidence
        priority TEXT NOT NULL,
        confidence FLOAT DEFAULT 1.0,
        
        -- Lifecycle
        active BOOLEAN DEFAULT 1,
        expires_at TIMESTAMP,
        
        -- Metadata
        extracted_via TEXT
        
        -- NO UNIQUE CONSTRAINT - allow historical tracking!
    , original_confidence REAL DEFAULT 1.0);

CREATE TABLE explicit_context_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_id INTEGER,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context_type TEXT NOT NULL,
                context_key TEXT,
                context_value TEXT NOT NULL,
                original_statement TEXT,
                priority TEXT DEFAULT 'NORMAL',
                confidence REAL DEFAULT 1.0,
                original_confidence REAL DEFAULT 1.0,
                active INTEGER DEFAULT 1,
                expires_at TIMESTAMP,
                extracted_via TEXT DEFAULT 'regex',
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archive_reason TEXT
            );

CREATE TABLE followup_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                context_snapshot TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP,
                was_used BOOLEAN DEFAULT 0
            );

CREATE TABLE frontend_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            error_message TEXT NOT NULL,
            character TEXT,
            context TEXT,
            user_agent TEXT,
            url TEXT,
            stack_trace TEXT
        );

CREATE TABLE history_primary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Raw data
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                response_type TEXT,
                
                -- Metadata
                session_id TEXT,
                message_length INTEGER,
                response_time_ms INTEGER,
                
                -- Source of truth marker
                is_primary BOOLEAN DEFAULT 1
            );

CREATE TABLE history_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                
                -- What we're tracking
                goal_category TEXT,
                metric_name TEXT,
                
                -- Timeline
                tracking_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Data points (JSON array)
                data_points TEXT NOT NULL,
                
                -- Trend analysis
                trend_direction TEXT,
                trend_confidence FLOAT,
                
                -- Related messages
                related_primary_ids TEXT
            );

CREATE TABLE history_secondary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Interpreted data
                detected_intent TEXT,
                emotional_tone TEXT,
                topics_extracted TEXT,
                personality_interpretation TEXT,
                
                -- Context snapshot
                context_snapshot TEXT,
                
                -- Insights
                progress_indicators TEXT,
                concerns_identified TEXT,
                opportunities_spotted TEXT,
                
                -- Guidance
                suggested_actions TEXT,
                follow_up_recommended TEXT,
                
                -- Meta
                analysis_confidence FLOAT,
                analysis_version TEXT DEFAULT 'v1.0', interpretation_confidence REAL DEFAULT 0.0, personality_traits_used TEXT,
                
                FOREIGN KEY (primary_id) REFERENCES history_primary(id)
            );

CREATE TABLE inferred_personality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    openness REAL NOT NULL DEFAULT 0.5,
                    conscientiousness REAL NOT NULL DEFAULT 0.5,
                    extraversion REAL NOT NULL DEFAULT 0.5,
                    agreeableness REAL NOT NULL DEFAULT 0.5,
                    neuroticism REAL NOT NULL DEFAULT 0.5,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    message_count INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                );

CREATE TABLE inferred_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                
                trait_category TEXT NOT NULL,
                trait_name TEXT NOT NULL,
                confidence FLOAT NOT NULL,
                
                evidence_count INTEGER NOT NULL,
                evidence_summary TEXT,
                
                first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                active BOOLEAN DEFAULT 1,
                
                UNIQUE(user_id, character, trait_category, trait_name)
            );

CREATE TABLE interaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT,
                response_type TEXT,  -- 'quick_reply' or 'full_ai'
                character TEXT,
                satisfaction_score REAL,  -- 0.0 to 1.0
                satisfaction_signals TEXT,  -- JSON array
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

CREATE TABLE message_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            message_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, date)
        );

CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'assistant')),
                content TEXT NOT NULL,
                metadata TEXT,  -- JSON string for additional message data
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
            );

CREATE TABLE pattern_analysis_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                messages_analyzed INTEGER DEFAULT 0,
                patterns_suggested INTEGER DEFAULT 0,
                ai_calls_used INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error_message TEXT
            );

CREATE TABLE pattern_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                pattern_regex TEXT,
                context_type TEXT,
                match_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                false_positive_count INTEGER DEFAULT 0,
                last_matched TIMESTAMP,
                avg_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pattern_id) REFERENCES pattern_suggestions(id)
            );

CREATE TABLE pattern_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_regex TEXT NOT NULL,
                context_type TEXT NOT NULL,
                description TEXT,
                sample_matches TEXT,
                confidence REAL DEFAULT 0.6,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                activated_at TIMESTAMP,
                match_count INTEGER DEFAULT 0,
                false_positive_count INTEGER DEFAULT 0,
                notes TEXT
            );

CREATE TABLE personality_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                event_type TEXT NOT NULL,
                raw_event TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                interpretation TEXT NOT NULL,
                emotional_impact TEXT,
                recommended_approach TEXT,
                confidence REAL NOT NULL,
                traits_used TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

CREATE TABLE psychology_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trait_name TEXT NOT NULL,
                trait_value REAL NOT NULL,
                trait_description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, trait_name)
            );

CREATE TABLE user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                interaction_data TEXT,  -- JSON string
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

CREATE TABLE user_learning_profiles (
                user_id INTEGER PRIMARY KEY,
                profile_data TEXT,  -- JSON with learning data
                interaction_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

CREATE TABLE user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                first_name TEXT,
                last_name TEXT,
                bio TEXT,
                avatar_url TEXT,
                birth_date DATE,
                location TEXT,
                preferences TEXT,  -- JSON string for preferences
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );

CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            , user_role TEXT DEFAULT 'guest', email_verified INTEGER DEFAULT 0, verification_code TEXT, verification_expires DATETIME, is_deleted INTEGER DEFAULT 0);


-- ============================================================
-- INDEX DEFINITIONS
-- ============================================================

CREATE INDEX idx_assessment_history_user 
            ON assessment_history(user_id, completed_at DESC)
        ;

CREATE INDEX idx_conversations_session 
                    ON ai_conversations(session_id)
                ;

CREATE INDEX idx_conversations_user_character 
                    ON ai_conversations(user_id, character_id)
                ;

CREATE INDEX idx_explicit_context_lookup 
    ON explicit_context(user_id, character, context_type, active)
;

CREATE INDEX idx_explicit_priority
            ON explicit_context(priority, active)
        ;

CREATE INDEX idx_explicit_user_active
            ON explicit_context(user_id, character, active)
        ;

CREATE INDEX idx_frontend_errors_timestamp
        ON frontend_errors(timestamp DESC)
    ;

CREATE INDEX idx_inferred_user_active
            ON inferred_traits(user_id, character, active)
        ;

CREATE INDEX idx_interaction_history_character 
            ON interaction_history(character)
        ;

CREATE INDEX idx_interaction_history_timestamp 
            ON interaction_history(timestamp)
        ;

CREATE INDEX idx_interaction_history_user 
            ON interaction_history(user_id)
        ;

CREATE INDEX idx_learning_profiles_updated 
            ON user_learning_profiles(last_updated)
        ;

CREATE INDEX idx_personality_interp_user 
            ON personality_interpretations(user_id, created_at DESC)
        ;

CREATE INDEX idx_primary_session 
            ON history_primary(session_id)
        ;

CREATE INDEX idx_primary_user_time 
            ON history_primary(user_id, timestamp)
        ;

CREATE INDEX idx_progress_user_goal 
            ON history_progress(user_id, goal_category)
        ;

CREATE INDEX idx_secondary_primary 
            ON history_secondary(primary_id)
        ;

CREATE INDEX idx_secondary_user 
            ON history_secondary(user_id, analysis_timestamp)
        ;

CREATE INDEX idx_usage_timestamp 
            ON ai_usage_log(timestamp)
        ;

CREATE INDEX idx_usage_type_time 
            ON ai_usage_log(call_type, timestamp)
        ;

CREATE INDEX idx_usage_user_time 
            ON ai_usage_log(user_id, timestamp)
        ;

