"""
System Health Monitor Agent

Autonomously monitors the health of the entire system:
- API endpoint responsiveness
- Database integrity & table counts
- AI budget consumption
- Character effectiveness trends
- Conversation quality metrics
- Error rate tracking
- Generates health reports with recommendations
"""

import requests
import json
import time
import sqlite3
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class HealthCheck:
    """Result of a single health check"""
    name: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class HealthReport:
    """Full system health report"""
    checks: List[HealthCheck]
    overall_status: str
    generated_at: str
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'overall_status': self.overall_status,
            'generated_at': self.generated_at,
            'checks': [
                {
                    'name': c.name,
                    'status': c.status,
                    'message': c.message,
                    'value': c.value,
                    'threshold': c.threshold,
                }
                for c in self.checks
            ],
            'recommendations': self.recommendations,
            'summary': {
                'healthy': sum(1 for c in self.checks if c.status == 'healthy'),
                'warning': sum(1 for c in self.checks if c.status == 'warning'),
                'critical': sum(1 for c in self.checks if c.status == 'critical'),
            }
        }


class SystemHealthAgent:
    """Monitors system health and generates reports"""
    
    def __init__(self, base_url: str, db_path: str = None, auth_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.db_path = db_path
        self.session = requests.Session()
        if auth_token:
            self.session.headers['Authorization'] = f'Bearer {auth_token}'
        self.history: List[HealthReport] = []
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate to get API access"""
        try:
            r = self.session.post(f"{self.base_url}/api/auth/login", json={
                'username': username, 'password': password
            }, timeout=30)
            if r.status_code == 200:
                token = r.json().get('token')
                if token:
                    self.session.headers['Authorization'] = f'Bearer {token}'
                    return True
            return False
        except Exception:
            return False
    
    # ================================================================
    # HEALTH CHECKS
    # ================================================================
    
    def check_api_health(self) -> HealthCheck:
        """Check if the API is responding"""
        try:
            start = time.time()
            r = self.session.get(f"{self.base_url}/", timeout=30)
            latency = time.time() - start
            
            if r.status_code == 200:
                if latency > 10:
                    return HealthCheck('api_response', 'warning',
                                      f'API responding but slow ({latency:.1f}s)',
                                      value=latency, threshold=10.0)
                return HealthCheck('api_response', 'healthy',
                                  f'API responding in {latency:.1f}s',
                                  value=latency, threshold=10.0)
            return HealthCheck('api_response', 'critical',
                              f'API returned status {r.status_code}',
                              value=float(r.status_code))
        except requests.Timeout:
            return HealthCheck('api_response', 'critical', 'API timeout (30s)')
        except requests.ConnectionError:
            return HealthCheck('api_response', 'critical', 'API connection refused')
        except Exception as e:
            return HealthCheck('api_response', 'critical', f'API error: {e}')
    
    def check_chat_endpoint(self) -> HealthCheck:
        """Check if the chat endpoint is functional"""
        try:
            # Try creating a conversation
            r = self.session.post(f"{self.base_url}/api/user/conversations", 
                                json={'title': 'Health Check'}, timeout=30)
            if r.status_code == 200:
                session_id = r.json().get('session_id')
                if session_id:
                    # Try sending a test message
                    start = time.time()
                    r2 = self.session.post(
                        f"{self.base_url}/api/user/conversations/{session_id}/messages",
                        json={'senderType': 'user', 'content': 'Health check: ping'},
                        timeout=60
                    )
                    latency = time.time() - start
                    
                    if r2.status_code == 200 and r2.json().get('ai_response'):
                        # Clean up - delete the test conversation
                        self.session.delete(
                            f"{self.base_url}/api/user/conversations/{session_id}",
                            timeout=10
                        )
                        if latency > 30:
                            return HealthCheck('chat_endpoint', 'warning',
                                              f'Chat responding but slow ({latency:.1f}s)',
                                              value=latency, threshold=30.0)
                        return HealthCheck('chat_endpoint', 'healthy',
                                          f'Chat responding in {latency:.1f}s',
                                          value=latency, threshold=30.0)
                    elif r2.status_code == 403:
                        return HealthCheck('chat_endpoint', 'warning',
                                          'Chat rate limited (expected for busy system)')
                    else:
                        return HealthCheck('chat_endpoint', 'warning',
                                          f'Chat returned {r2.status_code}')
            
            if r.status_code == 401:
                return HealthCheck('chat_endpoint', 'warning',
                                  'Not authenticated - cannot check chat endpoint')
            
            return HealthCheck('chat_endpoint', 'critical',
                              f'Conversation creation failed: {r.status_code}')
        except requests.Timeout:
            return HealthCheck('chat_endpoint', 'critical', 'Chat endpoint timeout (60s)')
        except Exception as e:
            return HealthCheck('chat_endpoint', 'critical', f'Chat error: {e}')
    
    def check_database_health(self) -> List[HealthCheck]:
        """Check database table counts and integrity"""
        checks = []
        
        if not self.db_path or not os.path.exists(self.db_path):
            checks.append(HealthCheck('database', 'warning', 
                                      f'Database not accessible: {self.db_path}'))
            return checks
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Check key tables exist and have data
            critical_tables = {
                'users': ('Users table', 1),
                'ai_conversations': ('Conversations table', 0),
                'messages': ('Messages table', 0),
                'conversation_outcomes': ('Effectiveness data', 0),
                'character_library': ('Character library', 0),
            }
            
            for table, (desc, min_expected) in critical_tables.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    if count < min_expected:
                        checks.append(HealthCheck(f'db_{table}', 'warning',
                                                  f'{desc}: {count} rows (expected >={min_expected})',
                                                  value=count, threshold=min_expected))
                    else:
                        checks.append(HealthCheck(f'db_{table}', 'healthy',
                                                  f'{desc}: {count} rows',
                                                  value=count))
                except sqlite3.OperationalError:
                    checks.append(HealthCheck(f'db_{table}', 'warning',
                                              f'{desc}: table does not exist'))
            
            # Check database size
            db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            if db_size_mb > 500:
                checks.append(HealthCheck('db_size', 'warning',
                                          f'Database is {db_size_mb:.1f}MB (consider cleanup)',
                                          value=db_size_mb, threshold=500))
            else:
                checks.append(HealthCheck('db_size', 'healthy',
                                          f'Database size: {db_size_mb:.1f}MB',
                                          value=db_size_mb))
            
            # Check recent activity
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM messages 
                    WHERE created_at > datetime('now', '-24 hours')
                """)
                recent = cursor.fetchone()[0]
                checks.append(HealthCheck('recent_activity', 'healthy',
                                          f'{recent} messages in last 24h',
                                          value=recent))
            except Exception:
                pass
            
            conn.close()
            
        except Exception as e:
            checks.append(HealthCheck('database', 'critical', f'Database error: {e}'))
        
        return checks
    
    def check_character_effectiveness(self) -> List[HealthCheck]:
        """Check character performance from effectiveness data"""
        checks = []
        
        if not self.db_path or not os.path.exists(self.db_path):
            return checks
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Overall satisfaction trend
            try:
                cursor.execute("""
                    SELECT AVG(satisfaction_estimate), COUNT(*)
                    FROM conversation_outcomes
                    WHERE analyzed_at > datetime('now', '-7 days')
                """)
                avg_sat, count = cursor.fetchone()
                
                if count and count > 0:
                    if avg_sat < 0.4:
                        checks.append(HealthCheck('avg_satisfaction', 'critical',
                                                  f'Low satisfaction ({avg_sat:.2f}) over {count} conversations',
                                                  value=avg_sat, threshold=0.4))
                    elif avg_sat < 0.6:
                        checks.append(HealthCheck('avg_satisfaction', 'warning',
                                                  f'Moderate satisfaction ({avg_sat:.2f}) over {count} conversations',
                                                  value=avg_sat, threshold=0.6))
                    else:
                        checks.append(HealthCheck('avg_satisfaction', 'healthy',
                                                  f'Good satisfaction ({avg_sat:.2f}) over {count} conversations',
                                                  value=avg_sat))
                else:
                    checks.append(HealthCheck('avg_satisfaction', 'warning',
                                              'No conversation outcomes in last 7 days'))
            except sqlite3.OperationalError:
                pass
            
            # Check for underperforming situation types
            try:
                cursor.execute("""
                    SELECT situation_type, AVG(satisfaction_estimate) as avg_sat, COUNT(*) as cnt
                    FROM conversation_outcomes
                    WHERE analyzed_at > datetime('now', '-14 days')
                    GROUP BY situation_type
                    HAVING cnt >= 3
                    ORDER BY avg_sat ASC
                    LIMIT 3
                """)
                weak_situations = cursor.fetchall()
                
                for sit_type, avg_sat, cnt in weak_situations:
                    if avg_sat < 0.45:
                        checks.append(HealthCheck(f'situation_{sit_type}', 'warning',
                                                  f'{sit_type}: avg satisfaction {avg_sat:.2f} ({cnt} convos) — consider new character',
                                                  value=avg_sat, threshold=0.45))
            except sqlite3.OperationalError:
                pass
            
            conn.close()
            
        except Exception as e:
            checks.append(HealthCheck('effectiveness', 'warning', f'Error checking effectiveness: {e}'))
        
        return checks
    
    def check_ai_budget(self) -> HealthCheck:
        """Check AI budget consumption via API"""
        try:
            r = self.session.get(f"{self.base_url}/api/admin/ai-budget/status", timeout=15)
            if r.status_code == 200:
                data = r.json()
                used = data.get('calls_today', 0)
                limit = data.get('daily_limit', 100)
                pct = (used / max(1, limit)) * 100
                
                if pct > 90:
                    return HealthCheck('ai_budget', 'critical',
                                      f'AI budget nearly exhausted: {used}/{limit} ({pct:.0f}%)',
                                      value=pct, threshold=90)
                elif pct > 70:
                    return HealthCheck('ai_budget', 'warning',
                                      f'AI budget high: {used}/{limit} ({pct:.0f}%)',
                                      value=pct, threshold=70)
                return HealthCheck('ai_budget', 'healthy',
                                  f'AI budget: {used}/{limit} ({pct:.0f}%)',
                                  value=pct)
            return HealthCheck('ai_budget', 'warning', 'Cannot access budget API')
        except Exception as e:
            return HealthCheck('ai_budget', 'warning', f'Budget check error: {e}')
    
    # ================================================================
    # FULL HEALTH REPORT
    # ================================================================
    
    def run_full_check(self, include_chat_test: bool = False) -> HealthReport:
        """Run all health checks and generate a report"""
        checks = []
        recommendations = []
        
        # 1. API Health
        api_check = self.check_api_health()
        checks.append(api_check)
        if api_check.status == 'critical':
            recommendations.append("URGENT: API is down. Check PythonAnywhere logs and reload webapp.")
        elif api_check.status == 'warning':
            recommendations.append("API is slow. Consider optimizing startup or checking server load.")
        
        # 2. Chat Endpoint (optional, costs 1 AI call)
        if include_chat_test:
            chat_check = self.check_chat_endpoint()
            checks.append(chat_check)
            if chat_check.status == 'critical':
                recommendations.append("Chat endpoint is failing. Check AI provider keys and model availability.")
        
        # 3. Database Health
        db_checks = self.check_database_health()
        checks.extend(db_checks)
        
        for c in db_checks:
            if c.status == 'critical':
                recommendations.append(f"Database issue: {c.message}")
            elif c.name == 'db_size' and c.status == 'warning':
                recommendations.append("Database is large. Run monthly cleanup task.")
        
        # 4. Character Effectiveness
        eff_checks = self.check_character_effectiveness()
        checks.extend(eff_checks)
        
        for c in eff_checks:
            if c.status == 'warning' and 'situation' in c.name:
                recommendations.append(f"Consider expanding characters for {c.message.split(':')[0]}")
        
        # 5. AI Budget
        budget_check = self.check_ai_budget()
        checks.append(budget_check)
        if budget_check.status == 'critical':
            recommendations.append("AI budget nearly exhausted. Reduce background tasks or increase limit.")
        
        # Determine overall status
        statuses = [c.status for c in checks]
        if 'critical' in statuses:
            overall = 'critical'
        elif 'warning' in statuses:
            overall = 'warning'
        else:
            overall = 'healthy'
        
        report = HealthReport(
            checks=checks,
            overall_status=overall,
            generated_at=datetime.now().isoformat(),
            recommendations=recommendations
        )
        
        self.history.append(report)
        return report
    
    def print_report(self, report: HealthReport):
        """Pretty-print a health report"""
        status_icons = {'healthy': '✅', 'warning': '⚠️', 'critical': '❌'}
        
        print(f"\n{'='*60}")
        print(f"SYSTEM HEALTH REPORT")
        print(f"Generated: {report.generated_at}")
        print(f"Overall: {status_icons.get(report.overall_status, '?')} {report.overall_status.upper()}")
        print(f"{'='*60}")
        
        for check in report.checks:
            icon = status_icons.get(check.status, '?')
            val = f" [{check.value:.1f}]" if check.value is not None else ""
            print(f"  {icon} {check.name:25s} {check.message}{val}")
        
        if report.recommendations:
            print(f"\n📋 Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        summary = report.to_dict()['summary']
        print(f"\nSummary: {summary['healthy']} healthy, {summary['warning']} warnings, {summary['critical']} critical")


# ================================================================
# CLI
# ================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='System Health Monitor')
    parser.add_argument('--url', default='http://localhost:5000')
    parser.add_argument('--production', action='store_true')
    parser.add_argument('--db', default=None, help='Path to database file')
    parser.add_argument('--chat-test', action='store_true', help='Include chat endpoint test (costs 1 AI call)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    url = 'https://trabcd.pythonanywhere.com' if args.production else args.url
    db = args.db or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                  'integrated_users.db')
    
    agent = SystemHealthAgent(url, db_path=db)
    
    # Try to authenticate for full checks
    agent.authenticate('SimUser_Alex', 'SimTest123!')
    
    report = agent.run_full_check(include_chat_test=args.chat_test)
    
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        agent.print_report(report)


if __name__ == '__main__':
    main()
