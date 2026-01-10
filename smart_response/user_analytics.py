"""
User Analytics Module
Provides insights into user behavior and conversation patterns.
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json
import re


class UserAnalytics:
    """
    Tracks and analyzes user behavior patterns.
    
    Features:
    - Session analytics
    - Conversation patterns
    - Character usage statistics
    - Engagement metrics
    - Trend analysis
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create analytics tables"""
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_data TEXT,
                    page TEXT,
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    character_id TEXT,
                    message_count INTEGER DEFAULT 0,
                    avg_message_length REAL,
                    session_duration_seconds INTEGER,
                    sentiment_score REAL,
                    topics TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    total_users INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    new_users INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    total_ai_calls INTEGER DEFAULT 0,
                    avg_session_duration INTEGER DEFAULT 0,
                    top_characters TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity_log(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_date ON user_activity_log(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conv_user ON conversation_analytics(user_id)')
            
            self.db.commit()
        except Exception as e:
            print(f"Warning: Could not create analytics tables: {e}")
    
    def log_activity(self, user_id: int, action_type: str, 
                     action_data: Dict = None, page: str = None,
                     session_id: str = None) -> None:
        """Log a user activity"""
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO user_activity_log (user_id, action_type, action_data, page, session_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, action_type, json.dumps(action_data) if action_data else None, 
                  page, session_id))
            self.db.commit()
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def get_user_stats(self, user_id: int, days: int = 30) -> Dict:
        """Get statistics for a specific user"""
        try:
            cursor = self.db.cursor()
            since = datetime.now() - timedelta(days=days)
            
            cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE user_id = ? AND last_activity_at > ?', (user_id, since))
            activity_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE user_id = ? AND activity_type = ? AND last_activity_at > ?', (user_id, 'message_sent', since))
            message_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_activity_log WHERE user_id = ? AND last_activity_at > ?', (user_id, since))
            session_count = cursor.fetchone()[0]
            
            return {
                'user_id': user_id,
                'period_days': days,
                'activity_count': activity_count,
                'message_count': message_count,
                'session_count': session_count,
                'favorite_characters': {},
                'avg_messages_per_session': round(message_count / max(session_count, 1), 1)
            }
        except Exception as e:
            return {'user_id': user_id, 'period_days': days, 'activity_count': 0, 'message_count': 0, 'session_count': 0, 'favorite_characters': {}, 'avg_messages_per_session': 0, 'note': 'Analytics tables not initialized'}
    
    def get_engagement_metrics(self, days: int = 7) -> Dict:
        """Get overall engagement metrics"""
        try:
            cursor = self.db.cursor()
            since = datetime.now() - timedelta(days=days)
            
            cursor.execute('SELECT DATE(last_activity_at) as day, COUNT(DISTINCT user_id) as users FROM user_activity_log WHERE last_activity_at > ? GROUP BY DATE(last_activity_at) ORDER BY day', (since,))
            daily_users = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_activity_log WHERE last_activity_at > ?', (since,))
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_activity_log WHERE last_activity_at > ?', (since,))
            total_activities = cursor.fetchone()[0]
            
            return {
                'period_days': days,
                'total_unique_users': total_users,
                'total_activities': total_activities,
                'daily_active_users': daily_users,
                'avg_daily_users': round(sum(daily_users.values()) / max(len(daily_users), 1), 1),
                'activity_breakdown': {}
            }
        except Exception as e:
            return {'period_days': days, 'total_unique_users': 0, 'total_activities': 0, 'daily_active_users': {}, 'avg_daily_users': 0, 'activity_breakdown': {}, 'note': 'Analytics tables not initialized'}
    
    def get_conversation_insights(self, days: int = 30) -> Dict:
        """Get conversation pattern insights"""
        try:
            cursor = self.db.cursor()
            since = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT character_id, COUNT(*), AVG(message_count)
                FROM conversation_analytics
                WHERE created_at > ? AND character_id IS NOT NULL
                GROUP BY character_id
                ORDER BY COUNT(*) DESC
            ''', (since,))
            
            character_stats = {}
            for row in cursor.fetchall():
                character_stats[row[0]] = {'sessions': row[1], 'avg_messages': round(row[2] or 0, 1)}
            
            cursor.execute('SELECT AVG(message_count), AVG(session_duration_seconds), AVG(avg_message_length) FROM conversation_analytics WHERE created_at > ?', (since,))
            row = cursor.fetchone()
            
            return {
                'period_days': days,
                'character_popularity': character_stats,
                'avg_messages_per_session': round(row[0] or 0, 1),
                'avg_session_duration_minutes': round((row[1] or 0) / 60, 1),
                'avg_message_length': round(row[2] or 0, 0)
            }
        except Exception as e:
            return {'period_days': days, 'character_popularity': {}, 'avg_messages_per_session': 0, 'avg_session_duration_minutes': 0, 'avg_message_length': 0, 'note': 'Analytics tables not initialized'}
    
    def get_hourly_activity(self, days: int = 7) -> Dict:
        """Get activity breakdown by hour of day"""
        try:
            cursor = self.db.cursor()
            since = datetime.now() - timedelta(days=days)
            
            cursor.execute('SELECT strftime("%H", last_activity_at) as hour, COUNT(*) FROM user_activity_log WHERE last_activity_at > ? GROUP BY hour ORDER BY hour', (since,))
            
            hourly = {str(i).zfill(2): 0 for i in range(24)}
            for row in cursor.fetchall():
                hourly[row[0]] = row[1]
            
            sorted_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)
            peak_hours = [h for h, _ in sorted_hours[:3]]
            
            return {'hourly_distribution': hourly, 'peak_hours': peak_hours, 'total_activities': sum(hourly.values())}
        except Exception as e:
            return {'hourly_distribution': {str(i).zfill(2): 0 for i in range(24)}, 'peak_hours': [], 'total_activities': 0, 'note': 'Analytics tables not initialized'}
    
    def record_conversation_session(self, user_id: int, character_id: str,
                                    message_count: int, duration_seconds: int,
                                    avg_message_length: float = None,
                                    topics: List[str] = None) -> None:
        """Record a conversation session for analytics"""
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO conversation_analytics 
                (user_id, character_id, message_count, session_duration_seconds, 
                 avg_message_length, topics)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, character_id, message_count, duration_seconds,
                  avg_message_length, json.dumps(topics) if topics else None))
            self.db.commit()
        except Exception as e:
            print(f"Error recording session: {e}")
    
    def update_daily_stats(self) -> None:
        """Update daily statistics (call at end of day or on demand)"""
        cursor = self.db.cursor()
        today = datetime.now().date()
        
        # Get today's stats
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM user_activity_log
            WHERE DATE(created_at) = ?
        ''', (today,))
        active_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_activity_log
            WHERE DATE(created_at) = ? AND action_type = 'message_sent'
        ''', (today,))
        total_messages = cursor.fetchone()[0]
        
        # Insert or update
        cursor.execute('''
            INSERT INTO daily_stats (date, active_users, total_messages)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                active_users = ?,
                total_messages = ?
        ''', (today, active_users, total_messages, active_users, total_messages))
        
        self.db.commit()
    
    def get_trend_data(self, metric: str, days: int = 30) -> List[Dict]:
        """Get trend data for a specific metric"""
        try:
            cursor = self.db.cursor()
            since = datetime.now() - timedelta(days=days)
            
            if metric == 'active_users':
                cursor.execute('SELECT DATE(created_at), COUNT(DISTINCT user_id) FROM user_activity_log WHERE created_at > ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)', (since,))
            elif metric == 'messages':
                cursor.execute('SELECT DATE(created_at), COUNT(*) FROM user_activity_log WHERE created_at > ? AND action_type = ? GROUP BY DATE(created_at) ORDER BY DATE(created_at)', (since, 'message_sent'))
            else:
                return []
            
            return [{'date': row[0], 'value': row[1]} for row in cursor.fetchall()]
        except Exception as e:
            return []


def create_user_analytics(db_connection: sqlite3.Connection) -> UserAnalytics:
    """Factory function"""
    return UserAnalytics(db_connection)
