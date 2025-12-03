"""
Auto-Documentation Hook
Integrates with the main application to automatically update documentation
"""

import atexit
import threading
import time
from pathlib import Path
from ai_compare.doc_updater import DocumentationUpdater

class AutoDocHook:
    """Automatic documentation update hook for the AI Model Compare system."""
    
    def __init__(self, project_root: str = ".", update_interval: int = 30):
        self.project_root = Path(project_root)
        self.update_interval = update_interval  # seconds
        self.updater = DocumentationUpdater(project_root)
        self.running = False
        self.thread = None
        
    def start_monitoring(self):
        """Start background documentation monitoring."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            
            # Register cleanup on exit
            atexit.register(self.stop_monitoring)
            
            print("[AutoDoc] Monitoring started")
    
    def stop_monitoring(self):
        """Stop background documentation monitoring."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        print("[AutoDoc] Monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                changes = self.updater.update_all_documentation()
                if any(changes.values()):
                    print("[AutoDoc] Documentation automatically updated")
            except Exception as e:
                print(f"[AutoDoc] Documentation update error: {e}")
            
            # Wait for next check
            for _ in range(self.update_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def force_update(self):
        """Force immediate documentation update."""
        try:
            changes = self.updater.update_all_documentation()
            if any(changes.values()):
                print("[AutoDoc] Documentation force-updated")
                return changes
            else:
                print("[AutoDoc] Documentation already up to date")
                return changes
        except Exception as e:
            print(f"[AutoDoc] Documentation update error: {e}")
            return {}

# Global instance for easy integration
auto_doc = AutoDocHook()

def enable_auto_docs():
    """Enable automatic documentation updates."""
    auto_doc.start_monitoring()

def disable_auto_docs():
    """Disable automatic documentation updates."""
    auto_doc.stop_monitoring()

def update_docs_now():
    """Force immediate documentation update."""
    return auto_doc.force_update()

# Auto-start when imported (can be disabled by setting environment variable)
import os
if os.getenv('DISABLE_AUTO_DOCS', '').lower() not in ('true', '1', 'yes'):
    enable_auto_docs()
