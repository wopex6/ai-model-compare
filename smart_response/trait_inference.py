"""
Automatic Trait Inference Engine
Learns user personality traits from conversation patterns without formal assessment

Phase 3.2.2 - Personality Data Quality
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json


class TraitInferenceEngine:
    """
    Analyzes conversation patterns to infer Big 5 personality traits
    
    Big 5 Traits (OCEAN):
    - Openness: Creativity, curiosity, intellectual exploration
    - Conscientiousness: Organization, discipline, goal-oriented
    - Extraversion: Social energy, assertiveness, outgoing
    - Agreeableness: Cooperation, kindness, empathy
    - Neuroticism: Emotional stability (inverted for display)
    """
    
    def __init__(self, database):
        """Initialize with database connection"""
        self.db = database
        
        # Pattern keywords for each trait
        self.trait_patterns = {
            'openness': {
                'high': [
                    # Creativity & Ideas
                    r'\b(creative|creativity|imagine|innovation|innovative|invent|novel|original|unique)\b',
                    r'\b(idea|ideas|concept|theory|philosophy|abstract|intellectual)\b',
                    r'\b(curious|curiosity|explore|wonder|discover|learn new|try new)\b',
                    r'\b(art|artistic|poetry|literature|music|design)\b',
                    # Open-mindedness
                    r'\b(open.minded|perspective|viewpoint|consider|possibility|alternative)\b',
                    r'\b(different way|new approach|think outside|unconventional)\b',
                    # Questions about "why" and "what if"
                    r'\bwhy\s+(do|does|is|are|would|should)',
                    r'\bwhat\s+if\b',
                ],
                'low': [
                    # Routine & Tradition
                    r'\b(routine|always|usual|normal|tradition|conventional|standard)\b',
                    r'\b(same way|keep it simple|stick to|as usual|like always)\b',
                    r'\b(practical|realistic|proven|tested|reliable|familiar)\b',
                    # Resistance to change
                    r'\b(don\'t change|prefer.*same|comfortable with|used to)\b',
                ]
            },
            
            'conscientiousness': {
                'high': [
                    # Organization & Planning
                    r'\b(organize|organized|plan|planning|schedule|prepare|preparation)\b',
                    r'\b(list|checklist|agenda|calendar|timeline|deadline)\b',
                    r'\b(structure|systematic|methodical|ordered|arranged)\b',
                    # Goal-oriented
                    r'\b(goal|objective|target|aim|achieve|accomplish|complete)\b',
                    r'\b(progress|milestone|track|measure|productivity)\b',
                    # Discipline & Responsibility
                    r'\b(responsible|responsibility|duty|obligation|commitment)\b',
                    r'\b(disciplin|focus|dedicated|diligent|thorough)\b',
                    r'\b(detail|careful|precise|accurate|perfect)\b',
                ],
                'low': [
                    # Disorganization
                    r'\b(forgot|forget|forgot to|missed|missing|lose|lost)\b',
                    r'\b(messy|disorganized|chaotic|scattered)\b',
                    r'\b(procrastinat|delay|put off|later|postpone)\b',
                    # Spontaneity
                    r'\b(spontaneous|impulsive|wing it|go with flow|flexible)\b',
                    r'\b(last minute|rush|hurry|whatever happens)\b',
                ]
            },
            
            'extraversion': {
                'high': [
                    # Social interaction
                    r'\b(party|parties|social|socialize|gathering|event|meetup)\b',
                    r'\b(friends|people|everyone|crowd|group|team)\b',
                    r'\b(talk|talking|chat|conversation|discuss|share)\b',
                    r'\b(outgoing|energetic|enthusiastic|excitement|excited)\b',
                    # Energy from others
                    r'\b(love being around|enjoy.*people|meet new people)\b',
                    r'\b(can\'t wait to|looking forward to.*people)\b',
                ],
                'low': [
                    # Prefer solitude
                    r'\b(alone|quiet|peace|solitude|private|myself)\b',
                    r'\b(introvert|introverted|shy|reserved|quiet)\b',
                    r'\b(recharge|need space|need time alone|tired of people)\b',
                    # Small groups
                    r'\b(prefer.*small|one.on.one|few people|close friends)\b',
                    r'\b(drain|draining|exhausting.*social|too many people)\b',
                ]
            },
            
            'agreeableness': {
                'high': [
                    # Empathy & Kindness
                    r'\b(help|helping|support|care|caring|kind|kindness)\b',
                    r'\b(empathy|empathize|understand|compassion|sympathize)\b',
                    r'\b(feel for|sorry for|poor|unfortunately)\b',
                    # Cooperation
                    r'\b(together|cooperate|collaborate|team|agree|compromise)\b',
                    r'\b(harmony|peace|get along|friendly|nice)\b',
                    # Considerate
                    r'\b(consider.*feelings|thoughtful|polite|respect)\b',
                ],
                'low': [
                    # Directness
                    r'\b(honestly|frankly|bluntly|straight|direct|truth)\b',
                    r'\b(disagree|argument|debate|challenge|confront)\b',
                    # Competition
                    r'\b(compete|competition|win|beat|outdo|better than)\b',
                    r'\b(assert|assertive|stand up|defend|argue)\b',
                ]
            },
            
            'neuroticism': {
                'high': [
                    # Stress & Anxiety
                    r'\b(stress|stressed|stressful|anxiety|anxious|worry|worried)\b',
                    r'\b(nervous|tense|pressure|overwhelm|panic)\b',
                    r'\b(fear|afraid|scared|frighten|terrif)\b',
                    # Negative emotions
                    r'\b(sad|sadness|depress|unhappy|miserable|hopeless)\b',
                    r'\b(angry|anger|frustrated|annoy|irritat)\b',
                    r'\b(upset|emotional|cry|crying|tears)\b',
                    # Self-doubt
                    r'\b(doubt|uncertain|unsure|insecure|inadequate)\b',
                    r'\b(can\'t do|too hard|impossible|fail|failure)\b',
                ],
                'low': [
                    # Calm & Stable
                    r'\b(calm|relax|peaceful|serene|tranquil)\b',
                    r'\b(stable|steady|balanced|composed|confident)\b',
                    r'\b(fine|okay|alright|no problem|no worries)\b',
                    # Resilience
                    r'\b(handle|manage|cope|deal with|bounce back)\b',
                    r'\b(positive|optimistic|hopeful|confident)\b',
                ]
            }
        }
        
    def analyze_conversation_patterns(self, user_id: int, message_count: int = 50) -> Dict[str, float]:
        """
        Analyze recent conversation patterns to infer trait scores
        
        Args:
            user_id: User to analyze
            message_count: Number of recent messages to analyze
            
        Returns:
            Dict with trait scores (0-100) and confidence (0-1)
        """
        # Get recent user messages
        messages = self._get_recent_messages(user_id, message_count)
        
        if len(messages) < 10:
            return {
                'scores': {},
                'confidence': 0.0,
                'message_count': len(messages),
                'reason': 'Insufficient messages for inference (minimum: 10)'
            }
        
        # Analyze each trait
        trait_scores = {}
        for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
            score = self._analyze_trait(messages, trait)
            trait_scores[trait] = score
        
        # Calculate overall confidence based on message count and pattern clarity
        confidence = self._calculate_confidence(len(messages), trait_scores)
        
        return {
            'scores': trait_scores,
            'confidence': confidence,
            'message_count': len(messages),
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _get_recent_messages(self, user_id: int, count: int) -> List[str]:
        """Get recent user messages from all conversations"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT user_message 
                FROM history_primary
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, count))
            
            messages = [row[0] for row in cursor.fetchall()]
            return messages
        finally:
            conn.close()
    
    def _analyze_trait(self, messages: List[str], trait: str) -> float:
        """
        Analyze messages for a specific trait
        
        Returns score from 0-100 where:
        - 0-40: Low trait
        - 40-60: Moderate trait
        - 60-100: High trait
        """
        combined_text = ' '.join(messages).lower()
        
        high_patterns = self.trait_patterns[trait]['high']
        low_patterns = self.trait_patterns[trait]['low']
        
        # Count pattern matches
        high_matches = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) 
                          for pattern in high_patterns)
        low_matches = sum(len(re.findall(pattern, combined_text, re.IGNORECASE)) 
                         for pattern in low_patterns)
        
        # Calculate score (baseline 50, adjusted by pattern frequency)
        total_words = len(combined_text.split())
        if total_words == 0:
            return 50.0
        
        # Normalize by text length (matches per 100 words)
        high_density = (high_matches / total_words) * 100
        low_density = (low_matches / total_words) * 100
        
        # Score calculation
        # Base of 50, then add/subtract based on pattern density
        # High patterns increase score, low patterns decrease it
        score = 50.0 + (high_density * 10) - (low_density * 10)
        
        # Clamp to 0-100
        score = max(0, min(100, score))
        
        return round(score, 1)
    
    def _calculate_confidence(self, message_count: int, trait_scores: Dict[str, float]) -> float:
        """
        Calculate confidence in the inferred traits
        
        Confidence increases with:
        - More messages analyzed
        - More distinct scores (not all 50)
        """
        # Base confidence from message count
        # 10 messages = 20%, 50 messages = 60%, 100+ messages = 80%
        if message_count < 20:
            base_confidence = 0.2 + (message_count / 20) * 0.2  # 20-40%
        elif message_count < 50:
            base_confidence = 0.4 + ((message_count - 20) / 30) * 0.2  # 40-60%
        elif message_count < 100:
            base_confidence = 0.6 + ((message_count - 50) / 50) * 0.15  # 60-75%
        else:
            base_confidence = 0.75 + min((message_count - 100) / 200, 0.15)  # 75-90%
        
        # Bonus for clear patterns (scores far from neutral 50)
        pattern_clarity = sum(abs(score - 50) for score in trait_scores.values()) / len(trait_scores)
        clarity_bonus = min(pattern_clarity / 100, 0.1)  # Up to +10%
        
        confidence = min(base_confidence + clarity_bonus, 0.9)  # Max 90%
        return round(confidence, 2)
    
    def update_inferred_traits(self, user_id: int, trait_scores: Dict[str, float], confidence: float) -> bool:
        """
        Update or create inferred traits in database
        
        Args:
            user_id: User ID
            trait_scores: Dict of trait name -> score (0-100)
            confidence: Confidence level (0-1)
            
        Returns:
            True if successful
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if inferred traits already exist
            cursor.execute('''
                SELECT 1 FROM inferred_personality WHERE user_id = ?
            ''', (user_id,))
            
            exists = cursor.fetchone() is not None
            
            # Convert scores to 0-1 scale for storage
            normalized_scores = {k: v/100 for k, v in trait_scores.items()}
            
            if exists:
                # Update existing
                cursor.execute('''
                    UPDATE inferred_personality
                    SET openness = ?,
                        conscientiousness = ?,
                        extraversion = ?,
                        agreeableness = ?,
                        neuroticism = ?,
                        confidence = ?,
                        last_updated = CURRENT_TIMESTAMP,
                        message_count = message_count + 1
                    WHERE user_id = ?
                ''', (
                    normalized_scores.get('openness', 0.5),
                    normalized_scores.get('conscientiousness', 0.5),
                    normalized_scores.get('extraversion', 0.5),
                    normalized_scores.get('agreeableness', 0.5),
                    normalized_scores.get('neuroticism', 0.5),
                    confidence,
                    user_id
                ))
            else:
                # Create new
                cursor.execute('''
                    INSERT INTO inferred_personality 
                    (user_id, openness, conscientiousness, extraversion, agreeableness, neuroticism, confidence, message_count, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                ''', (
                    user_id,
                    normalized_scores.get('openness', 0.5),
                    normalized_scores.get('conscientiousness', 0.5),
                    normalized_scores.get('extraversion', 0.5),
                    normalized_scores.get('agreeableness', 0.5),
                    normalized_scores.get('neuroticism', 0.5),
                    confidence
                ))
            
            conn.commit()
            
            # Clear personality cache since data changed
            self.db.clear_personality_cache(user_id)
            
            return True
            
        except Exception as e:
            print(f"Error updating inferred traits: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def should_run_inference(self, user_id: int) -> bool:
        """
        Determine if we should run inference for this user
        
        Criteria:
        - No formal assessment completed OR
        - Last inference was >24 hours ago OR
        - User has sent 10+ new messages since last inference
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user has formal assessment in assessment_history
            cursor.execute('''
                SELECT COUNT(*) FROM assessment_history 
                WHERE user_id = ?
            ''', (user_id,))
            
            has_assessment = cursor.fetchone()[0] > 0
            
            # If they have assessment, inference is lower priority (but still run if new messages)
            # We'll continue checking instead of returning False immediately
            
            # Check last inference time
            cursor.execute('''
                SELECT last_updated, message_count 
                FROM inferred_personality 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            if result is None:
                # Never inferred - run if user has at least 10 messages
                cursor.execute('''
                    SELECT COUNT(*) FROM history_primary 
                    WHERE user_id = ?
                ''', (user_id,))
                message_count = cursor.fetchone()[0]
                return message_count >= 10
            
            last_updated, last_message_count = result
            
            # Check if 24 hours have passed
            if last_updated:
                last_updated_dt = datetime.fromisoformat(last_updated)
                if datetime.now() - last_updated_dt < timedelta(hours=24):
                    return False
            
            # Check if user has 10+ new messages
            cursor.execute('''
                SELECT COUNT(*) FROM history_primary 
                WHERE user_id = ?
            ''', (user_id,))
            current_message_count = cursor.fetchone()[0]
            
            new_messages = current_message_count - last_message_count
            return new_messages >= 10
            
        finally:
            conn.close()
    
    def run_inference_if_needed(self, user_id: int) -> Optional[Dict]:
        """
        Check if inference should run, and run it if needed
        
        Returns:
            Inference results if ran, None if not needed
        """
        if not self.should_run_inference(user_id):
            return None
        
        # Run inference
        results = self.analyze_conversation_patterns(user_id)
        
        if results['confidence'] > 0.2:  # Only update if reasonable confidence
            self.update_inferred_traits(
                user_id, 
                results['scores'], 
                results['confidence']
            )
        
        return results
