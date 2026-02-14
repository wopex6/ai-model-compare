"""
Data Cleanup Module
Handles automatic cleanup of expired data based on retention settings.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from pathlib import Path


class DataCleanupManager:
    """Manages automatic cleanup of expired interpretation data"""
    
    def __init__(self, users_db_path: str = None, smart_response_db_path: str = None):
        base_path = Path(__file__).parent.parent
        self.users_db_path = users_db_path or str(base_path / 'integrated_users.db')
        self.smart_response_db_path = smart_response_db_path or str(base_path / 'smart_response.db')
    
    def _get_setting(self, key: str, default):
        """Get a setting from admin_settings table"""
        try:
            conn = sqlite3.connect(self.smart_response_db_path)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            cursor.execute('SELECT value, setting_type FROM admin_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                value, setting_type = row
                if setting_type == 'integer':
                    return int(value)
                elif setting_type == 'float':
                    return float(value)
                elif setting_type == 'boolean':
                    return value.lower() in ('true', '1', 'yes')
                return value
            return default
        except:
            return default
    
    def get_retention_years(self) -> int:
        """Get the configured data retention period in years"""
        return self._get_setting('data_retention_years', 3)
    
    def is_cleanup_enabled(self) -> bool:
        """Check if automatic cleanup is enabled"""
        return self._get_setting('auto_cleanup_enabled', True)
    
    def get_batch_size(self) -> int:
        """Get the cleanup batch size"""
        return self._get_setting('cleanup_batch_size', 1000)
    
    def get_cutoff_date(self) -> datetime:
        """Calculate the cutoff date based on retention years"""
        retention_years = self.get_retention_years()
        return datetime.now() - timedelta(days=retention_years * 365)
    
    def count_expired_records(self) -> Dict[str, int]:
        """Count expired records in each table"""
        cutoff = self.get_cutoff_date().strftime('%Y-%m-%d %H:%M:%S')
        counts = {}
        
        conn = sqlite3.connect(self.users_db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        # Character interpretations
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM character_interpretations 
                WHERE timestamp < ?
            ''', (cutoff,))
            counts['character_interpretations'] = cursor.fetchone()[0]
        except:
            counts['character_interpretations'] = 0
        
        # Flexible context
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM flexible_context 
                WHERE created_at < ?
            ''', (cutoff,))
            counts['flexible_context'] = cursor.fetchone()[0]
        except:
            counts['flexible_context'] = 0
        
        conn.close()
        return counts
    
    def cleanup_expired_interpretations(self, dry_run: bool = False) -> Dict[str, int]:
        """
        Remove expired character interpretations.
        Returns count of deleted records.
        """
        if not self.is_cleanup_enabled() and not dry_run:
            return {'skipped': True, 'reason': 'Auto cleanup disabled'}
        
        cutoff = self.get_cutoff_date().strftime('%Y-%m-%d %H:%M:%S')
        batch_size = self.get_batch_size()
        
        conn = sqlite3.connect(self.users_db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        results = {
            'cutoff_date': cutoff,
            'batch_size': batch_size,
            'dry_run': dry_run,
            'deleted': {}
        }
        
        try:
            # Count before deletion
            cursor.execute('''
                SELECT COUNT(*) FROM character_interpretations WHERE timestamp < ?
            ''', (cutoff,))
            expired_count = cursor.fetchone()[0]
            results['deleted']['character_interpretations'] = {
                'found': expired_count,
                'deleted': 0
            }
            
            if not dry_run and expired_count > 0:
                # Delete in batches to avoid locking
                total_deleted = 0
                while True:
                    cursor.execute('''
                        DELETE FROM character_interpretations 
                        WHERE id IN (
                            SELECT id FROM character_interpretations 
                            WHERE timestamp < ? 
                            LIMIT ?
                        )
                    ''', (cutoff, batch_size))
                    deleted = cursor.rowcount
                    total_deleted += deleted
                    conn.commit()
                    
                    if deleted < batch_size:
                        break
                
                results['deleted']['character_interpretations']['deleted'] = total_deleted
            
            # Also cleanup old flexible_context if it has retention
            cursor.execute('''
                SELECT COUNT(*) FROM flexible_context 
                WHERE created_at < datetime('now', '-' || COALESCE(retention_years, 10) || ' years')
            ''')
            flex_expired = cursor.fetchone()[0]
            results['deleted']['flexible_context'] = {
                'found': flex_expired,
                'deleted': 0
            }
            
            if not dry_run and flex_expired > 0:
                cursor.execute('''
                    DELETE FROM flexible_context 
                    WHERE created_at < datetime('now', '-' || COALESCE(retention_years, 10) || ' years')
                ''')
                results['deleted']['flexible_context']['deleted'] = cursor.rowcount
                conn.commit()
            
        except Exception as e:
            results['error'] = str(e)
        finally:
            conn.close()
        
        return results
    
    def cleanup_user_data(self, user_id: int) -> Dict[str, int]:
        """
        Delete all interpretation data for a specific user.
        Called when user requests data deletion (GDPR compliance).
        """
        conn = sqlite3.connect(self.users_db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        results = {'user_id': user_id, 'deleted': {}}
        
        try:
            # Get history IDs for this user
            cursor.execute('''
                SELECT id FROM history_primary WHERE user_id = ?
            ''', (user_id,))
            history_ids = [row[0] for row in cursor.fetchall()]
            
            if history_ids:
                # Delete interpretations linked to user's history
                placeholders = ','.join('?' * len(history_ids))
                cursor.execute(f'''
                    DELETE FROM character_interpretations 
                    WHERE primary_history_id IN ({placeholders})
                ''', history_ids)
                results['deleted']['character_interpretations'] = cursor.rowcount
            else:
                results['deleted']['character_interpretations'] = 0
            
            # Delete flexible context
            cursor.execute('''
                DELETE FROM flexible_context WHERE user_id = ?
            ''', (user_id,))
            results['deleted']['flexible_context'] = cursor.rowcount
            
            conn.commit()
            
        except Exception as e:
            results['error'] = str(e)
        finally:
            conn.close()
        
        return results
    
    def export_user_data(self, user_id: int) -> Dict:
        """
        Export all interpretation data for a specific user.
        Returns data in a structured format for GDPR data portability.
        """
        conn = sqlite3.connect(self.users_db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        export_data = {
            'user_id': user_id,
            'exported_at': datetime.now().isoformat(),
            'data': {}
        }
        
        try:
            # Get history IDs for this user
            cursor.execute('''
                SELECT id FROM history_primary WHERE user_id = ?
            ''', (user_id,))
            history_ids = [row[0] for row in cursor.fetchall()]
            
            if history_ids:
                placeholders = ','.join('?' * len(history_ids))
                
                # Export interpretations
                cursor.execute(f'''
                    SELECT ci.id, ci.character_id, ci.interpretation, 
                           ci.concern_level, ci.responded, ci.timestamp
                    FROM character_interpretations ci
                    WHERE ci.primary_history_id IN ({placeholders})
                    ORDER BY ci.timestamp DESC
                ''', history_ids)
                
                interpretations = []
                for row in cursor.fetchall():
                    # Parse interpretation JSON string into object
                    interp_data = row[2]
                    try:
                        import json
                        interp_data = json.loads(row[2]) if row[2] else {}
                    except:
                        interp_data = row[2]
                    
                    interpretations.append({
                        'id': row[0],
                        'character_id': row[1],
                        'interpretation': interp_data,
                        'concern_level': row[3],
                        'responded': bool(row[4]),
                        'timestamp': row[5]
                    })
                export_data['data']['interpretations'] = interpretations
            else:
                export_data['data']['interpretations'] = []
            
            # Export flexible context
            cursor.execute('''
                SELECT id, context_type, context_data, source, created_at
                FROM flexible_context WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            export_data['data']['context'] = [
                {
                    'id': row[0],
                    'type': row[1],
                    'data': row[2],
                    'source': row[3],
                    'created_at': row[4]
                }
                for row in cursor.fetchall()
            ]
            
        except Exception as e:
            export_data['error'] = str(e)
        finally:
            conn.close()
        
        return export_data
    
    def get_cleanup_stats(self) -> Dict:
        """Get statistics about data and cleanup status"""
        conn = sqlite3.connect(self.users_db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        stats = {
            'retention_years': self.get_retention_years(),
            'cleanup_enabled': self.is_cleanup_enabled(),
            'cutoff_date': self.get_cutoff_date().strftime('%Y-%m-%d'),
            'tables': {}
        }
        
        try:
            # Character interpretations stats
            cursor.execute('SELECT COUNT(*) FROM character_interpretations')
            total = cursor.fetchone()[0]
            
            cutoff = self.get_cutoff_date().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                SELECT COUNT(*) FROM character_interpretations WHERE timestamp < ?
            ''', (cutoff,))
            expired = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT MIN(timestamp), MAX(timestamp) FROM character_interpretations
            ''')
            date_range = cursor.fetchone()
            
            stats['tables']['character_interpretations'] = {
                'total_records': total,
                'expired_records': expired,
                'oldest_record': date_range[0],
                'newest_record': date_range[1]
            }
            
            # Flexible context stats
            cursor.execute('SELECT COUNT(*) FROM flexible_context')
            total_flex = cursor.fetchone()[0]
            
            stats['tables']['flexible_context'] = {
                'total_records': total_flex
            }
            
        except Exception as e:
            stats['error'] = str(e)
        finally:
            conn.close()
        
        return stats


# Singleton
_cleanup_manager = None

def get_cleanup_manager() -> DataCleanupManager:
    """Get or create the cleanup manager singleton"""
    global _cleanup_manager
    if _cleanup_manager is None:
        _cleanup_manager = DataCleanupManager()
    return _cleanup_manager
