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
    from smart_response.character_expansion import CharacterExpansionSystem
except ModuleNotFoundError:
    from pattern_expander import PatternExpander
    from context_archival import ContextArchival
    from ai_budget_manager import AIBudgetManager
    from character_expansion import CharacterExpansionSystem


class BackgroundScheduler:
    """
    Manages background tasks for context and pattern maintenance
    Respects AI budget limits
    """
    
    def __init__(self, db_path='integrated_users.db', budget_manager=None, 
                 character_trait_system=None):
        self.db_path = db_path
        self.running = False
        self.thread = None
        
        # Initialize components
        self.pattern_expander = PatternExpander(db_path)
        self.context_archival = ContextArchival(db_path)
        self.budget_manager = budget_manager  # Pass in from app.py, or None for testing
        self.character_trait_system = character_trait_system  # For character expansion
        self.character_expansion = None  # Lazy init when needed
    
    def schedule_tasks(self):
        """Configure task schedule"""
        
        # Daily tasks (run at 2 AM)
        schedule.every().day.at("02:00").do(self.run_context_maintenance)
        
        # Weekly tasks (run Sunday at 3 AM)
        schedule.every().sunday.at("03:00").do(self.run_pattern_expansion)
        
        # Weekly character expansion (run Wednesday at 3 AM - spread out from pattern expansion)
        schedule.every().wednesday.at("03:00").do(self.run_character_expansion)
        
        # Monthly tasks (run every 30 days at 4 AM - approximates monthly)
        schedule.every(30).days.at("04:00").do(self.run_monthly_cleanup)
        
        print("✓ Background tasks scheduled:")
        print("   - Context maintenance: Daily at 2:00 AM")
        print("   - Pattern expansion: Weekly on Sunday at 3:00 AM")
        print("   - Character expansion: Weekly on Wednesday at 3:00 AM")
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
            
            # EXPLICIT CONTEXT EXPIRATION: Expire old emotional states, goals, etc.
            try:
                from smart_response.explicit_context_handler import ExplicitContextHandler
                import sqlite3
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=5000')
                explicit_handler = ExplicitContextHandler(conn)
                expired = explicit_handler.expire_old_context()
                results['explicit_context_expired'] = expired
                conn.close()
            except Exception as e:
                print(f"⚠️ Explicit context expiration failed: {e}")
                results['explicit_context_error'] = str(e)
            
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
    
    def run_character_expansion(self):
        """Weekly character expansion - fills gaps in trait-space (uses AI - check budget)"""
        print(f"\n{'='*60}")
        print(f"SCHEDULED TASK: Character Expansion")
        print(f"Time: {datetime.now()}")
        print(f"{'='*60}")
        
        if not self.character_trait_system:
            print("⚠️ Skipping character expansion: No character_trait_system configured")
            return None
        
        try:
            # Initialize character expansion if needed
            if not self.character_expansion:
                import sqlite3
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=5000')
                self.character_expansion = CharacterExpansionSystem(conn, self.budget_manager)
            
            # Analyze gaps in trait-space
            gaps = self.character_expansion.analyze_trait_space_coverage(self.character_trait_system)
            
            if not gaps:
                print("✓ No significant gaps found in trait-space")
                return {'gaps_found': 0, 'characters_added': 0}
            
            print(f"📊 Found {len(gaps)} gaps in trait-space")
            
            # Try to fill the most severe gap (limit to 1 per run to conserve budget)
            characters_added = 0
            for gap in gaps[:1]:  # Only process top gap
                print(f"   → Gap score: {gap.gap_score:.2f}, situations: {gap.situation_types}")
                
                # Generate character (template-based, no AI cost)
                candidate = self.character_expansion.generate_character_for_gap(gap)
                
                if candidate:
                    # Add to system
                    success = self.character_expansion.add_character_to_system(
                        candidate, self.character_trait_system
                    )
                    if success:
                        characters_added += 1
            
            print(f"\n✓ Character expansion completed")
            print(f"   Gaps analyzed: {len(gaps)}")
            print(f"   Characters added: {characters_added}")
            
            return {
                'gaps_found': len(gaps),
                'characters_added': characters_added
            }
            
        except Exception as e:
            print(f"\n❌ Character expansion failed: {e}")
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
        elif task_name == 'character_expansion':
            return self.run_character_expansion()
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
