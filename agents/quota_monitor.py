"""
AI Model Quota Monitor

Monitors AI provider quota status and alerts when models run out of credits.
Checks:
- Provider error logs for 429/quota errors
- Provider health status (consecutive failures)
- Budget consumption rate
- Estimated time until quota exhaustion

Alerts are printed to console and optionally published to Event Bus.
"""

import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ProviderQuotaStatus:
    """Quota status for a single AI provider"""
    provider: str
    healthy: bool
    available: bool
    consecutive_failures: int = 0
    quota_errors_24h: int = 0
    total_errors_24h: int = 0
    last_error_time: Optional[str] = None
    last_error_message: Optional[str] = None
    estimated_calls_remaining: Optional[int] = None
    status: str = 'unknown'  # 'ok', 'warning', 'quota_exceeded', 'down', 'unknown'
    
    def __post_init__(self):
        if not self.available:
            self.status = 'not_configured'
        elif self.quota_errors_24h > 0:
            self.status = 'quota_exceeded'
        elif self.consecutive_failures >= 3:
            self.status = 'down'
        elif self.total_errors_24h > 5:
            self.status = 'warning'
        elif self.healthy:
            self.status = 'ok'


@dataclass 
class QuotaReport:
    """Full quota monitoring report"""
    providers: List[ProviderQuotaStatus]
    budget_used_today: int = 0
    budget_limit: int = 0
    budget_percentage: float = 0.0
    alerts: List[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def has_critical_alerts(self) -> bool:
        return any('CRITICAL' in a or 'QUOTA EXCEEDED' in a for a in self.alerts)
    
    def to_dict(self) -> Dict:
        return {
            'checked_at': self.checked_at,
            'providers': [
                {
                    'provider': p.provider,
                    'status': p.status,
                    'healthy': p.healthy,
                    'available': p.available,
                    'consecutive_failures': p.consecutive_failures,
                    'quota_errors_24h': p.quota_errors_24h,
                    'total_errors_24h': p.total_errors_24h,
                    'last_error_time': p.last_error_time,
                    'last_error_message': p.last_error_message,
                }
                for p in self.providers
            ],
            'budget': {
                'used_today': self.budget_used_today,
                'limit': self.budget_limit,
                'percentage': round(self.budget_percentage, 1),
            },
            'alerts': self.alerts,
            'has_critical': self.has_critical_alerts(),
        }


class QuotaMonitor:
    """Monitors AI model quota and alerts on issues"""
    
    def __init__(self, db_path: str = None, base_url: str = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'integrated_users.db'
        )
        self.base_url = base_url
        self.event_bus = None
        
        # Try to import event bus
        try:
            from agents.event_bus import EventBus, Topics
            self.Topics = Topics
        except ImportError:
            self.Topics = None
    
    def set_event_bus(self, bus):
        """Attach event bus for publishing alerts"""
        self.event_bus = bus
    
    def check_provider_errors(self) -> List[ProviderQuotaStatus]:
        """Check AI provider error logs in the database"""
        providers = []
        known_providers = ['openai', 'anthropic', 'google', 'grok']
        
        if not os.path.exists(self.db_path):
            return [ProviderQuotaStatus(p, False, False, status='db_unavailable') 
                    for p in known_providers]
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Check if error table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ai_provider_errors'
            """)
            if not cursor.fetchone():
                conn.close()
                return [ProviderQuotaStatus(p, True, True, status='no_error_data') 
                        for p in known_providers]
            
            for provider in known_providers:
                # Count quota errors in last 24h
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_provider_errors
                    WHERE provider = ? AND error_type = 'quota_exceeded'
                    AND timestamp > datetime('now', '-1 day')
                """, (provider,))
                quota_errors = cursor.fetchone()[0]
                
                # Count total errors in last 24h
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_provider_errors
                    WHERE provider = ? AND timestamp > datetime('now', '-1 day')
                """, (provider,))
                total_errors = cursor.fetchone()[0]
                
                # Get most recent error
                cursor.execute("""
                    SELECT timestamp, error_message, error_type FROM ai_provider_errors
                    WHERE provider = ?
                    ORDER BY timestamp DESC LIMIT 1
                """, (provider,))
                last_err = cursor.fetchone()
                
                # Count consecutive recent failures (no successes between them)
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_provider_errors
                    WHERE provider = ? AND resolved = 0
                    AND timestamp > datetime('now', '-1 hour')
                """, (provider,))
                recent_failures = cursor.fetchone()[0]
                
                status = ProviderQuotaStatus(
                    provider=provider,
                    healthy=quota_errors == 0 and recent_failures < 3,
                    available=True,  # We know it was configured if there are errors
                    consecutive_failures=recent_failures,
                    quota_errors_24h=quota_errors,
                    total_errors_24h=total_errors,
                    last_error_time=last_err[0] if last_err else None,
                    last_error_message=last_err[1][:200] if last_err else None,
                )
                providers.append(status)
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error checking provider errors: {e}")
            providers = [ProviderQuotaStatus(p, False, False, status='error') 
                        for p in known_providers]
        
        return providers
    
    def check_budget(self) -> Dict:
        """Check AI budget consumption"""
        budget_info = {'used_today': 0, 'limit': 0, 'percentage': 0.0}
        
        if not os.path.exists(self.db_path):
            return budget_info
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Check ai_budget_log table
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ai_budget_log'
            """)
            if cursor.fetchone():
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_budget_log
                    WHERE date(timestamp) = date('now')
                """)
                budget_info['used_today'] = cursor.fetchone()[0]
            
            # Check budget settings (key-value table)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ai_budget_settings'
            """)
            if cursor.fetchone():
                cursor.execute(
                    "SELECT value FROM ai_budget_settings WHERE key = 'daily_limit'"
                )
                row = cursor.fetchone()
                if row:
                    try:
                        budget_info['limit'] = int(row[0])
                        budget_info['percentage'] = (
                            budget_info['used_today'] / max(1, int(row[0])) * 100
                        )
                    except (ValueError, TypeError):
                        pass
            
            conn.close()
        except Exception as e:
            print(f"⚠️ Error checking budget: {e}")
        
        return budget_info
    
    def check_via_api(self, session: requests.Session = None) -> Optional[Dict]:
        """Check provider status via the API (if base_url configured)"""
        if not self.base_url:
            return None
        
        s = session or requests.Session()
        try:
            r = s.get(f"{self.base_url}/api/admin/ai-provider-status", timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None
    
    def run_check(self) -> QuotaReport:
        """Run a full quota check and generate alerts"""
        providers = self.check_provider_errors()
        budget = self.check_budget()
        alerts = []
        
        # Check each provider
        for p in providers:
            if p.status == 'quota_exceeded':
                alert = f"🚨 QUOTA EXCEEDED: {p.provider.upper()} — {p.quota_errors_24h} quota errors in 24h"
                if p.last_error_message:
                    alert += f"\n   Last error: {p.last_error_message[:150]}"
                alerts.append(alert)
            elif p.status == 'down':
                alerts.append(
                    f"❌ CRITICAL: {p.provider.upper()} is DOWN — "
                    f"{p.consecutive_failures} consecutive failures"
                )
            elif p.status == 'warning':
                alerts.append(
                    f"⚠️ WARNING: {p.provider.upper()} — "
                    f"{p.total_errors_24h} errors in 24h"
                )
        
        # Budget alerts
        if budget['percentage'] > 90:
            alerts.append(
                f"🚨 BUDGET CRITICAL: {budget['used_today']}/{budget['limit']} "
                f"AI calls today ({budget['percentage']:.0f}%)"
            )
        elif budget['percentage'] > 70:
            alerts.append(
                f"⚠️ BUDGET HIGH: {budget['used_today']}/{budget['limit']} "
                f"AI calls today ({budget['percentage']:.0f}%)"
            )
        
        # All providers down?
        available_providers = [p for p in providers if p.available and p.status not in ('quota_exceeded', 'down')]
        if not available_providers and any(p.available for p in providers):
            alerts.append("🚨🚨 ALL AI PROVIDERS ARE DOWN OR OUT OF QUOTA — SYSTEM CANNOT GENERATE RESPONSES")
        
        report = QuotaReport(
            providers=providers,
            budget_used_today=budget['used_today'],
            budget_limit=budget['limit'],
            budget_percentage=budget['percentage'],
            alerts=alerts,
        )
        
        # Publish alerts to event bus if available
        if self.event_bus and alerts:
            for alert in alerts:
                if 'CRITICAL' in alert or 'QUOTA EXCEEDED' in alert or 'ALL AI PROVIDERS' in alert:
                    topic = self.Topics.HEALTH_CRITICAL if self.Topics else 'health.critical'
                else:
                    topic = self.Topics.HEALTH_WARNING if self.Topics else 'health.warning'
                
                self.event_bus.publish(topic, {
                    'alert': alert,
                    'report': report.to_dict()
                }, source='quota_monitor')
        
        return report
    
    def print_report(self, report: QuotaReport):
        """Pretty-print a quota report"""
        status_icons = {
            'ok': '✅', 'warning': '⚠️', 'quota_exceeded': '🚨',
            'down': '❌', 'not_configured': '⬜', 'unknown': '❓',
            'no_error_data': '✅', 'db_unavailable': '❓', 'error': '❓'
        }
        
        print(f"\n{'='*60}")
        print(f"AI MODEL QUOTA MONITOR")
        print(f"Checked: {report.checked_at}")
        print(f"{'='*60}")
        
        print(f"\n  Provider Status:")
        for p in report.providers:
            icon = status_icons.get(p.status, '❓')
            err_info = f" | {p.total_errors_24h} errors 24h" if p.total_errors_24h > 0 else ""
            quota_info = f" | {p.quota_errors_24h} QUOTA ERRORS" if p.quota_errors_24h > 0 else ""
            print(f"    {icon} {p.provider:12s} {p.status:18s}{err_info}{quota_info}")
            if p.last_error_message and p.status in ('quota_exceeded', 'down', 'warning'):
                print(f"       └─ {p.last_error_message[:80]}")
        
        print(f"\n  AI Budget:")
        pct = report.budget_percentage
        bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
        print(f"    [{bar}] {pct:.0f}% ({report.budget_used_today}/{report.budget_limit})")
        
        if report.alerts:
            print(f"\n  🔔 ALERTS ({len(report.alerts)}):")
            for alert in report.alerts:
                print(f"    {alert}")
        else:
            print(f"\n  ✅ No alerts — all providers operating normally")
        
        return report.has_critical_alerts()


# ================================================================
# CLI
# ================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI Model Quota Monitor')
    parser.add_argument('--db', default=None, help='Database path')
    parser.add_argument('--url', default=None, help='API base URL')
    parser.add_argument('--production', action='store_true')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--watch', type=int, default=0, 
                       help='Watch mode: check every N seconds')
    
    args = parser.parse_args()
    
    db = args.db or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'integrated_users.db'
    )
    url = 'https://trabcd.pythonanywhere.com' if args.production else args.url
    
    monitor = QuotaMonitor(db_path=db, base_url=url)
    
    if args.watch > 0:
        import time
        print(f"Watching quota status every {args.watch}s (Ctrl+C to stop)...")
        try:
            while True:
                report = monitor.run_check()
                if args.json:
                    print(json.dumps(report.to_dict(), indent=2))
                else:
                    monitor.print_report(report)
                
                if report.has_critical_alerts():
                    print("\n  ⚡ CRITICAL ALERT — Please top up AI provider credits!")
                
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        report = monitor.run_check()
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            has_critical = monitor.print_report(report)
            if has_critical:
                print("\n  ⚡ ACTION REQUIRED: Top up AI provider credits!")
                return 1
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
