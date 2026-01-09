"""
Monitoring and Error Tracking Module
Provides error tracking, uptime monitoring, and alerting.
"""
import time
import traceback
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
import threading
import json


@dataclass
class ErrorEvent:
    """Represents a tracked error"""
    error_type: str
    message: str
    endpoint: str
    user_id: Optional[int]
    timestamp: float
    traceback: str
    context: Dict = field(default_factory=dict)
    resolved: bool = False


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time_ms: float
    last_check: float
    details: Dict = field(default_factory=dict)


class ErrorTracker:
    """
    Tracks and aggregates application errors.
    
    Features:
    - Error deduplication
    - Rate tracking
    - Pattern detection
    - Alerting thresholds
    """
    
    MAX_ERRORS = 1000  # Maximum errors to keep in memory
    ALERT_THRESHOLD = 10  # Errors per minute to trigger alert
    
    def __init__(self):
        self._errors: deque = deque(maxlen=self.MAX_ERRORS)
        self._error_counts: Dict[str, int] = {}  # error_type -> count
        self._lock = threading.RLock()
        self._alert_callbacks: List[Callable] = []
        self._last_alert_time: Dict[str, float] = {}
    
    def track_error(self, error: Exception, endpoint: str = '', 
                    user_id: int = None, context: Dict = None) -> ErrorEvent:
        """Track an error occurrence"""
        error_type = type(error).__name__
        tb = traceback.format_exc()
        
        event = ErrorEvent(
            error_type=error_type,
            message=str(error),
            endpoint=endpoint,
            user_id=user_id,
            timestamp=time.time(),
            traceback=tb,
            context=context or {}
        )
        
        with self._lock:
            self._errors.append(event)
            self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
            
            # Check if we should alert
            self._check_alert(error_type)
        
        return event
    
    def _check_alert(self, error_type: str) -> None:
        """Check if error rate warrants an alert"""
        now = time.time()
        one_minute_ago = now - 60
        
        # Count recent errors of this type
        recent_count = sum(1 for e in self._errors 
                         if e.error_type == error_type and e.timestamp > one_minute_ago)
        
        if recent_count >= self.ALERT_THRESHOLD:
            # Check cooldown (don't spam alerts)
            last_alert = self._last_alert_time.get(error_type, 0)
            if now - last_alert > 300:  # 5 minute cooldown
                self._last_alert_time[error_type] = now
                self._trigger_alert(error_type, recent_count)
    
    def _trigger_alert(self, error_type: str, count: int) -> None:
        """Trigger alert callbacks"""
        for callback in self._alert_callbacks:
            try:
                callback(error_type, count)
            except:
                pass  # Don't let callback errors break tracking
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register a callback for alerts"""
        self._alert_callbacks.append(callback)
    
    def get_recent_errors(self, limit: int = 50, error_type: str = None) -> List[Dict]:
        """Get recent errors"""
        with self._lock:
            errors = list(self._errors)
            
            if error_type:
                errors = [e for e in errors if e.error_type == error_type]
            
            # Most recent first
            errors = sorted(errors, key=lambda e: e.timestamp, reverse=True)[:limit]
            
            return [{
                'type': e.error_type,
                'message': e.message,
                'endpoint': e.endpoint,
                'user_id': e.user_id,
                'timestamp': datetime.fromtimestamp(e.timestamp).isoformat(),
                'context': e.context
            } for e in errors]
    
    def get_error_summary(self) -> Dict:
        """Get error statistics"""
        with self._lock:
            now = time.time()
            hour_ago = now - 3600
            day_ago = now - 86400
            
            last_hour = [e for e in self._errors if e.timestamp > hour_ago]
            last_day = [e for e in self._errors if e.timestamp > day_ago]
            
            # Group by type
            by_type = {}
            for e in last_day:
                by_type[e.error_type] = by_type.get(e.error_type, 0) + 1
            
            return {
                'total_tracked': len(self._errors),
                'last_hour': len(last_hour),
                'last_24h': len(last_day),
                'by_type': by_type,
                'top_errors': sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]
            }


class UptimeMonitor:
    """
    Monitors application and dependency health.
    
    Features:
    - Periodic health checks
    - Response time tracking
    - Dependency monitoring
    """
    
    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._history: Dict[str, deque] = {}  # name -> response times
        self._lock = threading.RLock()
        self._start_time = time.time()
    
    def record_check(self, name: str, status: str, response_time_ms: float,
                    details: Dict = None) -> HealthCheck:
        """Record a health check result"""
        check = HealthCheck(
            name=name,
            status=status,
            response_time_ms=response_time_ms,
            last_check=time.time(),
            details=details or {}
        )
        
        with self._lock:
            self._checks[name] = check
            
            if name not in self._history:
                self._history[name] = deque(maxlen=100)
            self._history[name].append(response_time_ms)
        
        return check
    
    def check_database(self, db_connection) -> HealthCheck:
        """Check database health"""
        start = time.time()
        try:
            cursor = db_connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            response_time = (time.time() - start) * 1000
            return self.record_check('database', 'healthy', response_time)
        except Exception as e:
            response_time = (time.time() - start) * 1000
            return self.record_check('database', 'unhealthy', response_time, 
                                    {'error': str(e)})
    
    def get_uptime(self) -> Dict:
        """Get uptime statistics"""
        uptime_seconds = time.time() - self._start_time
        
        return {
            'uptime_seconds': int(uptime_seconds),
            'uptime_formatted': str(timedelta(seconds=int(uptime_seconds))),
            'started_at': datetime.fromtimestamp(self._start_time).isoformat()
        }
    
    def get_health_status(self) -> Dict:
        """Get overall health status"""
        with self._lock:
            checks = {}
            overall_status = 'healthy'
            
            for name, check in self._checks.items():
                checks[name] = {
                    'status': check.status,
                    'response_time_ms': round(check.response_time_ms, 2),
                    'last_check': datetime.fromtimestamp(check.last_check).isoformat()
                }
                
                if check.status == 'unhealthy':
                    overall_status = 'unhealthy'
                elif check.status == 'degraded' and overall_status == 'healthy':
                    overall_status = 'degraded'
            
            # Calculate average response times
            avg_times = {}
            for name, history in self._history.items():
                if history:
                    avg_times[name] = round(sum(history) / len(history), 2)
            
            return {
                'status': overall_status,
                'checks': checks,
                'average_response_times': avg_times,
                **self.get_uptime()
            }


class AlertManager:
    """
    Manages alerts and notifications.
    
    Features:
    - Multiple alert channels (console, database, webhook)
    - Alert deduplication
    - Severity levels
    """
    
    SEVERITY_LEVELS = ['info', 'warning', 'error', 'critical']
    
    def __init__(self, db_connection=None):
        self._alerts: deque = deque(maxlen=500)
        self._db = db_connection
        self._lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize alerts table"""
        if self._db:
            try:
                cursor = self._db.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        severity TEXT NOT NULL,
                        category TEXT NOT NULL,
                        message TEXT NOT NULL,
                        details TEXT,
                        acknowledged BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self._db.commit()
            except:
                pass
    
    def send_alert(self, severity: str, category: str, message: str, 
                   details: Dict = None) -> None:
        """Send an alert"""
        alert = {
            'severity': severity,
            'category': category,
            'message': message,
            'details': details or {},
            'timestamp': time.time()
        }
        
        with self._lock:
            self._alerts.append(alert)
        
        # Log to console
        log_level = getattr(logging, severity.upper(), logging.INFO)
        logging.log(log_level, f"[{category}] {message}")
        
        # Save to database
        if self._db:
            try:
                cursor = self._db.cursor()
                cursor.execute('''
                    INSERT INTO system_alerts (severity, category, message, details)
                    VALUES (?, ?, ?, ?)
                ''', (severity, category, message, json.dumps(details or {})))
                self._db.commit()
            except:
                pass
    
    def get_recent_alerts(self, limit: int = 50, severity: str = None) -> List[Dict]:
        """Get recent alerts"""
        with self._lock:
            alerts = list(self._alerts)
            
            if severity:
                alerts = [a for a in alerts if a['severity'] == severity]
            
            return sorted(alerts, key=lambda a: a['timestamp'], reverse=True)[:limit]


# Global instances
_error_tracker = ErrorTracker()
_uptime_monitor = UptimeMonitor()
_alert_manager = None


def get_error_tracker() -> ErrorTracker:
    return _error_tracker


def get_uptime_monitor() -> UptimeMonitor:
    return _uptime_monitor


def get_alert_manager(db_connection=None) -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(db_connection)
    return _alert_manager


def track_error(error: Exception, endpoint: str = '', user_id: int = None, 
                context: Dict = None) -> ErrorEvent:
    """Convenience function to track an error"""
    return _error_tracker.track_error(error, endpoint, user_id, context)
