"""
Base Chatbot - Core Processing Pipeline
Shared by all AI characters to ensure consistency and eliminate redundancy
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from abc import ABC, abstractmethod

from .compare import AICompare
from .chatbot_personality import ChatbotPersonality, PERSONALITY_PRESETS, USER_TRAIT_PRESETS
from .conversation_manager import ConversationManager
from .personality_profiler import PersonalityProfiler
from .adaptive_personality import AdaptivePersonality
from .tools import AITools, FunctionCallingParser


class BaseChatbot(ABC):
    """
    Base class for all AI chatbot characters
    Implements the core processing pipeline that all characters share
    """
    
    def __init__(self, personality_preset: str = "helpful_assistant", 
                 user_preset: str = "casual_learner", 
                 session_id: str = None):
        """
        Initialize base chatbot with shared components
        
        Args:
            personality_preset: Name of personality preset to use
            user_preset: Name of user trait preset to use
            session_id: Optional session ID to load existing session
        """
        # Initialize personality
        self.personality = ChatbotPersonality()
        if personality_preset in PERSONALITY_PRESETS:
            self.personality.traits = PERSONALITY_PRESETS[personality_preset]
        if user_preset in USER_TRAIT_PRESETS:
            self.personality.user_traits = USER_TRAIT_PRESETS[user_preset]
        
        # SHARED CORE COMPONENTS - Used by all characters
        self.ai_compare = AICompare()  # Single point of AI model communication
        self.conversation_manager = ConversationManager()  # Single conversation storage
        self.tools = AITools()  # Shared real-time data tools
        self.function_parser = FunctionCallingParser()  # Shared function parsing
        self.personality_profiler = PersonalityProfiler()  # Shared profiling
        
        # Session management
        if session_id:
            self.session_id = session_id
            self.load_session(session_id)
        else:
            self.session_id = self.conversation_manager.create_session(
                f"{self.personality.traits.character} Chat Session"
            )
        
        self.conversation_history = []
        self.adaptive_personality = AdaptivePersonality(self.session_id, self.personality_profiler)
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict[str, any]:
        """
        CORE PROCESSING PIPELINE - Shared by all characters
        
        This method defines the standard flow:
        1. Pre-process message (character-specific)
        2. Core AI processing (shared)
        3. Post-process response (character-specific)
        4. Save to database (shared)
        
        Args:
            user_message: User's input message
            include_context: Whether to include conversation history
            
        Returns:
            Dict with response and metadata
        """
        # STEP 1: Pre-processing (can be overridden by characters)
        preprocessed_message = await self._preprocess_message(user_message)
        
        # STEP 2: CORE AI PROCESSING (shared by all)
        response_data = await self._core_process(preprocessed_message, include_context)
        
        # STEP 3: Post-processing (can be enhanced by characters)
        final_response_data = await self._postprocess_response(response_data, user_message)
        
        # STEP 4: Save to database (shared by all)
        await self._save_conversation(user_message, final_response_data)
        
        return final_response_data
    
    async def _preprocess_message(self, user_message: str) -> str:
        """
        Pre-process user message before core processing
        Override in subclasses to add character-specific logic
        
        Args:
            user_message: Original user message
            
        Returns:
            Preprocessed message (may include context enhancements)
        """
        # Default: return message as-is
        # Characters can override to add their own context
        return user_message
    
    async def _core_process(self, enhanced_message: str, include_context: bool) -> Dict[str, any]:
        """
        CORE AI PROCESSING - SHARED BY ALL CHARACTERS
        This is the heart of the system and should NOT be overridden
        
        Args:
            enhanced_message: Pre-processed message
            include_context: Whether to include conversation history
            
        Returns:
            Dict with AI response and metadata
        """
        # Adapt personality based on message
        self.personality.adapt_to_user_message(enhanced_message)
        
        # Check for real-time data needs
        tool_enhanced_message, tool_results = self.function_parser.enhance_prompt_with_tools(
            enhanced_message, self.tools
        )
        
        # Build context-aware prompt with personality
        enhanced_prompt = self._build_enhanced_prompt(tool_enhanced_message, include_context)
        
        # Get response from AI models (Claude Sonnet 4.5 + others)
        model_responses = await self.ai_compare.ask_all(enhanced_prompt)
        
        # Consolidate responses from multiple models
        consolidated_response = model_responses.get('_auto_consolidated', '')
        if not consolidated_response:
            successful_responses = {
                k: v for k, v in model_responses.items() 
                if not k.startswith('_') and not v.startswith('Error:')
            }
            if successful_responses:
                consolidated_response = await self.ai_compare.consolidate_responses(successful_responses)
        
        # Apply personality filter
        base_response = self._apply_personality_filter(consolidated_response)
        
        # Apply adaptive personality adjustments
        final_response = self.adaptive_personality.adapt_response_style(
            enhanced_message, base_response
        )
        
        return {
            "response": final_response,
            "character": self.personality.traits.character,
            "mood": self.personality.traits.mood.value,
            "conversation_id": self.session_id,
            "response_metadata": {
                "models_used": len([r for r in model_responses.values() if not r.startswith('Error:')]),
                "response_length": len(final_response),
                "personality_adapted": True,
                "adaptive_personality_applied": True,
                "tools_used": tool_results is not None,
                "real_time_data": tool_results if tool_results else None
            },
            "personality_feedback": self.adaptive_personality.get_personality_feedback(),
            "raw_model_responses": model_responses if include_context else None
        }
    
    async def _postprocess_response(self, response_data: Dict, original_message: str) -> Dict:
        """
        Post-process AI response to add character-specific enhancements
        Override in subclasses to add character-specific touches
        
        Args:
            response_data: Response from core processing
            original_message: Original user message
            
        Returns:
            Enhanced response data
        """
        # Default: return response as-is
        # Characters can override to add their own enhancements
        return response_data
    
    async def _save_conversation(self, user_message: str, response_data: Dict):
        """
        Save conversation to database - SHARED BY ALL CHARACTERS
        This ensures consistent data storage
        
        Args:
            user_message: User's message
            response_data: AI's response data
        """
        # Save user message
        self.conversation_manager.save_message(
            self.session_id, "user", user_message,
            {"personality_adapted": True}
        )
        
        # Save assistant response
        self.conversation_manager.save_message(
            self.session_id, "assistant", response_data["response"],
            {
                "personality_state": {
                    "character": self.personality.traits.character,
                    "mood": self.personality.traits.mood.value,
                    "goal": self.personality.traits.goal.value
                },
                "model_responses": response_data["response_metadata"]["models_used"]
            }
        )
        
        # Update local history
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": response_data["response"],
            "personality_state": {
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value,
                "goal": self.personality.traits.goal.value
            }
        }
        self.conversation_history.append(conversation_entry)
    
    def _build_enhanced_prompt(self, user_message: str, include_context: bool) -> str:
        """
        Build personality and context-aware prompt - SHARED
        
        Args:
            user_message: User's message
            include_context: Whether to include conversation history
            
        Returns:
            Enhanced prompt for AI models
        """
        personality_prompt = self.personality.get_personality_prompt()
        guidelines = self.personality.get_response_guidelines()
        
        # Add conversation context if requested
        context = ""
        if include_context and self.conversation_history:
            recent_history = self.conversation_history[-3:]
            context = "\n\nRecent conversation context:\n"
            for entry in recent_history:
                context += f"User: {entry['user_message']}\n"
                context += f"You: {entry['bot_response'][:100]}...\n"
        
        # Build the enhanced prompt
        enhanced_prompt = f"""{personality_prompt}

Response Guidelines:
- Maximum length: {guidelines['max_length']} characters
- Tone: {guidelines['tone']}
- Technical depth: {guidelines['technical_depth']}
- Include examples: {guidelines['include_examples']}
- Show empathy: {guidelines['show_empathy']}
- Encourage exploration: {guidelines['encourage_exploration']}

{context}

Current user message: {user_message}

Please respond as {self.personality.traits.character} with the specified personality traits and guidelines."""

        return enhanced_prompt
    
    def _apply_personality_filter(self, response: str) -> str:
        """
        Apply personality-based filtering - SHARED
        
        Args:
            response: Raw AI response
            
        Returns:
            Personality-filtered response
        """
        if not response:
            return f"I'm {self.personality.traits.character}, and I'm here to help! Could you tell me more about what you're looking for?"
        
        guidelines = self.personality.get_response_guidelines()
        
        # Trim if too long
        if len(response) > guidelines['max_length']:
            sentences = response.split('. ')
            trimmed = ""
            for sentence in sentences:
                if len(trimmed + sentence + '. ') <= guidelines['max_length']:
                    trimmed += sentence + '. '
                else:
                    break
            response = trimmed.rstrip('. ') + '.' if trimmed else response[:guidelines['max_length']] + "..."
        
        # Add personality touches
        if self.personality.traits.humor_level > 0.6 and len(response) < guidelines['max_length'] - 50:
            humor_additions = [" 😊", " (just my two cents!)", " - hope that helps!", 
                             " Let me know what you think!", " Pretty cool, right?"]
            if not any(punct in response[-10:] for punct in ['!', '?', '😊']):
                response += humor_additions[hash(response) % len(humor_additions)]
        
        return response
    
    # SESSION MANAGEMENT - SHARED
    def load_session(self, session_id: str) -> bool:
        """Load existing conversation session"""
        session_data = self.conversation_manager.load_session(session_id)
        if session_data:
            self.session_id = session_id
            self.conversation_history = self.conversation_manager.get_conversation_history(session_id)
            return True
        return False
    
    def create_new_session(self) -> str:
        """Create new conversation session"""
        self.session_id = self.conversation_manager.create_session("chat")
        self.conversation_history = []
        return self.session_id
    
    def get_conversation_summary(self) -> Dict[str, any]:
        """Get summary of current conversation"""
        if not self.conversation_history:
            return {"summary": "No conversation yet", "message_count": 0, "session_id": self.session_id}
        
        total_messages = len(self.conversation_history)
        characters = [entry.get("personality_state", {}).get("character", "Unknown") 
                     for entry in self.conversation_history]
        most_common_character = max(set(characters), key=characters.count) if characters else "Unknown"
        
        return {
            "summary": f"Conversation with {total_messages} exchanges using primarily {most_common_character} personality",
            "message_count": total_messages,
            "session_id": self.session_id,
            "dominant_character": most_common_character,
            "conversation_start": self.conversation_history[0]["timestamp"] if self.conversation_history else None,
            "last_interaction": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
