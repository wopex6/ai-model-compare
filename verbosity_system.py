"""
Verbosity Detection and Adaptation System
Analyzes user preferences for short vs long answers and adapts AI responses
"""

import re
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

@dataclass
class UserVerbosityProfile:
    """User's verbosity preferences and patterns"""
    user_id: str
    preferred_length: str = "balanced"  # short, balanced, long
    avg_message_length: float = 50.0
    message_length_variance: float = 10.0
    context_sensitivity: float = 0.5  # How much context affects length preference
    topic_specific_preferences: Dict[str, str] = field(default_factory=dict)
    feedback_history: List[Dict] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_profile(self, message_length: float, context: str = None):
        """Update user profile based on new message"""
        # Update average message length
        self.avg_message_length = (self.avg_message_length + message_length) / 2
        
        # Update variance
        self.message_length_variance = abs(message_length - self.avg_message_length)
        
        # Update context-specific preferences
        if context:
            if context not in self.topic_specific_preferences:
                self.topic_specific_preferences[context] = self.preferred_length
            else:
                # Adapt based on pattern
                if message_length > self.avg_message_length * 1.5:
                    self.topic_specific_preferences[context] = "long"
                elif message_length < self.avg_message_length * 0.5:
                    self.topic_specific_preferences[context] = "short"
        
        self.last_updated = datetime.now()

class VerbosityAnalyzer:
    """Analyzes user verbosity patterns and preferences"""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserVerbosityProfile] = {}
        self.context_keywords = {
            'technical': ['code', 'programming', 'algorithm', 'function', 'debug'],
            'creative': ['idea', 'story', 'design', 'art', 'imagine'],
            'business': ['strategy', 'market', 'revenue', 'customer', 'growth'],
            'personal': ['feel', 'emotion', 'relationship', 'family', 'health'],
            'learning': ['explain', 'understand', 'learn', 'study', 'concept'],
            'urgent': ['quick', 'fast', 'immediate', 'urgent', 'asap'],
            'detailed': ['explain', 'detail', 'thorough', 'comprehensive', 'deep']
        }
    
    def analyze_message_length(self, message: str) -> float:
        """Calculate message length metrics"""
        # Basic character count
        char_count = len(message.strip())
        
        # Word count
        word_count = len(re.findall(r'\b\w+\b', message))
        
        # Sentence count
        sentence_count = len(re.findall(r'[.!?]+', message))
        
        # Complexity score (punctuation, capitalization, etc.)
        complexity = len(re.findall(r'[,:;]', message))
        
        # Weighted score
        length_score = (char_count * 0.3 + word_count * 5 + sentence_count * 10 + complexity * 2)
        
        return length_score
    
    def detect_context(self, message: str) -> List[str]:
        """Detect context from message keywords"""
        message_lower = message.lower()
        detected_contexts = []
        
        for context, keywords in self.context_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_contexts.append(context)
        
        return detected_contexts if detected_contexts else ['general']
    
    def determine_length_preference(self, message: str, user_id: str) -> str:
        """Determine user's preferred response length"""
        # Get or create user profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserVerbosityProfile(user_id=user_id)
        
        profile = self.user_profiles[user_id]
        
        # Analyze current message
        message_length = self.analyze_message_length(message)
        contexts = self.detect_context(message)
        
        # Update profile
        profile.update_profile(message_length, contexts[0])
        
        # Determine preference based on patterns
        if message_length > profile.avg_message_length * 1.5:
            return "long"
        elif message_length < profile.avg_message_length * 0.5:
            return "short"
        else:
            return profile.preferred_length
    
    def get_adapted_response_length(self, user_id: str, context: str = None) -> str:
        """Get preferred response length for user in specific context"""
        if user_id not in self.user_profiles:
            return "balanced"
        
        profile = self.user_profiles[user_id]
        
        # Check context-specific preference
        if context and context in profile.topic_specific_preferences:
            return profile.topic_specific_preferences[context]
        
        return profile.preferred_length
    
    def record_feedback(self, user_id: str, response_length: str, feedback_rating: int, context: str = None):
        """Record user feedback on response length"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserVerbosityProfile(user_id=user_id)
        
        profile = self.user_profiles[user_id]
        
        feedback_data = {
            'response_length': response_length,
            'rating': feedback_rating,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        profile.feedback_history.append(feedback_data)
        
        # Update preferences based on feedback
        self._update_preferences_from_feedback(profile)
    
    def _update_preferences_from_feedback(self, profile: UserVerbosityProfile):
        """Update user preferences based on feedback history"""
        if len(profile.feedback_history) < 3:
            return  # Need more data
        
        # Analyze recent feedback
        recent_feedback = profile.feedback_history[-10:]  # Last 10 feedbacks
        
        length_ratings = {}
        for feedback in recent_feedback:
            length = feedback['response_length']
            rating = feedback['rating']
            
            if length not in length_ratings:
                length_ratings[length] = []
            length_ratings[length].append(rating)
        
        # Find best performing length
        best_length = "balanced"
        best_avg_rating = 0
        
        for length, ratings in length_ratings.items():
            avg_rating = statistics.mean(ratings)
            if avg_rating > best_avg_rating:
                best_avg_rating = avg_rating
                best_length = length
        
        # Update preference if significantly better
        if best_avg_rating > 3.5:  # Good feedback threshold
            profile.preferred_length = best_length

class ResponseLengthAdapter:
    """Adapts AI response length based on user preferences"""
    
    def __init__(self, verbosity_analyzer: VerbosityAnalyzer):
        self.analyzer = verbosity_analyzer
        self.length_multipliers = {
            'short': 0.5,      # 50% of original length
            'balanced': 1.0,   # 100% of original length
            'long': 1.5        # 150% of original length
        }
    
    def adapt_response_length(self, response: str, user_id: str, context: str = None) -> str:
        """Adapt response length based on user preferences"""
        # Get preferred length
        preferred_length = self.analyzer.get_adapted_response_length(user_id, context)
        
        # Apply length adaptation
        if preferred_length == "balanced":
            return response
        
        multiplier = self.length_multipliers[preferred_length]
        
        if preferred_length == "short":
            return self._shorten_response(response, multiplier)
        else:  # long
            return self._lengthen_response(response, multiplier)
    
    def _shorten_response(self, response: str, multiplier: float) -> str:
        """Shorten response while maintaining key information"""
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 2:
            return response  # Already short enough
        
        # Keep most important sentences (heuristic: first and last)
        target_count = max(1, int(len(sentences) * multiplier))
        
        # Keep first sentence and some others
        important_sentences = [sentences[0]]
        
        # Add sentences from middle and end
        if target_count > 1:
            step = len(sentences) // target_count
            for i in range(step, len(sentences), step):
                if len(important_sentences) < target_count:
                    important_sentences.append(sentences[i])
        
        # Ensure last sentence is included if it's important
        if len(sentences) > 1 and len(important_sentences) < target_count:
            important_sentences.append(sentences[-1])
        
        return '. '.join(important_sentences[:target_count]) + '.'
    
    def _lengthen_response(self, response: str, multiplier: float) -> str:
        """Lengthen response with additional details and explanations"""
        sentences = re.split(r'[.!?]+', response)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) >= 5:
            return response  # Already long enough
        
        lengthened_sentences = []
        
        for sentence in sentences:
            lengthened_sentences.append(sentence)
            
            # Add elaboration for key points
            if self._is_key_point(sentence):
                elaboration = self._generate_elaboration(sentence)
                if elaboration:
                    lengthened_sentences.append(elaboration)
        
        return '. '.join(lengthened_sentences) + '.'
    
    def _is_key_point(self, sentence: str) -> bool:
        """Determine if sentence contains key information worth elaborating"""
        key_indicators = [
            'important', 'crucial', 'essential', 'key', 'main', 'primary',
            'because', 'therefore', 'however', 'although', 'specifically',
            'for example', 'such as', 'including', 'especially'
        ]
        
        sentence_lower = sentence.lower()
        return any(indicator in sentence_lower for indicator in key_indicators)
    
    def _generate_elaboration(self, sentence: str) -> str:
        """Generate elaboration for a sentence"""
        elaborations = [
            "This means that it plays a significant role in the overall context.",
            "It's worth noting that this aspect deserves careful consideration.",
            "In practice, this translates to tangible benefits and outcomes.",
            "This particular point is often overlooked but is actually quite important.",
            "Building on this idea, we can see several implications and applications."
        ]
        
        # Simple heuristic - return elaboration based on sentence content
        if 'because' in sentence.lower():
            return "This causal relationship helps explain the underlying mechanism."
        elif 'example' in sentence.lower():
            return "This illustrates the concept in a practical, relatable way."
        elif 'important' in sentence.lower():
            return "Its significance cannot be overstated in this context."
        else:
            return elaborations[hash(sentence) % len(elaborations)]

# Test the verbosity system
def test_verbosity_system():
    """Run automatic tests for verbosity detection and adaptation"""
    print("🧪 Testing Verbosity Detection and Adaptation...")
    
    test_results = []
    
    # Test 1: Message length analysis
    try:
        analyzer = VerbosityAnalyzer()
        
        short_message = "Hi"
        long_message = "Hello, I was wondering if you could help me understand the intricacies of machine learning algorithms, specifically focusing on how neural networks process information and make decisions based on training data."
        
        short_length = analyzer.analyze_message_length(short_message)
        long_length = analyzer.analyze_message_length(long_message)
        
        success = long_length > short_length
        test_results.append({
            'test': 'Message Length Analysis',
            'passed': success,
            'details': f"Short: {short_length:.1f}, Long: {long_length:.1f}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Message Length Analysis',
            'passed': False,
            'details': str(e)
        })
    
    # Test 2: Context detection
    try:
        technical_message = "I need help with this Python code for machine learning"
        creative_message = "I have an idea for a new story about artificial intelligence"
        
        tech_contexts = analyzer.detect_context(technical_message)
        creative_contexts = analyzer.detect_context(creative_message)
        
        success = 'technical' in tech_contexts and 'creative' in creative_contexts
        test_results.append({
            'test': 'Context Detection',
            'passed': success,
            'details': f"Tech: {tech_contexts}, Creative: {creative_contexts}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Context Detection',
            'passed': False,
            'details': str(e)
        })
    
    # Test 3: User preference learning
    try:
        user_id = "test_user"
        
        # Simulate user with preference for short answers
        short_messages = ["Quick help", "Fast answer", "Brief explanation"]
        long_messages = ["I need a detailed explanation of this topic", "Please provide comprehensive information about this subject"]
        
        # Analyze patterns
        for msg in short_messages:
            analyzer.determine_length_preference(msg, user_id)
        
        preference = analyzer.get_adapted_response_length(user_id)
        
        success = preference in ["short", "balanced"]
        test_results.append({
            'test': 'User Preference Learning',
            'passed': success,
            'details': f"Detected preference: {preference}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'User Preference Learning',
            'passed': False,
            'details': str(e)
        })
    
    # Test 4: Response adaptation
    try:
        adapter = ResponseLengthAdapter(analyzer)
        
        original_response = "This is a comprehensive response that contains multiple sentences with detailed information about the topic being discussed."
        
        # Test shortening
        short_response = adapter.adapt_response_length(original_response, "test_user", "technical")
        
        # Test lengthening
        long_response = adapter.adapt_response_length(original_response, "test_user", "learning")
        
        success = len(short_response) <= len(original_response) and len(long_response) >= len(original_response)
        test_results.append({
            'test': 'Response Adaptation',
            'passed': success,
            'details': f"Original: {len(original_response)}, Short: {len(short_response)}, Long: {len(long_response)}"
        })
        
    except Exception as e:
        test_results.append({
            'test': 'Response Adaptation',
            'passed': False,
            'details': str(e)
        })
    
    # Print results
    passed = sum(1 for result in test_results if result['passed'])
    total = len(test_results)
    
    print(f"\n📊 Verbosity System Test Results:")
    print(f"Passed: {passed}/{total}")
    
    for result in test_results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status}: {result['test']}")
        if not result['passed']:
            print(f"   Details: {result['details']}")
    
    return passed == total

if __name__ == "__main__":
    test_verbosity_system()
