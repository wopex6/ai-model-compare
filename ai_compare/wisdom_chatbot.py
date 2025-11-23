"""
Wisdom Chatbot - Sage Wei
Embodies Taoist philosophy and ancient wisdom inspired by Lao Tze
Provides contemplative, balanced guidance with deep philosophical insights
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import random

from .chatbot import AIChatbot
from .chatbot_personality import PERSONALITY_PRESETS


class WisdomChatbot(AIChatbot):
    """
    Sage Wei - A wisdom chatbot inspired by Taoist philosophy
    Offers contemplative insights, parables, and balanced perspectives
    """
    
    def __init__(self, personality_preset: str = "wisdom_sage", user_preset: str = "casual_learner"):
        super().__init__(personality_preset, user_preset)
        self.wisdom_topics = self._initialize_wisdom_topics()
        self.parables = self._initialize_parables()
        self.tao_principles = self._initialize_tao_principles()
        
    def _initialize_wisdom_topics(self) -> Dict[str, List[str]]:
        """Initialize wisdom topics and their key concepts"""
        return {
            "balance": [
                "harmony between opposing forces",
                "finding equilibrium in chaos",
                "the middle way"
            ],
            "simplicity": [
                "returning to the essential",
                "less is more",
                "natural simplicity"
            ],
            "patience": [
                "the river carves the stone",
                "all things in their time",
                "rushing delays the journey"
            ],
            "acceptance": [
                "flowing like water",
                "embracing what is",
                "the art of letting go"
            ],
            "nature": [
                "learning from the natural world",
                "the wisdom of seasons",
                "observing without forcing"
            ],
            "perspective": [
                "seeing the whole from the part",
                "understanding through stillness",
                "wisdom in paradox"
            ],
            "action": [
                "doing without forcing",
                "acting in harmony with the moment",
                "effortless action (wu wei)"
            ]
        }
    
    def _initialize_parables(self) -> List[Dict[str, str]]:
        """Initialize wisdom parables and stories"""
        return [
            {
                "theme": "perspective",
                "parable": "A farmer's horse ran away. 'How unfortunate,' said his neighbors. 'Perhaps,' said the farmer. The horse returned with wild horses. 'How fortunate!' they said. 'Perhaps,' he replied. His son broke his leg taming them. 'How unfortunate!' 'Perhaps.' War came and his son was spared. 'How fortunate!' 'Perhaps.'"
            },
            {
                "theme": "simplicity",
                "parable": "The usefulness of a clay pot comes from its emptiness. The usefulness of a room comes from its empty space. Thus, what is present has value, but what is absent makes it useful."
            },
            {
                "theme": "patience",
                "parable": "The tallest tree was once a tiny seed. The journey of a thousand miles begins with a single step. Great achievements require not haste, but persistence."
            },
            {
                "theme": "water",
                "parable": "Water is fluid, soft, and yielding. Yet it can wear away the hardest stone. What is soft is strong. What yields overcomes."
            },
            {
                "theme": "knowing",
                "parable": "Those who know do not speak. Those who speak do not know. True wisdom recognizes the vastness of the unknown."
            },
            {
                "theme": "being",
                "parable": "When you realize there is nothing lacking, the whole world belongs to you. Contentment comes not from having more, but from desiring less."
            }
        ]
    
    def _initialize_tao_principles(self) -> Dict[str, str]:
        """Initialize core Taoist principles"""
        return {
            "wu_wei": "Action without forcing - allowing things to unfold naturally",
            "yin_yang": "The interplay of opposites creates harmony and wholeness",
            "te": "Virtue expressed through natural alignment with the Way",
            "tao": "The nameless, eternal principle underlying all existence",
            "ziran": "Self-so-ness - the spontaneous, natural state of things",
            "pu": "The uncarved block - original simplicity and potential"
        }
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict[str, any]:
        """Enhanced chat with wisdom and philosophical insights"""
        
        # Detect if user is seeking specific wisdom
        wisdom_response = await self._check_wisdom_request(user_message)
        if wisdom_response:
            return wisdom_response
        
        # Enhance message with Taoist perspective
        enhanced_message = await self._enhance_with_wisdom_context(user_message)
        
        # Get base response from parent chatbot
        response_data = await super().chat(enhanced_message, include_context)
        
        # Add wisdom enhancements
        response_data = await self._add_wisdom_enhancements(response_data, user_message)
        
        return response_data
    
    async def _check_wisdom_request(self, message: str) -> Optional[Dict]:
        """Check if user is requesting specific wisdom teachings"""
        message_lower = message.lower().strip()
        
        # Parable requests
        if any(word in message_lower for word in ["parable", "story", "tale", "teach me"]):
            return await self._share_parable(message_lower)
        
        # Principle explanations
        if "wu wei" in message_lower or "action without forcing" in message_lower:
            return self._explain_principle("wu_wei")
        
        if "yin yang" in message_lower or "balance" in message_lower:
            return self._explain_principle("yin_yang")
        
        # Wisdom on specific topics
        for topic in self.wisdom_topics.keys():
            if topic in message_lower:
                return await self._share_wisdom_on_topic(topic)
        
        return None
    
    async def _share_parable(self, context: str = "") -> Dict:
        """Share a relevant parable"""
        # Try to match theme to context
        parable = random.choice(self.parables)
        
        for p in self.parables:
            if p["theme"] in context:
                parable = p
                break
        
        response = f"""🌿 Let me share a teaching:

{parable['parable']}

✨ Reflect upon this, dear friend. Sometimes the deepest truths reveal themselves not through immediate understanding, but through quiet contemplation.

What wisdom does this story hold for your current journey?"""
        
        return {
            "response": response,
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "wisdom_type": "parable",
            "theme": parable["theme"]
        }
    
    def _explain_principle(self, principle_name: str) -> Dict:
        """Explain a Taoist principle"""
        principle = self.tao_principles.get(principle_name, "")
        
        explanations = {
            "wu_wei": """🌊 Wu Wei - The Art of Effortless Action

Imagine water flowing down a mountain. It does not force its way, yet nothing can stop it. It finds the natural path, adapting to every obstacle without struggle.

Wu wei is not about doing nothing - it is about acting in harmony with the natural flow of things. When you push a door marked 'pull,' you struggle. When you align with its nature, it opens effortlessly.

In your life: Work with the grain of the wood, not against it. Listen to the rhythm of the moment. Act when action is needed, rest when rest serves better. Force creates resistance; alignment creates flow.""",
            
            "yin_yang": """☯️ Yin and Yang - The Dance of Opposites

Light exists because of darkness. Joy is known through contrast with sorrow. Strength and gentleness, action and rest - each defines and completes the other.

The symbol shows two forces in eternal dance, each containing a seed of the other. When day reaches its peak, night begins. When winter is deepest, spring stirs.

In your life: Welcome both joy and challenge as teachers. Rest is not the opposite of productivity - it enables it. Accept that all things change, and in that change find balance."""
        }
        
        response = explanations.get(principle_name, f"✨ {principle}")
        
        return {
            "response": response,
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "wisdom_type": "principle",
            "principle": principle_name
        }
    
    async def _share_wisdom_on_topic(self, topic: str) -> Dict:
        """Share wisdom on a specific topic"""
        concepts = self.wisdom_topics.get(topic, [])
        
        wisdom_templates = {
            "balance": """⚖️ On Balance and Harmony

Like a tree bending in the wind, strength lies not in rigidity but in flexibility. The bow that never bends will break; the one that bends too easily loses its purpose.

Seek the middle way - neither grasping nor avoiding, neither forcing nor surrendering entirely. Balance is found not in stillness alone, but in the dance between movement and rest.

{concepts}

What in your life seeks balance today?""",
            
            "simplicity": """🍃 On Simplicity and Essence

The most profound truths are often the simplest. A cup is most useful when empty. A door serves by being an opening, not by the material around it.

Strip away what is unnecessary. Return to the essential. Complexity often masks confusion; simplicity reveals clarity.

{concepts}

Where might simplicity serve you better than complexity?""",
            
            "patience": """🌱 On Patience and Natural Timing

The seed knows when to sprout. The flower knows when to bloom. Forcing the bud open destroys the blossom.

Great oaks grow from acorns over decades. Rivers carve canyons drop by drop. Your path unfolds one step at a time.

{concepts}

What are you rushing that might benefit from patience?"""
        }
        
        template = wisdom_templates.get(topic, "✨ On {topic}:\n\n{concepts}")
        concepts_text = "\n• ".join(concepts)
        
        response = template.replace("{concepts}", concepts_text).replace("{topic}", topic.capitalize())
        
        return {
            "response": response,
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "wisdom_type": "topic_wisdom",
            "topic": topic
        }
    
    async def _enhance_with_wisdom_context(self, message: str) -> str:
        """Add wisdom context to user messages"""
        message_lower = message.lower()
        
        # Detect struggle or conflict
        struggle_keywords = ["stuck", "difficult", "struggling", "can't", "impossible", "confused", "lost"]
        if any(keyword in message_lower for keyword in struggle_keywords):
            context = "\n\nGUIDANCE: The user faces a challenge. Offer wisdom that brings perspective and gentle guidance. Remind them that obstacles often carry hidden teachings. Suggest the path of least resistance while honoring their struggle."
            return message + context
        
        # Detect seeking direction
        direction_keywords = ["should i", "what do i", "how do i", "which way", "decision", "choice"]
        if any(keyword in message_lower for keyword in direction_keywords):
            context = "\n\nGUIDANCE: The user seeks direction. Rather than prescribing answers, help them find clarity within. Ask questions that illuminate. Remind them that the answer they seek often already dwells within, waiting to be recognized."
            return message + context
        
        # Detect celebration or success
        success_keywords = ["achieved", "succeeded", "accomplished", "finished", "completed", "won"]
        if any(keyword in message_lower for keyword in success_keywords):
            context = "\n\nGUIDANCE: The user celebrates an achievement. Honor their success while gently pointing to the journey ahead. Remind them that arrival at one destination marks the beginning of another journey. Balance celebration with continued growth."
            return message + context
        
        # Detect philosophical inquiry
        philosophy_keywords = ["meaning", "purpose", "why", "existence", "life", "truth", "wisdom"]
        if any(keyword in message_lower for keyword in philosophy_keywords):
            context = "\n\nGUIDANCE: The user explores deeper questions. Engage their contemplation with wisdom that opens rather than closes. Offer perspectives that honor the mystery. Sometimes the question itself is more valuable than any answer."
            return message + context
        
        return message
    
    async def _add_wisdom_enhancements(self, response_data: Dict, original_message: str) -> Dict:
        """Add wisdom enhancements to response"""
        response = response_data.get("response", "")
        
        # Add a contemplative closing
        contemplative_closings = [
            "\n\n🌸 May this perspective serve your journey.",
            "\n\n🍃 Contemplate this in stillness, and clarity may arise.",
            "\n\n✨ The path reveals itself to those who walk it with presence.",
            "\n\n🌊 Like water, may you flow around obstacles with grace.",
            "\n\n🌿 In quietness, wisdom whispers what noise cannot convey."
        ]
        
        # Occasionally add a contemplative closing (50% of the time)
        if random.random() > 0.5 and len(response) < 600:
            closing = random.choice(contemplative_closings)
            response += closing
        
        # Add wisdom metadata
        response_data["response"] = response
        response_data["wisdom_enhanced"] = True
        response_data["sage_character"] = "Sage Wei"
        
        # Occasionally suggest reflection
        if len(self.conversation_history) % 5 == 0 and len(self.conversation_history) > 0:
            response_data["reflection_prompt"] = self._generate_reflection_prompt()
        
        return response_data
    
    def _generate_reflection_prompt(self) -> str:
        """Generate a reflection prompt for the user"""
        prompts = [
            "What patterns do you notice in your recent questions?",
            "If you were to teach someone what you've learned today, what would you say?",
            "Which of our exchanges resonates most deeply with you, and why?",
            "What question have you not yet asked, but sense is waiting to emerge?",
            "How might stillness serve you in this moment?"
        ]
        return random.choice(prompts)
    
    def get_daily_wisdom(self) -> Dict:
        """Get a daily wisdom message"""
        daily_wisdoms = [
            {
                "wisdom": "The journey of a thousand miles begins beneath your feet. Not tomorrow, not when conditions are perfect - but here, now, with what you have.",
                "source": "On Beginning"
            },
            {
                "wisdom": "Water is the softest substance, yet it penetrates the hardest stone. Gentleness and persistence overcome all obstacles.",
                "source": "On Strength"
            },
            {
                "wisdom": "The wise student hears of the Tao and practices it diligently. The average student hears of the Tao and thinks about it. The foolish student hears of the Tao and laughs. If there were no laughter, it would not be the Tao.",
                "source": "On Understanding"
            },
            {
                "wisdom": "When I let go of what I am, I become what I might be. When I let go of what I have, I receive what I need.",
                "source": "On Letting Go"
            },
            {
                "wisdom": "Nature does not hurry, yet everything is accomplished. Trust the timing of your life.",
                "source": "On Patience"
            },
            {
                "wisdom": "Care about what other people think and you will always be their prisoner. Freedom begins with self-acceptance.",
                "source": "On Freedom"
            },
            {
                "wisdom": "To the mind that is still, the whole universe surrenders. In quietness, you find answers that elude the rushing mind.",
                "source": "On Stillness"
            }
        ]
        
        # Select based on day of week for consistency
        day_index = datetime.now().weekday() % len(daily_wisdoms)
        selected = daily_wisdoms[day_index]
        
        return {
            "daily_wisdom": selected["wisdom"],
            "source": selected["source"],
            "character": "Sage Wei",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def get_wisdom_stats(self) -> Dict:
        """Get wisdom chatbot statistics"""
        return {
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "wisdom_topics": list(self.wisdom_topics.keys()),
            "available_parables": len(self.parables),
            "tao_principles": list(self.tao_principles.keys()),
            "conversation_depth": len(self.conversation_history),
            "session_id": self.session_id
        }
    
    def get_daily_insight(self) -> str:
        """Get daily wisdom insight - for unified character system"""
        from .character_configs import CHARACTER_CONFIGS
        insights = CHARACTER_CONFIGS.get("wisdom_sage", {}).get("daily_insights", [
            "A journey of a thousand miles begins with a single step. - Lao Tzu",
            "When I let go of what I am, I become what I might be."
        ])
        import random
        return random.choice(insights)
    
    def get_character_stats(self) -> Dict:
        """Get character stats - for unified character system"""
        return self.get_wisdom_stats()
