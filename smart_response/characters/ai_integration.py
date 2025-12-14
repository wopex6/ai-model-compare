"""
AI Integration for Domain Characters

Connects domain characters to AI providers (OpenAI, Anthropic, etc.)
for generating responses with character-specific personalities.
"""

import os
from typing import Dict, Optional, Any
from datetime import datetime
import json

# AI Provider imports
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import BaseCharacter, DomainCharacter, CoordinatorCharacter, CharacterResponse
from .configs import DOMAIN_CHARACTER_CONFIGS


class DomainCharacterAI:
    """
    AI integration layer for domain characters.
    
    Generates responses using AI with character-specific system prompts
    and style configurations.
    """
    
    def __init__(self, ai_budget_manager=None):
        """
        Initialize AI integration.
        
        Args:
            ai_budget_manager: Optional AIBudgetManager for cost control
        """
        self.ai_budget = ai_budget_manager
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize available AI clients
        self._init_ai_clients()
    
    def _init_ai_clients(self):
        """Initialize AI provider clients"""
        # OpenAI
        if OPENAI_AVAILABLE:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                print("✓ OpenAI client initialized for domain characters")
        
        # Anthropic
        if ANTHROPIC_AVAILABLE:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                print("✓ Anthropic client initialized for domain characters")
    
    def generate_response(self, character: BaseCharacter, message: str, 
                         context: Dict, provider: str = 'openai') -> CharacterResponse:
        """
        Generate AI response for a domain character.
        
        Args:
            character: The domain character instance
            message: User's message
            context: Conversation context
            provider: AI provider to use ('openai' or 'anthropic')
            
        Returns:
            CharacterResponse with AI-generated content
        """
        # Check AI budget if available
        if self.ai_budget:
            user_id = context.get('user_id')
            allowed, deny_reason = self.ai_budget.can_make_ai_call(
                user_id=user_id,
                is_admin=False,
                is_background=False
            )
            if not allowed:
                return CharacterResponse(
                    character_id=character.character_id,
                    display_name=character.display_name,
                    content=f"I've reached my daily conversation limit. Please try again tomorrow!",
                    concern_level=0.0,
                    interpretation={},
                    should_display=True,
                    metadata={'budget_limited': True, 'reason': deny_reason}
                )
        
        # Get character config
        config = DOMAIN_CHARACTER_CONFIGS.get(character.character_id, {})
        system_prompt = config.get('system_prompt', '')
        
        # Build the full system prompt with style instructions
        full_system_prompt = self._build_system_prompt(character, system_prompt, context)
        
        # Generate response based on provider (prefer Anthropic due to OpenAI quota limits)
        try:
            if provider == 'anthropic' and self.anthropic_client:
                ai_response = self._generate_anthropic(full_system_prompt, message, context)
            elif provider == 'openai' and self.openai_client:
                ai_response = self._generate_openai(full_system_prompt, message, context)
            else:
                # Fallback to available provider - try Anthropic first
                if self.anthropic_client:
                    ai_response = self._generate_anthropic(full_system_prompt, message, context)
                elif self.openai_client:
                    ai_response = self._generate_openai(full_system_prompt, message, context)
                else:
                    ai_response = self._generate_fallback(character, message)
            
            # Log AI call if budget manager available
            if self.ai_budget:
                self.ai_budget.log_ai_call(
                    call_type='domain_character',
                    purpose=f'{character.character_id} chat',
                    success=True,
                    user_id=context.get('user_id'),
                    character=character.character_id,
                    is_background=False
                )
            
            # Create character response
            concern_level = character.analyze_context(message, context)
            interpretation = character.interpret_context(message, context)
            
            return CharacterResponse(
                character_id=character.character_id,
                display_name=character.display_name,
                content=ai_response,
                concern_level=concern_level,
                interpretation=interpretation,
                should_display=True,
                metadata={
                    'provider': provider,
                    'domain': getattr(character, 'domain', 'general'),
                    'ai_generated': True
                }
            )
            
        except Exception as e:
            print(f"Error generating AI response for {character.character_id}: {e}")
            
            # Log failed call
            if self.ai_budget:
                self.ai_budget.log_ai_call(
                    call_type='domain_character',
                    purpose=f'{character.character_id} chat (FAILED)',
                    success=False,
                    user_id=context.get('user_id'),
                    character=character.character_id,
                    is_background=False,
                    error_message=str(e)
                )
            
            return CharacterResponse(
                character_id=character.character_id,
                display_name=character.display_name,
                content=f"I apologize, but I encountered an issue. Please try again.",
                concern_level=0.0,
                interpretation={},
                should_display=True,
                metadata={'error': str(e)}
            )
    
    def _build_system_prompt(self, character: BaseCharacter, 
                            base_prompt: str, context: Dict) -> str:
        """Build the full system prompt with style and context"""
        parts = []
        
        # Base character prompt
        if base_prompt:
            parts.append(base_prompt)
        
        # Style instructions
        style_instructions = character.get_style_instructions()
        if style_instructions:
            parts.append(f"\nStyle: {style_instructions}")
        
        # Context information (if available)
        if context.get('user_profile'):
            parts.append(f"\nUser context: {json.dumps(context['user_profile'])}")
        
        # Recent conversation summary
        if context.get('conversation_summary'):
            parts.append(f"\nRecent conversation: {context['conversation_summary']}")
        
        return "\n".join(parts)
    
    def _generate_openai(self, system_prompt: str, message: str, 
                        context: Dict) -> str:
        """Generate response using OpenAI"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Add conversation history if available
        history = context.get('message_history', [])
        if history:
            # Insert history before the current message
            for hist_msg in history[-6:]:  # Last 3 exchanges
                messages.insert(-1, {
                    "role": hist_msg.get('role', 'user'),
                    "content": hist_msg.get('content', '')
                })
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def _generate_anthropic(self, system_prompt: str, message: str,
                           context: Dict) -> str:
        """Generate response using Anthropic Claude"""
        messages = [{"role": "user", "content": message}]
        
        # Add conversation history if available
        history = context.get('message_history', [])
        if history:
            for hist_msg in history[-6:]:
                role = "user" if hist_msg.get('role') == 'user' else "assistant"
                messages.insert(-1, {
                    "role": role,
                    "content": hist_msg.get('content', '')
                })
        
        response = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",  # Cost-effective model
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
    
    def _generate_fallback(self, character: BaseCharacter, message: str) -> str:
        """Generate fallback response when no AI is available"""
        config = DOMAIN_CHARACTER_CONFIGS.get(character.character_id, {})
        display_name = config.get('display_name', 'Advisor')
        domain = config.get('domain', 'general')
        
        return f"[{display_name}] I notice this relates to {domain}. While I'm currently limited in my responses, I'm here to listen and support you. What aspect would you like to explore further?"


def create_ai_integration(ai_budget_manager=None) -> DomainCharacterAI:
    """Create and return a DomainCharacterAI instance"""
    return DomainCharacterAI(ai_budget_manager)
