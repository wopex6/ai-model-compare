"""
AI Chatbot System
Integrates personality system with model comparison for intelligent responses
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from .compare import AICompare
from .chatbot_personality import ChatbotPersonality, PERSONALITY_PRESETS, USER_TRAIT_PRESETS
from .conversation_manager import ConversationManager
from .personality_profiler import PersonalityProfiler
from .adaptive_personality import AdaptivePersonality
from .tools import AITools, FunctionCallingParser

class AIChatbot:
    """Main chatbot class that combines personality with model comparison"""
    
    def __init__(self, personality_preset: str = "helpful_assistant", user_preset: str = "casual_learner", session_id: str = None):
        self.personality = ChatbotPersonality()
        
        # Load personality preset if specified
        if personality_preset in PERSONALITY_PRESETS:
            self.personality.traits = PERSONALITY_PRESETS[personality_preset]
        
        # Load user trait preset if specified
        if user_preset in USER_TRAIT_PRESETS:
            self.personality.user_traits = USER_TRAIT_PRESETS[user_preset]
        
        self.ai_compare = AICompare()
        self.conversation_manager = ConversationManager()
        
        # Initialize tools for real-time data access
        self.tools = AITools()
        self.function_parser = FunctionCallingParser()
        
        # Initialize personality profiling system
        self.personality_profiler = PersonalityProfiler()
        self.adaptive_personality = None
        
        # Load existing session or create new one
        if session_id:
            self.session_id = session_id
            self.load_session(session_id)
        else:
            self.session_id = self.conversation_manager.create_session("AI Chatbot Session")
        
        self.conversation_history = []
        
        # Initialize adaptive personality for this session
        self.adaptive_personality = AdaptivePersonality(self.session_id, self.personality_profiler)
    
    async def chat(self, user_message: str, include_context: bool = True) -> Dict[str, any]:
        """
        Process user message and generate personality-aware response
        
        Args:
            user_message: The user's input message
            include_context: Whether to include conversation context
            
        Returns:
            Dict containing response, metadata, and conversation info
        """
        # Adapt personality based on user message
        self.personality.adapt_to_user_message(user_message)
        
        # Check if we need to use tools for real-time data
        enhanced_message, tool_results = self.function_parser.enhance_prompt_with_tools(user_message, self.tools)
        
        # Build context-aware prompt
        enhanced_prompt = self._build_enhanced_prompt(enhanced_message, include_context)
        
        # Get response from model comparison system
        model_responses = await self.ai_compare.ask_all(enhanced_prompt)
        
        # Extract consolidated response
        consolidated_response = model_responses.get('_auto_consolidated', '')
        
        # If no consolidated response, create one from available responses
        if not consolidated_response:
            successful_responses = {k: v for k, v in model_responses.items() 
                                  if not k.startswith('_') and not v.startswith('Error:')}
            
            if successful_responses:
                consolidated_response = await self.ai_compare.consolidate_responses(successful_responses)
        
        # Apply personality filter to response
        base_response = self._apply_personality_filter(consolidated_response)
        
        # Apply adaptive personality adjustments
        final_response = self.adaptive_personality.adapt_response_style(user_message, base_response)
        
        # Save messages to persistent storage
        self.conversation_manager.save_message(
            self.session_id, "user", user_message,
            {"personality_adapted": True}
        )
        self.conversation_manager.save_message(
            self.session_id, "assistant", final_response,
            {
                "personality_state": {
                    "character": self.personality.traits.character,
                    "mood": self.personality.traits.mood.value,
                    "goal": self.personality.traits.goal.value
                },
                "model_responses": len([r for r in model_responses.values() if not r.startswith('Error:')])
            }
        )
        
        # Update local conversation history for compatibility
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": final_response,
            "personality_state": {
                "character": self.personality.traits.character,
                "mood": self.personality.traits.mood.value,
                "goal": self.personality.traits.goal.value
            }
        }
        self.conversation_history.append(conversation_entry)
        
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
    
    def should_offer_assessment(self) -> bool:
        """Check if personality assessment should be offered to user"""
        return self.adaptive_personality.should_suggest_assessment()
    
    def get_assessment_prompt(self) -> Dict:
        """Get personality assessment prompt for user"""
        return self.adaptive_personality.get_assessment_prompt()
    
    def get_personality_feedback(self) -> Dict:
        """Get current personality feedback"""
        return self.adaptive_personality.get_personality_feedback()
    
    def _build_enhanced_prompt(self, user_message: str, include_context: bool) -> str:
        """Build personality and context-aware prompt"""
        personality_prompt = self.personality.get_personality_prompt()
        guidelines = self.personality.get_response_guidelines()
        
        # Add conversation context if requested and available
        context = ""
        if include_context and self.conversation_history:
            recent_history = self.conversation_history[-3:]  # Last 3 exchanges
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
        """Apply personality-based filtering and adjustments to response"""
        if not response:
            return f"I'm {self.personality.traits.character}, and I'm here to help! Could you tell me more about what you're looking for?"
        
        guidelines = self.personality.get_response_guidelines()
        
        # Trim response if too long
        if len(response) > guidelines['max_length']:
            # Find a good breaking point (sentence end)
            sentences = response.split('. ')
            trimmed = ""
            for sentence in sentences:
                if len(trimmed + sentence + '. ') <= guidelines['max_length']:
                    trimmed += sentence + '. '
                else:
                    break
            
            if trimmed:
                response = trimmed.rstrip('. ') + '.'
            else:
                response = response[:guidelines['max_length']] + "..."
        
        # Add personality touches based on traits
        if self.personality.traits.humor_level > 0.6 and len(response) < guidelines['max_length'] - 50:
            humor_additions = [
                " 😊", " (just my two cents!)", " - hope that helps!",
                " Let me know what you think!", " Pretty cool, right?"
            ]
            if not any(punct in response[-10:] for punct in ['!', '?', '😊']):
                response += humor_additions[hash(response) % len(humor_additions)]
        
        return response
    
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
    
    def change_personality(self, preset_name: str) -> bool:
        """Change chatbot personality to a different preset"""
        if preset_name in PERSONALITY_PRESETS:
            self.personality.traits = PERSONALITY_PRESETS[preset_name]
            return True
        return False
    
    def adjust_user_profile(self, **kwargs) -> None:
        """Manually adjust user traits"""
        for key, value in kwargs.items():
            if hasattr(self.personality.user_traits, key):
                setattr(self.personality.user_traits, key, value)
    
    async def get_personality_comparison(self, message: str) -> Dict[str, str]:
        """Get responses from different personality presets for comparison"""
        responses = {}
        original_traits = self.personality.traits
        
        for preset_name, traits in PERSONALITY_PRESETS.items():
            self.personality.traits = traits
            enhanced_prompt = self._build_enhanced_prompt(message, False)
            
            # Get consolidated response
            model_responses = await self.ai_compare.ask_all(enhanced_prompt)
            consolidated = model_responses.get('_auto_consolidated', '')
            
            if not consolidated:
                successful_responses = {k: v for k, v in model_responses.items() 
                                      if not k.startswith('_') and not v.startswith('Error:')}
                if successful_responses:
                    consolidated = await self.ai_compare.consolidate_responses(successful_responses)
            
            responses[preset_name] = self._apply_personality_filter(consolidated)
        
        # Restore original personality
        self.personality.traits = original_traits
        
        return responses
    
    def load_session(self, session_id: str) -> bool:
        """Load an existing conversation session."""
        session_data = self.conversation_manager.load_session(session_id)
        if session_data:
            self.session_id = session_id
            self.conversation_history = self.conversation_manager.get_conversation_history(session_id)
            return True
        return False
    
    def create_new_session(self) -> str:
        """Create a new conversation session."""
        self.session_id = self.conversation_manager.create_session("chat")
        self.conversation_history = []
        return self.session_id
    
    def list_sessions(self) -> List[Dict]:
        """List all available chat sessions."""
        return self.conversation_manager.list_sessions("chat")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        return self.conversation_manager.delete_session(session_id)
    
    def export_conversation(self, format: str = "json") -> Optional[str]:
        """Export current conversation."""
        return self.conversation_manager.export_session(self.session_id, format)
