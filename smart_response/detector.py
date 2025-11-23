"""
Small Talk Detector - Determines if a message is small talk or needs full AI
"""

import re
from typing import Dict, Optional, List
from datetime import datetime

# Global NLP model instance
_nlp_model = None

def get_nlp_model():
    """Lazy load spaCy model"""
    global _nlp_model
    if _nlp_model is None:
        try:
            import spacy
            _nlp_model = spacy.load("en_core_web_sm")
        except:
            # Fallback if spaCy not available
            _nlp_model = False
    return _nlp_model if _nlp_model else None


class SmallTalkDetector:
    """
    Detects small talk vs complex messages using pattern matching + NLP
    """
    
    # Pattern-based detection (instant, no NLP needed)
    OBVIOUS_PATTERNS = {
        'greeting': [
            r'\b(hi|hello|hey|good morning|good evening|good afternoon|howdy|greetings)\b',
        ],
        'farewell': [
            r'\b(bye|goodbye|see you|talk later|catch you later|gtg|gotta go|take care)\b',
        ],
        'thanks': [
            r'\b(thanks?|thank you|thx|ty|thanx|appreciate|appreciated|grateful)\b',
        ],
        'acknowledgment': [
            r'\b(ok|okay|got it|sure|alright|k|kk|understood|right|noted)\b',
        ],
        'agreement': [
            r'\b(yes|yeah|yep|yup|correct|exactly|absolutely|indeed)\b',
        ],
        'disagreement': [
            r'\b(no|nope|nah|not really|don\'t think so)\b',
        ],
        'simple_questions': [
            r'^(how are you|how\'s it going|what\'s up|sup)\??$',
        ]
    }
    
    # Complexity markers (indicate need for full AI)
    COMPLEXITY_KEYWORDS = [
        'feel', 'feeling', 'worried', 'anxious', 'happy', 'sad',
        'afraid', 'confused', 'angry', 'frustrated', 'depressed',
        'help', 'advice', 'how do i', 'what should', 'struggling',
        'problem', 'issue', 'difficult', 'challenge', 'concern'
    ]
    
    # Critical keywords that ALWAYS require AI (safety)
    CRITICAL_KEYWORDS = [
        'suicide', 'suicidal', 'kill myself', 'end it all', 'want to die',
        'self-harm', 'hurt myself', 'cutting', 'abuse', 'abused',
        'trauma', 'traumatic', 'panic attack', 'breakdown'
    ]
    
    def __init__(self):
        self.nlp = get_nlp_model()
    
    def detect(self, message: str, context: Optional[Dict] = None) -> Dict:
        """
        Main detection method
        
        Returns:
            {
                'type': 'SMALL_TALK' | 'COMPLEX' | 'BORDERLINE',
                'confidence': float (0-1),
                'category': str (optional),
                'reasoning': List[str]
            }
        """
        message_lower = message.lower().strip()
        word_count = len(message.split())
        reasoning = []
        
        # Step 1: Check for critical keywords (safety first!)
        if self._contains_critical_keywords(message_lower):
            return {
                'type': 'COMPLEX',
                'confidence': 1.0,
                'category': 'critical_safety',
                'reasoning': ['Contains critical safety keywords - requires full AI']
            }
        
        # Step 2: Pattern-based detection (fast path)
        pattern_result = self._check_patterns(message_lower)
        if pattern_result['confidence'] > 0.85:
            return pattern_result
        
        # Step 3: Quick complexity check
        if word_count < 3 and pattern_result['confidence'] > 0.5:
            # Very short + matches pattern = likely small talk
            pattern_result['confidence'] = min(pattern_result['confidence'] + 0.15, 0.95)
            pattern_result['reasoning'].append('Very short message')
            return pattern_result
        
        if word_count > 30:
            # Long message = complex
            reasoning.append('Long message (>30 words)')
            return {
                'type': 'COMPLEX',
                'confidence': 0.90,
                'reasoning': reasoning
            }
        
        # Step 4: Check for complexity markers
        complexity_score = self._check_complexity_markers(message_lower)
        if complexity_score > 0:
            reasoning.append(f'Complexity markers detected (score: {complexity_score})')
            if complexity_score >= 2:
                return {
                    'type': 'COMPLEX',
                    'confidence': 0.85,
                    'reasoning': reasoning
                }
        
        # Step 5: NLP analysis (if available and needed)
        if self.nlp and pattern_result['confidence'] < 0.75:
            nlp_result = self._analyze_with_nlp(message, message_lower)
            # Combine pattern and NLP results
            combined_confidence = (pattern_result['confidence'] + nlp_result['confidence']) / 2
            combined_reasoning = pattern_result['reasoning'] + nlp_result['reasoning']
            
            if combined_confidence >= 0.70:
                return {
                    'type': 'SMALL_TALK',
                    'confidence': combined_confidence,
                    'category': pattern_result.get('category', 'general'),
                    'reasoning': combined_reasoning
                }
            elif combined_confidence <= 0.40:
                return {
                    'type': 'COMPLEX',
                    'confidence': 1 - combined_confidence,
                    'reasoning': combined_reasoning
                }
            else:
                return {
                    'type': 'BORDERLINE',
                    'confidence': 0.60,
                    'reasoning': combined_reasoning
                }
        
        # Step 6: Default to pattern result or borderline
        if pattern_result['confidence'] >= 0.60:
            return pattern_result
        else:
            return {
                'type': 'BORDERLINE',
                'confidence': 0.55,
                'reasoning': reasoning + ['Ambiguous message, needs user history context']
            }
    
    def _check_patterns(self, message_lower: str) -> Dict:
        """Check against obvious patterns"""
        for category, patterns in self.OBVIOUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Exact match = high confidence
                    words = message_lower.split()
                    if len(words) <= 3:  # Very short
                        confidence = 0.95
                    else:
                        confidence = 0.85
                    
                    return {
                        'type': 'SMALL_TALK',
                        'confidence': confidence,
                        'category': category,
                        'reasoning': [f'Matches {category} pattern']
                    }
        
        return {
            'type': 'UNKNOWN',
            'confidence': 0.0,
            'reasoning': []
        }
    
    def _check_complexity_markers(self, message_lower: str) -> int:
        """Count complexity markers"""
        score = 0
        
        # Check for question marks
        if '?' in message_lower:
            score += 1
        
        # Check for complexity keywords
        for keyword in self.COMPLEXITY_KEYWORDS:
            if keyword in message_lower:
                score += 1
        
        # Check for multiple sentences
        if message_lower.count('.') > 1 or message_lower.count('!') > 1:
            score += 1
        
        return score
    
    def _contains_critical_keywords(self, message_lower: str) -> bool:
        """Check for critical safety keywords"""
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in message_lower:
                return True
        return False
    
    def _analyze_with_nlp(self, message: str, message_lower: str) -> Dict:
        """Use spaCy for deeper analysis"""
        try:
            doc = self.nlp(message)
            reasoning = []
            confidence = 0.5  # Start neutral
            
            # Sentiment analysis (if available)
            if hasattr(doc, 'sentiment'):
                if abs(doc.sentiment) < 0.2:
                    confidence += 0.10
                    reasoning.append('Neutral sentiment')
                else:
                    confidence -= 0.10
                    reasoning.append('Emotional content detected')
            
            # Entity detection
            if len(doc.ents) > 0:
                confidence -= 0.15
                reasoning.append(f'Contains entities: {[e.text for e in doc.ents]}')
            
            # Dependency depth (complexity)
            max_depth = 0
            for token in doc:
                depth = abs(token.head.i - token.i)
                if depth > max_depth:
                    max_depth = depth
            
            if max_depth > 3:
                confidence -= 0.15
                reasoning.append('Complex sentence structure')
            else:
                confidence += 0.10
                reasoning.append('Simple sentence structure')
            
            # POS tags analysis
            verb_count = sum(1 for token in doc if token.pos_ == 'VERB')
            if verb_count > 2:
                confidence -= 0.10
                reasoning.append('Multiple verbs (complex action)')
            
            return {
                'confidence': max(0.0, min(1.0, confidence)),
                'reasoning': reasoning
            }
        
        except Exception as e:
            return {
                'confidence': 0.5,
                'reasoning': [f'NLP analysis failed: {str(e)}']
            }
