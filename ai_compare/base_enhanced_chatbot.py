"""
Base Enhanced Chatbot - Common functionality for all specialized chatbots
Configuration-driven design to avoid redundancy and hard-coding
"""
from typing import Dict, List, Optional, Any
import random
import json
from pathlib import Path
from .chatbot import AIChatbot
from .knowledge_enhanced_chatbot import KnowledgeEnhancedMixin


class BaseEnhancedChatbot(KnowledgeEnhancedMixin, AIChatbot):
    """
    Base class for all enhanced chatbots with specialized knowledge and capabilities
    All character-specific logic is driven by configuration, not hard-coded
    """
    
    def __init__(self, 
                 character_id: str,
                 personality_preset: str,
                 user_preset: str = "casual_learner",
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize enhanced chatbot with configuration
        
        Args:
            character_id: Unique identifier for character (e.g., "zen_master")
            personality_preset: Personality preset key
            user_preset: User preset key
            config: Character configuration dictionary
        """
        super().__init__(personality_preset, user_preset)
        
        self.character_id = character_id
        self.config = config or {}
        
        # Setup knowledge system if available
        try:
            self.setup_knowledge(character_id)
            self._knowledge_enabled = True
        except ImportError as e:
            print(f"Knowledge system not available for {character_id}: {e}")
            self._knowledge_enabled = False
        
        # Load character-specific configuration
        self._load_character_config()
    
    def _load_character_config(self):
        """Load character configuration from config dict"""
        # Core character info
        self.display_name = self.config.get("display_name", "Assistant")
        self.tagline = self.config.get("tagline", "Here to help")
        self.description = self.config.get("description", "AI Assistant")
        
        # Specialized knowledge structures (all config-driven)
        self.approaches = self.config.get("approaches", {})
        self.concepts = self.config.get("concepts", {})
        self.strategies = self.config.get("strategies", {})
        self.exercises = self.config.get("exercises", {})
        self.insights = self.config.get("daily_insights", [])
        self.quick_topics = self.config.get("quick_topics", [])
        
        # Detection keywords (for topic classification)
        self.concept_keywords = self.config.get("concept_keywords", [])
        self.strategy_keywords = self.config.get("strategy_keywords", [])
        self.approach_keywords = self.config.get("approach_keywords", [])
        
        # Visual theme
        self.theme = self.config.get("theme", {
            "primary_color": "#4CAF50",
            "secondary_color": "#81C784",
            "icon": "fa-robot"
        })
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict:
        """
        Enhanced chat with specialized knowledge
        Detects topic area and provides appropriate responses
        """
        # Detect what type of inquiry this is
        topic_area = self._detect_topic_area(user_message)
        
        # Route to appropriate handler
        if topic_area == "concept_inquiry" and self.concepts:
            return await self._explain_concept(user_message)
        
        if topic_area == "strategy_request" and self.strategies:
            return await self._provide_strategy(user_message)
        
        if topic_area == "approach_question" and self.approaches:
            return await self._explain_approach(user_message)
        
        if topic_area == "exercise_request" and self.exercises:
            return await self._provide_exercise(user_message)
        
        # For general conversation, use knowledge-enhanced chat if available
        if self._knowledge_enabled:
            response = await self.chat_with_knowledge(user_message, include_context)
        else:
            response = await super().chat(user_message)
        
        # Add character-specific enhancement
        response = self._add_character_enhancement(response, user_message)
        
        return response
    
    def _detect_topic_area(self, message: str) -> str:
        """Detect what type of inquiry using configured keywords"""
        message_lower = message.lower()
        
        # Check for concept questions
        concept_triggers = ["what is", "explain", "define", "tell me about", "what does", "meaning of"]
        if any(trigger in message_lower for trigger in concept_triggers):
            if any(keyword in message_lower for keyword in self.concept_keywords):
                return "concept_inquiry"
        
        # Check for strategy/technique requests
        strategy_triggers = ["how do i", "help me", "what should i do", "how can i",
                            "strategies for", "techniques for", "dealing with", "ways to"]
        if any(trigger in message_lower for trigger in strategy_triggers):
            if any(keyword in message_lower for keyword in self.strategy_keywords):
                return "strategy_request"
        
        # Check for approach/method questions
        if any(keyword in message_lower for keyword in self.approach_keywords):
            return "approach_question"
        
        # Check for exercise requests
        exercise_triggers = ["exercise", "practice", "guide me", "walk me through"]
        if any(trigger in message_lower for trigger in exercise_triggers):
            return "exercise_request"
        
        return "general"
    
    async def _explain_concept(self, message: str) -> Dict:
        """Explain a concept from configured concepts"""
        message_lower = message.lower()
        
        # Find matching concept
        for concept_key, concept_info in self.concepts.items():
            concept_name = concept_info.get("name", concept_key.replace("_", " "))
            concept_aliases = concept_info.get("aliases", [])
            
            # Check if concept matches
            if (concept_name.lower() in message_lower or 
                concept_key in message_lower or
                any(alias.lower() in message_lower for alias in concept_aliases)):
                
                response = f"**{concept_name}**\n\n"
                response += f"{concept_info.get('description', '')}\n\n"
                
                # Add context if available
                if "context" in concept_info:
                    response += f"**Context**: {concept_info['context']}\n\n"
                
                # Add related concepts
                if "related" in concept_info:
                    response += "**Related concepts**: "
                    response += ", ".join(concept_info["related"]) + "\n\n"
                
                response += concept_info.get("closing", "Would you like to explore this further?")
                
                return {"response": response, "concept_explained": concept_key}
        
        # If no specific concept found, use knowledge-enhanced chat
        if self._knowledge_enabled:
            return await self.chat_with_knowledge(message)
        else:
            return await super().chat(message)
    
    async def _provide_strategy(self, message: str) -> Dict:
        """Provide strategy/technique from configured strategies (CONTEXT-AWARE)"""
        message_lower = message.lower()
        
        # Extract explicit context if present (prepended by Smart Response)
        context_data = self._extract_context_from_message(message)
        
        # Find matching strategy category
        for strategy_key, strategy_info in self.strategies.items():
            keywords = strategy_info.get("keywords", [])
            
            if any(keyword in message_lower for keyword in keywords):
                strategy_name = strategy_info.get("name", strategy_key.replace("_", " "))
                techniques = strategy_info.get("techniques", [])
                
                response = f"**{strategy_name}**\n\n"
                
                # Context-aware intro
                if context_data:
                    response += self._build_context_aware_intro(context_data, strategy_key)
                elif "intro" in strategy_info:
                    response += f"{strategy_info['intro']}\n\n"
                
                response += "**Here are some effective techniques:**\n\n"
                
                for i, technique in enumerate(techniques, 1):
                    if isinstance(technique, dict):
                        response += f"{i}. **{technique.get('name', '')}**: {technique.get('description', '')}\n"
                    else:
                        response += f"{i}. {technique}\n"
                
                if "note" in strategy_info:
                    response += f"\n**Note**: {strategy_info['note']}\n"
                
                # Context-aware closing
                if context_data and context_data.get('goal'):
                    response += f"\n💡 Remember: These strategies can help you stay focused on {context_data['goal']} while managing {context_data.get('emotion', 'stress')}."
                elif "closing" in strategy_info:
                    response += f"\n{strategy_info['closing']}"
                
                return {"response": response, "strategy_provided": strategy_key, "context_used": bool(context_data)}
        
        # General fallback
        if self._knowledge_enabled:
            return await self.chat_with_knowledge(message)
        else:
            return await super().chat(message)
    
    async def _explain_approach(self, message: str) -> Dict:
        """Explain an approach/method from configured approaches"""
        message_lower = message.lower()
        
        for approach_key, approach_info in self.approaches.items():
            approach_name = approach_info.get("name", approach_key.replace("_", " "))
            
            if (approach_name.lower() in message_lower or 
                approach_key.replace("_", " ") in message_lower):
                
                response = f"**{approach_name}**\n\n"
                response += f"**Focus**: {approach_info.get('focus', '')}\n\n"
                
                if "key_concepts" in approach_info:
                    response += "**Key Concepts**:\n"
                    for concept in approach_info["key_concepts"]:
                        response += f"• {concept}\n"
                    response += "\n"
                
                if "techniques" in approach_info:
                    response += "**Common Techniques**:\n"
                    for technique in approach_info["techniques"]:
                        response += f"• {technique}\n"
                    response += "\n"
                
                if "when_helpful" in approach_info:
                    response += f"**When it's helpful**: {approach_info['when_helpful']}\n\n"
                
                response += approach_info.get("closing", "Would you like to learn more?")
                
                return {"response": response, "approach_explained": approach_key}
        
        if self._knowledge_enabled:
            return await self.chat_with_knowledge(message)
        else:
            return await super().chat(message)
    
    async def _provide_exercise(self, message: str) -> Dict:
        """Provide an exercise from configured exercises"""
        message_lower = message.lower()
        
        # Find matching exercise
        for exercise_key, exercise_info in self.exercises.items():
            keywords = exercise_info.get("keywords", [])
            
            if any(keyword in message_lower for keyword in keywords):
                exercise_name = exercise_info.get("name", exercise_key.replace("_", " "))
                
                response = f"**{exercise_name}**\n\n"
                
                if "intro" in exercise_info:
                    response += f"{exercise_info['intro']}\n\n"
                
                if "steps" in exercise_info:
                    response += "**Steps**:\n"
                    for i, step in enumerate(exercise_info["steps"], 1):
                        response += f"{i}. {step}\n"
                    response += "\n"
                
                if "duration" in exercise_info:
                    response += f"**Duration**: {exercise_info['duration']}\n\n"
                
                if "benefits" in exercise_info:
                    response += f"**Benefits**: {exercise_info['benefits']}\n\n"
                
                response += exercise_info.get("closing", "Give it a try and let me know how it goes!")
                
                return {"response": response, "exercise_provided": exercise_key}
        
        if self._knowledge_enabled:
            return await self.chat_with_knowledge(message)
        else:
            return await super().chat(message)
    
    def _add_character_enhancement(self, response: Dict, user_message: str) -> Dict:
        """Add character-specific enhancements to responses"""
        original_response = response.get("response", "")
        
        # Add validation if emotional content detected
        if self._detect_emotions(user_message):
            validations = self.config.get("validations", [
                "I hear you. ",
                "I understand this is important to you. ",
                "Thank you for sharing. "
            ])
            if validations:
                validation = random.choice(validations)
                response["response"] = validation + original_response
        
        # Add closing message
        closings = self.config.get("closings", [])
        if closings:
            response["response"] += "\n\n" + random.choice(closings)
        
        return response
    
    def _detect_emotions(self, message: str) -> bool:
        """Detect if message contains emotional content"""
        emotion_words = self.config.get("emotion_keywords", [
            "feel", "feeling", "felt", "worried", "sad", "happy",
            "angry", "frustrated", "confused", "scared", "hurt"
        ])
        message_lower = message.lower()
        return any(word in message_lower for word in emotion_words)
    
    def _extract_context_from_message(self, message: str) -> Optional[Dict]:
        """
        Extract explicit context from message (prepended by Smart Response)
        Returns dict with emotion, goal, etc. or None if no context found
        """
        # Check if message contains the context marker
        if "USER'S EXPLICIT STATEMENTS" not in message:
            return None
        
        context = {}
        lines = message.split('\n')
        
        for line in lines:
            # Extract emotion
            if "emotional state:" in line.lower() or "current emotion:" in line.lower():
                emotion = line.split(':', 1)[1].strip()
                context['emotion'] = emotion
            
            # Extract goal
            if "goal:" in line.lower():
                goal = line.split(':', 1)[1].strip()
                context['goal'] = goal
            
            # Extract other context items
            if "preference:" in line.lower():
                preference = line.split(':', 1)[1].strip()
                context['preference'] = preference
        
        return context if context else None
    
    def _build_context_aware_intro(self, context_data: Dict, strategy_key: str) -> str:
        """
        Build a personalized intro based on user's explicit context
        """
        emotion = context_data.get('emotion', '')
        goal = context_data.get('goal', '')
        
        # Build personalized opening
        intro = ""
        
        if emotion and goal:
            intro = f"I can see you're dealing with {emotion} while working toward {goal}. That's a challenging combination, and it's completely understandable. "
        elif emotion:
            intro = f"I hear that you're experiencing {emotion}. "
        elif goal:
            intro = f"As you work toward {goal}, "
        
        # Add strategy-specific context
        if strategy_key == "anxiety":
            intro += "Here are evidence-based strategies specifically for managing anxiety:\n\n"
        elif strategy_key == "stress":
            intro += "Here are evidence-based techniques for stress management:\n\n"
        elif strategy_key == "depression":
            intro += "Here are evidence-based strategies that can help:\n\n"
        else:
            intro += "Here are some effective strategies:\n\n"
        
        return intro
    
    def get_daily_insight(self) -> str:
        """Get a daily insight from configured insights"""
        if self.insights:
            return random.choice(self.insights)
        return f"Welcome! I'm {self.display_name}, {self.tagline}"
    
    def get_character_stats(self) -> Dict:
        """Get statistics about the character"""
        stats = {
            "character_id": self.character_id,
            "display_name": self.display_name,
            "approaches_count": len(self.approaches),
            "concepts_count": len(self.concepts),
            "strategies_count": len(self.strategies),
            "exercises_count": len(self.exercises),
            "insights_count": len(self.insights)
        }
        
        # Add knowledge system stats if available
        if self._knowledge_enabled:
            knowledge_stats = self.get_knowledge_stats()
            stats.update(knowledge_stats)
        
        return stats
