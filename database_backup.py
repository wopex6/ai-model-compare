"""
Database Backup System
======================
Automated and manual backup system for all project databases.

Features:
- Automatic backups on app startup
- Scheduled periodic backups (configurable interval)
- Manual backup via API endpoint
- Backup rotation (keeps last N backups per database)
- Restore capability
- Backup verification (integrity check)

Usage:
    from database_backup import BackupManager
    backup_mgr = BackupManager()
    backup_mgr.backup_all()  # Manual backup
    backup_mgr.start_scheduler()  # Start automatic backups
"""

import os
import shutil
import sqlite3
import hashlib
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class BackupManager:
    """
    Manages database backups with automatic scheduling and rotation.
    Auto-discovers all .db files in project - no manual updates needed.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'backup_dir': 'backups',
        'max_backups_per_db': 30,  # Keep last 30 backups per database
        'backup_interval_hours': 4,  # Backup every 4 hours
        'backup_on_startup': True,
        'verify_backups': True,
        'compress_backups': False,  # SQLite files compress well but adds complexity
    }
    
    # Patterns to EXCLUDE from backup (temp files, test dbs, backups themselves)
    EXCLUDE_PATTERNS = [
        'backups/',        # Don't backup backups
        'test_',           # Test databases
        'temp_',           # Temporary databases
        '__pycache__/',    # Python cache
        '.git/',           # Git directory
        'node_modules/',   # Node modules
        'venv/',           # Virtual environment
        '.bak',            # Backup files
    ]
    
    def __init__(self, project_root: str = None, config: Dict = None):
        """
        Initialize backup manager.
        
        Args:
            project_root: Root directory of the project (default: current directory)
            config: Override default configuration
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.backup_dir = self.project_root / self.config['backup_dir']
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Scheduler state
        self._scheduler_thread = None
        self._scheduler_running = False
        
        # Backup log
        self.log_file = self.backup_dir / 'backup_log.json'
        self._load_log()
        
        print(f"✓ BackupManager initialized")
        print(f"  Backup directory: {self.backup_dir}")
        print(f"  Max backups per DB: {self.config['max_backups_per_db']}")
        print(f"  Backup interval: {self.config['backup_interval_hours']} hours")
    
    def _load_log(self):
        """Load backup log from file."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.log = json.load(f)
            except:
                self.log = {'backups': [], 'restores': [], 'errors': []}
        else:
            self.log = {'backups': [], 'restores': [], 'errors': []}
    
    def _save_log(self):
        """Save backup log to file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.log, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Could not save backup log: {e}")
    
    def discover_databases(self) -> List[str]:
        """
        Auto-discover all .db files in project directory.
        Excludes files matching EXCLUDE_PATTERNS.
        
        Returns:
            List of database paths relative to project root
        """
        databases = []
        
        # Search for all .db files recursively
        for db_file in self.project_root.rglob('*.db'):
            # Get relative path
            try:
                rel_path = db_file.relative_to(self.project_root)
                # Normalize to forward slashes for consistent pattern matching
                rel_path_str = str(rel_path).replace('\\', '/')
                
                # Check exclusion patterns
                excluded = False
                for pattern in self.EXCLUDE_PATTERNS:
                    # Normalize pattern too
                    norm_pattern = pattern.replace('\\', '/')
                    if norm_pattern in rel_path_str or rel_path_str.startswith(norm_pattern):
                        excluded = True
                        break
                
                if not excluded:
                    # Return original path format for the OS
                    databases.append(str(rel_path))
                    
            except ValueError:
                # File is not under project root
                continue
        
        # Sort for consistent ordering
        databases.sort()
        return databases
    
    def _get_db_hash(self, db_path: Path) -> str:
        """Calculate MD5 hash of database file for integrity verification."""
        if not db_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(db_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _verify_sqlite_integrity(self, db_path: Path) -> Tuple[bool, str]:
        """Verify SQLite database integrity."""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            
            if result == "ok":
                return True, "Integrity check passed"
            else:
                return False, f"Integrity check failed: {result}"
        except Exception as e:
            return False, f"Could not verify: {e}"
    
    def _get_backup_filename(self, db_name: str, timestamp: datetime = None) -> str:
        """Generate backup filename with timestamp."""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Sanitize db name (replace path separators)
        safe_name = db_name.replace('/', '_').replace('\\', '_')
        ts = timestamp.strftime('%Y%m%d_%H%M%S')
        return f"{safe_name}.{ts}.bak"
    
    def backup_database(self, db_name: str, reason: str = "manual") -> Dict:
        """
        Backup a single database.
        
        Args:
            db_name: Database filename (relative to project root)
            reason: Reason for backup (startup, scheduled, manual, pre-restore)
            
        Returns:
            Dict with backup result info
        """
        db_path = self.project_root / db_name
        
        result = {
            'database': db_name,
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'success': False,
            'backup_file': None,
            'size_bytes': 0,
            'hash': None,
            'error': None
        }
        
        # Check if database exists
        if not db_path.exists():
            result['error'] = f"Database not found: {db_path}"
            print(f"⚠️ {result['error']}")
            return result
        
        try:
            # Create backup subdirectory for this database
            safe_name = db_name.replace('/', '_').replace('\\', '_')
            db_backup_dir = self.backup_dir / safe_name
            db_backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup filename
            backup_filename = self._get_backup_filename(db_name)
            backup_path = db_backup_dir / backup_filename
            
            # Use SQLite backup API for safe hot backup
            source_conn = sqlite3.connect(str(db_path))
            backup_conn = sqlite3.connect(str(backup_path))
            
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Verify backup
            if self.config['verify_backups']:
                is_valid, msg = self._verify_sqlite_integrity(backup_path)
                if not is_valid:
                    result['error'] = f"Backup verification failed: {msg}"
                    backup_path.unlink()  # Remove invalid backup
                    return result
            
            # Get backup info
            result['success'] = True
            result['backup_file'] = str(backup_path.relative_to(self.project_root))
            result['size_bytes'] = backup_path.stat().st_size
            result['hash'] = self._get_db_hash(backup_path)
            
            print(f"✓ Backed up {db_name} ({result['size_bytes']:,} bytes)")
            
            # Rotate old backups
            self._rotate_backups(db_backup_dir)
            
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ Backup failed for {db_name}: {e}")
        
        # Log the backup
        self.log['backups'].append(result)
        self._save_log()
        
        return result
    
    def _rotate_backups(self, backup_dir: Path):
        """Remove old backups beyond retention limit."""
        max_backups = self.config['max_backups_per_db']
        
        # Get all backup files sorted by modification time (newest first)
        backups = sorted(
            backup_dir.glob("*.bak"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Remove excess backups
        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
                print(f"  ↻ Rotated old backup: {old_backup.name}")
            except Exception as e:
                print(f"  ⚠️ Could not remove old backup {old_backup.name}: {e}")
    
    def backup_all(self, reason: str = "manual") -> List[Dict]:
        """
        Backup all auto-discovered databases.
        
        Args:
            reason: Reason for backup
            
        Returns:
            List of backup results
        """
        # Auto-discover databases each time (picks up new ones automatically)
        databases = self.discover_databases()
        
        print(f"\n{'='*50}")
        print(f"📦 Starting backup of all databases ({reason})")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Discovered {len(databases)} databases")
        print(f"{'='*50}")
        
        results = []
        success_count = 0
        
        for db_name in databases:
            result = self.backup_database(db_name, reason)
            results.append(result)
            if result['success']:
                success_count += 1
        
        print(f"\n✓ Backup complete: {success_count}/{len(databases)} databases backed up")
        return results
    
    def list_backups(self, db_name: str = None) -> List[Dict]:
        """
        List available backups.
        
        Args:
            db_name: Specific database to list backups for (None = all)
            
        Returns:
            List of backup info dicts
        """
        backups = []
        
        if db_name:
            safe_name = db_name.replace('/', '_').replace('\\', '_')
            dirs_to_check = [self.backup_dir / safe_name]
        else:
            dirs_to_check = [d for d in self.backup_dir.iterdir() if d.is_dir()]
        
        for backup_dir in dirs_to_check:
            if not backup_dir.exists():
                continue
                
            for backup_file in sorted(backup_dir.glob("*.bak"), reverse=True):
                # Parse timestamp from filename
                parts = backup_file.stem.split('.')
                if len(parts) >= 2:
                    timestamp_str = parts[-1]
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    except:
                        timestamp = None
                else:
                    timestamp = None
                
                backups.append({
                    'database': backup_dir.name,
                    'filename': backup_file.name,
                    'path': str(backup_file.relative_to(self.project_root)),
                    'size_bytes': backup_file.stat().st_size,
                    'timestamp': timestamp.isoformat() if timestamp else None,
                    'age_hours': (datetime.now() - timestamp).total_seconds() / 3600 if timestamp else None
                })
        
        return backups
    
    def restore_database(self, db_name: str, backup_filename: str = None, 
                         create_pre_restore_backup: bool = True) -> Dict:
        """
        Restore a database from backup.
        
        Args:
            db_name: Database to restore
            backup_filename: Specific backup file to restore (None = latest)
            create_pre_restore_backup: Create backup before restoring
            
        Returns:
            Dict with restore result
        """
        result = {
            'database': db_name,
            'timestamp': datetime.now().isoformat(),
            'backup_file': backup_filename,
            'success': False,
            'pre_restore_backup': None,
            'error': None
        }
        
        # Find backup file
        safe_name = db_name.replace('/', '_').replace('\\', '_')
        db_backup_dir = self.backup_dir / safe_name
        
        if not db_backup_dir.exists():
            result['error'] = f"No backups found for {db_name}"
            return result
        
        if backup_filename:
            backup_path = db_backup_dir / backup_filename
            if not backup_path.exists():
                result['error'] = f"Backup file not found: {backup_filename}"
                return result
        else:
            # Get latest backup
            backups = sorted(db_backup_dir.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not backups:
                result['error'] = f"No backups found for {db_name}"
                return result
            backup_path = backups[0]
            result['backup_file'] = backup_path.name
        
        # Verify backup integrity before restore
        is_valid, msg = self._verify_sqlite_integrity(backup_path)
        if not is_valid:
            result['error'] = f"Backup file is corrupted: {msg}"
            return result
        
        db_path = self.project_root / db_name
        
        try:
            # Create pre-restore backup
            if create_pre_restore_backup and db_path.exists():
                pre_backup = self.backup_database(db_name, reason="pre-restore")
                result['pre_restore_backup'] = pre_backup.get('backup_file')
                print(f"✓ Created pre-restore backup")
            
            # Restore using SQLite backup API
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Ensure target directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            target_conn = sqlite3.connect(str(db_path))
            
            with target_conn:
                backup_conn.backup(target_conn)
            
            backup_conn.close()
            target_conn.close()
            
            # Verify restored database
            is_valid, msg = self._verify_sqlite_integrity(db_path)
            if not is_valid:
                result['error'] = f"Restored database verification failed: {msg}"
                return result
            
            result['success'] = True
            print(f"✓ Restored {db_name} from {result['backup_file']}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ Restore failed for {db_name}: {e}")
        
        # Log the restore
        self.log['restores'].append(result)
        self._save_log()
        
        return result
    
    def get_backup_status(self) -> Dict:
        """
        Get overall backup status.
        
        Returns:
            Dict with status information
        """
        status = {
            'backup_dir': str(self.backup_dir),
            'databases': {},
            'total_backup_size_mb': 0,
            'last_backup': None,
            'scheduler_running': self._scheduler_running
        }
        
        total_size = 0
        latest_backup_time = None
        
        # Auto-discover databases for status
        databases = self.discover_databases()
        
        for db_name in databases:
            safe_name = db_name.replace('/', '_').replace('\\', '_')
            db_backup_dir = self.backup_dir / safe_name
            
            db_status = {
                'backup_count': 0,
                'latest_backup': None,
                'latest_backup_age_hours': None,
                'total_size_mb': 0
            }
            
            if db_backup_dir.exists():
                backups = sorted(db_backup_dir.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
                db_status['backup_count'] = len(backups)
                
                if backups:
                    latest = backups[0]
                    latest_time = datetime.fromtimestamp(latest.stat().st_mtime)
                    db_status['latest_backup'] = latest.name
                    db_status['latest_backup_age_hours'] = round((datetime.now() - latest_time).total_seconds() / 3600, 1)
                    
                    if latest_backup_time is None or latest_time > latest_backup_time:
                        latest_backup_time = latest_time
                
                size = sum(f.stat().st_size for f in backups)
                db_status['total_size_mb'] = round(size / (1024 * 1024), 2)
                total_size += size
            
            status['databases'][db_name] = db_status
        
        status['total_backup_size_mb'] = round(total_size / (1024 * 1024), 2)
        status['last_backup'] = latest_backup_time.isoformat() if latest_backup_time else None
        
        return status
    
    # ==================== SCHEDULER ====================
    
    def _scheduler_loop(self):
        """Background scheduler loop for automatic backups."""
        interval_seconds = self.config['backup_interval_hours'] * 3600
        
        while self._scheduler_running:
            try:
                # Wait for interval (check every minute if we should stop)
                for _ in range(int(interval_seconds / 60)):
                    if not self._scheduler_running:
                        break
                    time.sleep(60)
                
                if self._scheduler_running:
                    self.backup_all(reason="scheduled")
                    
            except Exception as e:
                error = {
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'context': 'scheduler'
                }
                self.log['errors'].append(error)
                self._save_log()
                print(f"⚠️ Scheduler error: {e}")
    
    def start_scheduler(self):
        """Start the automatic backup scheduler."""
        if self._scheduler_running:
            print("⚠️ Scheduler already running")
            return
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        print(f"✓ Backup scheduler started (every {self.config['backup_interval_hours']} hours)")
    
    def stop_scheduler(self):
        """Stop the automatic backup scheduler."""
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        print("✓ Backup scheduler stopped")


# ==================== STANDALONE USAGE ====================

if __name__ == '__main__':
    import sys
    
    backup_mgr = BackupManager()
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python database_backup.py backup     - Backup all databases")
        print("  python database_backup.py status     - Show backup status")
        print("  python database_backup.py list       - List all backups")
        print("  python database_backup.py restore <db_name> [backup_file]")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == 'backup':
        backup_mgr.backup_all(reason="manual")
        
    elif command == 'status':
        status = backup_mgr.get_backup_status()
        print("\n📊 Backup Status")
        print(f"   Backup directory: {status['backup_dir']}")
        print(f"   Total backup size: {status['total_backup_size_mb']} MB")
        print(f"   Last backup: {status['last_backup']}")
        print("\n   Databases:")
        for db, info in status['databases'].items():
            age = info['latest_backup_age_hours']
            age_str = f"{age}h ago" if age else "never"
            print(f"     {db}: {info['backup_count']} backups, latest: {age_str}")
            
    elif command == 'list':
        backups = backup_mgr.list_backups()
        print(f"\n📋 Available Backups ({len(backups)} total)")
        for b in backups[:20]:  # Show first 20
            age = f"{b['age_hours']:.1f}h ago" if b['age_hours'] else "unknown"
            size = f"{b['size_bytes']/1024/1024:.2f} MB"
            print(f"   {b['database']}/{b['filename']} ({size}, {age})")
        if len(backups) > 20:
            print(f"   ... and {len(backups) - 20} more")
            
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Usage: python database_backup.py restore <db_name> [backup_file]")
            sys.exit(1)
        
        db_name = sys.argv[2]
        backup_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        print(f"\n⚠️  WARNING: This will restore {db_name}")
        if backup_file:
            print(f"   From backup: {backup_file}")
        else:
            print(f"   From latest backup")
        
        confirm = input("\nType 'RESTORE' to confirm: ")
        if confirm == 'RESTORE':
            result = backup_mgr.restore_database(db_name, backup_file)
            if result['success']:
                print(f"\n✅ Restore completed successfully")
            else:
                print(f"\n❌ Restore failed: {result['error']}")
        else:
            print("Restore cancelled")
    
    else:
        print(f"Unknown command: {command}")
