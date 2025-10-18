import sqlite3
import bcrypt
import json
import os
from datetime import datetime
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
    
    # Profile methods
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT first_name, last_name, bio, avatar_url, birth_date, location, preferences
            FROM user_profiles WHERE user_id = ?
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
                'preferences': json.loads(profile[6]) if profile[6] else {}
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
            limit = 2  # Testing limit
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
