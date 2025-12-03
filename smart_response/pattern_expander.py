"""
AI-Assisted Pattern Expansion for Explicit Context
Automatically discovers new extraction patterns using AI analysis
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from anthropic import Anthropic
import os


class PatternExpander:
    """
    Discovers new extraction patterns by analyzing user messages with AI
    Suggests patterns for admin approval before activating
    """
    
    def __init__(self, db_path='integrated_users.db', api_key=None):
        self.db_path = db_path
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None  # Initialize lazily when needed
        self._init_tables()
    
    def _init_tables(self):
        """Create tables for pattern suggestions and usage tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pattern suggestions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_regex TEXT NOT NULL,
                context_type TEXT NOT NULL,
                description TEXT,
                sample_matches TEXT,
                confidence REAL DEFAULT 0.6,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                activated_at TIMESTAMP,
                match_count INTEGER DEFAULT 0,
                false_positive_count INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')
        
        # Pattern usage statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                pattern_regex TEXT,
                context_type TEXT,
                match_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                false_positive_count INTEGER DEFAULT 0,
                last_matched TIMESTAMP,
                avg_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pattern_id) REFERENCES pattern_suggestions(id)
            )
        ''')
        
        # Analysis jobs (track when pattern expansion runs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_analysis_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                messages_analyzed INTEGER DEFAULT 0,
                patterns_suggested INTEGER DEFAULT 0,
                ai_calls_used INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def analyze_recent_messages(self, days=7, limit=100):
        """
        Analyze recent messages to discover new patterns
        Returns suggested patterns for admin review
        """
        print(f"📊 Analyzing messages from last {days} days...")
        
        # Create analysis job record
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pattern_analysis_jobs (started_at, status)
            VALUES (CURRENT_TIMESTAMP, 'running')
        ''')
        job_id = cursor.lastrowid
        conn.commit()
        
        try:
            # Get recent messages (primary history)
            cursor.execute('''
                SELECT user_message, character, timestamp
                FROM history_primary
                WHERE timestamp > datetime('now', '-' || ? || ' days')
                AND user_message IS NOT NULL
                AND length(user_message) > 10
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (days, limit))
            
            messages = cursor.fetchall()
            
            if not messages:
                print("⚠️ No recent messages found")
                cursor.execute('''
                    UPDATE pattern_analysis_jobs
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP,
                        messages_analyzed = 0
                    WHERE id = ?
                ''', (job_id,))
                conn.commit()
                conn.close()
                return []
            
            print(f"✓ Found {len(messages)} messages to analyze")
            
            # Sample messages for AI analysis (don't send all)
            sample_size = min(50, len(messages))
            sample_messages = [msg[0] for msg in messages[:sample_size]]
            
            # Call AI to discover patterns
            suggestions = self._discover_patterns_with_ai(sample_messages)
            
            # Store suggestions in database
            stored_count = 0
            for suggestion in suggestions:
                cursor.execute('''
                    INSERT INTO pattern_suggestions 
                    (pattern_regex, context_type, description, sample_matches, confidence, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                ''', (
                    suggestion['pattern_regex'],
                    suggestion['context_type'],
                    suggestion['description'],
                    json.dumps(suggestion.get('sample_matches', [])),
                    suggestion.get('confidence', 0.6)
                ))
                stored_count += 1
            
            # Update job status
            cursor.execute('''
                UPDATE pattern_analysis_jobs
                SET status = 'completed', 
                    completed_at = CURRENT_TIMESTAMP,
                    messages_analyzed = ?,
                    patterns_suggested = ?,
                    ai_calls_used = 1
                WHERE id = ?
            ''', (len(messages), stored_count, job_id))
            
            conn.commit()
            print(f"✓ Suggested {stored_count} new patterns for review")
            
            return suggestions
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            cursor.execute('''
                UPDATE pattern_analysis_jobs
                SET status = 'failed', 
                    completed_at = CURRENT_TIMESTAMP,
                    error_message = ?
                WHERE id = ?
            ''', (str(e), job_id))
            conn.commit()
            raise
        
        finally:
            conn.close()
    
    def _discover_patterns_with_ai(self, sample_messages):
        """Use AI to analyze messages and suggest extraction patterns"""
        
        # Initialize client if needed
        if not self.client:
            if not self.api_key:
                print("⚠️ No API key available - cannot run AI analysis")
                return []
            self.client = Anthropic(api_key=self.api_key)
        
        # Prepare prompt
        messages_text = "\n".join([f"- {msg}" for msg in sample_messages[:30]])
        
        prompt = f"""Analyze these user messages and identify patterns for extracting explicit statements about:
- Emotional states (feelings, moods)
- Goals (aspirations, objectives)
- Preferences (likes, dislikes, ways of working)
- Needs (requirements, necessities)
- Values (beliefs, principles)

User messages:
{messages_text}

For each pattern you identify:
1. Provide a Python regex pattern to match it
2. Specify the context type (emotional_state, goal, preference, need, value)
3. Give a brief description
4. Provide 2-3 sample matches from the messages above

Format your response as JSON array:
[
  {{
    "pattern_regex": "regex pattern here",
    "context_type": "emotional_state|goal|preference|need|value",
    "description": "brief description",
    "sample_matches": ["example 1", "example 2"]
  }}
]

Only suggest patterns that are clearly explicit (user directly stating something).
Focus on patterns NOT already covered by:
- "I'm feeling X"
- "My goal is to X"
- "I prefer X"
"""
        
        try:
            print("🤖 Calling AI for pattern analysis...")
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text
            
            # Try to parse JSON
            # Look for JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                suggestions = json.loads(json_match.group(0))
                print(f"✓ AI suggested {len(suggestions)} patterns")
                return suggestions
            else:
                print("⚠️ AI response did not contain valid JSON")
                return []
                
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return []
    
    def get_pending_suggestions(self):
        """Get all patterns awaiting admin review"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, pattern_regex, context_type, description, 
                   sample_matches, confidence, created_at
            FROM pattern_suggestions
            WHERE status = 'pending'
            ORDER BY created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        suggestions = []
        for row in rows:
            suggestions.append({
                'id': row[0],
                'pattern_regex': row[1],
                'context_type': row[2],
                'description': row[3],
                'sample_matches': json.loads(row[4]) if row[4] else [],
                'confidence': row[5],
                'created_at': row[6]
            })
        
        return suggestions
    
    def approve_pattern(self, pattern_id, admin_user_id, notes=None):
        """Approve a suggested pattern and activate it"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE pattern_suggestions
            SET status = 'approved',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                activated_at = CURRENT_TIMESTAMP,
                notes = ?
            WHERE id = ?
        ''', (admin_user_id, notes, pattern_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Pattern {pattern_id} approved and activated")
    
    def reject_pattern(self, pattern_id, admin_user_id, reason=None):
        """Reject a suggested pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE pattern_suggestions
            SET status = 'rejected',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                notes = ?
            WHERE id = ?
        ''', (admin_user_id, reason, pattern_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Pattern {pattern_id} rejected")
    
    def get_approved_patterns(self):
        """Get all approved patterns for use in extraction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, pattern_regex, context_type, confidence
            FROM pattern_suggestions
            WHERE status = 'approved'
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        patterns = []
        for row in rows:
            patterns.append({
                'id': row[0],
                'pattern_regex': row[1],
                'context_type': row[2],
                'confidence': row[3]
            })
        
        return patterns
    
    def test_pattern_against_messages(self, pattern_regex, limit=100):
        """Test how many recent messages match a given pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message
            FROM history_primary
            WHERE user_message IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        messages = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Test pattern
        matches = []
        try:
            compiled_pattern = re.compile(pattern_regex, re.IGNORECASE)
            for msg in messages:
                match = compiled_pattern.search(msg)
                if match:
                    matches.append({
                        'message': msg,
                        'matched_text': match.group(0),
                        'groups': match.groups()
                    })
        except re.error as e:
            print(f"❌ Invalid regex: {e}")
            return []
        
        return matches
    
    def get_analysis_history(self, limit=10):
        """Get history of pattern analysis jobs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, started_at, completed_at, messages_analyzed,
                   patterns_suggested, ai_calls_used, status, error_message
            FROM pattern_analysis_jobs
            ORDER BY started_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in rows:
            jobs.append({
                'id': row[0],
                'started_at': row[1],
                'completed_at': row[2],
                'messages_analyzed': row[3],
                'patterns_suggested': row[4],
                'ai_calls_used': row[5],
                'status': row[6],
                'error_message': row[7]
            })
        
        return jobs


if __name__ == '__main__':
    """Test pattern expander"""
    print("=" * 60)
    print("PATTERN EXPANDER TEST")
    print("=" * 60)
    
    expander = PatternExpander()
    
    # Analyze recent messages
    print("\n1. Analyzing recent messages...")
    suggestions = expander.analyze_recent_messages(days=30, limit=50)
    
    print(f"\n✓ Analysis complete!")
    print(f"   Suggestions: {len(suggestions)}")
    
    # Show pending suggestions
    print("\n2. Pending pattern suggestions:")
    pending = expander.get_pending_suggestions()
    for i, pattern in enumerate(pending, 1):
        print(f"\n   {i}. {pattern['context_type']}")
        print(f"      Pattern: {pattern['pattern_regex']}")
        print(f"      Description: {pattern['description']}")
        print(f"      Confidence: {pattern['confidence']}")
        print(f"      Samples: {pattern['sample_matches']}")
    
    # Show analysis history
    print("\n3. Analysis job history:")
    jobs = expander.get_analysis_history(limit=5)
    for job in jobs:
        print(f"\n   Job #{job['id']}: {job['status']}")
        print(f"   Started: {job['started_at']}")
        print(f"   Messages: {job['messages_analyzed']}")
        print(f"   Patterns: {job['patterns_suggested']}")
        print(f"   AI calls: {job['ai_calls_used']}")
