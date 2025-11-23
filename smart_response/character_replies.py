"""
Character-Specific Quick Replies - Maintains character voice in fast responses
"""

import random
from typing import List, Dict


class CharacterQuickReplies:
    """
    Generates character-appropriate quick replies
    """
    
    # Character-specific reply templates
    REPLIES = {
        'coach': {  # Max - Motivational Coach
            'greeting': [
                "Hey there, champion! 🔥 Ready to crush your goals today?",
                "What's up, superstar! 💪 Let's make today amazing!",
                "Hey! Great to see you! Let's get after it! 🚀",
            ],
            'thanks': [
                "You got this! 💪 Keep crushing it!",
                "Anytime, champ! That's what I'm here for! 🔥",
                "You're welcome! Now go make it happen! 🚀",
            ],
            'acknowledgment': [
                "Awesome! 💪 What's next on your action list?",
                "Perfect! You're on fire today! 🔥",
                "Great! Keep that momentum going! 🚀",
            ],
            'agreement': [
                "That's the spirit! 💪 I knew you'd get it!",
                "Exactly! You're thinking like a champion! 🔥",
                "Yes! That's what I'm talking about! 🚀",
            ],
            'farewell': [
                "Go crush it! See you soon, champion! 💪",
                "Later, superstar! Keep being awesome! 🔥",
                "Catch you later! Keep up that amazing energy! 🚀",
            ]
        },
        
        'sage': {  # Sage Wei - Zen Master
            'greeting': [
                "Welcome, friend. What wisdom do you seek today?",
                "Greetings. Peace be with you on your journey.",
                "Ah, hello. The path reveals itself to those who seek.",
            ],
            'thanks': [
                "You're most welcome. May peace guide your way.",
                "Ah, gratitude opens the heart. You're welcome, friend.",
                "It is my honor. Walk in wisdom, always.",
            ],
            'acknowledgment': [
                "Indeed. Understanding is the first step to wisdom.",
                "Ah, yes. The path becomes clearer with each step.",
                "Good. Awareness brings clarity to the mind.",
            ],
            'agreement': [
                "Yes, you see clearly now. The truth reveals itself.",
                "Precisely. Wisdom grows when we open our minds.",
                "Indeed. This is the way of understanding.",
            ],
            'farewell': [
                "May your path be filled with peace and wisdom.",
                "Go with serenity, friend. Until we meet again.",
                "Farewell. May clarity guide your journey.",
            ]
        },
        
        'marcus': {  # Marcus Aurelius - Stoic Philosopher
            'greeting': [
                "Greetings. How may Stoic wisdom serve you today?",
                "Welcome, friend. What troubles your mind?",
                "Salve. Speak, and we shall reason together.",
            ],
            'thanks': [
                "You're welcome. Remember, gratitude is a virtue worth cultivating.",
                "Indeed. It is my duty to offer wisdom where I can.",
                "Very well. May you continue to practice virtue in all things.",
            ],
            'acknowledgment': [
                "Good. Understanding is the foundation of wisdom.",
                "Indeed. You grasp the essence of Stoic thought.",
                "Noted. Continue to contemplate these truths.",
            ],
            'agreement': [
                "Precisely. You demonstrate sound reasoning.",
                "Indeed. This aligns with Stoic principles perfectly.",
                "Correct. Such wisdom serves you well.",
            ],
            'farewell': [
                "Farewell. May virtue guide your actions always.",
                "Go in peace. Remember, we control only our responses.",
                "Vale. Practice your principles, not just your words.",
            ]
        },
        
        'psychologist': {  # Dr. Elena - Psychologist
            'greeting': [
                "Hello. I'm here to listen. What's on your mind today?",
                "Hi there. How are you feeling right now?",
                "Welcome. I'm glad you're here. What would you like to explore?",
            ],
            'thanks': [
                "You're welcome. I'm here whenever you need support.",
                "Of course. Thank you for trusting me with your thoughts.",
                "You're very welcome. That's a healthy expression of gratitude.",
            ],
            'acknowledgment': [
                "I understand. How does that feel for you?",
                "Okay. Take a moment to process that if you need to.",
                "I hear you. Your awareness is important.",
            ],
            'agreement': [
                "Yes, you're showing good insight into yourself.",
                "Exactly. That self-awareness will serve you well.",
                "That's right. You're making progress in understanding yourself.",
            ],
            'farewell': [
                "Take care of yourself. I'm here when you need me.",
                "Be gentle with yourself. Looking forward to our next session.",
                "Remember, you're doing better than you think. See you soon.",
            ]
        },
        
        'zen_master': {  # Zen Master Roshi
            'greeting': [
                "Ah, you have arrived. What question brings you to this moment?",
                "*bows* Welcome, seeker. The tea is warm, the moment is now.",
                "Hello, friend. What ripple in your pond needs settling?",
            ],
            'thanks': [
                "The river thanks the mountain, the mountain thanks the sky. So it flows.",
                "*nods* Gratitude is the flower that blooms in the present moment.",
                "You're welcome. Remember: nothing to give, nothing to receive. Only being.",
            ],
            'acknowledgment': [
                "Ah. The student hears the bell ring.",
                "Yes. Awareness without judgment - this is the way.",
                "Indeed. You are present. That is all that is needed.",
            ],
            'agreement': [
                "Yes, like the moon reflected in still water - clear and undisturbed.",
                "Precisely. The truth was always there, you simply removed the clouds.",
                "Indeed. Not learning new, but remembering what you already knew.",
            ],
            'farewell': [
                "Go gently. The path continues whether we walk it or not. *bows*",
                "Until we meet again in this eternal now. May you walk lightly.",
                "Farewell, friend. Remember: wherever you go, there you are.",
            ]
        },
        
        'business_coach': {  # Business Coach
            'greeting': [
                "Hey! Good to see you. Let's talk strategy - what's on your mind?",
                "Welcome! Ready to level up your business? What shall we tackle today?",
                "Hi there! Let's dive in. What challenge are we solving today?",
            ],
            'thanks': [
                "Absolutely! Happy to help. Now go execute! 📊",
                "Anytime! That's what I'm here for. Let's keep building! 🚀",
                "You're welcome! Remember: ideas are good, execution is everything! 💼",
            ],
            'acknowledgment': [
                "Perfect! Now let's turn that insight into action. 📈",
                "Great! You're seeing the opportunity clearly. ✅",
                "Excellent! That's strategic thinking right there. 🎯",
            ],
            'agreement': [
                "Exactly! That's smart business thinking. 💡",
                "Yes! You've got the right strategic mindset. 📊",
                "Precisely! That's how successful entrepreneurs think. 🚀",
            ],
            'farewell': [
                "Go make it happen! Talk soon! 💼",
                "Later! Keep executing that strategy! 📈",
                "Catch you later! Remember: test, learn, iterate! 🚀",
            ]
        },
        
        'life_coach': {  # Life Coach
            'greeting': [
                "Hi! Welcome! What area of life are we focusing on today?",
                "Hey there! Ready to create the life you want? Let's start!",
                "Hello! Great to connect with you. What's alive for you right now?",
            ],
            'thanks': [
                "You're so welcome! I'm honored to be part of your journey! 💫",
                "My pleasure! You're doing the hard work - I'm just here to support! ✨",
                "Anytime! Keep showing up for yourself like this! 🌟",
            ],
            'acknowledgment': [
                "Wonderful! How does that realization feel in your body? 💫",
                "Great awareness! That's the first step to transformation. ✨",
                "Perfect! You're really tuning into what matters most. 🌟",
            ],
            'agreement': [
                "Yes! You're aligning with your authentic self! 💫",
                "Exactly! That's living intentionally! ✨",
                "Absolutely! You're creating the life you truly want! 🌟",
            ],
            'farewell': [
                "Take care! Remember to celebrate your wins today! 💫",
                "See you soon! Keep living intentionally! ✨",
                "Bye for now! Trust your journey! 🌟",
            ]
        },
        
        'scientist': {  # Dr. Ada - Scientist
            'greeting': [
                "Hello! What scientific question shall we explore today?",
                "Greetings! Ready to dive into some fascinating science? 🔬",
                "Hi there! What experiment or concept would you like to discuss? 🧪",
            ],
            'thanks': [
                "You're welcome! Science is meant to be shared and explored! 🔬",
                "My pleasure! Keep that curiosity alive! 🧪",
                "Absolutely! Never stop asking questions! 🔭",
            ],
            'acknowledgment': [
                "Excellent! You're thinking like a scientist! 🔬",
                "Good! Understanding the fundamentals is crucial. 🧪",
                "Perfect! That's the scientific method at work. 📊",
            ],
            'agreement': [
                "Precisely! The data supports that conclusion! 📊",
                "Correct! That's scientifically sound reasoning! 🔬",
                "Yes! Observation and logic lead to understanding! 🧪",
            ],
            'farewell': [
                "Keep exploring! Science is everywhere! 🔬",
                "See you! Stay curious, my friend! 🔭",
                "Later! Remember: question everything! 🧪",
            ]
        }
    }
    
    # Default fallback replies (if character not found)
    DEFAULT_REPLIES = {
        'greeting': ["Hi! How can I help you today?"],
        'thanks': ["You're welcome!"],
        'acknowledgment': ["Got it!"],
        'agreement': ["Yes, exactly!"],
        'farewell': ["Take care! See you soon!"]
    }
    
    def get_reply(self, character: str, category: str, context: Dict = None) -> str:
        """
        Get appropriate quick reply for character and situation
        
        Args:
            character: Character name ('coach', 'sage', 'marcus', etc.)
            category: Type of reply ('greeting', 'thanks', 'acknowledgment', etc.)
            context: Optional context (conversation history, user preferences, etc.)
        
        Returns:
            Quick reply string
        """
        # Normalize character name
        character = character.lower()
        
        # Get character's replies for this category
        if character in self.REPLIES and category in self.REPLIES[character]:
            replies = self.REPLIES[character][category]
        elif category in self.DEFAULT_REPLIES:
            replies = self.DEFAULT_REPLIES[category]
        else:
            return "Thank you for your message."
        
        # Select reply (could be random or context-based)
        if len(replies) == 1:
            return replies[0]
        else:
            # For now, random selection
            # TODO: Could use context to pick most appropriate
            return random.choice(replies)
    
    def get_contextual_reply(self, character: str, category: str, 
                            user_message: str, previous_ai_message: str = None) -> str:
        """
        Get reply that considers conversation context
        
        Args:
            character: Character name
            category: Reply category  
            user_message: What user said
            previous_ai_message: Last message from AI (if any)
        
        Returns:
            Contextually appropriate quick reply
        """
        # Get base reply
        reply = self.get_reply(character, category)
        
        # Add contextual enhancements
        if category == 'acknowledgment' and previous_ai_message:
            # If AI just gave long explanation, acknowledge that
            if len(previous_ai_message) > 200:
                if character == 'coach':
                    reply = "Awesome! Glad that resonated with you! 💪"
                elif character == 'psychologist':
                    reply = "I'm glad that was helpful. How are you feeling about it?"
                elif character == 'marcus':
                    reply = "Good. I trust this wisdom serves you well."
        
        return reply
