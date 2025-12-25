"""
Background scheduler for automated greeting system

Periodically checks if greetings should be sent to users based on:
- Daily greeting schedule (at preferred time)
- Inactivity timeout (e.g., 10 minutes for development)

Author: AI Life Companion Team
Date: December 2025
"""

import threading
import time
from datetime import datetime
from integrated_database import IntegratedDatabase
from automated_greeting_system import AutomatedGreetingSystem


class GreetingScheduler:
    """
    Background scheduler that checks for greeting triggers
    """
    
    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize scheduler
        
        Args:
            check_interval_seconds: How often to check for greeting triggers (default: 60 seconds)
        """
        self.db = IntegratedDatabase()
        self.greeting_system = AutomatedGreetingSystem(self.db)
        self.check_interval = check_interval_seconds
        self.running = False
        self.thread = None
        self.last_cleanup = None
        self.cleanup_interval_hours = 6  # Run cleanup every 6 hours
    
    def _check_all_users(self):
        """Check all eligible users for greeting triggers"""
        try:
            # Get all users with eligible roles
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_role 
                FROM users 
                WHERE user_role IN ('developer', 'administrator', 'master')
                AND is_deleted = 0
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            for user_id, user_role in users:
                try:
                    # Check and send greetings for this user
                    sent_greetings = self.greeting_system.check_and_send_greetings(user_id)
                    
                    if sent_greetings:
                        print(f"✅ Sent {len(sent_greetings)} greeting(s) to user {user_id}")
                        for greeting in sent_greetings:
                            print(f"   - {greeting['type']}: {greeting['message'][:50]}...")
                
                except Exception as e:
                    print(f"❌ Error checking greetings for user {user_id}: {e}")
        
        except Exception as e:
            print(f"❌ Error in greeting scheduler: {e}")
    
    def _maybe_run_cleanup(self):
        """Run cleanup if enough time has passed since last cleanup"""
        from datetime import timedelta
        
        current_time = datetime.now()
        
        # Run cleanup if never run or if interval has passed
        if self.last_cleanup is None or \
           (current_time - self.last_cleanup) > timedelta(hours=self.cleanup_interval_hours):
            try:
                deleted = self.greeting_system.cleanup_old_greetings(days_to_keep=7)
                self.last_cleanup = current_time
                if deleted > 0:
                    print(f"🧹 Periodic cleanup: removed {deleted} old greetings")
            except Exception as e:
                print(f"❌ Error in periodic cleanup: {e}")
    
    def _run(self):
        """Main scheduler loop"""
        print(f"🚀 Greeting scheduler started (checking every {self.check_interval}s)")
        
        while self.running:
            try:
                current_time = datetime.now()
                print(f"🔍 Checking greetings at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                self._check_all_users()
                
                # Run periodic cleanup (every 6 hours)
                self._maybe_run_cleanup()
                
                # Sleep until next check
                time.sleep(self.check_interval)
            
            except Exception as e:
                print(f"❌ Error in scheduler loop: {e}")
                time.sleep(self.check_interval)
        
        print("🛑 Greeting scheduler stopped")
    
    def start(self):
        """Start the background scheduler"""
        if self.running:
            print("⚠️ Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
