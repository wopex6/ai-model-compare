"""
Alert Notifier Agent
====================
Subscribes to Event Bus critical events and sends email/console notifications.
Prevents spam via per-topic cooldowns.

Triggers on:
  - health.critical   → AI provider down, quota exceeded
  - agent.error       → Agent failures
  - Any event with level='critical' in data

Usage:
    # Wire into app.py at startup:
    from agents.alert_notifier import AlertNotifier
    notifier = AlertNotifier(event_bus, email_service)
    notifier.start()
    
    # Standalone test:
    python agents/alert_notifier.py
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AlertNotifier:
    """Monitors Event Bus for critical events and sends notifications."""
    
    # Cooldown: don't re-alert on same topic within this window
    DEFAULT_COOLDOWN_MINUTES = 30
    
    def __init__(self, event_bus=None, email_service=None,
                 admin_email: str = None, cooldown_minutes: int = None):
        """
        Args:
            event_bus: EventBus instance to subscribe to
            email_service: EmailService instance for sending emails
            admin_email: Override recipient (default: from env ADMIN_ALERT_EMAIL or EMAIL_SENDER)
            cooldown_minutes: Min minutes between repeated alerts on same topic
        """
        self.event_bus = event_bus
        self.email_service = email_service
        self.cooldown_minutes = cooldown_minutes or self.DEFAULT_COOLDOWN_MINUTES
        
        # Resolve admin email
        self.admin_email = admin_email or os.getenv('ADMIN_ALERT_EMAIL') or os.getenv('EMAIL_SENDER')
        
        # Track last alert time per topic to enforce cooldowns
        self._last_alert: Dict[str, datetime] = {}
        self._lock = threading.Lock()
        
        # Alert history for dashboard
        self.alert_history: List[Dict] = []
        self._max_history = 200
        
        # Stats
        self.stats = {
            'alerts_received': 0,
            'emails_sent': 0,
            'emails_suppressed': 0,
            'email_failures': 0,
        }
    
    def start(self):
        """Subscribe to critical event topics on the Event Bus."""
        if not self.event_bus:
            print("[AlertNotifier] ⚠️ No Event Bus — running in log-only mode")
            return
        
        # Subscribe to critical topics
        self.event_bus.subscribe('health.critical', self._on_critical, name='alert_notifier_health')
        self.event_bus.subscribe('health.warning', self._on_warning, name='alert_notifier_warning')
        self.event_bus.subscribe('agent.error', self._on_critical, name='alert_notifier_agent')
        self.event_bus.subscribe('agent.rate_limited', self._on_warning, name='alert_notifier_ratelimit')
        
        print(f"[AlertNotifier] ✅ Listening for critical events"
              f" (email: {self.admin_email or 'not configured'},"
              f" cooldown: {self.cooldown_minutes}min)")
    
    def _on_critical(self, event):
        """Handle critical events — always attempt email notification."""
        self.stats['alerts_received'] += 1
        
        alert_key = f"{event.topic}:{event.data.get('provider', 'system')}"
        alert_msg = event.data.get('alert') or event.data.get('message') or str(event.data)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'level': 'critical',
            'topic': event.topic,
            'message': alert_msg,
            'source': event.source,
            'data': event.data,
        }
        self._store_alert(record)
        
        # Console alert (always)
        print(f"\n🚨 [CRITICAL ALERT] {alert_msg}")
        print(f"   Source: {event.source} | Topic: {event.topic}")
        
        # Email alert (with cooldown)
        self._send_alert_email(alert_key, 'CRITICAL', alert_msg, event)
    
    def _on_warning(self, event):
        """Handle warning events — log, email only for repeated warnings."""
        self.stats['alerts_received'] += 1
        
        alert_msg = event.data.get('alert') or event.data.get('message') or str(event.data)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'level': 'warning',
            'topic': event.topic,
            'message': alert_msg,
            'source': event.source,
            'data': event.data,
        }
        self._store_alert(record)
        
        print(f"⚠️ [WARNING] {alert_msg} (source: {event.source})")
    
    def _send_alert_email(self, alert_key: str, level: str, message: str, event):
        """Send email if not in cooldown window."""
        if not self.email_service or not self.admin_email:
            return
        
        # Check cooldown
        with self._lock:
            last = self._last_alert.get(alert_key)
            now = datetime.now()
            
            if last and (now - last) < timedelta(minutes=self.cooldown_minutes):
                self.stats['emails_suppressed'] += 1
                remaining = self.cooldown_minutes - int((now - last).total_seconds() / 60)
                print(f"   📧 Email suppressed (cooldown: {remaining}min remaining)")
                return
            
            self._last_alert[alert_key] = now
        
        # Build and send email
        try:
            subject = f"[AI ChatChat {level}] {message[:80]}"
            
            provider = event.data.get('provider', 'N/A')
            source = event.source or 'unknown'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <div style="background: {'#dc3545' if level == 'CRITICAL' else '#ffc107'}; 
                              padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h2 style="color: white; margin: 0;">
                      {'🚨' if level == 'CRITICAL' else '⚠️'} AI ChatChat — {level} Alert
                    </h2>
                  </div>
                  
                  <div style="background: #f8f9fa; padding: 25px; border-radius: 0 0 10px 10px;">
                    <table style="width: 100%; border-collapse: collapse;">
                      <tr>
                        <td style="padding: 8px; font-weight: bold; width: 120px;">Alert:</td>
                        <td style="padding: 8px; color: #dc3545; font-weight: bold;">{message}</td>
                      </tr>
                      <tr>
                        <td style="padding: 8px; font-weight: bold;">Provider:</td>
                        <td style="padding: 8px;">{provider}</td>
                      </tr>
                      <tr>
                        <td style="padding: 8px; font-weight: bold;">Source:</td>
                        <td style="padding: 8px;">{source}</td>
                      </tr>
                      <tr>
                        <td style="padding: 8px; font-weight: bold;">Time:</td>
                        <td style="padding: 8px;">{timestamp}</td>
                      </tr>
                      <tr>
                        <td style="padding: 8px; font-weight: bold;">Topic:</td>
                        <td style="padding: 8px;">{event.topic}</td>
                      </tr>
                    </table>
                    
                    <div style="margin-top: 20px; padding: 15px; background: white; 
                                border-radius: 8px; border-left: 4px solid #dc3545;">
                      <strong>Action Required:</strong>
                      <p style="margin: 5px 0 0 0;">
                        {self._get_action_text(event)}
                      </p>
                    </div>
                    
                    <p style="margin-top: 20px; color: #888; font-size: 12px;">
                      This alert will not repeat for {self.cooldown_minutes} minutes.
                      Check status: <a href="https://trabcd.pythonanywhere.com/api/admin/ai-quota-status">Quota Status API</a>
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            text = (
                f"AI ChatChat — {level} Alert\n"
                f"{'='*40}\n"
                f"Alert:    {message}\n"
                f"Provider: {provider}\n"
                f"Source:   {source}\n"
                f"Time:     {timestamp}\n\n"
                f"Action: {self._get_action_text(event)}\n"
            )
            
            self._send_email(subject, html, text)
            self.stats['emails_sent'] += 1
            print(f"   📧 Alert email sent to {self.admin_email}")
            
        except Exception as e:
            self.stats['email_failures'] += 1
            print(f"   📧 Email failed: {e}")
    
    def _get_action_text(self, event) -> str:
        """Generate action-required text based on event type."""
        data = event.data
        provider = data.get('provider', '').lower()
        
        if 'quota' in str(data).lower():
            return (
                f"The {provider.upper() or 'AI'} API has exceeded its quota. "
                f"Please top up credits at the provider's dashboard to restore service."
            )
        elif 'budget' in str(data).lower():
            return (
                "Daily AI budget is nearly exhausted. "
                "Consider increasing the budget limit in admin settings."
            )
        elif event.topic == 'agent.error':
            return "An agent encountered an error. Check the orchestrator logs for details."
        else:
            return "Please investigate and take corrective action."
    
    def _send_email(self, subject: str, html: str, text: str):
        """Send email using the email service's SMTP configuration."""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import smtplib
        
        es = self.email_service
        if not es.sender_email or not es.sender_password:
            print("   📧 Email credentials not configured")
            return
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = es.sender_email
        message["To"] = self.admin_email
        
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))
        
        with smtplib.SMTP(es.smtp_server, es.smtp_port) as server:
            server.starttls()
            server.login(es.sender_email, es.sender_password)
            server.sendmail(es.sender_email, self.admin_email, message.as_string())
    
    def _store_alert(self, record: Dict):
        """Store alert in history for dashboard access."""
        self.alert_history.append(record)
        if len(self.alert_history) > self._max_history:
            self.alert_history = self.alert_history[-self._max_history:]
    
    def get_recent_alerts(self, limit: int = 50, level: str = None) -> List[Dict]:
        """Get recent alerts, optionally filtered by level."""
        alerts = self.alert_history
        if level:
            alerts = [a for a in alerts if a['level'] == level]
        return alerts[-limit:]
    
    def get_stats(self) -> Dict:
        """Get notifier statistics."""
        return {
            **self.stats,
            'admin_email': self.admin_email or 'not configured',
            'cooldown_minutes': self.cooldown_minutes,
            'active_cooldowns': len(self._last_alert),
            'alert_history_size': len(self.alert_history),
        }
    
    # --- Manual alert (for testing or direct use) ---
    
    def send_test_alert(self):
        """Send a test alert email to verify configuration."""
        if not self.email_service or not self.admin_email:
            print("❌ Cannot send test: email_service or admin_email not configured")
            return False
        
        try:
            subject = "[AI ChatChat TEST] Alert system verification"
            html = """
            <html><body style="font-family: Arial; text-align: center; padding: 40px;">
              <h2>✅ Alert System Working</h2>
              <p>This is a test alert from AI ChatChat.</p>
              <p>You will receive emails when AI providers run out of quota or critical errors occur.</p>
            </body></html>
            """
            text = "AI ChatChat Alert Test\nThis confirms the alert system is working.\n"
            
            self._send_email(subject, html, text)
            print(f"✅ Test alert sent to {self.admin_email}")
            return True
        except Exception as e:
            print(f"❌ Test alert failed: {e}")
            return False


# ================================================================
# CLI
# ================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Alert Notifier Agent')
    parser.add_argument('--test', action='store_true', help='Send test alert email')
    parser.add_argument('--email', type=str, help='Override recipient email')
    args = parser.parse_args()
    
    from email_service import EmailService
    
    es = EmailService()
    notifier = AlertNotifier(email_service=es, admin_email=args.email)
    
    if args.test:
        notifier.send_test_alert()
    else:
        print("Alert Notifier Agent")
        print(f"  Admin email: {notifier.admin_email or 'NOT SET'}")
        print(f"  Cooldown:    {notifier.cooldown_minutes} min")
        print(f"\nTo test: python agents/alert_notifier.py --test")
        print(f"Set ADMIN_ALERT_EMAIL in .env to configure recipient")
