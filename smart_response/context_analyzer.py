"""
Conversation Context Analyzer - Analyzes conversation flow and context
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re


class ConversationContextAnalyzer:
    """
    Analyzes conversation history to determine context and improve detection
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def analyze_context(self, user_id: int, current_message: str, 
                       character: str, limit: int = 10) -> Dict:
        """
        Analyze recent conversation context
        
        Returns:
            {
                'conversation_depth': int,  # How many exchanges
                'last_ai_message': str,
                'last_ai_length': int,
                'time_since_last': float,  # seconds
                'is_acknowledgment': bool,
                'topic_detected': str,
                'emotional_context': bool,
                'context_score': float  # Adjusts confidence
            }
        """
        # Get recent messages
        history = self._get_recent_messages(user_id, character, limit)
        
        if not history:
            return {
                'conversation_depth': 0,
                'last_ai_message': None,
                'last_ai_length': 0,
                'time_since_last': float('inf'),
                'is_acknowledgment': False,
                'topic_detected': 'general',
                'emotional_context': False,
                'context_score': 0.0
            }
        
        # Analyze
        last_message = history[-1] if history else None
        conversation_depth = len(history) // 2  # Pairs of exchanges
        
        # Time since last message
        time_since = 999999
        if last_message:
            try:
                last_time = datetime.fromisoformat(last_message['timestamp'])
                time_since = (datetime.now() - last_time).total_seconds()
            except:
                time_since = 999999
        
        # Check if current message is acknowledging previous AI response
        is_ack = False
        last_ai_message = None
        last_ai_length = 0
        
        if last_message and last_message['role'] == 'assistant':
            last_ai_message = last_message['content']
            last_ai_length = len(last_ai_message.split())
            
            # If AI gave long response and user responds quickly with short message
            if last_ai_length > 50 and time_since < 15:
                if len(current_message.split()) < 5:
                    is_ack = True
        
        # Detect topic
        topic = self._detect_topic(history + [{'role': 'user', 'content': current_message}])
        
        # Check for emotional context
        emotional = self._has_emotional_context(history, current_message)
        
        # Calculate context adjustment score
        context_score = self._calculate_context_score(
            conversation_depth, is_ack, last_ai_length, 
            time_since, topic, emotional
        )
        
        return {
            'conversation_depth': conversation_depth,
            'last_ai_message': last_ai_message,
            'last_ai_length': last_ai_length,
            'time_since_last': time_since,
            'is_acknowledgment': is_ack,
            'topic_detected': topic,
            'emotional_context': emotional,
            'context_score': context_score
        }
    
    def _get_recent_messages(self, user_id: int, character: str, limit: int) -> List[Dict]:
        """Get recent messages from conversation"""
        cursor = self.db.cursor()
        
        # Get recent messages from messages table first (if exists)
        try:
            cursor.execute('''
                SELECT role, content, timestamp
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.user_id = ?
                ORDER BY m.timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            if rows:
                messages = []
                for row in rows:
                    messages.append({
                        'role': row[0],
                        'content': row[1],
                        'timestamp': row[2]
                    })
                return list(reversed(messages))  # Oldest first
        except:
            pass
        
        # Fallback: Try ai_conversations table
        try:
            cursor.execute('''
                SELECT conversation_data
                FROM ai_conversations
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row and row[0]:
                import json
                conv_data = json.loads(row[0])
                messages = conv_data.get('messages', [])
                return messages[-limit:] if messages else []
        except:
            pass
        
        return []
    
    def _detect_topic(self, messages: List[Dict]) -> str:
        """Detect conversation topic"""
        # Combine recent messages
        text = ' '.join([m.get('content', '') for m in messages[-5:]])
        text_lower = text.lower()
        
        # Topic keywords
        topics = {
            'philosophy': ['stoic', 'virtue', 'wisdom', 'philosophy', 'meaning', 'purpose'],
            'motivation': ['goal', 'motivation', 'success', 'achieve', 'confidence'],
            'mental_health': ['anxiety', 'depression', 'stress', 'mental', 'therapy'],
            'relationships': ['relationship', 'partner', 'family', 'friend', 'love'],
            'work': ['job', 'career', 'work', 'business', 'professional'],
            'meditation': ['meditation', 'mindfulness', 'peace', 'calm', 'zen'],
            'productivity': ['productivity', 'time', 'organize', 'efficiency', 'habit'],
            'science': ['science', 'research', 'experiment', 'data', 'theory']
        }
        
        for topic, keywords in topics.items():
            if any(kw in text_lower for kw in keywords):
                return topic
        
        return 'general'
    
    def _has_emotional_context(self, history: List[Dict], current_message: str) -> bool:
        """Check if conversation has emotional context"""
        # Emotional keywords
        emotional_keywords = [
            'feel', 'feeling', 'felt', 'emotion', 'emotional',
            'sad', 'happy', 'angry', 'frustrated', 'anxious', 'worried',
            'scared', 'afraid', 'excited', 'depressed', 'upset',
            'hurt', 'pain', 'suffering', 'joy', 'love', 'hate'
        ]
        
        # Check recent history
        recent_text = ' '.join([m.get('content', '') for m in history[-3:]])
        recent_text += ' ' + current_message
        recent_text = recent_text.lower()
        
        return any(kw in recent_text for kw in emotional_keywords)
    
    def _calculate_context_score(self, depth: int, is_ack: bool, 
                                 ai_length: int, time_since: float,
                                 topic: str, emotional: bool) -> float:
        """
        Calculate score adjustment based on context
        Positive score = lean toward quick reply
        Negative score = lean toward full AI
        """
        score = 0.0
        
        # Acknowledgment pattern
        if is_ack and ai_length > 50:
            score += 0.25  # Likely acknowledging explanation
        
        # Conversation depth
        if depth < 2:
            score += 0.05  # Early conversation, casual OK
        elif depth > 8:
            score -= 0.10  # Deep conversation, be careful
        
        # Topic sensitivity
        sensitive_topics = ['mental_health', 'relationships', 'philosophy']
        if topic in sensitive_topics:
            score -= 0.15  # These need careful responses
        
        # Emotional context
        if emotional:
            score -= 0.20  # Be cautious with emotions
        
        # Time gaps
        if time_since > 3600:  # More than 1 hour gap
            score += 0.05  # Fresh start, casual OK
        elif time_since < 5:  # Very quick response
            # Could be eager OR frustrated
            if is_ack:
                score += 0.10  # Eager acknowledgment
            else:
                score -= 0.10  # Might be frustrated
        
        return score
    
    def get_sentiment_from_followup(self, followup_message: str) -> float:
        """
        Estimate sentiment of followup message
        Returns: -1.0 (negative) to 1.0 (positive)
        """
        if not followup_message:
            return 0.0
        
        message_lower = followup_message.lower()
        
        # Positive indicators
        positive_words = [
            'thanks', 'thank', 'great', 'perfect', 'excellent', 'awesome',
            'helpful', 'good', 'nice', 'wonderful', 'love', 'appreciate',
            'exactly', 'brilliant', 'fantastic'
        ]
        
        # Negative indicators
        negative_words = [
            'but', 'however', 'not', "doesn't", "don't", 'confused',
            'unclear', 'wrong', 'disagree', 'problem', 'issue', 'frustrated',
            "that's not", 'what about', 'explain', 'elaborate'
        ]
        
        pos_count = sum(1 for word in positive_words if word in message_lower)
        neg_count = sum(1 for word in negative_words if word in message_lower)
        
        # Simple scoring
        if pos_count > neg_count:
            return min(1.0, pos_count * 0.3)
        elif neg_count > pos_count:
            return max(-1.0, -neg_count * 0.3)
        else:
            return 0.0
