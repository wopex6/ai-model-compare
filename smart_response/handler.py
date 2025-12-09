"""
Smart Response Handler - Main integration point for the system
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import json

from .detector import SmallTalkDetector
from .learner import UserStyleLearner
from .character_replies import CharacterQuickReplies
from .context_analyzer import ConversationContextAnalyzer


class SmartResponseHandler:
    """
    Main handler that coordinates detection, learning, and response generation
    """
    
    # Character safety rules - these topics ALWAYS use full AI
    CHARACTER_SAFETY_RULES = {
        'psychologist': {
            'critical_keywords': [
                'suicide', 'suicidal', 'kill myself', 'end it all', 'want to die',
                'self-harm', 'hurt myself', 'cutting', 'abuse', 'abused',
                'trauma', 'traumatic', 'panic attack', 'breakdown'
            ],
            'sensitive_topics': [
                'mental health', 'depression', 'anxiety disorder', 'ptsd'
            ]
        },
        'life_coach': {
            'critical_keywords': [
                'should i quit', 'thinking about divorce', 'end my relationship',
                'major life decision'
            ],
            # Life coach benefits from personalized, detailed responses
            # Quick replies feel too generic for life transformation work
            'prefer_full_ai': True,
            'confidence_threshold': 0.97  # Only use quick replies for VERY obvious small talk
        },
        'marcus': {
            'prefer_ai_keywords': [
                'virtue', 'ethics', 'morality', 'should i', 'right thing to do'
            ]
        }
    }
    
    def __init__(self, db_connection):
        """
        Initialize with database connection
        
        Args:
            db_connection: Active SQLite connection
        """
        self.db = db_connection
        self.detector = SmallTalkDetector()
        self.learner = UserStyleLearner(db_connection)
        self.quick_replies = CharacterQuickReplies()
        self.context_analyzer = ConversationContextAnalyzer(db_connection)
    
    def process_message(self, user_id: int, message: str, 
                       character: str) -> Tuple[str, Dict]:
        """
        Process incoming message and determine response strategy
        
        Args:
            user_id: User ID
            message: User's message
            character: Character name ('coach', 'sage', 'marcus', etc.)
        
        Returns:
            Tuple of (response_type, response_data)
            - response_type: 'quick_reply' | 'full_ai'
            - response_data: {
                'text': str (if quick_reply),
                'confidence': float,
                'reasoning': List[str],
                'metadata': Dict
              }
        """
        # Step 1: Check character safety rules
        if self._requires_full_ai_by_safety(message, character):
            return 'full_ai', {
                'confidence': 1.0,
                'reasoning': ['Character safety rule triggered'],
                'metadata': {'safety_override': True}
            }
        
        # Step 2: Analyze conversation context
        context = self.context_analyzer.analyze_context(user_id, message, character)
        
        # Step 3: Detect if message is small talk
        detection = self.detector.detect(message, context)
        
        # Step 4: Adjust confidence based on context
        adjusted_confidence = detection['confidence'] + context['context_score']
        adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
        
        detection['original_confidence'] = detection['confidence']
        detection['confidence'] = adjusted_confidence
        detection['reasoning'].append(f"Context adjustment: {context['context_score']:+.2f}")
        
        # Step 5: Check character-specific threshold (if configured)
        character_threshold = self._get_character_threshold(character)
        if character_threshold is not None:
            # Character has a specific threshold - use it
            should_use_quick = adjusted_confidence >= character_threshold
            if not should_use_quick:
                detection['reasoning'].append(f"Below {character} threshold ({character_threshold:.2f})")
        else:
            # No character-specific threshold - use user preferences
            should_use_quick = self.learner.should_use_quick_reply(
                user_id, 
                adjusted_confidence,
                character
            )
        
        if should_use_quick and detection['type'] == 'SMALL_TALK':
            # Generate quick reply
            category = detection.get('category', 'acknowledgment')
            
            if detection['category']:
                # Get reply with contextual suggestion
                reply, suggestion = self.quick_replies.get_reply_with_suggestion(
                    character, 
                    detection['category'],
                    context={'recent_suggestions': context.get('recent_suggestions', [])}
                )
                
                return 'quick_reply', {
                    'text': reply,
                    'suggestion': suggestion,  # NEW: Follow-up prompt
                    'confidence': adjusted_confidence,
                    'category': detection['category'],
                    'metadata': {
                        'detection_type': detection['type'],
                        'context': context
                    }
                }
            else:
                quick_reply_text = self.quick_replies.get_contextual_reply(
                    character,
                    category,
                    message,
                    context.get('last_ai_message')
                )
                
                return 'quick_reply', {
                    'text': quick_reply_text,
                    'confidence': adjusted_confidence,
                    'reasoning': detection['reasoning'],
                    'metadata': {
                        'category': category,
                        'detection_type': detection['type'],
                        'context': context
                    }
                }
        else:
            # Use full AI
            return 'full_ai', {
                'confidence': adjusted_confidence,
                'reasoning': detection['reasoning'] + [
                    f"Confidence {adjusted_confidence:.2f} below threshold for quick reply"
                ],
                'metadata': {
                    'detection_type': detection['type'],
                    'context': context
                }
            }
    
    def track_response(self, user_id: int, message: str, response_type: str,
                      character: str, user_followup: Optional[str] = None,
                      time_to_followup: Optional[float] = None):
        """
        Track the response and learn from user's reaction
        
        Args:
            user_id: User ID
            message: Original message
            response_type: 'quick_reply' or 'full_ai'
            character: Character name
            user_followup: User's next message (if any)
            time_to_followup: Seconds until user's next message
        """
        # Get sentiment if there's a followup
        followup_sentiment = None
        if user_followup:
            followup_sentiment = self.context_analyzer.get_sentiment_from_followup(user_followup)
        
        # Check if conversation continued
        conversation_continued = user_followup is not None
        
        # Track interaction
        interaction_data = {
            'message': message,
            'response_type': response_type,
            'character': character,
            'timestamp': datetime.now(),
            'user_followup': user_followup,
            'time_to_followup': time_to_followup,
            'followup_sentiment': followup_sentiment,
            'conversation_continued': conversation_continued
        }
        
        self.learner.track_interaction(user_id, interaction_data)
    
    def _requires_full_ai_by_safety(self, message: str, character: str) -> bool:
        """Check if character safety rules require full AI"""
        message_lower = message.lower()
        character = character.lower()
        
        if character not in self.CHARACTER_SAFETY_RULES:
            return False
        
        rules = self.CHARACTER_SAFETY_RULES[character]
        
        # Check critical keywords
        if 'critical_keywords' in rules:
            for keyword in rules['critical_keywords']:
                if keyword in message_lower:
                    return True
        
        # Check sensitive topics (these also should use AI)
        if 'sensitive_topics' in rules:
            for topic in rules['sensitive_topics']:
                if topic in message_lower:
                    return True
        
        return False
    
    def _get_character_threshold(self, character: str) -> Optional[float]:
        """Get character-specific confidence threshold if configured"""
        character = character.lower()
        
        if character not in self.CHARACTER_SAFETY_RULES:
            return None
        
        rules = self.CHARACTER_SAFETY_RULES[character]
        return rules.get('confidence_threshold', None)
    
    def get_user_stats(self, user_id: int) -> Dict:
        """
        Get statistics about user's learning profile
        
        Returns:
            {
                'interaction_count': int,
                'quick_reply_rate': float,
                'success_rate': float,
                'threshold': float,
                'preferences': Dict
            }
        """
        profile = self.learner.get_user_profile(user_id)
        
        # Get interaction statistics
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN response_type = 'quick_reply' THEN 1 ELSE 0 END) as quick_count,
                AVG(satisfaction_score) as avg_satisfaction
            FROM interaction_history
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        total = row[0] if row else 0
        quick_count = row[1] if row else 0
        avg_satisfaction = row[2] if row else 0.5
        
        quick_reply_rate = (quick_count / total) if total > 0 else 0.0
        
        return {
            'interaction_count': profile.get('interaction_count', 0),
            'quick_reply_rate': quick_reply_rate,
            'success_rate': profile.get('quick_reply_success_rate', 0.5),
            'threshold': profile.get('quick_reply_threshold', 0.90),
            'avg_satisfaction': avg_satisfaction,
            'prefer_detailed': profile.get('prefer_detailed', False),
            'character_preferences': profile.get('character_preferences', {})
        }
    
    def reset_user_learning(self, user_id: int):
        """Reset a user's learning profile"""
        cursor = self.db.cursor()
        
        # Delete learning profile
        cursor.execute('DELETE FROM user_learning_profiles WHERE user_id = ?', (user_id,))
        
        # Optionally keep or delete interaction history
        # cursor.execute('DELETE FROM interaction_history WHERE user_id = ?', (user_id,))
        
        self.db.commit()
