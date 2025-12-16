"""
Developer Analytics System
Special privileged access for developers to study the system.
Provides deep insights into AI behavior, user patterns, and system performance.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class SystemMetrics:
    """System-wide metrics for developers"""
    total_ai_calls_today: int
    total_ai_calls_week: int
    avg_tokens_per_call: float
    total_users: int
    active_users_today: int
    total_conversations: int
    avg_messages_per_conversation: float
    error_rate: float
    circuit_breaker_activations: int
    

class DeveloperAnalytics:
    """
    Provides developer-level access to system internals.
    
    Developer privileges (beyond administrator):
    - View all AI call logs with full details
    - Access raw database queries
    - View system performance metrics
    - Export data for analysis
    - View algorithm effectiveness scores
    - Access pattern extraction internals
    - View user context learning in real-time
    - Debug mode access
    """
    
    # Developer AI budget (much higher than admin)
    DEVELOPER_DAILY_LIMIT = 5000  # 5x admin limit
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create developer-specific tracking tables"""
        cursor = self.db.cursor()
        
        # Developer access log (audit trail)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS developer_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                endpoint TEXT,
                parameters TEXT,
                result_summary TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # System health snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_health_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metrics_json TEXT NOT NULL,
                snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dev_access_user ON developer_access_log(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dev_access_time ON developer_access_log(timestamp)')
        
        self.db.commit()
    
    def log_access(self, user_id: int, action: str, endpoint: str = None, 
                   parameters: Dict = None, result_summary: str = None):
        """Log developer access for audit trail"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO developer_access_log
            (user_id, action, endpoint, parameters, result_summary)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, endpoint, 
              json.dumps(parameters) if parameters else None,
              result_summary))
        self.db.commit()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        cursor = self.db.cursor()
        metrics = {}
        
        # AI usage metrics
        cursor.execute('''
            SELECT COUNT(*), AVG(input_tokens + output_tokens)
            FROM ai_usage_log WHERE DATE(timestamp) = DATE('now')
        ''')
        row = cursor.fetchone()
        metrics['ai_calls_today'] = row[0] or 0
        metrics['avg_tokens_per_call'] = round(row[1] or 0, 1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log 
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        metrics['ai_calls_week'] = cursor.fetchone()[0] or 0
        
        # Error rate
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN success = 0 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)
            FROM ai_usage_log WHERE DATE(timestamp) = DATE('now')
        ''')
        metrics['error_rate_today'] = round(cursor.fetchone()[0] or 0, 2)
        
        # User metrics
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_deleted = 0')
        metrics['total_users'] = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM history_primary
            WHERE DATE(timestamp) = DATE('now')
        ''')
        metrics['active_users_today'] = cursor.fetchone()[0] or 0
        
        # Conversation metrics
        cursor.execute('SELECT COUNT(*) FROM history_primary')
        metrics['total_messages'] = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT AVG(msg_count) FROM (
                SELECT COUNT(*) as msg_count FROM history_primary
                GROUP BY user_id, character
            )
        ''')
        metrics['avg_messages_per_conversation'] = round(cursor.fetchone()[0] or 0, 1)
        
        # Budget notifications
        cursor.execute('''
            SELECT COUNT(*) FROM ai_budget_notifications
            WHERE notification_type = 'circuit_breaker'
        ''')
        metrics['circuit_breaker_activations'] = cursor.fetchone()[0] or 0
        
        # User context metrics
        cursor.execute('SELECT COUNT(*) FROM user_context')
        metrics['total_user_context_facts'] = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM user_language_patterns')
        metrics['total_language_patterns'] = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM conversation_summaries')
        metrics['total_summaries'] = cursor.fetchone()[0] or 0
        
        return metrics
    
    def get_ai_call_details(self, limit: int = 100, 
                           filters: Dict = None) -> List[Dict]:
        """Get detailed AI call logs for analysis"""
        cursor = self.db.cursor()
        
        query = '''
            SELECT id, timestamp, call_type, character, user_id, 
                   estimated_cost, purpose, input_tokens, output_tokens,
                   success, error_message, is_background
            FROM ai_usage_log
        '''
        
        conditions = []
        params = []
        
        if filters:
            if filters.get('date_from'):
                conditions.append('timestamp >= ?')
                params.append(filters['date_from'])
            if filters.get('date_to'):
                conditions.append('timestamp <= ?')
                params.append(filters['date_to'])
            if filters.get('call_type'):
                conditions.append('call_type = ?')
                params.append(filters['call_type'])
            if filters.get('user_id'):
                conditions.append('user_id = ?')
                params.append(filters['user_id'])
            if filters.get('success') is not None:
                conditions.append('success = ?')
                params.append(1 if filters['success'] else 0)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        columns = ['id', 'timestamp', 'call_type', 'character', 'user_id',
                  'estimated_cost', 'purpose', 'input_tokens', 'output_tokens',
                  'success', 'error_message', 'is_background']
        
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_user_context_analysis(self, user_id: int = None) -> Dict[str, Any]:
        """Get detailed user context analysis"""
        cursor = self.db.cursor()
        result = {}
        
        # Aggregate stats
        if user_id:
            cursor.execute('''
                SELECT fact_type, COUNT(*), AVG(confidence)
                FROM user_context WHERE user_id = ? AND is_active = 1
                GROUP BY fact_type
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT fact_type, COUNT(*), AVG(confidence)
                FROM user_context WHERE is_active = 1
                GROUP BY fact_type
            ''')
        
        result['fact_distribution'] = [
            {'type': row[0], 'count': row[1], 'avg_confidence': round(row[2] or 0, 2)}
            for row in cursor.fetchall()
        ]
        
        # Language patterns
        if user_id:
            cursor.execute('''
                SELECT pattern_type, user_phrase, frequency
                FROM user_language_patterns WHERE user_id = ?
                ORDER BY frequency DESC LIMIT 20
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT pattern_type, user_phrase, SUM(frequency) as total_freq
                FROM user_language_patterns
                GROUP BY pattern_type, user_phrase
                ORDER BY total_freq DESC LIMIT 50
            ''')
        
        result['top_language_patterns'] = [
            {'type': row[0], 'phrase': row[1], 'frequency': row[2]}
            for row in cursor.fetchall()
        ]
        
        # Summary stats
        cursor.execute('''
            SELECT character_id, COUNT(*), AVG(message_count)
            FROM conversation_summaries
            GROUP BY character_id
        ''')
        result['summary_by_character'] = [
            {'character': row[0], 'count': row[1], 'avg_messages': round(row[2] or 0, 1)}
            for row in cursor.fetchall()
        ]
        
        return result
    
    def get_character_effectiveness(self) -> List[Dict]:
        """Get character effectiveness scores and usage"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT character_id, display_name, effectiveness_score, 
                   usage_count, domain
            FROM character_library
            ORDER BY effectiveness_score DESC
        ''')
        
        return [
            {
                'character_id': row[0],
                'display_name': row[1],
                'effectiveness': round(row[2] or 0.5, 2),
                'usage_count': row[3] or 0,
                'domain': row[4]
            }
            for row in cursor.fetchall()
        ]
    
    def get_clarification_effectiveness(self) -> Dict[str, Any]:
        """Analyze how effective clarification questions are"""
        cursor = self.db.cursor()
        
        # Questions asked vs answered
        cursor.execute('''
            SELECT 
                COUNT(*) as total_asked,
                SUM(CASE WHEN user_response IS NOT NULL THEN 1 ELSE 0 END) as answered,
                SUM(CASE WHEN was_helpful = 1 THEN 1 ELSE 0 END) as helpful
            FROM clarification_history
        ''')
        row = cursor.fetchone()
        
        result = {
            'total_questions_asked': row[0] or 0,
            'questions_answered': row[1] or 0,
            'questions_helpful': row[2] or 0,
            'answer_rate': round((row[1] or 0) / max(row[0] or 1, 1) * 100, 1),
            'helpfulness_rate': round((row[2] or 0) / max(row[1] or 1, 1) * 100, 1)
        }
        
        # By reason type
        cursor.execute('''
            SELECT reason, COUNT(*), 
                   SUM(CASE WHEN was_helpful = 1 THEN 1 ELSE 0 END)
            FROM clarification_history
            GROUP BY reason
        ''')
        result['by_reason'] = [
            {'reason': row[0], 'count': row[1], 'helpful': row[2] or 0}
            for row in cursor.fetchall()
        ]
        
        return result
    
    def export_data(self, table: str, format: str = 'json',
                   filters: Dict = None) -> Any:
        """Export table data for external analysis"""
        allowed_tables = [
            'ai_usage_log', 'user_context', 'user_language_patterns',
            'conversation_summaries', 'user_engagement', 'history_primary',
            'clarification_history', 'character_library', 'character_usage_outcomes'
        ]
        
        if table not in allowed_tables:
            raise ValueError(f"Table '{table}' not allowed for export")
        
        cursor = self.db.cursor()
        
        # Get column names
        cursor.execute(f'PRAGMA table_info({table})')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get data
        query = f'SELECT * FROM {table}'
        params = []
        
        if filters and filters.get('limit'):
            query += f" LIMIT {int(filters['limit'])}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if format == 'json':
            return [dict(zip(columns, row)) for row in rows]
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            return output.getvalue()
        else:
            return {'columns': columns, 'rows': rows}
    
    def run_custom_query(self, query: str, params: tuple = None) -> Dict:
        """
        Run a custom read-only query (SELECT only).
        DANGEROUS - only for developers.
        """
        # Safety check - only allow SELECT
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries allowed")
        
        # Block dangerous keywords
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")
        
        cursor = self.db.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            return {
                'columns': columns,
                'rows': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_debug_info(self, component: str = 'all') -> Dict[str, Any]:
        """Get debug information for system components"""
        cursor = self.db.cursor()
        debug = {}
        
        if component in ('all', 'database'):
            # Table sizes
            cursor.execute('''
                SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
            ''')
            tables = [row[0] for row in cursor.fetchall()]
            
            debug['tables'] = {}
            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    debug['tables'][table] = cursor.fetchone()[0]
                except:
                    debug['tables'][table] = 'error'
        
        if component in ('all', 'indexes'):
            cursor.execute('''
                SELECT name, tbl_name FROM sqlite_master 
                WHERE type='index' ORDER BY tbl_name
            ''')
            debug['indexes'] = [
                {'name': row[0], 'table': row[1]}
                for row in cursor.fetchall()
            ]
        
        if component in ('all', 'recent_errors'):
            cursor.execute('''
                SELECT timestamp, error_message, call_type, purpose
                FROM ai_usage_log
                WHERE success = 0
                ORDER BY timestamp DESC LIMIT 20
            ''')
            debug['recent_errors'] = [
                {'timestamp': row[0], 'error': row[1], 'type': row[2], 'purpose': row[3]}
                for row in cursor.fetchall()
            ]
        
        return debug
    
    def take_health_snapshot(self) -> int:
        """Take a snapshot of current system health"""
        metrics = self.get_system_metrics()
        
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO system_health_snapshots (metrics_json)
            VALUES (?)
        ''', (json.dumps(metrics),))
        self.db.commit()
        
        return cursor.lastrowid
    
    def get_health_history(self, days: int = 7) -> List[Dict]:
        """Get health snapshot history"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, metrics_json, snapshot_time
            FROM system_health_snapshots
            WHERE snapshot_time > datetime('now', ?)
            ORDER BY snapshot_time DESC
        ''', (f'-{days} days',))
        
        return [
            {
                'id': row[0],
                'metrics': json.loads(row[1]),
                'timestamp': row[2]
            }
            for row in cursor.fetchall()
        ]


def create_developer_analytics(db_connection: sqlite3.Connection) -> DeveloperAnalytics:
    """Factory function"""
    return DeveloperAnalytics(db_connection)
