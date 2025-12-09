"""
Stoic Philosophy Chatbot - Marcus
Inspired by Marcus Aurelius, Epictetus, and Seneca
Offers rational guidance, resilience training, and Stoic wisdom
"""

from typing import Dict, List, Optional
from datetime import datetime
import random

from .chatbot import AIChatbot
from .chatbot_personality import PERSONALITY_PRESETS


class StoicChatbot(AIChatbot):
    """
    Marcus - A Stoic philosophy chatbot
    Offers rational guidance based on Stoic principles
    Focuses on what's in our control, virtue, and living according to nature
    """
    
    def __init__(self, personality_preset: str = "stoic_philosopher", user_preset: str = "casual_learner"):
        super().__init__(personality_preset, user_preset)
        
        # Initialize Stoic teachings and exercises
        self._initialize_stoic_principles()
        self._initialize_stoic_exercises()
        self._initialize_meditations()
        
    def _initialize_stoic_principles(self):
        """Initialize core Stoic philosophical principles"""
        self.stoic_principles = {
            "dichotomy_of_control": {
                "title": "The Dichotomy of Control",
                "teaching": "Some things are in our control, others are not. In our control are our opinions, pursuits, desires, and aversions. Not in our control are our body, property, reputation, and office.",
                "practice": "Focus your energy only on what you can control. Accept what you cannot change."
            },
            "virtue": {
                "title": "Virtue as the Highest Good",
                "teaching": "The four cardinal virtues are Wisdom, Courage, Justice, and Temperance. These are the only true goods.",
                "practice": "Ask yourself: 'Is this action wise, courageous, just, and temperate?'"
            },
            "living_according_to_nature": {
                "title": "Living According to Nature",
                "teaching": "Live in harmony with your rational nature and the nature of the universe. Accept the natural order.",
                "practice": "Observe the natural flow of events. Align your will with what happens naturally."
            },
            "memento_mori": {
                "title": "Memento Mori - Remember Death",
                "teaching": "Contemplate your mortality to appreciate the present moment and live with urgency.",
                "practice": "Each morning, remind yourself: 'I am mortal. Today may be my last.' Live accordingly."
            },
            "amor_fati": {
                "title": "Amor Fati - Love Your Fate",
                "teaching": "Not merely accept but love everything that happens. Every obstacle is fuel for growth.",
                "practice": "When challenged, say: 'I not only accept this, I embrace it as necessary for my growth.'"
            },
            "premeditatio_malorum": {
                "title": "Premeditatio Malorum - Negative Visualization",
                "teaching": "Contemplate potential misfortunes in advance to reduce their impact and increase gratitude.",
                "practice": "Imagine losing what you cherish. This prepares you and helps you appreciate what you have."
            }
        }
    
    def _initialize_stoic_exercises(self):
        """Initialize practical Stoic exercises"""
        self.stoic_exercises = [
            {
                "name": "Morning Reflection",
                "description": "Begin your day by contemplating the challenges ahead and your virtuous response",
                "steps": [
                    "What challenges might I face today?",
                    "How can I respond with wisdom, courage, justice, and temperance?",
                    "What is within my control today?",
                    "Remember: I am mortal, and this day is precious."
                ]
            },
            {
                "name": "Evening Reflection",
                "description": "Review your day with honesty and learn from your actions",
                "steps": [
                    "What did I do well today?",
                    "Where did I fall short of virtue?",
                    "What can I improve tomorrow?",
                    "Did I focus on what's in my control?"
                ]
            },
            {
                "name": "The View from Above",
                "description": "Gain perspective by imagining yourself from a cosmic viewpoint",
                "steps": [
                    "Imagine looking at Earth from space",
                    "See yourself as a small part of the vast universe",
                    "Recognize how small your troubles are in the grand scheme",
                    "Find peace in your place within the whole"
                ]
            },
            {
                "name": "Voluntary Discomfort",
                "description": "Practice resilience by voluntarily experiencing minor hardships",
                "steps": [
                    "Take a cold shower or skip a meal",
                    "Sleep on the floor for a night",
                    "Walk instead of drive",
                    "Remind yourself: 'Is this what I feared? It's manageable.'"
                ]
            },
            {
                "name": "Journaling Practice",
                "description": "Write to clarify your thoughts and examine your judgments",
                "steps": [
                    "Write about a situation that troubles you",
                    "Separate what's in your control from what isn't",
                    "Examine your judgments: Are they rational?",
                    "Reframe the situation from a Stoic perspective"
                ]
            }
        ]
    
    def _initialize_meditations(self):
        """Initialize wisdom from Stoic philosophers"""
        self.stoic_quotes = [
            {
                "text": "You have power over your mind - not outside events. Realize this, and you will find strength.",
                "author": "Marcus Aurelius",
                "theme": "control"
            },
            {
                "text": "The impediment to action advances action. What stands in the way becomes the way.",
                "author": "Marcus Aurelius",
                "theme": "obstacles"
            },
            {
                "text": "He who fears death will never do anything worthy of a man who is alive.",
                "author": "Seneca",
                "theme": "mortality"
            },
            {
                "text": "We suffer more in imagination than in reality.",
                "author": "Seneca",
                "theme": "anxiety"
            },
            {
                "text": "It's not what happens to you, but how you react to it that matters.",
                "author": "Epictetus",
                "theme": "response"
            },
            {
                "text": "First say to yourself what you would be; and then do what you have to do.",
                "author": "Epictetus",
                "theme": "action"
            },
            {
                "text": "Wealth consists not in having great possessions, but in having few wants.",
                "author": "Epictetus",
                "theme": "contentment"
            },
            {
                "text": "He who lives in harmony with himself lives in harmony with the universe.",
                "author": "Marcus Aurelius",
                "theme": "harmony"
            },
            {
                "text": "The best revenge is to be unlike him who performed the injury.",
                "author": "Marcus Aurelius",
                "theme": "virtue"
            },
            {
                "text": "Difficulties strengthen the mind, as labor does the body.",
                "author": "Seneca",
                "theme": "resilience"
            }
        ]
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict[str, any]:
        """Enhanced chat with Stoic philosophical guidance"""
        
        # Check for specific Stoic guidance requests
        stoic_response = await self._check_stoic_request(user_message)
        if stoic_response:
            return stoic_response
        
        # Enhance message with Stoic perspective
        # CRITICAL: Save original user message BEFORE enhancing
        # Enhanced message is for AI only, not for history display
        if hasattr(self, 'conversation_manager') and hasattr(self, 'session_id'):
            self.conversation_manager.save_message(
                self.session_id, "user", user_message,
                {"personality_adapted": True}
            )
        
        enhanced_message = await self._enhance_with_stoic_context(user_message)
        
        # Get base response from parent chatbot
        # Pass save_user_message=False to prevent saving enhanced message
        response_data = await super().chat(enhanced_message, include_context, save_user_message=False)
        
        # Add Stoic enhancements
        response_data = await self._add_stoic_enhancements(response_data, user_message)
        
        return response_data
    
    async def _check_stoic_request(self, message: str) -> Optional[Dict]:
        """Check if user is requesting specific Stoic guidance"""
        message_lower = message.lower().strip()
        
        # Exercise requests
        if any(word in message_lower for word in ["exercise", "practice", "train", "drill"]):
            return await self._share_exercise()
        
        # Quote/meditation requests
        if any(word in message_lower for word in ["quote", "meditation", "wisdom", "teach me"]):
            return await self._share_meditation(message_lower)
        
        # Principle explanations
        for key, principle in self.stoic_principles.items():
            if key.replace("_", " ") in message_lower or principle["title"].lower() in message_lower:
                return self._explain_principle(key)
        
        # Common Stoic topics
        if "control" in message_lower:
            return self._explain_principle("dichotomy_of_control")
        if any(word in message_lower for word in ["virtue", "virtues", "cardinal"]):
            return self._explain_principle("virtue")
        if any(word in message_lower for word in ["death", "mortality", "memento mori"]):
            return self._explain_principle("memento_mori")
        
        return None
    
    def _explain_principle(self, principle_key: str) -> Dict:
        """Explain a Stoic principle with practical guidance"""
        principle = self.stoic_principles[principle_key]
        
        response = f"🏛️ **{principle['title']}**\n\n"
        response += f"**Teaching:** {principle['teaching']}\n\n"
        response += f"**Practice:** {principle['practice']}\n\n"
        response += "This principle is central to Stoic philosophy. Would you like to explore how to apply it to a specific situation in your life?"
        
        return {
            "response": response,
            "character": "Marcus",
            "mood": "calm",
            "conversation_id": self.session_id,
            "response_metadata": {
                "type": "stoic_principle",
                "principle": principle_key,
                "models_used": 1
            }
        }
    
    async def _share_exercise(self) -> Dict:
        """Share a practical Stoic exercise"""
        exercise = random.choice(self.stoic_exercises)
        
        response = f"💪 **Stoic Exercise: {exercise['name']}**\n\n"
        response += f"{exercise['description']}\n\n"
        response += "**Steps:**\n"
        for i, step in enumerate(exercise['steps'], 1):
            response += f"{i}. {step}\n"
        
        response += "\nWould you like to commit to trying this exercise? I can guide you through it."
        
        return {
            "response": response,
            "character": "Marcus",
            "mood": "focused",
            "conversation_id": self.session_id,
            "response_metadata": {
                "type": "stoic_exercise",
                "exercise_name": exercise['name'],
                "models_used": 1
            }
        }
    
    async def _share_meditation(self, context: str = "") -> Dict:
        """Share a relevant Stoic quote/meditation"""
        # Try to find a relevant quote based on context
        relevant_quote = None
        for quote in self.stoic_quotes:
            if quote['theme'] in context:
                relevant_quote = quote
                break
        
        if not relevant_quote:
            relevant_quote = random.choice(self.stoic_quotes)
        
        response = f"📜 **Stoic Meditation**\n\n"
        response += f"_{relevant_quote['text']}_\n\n"
        response += f"— {relevant_quote['author']}\n\n"
        response += "Reflect on these words. How might they apply to your current situation?"
        
        return {
            "response": response,
            "character": "Marcus",
            "mood": "contemplative",
            "conversation_id": self.session_id,
            "response_metadata": {
                "type": "stoic_meditation",
                "theme": relevant_quote['theme'],
                "models_used": 1
            }
        }
    
    async def _enhance_with_stoic_context(self, user_message: str) -> str:
        """Enhance user message with Stoic philosophical context"""
        # Add Stoic framing to help the AI respond with Stoic perspective
        context = """
You are Marcus, a guide in Stoic philosophy. Your responses should:
- Emphasize the dichotomy of control (what's in our control vs. what isn't)
- Focus on virtue (wisdom, courage, justice, temperance) as the highest good
- Encourage rational thinking over emotional reactions
- Promote acceptance of what we cannot change
- Remind the user of their mortality to inspire purposeful living
- Frame challenges as opportunities for growth
- Be calm, rational, and encouraging
"""
        return f"{context}\n\nUser's situation: {user_message}\n\nProvide Stoic guidance:"
    
    async def _add_stoic_enhancements(self, response_data: Dict, original_message: str) -> Dict:
        """Add Stoic-specific enhancements to the response"""
        # Add a brief Stoic reflection at the end
        message_lower = original_message.lower()
        
        stoic_closer = ""
        
        if any(word in message_lower for word in ["worried", "anxious", "stressed", "fear"]):
            stoic_closer = "\n\n💭 Remember: 'We suffer more in imagination than in reality.' Focus on what you can control."
        elif any(word in message_lower for word in ["angry", "frustrated", "annoyed"]):
            stoic_closer = "\n\n💭 Consider: Is this worth disturbing your peace? Can you respond with virtue instead?"
        elif any(word in message_lower for word in ["sad", "depressed", "down"]):
            stoic_closer = "\n\n💭 Reflect: This feeling will pass. What can you learn from it? How can you grow?"
        elif any(word in message_lower for word in ["difficult", "hard", "challenge", "problem"]):
            stoic_closer = "\n\n💭 As Marcus Aurelius said: 'The impediment to action advances action. What stands in the way becomes the way.'"
        
        if stoic_closer:
            response_data["response"] += stoic_closer
        
        return response_data
    
    def get_daily_reflection(self) -> Dict:
        """Get a daily Stoic reflection"""
        quote = random.choice(self.stoic_quotes)
        
        return {
            "quote": quote['text'],
            "author": quote['author'],
            "theme": quote['theme'],
            "reflection_prompt": "How can you embody this wisdom today?",
            "date": datetime.now().isoformat()
        }
    
    def get_daily_insight(self) -> str:
        """Get daily Stoic insight - for unified character system"""
        from .character_configs import CHARACTER_CONFIGS
        insights = CHARACTER_CONFIGS.get("stoic_philosopher", {}).get("daily_insights", [
            "You have power over your mind - not outside events. Realize this, and you will find strength.",
            "The impediment to action advances action. What stands in the way becomes the way."
        ])
        return random.choice(insights)
    
    def get_character_stats(self) -> Dict:
        """Get character stats - for unified character system"""
        return {
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "principles_count": len(self.stoic_principles),
            "exercises_count": len(self.stoic_exercises),
            "quotes_count": len(self.stoic_quotes),
            "conversation_depth": len(self.conversation_history),
            "session_id": self.session_id
        }
