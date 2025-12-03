"""
Context Expiration & Archival System
Manages lifecycle of explicit context data:
- Archives old context (preserves for analysis)
- Expires context based on age
- Reduces confidence over time (decay)
"""

import sqlite3
from datetime import datetime, timedelta


class ContextArchival:
    """
    Manages expiration and archival of explicit context
    Old context is archived (not deleted) for trend analysis
    """
    
    def __init__(self, db_path='integrated_users.db'):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Create archive table and add expiration fields to main table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Archive table (identical structure to explicit_context)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS explicit_context_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_id INTEGER,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context_type TEXT NOT NULL,
                context_key TEXT,
                context_value TEXT NOT NULL,
                original_statement TEXT,
                priority TEXT DEFAULT 'NORMAL',
                confidence REAL DEFAULT 1.0,
                original_confidence REAL DEFAULT 1.0,
                active INTEGER DEFAULT 1,
                expires_at TIMESTAMP,
                extracted_via TEXT DEFAULT 'regex',
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archive_reason TEXT
            )
        ''')
        
        # Archival statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archival_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contexts_archived INTEGER DEFAULT 0,
                contexts_expired INTEGER DEFAULT 0,
                contexts_decayed INTEGER DEFAULT 0,
                oldest_archived_days INTEGER,
                notes TEXT
            )
        ''')
        
        # Add expires_at column if it doesn't exist
        try:
            cursor.execute('''
                ALTER TABLE explicit_context 
                ADD COLUMN original_confidence REAL DEFAULT 1.0
            ''')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()
    
    def apply_confidence_decay(self, decay_days=30):
        """
        Reduce confidence of old context over time
        Formula: confidence = original_confidence * (1 - age_days / decay_days)
        
        Example:
        - Day 0: confidence = 1.0
        - Day 15: confidence = 0.5
        - Day 30: confidence = 0.0 (expired)
        """
        print(f"⏰ Applying confidence decay (decay period: {decay_days} days)...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Initialize original_confidence for existing records
        cursor.execute('''
            UPDATE explicit_context
            SET original_confidence = confidence
            WHERE original_confidence IS NULL OR original_confidence = 0
        ''')
        
        # Calculate new confidence based on age
        cursor.execute(f'''
            UPDATE explicit_context
            SET confidence = original_confidence * (
                1.0 - CAST(
                    julianday('now') - julianday(timestamp)
                AS REAL) / {decay_days}
            )
            WHERE active = 1
            AND julianday('now') - julianday(timestamp) < {decay_days}
        ''')
        
        decayed_count = cursor.rowcount
        
        # Mark fully decayed context as inactive (confidence <= 0)
        cursor.execute('''
            UPDATE explicit_context
            SET active = 0,
                confidence = 0.0
            WHERE confidence <= 0
            AND active = 1
        ''')
        
        expired_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✓ Decayed {decayed_count} contexts")
        print(f"✓ Expired {expired_count} contexts (confidence reached 0)")
        
        return {
            'decayed_count': decayed_count,
            'expired_count': expired_count
        }
    
    def archive_old_context(self, archive_days=90, auto_archive=True):
        """
        Archive context older than specified days
        Moves data to archive table, optionally removes from main table
        
        Args:
            archive_days: Age threshold for archival
            auto_archive: If True, automatically archive. If False, only suggest
        """
        print(f"📦 Archiving context older than {archive_days} days...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find old context to archive
        cursor.execute(f'''
            SELECT id, user_id, character, timestamp, context_type, context_key,
                   context_value, original_statement, priority, confidence,
                   original_confidence, active, expires_at, extracted_via
            FROM explicit_context
            WHERE julianday('now') - julianday(timestamp) > {archive_days}
            AND id NOT IN (SELECT original_id FROM explicit_context_archive WHERE original_id IS NOT NULL)
        ''')
        
        old_contexts = cursor.fetchall()
        
        if not old_contexts:
            print("✓ No old context found to archive")
            conn.close()
            return {'archived_count': 0}
        
        print(f"   Found {len(old_contexts)} old contexts")
        
        if not auto_archive:
            conn.close()
            return {
                'archived_count': 0,
                'suggested_count': len(old_contexts),
                'preview': old_contexts[:5]
            }
        
        # Archive each context
        archived_count = 0
        for row in old_contexts:
            original_id = row[0]
            age_days = (datetime.now() - datetime.fromisoformat(row[3])).days
            
            cursor.execute('''
                INSERT INTO explicit_context_archive 
                (original_id, user_id, character, timestamp, context_type, context_key,
                 context_value, original_statement, priority, confidence, 
                 original_confidence, active, expires_at, extracted_via, 
                 archived_at, archive_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (
                original_id, row[1], row[2], row[3], row[4], row[5],
                row[6], row[7], row[8], row[9], row[10], row[11],
                row[12], row[13],
                f'Auto-archived after {age_days} days'
            ))
            
            archived_count += 1
        
        # Remove from main table (optional - keep for now, just mark as archived)
        # cursor.execute('''
        #     DELETE FROM explicit_context
        #     WHERE julianday('now') - julianday(timestamp) > ?
        # ''', (archive_days,))
        
        # Record statistics
        cursor.execute(f'''
            SELECT MAX(julianday('now') - julianday(timestamp))
            FROM explicit_context
            WHERE julianday('now') - julianday(timestamp) > {archive_days}
        ''')
        oldest_days = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO archival_statistics
            (run_date, contexts_archived, oldest_archived_days)
            VALUES (CURRENT_TIMESTAMP, ?, ?)
        ''', (archived_count, int(oldest_days) if oldest_days else 0))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Archived {archived_count} contexts")
        
        return {
            'archived_count': archived_count,
            'oldest_archived_days': int(oldest_days) if oldest_days else 0
        }
    
    def expire_old_context(self, expiration_days=60):
        """
        Mark context as inactive (expired) based on age
        More aggressive than decay - hard cutoff
        """
        print(f"⏰ Expiring context older than {expiration_days} days...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Set expires_at if not already set
        cursor.execute(f'''
            UPDATE explicit_context
            SET expires_at = datetime(timestamp, '+{expiration_days} days')
            WHERE expires_at IS NULL
        ''')
        
        # Expire context past expiration date
        cursor.execute('''
            UPDATE explicit_context
            SET active = 0
            WHERE expires_at < datetime('now')
            AND active = 1
        ''')
        
        expired_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✓ Expired {expired_count} contexts")
        
        return {'expired_count': expired_count}
    
    def get_expiring_soon(self, days_threshold=7):
        """Get context that will expire soon (for user notification)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT id, user_id, character, context_type, context_value,
                   original_statement, timestamp, expires_at,
                   julianday(expires_at) - julianday('now') as days_until_expiry
            FROM explicit_context
            WHERE active = 1
            AND expires_at IS NOT NULL
            AND julianday(expires_at) - julianday('now') <= {days_threshold}
            AND julianday(expires_at) - julianday('now') > 0
            ORDER BY expires_at ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        expiring = []
        for row in rows:
            expiring.append({
                'id': row[0],
                'user_id': row[1],
                'character': row[2],
                'context_type': row[3],
                'context_value': row[4],
                'original_statement': row[5],
                'timestamp': row[6],
                'expires_at': row[7],
                'days_until_expiry': int(row[8])
            })
        
        return expiring
    
    def extend_context_expiration(self, context_id, additional_days=30):
        """Extend expiration date for important context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            UPDATE explicit_context
            SET expires_at = datetime(expires_at, '+{additional_days} days')
            WHERE id = ?
        ''', (context_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Extended expiration for context {context_id} by {additional_days} days")
    
    def get_archival_statistics(self):
        """Get statistics about archival operations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total archived
        cursor.execute('SELECT COUNT(*) FROM explicit_context_archive')
        total_archived = cursor.fetchone()[0]
        
        # Active contexts
        cursor.execute('SELECT COUNT(*) FROM explicit_context WHERE active = 1')
        total_active = cursor.fetchone()[0]
        
        # Expired contexts
        cursor.execute('SELECT COUNT(*) FROM explicit_context WHERE active = 0')
        total_expired = cursor.fetchone()[0]
        
        # Recent archival runs
        cursor.execute('''
            SELECT run_date, contexts_archived, contexts_expired, contexts_decayed
            FROM archival_statistics
            ORDER BY run_date DESC
            LIMIT 10
        ''')
        recent_runs = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_archived': total_archived,
            'total_active': total_active,
            'total_expired': total_expired,
            'recent_runs': [
                {
                    'date': row[0],
                    'archived': row[1],
                    'expired': row[2],
                    'decayed': row[3]
                }
                for row in recent_runs
            ]
        }
    
    def run_maintenance(self, decay_days=30, archive_days=90, expiration_days=60):
        """
        Run complete maintenance:
        1. Apply confidence decay
        2. Expire old context
        3. Archive very old context
        """
        print("=" * 60)
        print("CONTEXT MAINTENANCE")
        print("=" * 60)
        
        results = {}
        
        # Step 1: Decay
        print("\n1. Applying confidence decay...")
        results['decay'] = self.apply_confidence_decay(decay_days)
        
        # Step 2: Expire
        print("\n2. Expiring old context...")
        results['expiration'] = self.expire_old_context(expiration_days)
        
        # Step 3: Archive
        print("\n3. Archiving very old context...")
        results['archival'] = self.archive_old_context(archive_days)
        
        # Step 4: Statistics
        print("\n4. Gathering statistics...")
        results['stats'] = self.get_archival_statistics()
        
        print("\n" + "=" * 60)
        print("MAINTENANCE COMPLETE")
        print("=" * 60)
        print(f"   Decayed: {results['decay']['decayed_count']}")
        print(f"   Expired: {results['decay']['expired_count'] + results['expiration']['expired_count']}")
        print(f"   Archived: {results['archival']['archived_count']}")
        print(f"   Active: {results['stats']['total_active']}")
        print(f"   Total Archived: {results['stats']['total_archived']}")
        
        return results


if __name__ == '__main__':
    """Test context archival"""
    print("=" * 60)
    print("CONTEXT ARCHIVAL TEST")
    print("=" * 60)
    
    archival = ContextArchival()
    
    # Run full maintenance
    results = archival.run_maintenance(
        decay_days=30,
        archive_days=90,
        expiration_days=60
    )
    
    # Show expiring soon
    print("\n" + "=" * 60)
    print("CONTEXTS EXPIRING SOON")
    print("=" * 60)
    expiring = archival.get_expiring_soon(days_threshold=7)
    
    if expiring:
        for item in expiring:
            print(f"\n   User {item['user_id']} - {item['character']}")
            print(f"   Type: {item['context_type']}")
            print(f"   Value: {item['context_value']}")
            print(f"   Expires in: {item['days_until_expiry']} days")
    else:
        print("\n   No contexts expiring soon")
    
    # Show statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    stats = archival.get_archival_statistics()
    print(f"\n   Active contexts: {stats['total_active']}")
    print(f"   Expired contexts: {stats['total_expired']}")
    print(f"   Archived contexts: {stats['total_archived']}")
    
    if stats['recent_runs']:
        print("\n   Recent maintenance runs:")
        for run in stats['recent_runs'][:3]:
            print(f"      {run['date']}: archived={run['archived']}, expired={run['expired']}")
