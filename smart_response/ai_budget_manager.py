"""
AI Budget Manager
Strict cost control and monitoring for all AI calls
Prevents runaway expenses with circuit breakers and notifications
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
import time


class AIBudgetManager:
    """
    Manages AI usage with strict limits and monitoring
    
    USER REQUIREMENTS:
    - Maximum 100 AI calls per day (TOTAL)
    - Notify user when funds run out
    - Monitor and detect unusual patterns
    - Circuit breaker for emergencies
    """
    
    # HARD LIMITS (as per user requirements)
    DAILY_CALL_LIMIT = 100  # Maximum 100 calls/day TOTAL
    HOURLY_CALL_LIMIT = 30  # Maximum 30 calls/hour (prevent spikes)
    BACKGROUND_CALL_LIMIT = 10  # Maximum 10 background calls/day
    
    # RATE LIMITS
    CALLS_PER_MINUTE = 20  # Max 20 calls/minute
    
    # COST TRACKING (for reporting)
    COST_PER_CALL = 0.002  # Approximate cost per call
    
    # PATTERN THRESHOLDS
    SPIKE_THRESHOLD = 15  # >15 calls in 5 minutes = spike
    LOOP_THRESHOLD = 10  # >10 identical calls in 2 minutes = loop
    ERROR_THRESHOLD = 5  # >5 errors in 5 minutes = cascade
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_tables()
        self.circuit_breaker_active = False
        self.notifications_sent = {}  # Track notifications to avoid spam
    
    def _init_tables(self):
        """Create tables for AI usage tracking"""
        cursor = self.db.cursor()
        
        # Track every AI call
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage_log (
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
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usage_timestamp 
            ON ai_usage_log(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_usage_type_time 
            ON ai_usage_log(call_type, timestamp)
        ''')
        
        # Track unusual patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_usage_patterns (
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
            )
        ''')
        
        # Track notifications sent to user
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_budget_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notification_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT 0
            )
        ''')
        
        self.db.commit()
        print("✓ AI Budget Manager initialized (100 calls/day limit)")
    
    def request_ai_call(self, call_type: str, purpose: str,
                       user_id: Optional[int] = None,
                       character: Optional[str] = None,
                       is_background: bool = False) -> Tuple[bool, str]:
        """
        Request permission to make an AI call
        
        Returns:
            (allowed, reason) - If False, reason explains why denied
        """
        
        # CIRCUIT BREAKER CHECK
        if self.circuit_breaker_active:
            self._notify_user(
                'circuit_breaker_active',
                'AI calls temporarily halted due to circuit breaker activation. Manual reset required.',
                'critical'
            )
            return False, "Circuit breaker active - AI calls temporarily halted"
        
        # CHECK DAILY LIMIT (MOST IMPORTANT)
        calls_today = self._get_calls_in_period('day')
        if calls_today >= self.DAILY_CALL_LIMIT:
            self._trigger_circuit_breaker(f"Daily limit reached: {calls_today}/{self.DAILY_CALL_LIMIT} calls")
            self._notify_user(
                'daily_limit_reached',
                f'AI call limit reached: {calls_today}/{self.DAILY_CALL_LIMIT} calls today. System using fallback responses.',
                'critical'
            )
            return False, f"Daily limit reached: {calls_today}/{self.DAILY_CALL_LIMIT} calls"
        
        # WARN at 80% of daily limit
        if calls_today >= self.DAILY_CALL_LIMIT * 0.8:
            remaining = self.DAILY_CALL_LIMIT - calls_today
            self._notify_user(
                'daily_limit_warning',
                f'AI budget warning: {calls_today}/{self.DAILY_CALL_LIMIT} calls used today. {remaining} remaining.',
                'warning'
            )
        
        # Check hourly limit (prevent spikes)
        calls_this_hour = self._get_calls_in_period('hour')
        if calls_this_hour >= self.HOURLY_CALL_LIMIT:
            self._trigger_throttle(f"Hourly limit reached: {calls_this_hour}/{self.HOURLY_CALL_LIMIT}")
            self._notify_user(
                'hourly_limit_reached',
                f'AI calls throttled: {calls_this_hour}/{self.HOURLY_CALL_LIMIT} calls this hour. Using cached responses.',
                'warning'
            )
            return False, f"Hourly limit reached: {calls_this_hour}/{self.HOURLY_CALL_LIMIT} calls"
        
        # Check background limit (if background call)
        if is_background:
            background_today = self._get_background_calls_today()
            if background_today >= self.BACKGROUND_CALL_LIMIT:
                return False, f"Background limit reached: {background_today}/{self.BACKGROUND_CALL_LIMIT} calls"
        
        # Check rate limits (prevent rapid firing)
        calls_last_minute = self._get_calls_last_n_minutes(1)
        if calls_last_minute >= self.CALLS_PER_MINUTE:
            self._trigger_throttle("Rate limit: calls per minute")
            return False, f"Rate limit: {calls_last_minute} calls in last minute (max {self.CALLS_PER_MINUTE})"
        
        # Check for unusual patterns
        pattern = self._detect_unusual_pattern()
        if pattern and pattern['severity'] in ['high', 'critical']:
            self._trigger_circuit_breaker(f"Unusual pattern: {pattern['pattern_type']}")
            self._notify_user(
                'unusual_pattern',
                f"Unusual AI usage pattern detected: {pattern['pattern_type']}. System paused for safety.",
                'critical'
            )
            return False, f"Unusual usage pattern detected: {pattern['pattern_type']}"
        
        # APPROVED
        return True, "OK"
    
    def log_ai_call(self, call_type: str, purpose: str,
                   success: bool,
                   user_id: Optional[int] = None,
                   character: Optional[str] = None,
                   is_background: bool = False,
                   input_tokens: int = 0,
                   output_tokens: int = 0,
                   error_message: Optional[str] = None):
        """Log every AI call for tracking and analysis"""
        
        estimated_cost = self.COST_PER_CALL
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO ai_usage_log
            (call_type, character, user_id, estimated_cost, purpose,
             input_tokens, output_tokens, success, error_message,
             is_background, is_automated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            call_type, character, user_id, estimated_cost, purpose,
            input_tokens, output_tokens, success, error_message,
            is_background, is_background
        ))
        
        self.db.commit()
        
        # If failed, check for error cascade
        if not success:
            recent_errors = self._count_recent_errors()
            if recent_errors >= self.ERROR_THRESHOLD:
                self._notify_user(
                    'error_cascade',
                    f'Multiple AI call failures detected ({recent_errors} in 5 minutes). Check API status.',
                    'high'
                )
    
    def _get_calls_in_period(self, period: str) -> int:
        """Get number of calls in specified period"""
        cursor = self.db.cursor()
        
        if period == 'day':
            cursor.execute('''
                SELECT COUNT(*) FROM ai_usage_log
                WHERE DATE(timestamp) = DATE('now')
            ''')
        elif period == 'hour':
            cursor.execute('''
                SELECT COUNT(*) FROM ai_usage_log
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
        else:
            return 0
        
        return cursor.fetchone()[0]
    
    def _get_background_calls_today(self) -> int:
        """Get background calls made today"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE DATE(timestamp) = DATE('now')
            AND is_background = 1
        ''')
        
        return cursor.fetchone()[0]
    
    def _get_calls_last_n_minutes(self, n: int) -> int:
        """Get number of calls in last N minutes"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE timestamp > datetime('now', '-' || ? || ' minutes')
        ''', (n,))
        
        return cursor.fetchone()[0]
    
    def _count_recent_errors(self) -> int:
        """Count errors in last 5 minutes"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE timestamp > datetime('now', '-5 minutes')
            AND success = 0
        ''')
        
        return cursor.fetchone()[0]
    
    def _detect_unusual_pattern(self) -> Optional[Dict]:
        """
        Detect unusual usage patterns:
        - Spikes (too many calls too fast)
        - Loops (same call repeated)
        - Error cascades (multiple failures)
        """
        cursor = self.db.cursor()
        
        # Pattern 1: Spike (>15 calls in 5 minutes)
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE timestamp > datetime('now', '-5 minutes')
        ''')
        recent_calls = cursor.fetchone()[0]
        
        if recent_calls > self.SPIKE_THRESHOLD:
            self._log_pattern('spike', 'critical', recent_calls, 5)
            return {
                'pattern_type': 'spike',
                'severity': 'critical',
                'call_count': recent_calls
            }
        
        # Pattern 2: Loop (same call_type + purpose repeated rapidly)
        cursor.execute('''
            SELECT call_type, purpose, COUNT(*) as cnt
            FROM ai_usage_log
            WHERE timestamp > datetime('now', '-2 minutes')
            GROUP BY call_type, purpose
            HAVING cnt > ?
        ''', (self.LOOP_THRESHOLD,))
        
        loop_detected = cursor.fetchone()
        if loop_detected:
            self._log_pattern('loop', 'high', loop_detected[2], 2)
            return {
                'pattern_type': 'loop',
                'severity': 'high',
                'call_count': loop_detected[2]
            }
        
        # Pattern 3: Error cascade (>5 errors in 5 minutes)
        error_count = self._count_recent_errors()
        if error_count > self.ERROR_THRESHOLD:
            self._log_pattern('error_cascade', 'high', error_count, 5)
            return {
                'pattern_type': 'error_cascade',
                'severity': 'high',
                'call_count': error_count
            }
        
        return None
    
    def _log_pattern(self, pattern_type: str, severity: str,
                    call_count: int, time_window: int):
        """Log detected unusual pattern"""
        cursor = self.db.cursor()
        
        # Check if already logged recently (avoid duplicates)
        cursor.execute('''
            SELECT id FROM ai_usage_patterns
            WHERE pattern_type = ?
            AND detected_at > datetime('now', '-10 minutes')
            AND resolved_at IS NULL
        ''', (pattern_type,))
        
        if cursor.fetchone():
            return  # Already logged
        
        cost_impact = call_count * self.COST_PER_CALL
        
        cursor.execute('''
            INSERT INTO ai_usage_patterns
            (pattern_type, severity, call_count, time_window_minutes, cost_impact)
            VALUES (?, ?, ?, ?, ?)
        ''', (pattern_type, severity, call_count, time_window, cost_impact))
        
        self.db.commit()
    
    def _trigger_throttle(self, reason: str):
        """Throttle AI calls (soft limit)"""
        print(f"⚠️ AI THROTTLE: {reason}")
        
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_usage_patterns
            SET action_taken = 'throttled'
            WHERE resolved_at IS NULL
            AND action_taken IS NULL
        ''')
        self.db.commit()
    
    def _trigger_circuit_breaker(self, reason: str):
        """EMERGENCY: Stop all AI calls (hard limit)"""
        self.circuit_breaker_active = True
        print(f"🚨 CIRCUIT BREAKER ACTIVATED: {reason}")
        print(f"   All AI calls halted. Manual reset required.")
        
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_usage_patterns
            SET action_taken = 'circuit_breaker'
            WHERE resolved_at IS NULL
            AND action_taken IS NULL
        ''')
        self.db.commit()
    
    def _notify_user(self, notification_type: str, message: str, severity: str):
        """
        Notify user about budget issues
        
        USER REQUIREMENT: Notify when funds run out or issues occur
        """
        
        # Prevent notification spam (one per hour per type)
        notification_key = f"{notification_type}_{datetime.now().strftime('%Y-%m-%d-%H')}"
        if notification_key in self.notifications_sent:
            return  # Already notified this hour
        
        self.notifications_sent[notification_key] = True
        
        # Store notification in database
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO ai_budget_notifications
            (notification_type, message, severity)
            VALUES (?, ?, ?)
        ''', (notification_type, message, severity))
        self.db.commit()
        
        # Print to console (immediate notification)
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'high': '🔴',
            'critical': '🚨'
        }
        
        emoji = severity_emoji.get(severity, 'ℹ️')
        print(f"\n{emoji} AI BUDGET NOTIFICATION:")
        print(f"   {message}\n")
        
        # In production: Also send email, SMS, Slack, etc.
    
    def reset_circuit_breaker(self, reason: str = "Manual reset"):
        """
        Reset circuit breaker
        Should be called manually by administrator
        """
        self.circuit_breaker_active = False
        print(f"✅ Circuit breaker reset: {reason}")
        
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_usage_patterns
            SET resolved_at = CURRENT_TIMESTAMP
            WHERE resolved_at IS NULL
        ''')
        self.db.commit()
        
        self._notify_user(
            'circuit_breaker_reset',
            f'Circuit breaker has been reset. AI calls resumed. Reason: {reason}',
            'info'
        )
    
    def get_usage_report(self) -> Dict:
        """
        Get current usage statistics
        For monitoring dashboard
        """
        cursor = self.db.cursor()
        
        # Today's stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_calls,
                SUM(estimated_cost) as total_cost,
                SUM(CASE WHEN is_background = 1 THEN 1 ELSE 0 END) as background_calls,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as error_count
            FROM ai_usage_log
            WHERE DATE(timestamp) = DATE('now')
        ''')
        
        row = cursor.fetchone()
        total_calls = row[0] or 0
        total_cost = row[1] or 0.0
        background_calls = row[2] or 0
        error_count = row[3] or 0
        
        # This hour's stats
        calls_this_hour = self._get_calls_in_period('hour')
        
        # Breakdown by call type
        cursor.execute('''
            SELECT call_type, COUNT(*), SUM(estimated_cost)
            FROM ai_usage_log
            WHERE DATE(timestamp) = DATE('now')
            GROUP BY call_type
        ''')
        
        breakdown = {
            row[0]: {'calls': row[1], 'cost': round(row[2], 3)}
            for row in cursor.fetchall()
        }
        
        # Recent patterns
        cursor.execute('''
            SELECT pattern_type, severity, detected_at, action_taken
            FROM ai_usage_patterns
            WHERE detected_at > datetime('now', '-24 hours')
            ORDER BY detected_at DESC
            LIMIT 5
        ''')
        
        patterns = [
            {
                'type': row[0],
                'severity': row[1],
                'time': row[2],
                'action': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        # Unacknowledged notifications
        cursor.execute('''
            SELECT COUNT(*) FROM ai_budget_notifications
            WHERE acknowledged = 0
        ''')
        unread_notifications = cursor.fetchone()[0]
        
        return {
            'today': {
                'calls': total_calls,
                'limit': self.DAILY_CALL_LIMIT,
                'remaining': self.DAILY_CALL_LIMIT - total_calls,
                'percentage_used': round((total_calls / self.DAILY_CALL_LIMIT) * 100, 1),
                'cost': round(total_cost, 2),
                'background_calls': background_calls,
                'errors': error_count
            },
            'this_hour': {
                'calls': calls_this_hour,
                'limit': self.HOURLY_CALL_LIMIT,
                'remaining': self.HOURLY_CALL_LIMIT - calls_this_hour
            },
            'breakdown': breakdown,
            'recent_patterns': patterns,
            'circuit_breaker_active': self.circuit_breaker_active,
            'unread_notifications': unread_notifications,
            'status': self._get_status_summary(total_calls, error_count)
        }
    
    def _get_status_summary(self, calls_today: int, errors: int) -> str:
        """Get human-readable status summary"""
        
        if self.circuit_breaker_active:
            return 'HALTED - Circuit breaker active'
        
        percentage = (calls_today / self.DAILY_CALL_LIMIT) * 100
        
        if percentage >= 100:
            return 'LIMIT REACHED - Using fallbacks'
        elif percentage >= 90:
            return 'CRITICAL - Nearly at limit'
        elif percentage >= 80:
            return 'WARNING - 80% budget used'
        elif percentage >= 50:
            return 'MODERATE - Half budget used'
        elif errors > 5:
            return 'ERRORS DETECTED - Check API'
        else:
            return 'HEALTHY - Normal operation'
    
    def get_unread_notifications(self) -> List[Dict]:
        """Get all unacknowledged notifications"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT id, sent_at, notification_type, message, severity
            FROM ai_budget_notifications
            WHERE acknowledged = 0
            ORDER BY sent_at DESC
        ''')
        
        return [
            {
                'id': row[0],
                'time': row[1],
                'type': row[2],
                'message': row[3],
                'severity': row[4]
            }
            for row in cursor.fetchall()
        ]
    
    def acknowledge_notification(self, notification_id: int):
        """Mark notification as read"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_budget_notifications
            SET acknowledged = 1
            WHERE id = ?
        ''', (notification_id,))
        self.db.commit()
    
    def acknowledge_all_notifications(self):
        """Mark all notifications as read"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_budget_notifications
            SET acknowledged = 1
            WHERE acknowledged = 0
        ''')
        self.db.commit()
