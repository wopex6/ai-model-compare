"""
Dual-Layer History System
Maintains two layers of conversation history:
1. PRIMARY - Raw, immutable data (what was actually said)
2. SECONDARY - Analytical interpretation (what it means)
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import sqlite3
import re


class DualLayerHistorySystem:
    """
    Manages dual-layer conversation history with progress tracking
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create tables for dual-layer history"""
        cursor = self.db.cursor()
        
        # PRIMARY LAYER - Raw conversation data (immutable)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_primary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Raw data
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                response_type TEXT,
                
                -- Metadata
                session_id TEXT,
                message_length INTEGER,
                response_time_ms INTEGER,
                
                -- Source of truth marker
                is_primary BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_primary_user_time 
            ON history_primary(user_id, timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_primary_session 
            ON history_primary(session_id)
        ''')
        
        # SECONDARY LAYER - Analytical interpretation (can evolve)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_secondary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                primary_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Interpreted data
                detected_intent TEXT,
                emotional_tone TEXT,
                topics_extracted TEXT,
                personality_interpretation TEXT,
                
                -- Context snapshot
                context_snapshot TEXT,
                
                -- Insights
                progress_indicators TEXT,
                concerns_identified TEXT,
                opportunities_spotted TEXT,
                
                -- Guidance
                suggested_actions TEXT,
                follow_up_recommended TEXT,
                
                -- Meta
                analysis_confidence FLOAT,
                analysis_version TEXT DEFAULT 'v1.0',
                
                FOREIGN KEY (primary_id) REFERENCES history_primary(id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_secondary_user 
            ON history_secondary(user_id, analysis_timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_secondary_primary 
            ON history_secondary(primary_id)
        ''')
        
        # PROGRESS TRACKING - Long-term patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                
                -- What we're tracking
                goal_category TEXT,
                metric_name TEXT,
                
                -- Timeline
                tracking_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Data points (JSON array)
                data_points TEXT NOT NULL,
                
                -- Trend analysis
                trend_direction TEXT,
                trend_confidence FLOAT,
                
                -- Related messages
                related_primary_ids TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_progress_user_goal 
            ON history_progress(user_id, goal_category)
        ''')
        
        self.db.commit()
        print("✓ Dual-layer history tables initialized")
    
    def store_interaction(self, user_id: int, character: str,
                         user_message: str, assistant_response: str,
                         response_type: str, metadata: Optional[Dict] = None) -> int:
        """
        Store interaction in PRIMARY layer (raw, immutable data)
        
        Args:
            user_id: User ID
            character: Character name
            user_message: Exact user message
            assistant_response: Exact assistant response
            response_type: 'quick_reply' or 'full_ai'
            metadata: Optional metadata dict
        
        Returns:
            primary_id for linking secondary analysis
        """
        if metadata is None:
            metadata = {}
        
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO history_primary 
            (user_id, character, user_message, assistant_response, 
             response_type, session_id, message_length, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            character,
            user_message,
            assistant_response,
            response_type,
            metadata.get('session_id'),
            len(user_message),
            metadata.get('response_time_ms', 0)
        ))
        
        primary_id = cursor.lastrowid
        self.db.commit()
        
        return primary_id
    
    def analyze_and_store_secondary(self, primary_id: int,
                                   user_id: int, character: str,
                                   interpretation: Optional[Dict] = None,
                                   context: Optional[Dict] = None) -> int:
        """
        Analyze and store in SECONDARY layer (interpretations)
        
        Args:
            primary_id: ID from primary layer
            user_id: User ID
            character: Character name
            interpretation: Optional pre-computed interpretation
            context: Optional context snapshot
        
        Returns:
            secondary_id
        """
        cursor = self.db.cursor()
        
        # Get primary record if we need to analyze
        if interpretation is None:
            cursor.execute('''
                SELECT user_message, assistant_response
                FROM history_primary WHERE id = ?
            ''', (primary_id,))
            
            row = cursor.fetchone()
            if not row:
                return -1
            
            user_message, assistant_response = row
            
            # Simple analysis (can be enhanced with AI)
            interpretation = self._analyze_simple(user_message, assistant_response)
        
        # Extract components
        detected_intent = interpretation.get('detected_intent', 'general')
        emotional_tone = interpretation.get('emotional_tone', 'neutral')
        topics = interpretation.get('topics_extracted', [])
        personality_interp = interpretation.get('personality_interpretation', {})
        progress_indicators = interpretation.get('progress_indicators', {})
        concerns = interpretation.get('concerns_identified', [])
        opportunities = interpretation.get('opportunities_spotted', [])
        confidence = interpretation.get('confidence_level', 0.5)
        
        # Store analysis
        cursor.execute('''
            INSERT INTO history_secondary 
            (primary_id, user_id, character, detected_intent, emotional_tone,
             topics_extracted, personality_interpretation, context_snapshot,
             progress_indicators, concerns_identified, opportunities_spotted,
             analysis_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            primary_id, user_id, character,
            detected_intent,
            emotional_tone,
            json.dumps(topics),
            json.dumps(personality_interp),
            json.dumps(context) if context else None,
            json.dumps(progress_indicators),
            json.dumps(concerns),
            json.dumps(opportunities),
            confidence
        ))
        
        secondary_id = cursor.lastrowid
        self.db.commit()
        
        return secondary_id
    
    def _analyze_simple(self, user_message: str, assistant_response: str) -> Dict:
        """
        Simple analysis of message (can be enhanced with AI)
        """
        msg_lower = user_message.lower()
        
        # Detect intent
        intent = 'general'
        if any(word in msg_lower for word in ['help', 'how', 'what', 'why']):
            intent = 'seeking_information'
        elif any(word in msg_lower for word in ['thanks', 'thank you']):
            intent = 'gratitude'
        elif any(word in msg_lower for word in ['hi', 'hello', 'hey']):
            intent = 'greeting'
        
        # Detect emotional tone
        tone = self._detect_emotional_tone(user_message)
        
        # Extract topics
        topics = self._extract_topics_simple(user_message)
        
        # Detect progress indicators
        progress = self._detect_progress_indicators(user_message)
        
        # Identify concerns
        concerns = self._identify_concerns_simple(user_message)
        
        # Spot opportunities
        opportunities = self._spot_opportunities_simple(user_message)
        
        return {
            'detected_intent': intent,
            'emotional_tone': tone,
            'topics_extracted': topics,
            'progress_indicators': progress,
            'concerns_identified': concerns,
            'opportunities_spotted': opportunities,
            'confidence_level': 0.6  # Simple analysis = moderate confidence
        }
    
    def _detect_emotional_tone(self, text: str) -> str:
        """Detect emotional tone from text"""
        text_lower = text.lower()
        
        # Positive emotions
        positive_words = ['happy', 'excited', 'great', 'awesome', 'love', 'wonderful', 'amazing']
        if any(word in text_lower for word in positive_words):
            return 'positive'
        
        # Negative emotions
        negative_words = ['sad', 'angry', 'frustrated', 'upset', 'hate', 'terrible', 'awful']
        if any(word in text_lower for word in negative_words):
            return 'negative'
        
        # Anxious emotions
        anxious_words = ['worried', 'anxious', 'nervous', 'scared', 'afraid', 'stressed', 'overwhelmed']
        if any(word in text_lower for word in anxious_words):
            return 'anxious'
        
        return 'neutral'
    
    def _extract_topics_simple(self, text: str) -> List[str]:
        """Simple topic extraction"""
        text_lower = text.lower()
        topics = []
        
        topic_keywords = {
            'goals': ['goal', 'target', 'objective', 'aim'],
            'motivation': ['motivat', 'inspire', 'energy', 'drive'],
            'challenges': ['challenge', 'difficulty', 'problem', 'struggle', 'issue'],
            'progress': ['progress', 'improvement', 'better', 'growing', 'improve'],
            'emotions': ['feel', 'emotion', 'mood'],
            'relationships': ['relationship', 'friend', 'family', 'partner'],
            'work': ['work', 'job', 'career', 'profession'],
            'health': ['health', 'fitness', 'exercise', 'diet', 'workout'],
            'mindfulness': ['meditation', 'mindful', 'peace', 'zen', 'calm'],
            'philosophy': ['philosophy', 'wisdom', 'stoic', 'virtue', 'meaning']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _detect_progress_indicators(self, text: str) -> Dict:
        """Detect indicators of progress or setbacks"""
        text_lower = text.lower()
        indicators = {}
        
        progress_patterns = {
            'achievement': ['completed', 'achieved', 'succeeded', 'won', 'finished', 'accomplished'],
            'improvement': ['better', 'improved', 'progress', 'growing', 'increasing'],
            'setback': ['failed', 'couldn\'t', 'didn\'t work', 'setback', 'worse'],
            'milestone': ['milestone', 'breakthrough', 'first time', 'finally']
        }
        
        for category, keywords in progress_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                indicators[category] = True
        
        return indicators
    
    def _identify_concerns_simple(self, text: str) -> List[str]:
        """Identify concerns or challenges"""
        concerns = []
        
        concern_patterns = [
            r"(?:worried|concerned|anxious) about (.+?)(?:\.|$|,)",
            r"struggling with (.+?)(?:\.|$|,)",
            r"having trouble (?:with )?(.+?)(?:\.|$|,)",
            r"can't (?:seem to )?(.+?)(?:\.|$|,)"
        ]
        
        for pattern in concern_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            concerns.extend(matches)
        
        return [c.strip() for c in concerns if c.strip()]
    
    def _spot_opportunities_simple(self, text: str) -> List[str]:
        """Spot opportunities for intervention"""
        opportunities = []
        text_lower = text.lower()
        
        # Desire for change
        if any(phrase in text_lower for phrase in ['want to', 'would like to', 'hoping to']):
            opportunities.append('expressed_desire_for_change')
        
        # Seeking guidance
        if '?' in text and any(word in text_lower for word in ['how', 'what', 'should', 'can you']):
            opportunities.append('seeking_guidance')
        
        # High motivation
        if any(word in text_lower for word in ['ready', 'prepared', 'let\'s', 'excited to']):
            opportunities.append('high_motivation_moment')
        
        # Openness to feedback
        if any(phrase in text_lower for phrase in ['what do you think', 'your thoughts', 'feedback']):
            opportunities.append('open_to_feedback')
        
        return opportunities
    
    def get_conversation_history(self, user_id: int, character: str,
                                layer: str = 'both',
                                limit: int = 20) -> List[Dict]:
        """
        Retrieve history from specified layer(s)
        
        Args:
            user_id: User ID
            character: Character name
            layer: 'primary', 'secondary', or 'both'
            limit: Maximum number of records
        
        Returns:
            List of history records
        """
        cursor = self.db.cursor()
        
        if layer == 'primary' or layer == 'both':
            cursor.execute('''
                SELECT id, timestamp, user_message, assistant_response, 
                       response_type, session_id
                FROM history_primary
                WHERE user_id = ? AND character = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, character, limit))
            
            primary_records = [
                {
                    'id': row[0],
                    'timestamp': row[1],
                    'user_message': row[2],
                    'assistant_response': row[3],
                    'response_type': row[4],
                    'session_id': row[5],
                    'layer': 'primary'
                }
                for row in cursor.fetchall()
            ]
        else:
            primary_records = []
        
        if layer == 'secondary' or layer == 'both':
            cursor.execute('''
                SELECT id, primary_id, analysis_timestamp,
                       detected_intent, emotional_tone, topics_extracted,
                       progress_indicators, concerns_identified,
                       opportunities_spotted, analysis_confidence
                FROM history_secondary
                WHERE user_id = ? AND character = ?
                ORDER BY analysis_timestamp DESC
                LIMIT ?
            ''', (user_id, character, limit))
            
            secondary_records = [
                {
                    'id': row[0],
                    'primary_id': row[1],
                    'timestamp': row[2],
                    'intent': row[3],
                    'emotional_tone': row[4],
                    'topics': json.loads(row[5]) if row[5] else [],
                    'progress': json.loads(row[6]) if row[6] else {},
                    'concerns': json.loads(row[7]) if row[7] else [],
                    'opportunities': json.loads(row[8]) if row[8] else [],
                    'confidence': row[9],
                    'layer': 'secondary'
                }
                for row in cursor.fetchall()
            ]
        else:
            secondary_records = []
        
        if layer == 'both':
            # Merge primary and secondary
            merged = []
            for primary in primary_records:
                secondary = next(
                    (s for s in secondary_records if s['primary_id'] == primary['id']),
                    None
                )
                merged.append({
                    'primary': primary,
                    'secondary': secondary
                })
            return merged
        elif layer == 'primary':
            return primary_records
        else:
            return secondary_records
    
    def get_stats(self, user_id: int, character: str) -> Dict:
        """Get statistics about user's history"""
        cursor = self.db.cursor()
        
        # Total interactions
        cursor.execute('''
            SELECT COUNT(*) FROM history_primary
            WHERE user_id = ? AND character = ?
        ''', (user_id, character))
        total_interactions = cursor.fetchone()[0]
        
        # Quick reply vs Full AI
        cursor.execute('''
            SELECT response_type, COUNT(*) FROM history_primary
            WHERE user_id = ? AND character = ?
            GROUP BY response_type
        ''', (user_id, character))
        response_types = dict(cursor.fetchall())
        
        # Common topics
        cursor.execute('''
            SELECT topics_extracted FROM history_secondary
            WHERE user_id = ? AND character = ?
            AND topics_extracted IS NOT NULL
        ''', (user_id, character))
        
        all_topics = []
        for row in cursor.fetchall():
            topics = json.loads(row[0]) if row[0] else []
            all_topics.extend(topics)
        
        from collections import Counter
        topic_counts = Counter(all_topics)
        
        # Emotional tone distribution
        cursor.execute('''
            SELECT emotional_tone, COUNT(*) FROM history_secondary
            WHERE user_id = ? AND character = ?
            GROUP BY emotional_tone
        ''', (user_id, character))
        emotional_distribution = dict(cursor.fetchall())
        
        return {
            'total_interactions': total_interactions,
            'response_types': response_types,
            'top_topics': dict(topic_counts.most_common(5)),
            'emotional_distribution': emotional_distribution
        }
