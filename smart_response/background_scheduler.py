"""
Background Task Scheduler
Runs periodic maintenance tasks:
- Pattern expansion (weekly)
- Context archival (daily)
- Confidence decay (daily)
"""

import schedule
import time
import threading
from datetime import datetime

# Handle imports for both direct execution and package import
try:
    from smart_response.pattern_expander import PatternExpander
    from smart_response.context_archival import ContextArchival
    from smart_response.ai_budget_manager import AIBudgetManager
except ModuleNotFoundError:
    from pattern_expander import PatternExpander
    from context_archival import ContextArchival
    from ai_budget_manager import AIBudgetManager


class BackgroundScheduler:
    """
    Manages background tasks for context and pattern maintenance
    Respects AI budget limits
    """
    
    def __init__(self, db_path='integrated_users.db', budget_manager=None):
        self.db_path = db_path
        self.running = False
        self.thread = None
        
        # Initialize components
        self.pattern_expander = PatternExpander(db_path)
        self.context_archival = ContextArchival(db_path)
        self.budget_manager = budget_manager  # Pass in from app.py, or None for testing
    
    def schedule_tasks(self):
        """Configure task schedule"""
        
        # Daily tasks (run at 2 AM)
        schedule.every().day.at("02:00").do(self.run_context_maintenance)
        
        # Weekly tasks (run Sunday at 3 AM)
        schedule.every().sunday.at("03:00").do(self.run_pattern_expansion)
        
        # Monthly tasks (run every 30 days at 4 AM - approximates monthly)
        schedule.every(30).days.at("04:00").do(self.run_monthly_cleanup)
        
        print("✓ Background tasks scheduled:")
        print("   - Context maintenance: Daily at 2:00 AM")
        print("   - Pattern expansion: Weekly on Sunday at 3:00 AM")
        print("   - Monthly cleanup: 1st of month at 4:00 AM")
    
    def run_context_maintenance(self):
        """Daily context maintenance"""
        print(f"\n{'='*60}")
        print(f"SCHEDULED TASK: Context Maintenance")
        print(f"Time: {datetime.now()}")
        print(f"{'='*60}")
        
        try:
            results = self.context_archival.run_maintenance(
                decay_days=30,
                archive_days=90,
                expiration_days=60
            )
            
            print(f"\n✓ Maintenance completed successfully")
            return results
            
        except Exception as e:
            print(f"\n❌ Maintenance failed: {e}")
            return None
    
    def run_pattern_expansion(self):
        """Weekly pattern expansion (uses AI - check budget)"""
        print(f"\n{'='*60}")
        print(f"SCHEDULED TASK: Pattern Expansion")
        print(f"Time: {datetime.now()}")
        print(f"{'='*60}")
        
        try:
            # Check budget first (if budget manager available)
            if self.budget_manager and not self.budget_manager.can_make_call(
                purpose='background_pattern_expansion',
                is_background=True
            ):
                print("⚠️ Skipping pattern expansion: Budget limit reached")
                return None
            
            # Run analysis
            suggestions = self.pattern_expander.analyze_recent_messages(
                days=7,
                limit=50
            )
            
            print(f"\n✓ Pattern expansion completed")
            print(f"   Suggested {len(suggestions)} new patterns")
            
            return suggestions
            
        except Exception as e:
            print(f"\n❌ Pattern expansion failed: {e}")
            return None
    
    def run_monthly_cleanup(self):
        """Monthly deep cleanup"""
        print(f"\n{'='*60}")
        print(f"SCHEDULED TASK: Monthly Cleanup")
        print(f"Time: {datetime.now()}")
        print(f"{'='*60}")
        
        try:
            # More aggressive archival for monthly cleanup
            results = self.context_archival.archive_old_context(
                archive_days=120,  # Archive anything older than 4 months
                auto_archive=True
            )
            
            print(f"\n✓ Monthly cleanup completed")
            return results
            
        except Exception as e:
            print(f"\n❌ Monthly cleanup failed: {e}")
            return None
    
    def run_manual_task(self, task_name):
        """Manually trigger a scheduled task"""
        print(f"\n🔧 Manually triggering: {task_name}")
        
        if task_name == 'context_maintenance':
            return self.run_context_maintenance()
        elif task_name == 'pattern_expansion':
            return self.run_pattern_expansion()
        elif task_name == 'monthly_cleanup':
            return self.run_monthly_cleanup()
        else:
            print(f"❌ Unknown task: {task_name}")
            return None
    
    def start(self):
        """Start the scheduler in background thread"""
        if self.running:
            print("⚠️ Scheduler already running")
            return
        
        self.running = True
        self.schedule_tasks()
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        
        print("✓ Background scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        print("✓ Background scheduler stopped")
    
    def get_next_runs(self):
        """Get next scheduled run times"""
        jobs = schedule.get_jobs()
        
        next_runs = []
        for job in jobs:
            next_runs.append({
                'task': str(job.job_func),
                'next_run': job.next_run,
                'interval': str(job.interval),
                'unit': job.unit
            })
        
        return next_runs


if __name__ == '__main__':
    """Test scheduler (for development)"""
    print("=" * 60)
    print("BACKGROUND SCHEDULER TEST")
    print("=" * 60)
    
    scheduler = BackgroundScheduler()
    
    # Show schedule
    scheduler.schedule_tasks()
    print("\nScheduled tasks:")
    for run in scheduler.get_next_runs():
        print(f"   {run['task']}: {run['next_run']}")
    
    # Test manual execution
    print("\n" + "=" * 60)
    print("MANUAL TASK EXECUTION")
    print("=" * 60)
    
    print("\n1. Running context maintenance manually...")
    scheduler.run_manual_task('context_maintenance')
    
    print("\n2. Checking if pattern expansion can run (budget)...")
    if scheduler.budget_manager:
        can_run = scheduler.budget_manager.can_make_call(
            purpose='test_pattern_expansion',
            is_background=True
        )
        print(f"   Can run: {can_run}")
        
        if can_run:
            print("\n3. Running pattern expansion manually...")
            scheduler.run_manual_task('pattern_expansion')
        else:
            print("\n3. Skipping pattern expansion (budget limit)")
    else:
        print("   Budget manager not initialized (test mode)")
        print("\n3. Skipping pattern expansion (no budget manager)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nTo run scheduler in production:")
    print("   scheduler = BackgroundScheduler()")
    print("   scheduler.start()  # Runs in background")
    print("   # ... your app runs ...")
    print("   scheduler.stop()  # When shutting down")
