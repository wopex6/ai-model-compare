"""
User Style Learner - Learns user preferences implicitly from behavior
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json


class UserStyleLearner:
    """
    Learns user conversation preferences without explicit feedback
    Tracks satisfaction signals and adapts response strategy
    """
    
    def __init__(self, db_connection):
        """
        Args:
            db_connection: Database connection for storing/retrieving learning data
        """
        self.db = db_connection
    
    def get_user_profile(self, user_id: int) -> Dict:
        """
        Get user's learned preference profile
        
        Returns:
            {
                'quick_reply_threshold': float (0-1),  # Confidence needed for quick reply
                'prefer_detailed': bool,
                'interaction_count': int,
                'quick_reply_success_rate': float,
                'character_preferences': Dict[str, float],
                'time_patterns': Dict[str, str],  # hour -> preference
                'topic_preferences': Dict[str, str],
                'personality_traits': Dict[str, float]  # from psychology test if available
            }
        """
        cursor = self.db.cursor()
        
        # Get learning profile
        cursor.execute('''
            SELECT profile_data, interaction_count, last_updated
            FROM user_learning_profiles
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            profile_data = json.loads(row[0]) if row[0] else {}
            profile_data['interaction_count'] = row[1]
            profile_data['last_updated'] = row[2]
        else:
            # New user - conservative defaults
            profile_data = {
                'quick_reply_threshold': 0.90,  # Start conservative
                'prefer_detailed': False,  # Unknown
                'interaction_count': 0,
                'quick_reply_success_rate': 0.5,  # Neutral
                'character_preferences': {},
                'time_patterns': {},
                'topic_preferences': {},
                'personality_traits': {}
            }
        
        # Get psychology traits if available
        cursor.execute('''
            SELECT trait_name, trait_value
            FROM psychology_traits
            WHERE user_id = ?
        ''', (user_id,))
        
        traits = {row[0]: row[1] for row in cursor.fetchall()}
        if traits:
            profile_data['personality_traits'] = traits
        
        return profile_data
    
    def track_interaction(self, user_id: int, interaction_data: Dict):
        """
        Track an interaction and learn from it
        
        interaction_data:
            {
                'message': str,
                'response_type': 'quick_reply' | 'full_ai',
                'character': str,
                'timestamp': datetime,
                'user_followup': Optional[str],
                'time_to_followup': Optional[float],  # seconds
                'followup_sentiment': Optional[float],
                'conversation_continued': bool
            }
        """
        # Detect satisfaction signals
        satisfaction = self._detect_satisfaction(interaction_data)
        
        # Update profile based on satisfaction
        self._update_profile(user_id, interaction_data, satisfaction)
        
        # Store interaction for history
        self._store_interaction(user_id, interaction_data, satisfaction)
    
    def _detect_satisfaction(self, interaction_data: Dict) -> Dict:
        """
        Detect if user was satisfied with the response (implicit signals)
        
        Returns:
            {
                'satisfied': bool,
                'confidence': float (0-1),
                'signals': List[str]
            }
        """
        score = 0.5  # Start neutral
        signals = []
        
        response_type = interaction_data.get('response_type')
        user_followup = (interaction_data.get('user_followup') or '').lower()
        time_to_followup = interaction_data.get('time_to_followup')
        followup_sentiment = interaction_data.get('followup_sentiment', 0)
        
        # Positive signals
        if time_to_followup and time_to_followup > 10:
            score += 0.15
            signals.append('User took time to think')
        
        if user_followup and len(user_followup.split()) > 5:
            score += 0.10
            signals.append('Substantial engaged followup')
        
        if followup_sentiment and followup_sentiment > 0.3:
            score += 0.20
            signals.append('Positive sentiment in followup')
        
        # Positive keywords
        positive_keywords = ['great', 'perfect', 'exactly', 'helpful', 'thanks', 'love', 'awesome']
        if any(kw in user_followup for kw in positive_keywords):
            score += 0.25
            signals.append('Explicit positive feedback')
        
        if interaction_data.get('conversation_continued', False):
            score += 0.10
            signals.append('User continued conversation')
        
        # Negative signals
        if time_to_followup and time_to_followup < 2:
            score -= 0.15
            signals.append('Immediate response (possible frustration)')
        
        if followup_sentiment and followup_sentiment < -0.2:
            score -= 0.25
            signals.append('Negative sentiment in followup')
        
        # Dissatisfaction keywords
        negative_keywords = ['but', 'however', "that's not", 'what about', 'i mean', 
                            'explain', 'elaborate', 'more detail', "doesn't help"]
        if any(kw in user_followup for kw in negative_keywords):
            score -= 0.20
            signals.append('Dissatisfaction indicators')
        
        # Very short, disengaged response
        if user_followup and len(user_followup.split()) < 3 and time_to_followup and time_to_followup < 5:
            score -= 0.15
            signals.append('Short disengaged response')
        
        # If quick reply was used but user immediately asks for more
        if response_type == 'quick_reply' and any(kw in user_followup for kw in 
                ['more', 'explain', 'how', 'why', 'what', 'elaborate']):
            score -= 0.30
            signals.append('Quick reply insufficient, needed more detail')
        
        satisfied = score > 0.65
        dissatisfied = score < 0.35
        
        return {
            'satisfied': satisfied,
            'dissatisfied': dissatisfied,
            'score': max(0.0, min(1.0, score)),
            'signals': signals
        }
    
    def _update_profile(self, user_id: int, interaction_data: Dict, satisfaction: Dict):
        """Update user profile based on interaction outcome"""
        profile = self.get_user_profile(user_id)
        
        response_type = interaction_data.get('response_type')
        character = interaction_data.get('character', '').lower()
        hour = interaction_data.get('timestamp', datetime.now()).hour
        
        # Update interaction count
        profile['interaction_count'] = profile.get('interaction_count', 0) + 1
        count = profile['interaction_count']
        
        # Learning rate (higher for new users, lower as they mature)
        if count < 20:
            learn_rate = 0.15  # Aggressive learning
        elif count < 50:
            learn_rate = 0.08  # Moderate learning
        else:
            learn_rate = 0.03  # Fine-tuning
        
        # Update quick reply threshold based on satisfaction
        if response_type == 'quick_reply':
            if satisfaction['satisfied']:
                # Quick reply worked - can be slightly more aggressive
                profile['quick_reply_threshold'] = max(0.70, 
                    profile.get('quick_reply_threshold', 0.90) - learn_rate)
            elif satisfaction['dissatisfied']:
                # Quick reply failed - need higher confidence
                profile['quick_reply_threshold'] = min(0.95,
                    profile.get('quick_reply_threshold', 0.90) + learn_rate * 2)
        
        # Track character-specific preferences
        if character:
            char_prefs = profile.get('character_preferences', {})
            current_pref = char_prefs.get(character, 0.5)
            
            if satisfaction['satisfied']:
                char_prefs[character] = min(1.0, current_pref + learn_rate)
            elif satisfaction['dissatisfied']:
                char_prefs[character] = max(0.0, current_pref - learn_rate)
            
            profile['character_preferences'] = char_prefs
        
        # Track time-of-day patterns
        time_prefs = profile.get('time_patterns', {})
        hour_key = f"hour_{hour}"
        
        if satisfaction['satisfied']:
            time_prefs[hour_key] = response_type  # Remember what worked
        
        profile['time_patterns'] = time_prefs
        
        # Update success rate
        if response_type == 'quick_reply':
            old_rate = profile.get('quick_reply_success_rate', 0.5)
            new_point = 1.0 if satisfaction['satisfied'] else 0.0
            # Exponential moving average
            profile['quick_reply_success_rate'] = old_rate * 0.9 + new_point * 0.1
        
        # Detect preference for detail
        if satisfaction['dissatisfied'] and response_type == 'quick_reply':
            profile['prefer_detailed'] = True
        elif satisfaction['satisfied'] and response_type == 'quick_reply':
            # If consistently satisfied with quick replies
            if profile.get('quick_reply_success_rate', 0) > 0.75:
                profile['prefer_detailed'] = False
        
        # Save updated profile
        self._save_profile(user_id, profile)
    
    def _save_profile(self, user_id: int, profile: Dict):
        """Save updated profile to database"""
        cursor = self.db.cursor()
        
        # Remove non-serializable fields
        profile_data = dict(profile)
        profile_data.pop('last_updated', None)
        interaction_count = profile_data.pop('interaction_count', 0)
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_learning_profiles 
            (user_id, profile_data, interaction_count, last_updated)
            VALUES (?, ?, ?, ?)
        ''', (user_id, json.dumps(profile_data), interaction_count, datetime.now().isoformat()))
        
        self.db.commit()
    
    def _store_interaction(self, user_id: int, interaction_data: Dict, satisfaction: Dict):
        """Store interaction for historical analysis"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO interaction_history
            (user_id, message, response_type, character, satisfaction_score, 
             satisfaction_signals, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            interaction_data.get('message', ''),
            interaction_data.get('response_type', ''),
            interaction_data.get('character', ''),
            satisfaction['score'],
            json.dumps(satisfaction['signals']),
            interaction_data.get('timestamp', datetime.now()).isoformat()
        ))
        
        self.db.commit()
    
    def should_use_quick_reply(self, user_id: int, detection_confidence: float, 
                               character: str = None) -> bool:
        """
        Decide if quick reply should be used based on user profile
        
        Args:
            user_id: User ID
            detection_confidence: Confidence from detector (0-1)
            character: Character name
        
        Returns:
            True if should use quick reply, False for full AI
        """
        profile = self.get_user_profile(user_id)
        
        threshold = profile.get('quick_reply_threshold', 0.90)
        
        # Adjust threshold based on character preference
        if character:
            char_pref = profile.get('character_preferences', {}).get(character.lower(), 0.5)
            threshold = threshold - (char_pref - 0.5) * 0.2  # Adjust by preference
        
        # Adjust based on personality traits
        traits = profile.get('personality_traits', {})
        if traits.get('openness', 0.5) > 0.7:
            threshold += 0.05  # High openness prefers detail
        if traits.get('extraversion', 0.5) < 0.3:
            threshold -= 0.05  # Low extraversion OK with brief
        
        # For new users (cold start), be conservative
        if profile.get('interaction_count', 0) < 10:
            threshold = max(threshold, 0.88)
        
        return detection_confidence >= threshold
