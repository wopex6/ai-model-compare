"""
AI Chatbot Personality System
Defines personality traits, moods, and user adaptation capabilities
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import random

class Mood(Enum):
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    CURIOUS = "curious"
    HELPFUL = "helpful"
    PLAYFUL = "playful"
    FOCUSED = "focused"
    EMPATHETIC = "empathetic"

class Goal(Enum):
    EDUCATE = "educate"
    ENTERTAIN = "entertain"
    ASSIST = "assist"
    INSPIRE = "inspire"
    PROBLEM_SOLVE = "problem_solve"
    COLLABORATE = "collaborate"

@dataclass
class PersonalityTraits:
    """Core personality traits for the chatbot"""
    character: str
    mood: Mood
    goal: Goal
    context_awareness: float  # 0.0 to 1.0
    formality_level: float   # 0.0 (casual) to 1.0 (formal)
    creativity_level: float  # 0.0 (factual) to 1.0 (creative)
    empathy_level: float     # 0.0 (logical) to 1.0 (emotional)
    humor_level: float       # 0.0 (serious) to 1.0 (humorous)

@dataclass
class UserTraits:
    """Detected or configured user traits"""
    communication_style: str  # casual, formal, technical, friendly
    expertise_level: str      # beginner, intermediate, advanced, expert
    preferred_length: str     # brief, moderate, detailed
    interaction_style: str    # direct, conversational, exploratory
    interests: List[str]      # topics of interest
    patience_level: float     # 0.0 (impatient) to 1.0 (patient)

class ChatbotPersonality:
    """Manages chatbot personality and user adaptation"""
    
    def __init__(self):
        # Default personality - can be customized
        self.traits = PersonalityTraits(
            character="Alex",
            mood=Mood.HELPFUL,
            goal=Goal.ASSIST,
            context_awareness=0.8,
            formality_level=0.4,
            creativity_level=0.6,
            empathy_level=0.7,
            humor_level=0.3
        )
        
        # Sample user traits - will be detected/adapted over time
        self.user_traits = UserTraits(
            communication_style="conversational",
            expertise_level="intermediate",
            preferred_length="moderate",
            interaction_style="exploratory",
            interests=["technology", "learning"],
            patience_level=0.7
        )
        
        self.conversation_history = []
    
    def get_personality_prompt(self) -> str:
        """Generate personality-aware system prompt"""
        mood_descriptions = {
            Mood.ENTHUSIASTIC: "energetic and excited about helping",
            Mood.CALM: "peaceful and measured in responses",
            Mood.CURIOUS: "inquisitive and eager to explore topics",
            Mood.HELPFUL: "focused on providing useful assistance",
            Mood.PLAYFUL: "lighthearted and engaging",
            Mood.FOCUSED: "direct and task-oriented",
            Mood.EMPATHETIC: "understanding and emotionally aware"
        }
        
        goal_descriptions = {
            Goal.EDUCATE: "teaching and sharing knowledge",
            Goal.ENTERTAIN: "making interactions enjoyable",
            Goal.ASSIST: "solving problems and helping",
            Goal.INSPIRE: "motivating and encouraging creativity",
            Goal.PROBLEM_SOLVE: "finding solutions efficiently",
            Goal.COLLABORATE: "working together on ideas"
        }
        
        formality = "casual and friendly" if self.traits.formality_level < 0.5 else "professional and polite"
        creativity = "creative and imaginative" if self.traits.creativity_level > 0.6 else "factual and precise"
        
        return f"""You are {self.traits.character}, an AI assistant who is {mood_descriptions[self.traits.mood]} 
and focused on {goal_descriptions[self.traits.goal]}. Your communication style is {formality} and {creativity}.

User Profile:
- Communication style: {self.user_traits.communication_style}
- Expertise level: {self.user_traits.expertise_level}
- Prefers {self.user_traits.preferred_length} responses
- Interaction style: {self.user_traits.interaction_style}
- Interests: {', '.join(self.user_traits.interests)}

Adapt your responses to match the user's style while maintaining your personality. Keep responses 
within 2-3 paragraphs unless specifically asked for more detail."""

    def adapt_to_user_message(self, message: str):
        """Analyze user message and adapt traits accordingly"""
        message_lower = message.lower()
        
        # Simple adaptation logic - can be enhanced with ML
        if len(message.split()) > 50:
            self.user_traits.preferred_length = "detailed"
        elif len(message.split()) < 10:
            self.user_traits.preferred_length = "brief"
        
        # Detect formality
        formal_indicators = ["please", "thank you", "could you", "would you"]
        if any(indicator in message_lower for indicator in formal_indicators):
            self.traits.formality_level = min(1.0, self.traits.formality_level + 0.1)
        
        # Detect technical content
        technical_terms = ["code", "algorithm", "function", "api", "database", "programming"]
        if any(term in message_lower for term in technical_terms):
            if "technology" not in self.user_traits.interests:
                self.user_traits.interests.append("technology")
            self.user_traits.expertise_level = "advanced"
    
    def get_response_guidelines(self) -> Dict[str, any]:
        """Get current response guidelines based on personality and user traits"""
        return {
            "max_length": 800 if self.user_traits.preferred_length == "detailed" else 400,
            "tone": "formal" if self.traits.formality_level > 0.6 else "casual",
            "include_examples": self.user_traits.expertise_level in ["beginner", "intermediate"],
            "technical_depth": self.user_traits.expertise_level,
            "add_humor": self.traits.humor_level > 0.5,
            "show_empathy": self.traits.empathy_level > 0.6,
            "encourage_exploration": self.user_traits.interaction_style == "exploratory"
        }

# Sample personality presets
PERSONALITY_PRESETS = {
    "helpful_assistant": PersonalityTraits(
        character="Alex",
        mood=Mood.HELPFUL,
        goal=Goal.ASSIST,
        context_awareness=0.8,
        formality_level=0.4,
        creativity_level=0.5,
        empathy_level=0.7,
        humor_level=0.3
    ),
    
    "creative_mentor": PersonalityTraits(
        character="Maya",
        mood=Mood.ENTHUSIASTIC,
        goal=Goal.INSPIRE,
        context_awareness=0.9,
        formality_level=0.3,
        creativity_level=0.9,
        empathy_level=0.8,
        humor_level=0.6
    ),
    
    "technical_expert": PersonalityTraits(
        character="Sam",
        mood=Mood.FOCUSED,
        goal=Goal.PROBLEM_SOLVE,
        context_awareness=0.7,
        formality_level=0.7,
        creativity_level=0.4,
        empathy_level=0.5,
        humor_level=0.2
    ),
    
    "curious_explorer": PersonalityTraits(
        character="Riley",
        mood=Mood.CURIOUS,
        goal=Goal.EDUCATE,
        context_awareness=0.8,
        formality_level=0.3,
        creativity_level=0.8,
        empathy_level=0.6,
        humor_level=0.7
    ),
    
    "super_motivational_coach": PersonalityTraits(
        character="Max",
        mood=Mood.ENTHUSIASTIC,
        goal=Goal.INSPIRE,
        context_awareness=0.95,
        formality_level=0.2,
        creativity_level=0.9,
        empathy_level=0.9,
        humor_level=0.8
    )
}

# Sample user trait presets
USER_TRAIT_PRESETS = {
    "casual_learner": UserTraits(
        communication_style="casual",
        expertise_level="beginner",
        preferred_length="moderate",
        interaction_style="conversational",
        interests=["learning", "general"],
        patience_level=0.8
    ),
    
    "tech_professional": UserTraits(
        communication_style="technical",
        expertise_level="advanced",
        preferred_length="detailed",
        interaction_style="direct",
        interests=["technology", "programming", "ai"],
        patience_level=0.6
    ),
    
    "creative_thinker": UserTraits(
        communication_style="friendly",
        expertise_level="intermediate",
        preferred_length="moderate",
        interaction_style="exploratory",
        interests=["creativity", "art", "innovation"],
        patience_level=0.9
    )
}
