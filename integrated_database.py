import sqlite3
import bcrypt
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

class IntegratedDatabase:
    """
    Integrated database system that combines multi-user authentication
    with AI chatbot conversation and personality management
    """
    
    def __init__(self, db_path: str = "integrated_users.db"):
        self.db_path = Path(db_path)
        self.init_database()
        self.create_default_user()
        self.add_email_verification_columns()
        self.migrate_add_character_id()  # NEW: Add character_id column
        
        # Initialize PersonalityResolver (lazy import to avoid circular dependency)
        self._resolver = None
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table for authentication
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
        
        # User profiles table
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
                preferences TEXT,  -- JSON string for preferences
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Psychology traits table (current/active assessment)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS psychology_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trait_name TEXT NOT NULL,
                trait_value REAL NOT NULL,
                trait_description TEXT,
                source TEXT DEFAULT 'assessment',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, trait_name)
            )
        ''')
        
        # Assessment history table (Phase 3.2 - track all assessments)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment_history (
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
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_assessment_history_user 
            ON assessment_history(user_id, completed_at DESC)
        ''')
        
        # AI Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT UNIQUE NOT NULL,
                title TEXT,
                conversation_data TEXT,  -- JSON string for conversation history
                personality_data TEXT,   -- JSON string for personality settings
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Messages table for detailed message tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'assistant')),
                content TEXT NOT NULL,
                metadata TEXT,  -- JSON string for additional message data
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
            )
        ''')
        
        # User interactions table for tracking AI usage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                interaction_data TEXT,  -- JSON string
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Admin messages table for user-admin communication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'admin')),
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Conversation highlights table for saving important parts
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
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_highlights_user 
            ON conversation_highlights(user_id, created_at DESC)
        ''')
        
        # Automated greetings table
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
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_greetings_user_sent 
            ON automated_greetings(user_id, sent_at DESC)
        ''')
        
        # Pinned messages table (like WhatsApp pin feature)
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
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pinned_messages_user 
            ON pinned_messages(user_id, display_order, pinned_at DESC)
        ''')
        
        # User activity tracking table
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
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_activity_user_time 
            ON user_activity_log(user_id, last_activity_at DESC)
        ''')
        
        # User greeting preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_greeting_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                enabled BOOLEAN DEFAULT 1,
                preferred_time_hour INTEGER DEFAULT 9,
                inactivity_minutes INTEGER DEFAULT 10,
                last_daily_greeting DATETIME,
                last_inactivity_greeting DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # ==================== GOAL COACHING SYSTEM ====================
        # User goals table - tracks what users want to achieve
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_title TEXT NOT NULL,
                goal_description TEXT,
                goal_type TEXT DEFAULT 'general',
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                target_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_goals_user_status 
            ON user_goals(user_id, status, priority DESC)
        ''')
        
        # Goal strategies - AI-generated strategies behind the scenes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                strategy_phase TEXT DEFAULT 'discovery',
                current_step INTEGER DEFAULT 1,
                total_steps INTEGER,
                strategy_json TEXT,
                next_action TEXT,
                next_question TEXT,
                validation_needed TEXT,
                last_user_input TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES user_goals (id) ON DELETE CASCADE
            )
        ''')
        
        # Goal milestones - trackable progress markers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                milestone_title TEXT NOT NULL,
                milestone_description TEXT,
                sequence_order INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                due_date DATE,
                completed_at DATETIME,
                celebration_sent BOOLEAN DEFAULT 0,
                FOREIGN KEY (goal_id) REFERENCES user_goals (id) ON DELETE CASCADE
            )
        ''')
        
        # Goal follow-ups - scheduled proactive check-ins
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                followup_type TEXT DEFAULT 'check_in',
                followup_question TEXT NOT NULL,
                context_summary TEXT,
                scheduled_for DATETIME,
                sent_at DATETIME,
                user_responded BOOLEAN DEFAULT 0,
                response_summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (goal_id) REFERENCES user_goals (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_followups_scheduled 
            ON goal_followups(user_id, scheduled_for, sent_at)
        ''')
        
        # Goal coaching sessions - tracks conversation context for goals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goal_coaching_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_id INTEGER,
                session_type TEXT DEFAULT 'discovery',
                session_summary TEXT,
                insights_gathered TEXT,
                blockers_identified TEXT,
                recommendations TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (goal_id) REFERENCES user_goals (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_default_user(self):
        """Create the default user 'Wai Tse' with password './/.'"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', ('Wai Tse',))
        if cursor.fetchone():
            conn.close()
            return
        
        # Create user
        password_hash = bcrypt.hashpw('.//'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', ('Wai Tse', 'wai.tse@example.com', password_hash))
        
        user_id = cursor.lastrowid
        
        # Create profile
        cursor.execute('''
            INSERT INTO user_profiles (user_id, first_name, last_name, bio, location, preferences)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Wai', 'Tse', 'Default user with existing conversation history', 'Unknown', 
              json.dumps({
                  'communication_style': 'friendly',
                  'interests': ['technology', 'AI', 'programming'],
                  'preferred_models': ['gpt-4', 'claude']
              })))
        
        # Create psychology traits
        traits = [
            ('Openness', 0.8, 'High openness to new experiences'),
            ('Conscientiousness', 0.7, 'Well-organized and reliable'),
            ('Extraversion', 0.6, 'Moderately social and outgoing'),
            ('Agreeableness', 0.9, 'Very cooperative and trusting'),
            ('Neuroticism', 0.3, 'Emotionally stable')
        ]
        
        for trait_name, trait_value, description in traits:
            cursor.execute('''
                INSERT INTO psychology_traits (user_id, trait_name, trait_value, trait_description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, trait_name, trait_value, description))
        
        # Create sample conversation
        session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conversation_data = {
            'messages': [
                {'role': 'user', 'content': 'Hello, I need help with my project.', 'timestamp': datetime.now().isoformat()},
                {'role': 'assistant', 'content': 'I\'d be happy to help! What kind of project are you working on?', 'timestamp': datetime.now().isoformat()},
                {'role': 'user', 'content': 'I\'m building a web application for task management.', 'timestamp': datetime.now().isoformat()},
                {'role': 'assistant', 'content': 'That sounds interesting! What features are you planning to include?', 'timestamp': datetime.now().isoformat()}
            ]
        }
        
        cursor.execute('''
            INSERT INTO ai_conversations (user_id, session_id, title, conversation_data, personality_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_id, 'Previous Discussion', json.dumps(conversation_data), 
              json.dumps({'personality': 'helpful_assistant', 'user_traits': 'casual_learner'})))
        
        conversation_id = cursor.lastrowid
        
        # Add individual messages
        for msg in conversation_data['messages']:
            cursor.execute('''
                INSERT INTO messages (conversation_id, sender_type, content, metadata)
                VALUES (?, ?, ?, ?)
            ''', (conversation_id, msg['role'], msg['content'], json.dumps({'timestamp': msg['timestamp']})))
        
        conn.commit()
        conn.close()
        print(f"Created default user 'Wai Tse' with ID: {user_id}")
    
    # Authentication methods
    def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            
            user_id = cursor.lastrowid
            
            # Create default profile
            cursor.execute('''
                INSERT INTO user_profiles (user_id, first_name, last_name, bio, preferences)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, '', '', '', json.dumps({})))
            
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2]
            }
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            }
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, created_at FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            }
        return None
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Update user password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (password_hash, user_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, created_at FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            }
        return None
    
    def update_user_email(self, user_id: int, new_email: str) -> bool:
        """Update user email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users SET email = ?, updated_at = CURRENT_TIMESTAMP, email_verified = 0
                WHERE id = ?
            ''', (new_email, user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            return success
        except sqlite3.IntegrityError:
            # Email already in use
            return False
        finally:
            conn.close()
    
    # Profile methods
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT up.first_name, up.last_name, up.bio, up.avatar_url, up.birth_date, up.location, up.preferences,
                   u.user_role, u.email, u.username
            FROM user_profiles up
            JOIN users u ON up.user_id = u.id
            WHERE up.user_id = ?
        ''', (user_id,))
        
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            prefs = json.loads(profile[6]) if profile[6] else {}
            return {
                'first_name': profile[0] or '',
                'last_name': profile[1] or '',
                'bio': profile[2] or '',
                'avatar_url': profile[3] or '',
                'birth_date': profile[4] or '',
                'location': profile[5] or '',
                'preferences': prefs.get('user_preferences', {}),
                'personal_info': prefs.get('personal_info', {}),
                'privacy_settings': prefs.get('privacy_settings', {}),
                'profile_completion': 50 if prefs.get('personal_info') else 0,
                'user_role': profile[7] or 'guest',
                'email': profile[8] or '',
                'username': profile[9] or ''
            }
        return None
    
    def get_user_profile_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT up.user_id, up.first_name, up.last_name, up.bio, up.avatar_url, up.birth_date, up.location, up.preferences,
                   u.user_role, u.email, u.username, u.id
            FROM user_profiles up
            JOIN users u ON up.user_id = u.id
            WHERE u.username = ?
        ''', (username,))
        
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            return {
                'id': profile[11],  # user.id
                'user_id': profile[0],
                'first_name': profile[1] or '',
                'last_name': profile[2] or '',
                'bio': profile[3] or '',
                'avatar_url': profile[4] or '',
                'birth_date': profile[5] or '',
                'location': profile[6] or '',
                'preferences': json.loads(profile[7]) if profile[7] else {},
                'user_role': profile[8] or 'guest',
                'email': profile[9] or '',
                'username': profile[10] or ''
            }
        return None
    
    def update_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """Update user profile - handles both direct fields and nested objects (personal_info, preferences, privacy_settings)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get existing preferences to merge with
        cursor.execute('SELECT preferences FROM user_profiles WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        existing_prefs = json.loads(row[0]) if row and row[0] else {}
        
        # Handle nested objects - store in preferences JSON
        if 'personal_info' in profile_data:
            existing_prefs['personal_info'] = profile_data['personal_info']
        if 'preferences' in profile_data:
            existing_prefs['user_preferences'] = profile_data['preferences']
        if 'privacy_settings' in profile_data:
            existing_prefs['privacy_settings'] = profile_data['privacy_settings']
        
        # Also extract specific fields for the dedicated columns
        personal_info = profile_data.get('personal_info', {})
        
        cursor.execute('''
            UPDATE user_profiles SET
                first_name = COALESCE(NULLIF(?, ''), first_name),
                last_name = COALESCE(NULLIF(?, ''), last_name),
                bio = COALESCE(NULLIF(?, ''), bio),
                avatar_url = COALESCE(NULLIF(?, ''), avatar_url),
                birth_date = COALESCE(NULLIF(?, ''), birth_date),
                location = COALESCE(NULLIF(?, ''), location),
                preferences = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            personal_info.get('name', profile_data.get('first_name', '')),
            profile_data.get('last_name', ''),
            personal_info.get('bio', profile_data.get('bio', '')),
            profile_data.get('avatar_url', ''),
            personal_info.get('age', profile_data.get('birth_date', '')),
            personal_info.get('location', profile_data.get('location', '')),
            json.dumps(existing_prefs),
            user_id
        ))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update or merge user preferences"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get existing preferences
        cursor.execute('SELECT preferences FROM user_profiles WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            existing_prefs = json.loads(row[0]) if row[0] else {}
            # Merge new preferences with existing ones
            existing_prefs.update(preferences)
            
            cursor.execute('''
                UPDATE user_profiles SET preferences = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (json.dumps(existing_prefs), user_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        
        conn.close()
        return False
    
    # Psychology traits methods
    def get_psychology_traits(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's psychology traits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT trait_name, trait_value, trait_description, created_at, updated_at
            FROM psychology_traits WHERE user_id = ? ORDER BY trait_name
        ''', (user_id,))
        
        traits = []
        for row in cursor.fetchall():
            traits.append({
                'trait_name': row[0],
                'trait_value': row[1],
                'trait_description': row[2] or '',
                'created_at': row[3],
                'updated_at': row[4]
            })
        
        conn.close()
        return traits
    
    def upsert_psychology_trait(self, user_id: int, trait_name: str, trait_value: float, description: str = '') -> bool:
        """Insert or update psychology trait"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO psychology_traits 
            (user_id, trait_name, trait_value, trait_description, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, trait_name, trait_value, description))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # ========================================
    # DATABASE MIGRATION METHODS
    # ========================================
    
    def migrate_add_character_id(self):
        """Add character_id column to ai_conversations table for user+character tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if column exists
            cursor.execute("PRAGMA table_info(ai_conversations)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'character_id' not in columns:
                print("🔧 Migrating database: Adding character_id column to ai_conversations...")
                
                # Add column
                cursor.execute('ALTER TABLE ai_conversations ADD COLUMN character_id TEXT')
                
                # Create index for fast user+character queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversations_user_character 
                    ON ai_conversations(user_id, character_id)
                ''')
                
                # Create index for session lookup
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversations_session 
                    ON ai_conversations(session_id)
                ''')
                
                conn.commit()
                print("✅ Migration complete: character_id column added")
            else:
                print("✓ character_id column already exists")
            
            # Add reply_to_message_id column to messages table (WhatsApp-style replies)
            cursor.execute("PRAGMA table_info(messages)")
            msg_columns = [col[1] for col in cursor.fetchall()]
            
            if 'reply_to_message_id' not in msg_columns:
                print("🔧 Migrating database: Adding reply_to_message_id column to messages...")
                cursor.execute('ALTER TABLE messages ADD COLUMN reply_to_message_id INTEGER')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_messages_reply_to 
                    ON messages(reply_to_message_id)
                ''')
                conn.commit()
                print("✅ Migration complete: reply_to_message_id column added")
            else:
                print("✓ reply_to_message_id column already exists")
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ========================================
    # CONVERSATION METHODS (Original)
    # ========================================
    def create_conversation(self, user_id: int, title: str, session_id: str = None) -> str:
        """Create a new conversation with retry logic for database locks"""
        import time
        import random
        
        if not session_id:
            # Use microseconds for better uniqueness
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            random_suffix = random.randint(1000, 9999)
            session_id = f"session_{user_id}_{timestamp}_{random_suffix}"
        
        # Retry logic for database locks
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Set busy timeout to handle locks
                cursor.execute('PRAGMA busy_timeout = 5000')
                
                cursor.execute('''
                    INSERT INTO ai_conversations (user_id, session_id, title, conversation_data, personality_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, session_id, title, json.dumps({'messages': []}), json.dumps({})))
                
                conn.commit()
                conn.close()
                return session_id
                
            except sqlite3.IntegrityError as e:
                conn.close()
                if 'UNIQUE constraint' in str(e):
                    # Session ID collision, regenerate and retry
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    random_suffix = random.randint(1000, 9999)
                    session_id = f"session_{user_id}_{timestamp}_{random_suffix}"
                    time.sleep(0.1)
                    continue
                else:
                    raise
                    
            except sqlite3.OperationalError as e:
                conn.close()
                if 'database is locked' in str(e) and attempt < max_retries - 1:
                    # Wait and retry
                    time.sleep(0.2 * (attempt + 1))
                    continue
                else:
                    raise
                    
            except Exception as e:
                conn.close()
                raise
        
        raise Exception("Failed to create conversation after multiple retries")
    
    def delete_conversation(self, session_id: str, user_id: int) -> bool:
        """Delete a conversation and its messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # First verify the conversation belongs to the user
            cursor.execute('''
                SELECT id FROM ai_conversations 
                WHERE session_id = ? AND user_id = ?
            ''', (session_id, user_id))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return False  # Not found or unauthorized
            
            conversation_id = result[0]
            
            # Delete messages first (if any) - table is called 'messages' not 'ai_messages'
            cursor.execute('''
                DELETE FROM messages 
                WHERE conversation_id = ?
            ''', (conversation_id,))
            
            # Delete the conversation
            cursor.execute('''
                DELETE FROM ai_conversations 
                WHERE session_id = ? AND user_id = ?
            ''', (session_id, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            raise e
    
    def get_user_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's conversations with deduplication"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Use DISTINCT on session_id to avoid duplicates
        cursor.execute('''
            SELECT DISTINCT id, session_id, title, created_at, updated_at
            FROM ai_conversations WHERE user_id = ? 
            ORDER BY updated_at DESC
        ''', (user_id,))
        
        conversations = []
        seen_sessions = set()  # Additional deduplication
        
        for row in cursor.fetchall():
            session_id = row[1]
            # Skip if we've already seen this session_id
            if session_id in seen_sessions:
                continue
            seen_sessions.add(session_id)
            
            conversations.append({
                'id': row[0],
                'session_id': session_id,
                'title': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            })
        
        conn.close()
        return conversations
    
    def get_conversation_messages(self, session_id: str, user_id: int, filter_old_greetings: bool = True) -> List[Dict[str, Any]]:
        """Get messages for a conversation, optionally filtering old automated greetings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, m.sender_type, m.content, m.metadata, m.timestamp
            FROM messages m
            JOIN ai_conversations c ON m.conversation_id = c.id
            WHERE c.session_id = ? AND c.user_id = ?
            ORDER BY m.timestamp ASC
        ''', (session_id, user_id))
        
        raw_messages = []
        for row in cursor.fetchall():
            metadata = json.loads(row[3]) if row[3] else {}
            # Append 'Z' to timestamp to indicate UTC (SQLite stores in UTC but doesn't include timezone)
            timestamp = row[4]
            if timestamp and not timestamp.endswith('Z'):
                timestamp = timestamp + 'Z'
            raw_messages.append({
                'id': row[0],
                'sender_type': row[1],
                'content': row[2],
                'metadata': metadata,
                'timestamp': timestamp
            })
        
        conn.close()
        
        # Filter out old GENERIC greetings (daily/inactivity) but KEEP AI context prompts
        # Users may want to follow up on context prompts after being reminded
        if filter_old_greetings and raw_messages:
            # Find all generic greeting indices (daily/inactivity only, not AI context prompts)
            generic_greeting_indices = []
            for i, msg in enumerate(raw_messages):
                metadata = msg['metadata']
                if metadata.get('is_automated_greeting'):
                    # Only filter generic greetings (daily, inactivity)
                    # Keep AI context prompts (triggered_by='ai_context' or no greeting_type)
                    greeting_type = metadata.get('greeting_type', '')
                    triggered_by = metadata.get('triggered_by', '')
                    
                    # Skip AI context prompts - keep them all
                    if triggered_by == 'ai_context' or 'context' in str(triggered_by).lower():
                        continue
                    
                    # Filter generic greetings (daily, inactivity, scheduled)
                    if greeting_type in ['daily', 'inactivity'] or triggered_by in ['scheduled_time', 'inactivity_timeout']:
                        generic_greeting_indices.append(i)
            
            # Keep only the most recent generic greeting (if any)
            if len(generic_greeting_indices) > 1:
                # Remove all but the last generic greeting
                indices_to_remove = set(generic_greeting_indices[:-1])
                raw_messages = [msg for i, msg in enumerate(raw_messages) if i not in indices_to_remove]
        
        return raw_messages
    
    def add_message(self, session_id: str, user_id: int, sender_type: str, content: str, 
                     metadata: Dict[str, Any] = None, reply_to_message_id: int = None) -> int:
        """Add a message to a conversation. Returns message ID or 0 on failure."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get conversation ID
        cursor.execute('SELECT id FROM ai_conversations WHERE session_id = ? AND user_id = ?', (session_id, user_id))
        conversation = cursor.fetchone()
        
        if not conversation:
            conn.close()
            return 0
        
        conversation_id = conversation[0]
        
        # Add message with optional reply reference
        cursor.execute('''
            INSERT INTO messages (conversation_id, sender_type, content, metadata, reply_to_message_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (conversation_id, sender_type, content, json.dumps(metadata or {}), reply_to_message_id))
        
        message_id = cursor.lastrowid
        
        # Update conversation timestamp
        cursor.execute('''
            UPDATE ai_conversations SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (conversation_id,))
        
        conn.commit()
        conn.close()
        return message_id
    
    def record_interaction(self, user_id: int, interaction_type: str, interaction_data: Dict[str, Any]) -> bool:
        """Record user interaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_interactions (user_id, interaction_type, interaction_data)
            VALUES (?, ?, ?)
        ''', (user_id, interaction_type, json.dumps(interaction_data)))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # ========================================
    # CHARACTER-SPECIFIC CONVERSATION METHODS
    # (Database migration - Phase 1 & 2)
    # ========================================
    
    def get_or_create_character_session(self, user_id: int, character_id: str) -> str:
        """Get existing session or create new one for user+character combination"""
        import uuid
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check for existing session for this user+character
            cursor.execute('''
                SELECT session_id FROM ai_conversations
                WHERE user_id = ? AND character_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            ''', (user_id, character_id))
            
            result = cursor.fetchone()
            
            if result:
                session_id = result[0]
                # Update timestamp to mark as recently used
                cursor.execute('''
                    UPDATE ai_conversations 
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                ''', (session_id,))
                conn.commit()
                print(f"✓ Found existing session: {session_id} for user {user_id}, character {character_id}")
                return session_id
            
            # Create new session
            session_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO ai_conversations (user_id, character_id, session_id, title)
                VALUES (?, ?, ?, ?)
            ''', (user_id, character_id, session_id, f"{character_id} conversation"))
            
            conn.commit()
            print(f"✓ Created new session: {session_id} for user {user_id}, character {character_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ Error in get_or_create_character_session: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save_character_message(self, user_id: int, character_id: str, role: str, content: str, 
                                 metadata: dict = None, reply_to_message_id: int = None) -> int:
        """Save message to database for user+character (auto-creates session if needed). Returns message ID."""
        try:
            # Get or create session for this user+character
            session_id = self.get_or_create_character_session(user_id, character_id)
            
            # Save message using existing add_message method
            return self.add_message(session_id, user_id, role, content, metadata, reply_to_message_id)
            
        except Exception as e:
            print(f"❌ Error saving character message: {e}")
            return 0
    
    def get_message_by_id(self, message_id: int) -> Optional[Dict]:
        """Get a specific message by ID (for reply context)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.id, m.conversation_id, m.sender_type, m.content, m.metadata, 
                   m.timestamp, m.reply_to_message_id
            FROM messages m
            WHERE m.id = ?
        ''', (message_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'conversation_id': row[1],
                'sender_type': row[2],
                'content': row[3],
                'metadata': json.loads(row[4]) if row[4] else {},
                'timestamp': row[5],
                'reply_to_message_id': row[6]
            }
        return None
    
    def get_character_messages(self, user_id: int, character_id: str, limit: int = None) -> List[Dict]:
        """Get conversation history for user+character"""
        try:
            # Get session for this user+character
            session_id = self.get_or_create_character_session(user_id, character_id)
            
            # Get messages using existing method
            messages = self.get_conversation_messages(session_id, user_id)
            
            # Apply limit if specified
            if limit and len(messages) > limit:
                messages = messages[-limit:]
            
            return messages
            
        except Exception as e:
            print(f"❌ Error getting character messages: {e}")
            return []
    
    def get_conversation_by_session(self, session_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Get conversation by session ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, conversation_data, personality_data, created_at, updated_at
            FROM ai_conversations WHERE session_id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        conversation = cursor.fetchone()
        conn.close()
        
        if conversation:
            return {
                'id': conversation[0],
                'title': conversation[1],
                'conversation_data': json.loads(conversation[2]) if conversation[2] else {},
                'personality_data': json.loads(conversation[3]) if conversation[3] else {},
                'created_at': conversation[4],
                'updated_at': conversation[5]
            }
        return None
    
    # ==================== USER ROLES & MESSAGE LIMITS ====================
    
    def get_user_role(self, user_id: int) -> str:
        """Get user role (administrator, master, paid, guest)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_role FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'guest'
    
    def has_personality_access(self, user_id: int) -> bool:
        """Check if user has access to Phase 3.1 personality features (master or administrator only)"""
        role = self.get_user_role(user_id)
        return role in ['administrator', 'master']
    
    def get_message_usage(self, user_id: int) -> Dict[str, Any]:
        """Get user's message usage for today"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        cursor.execute('''
            SELECT message_count FROM message_usage 
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        result = cursor.fetchone()
        conn.close()
        
        current_count = result[0] if result else 0
        role = self.get_user_role(user_id)
        
        # Set limits based on role
        if role in ['administrator', 'master', 'paid']:
            limit = None  # Unlimited
            remaining = None
        else:  # guest
            limit = 20  # Daily limit for guest users
            remaining = max(0, limit - current_count)
        
        return {
            'role': role,
            'current_count': current_count,
            'limit': limit,
            'remaining': remaining,
            'can_send': remaining is None or remaining > 0
        }
    
    def can_send_message(self, user_id: int) -> tuple[bool, str]:
        """Check if user can send a message. Returns (can_send, reason)"""
        usage = self.get_message_usage(user_id)
        
        if usage['can_send']:
            return True, ""
        else:
            return False, f"Daily message limit reached ({usage['limit']} messages per day for guest users)"
    
    def increment_message_count(self, user_id: int) -> bool:
        """Increment user's message count for today"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        try:
            # Try to insert new record
            cursor.execute('''
                INSERT INTO message_usage (user_id, date, message_count) 
                VALUES (?, ?, 1)
            ''', (user_id, today))
        except sqlite3.IntegrityError:
            # Record exists, update it
            cursor.execute('''
                UPDATE message_usage 
                SET message_count = message_count + 1 
                WHERE user_id = ? AND date = ?
            ''', (user_id, today))
        
        conn.commit()
        conn.close()
        return True
    
    def get_all_users_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all users (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get last active from multiple sources: messages (most accurate), ai_conversations, message_usage
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.email,
                u.user_role,
                u.created_at,
                COALESCE(SUM(mu.message_count), 0) as total_messages,
                COUNT(DISTINCT c.id) as total_conversations,
                (SELECT MAX(last_ts) FROM (
                    SELECT MAX(m.timestamp) as last_ts FROM messages m 
                    JOIN ai_conversations ac ON m.conversation_id = ac.id 
                    WHERE ac.user_id = u.id
                    UNION ALL
                    SELECT MAX(ac2.updated_at) FROM ai_conversations ac2 WHERE ac2.user_id = u.id
                    UNION ALL
                    SELECT MAX(mu2.date) FROM message_usage mu2 WHERE mu2.user_id = u.id
                )) as last_active,
                COALESCE(u.is_deleted, 0) as is_deleted
            FROM users u
            LEFT JOIN message_usage mu ON u.id = mu.user_id
            LEFT JOIN ai_conversations c ON u.id = c.user_id
            GROUP BY u.id, u.username, u.email, u.user_role, u.created_at, u.is_deleted
            ORDER BY u.is_deleted ASC, u.created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'role': row[3],
                'created_at': row[4],
                'total_messages': row[5],
                'total_conversations': row[6],
                'last_active': row[7],
                'is_deleted': bool(row[8])
            })
        
        conn.close()
        return users
    
    def soft_delete_user(self, user_id: int) -> bool:
        """Soft delete a user (mark as deleted without removing data)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET is_deleted = 1 
                WHERE id = ?
            ''', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error soft deleting user: {e}")
            return False
        finally:
            conn.close()
    
    def restore_user(self, user_id: int) -> bool:
        """Restore a soft-deleted user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET is_deleted = 0 
                WHERE id = ?
            ''', (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error restoring user: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== PERSONALITY FEATURES (PHASE 3.1) ====================
    
    def get_personality_profile(self, user_id: int) -> Dict[str, Any]:
        """Get user's personality profile with Big 5 traits"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT trait_name, trait_value, trait_description, updated_at
            FROM psychology_traits
            WHERE user_id = ?
        ''', (user_id,))
        
        traits = {}
        last_updated = None
        for row in cursor.fetchall():
            traits[row[0]] = {
                'value': row[1],
                'description': row[2],
                'updated_at': row[3]
            }
            if not last_updated or row[3] > last_updated:
                last_updated = row[3]
        
        # 3-TIER FALLBACK: Assessment → Inferred → Defaults (Phase 3.2.2)
        if traits:
            # Tier 1: Formal Assessment (highest confidence)
            source = 'assessment'
            confidence = 0.85
        else:
            # Tier 2: Inferred from conversations (medium confidence)
            cursor.execute('''
                SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism, confidence, last_updated
                FROM inferred_personality WHERE user_id = ?
            ''', (user_id,))
            inferred = cursor.fetchone()
            
            if inferred:
                source = 'inferred'
                confidence = inferred[5]  # Use actual inferred confidence
                last_updated = inferred[6]
                
                # Convert inferred traits to same format as psychology_traits
                big5_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'emotional_stability']
                big5_descriptions = {
                    'openness': 'Creative, curious, open to new experiences',
                    'conscientiousness': 'Organized, disciplined, goal-oriented',
                    'extraversion': 'Outgoing, energetic, socially engaged',
                    'agreeableness': 'Cooperative, kind, empathetic',
                    'emotional_stability': 'Calm, resilient, emotionally stable'
                }
                
                traits = {}
                for i, name in enumerate(big5_names):
                    traits[name] = {
                        'value': inferred[i],
                        'description': big5_descriptions[name],
                        'updated_at': last_updated
                    }
            else:
                # Tier 3: Neutral defaults (lowest confidence)
                source = 'default'
                confidence = 0.30
                
                # Provide neutral default traits (0.5 = moderate/balanced)
                big5_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'emotional_stability']
                big5_descriptions = {
                    'openness': 'Balanced between traditional and novel approaches',
                    'conscientiousness': 'Flexible balance of organization and spontaneity',
                    'extraversion': 'Adaptable in both social and solitary settings',
                    'agreeableness': 'Balanced empathy with directness',
                    'emotional_stability': 'Moderate emotional awareness and resilience'
                }
                
                traits = {}
                for name in big5_names:
                    traits[name] = {
                        'value': 0.5,
                        'description': big5_descriptions[name],
                        'updated_at': None
                    }
        
        conn.close()
        
        return {
            'user_id': user_id,
            'traits': traits,
            'source': source,
            'confidence': confidence,
            'last_updated': last_updated,
            'has_assessment': source == 'assessment'
        }
    
    @property
    def resolver(self):
        """Lazy-load PersonalityResolver to avoid circular imports"""
        if self._resolver is None:
            from smart_response.personality_resolver import PersonalityResolver
            self._resolver = PersonalityResolver(self)
        return self._resolver
    
    def get_personality_profile_v2(
        self, 
        user_id: int, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get personality profile using smart resolution logic (RECOMMENDED)
        
        This method uses PersonalityResolver for intelligent data selection:
        - Prioritizes fresh assessment data
        - Blends old assessment with recent inferred data
        - Provides confidence scores and recommendations
        - Caches results for performance
        
        Args:
            user_id: User ID
            context: Optional context hint ('character_selection', 'response_tone', 'action_plan')
        
        Returns:
            {
                'user_id': int,
                'traits': {
                    'openness': 0.80,
                    'conscientiousness': 0.70,
                    'extraversion': 0.60,
                    'agreeableness': 0.90,
                    'neuroticism': 0.30
                },
                'confidence': 0.85,
                'source': 'assessment',  # or 'inferred', 'blended', 'default'
                'metadata': {...},
                'recommendations': {...}
            }
        
        Example:
            profile = db.get_personality_profile_v2(user_id, context='character_selection')
            if profile['confidence'] > 0.7:
                # Use personality data for personalization
                character = select_character(profile['traits'])
        """
        result = self.resolver.get_decision_ready_profile(user_id, context)
        result['user_id'] = user_id
        return result
    
    def clear_personality_cache(self, user_id: Optional[int] = None):
        """
        Clear personality profile cache
        
        Call this after:
        - User completes new assessment
        - Inference updates traits
        - Any personality data change
        
        Args:
            user_id: Optional user ID. If None, clears all cache.
        """
        if self._resolver:
            self._resolver.clear_cache(user_id)
    
    def get_personality_interpretations(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent personality interpretations for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id, character, event_type, raw_event, raw_message,
                interpretation, emotional_impact, recommended_approach,
                confidence, traits_used, created_at
            FROM personality_interpretations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        interpretations = []
        for row in cursor.fetchall():
            interpretations.append({
                'id': row[0],
                'character': row[1],
                'event_type': row[2],
                'raw_event': row[3],
                'raw_message': row[4],
                'interpretation': row[5],
                'emotional_impact': row[6],
                'recommended_approach': row[7],
                'confidence': row[8],
                'traits_used': json.loads(row[9]) if row[9] else {},
                'created_at': row[10]
            })
        
        conn.close()
        return interpretations
    
    def get_personality_stats(self, user_id: int) -> Dict[str, Any]:
        """Get personality interpretation statistics for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total interpretations
        cursor.execute('''
            SELECT COUNT(*) FROM personality_interpretations WHERE user_id = ?
        ''', (user_id,))
        total = cursor.fetchone()[0]
        
        # By event type
        cursor.execute('''
            SELECT event_type, COUNT(*) 
            FROM personality_interpretations 
            WHERE user_id = ?
            GROUP BY event_type
        ''', (user_id,))
        by_event_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average confidence
        cursor.execute('''
            SELECT AVG(confidence) 
            FROM personality_interpretations 
            WHERE user_id = ?
        ''', (user_id,))
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # Get personality source
        profile = self.get_personality_profile(user_id)
        
        conn.close()
        
        return {
            'total_interpretations': total,
            'by_event_type': by_event_type,
            'average_confidence': round(avg_confidence, 2),
            'personality_source': profile['source'],
            'has_assessment': profile['has_assessment']
        }
    
    # ==================== ASSESSMENT HISTORY (PHASE 3.2 ENHANCEMENT) ====================
    
    def save_assessment_to_history(self, user_id: int, trait_scores: Dict[str, float], 
                                   started_at: str = None, completion_time_seconds: int = None,
                                   notes: str = None) -> int:
        """
        Save completed assessment to history before updating current traits
        
        Args:
            user_id: User ID
            trait_scores: Dict with Big 5 scores (0-1 scale)
            started_at: ISO timestamp when assessment started
            completion_time_seconds: Time taken to complete
            notes: Optional notes (e.g., "Retake after 6 months")
            
        Returns:
            ID of history record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO assessment_history 
                (user_id, openness, conscientiousness, extraversion, agreeableness, neuroticism,
                 completion_time_seconds, started_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                trait_scores.get('openness', 0.5),
                trait_scores.get('conscientiousness', 0.5),
                trait_scores.get('extraversion', 0.5),
                trait_scores.get('agreeableness', 0.5),
                trait_scores.get('neuroticism', 0.5),
                completion_time_seconds,
                started_at,
                notes
            ))
            
            history_id = cursor.lastrowid
            conn.commit()
            
            # Clear personality cache since data changed
            self.clear_personality_cache(user_id)
            
            return history_id
            
        except Exception as e:
            print(f"Error saving assessment history: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_assessment_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get assessment history for a user
        
        Returns list ordered by most recent first
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, assessment_version, openness, conscientiousness, extraversion,
                   agreeableness, neuroticism, completion_time_seconds, questions_answered,
                   started_at, completed_at, notes
            FROM assessment_history
            WHERE user_id = ?
            ORDER BY completed_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row[0],
                'version': row[1],
                'traits': {
                    'openness': row[2],
                    'conscientiousness': row[3],
                    'extraversion': row[4],
                    'agreeableness': row[5],
                    'neuroticism': row[6]
                },
                'completion_time_seconds': row[7],
                'questions_answered': row[8],
                'started_at': row[9],
                'completed_at': row[10],
                'notes': row[11]
            })
        
        conn.close()
        return history
    
    def compare_assessments(self, user_id: int, assessment1_id: int, assessment2_id: int = None) -> Dict[str, Any]:
        """
        Compare two assessments or compare an assessment to current profile
        
        Args:
            user_id: User ID
            assessment1_id: First assessment (usually older)
            assessment2_id: Second assessment (None = use current profile)
            
        Returns:
            Comparison with changes, trends, and insights
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get first assessment
        cursor.execute('''
            SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism, completed_at
            FROM assessment_history
            WHERE id = ? AND user_id = ?
        ''', (assessment1_id, user_id))
        
        row1 = cursor.fetchone()
        if not row1:
            conn.close()
            return {'error': 'First assessment not found'}
        
        traits1 = {
            'openness': row1[0],
            'conscientiousness': row1[1],
            'extraversion': row1[2],
            'agreeableness': row1[3],
            'neuroticism': row1[4]
        }
        date1 = row1[5]
        
        # Get second assessment or current profile
        if assessment2_id:
            cursor.execute('''
                SELECT openness, conscientiousness, extraversion, agreeableness, neuroticism, completed_at
                FROM assessment_history
                WHERE id = ? AND user_id = ?
            ''', (assessment2_id, user_id))
            
            row2 = cursor.fetchone()
            if not row2:
                conn.close()
                return {'error': 'Second assessment not found'}
            
            traits2 = {
                'openness': row2[0],
                'conscientiousness': row2[1],
                'extraversion': row2[2],
                'agreeableness': row2[3],
                'neuroticism': row2[4]
            }
            date2 = row2[5]
        else:
            # Use current profile
            profile = self.get_personality_profile(user_id)
            traits2 = {k: v['value'] for k, v in profile['traits'].items()}
            date2 = profile['last_updated']
        
        conn.close()
        
        # Calculate changes
        changes = {}
        total_change = 0
        for trait in traits1.keys():
            change = traits2.get(trait, 0.5) - traits1[trait]
            changes[trait] = {
                'old_value': round(traits1[trait] * 100, 1),
                'new_value': round(traits2.get(trait, 0.5) * 100, 1),
                'change': round(change * 100, 1),
                'direction': 'increased' if change > 0.05 else 'decreased' if change < -0.05 else 'stable'
            }
            total_change += abs(change)
        
        # Interpret overall change
        avg_change = total_change / len(traits1)
        if avg_change < 0.05:
            stability = 'Very stable - Your personality has remained consistent'
        elif avg_change < 0.10:
            stability = 'Mostly stable with minor changes'
        elif avg_change < 0.20:
            stability = 'Moderate changes - Some personality shifts detected'
        else:
            stability = 'Significant changes - Notable personality evolution'
        
        return {
            'comparison': changes,
            'overall_change': round(avg_change * 100, 1),
            'stability_assessment': stability,
            'date1': date1,
            'date2': date2,
            'time_between': self._calculate_time_between(date1, date2)
        }
    
    def _calculate_time_between(self, date1: str, date2: str) -> str:
        """Calculate human-readable time between two dates"""
        try:
            from datetime import datetime
            d1 = datetime.fromisoformat(date1) if isinstance(date1, str) else date1
            d2 = datetime.fromisoformat(date2) if isinstance(date2, str) else date2
            
            diff = abs((d2 - d1).days)
            
            if diff < 7:
                return f"{diff} day{'s' if diff != 1 else ''}"
            elif diff < 30:
                weeks = diff // 7
                return f"{weeks} week{'s' if weeks != 1 else ''}"
            elif diff < 365:
                months = diff // 30
                return f"{months} month{'s' if months != 1 else ''}"
            else:
                years = diff // 365
                return f"{years} year{'s' if years != 1 else ''}"
        except:
            return "Unknown"
    
    def get_trait_trends(self, user_id: int, trait_name: str) -> Dict[str, Any]:
        """
        Get trend data for a specific trait over time
        
        Returns history of values suitable for charting
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT completed_at, {trait_name}
            FROM assessment_history
            WHERE user_id = ?
            ORDER BY completed_at ASC
        ''', (user_id,))
        
        data_points = []
        for row in cursor.fetchall():
            data_points.append({
                'date': row[0],
                'value': round(row[1] * 100, 1)
            })
        
        conn.close()
        
        # Calculate trend
        if len(data_points) >= 2:
            first_val = data_points[0]['value']
            last_val = data_points[-1]['value']
            trend = 'increasing' if last_val > first_val + 5 else 'decreasing' if last_val < first_val - 5 else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trait': trait_name,
            'data_points': data_points,
            'trend': trend,
            'assessments_count': len(data_points)
        }
    
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update a user's role"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET user_role = ? 
                WHERE id = ?
            ''', (new_role, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
        finally:
            conn.close()
    
    def permanent_delete_user(self, user_id: int) -> bool:
        """Permanently delete a user and all their data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete in order to respect foreign key constraints
            # 1. Delete messages (they reference conversations)
            cursor.execute('''
                DELETE FROM messages 
                WHERE conversation_id IN (
                    SELECT id FROM ai_conversations WHERE user_id = ?
                )
            ''', (user_id,))
            
            # 2. Delete message usage
            cursor.execute('DELETE FROM message_usage WHERE user_id = ?', (user_id,))
            
            # 3. Delete user interactions
            cursor.execute('DELETE FROM user_interactions WHERE user_id = ?', (user_id,))
            
            # 4. Delete AI conversations
            cursor.execute('DELETE FROM ai_conversations WHERE user_id = ?', (user_id,))
            
            # 5. Delete admin messages
            cursor.execute('DELETE FROM admin_messages WHERE user_id = ?', (user_id,))
            
            # 6. Delete psychology traits
            cursor.execute('DELETE FROM psychology_traits WHERE user_id = ?', (user_id,))
            
            # 7. Delete user profiles
            cursor.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
            
            # 8. Finally delete the user
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            conn.commit()
            print(f"Permanently deleted user {user_id} and all related data")
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error permanently deleting user: {e}")
            return False
        finally:
            conn.close()
    
    def bulk_delete_deleted_users(self) -> int:
        """Permanently delete all logically deleted users and their data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all deleted user IDs
            cursor.execute('SELECT id FROM users WHERE is_deleted = 1')
            deleted_user_ids = [row[0] for row in cursor.fetchall()]
            
            if not deleted_user_ids:
                return 0
            
            # Delete all data for these users
            for user_id in deleted_user_ids:
                # Delete in order to respect foreign key constraints
                # 1. Delete messages first (they reference conversations)
                cursor.execute('''
                    DELETE FROM messages 
                    WHERE conversation_id IN (
                        SELECT id FROM ai_conversations WHERE user_id = ?
                    )
                ''', (user_id,))
                
                # 2. Delete other related data
                cursor.execute('DELETE FROM message_usage WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM user_interactions WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM ai_conversations WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM admin_messages WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM psychology_traits WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM user_profiles WHERE user_id = ?', (user_id,))
                
                # 3. Finally delete the user
                cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            conn.commit()
            print(f"Bulk deleted {len(deleted_user_ids)} users and all their data")
            return len(deleted_user_ids)
        except Exception as e:
            conn.rollback()
            print(f"Error bulk deleting users: {e}")
            return 0
        finally:
            conn.close()
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get overall usage statistics (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Total messages today
        today = datetime.now().date().isoformat()
        cursor.execute('SELECT SUM(message_count) FROM message_usage WHERE date = ?', (today,))
        messages_today = cursor.fetchone()[0] or 0
        
        # Total messages all time
        cursor.execute('SELECT SUM(message_count) FROM message_usage')
        total_messages = cursor.fetchone()[0] or 0
        
        # Active users today
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM message_usage WHERE date = ?', (today,))
        active_today = cursor.fetchone()[0]
        
        # Users by role
        cursor.execute('SELECT user_role, COUNT(*) FROM users GROUP BY user_role')
        users_by_role = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_users': total_users,
            'messages_today': messages_today,
            'total_messages': total_messages,
            'active_today': active_today,
            'users_by_role': users_by_role
        }
    
    def add_email_verification_columns(self):
        """Add email verification columns if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if columns exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'email_verified' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0')
            if 'verification_code' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN verification_code TEXT')
            if 'verification_expires' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN verification_expires DATETIME')
            
            conn.commit()
        except Exception as e:
            print(f"Note: Email verification columns may already exist: {e}")
        finally:
            conn.close()
    
    def create_verification_code(self, user_id: int) -> str:
        """Generate and store verification code for user"""
        import random
        verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = datetime.now() + timedelta(hours=1)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET verification_code = ?, verification_expires = ?
            WHERE id = ?
        ''', (verification_code, expires_at.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        return verification_code
    
    def verify_email_code(self, user_id: int, code: str) -> tuple[bool, str]:
        """Verify the email verification code"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT verification_code, verification_expires 
            FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "User not found"
        
        stored_code, expires_at = result
        
        if not stored_code:
            conn.close()
            return False, "No verification code found"
        
        # Check expiration
        if datetime.now() > datetime.fromisoformat(expires_at):
            conn.close()
            return False, "Verification code has expired"
        
        # Check code match
        if stored_code != code:
            conn.close()
            return False, "Invalid verification code"
        
        # Mark as verified
        cursor.execute('''
            UPDATE users 
            SET email_verified = 1, verification_code = NULL, verification_expires = NULL
            WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return True, "Email verified successfully"
    
    def is_email_verified(self, user_id: int) -> bool:
        """Check if user's email is verified"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT email_verified FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return bool(result[0]) if result else False
    
    # Admin Messaging Methods
    def send_admin_message(self, user_id: int, sender_type: str, message: str, 
                          file_url: str = None, file_name: str = None, file_size: int = None, reply_to: int = None) -> bool:
        """Send a message between user and admin with optional file attachment and reply"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO admin_messages (user_id, sender_type, message, file_url, file_name, file_size, reply_to)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, sender_type, message, file_url, file_name, file_size, reply_to))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error sending admin message: {e}")
            return False
        finally:
            conn.close()
    
    def get_admin_messages(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all messages between user and admin with file attachments and replies"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT am.id, am.sender_type, am.message, am.is_read, am.timestamp, 
                   am.file_url, am.file_name, am.file_size, am.reply_to,
                   rm.message as reply_to_message, rm.sender_type as reply_to_sender
            FROM admin_messages am
            LEFT JOIN admin_messages rm ON am.reply_to = rm.id
            WHERE am.user_id = ?
            ORDER BY am.timestamp ASC
        ''', (user_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'sender_type': row[1],
                'message': row[2],
                'is_read': bool(row[3]),
                'timestamp': row[4],
                'file_url': row[5],
                'file_name': row[6],
                'file_size': row[7],
                'reply_to': row[8],
                'reply_to_message': row[9],
                'reply_to_sender': row[10]
            })
        
        conn.close()
        return messages
    
    def mark_admin_messages_read(self, user_id: int, sender_type: str) -> bool:
        """Mark messages as read"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE admin_messages
                SET is_read = 1
                WHERE user_id = ? AND sender_type = ? AND is_read = 0
            ''', (user_id, sender_type))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error marking messages as read: {e}")
            return False
        finally:
            conn.close()
    
    def get_unread_admin_message_count(self, user_id: int, sender_type: str) -> int:
        """Get count of unread messages"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*)
            FROM admin_messages
            WHERE user_id = ? AND sender_type = ? AND is_read = 0
        ''', (user_id, sender_type))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def get_all_user_admin_chats(self) -> List[Dict[str, Any]]:
        """Get all users who have admin messages (admin view)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT u.id, u.username, u.email,
                   (SELECT COUNT(*) FROM admin_messages 
                    WHERE user_id = u.id AND sender_type = 'user' AND is_read = 0) as unread_count,
                   (SELECT MAX(timestamp) FROM admin_messages WHERE user_id = u.id) as last_message
            FROM users u
            INNER JOIN admin_messages am ON u.id = am.user_id
            ORDER BY last_message DESC
        ''')
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                'user_id': row[0],
                'username': row[1],
                'email': row[2],
                'unread_count': row[3],
                'last_message': row[4]
            })
        
        conn.close()
        return chats
    
    def delete_admin_message(self, message_id: int, deleting_user_id: int) -> bool:
        """Delete an admin message by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if deleting user is admin
            role = self.get_user_role(deleting_user_id)
            
            if role == 'administrator':
                # Admin can delete any message
                cursor.execute('''
                    DELETE FROM admin_messages
                    WHERE id = ?
                ''', (message_id,))
            else:
                # Regular user can only delete their own messages
                # Get the message to check user_id
                cursor.execute('''
                    SELECT user_id FROM admin_messages WHERE id = ?
                ''', (message_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                message_user_id = result[0]
                
                # Only allow deletion if message belongs to this user
                if message_user_id != deleting_user_id:
                    return False
                
                cursor.execute('''
                    DELETE FROM admin_messages
                    WHERE id = ?
                ''', (message_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting admin message: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== CONVERSATION HIGHLIGHTS ====================
    
    def save_highlight(self, user_id: int, highlighted_text: str, character_id: str = None,
                       message_id: int = None, full_message: str = None, 
                       message_role: str = None, note: str = None, color: str = 'green') -> Optional[int]:
        """Save a highlighted portion of conversation text"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO conversation_highlights 
                (user_id, character_id, message_id, highlighted_text, full_message, message_role, note, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, character_id, message_id, highlighted_text, full_message, message_role, note, color))
            
            conn.commit()
            highlight_id = cursor.lastrowid
            print(f"✓ Saved highlight #{highlight_id} for user {user_id}")
            return highlight_id
        except Exception as e:
            print(f"Error saving highlight: {e}")
            return None
        finally:
            conn.close()
    
    def get_highlights(self, user_id: int, character_id: str = None, limit: int = 50) -> List[Dict]:
        """Get user's saved highlights, optionally filtered by character"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if character_id:
                cursor.execute('''
                    SELECT id, character_id, message_id, highlighted_text, full_message, 
                           message_role, note, color, created_at
                    FROM conversation_highlights
                    WHERE user_id = ? AND character_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, character_id, limit))
            else:
                cursor.execute('''
                    SELECT id, character_id, message_id, highlighted_text, full_message, 
                           message_role, note, color, created_at
                    FROM conversation_highlights
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
            
            rows = cursor.fetchall()
            highlights = []
            for row in rows:
                highlights.append({
                    'id': row[0],
                    'character_id': row[1],
                    'message_id': row[2],
                    'highlighted_text': row[3],
                    'full_message': row[4],
                    'message_role': row[5],
                    'note': row[6],
                    'color': row[7],
                    'created_at': row[8]
                })
            return highlights
        except Exception as e:
            print(f"Error getting highlights: {e}")
            return []
        finally:
            conn.close()
    
    def update_highlight_note(self, highlight_id: int, user_id: int, note: str) -> bool:
        """Update the note on a highlight"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE conversation_highlights
                SET note = ?
                WHERE id = ? AND user_id = ?
            ''', (note, highlight_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating highlight note: {e}")
            return False
        finally:
            conn.close()
    
    def delete_highlight(self, highlight_id: int, user_id: int) -> bool:
        """Delete a highlight"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM conversation_highlights
                WHERE id = ? AND user_id = ?
            ''', (highlight_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting highlight: {e}")
            return False
        finally:
            conn.close()
