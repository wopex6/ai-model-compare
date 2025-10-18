"""
Documentation Configuration and Management
Provides configuration options and manual control for auto-documentation
"""

import os
from auto_doc_hook import auto_doc, enable_auto_docs, disable_auto_docs, update_docs_now

class DocumentationConfig:
    """Configuration manager for auto-documentation system."""
    
    def __init__(self):
        self.enabled = True
        self.update_interval = 30  # seconds
        self.monitored_extensions = ['.py', '.txt', '.md', '.env']
        self.excluded_files = ['__pycache__', '.git', 'node_modules']
        
    def enable(self):
        """Enable auto-documentation."""
        enable_auto_docs()
        self.enabled = True
        print("📚 Auto-documentation enabled")
    
    def disable(self):
        """Disable auto-documentation."""
        disable_auto_docs()
        self.enabled = False
        print("📚 Auto-documentation disabled")
    
    def update_now(self):
        """Force immediate documentation update."""
        return update_docs_now()
    
    def set_update_interval(self, seconds: int):
        """Set update check interval."""
        self.update_interval = seconds
        auto_doc.update_interval = seconds
        print(f"📚 Update interval set to {seconds} seconds")
    
    def get_status(self):
        """Get current auto-documentation status."""
        return {
            'enabled': self.enabled,
            'running': auto_doc.running,
            'update_interval': self.update_interval,
            'monitored_files': auto_doc.updater.monitored_files
        }

# Global configuration instance
doc_config = DocumentationConfig()

# Environment variable controls
if os.getenv('AUTO_DOC_INTERVAL'):
    try:
        interval = int(os.getenv('AUTO_DOC_INTERVAL'))
        doc_config.set_update_interval(interval)
    except ValueError:
        pass

if os.getenv('DISABLE_AUTO_DOCS', '').lower() in ('true', '1', 'yes'):
    doc_config.disable()
