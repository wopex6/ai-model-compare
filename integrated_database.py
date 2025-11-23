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
        
        # Psychology traits table
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
            return {
                'first_name': profile[0] or '',
                'last_name': profile[1] or '',
                'bio': profile[2] or '',
                'avatar_url': profile[3] or '',
                'birth_date': profile[4] or '',
                'location': profile[5] or '',
                'preferences': json.loads(profile[6]) if profile[6] else {},
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
        """Update user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_profiles SET
                first_name = ?, last_name = ?, bio = ?, avatar_url = ?,
                birth_date = ?, location = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            profile_data.get('first_name', ''),
            profile_data.get('last_name', ''),
            profile_data.get('bio', ''),
            profile_data.get('avatar_url', ''),
            profile_data.get('birth_date', ''),
            profile_data.get('location', ''),
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
    
    # Conversation methods
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
    
    def get_conversation_messages(self, session_id: str, user_id: int) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.sender_type, m.content, m.metadata, m.timestamp
            FROM messages m
            JOIN ai_conversations c ON m.conversation_id = c.id
            WHERE c.session_id = ? AND c.user_id = ?
            ORDER BY m.timestamp ASC
        ''', (session_id, user_id))
        
        messages = []
        for row in cursor.fetchall():
            metadata = json.loads(row[2]) if row[2] else {}
            messages.append({
                'sender_type': row[0],
                'content': row[1],
                'metadata': metadata,
                'timestamp': row[3]
            })
        
        conn.close()
        return messages
    
    def add_message(self, session_id: str, user_id: int, sender_type: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a message to a conversation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get conversation ID
        cursor.execute('SELECT id FROM ai_conversations WHERE session_id = ? AND user_id = ?', (session_id, user_id))
        conversation = cursor.fetchone()
        
        if not conversation:
            conn.close()
            return False
        
        conversation_id = conversation[0]
        
        # Add message
        cursor.execute('''
            INSERT INTO messages (conversation_id, sender_type, content, metadata)
            VALUES (?, ?, ?, ?)
        ''', (conversation_id, sender_type, content, json.dumps(metadata or {})))
        
        # Update conversation timestamp
        cursor.execute('''
            UPDATE ai_conversations SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (conversation_id,))
        
        conn.commit()
        conn.close()
        return True
    
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
        """Get user role (administrator, paid, guest)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_role FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 'guest'
    
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
        if role == 'administrator':
            limit = None  # Unlimited
            remaining = None
        elif role == 'paid':
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
        
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.email,
                u.user_role,
                u.created_at,
                COALESCE(SUM(mu.message_count), 0) as total_messages,
                COUNT(DISTINCT c.id) as total_conversations,
                MAX(mu.date) as last_active,
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
