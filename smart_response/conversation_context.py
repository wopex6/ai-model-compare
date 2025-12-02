"""
Enhanced Conversation Context Manager
- Persists context across sessions
- Passes context to AI for better responses
- Uses AI to update context intelligently
- Generates dynamic follow-up suggestions
- Captures and prioritizes explicit user statements
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import sqlite3
from smart_response.explicit_context_handler import ExplicitContextHandler
from smart_response.personality_trend_analyzer import PersonalityTrendAnalyzer


class ConversationContextManager:
    """
    Manages persistent conversation context with AI-powered updates
    Now includes:
    - Explicit context extraction (CRITICAL priority)
    - Personality pattern analysis (HIGH priority inferred traits)
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_context_tables()
        self.explicit_handler = ExplicitContextHandler(db_connection)
        self.personality_analyzer = PersonalityTrendAnalyzer(db_connection)
    
    def _init_context_tables(self):
        """Create tables for context storage"""
        cursor = self.db.cursor()
        
        # Table for conversation context
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                context_type TEXT NOT NULL,
                context_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, character, context_type)
            )
        ''')
        
        # Table for conversation topics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                topic TEXT NOT NULL,
                first_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_mentioned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mention_count INTEGER DEFAULT 1,
                importance_score FLOAT DEFAULT 0.5
            )
        ''')
        
        # Table for follow-up suggestions (AI-generated)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS followup_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                context_snapshot TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP,
                was_used BOOLEAN DEFAULT 0
            )
        ''')
        
        self.db.commit()
    
    def get_context_for_ai(self, user_id: int, character: str, 
                          message_history: List[Dict]) -> Dict:
        """
        Get comprehensive context to pass to AI
        
        Returns:
            {
                'conversation_summary': str,
                'recent_topics': List[str],
                'user_preferences': Dict,
                'ongoing_threads': List[str],
                'emotional_state': str,
                'last_session': str
            }
        """
        cursor = self.db.cursor()
        
        # Get stored context
        cursor.execute('''
            SELECT context_type, context_data 
            FROM conversation_context
            WHERE user_id = ? AND character = ?
        ''', (user_id, character))
        
        stored_context = {}
        for row in cursor.fetchall():
            context_type, context_data = row
            try:
                stored_context[context_type] = json.loads(context_data)
            except:
                stored_context[context_type] = context_data
        
        # Get recent topics
        cursor.execute('''
            SELECT topic, mention_count, importance_score
            FROM conversation_topics
            WHERE user_id = ? AND character = ?
            AND last_mentioned > datetime('now', '-7 days')
            ORDER BY importance_score DESC, last_mentioned DESC
            LIMIT 5
        ''', (user_id, character))
        
        recent_topics = [
            {'topic': row[0], 'mentions': row[1], 'importance': row[2]}
            for row in cursor.fetchall()
        ]
        
        # Build context summary
        context = {
            'user_id': user_id,  # For explicit context access
            'character': character,  # For explicit context access
            'conversation_summary': stored_context.get('summary', 'New conversation'),
            'recent_topics': [t['topic'] for t in recent_topics],
            'user_preferences': stored_context.get('preferences', {}),
            'ongoing_threads': stored_context.get('threads', []),
            'emotional_state': stored_context.get('emotional_state', 'neutral'),
            'last_session': stored_context.get('last_session_date', 'Never'),
            'message_count': len(message_history),
            'topics_discussed': recent_topics
        }
        
        return context
    
    def format_context_for_prompt(self, context: Dict) -> str:
        """
        Format context as a string for AI prompt
        EXPLICIT CONTEXT goes at the TOP (CRITICAL priority)
        
        Args:
            context: Context dictionary
        
        Returns:
            Formatted context string with explicit context first
        """
        parts = []
        
        # PRIORITY 1: EXPLICIT CONTEXT (from user's own words)
        if context.get('user_id') and context.get('character'):
            explicit_context = self.explicit_handler.format_for_ai_prompt(
                context['user_id'], context['character']
            )
            if explicit_context:
                parts.append(explicit_context)
                parts.append("")  # Blank line separator
        
        # PRIORITY 1.5: INFERRED PERSONALITY PATTERNS (from observations)
        if context.get('user_id') and context.get('character'):
            inferred_patterns = self.personality_analyzer.format_for_ai_prompt(
                context['user_id'], context['character']
            )
            if inferred_patterns:
                parts.append(inferred_patterns)
                parts.append("")  # Blank line separator
        
        # PRIORITY 2: General conversation context
        if not context or context.get('message_count', 0) == 0:
            return "\n".join(parts) if parts else ""
        
        parts.append("[Conversation Context]")
        
        # Summary
        if context.get('conversation_summary') and context['conversation_summary'] != 'New conversation':
            parts.append(f"Summary: {context['conversation_summary']}")
        
        # Recent topics
        if context.get('recent_topics'):
            topics_str = ", ".join(context['recent_topics'][:3])
            parts.append(f"Recent topics: {topics_str}")
        
        # Ongoing threads
        if context.get('ongoing_threads'):
            threads_str = "; ".join(context['ongoing_threads'][:2])
            parts.append(f"Ongoing: {threads_str}")
        
        # Emotional state (from inference, not explicit)
        if context.get('emotional_state') and context['emotional_state'] != 'neutral':
            parts.append(f"User seems: {context['emotional_state']}")
        
        # Last session
        if context.get('last_session') and context['last_session'] != 'Never':
            parts.append(f"Last chat: {context['last_session']}")
        
        return "\n".join(parts) if len(parts) > 1 else ""
    
    def update_context(self, user_id: int, character: str, 
                      message: str, response: str, 
                      context_updates: Optional[Dict] = None):
        """
        Update conversation context after an exchange
        NOW includes explicit context extraction (CRITICAL priority)
        
        Args:
            user_id: User ID
            character: Character name
            message: User's message
            response: AI's response
            context_updates: Optional AI-extracted updates
        """
        cursor = self.db.cursor()
        
        # FIRST: Increment message counter
        message_count = self._get_message_count(user_id, character) + 1
        self._upsert_context(user_id, character, 'message_count', str(message_count))
        
        # SECOND: Extract explicit context from user's message (CRITICAL priority)
        print(f"🔍 Extracting explicit context for user_id={user_id}, character={character}", flush=True)
        extracted = self.explicit_handler.extract_explicit_context(user_id, character, message)
        if extracted:
            print(f"   ✓ Extracted {len(extracted)} explicit context items", flush=True)
        else:
            print(f"   ℹ️ No explicit context found in message", flush=True)
        
        # THIRD: Analyze patterns every 5th message (avoid overhead)
        print(f"🔢 Message count: {message_count}", flush=True)
        if message_count % 5 == 0:
            print(f"🧠 Analyzing personality patterns (message #{message_count})...", flush=True)
            inferred = self.personality_analyzer.analyze_patterns(user_id, character, days=14)
            print(f"   📊 Total traits found: {len(inferred) if inferred else 0}", flush=True)
            if inferred:
                high_conf = [t for t in inferred if t['confidence'] >= 0.70]
                low_conf = [t for t in inferred if t['confidence'] < 0.70]
                if high_conf:
                    print(f"   ✓ Inferred {len(high_conf)} personality traits/values (≥70% confidence)", flush=True)
                    for trait in high_conf[:3]:  # Show top 3
                        print(f"     - {trait['category']}: {trait['trait']} (confidence: {trait['confidence']:.0%})", flush=True)
                if low_conf:
                    print(f"   ⚠️ Found {len(low_conf)} traits below 70% threshold (not shown)", flush=True)
                    for trait in low_conf[:2]:  # Show top 2 low-conf
                        print(f"     - {trait['category']}: {trait['trait']} (confidence: {trait['confidence']:.0%}) - needs more evidence", flush=True)
            else:
                print(f"   ℹ️ No patterns detected yet (need 3+ occurrences)", flush=True)
        # Update last session
        self._upsert_context(user_id, character, 'last_session_date', 
                            datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        # Extract and update topics
        topics = self._extract_topics(message + " " + response)
        for topic in topics:
            self._update_topic(user_id, character, topic)
        
        # Update context from AI (if provided)
        if context_updates:
            for key, value in context_updates.items():
                self._upsert_context(user_id, character, key, 
                                   json.dumps(value) if isinstance(value, (dict, list)) else value)
        
        self.db.commit()
    
    def _upsert_context(self, user_id: int, character: str, 
                       context_type: str, context_data: str):
        """Insert or update context"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO conversation_context (user_id, character, context_type, context_data, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, character, context_type) 
            DO UPDATE SET context_data = ?, updated_at = CURRENT_TIMESTAMP
        ''', (user_id, character, context_type, context_data, context_data))
    
    def _update_topic(self, user_id: int, character: str, topic: str):
        """Update or insert topic mention"""
        cursor = self.db.cursor()
        
        # Check if exists
        cursor.execute('''
            SELECT id, mention_count FROM conversation_topics
            WHERE user_id = ? AND character = ? AND topic = ?
        ''', (user_id, character, topic))
        
        row = cursor.fetchone()
        if row:
            # Update existing
            cursor.execute('''
                UPDATE conversation_topics
                SET mention_count = mention_count + 1,
                    last_mentioned = CURRENT_TIMESTAMP,
                    importance_score = MIN(1.0, importance_score + 0.1)
                WHERE id = ?
            ''', (row[0],))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO conversation_topics (user_id, character, topic)
                VALUES (?, ?, ?)
            ''', (user_id, character, topic))
    
    def _get_message_count(self, user_id: int, character: str) -> int:
        """Get total message count for user-character conversation"""
        cursor = self.db.cursor()
        
        # Check if message_count context exists
        cursor.execute('''
            SELECT context_data FROM conversation_context
            WHERE user_id = ? AND character = ? AND context_type = 'message_count'
        ''', (user_id, character))
        
        row = cursor.fetchone()
        if row:
            return int(row[0])
        else:
            # Initialize to 0 if not exists
            self._upsert_context(user_id, character, 'message_count', '0')
            return 0
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Simple keyword extraction for topics
        (In production, could use NLP or AI for better extraction)
        """
        # Common topics to track
        topic_keywords = {
            'goals': ['goal', 'target', 'objective', 'aim'],
            'motivation': ['motivat', 'inspire', 'energy', 'drive'],
            'challenges': ['challenge', 'difficulty', 'problem', 'struggle'],
            'progress': ['progress', 'improvement', 'better', 'growing'],
            'emotions': ['feel', 'emotion', 'mood', 'anxious', 'happy', 'sad'],
            'relationships': ['relationship', 'friend', 'family', 'partner'],
            'work': ['work', 'job', 'career', 'profession'],
            'health': ['health', 'fitness', 'exercise', 'diet'],
            'mindfulness': ['meditation', 'mindful', 'peace', 'zen'],
            'philosophy': ['philosophy', 'wisdom', 'stoic', 'virtue']
        }
        
        text_lower = text.lower()
        detected = []
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(topic)
                    break
        
        return list(set(detected))
    
    def save_ai_suggestion(self, user_id: int, character: str, 
                          suggestion: str, context: Dict):
        """Save AI-generated follow-up suggestion"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO followup_suggestions 
            (user_id, character, suggestion, context_snapshot)
            VALUES (?, ?, ?, ?)
        ''', (user_id, character, suggestion, json.dumps(context)))
        self.db.commit()
    
    def mark_suggestion_used(self, user_id: int, suggestion: str):
        """Mark a suggestion as used"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE followup_suggestions
            SET was_used = 1, used_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND suggestion = ?
            ORDER BY generated_at DESC
            LIMIT 1
        ''', (user_id, suggestion))
        self.db.commit()
    
    def get_context_summary(self, user_id: int, character: str) -> str:
        """Get human-readable context summary"""
        context = self.get_context_for_ai(user_id, character, [])
        
        if not context['recent_topics']:
            return "New conversation - no previous context"
        
        summary = f"Topics discussed: {', '.join(context['recent_topics'][:3])}"
        if context.get('ongoing_threads'):
            summary += f"\nOngoing: {context['ongoing_threads'][0]}"
        
        return summary
    
    def clear_old_context(self, days: int = 30):
        """Clear context older than specified days"""
        cursor = self.db.cursor()
        cursor.execute('''
            DELETE FROM conversation_context
            WHERE updated_at < datetime('now', '-' || ? || ' days')
        ''', (days,))
        cursor.execute('''
            DELETE FROM conversation_topics
            WHERE last_mentioned < datetime('now', '-' || ? || ' days')
        ''', (days,))
        cursor.execute('''
            DELETE FROM followup_suggestions
            WHERE generated_at < datetime('now', '-' || ? || ' days')
        ''', (days,))
        self.db.commit()
