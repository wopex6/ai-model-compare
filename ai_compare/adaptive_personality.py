"""
Adaptive AI Personality System
Dynamically adjusts AI behavior based on user personality profile and ongoing interactions
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from .personality_profiler import PersonalityProfiler, PersonalityProfile, CommunicationStyle, LearningPreference, GoalOrientation

@dataclass
class InteractionAnalysis:
    """Analysis of user interaction patterns"""
    message_length_avg: float = 0.0
    question_frequency: float = 0.0
    technical_language_usage: float = 0.0
    emotional_indicators: Dict[str, float] = None
    response_time_preference: str = "medium"  # fast, medium, detailed
    feedback_preference: str = "balanced"  # direct, gentle, encouraging
    
    def __post_init__(self):
        if self.emotional_indicators is None:
            self.emotional_indicators = {}

class AdaptivePersonality:
    """AI personality that adapts to user characteristics and needs"""
    
    def __init__(self, user_id: str, profiler: PersonalityProfiler):
        self.user_id = user_id
        self.profiler = profiler
        self.profile = profiler.load_profile(user_id)
        self.interaction_history = []
        self.adaptation_settings = {}
        self.feedback_data = {}
        
        if self.profile:
            self.adaptation_settings = profiler.get_ai_adaptation_settings(self.profile)
        else:
            self.adaptation_settings = self._get_default_settings()
    
    def _get_default_settings(self) -> Dict:
        """Default AI behavior settings"""
        return {
            "response_style": "balanced",
            "detail_level": "medium",
            "encouragement_level": "medium",
            "formality": "casual",
            "explanation_style": "step_by_step",
            "interaction_style": "conversational",
            "use_examples": True,
            "reassurance_level": "medium"
        }
    
    def analyze_user_message(self, message: str, metadata: Dict = None) -> InteractionAnalysis:
        """Analyze user message for personality indicators"""
        analysis = InteractionAnalysis()
        
        # Message length analysis
        analysis.message_length_avg = len(message.split())
        
        # Question frequency
        question_marks = message.count('?')
        analysis.question_frequency = question_marks / max(len(message.split()), 1)
        
        # Technical language usage
        technical_terms = ['function', 'class', 'method', 'algorithm', 'implementation', 
                          'optimization', 'architecture', 'framework', 'library', 'API']
        tech_count = sum(1 for term in technical_terms if term.lower() in message.lower())
        analysis.technical_language_usage = tech_count / max(len(message.split()), 1)
        
        # Emotional indicators
        positive_words = ['great', 'awesome', 'excellent', 'love', 'amazing', 'perfect']
        negative_words = ['difficult', 'hard', 'confused', 'stuck', 'frustrated', 'problem']
        uncertainty_words = ['maybe', 'perhaps', 'not sure', 'think', 'might', 'possibly']
        
        analysis.emotional_indicators = {
            'positive': sum(1 for word in positive_words if word in message.lower()) / max(len(message.split()), 1),
            'negative': sum(1 for word in negative_words if word in message.lower()) / max(len(message.split()), 1),
            'uncertainty': sum(1 for word in uncertainty_words if word in message.lower()) / max(len(message.split()), 1)
        }
        
        # Response preference indicators
        if any(word in message.lower() for word in ['quick', 'brief', 'short', 'summary']):
            analysis.response_time_preference = "fast"
        elif any(word in message.lower() for word in ['detail', 'explain', 'elaborate', 'comprehensive']):
            analysis.response_time_preference = "detailed"
        
        return analysis
    
    def adapt_response_style(self, user_message: str, base_response: str) -> str:
        """Adapt AI response based on user personality and current interaction"""
        analysis = self.analyze_user_message(user_message)
        self.interaction_history.append(analysis)
        
        # Update profile based on interaction
        self._update_profile_from_interaction(analysis)
        
        # Apply personality-based adaptations
        adapted_response = self._apply_personality_adaptations(base_response, analysis)
        
        return adapted_response
    
    def _update_profile_from_interaction(self, analysis: InteractionAnalysis):
        """Update user profile based on interaction analysis"""
        if not self.profile:
            return
        
        # Adjust personality dimensions based on interaction patterns
        interaction_data = {
            'asks_many_questions': analysis.question_frequency > 0.1,
            'prefers_detailed_responses': analysis.response_time_preference == "detailed",
            'responds_quickly': analysis.message_length_avg < 10,
            'uses_technical_language': analysis.technical_language_usage > 0.05,
            'shows_uncertainty': analysis.emotional_indicators.get('uncertainty', 0) > 0.05,
            'shows_positivity': analysis.emotional_indicators.get('positive', 0) > 0.02
        }
        
        self.profiler.update_profile_from_interaction(self.user_id, interaction_data)
        
        # Reload updated profile
        self.profile = self.profiler.load_profile(self.user_id)
        if self.profile:
            self.adaptation_settings = self.profiler.get_ai_adaptation_settings(self.profile)
    
    def _apply_personality_adaptations(self, response: str, analysis: InteractionAnalysis) -> str:
        """Apply personality-based adaptations to response"""
        adapted_response = response
        
        # Apply communication style adaptations
        if self.adaptation_settings.get("response_style") == "concise":
            adapted_response = self._make_concise(adapted_response)
        elif self.adaptation_settings.get("response_style") == "encouraging":
            adapted_response = self._add_encouragement(adapted_response)
        
        # Apply detail level adaptations
        if self.adaptation_settings.get("detail_level") == "high" and analysis.response_time_preference == "detailed":
            adapted_response = self._add_details(adapted_response)
        elif self.adaptation_settings.get("detail_level") == "low" or analysis.response_time_preference == "fast":
            adapted_response = self._reduce_details(adapted_response)
        
        # Apply reassurance based on emotional state
        if analysis.emotional_indicators.get('uncertainty', 0) > 0.05:
            if self.adaptation_settings.get("reassurance_level") == "high":
                adapted_response = self._add_reassurance(adapted_response)
        
        # Apply formality adjustments
        if self.adaptation_settings.get("formality") == "professional":
            adapted_response = self._increase_formality(adapted_response)
        
        return adapted_response
    
    def _make_concise(self, response: str) -> str:
        """Make response more concise"""
        # Remove unnecessary phrases and get to the point
        concise_response = response.replace("I'd be happy to help you with that. ", "")
        concise_response = concise_response.replace("Let me explain this step by step. ", "")
        return concise_response
    
    def _add_encouragement(self, response: str) -> str:
        """Add encouraging elements to response"""
        encouraging_starters = [
            "Great question! ",
            "You're on the right track! ",
            "That's a smart approach! ",
            "Excellent thinking! "
        ]
        
        import random
        starter = random.choice(encouraging_starters)
        return starter + response
    
    def _add_details(self, response: str) -> str:
        """Add more detailed explanations"""
        if "because" not in response.lower() and "this is" not in response.lower():
            # Add explanatory context
            detailed_response = response + "\n\nThis approach works because it follows established patterns and best practices in the field."
        else:
            detailed_response = response
        
        return detailed_response
    
    def _reduce_details(self, response: str) -> str:
        """Reduce unnecessary details"""
        # Remove explanatory sentences
        sentences = response.split('. ')
        if len(sentences) > 2:
            # Keep first and last sentence, summarize middle
            reduced = sentences[0] + '. ' + sentences[-1]
        else:
            reduced = response
        
        return reduced
    
    def _add_reassurance(self, response: str) -> str:
        """Add reassuring elements for uncertain users"""
        reassuring_phrases = [
            "Don't worry, this is a common question. ",
            "This can be tricky at first, but you'll get it. ",
            "Many people find this challenging initially. ",
            "You're asking the right questions. "
        ]
        
        import random
        phrase = random.choice(reassuring_phrases)
        return phrase + response
    
    def _increase_formality(self, response: str) -> str:
        """Increase formality of response"""
        formal_response = response.replace("you're", "you are")
        formal_response = formal_response.replace("don't", "do not")
        formal_response = formal_response.replace("can't", "cannot")
        formal_response = formal_response.replace("won't", "will not")
        
        return formal_response
    
    def get_personality_feedback(self) -> Dict:
        """Generate feedback about current personality assessment"""
        if not self.profile:
            return {
                "status": "no_profile",
                "message": "No personality profile available. Consider taking the assessment.",
                "confidence": 0.0
            }
        
        feedback = {
            "status": self.profile.assessment_stage,
            "confidence": self.profile.confidence_level,
            "traits": {
                "communication_style": self.profile.communication_style.value,
                "learning_preference": self.profile.learning_preference.value,
                "goal_orientation": self.profile.goal_orientation.value
            },
            "adaptations": {
                "response_style": self.adaptation_settings.get("response_style", "balanced"),
                "detail_level": self.adaptation_settings.get("detail_level", "medium"),
                "interaction_style": self.adaptation_settings.get("interaction_style", "conversational")
            },
            "suggestions": []
        }
        
        # Add suggestions based on profile
        if self.profile.confidence_level < 0.5:
            feedback["suggestions"].append("Take more assessment questions to improve accuracy")
        
        if self.profile.interaction_count < 5:
            feedback["suggestions"].append("Continue conversations to refine personality understanding")
        
        # Recent interaction patterns
        if len(self.interaction_history) > 0:
            recent_analysis = self.interaction_history[-1]
            if recent_analysis.emotional_indicators.get('uncertainty', 0) > 0.1:
                feedback["suggestions"].append("AI is providing extra reassurance based on detected uncertainty")
        
        return feedback
    
    def should_suggest_assessment(self) -> bool:
        """Determine if user should be offered personality assessment"""
        if not self.profile:
            return True
        
        if self.profile.confidence_level < 0.3:
            return True
        
        if self.profile.interaction_count > 20 and self.profile.assessment_stage == "partial":
            return True
        
        return False
    
    def get_assessment_prompt(self) -> Dict:
        """Get personalized assessment prompt"""
        if not self.profile:
            return {
                "title": "Personality Assessment",
                "message": "I'd like to understand your communication preferences better to provide more helpful responses. This will take about 3-5 minutes and you can pause anytime.",
                "estimated_time": "3-5 minutes",
                "benefits": [
                    "More personalized responses",
                    "Better communication style matching",
                    "Improved learning experience"
                ]
            }
        else:
            return {
                "title": "Personality Assessment Update",
                "message": f"Based on our {self.profile.interaction_count} interactions, I'd like to refine my understanding of your preferences. This will take about 2-3 minutes.",
                "estimated_time": "2-3 minutes",
                "benefits": [
                    "More accurate personality matching",
                    "Better response adaptation",
                    "Enhanced conversation experience"
                ]
            }
