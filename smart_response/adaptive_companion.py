"""
Adaptive Companion Framework

Core philosophy: Understand users deeply, inspire with achievable steps,
adapt communication to their unique style, and continuously improve through feedback.

This module enhances AI responses to be truly helpful companions rather than generic advisors.
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'integrated_users.db'


class AdaptiveCompanion:
    """
    Enhances character responses with:
    1. Implicit need detection - understanding what users REALLY need
    2. Small achievable steps - breaking overwhelming situations into manageable actions
    3. Tone adaptation - matching user's communication style and emotional state
    4. Feedback integration - learning from user responses to improve
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
    
    # =========================================================================
    # 1. IMPLICIT NEED DETECTION
    # =========================================================================
    
    def detect_implicit_needs(self, message: str, user_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Detect what the user REALLY needs, beyond their explicit words.
        
        People often say one thing but need another:
        - "I'm so busy" → might need permission to say no
        - "My boss is unfair" → might need validation before solutions
        - "I don't know what to do" → might need someone to help them think, not tell them
        """
        message_lower = message.lower()
        
        implicit_needs = {
            'primary_need': None,
            'secondary_needs': [],
            'emotional_state': None,
            'readiness_for_action': 'unknown',
            'underlying_concerns': []
        }
        
        # Detect if user needs VALIDATION before solutions
        validation_signals = [
            'unfair', 'wrong', 'can\'t believe', 'frustrated', 'upset',
            'annoyed', 'angry', 'hurt', 'disappointed', 'let down'
        ]
        if any(signal in message_lower for signal in validation_signals):
            implicit_needs['primary_need'] = 'validation'
            implicit_needs['secondary_needs'].append('emotional_support')
        
        # Detect if user needs PERMISSION (to rest, say no, prioritize self)
        permission_signals = [
            'too busy', 'no time', 'should i', 'is it okay', 'feel guilty',
            'selfish', 'can\'t say no', 'everyone expects', 'obligations'
        ]
        if any(signal in message_lower for signal in permission_signals):
            implicit_needs['primary_need'] = implicit_needs['primary_need'] or 'permission'
            implicit_needs['secondary_needs'].append('boundary_setting')
        
        # Detect if user needs CLARITY (thinking partner, not answers)
        clarity_signals = [
            'confused', 'don\'t know', 'not sure', 'torn between',
            'can\'t decide', 'overwhelmed', 'too many options', 'stuck'
        ]
        if any(signal in message_lower for signal in clarity_signals):
            implicit_needs['primary_need'] = implicit_needs['primary_need'] or 'clarity'
            implicit_needs['secondary_needs'].append('thinking_partner')
        
        # Detect if user needs CONNECTION (feeling alone)
        connection_signals = [
            'lonely', 'no one understands', 'alone', 'isolated',
            'nobody cares', 'miss', 'disconnected', 'distant'
        ]
        if any(signal in message_lower for signal in connection_signals):
            implicit_needs['primary_need'] = implicit_needs['primary_need'] or 'connection'
            implicit_needs['emotional_state'] = 'lonely'
        
        # Detect if user needs HOPE (feeling hopeless)
        hope_signals = [
            'pointless', 'nothing works', 'given up', 'hopeless',
            'never going to', 'what\'s the point', 'always fails'
        ]
        if any(signal in message_lower for signal in hope_signals):
            implicit_needs['primary_need'] = implicit_needs['primary_need'] or 'hope'
            implicit_needs['emotional_state'] = 'hopeless'
            implicit_needs['readiness_for_action'] = 'low'
        
        # Detect readiness for action
        ready_signals = ['what should i', 'how do i', 'help me', 'i want to', 'ready to']
        not_ready_signals = ['just need to vent', 'so tired', 'exhausted', 'can\'t anymore']
        
        if any(signal in message_lower for signal in ready_signals):
            implicit_needs['readiness_for_action'] = 'high'
        elif any(signal in message_lower for signal in not_ready_signals):
            implicit_needs['readiness_for_action'] = 'low'
        
        # Default to supportive listening if no clear need detected
        if not implicit_needs['primary_need']:
            implicit_needs['primary_need'] = 'supportive_listening'
        
        return implicit_needs
    
    # =========================================================================
    # 2. SMALL ACHIEVABLE STEPS
    # =========================================================================
    
    def generate_micro_steps(self, situation: str, domain: str, 
                             readiness: str = 'medium') -> List[Dict[str, Any]]:
        """
        Break down overwhelming situations into tiny, achievable actions.
        
        Key principles:
        - Steps should be completable in 5-15 minutes
        - First step should be almost trivially easy (builds momentum)
        - Each step should feel achievable RIGHT NOW
        - Include "permission to pause" steps for low readiness
        """
        
        micro_steps = []
        
        # Domain-specific step templates
        step_templates = {
            'work': {
                'overwhelmed': [
                    {'action': 'Write down just ONE task that\'s on your mind right now', 'time': '2 min', 'difficulty': 'easy'},
                    {'action': 'Set a timer for 10 minutes and work on just that one thing', 'time': '10 min', 'difficulty': 'easy'},
                    {'action': 'Take a short break - you\'ve earned it', 'time': '5 min', 'difficulty': 'easy'},
                ],
                'conflict': [
                    {'action': 'Write down how you\'re feeling about this situation (just for yourself)', 'time': '5 min', 'difficulty': 'easy'},
                    {'action': 'Identify one specific thing that bothered you most', 'time': '3 min', 'difficulty': 'easy'},
                    {'action': 'Think of one thing you\'d like to be different', 'time': '2 min', 'difficulty': 'easy'},
                ],
                'decision': [
                    {'action': 'Write down the two options you\'re considering', 'time': '2 min', 'difficulty': 'easy'},
                    {'action': 'For each option, write one pro and one con', 'time': '5 min', 'difficulty': 'easy'},
                    {'action': 'Ask yourself: "Which option would I regret NOT trying?"', 'time': '2 min', 'difficulty': 'medium'},
                ]
            },
            'mental_health': {
                'anxious': [
                    {'action': 'Take 3 slow, deep breaths right now', 'time': '1 min', 'difficulty': 'easy'},
                    {'action': 'Name 5 things you can see around you', 'time': '1 min', 'difficulty': 'easy'},
                    {'action': 'Put your hand on your chest and say "I\'m safe right now"', 'time': '30 sec', 'difficulty': 'easy'},
                ],
                'overwhelmed': [
                    {'action': 'Give yourself permission to do nothing for 5 minutes', 'time': '5 min', 'difficulty': 'easy'},
                    {'action': 'Write down what\'s weighing on you most', 'time': '3 min', 'difficulty': 'easy'},
                    {'action': 'Choose just ONE thing to focus on today', 'time': '2 min', 'difficulty': 'easy'},
                ],
                'sad': [
                    {'action': 'Acknowledge: "It\'s okay to feel sad right now"', 'time': '1 min', 'difficulty': 'easy'},
                    {'action': 'Do one small thing that usually comforts you', 'time': '5 min', 'difficulty': 'easy'},
                    {'action': 'Reach out to one person, even just with a simple text', 'time': '2 min', 'difficulty': 'medium'},
                ]
            },
            'relationships': {
                'conflict': [
                    {'action': 'Write down your feelings without censoring (just for you)', 'time': '5 min', 'difficulty': 'easy'},
                    {'action': 'Try to name what you needed that you didn\'t get', 'time': '3 min', 'difficulty': 'medium'},
                    {'action': 'Consider: What might they have been feeling?', 'time': '3 min', 'difficulty': 'medium'},
                ],
                'lonely': [
                    {'action': 'Send a simple "thinking of you" message to someone', 'time': '1 min', 'difficulty': 'easy'},
                    {'action': 'Plan one small social activity for this week', 'time': '5 min', 'difficulty': 'medium'},
                    {'action': 'Remember: loneliness is a feeling, not a fact about your worth', 'time': '1 min', 'difficulty': 'easy'},
                ]
            },
            'default': [
                {'action': 'Take a moment to acknowledge how you\'re feeling', 'time': '1 min', 'difficulty': 'easy'},
                {'action': 'Write down one small thing you could do about this', 'time': '3 min', 'difficulty': 'easy'},
                {'action': 'Give yourself credit for reaching out and thinking about this', 'time': '1 min', 'difficulty': 'easy'},
            ]
        }
        
        # Adjust based on readiness
        if readiness == 'low':
            # For low readiness, focus on self-compassion first
            micro_steps = [
                {'action': 'It\'s okay to not have solutions right now', 'time': '0 min', 'difficulty': 'easy', 'type': 'permission'},
                {'action': 'Just being aware of this is already a step forward', 'time': '0 min', 'difficulty': 'easy', 'type': 'validation'},
            ]
        
        # Get domain-specific steps
        domain_key = domain.replace('domain_', '')
        if domain_key in step_templates:
            # Try to match situation to a category
            situation_lower = situation.lower()
            for category, steps in step_templates[domain_key].items():
                if category in situation_lower or any(word in situation_lower for word in category.split('_')):
                    micro_steps.extend(steps)
                    break
        
        # Add default steps if nothing specific found
        if len(micro_steps) < 2:
            micro_steps.extend(step_templates['default'])
        
        return micro_steps[:3]  # Return top 3 steps
    
    # =========================================================================
    # 3. TONE ADAPTATION
    # =========================================================================
    
    def get_user_communication_style(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze user's communication style from history to adapt tone.
        
        Considers:
        - Message length (brief vs detailed)
        - Formality (casual vs formal)
        - Emotional expressiveness
        - Preferred response style (direct vs exploratory)
        """
        style = {
            'formality': 'casual',  # casual, balanced, formal
            'brevity': 'balanced',  # brief, balanced, detailed
            'emotional_expressiveness': 'moderate',  # reserved, moderate, expressive
            'directness_preference': 'balanced',  # direct, balanced, exploratory
            'emoji_comfort': 'moderate'  # none, moderate, frequent
        }
        
        if not self.db:
            return style
        
        try:
            cursor = self.db.cursor()
            
            # Get recent user messages
            cursor.execute('''
                SELECT user_message FROM history_primary 
                WHERE user_id = ? 
                ORDER BY timestamp DESC LIMIT 20
            ''', (user_id,))
            
            messages = [row[0] for row in cursor.fetchall() if row[0]]
            
            if not messages:
                return style
            
            # Analyze message lengths
            avg_length = sum(len(m) for m in messages) / len(messages)
            if avg_length < 50:
                style['brevity'] = 'brief'
            elif avg_length > 150:
                style['brevity'] = 'detailed'
            
            # Check for emoji usage
            emoji_count = sum(1 for m in messages if any(c in m for c in '😀😊🙂😢😭😤💪❤️👍'))
            if emoji_count > len(messages) * 0.3:
                style['emoji_comfort'] = 'frequent'
            elif emoji_count == 0:
                style['emoji_comfort'] = 'none'
            
            # Check formality (presence of contractions, casual language)
            casual_markers = ["i'm", "don't", "can't", "won't", "gonna", "wanna", "kinda", "lol", "haha"]
            formal_markers = ["I am", "cannot", "will not", "however", "therefore", "regarding"]
            
            casual_count = sum(1 for m in messages for marker in casual_markers if marker in m.lower())
            formal_count = sum(1 for m in messages for marker in formal_markers if marker in m)
            
            if casual_count > formal_count * 2:
                style['formality'] = 'casual'
            elif formal_count > casual_count * 2:
                style['formality'] = 'formal'
            
            # Check emotional expressiveness
            emotional_words = ['feel', 'felt', 'feeling', 'emotion', 'happy', 'sad', 'angry', 'scared', 'love', 'hate']
            emotional_count = sum(1 for m in messages for word in emotional_words if word in m.lower())
            
            if emotional_count > len(messages) * 0.5:
                style['emotional_expressiveness'] = 'expressive'
            elif emotional_count < len(messages) * 0.1:
                style['emotional_expressiveness'] = 'reserved'
            
            # Check for question-asking (prefers exploration) vs statement-making (prefers directness)
            question_count = sum(1 for m in messages if '?' in m)
            if question_count > len(messages) * 0.4:
                style['directness_preference'] = 'exploratory'
            elif question_count < len(messages) * 0.1:
                style['directness_preference'] = 'direct'
                
        except Exception as e:
            print(f"Error analyzing user style: {e}")
        
        return style
    
    def adapt_response_tone(self, response: str, user_style: Dict[str, Any], 
                           emotional_state: str = None) -> str:
        """
        Adapt the response tone to match user's style.
        
        This provides GUIDANCE for the AI prompt, not direct text manipulation.
        """
        tone_instructions = []
        
        # Formality adaptation
        if user_style.get('formality') == 'casual':
            tone_instructions.append("Use a warm, conversational tone. Contractions are good.")
        elif user_style.get('formality') == 'formal':
            tone_instructions.append("Maintain a respectful, professional tone.")
        
        # Brevity adaptation
        if user_style.get('brevity') == 'brief':
            tone_instructions.append("Keep your response concise and focused. Get to the point.")
        elif user_style.get('brevity') == 'detailed':
            tone_instructions.append("Feel free to elaborate and provide thorough explanations.")
        
        # Emotional state adaptation
        if emotional_state == 'hopeless':
            tone_instructions.append("Be gentle and validating first. Don't rush to solutions.")
        elif emotional_state == 'anxious':
            tone_instructions.append("Be calm and grounding. Use reassuring language.")
        elif emotional_state == 'angry':
            tone_instructions.append("Acknowledge the frustration. Don't minimize their feelings.")
        
        # Directness preference
        if user_style.get('directness_preference') == 'direct':
            tone_instructions.append("Be direct with your suggestions. They appreciate clarity.")
        elif user_style.get('directness_preference') == 'exploratory':
            tone_instructions.append("Ask thoughtful questions to help them explore their own thoughts.")
        
        return "\n".join(tone_instructions)
    
    # =========================================================================
    # 4. FEEDBACK INTEGRATION
    # =========================================================================
    
    def record_feedback(self, user_id: int, message_id: int, 
                       feedback_type: str, feedback_data: Dict = None):
        """
        Record user feedback to improve future responses.
        
        Feedback types:
        - helpful: User found response helpful
        - not_helpful: Response missed the mark
        - too_long: Response was too verbose
        - too_short: Response needed more detail
        - wrong_tone: Tone didn't match user's needs
        - perfect: Response was exactly what they needed
        """
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            
            # Create feedback table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS response_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message_id INTEGER,
                    feedback_type TEXT NOT NULL,
                    feedback_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO response_feedback (user_id, message_id, feedback_type, feedback_data)
                VALUES (?, ?, ?, ?)
            ''', (user_id, message_id, feedback_type, json.dumps(feedback_data) if feedback_data else None))
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error recording feedback: {e}")
    
    def get_feedback_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze feedback to understand what works for this user.
        """
        insights = {
            'preferred_length': 'balanced',
            'tone_feedback': [],
            'helpful_patterns': [],
            'improvement_areas': []
        }
        
        if not self.db:
            return insights
        
        try:
            cursor = self.db.cursor()
            
            cursor.execute('''
                SELECT feedback_type, COUNT(*) 
                FROM response_feedback 
                WHERE user_id = ?
                GROUP BY feedback_type
            ''', (user_id,))
            
            feedback_counts = dict(cursor.fetchall())
            
            # Analyze length preferences
            if feedback_counts.get('too_long', 0) > feedback_counts.get('too_short', 0):
                insights['preferred_length'] = 'brief'
            elif feedback_counts.get('too_short', 0) > feedback_counts.get('too_long', 0):
                insights['preferred_length'] = 'detailed'
            
            # Track what's working
            if feedback_counts.get('helpful', 0) > 0 or feedback_counts.get('perfect', 0) > 0:
                insights['helpful_patterns'].append('Current approach is working well')
            
            # Track improvement areas
            if feedback_counts.get('wrong_tone', 0) > 2:
                insights['improvement_areas'].append('tone_adjustment_needed')
                
        except Exception as e:
            print(f"Error analyzing feedback: {e}")
        
        return insights
    
    # =========================================================================
    # MAIN: BUILD ENHANCED CONTEXT FOR AI
    # =========================================================================
    
    def build_adaptive_context(self, user_id: int, message: str, 
                               domain: str, user_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Build comprehensive context for truly adaptive AI responses.
        
        This combines all four pillars:
        1. What does the user implicitly need?
        2. What small steps could help them?
        3. How should we communicate with them?
        4. What have we learned from feedback?
        """
        
        # 1. Detect implicit needs
        implicit_needs = self.detect_implicit_needs(message, user_history)
        
        # 2. Generate micro-steps if appropriate
        micro_steps = []
        if implicit_needs['readiness_for_action'] != 'low':
            micro_steps = self.generate_micro_steps(
                message, domain, implicit_needs['readiness_for_action']
            )
        
        # 3. Get user's communication style
        user_style = self.get_user_communication_style(user_id)
        tone_guidance = self.adapt_response_tone(
            "", user_style, implicit_needs.get('emotional_state')
        )
        
        # 4. Get feedback insights
        feedback_insights = self.get_feedback_insights(user_id)
        
        # Build the enhanced context
        return {
            'implicit_needs': implicit_needs,
            'suggested_micro_steps': micro_steps,
            'user_style': user_style,
            'tone_guidance': tone_guidance,
            'feedback_insights': feedback_insights,
            'response_strategy': self._determine_response_strategy(implicit_needs)
        }
    
    def _determine_response_strategy(self, implicit_needs: Dict) -> str:
        """
        Determine the best response strategy based on detected needs.
        """
        primary_need = implicit_needs.get('primary_need')
        readiness = implicit_needs.get('readiness_for_action', 'medium')
        
        strategies = {
            'validation': "VALIDATE their feelings first. Acknowledge their experience before anything else. They need to feel heard.",
            'permission': "Give them PERMISSION. They may know what they need to do but feel guilty. Help them see it's okay.",
            'clarity': "Be a THINKING PARTNER. Ask questions that help them clarify their own thoughts. Don't give answers - help them find their own.",
            'connection': "CONNECT with them. They feel alone. Be warm, present, and remind them they matter.",
            'hope': "Offer GENTLE HOPE. Don't be falsely positive, but help them see small possibilities. One tiny step at a time.",
            'supportive_listening': "LISTEN and SUPPORT. Sometimes people just need to be heard. Reflect their feelings back to them."
        }
        
        strategy = strategies.get(primary_need, strategies['supportive_listening'])
        
        if readiness == 'low':
            strategy += "\n\nIMPORTANT: They're not ready for action steps right now. Focus on emotional support first."
        elif readiness == 'high':
            strategy += "\n\nThey're ready to act. Include practical, achievable next steps."
        
        return strategy


# Singleton instance
_adaptive_companion = None

def get_adaptive_companion(db_connection=None) -> AdaptiveCompanion:
    """Get or create the adaptive companion instance."""
    global _adaptive_companion
    if _adaptive_companion is None or db_connection is not None:
        _adaptive_companion = AdaptiveCompanion(db_connection)
    return _adaptive_companion
