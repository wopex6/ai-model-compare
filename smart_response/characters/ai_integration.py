"""
AI Integration for Domain Characters

Connects domain characters to AI providers (OpenAI, Anthropic, etc.)
for generating responses with character-specific personalities.
Includes automatic failover and admin error logging.
"""

import os
import sqlite3
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime
import json
import traceback

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


class AIProviderErrorLog:
    """Manages AI provider error logging for admin visibility"""
    
    def __init__(self, db_connection: sqlite3.Connection = None):
        self.db = db_connection
        self._ensure_table()
    
    def _ensure_table(self):
        """Create admin error log table if it doesn't exist"""
        if not self.db:
            return
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_provider_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    provider TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    error_code TEXT,
                    character_id TEXT,
                    user_id INTEGER,
                    request_context TEXT,
                    stack_trace TEXT,
                    resolved INTEGER DEFAULT 0,
                    admin_notes TEXT
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_errors_timestamp 
                ON ai_provider_errors(timestamp DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_errors_provider 
                ON ai_provider_errors(provider)
            ''')
            self.db.commit()
        except Exception as e:
            print(f"Warning: Could not create AI error log table: {e}")
    
    def log_error(self, provider: str, error_type: str, error_message: str,
                  error_code: str = None, character_id: str = None,
                  user_id: int = None, request_context: Dict = None):
        """Log an AI provider error for admin review"""
        if not self.db:
            print(f"[ADMIN ALERT] AI Provider Error: {provider} - {error_type}: {error_message}")
            return
        
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO ai_provider_errors 
                (provider, error_type, error_message, error_code, character_id, 
                 user_id, request_context, stack_trace)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                provider,
                error_type,
                error_message,
                error_code,
                character_id,
                user_id,
                json.dumps(request_context) if request_context else None,
                traceback.format_exc()
            ))
            self.db.commit()
            
            # Console notification for immediate visibility
            print(f"[ADMIN ALERT] AI Provider Error logged: {provider} - {error_type}")
            
        except Exception as e:
            print(f"Warning: Could not log AI error: {e}")
    
    def get_recent_errors(self, limit: int = 50, provider: str = None,
                          unresolved_only: bool = False) -> List[Dict]:
        """Get recent errors for admin review"""
        if not self.db:
            return []
        
        try:
            cursor = self.db.cursor()
            query = 'SELECT * FROM ai_provider_errors WHERE 1=1'
            params = []
            
            if provider:
                query += ' AND provider = ?'
                params.append(provider)
            if unresolved_only:
                query += ' AND resolved = 0'
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching AI errors: {e}")
            return []
    
    def mark_resolved(self, error_id: int, admin_notes: str = None) -> bool:
        """Mark an error as resolved"""
        if not self.db:
            return False
        
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                UPDATE ai_provider_errors 
                SET resolved = 1, admin_notes = ?
                WHERE id = ?
            ''', (admin_notes, error_id))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error marking AI error resolved: {e}")
            return False
    
    def get_error_stats(self) -> Dict:
        """Get error statistics for admin dashboard"""
        if not self.db:
            return {}
        
        try:
            cursor = self.db.cursor()
            stats = {}
            
            # Total errors
            cursor.execute('SELECT COUNT(*) FROM ai_provider_errors')
            stats['total_errors'] = cursor.fetchone()[0]
            
            # Unresolved errors
            cursor.execute('SELECT COUNT(*) FROM ai_provider_errors WHERE resolved = 0')
            stats['unresolved_errors'] = cursor.fetchone()[0]
            
            # Errors by provider
            cursor.execute('''
                SELECT provider, COUNT(*) as count 
                FROM ai_provider_errors 
                GROUP BY provider
            ''')
            stats['by_provider'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Errors in last 24 hours
            cursor.execute('''
                SELECT COUNT(*) FROM ai_provider_errors 
                WHERE timestamp > datetime('now', '-1 day')
            ''')
            stats['last_24h'] = cursor.fetchone()[0]
            
            return stats
        except Exception as e:
            print(f"Error getting AI error stats: {e}")
            return {}


class DomainCharacterAI:
    """
    AI integration layer for domain characters.
    
    Generates responses using AI with character-specific system prompts
    and style configurations.
    """
    
    def __init__(self, ai_budget_manager=None, db_connection: sqlite3.Connection = None):
        """
        Initialize AI integration.
        
        Args:
            ai_budget_manager: Optional AIBudgetManager for cost control
            db_connection: Database connection for error logging
        """
        self.ai_budget = ai_budget_manager
        self.db = db_connection
        self.openai_client = None
        self.anthropic_client = None
        self.error_log = AIProviderErrorLog(db_connection)
        
        # Provider health tracking for smart failover (all 4 configured providers)
        self.provider_status = {
            'openai': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
            'anthropic': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
            'google': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
            'grok': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False}
        }
        
        # Initialize available AI clients
        self._init_ai_clients()
    
    def _init_ai_clients(self):
        """Initialize AI provider clients"""
        # OpenAI
        if OPENAI_AVAILABLE:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                self.provider_status['openai']['available'] = True
                print("✓ OpenAI client initialized for domain characters")
        
        # Anthropic
        if ANTHROPIC_AVAILABLE:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                self.provider_status['anthropic']['available'] = True
                print("✓ Anthropic client initialized for domain characters")
        
        # Google (check if API key exists)
        google_key = os.environ.get('GOOGLE_API_KEY')
        if google_key:
            self.provider_status['google']['available'] = True
            print("✓ Google API key configured")
        
        # Grok (check if API key exists)
        grok_key = os.environ.get('GROK_API_KEY')
        if grok_key:
            self.provider_status['grok']['available'] = True
            print("✓ Grok API key configured")
    
    def _get_best_provider(self) -> str:
        """Determine best provider based on health status"""
        # Prefer Anthropic if both are healthy (due to OpenAI quota issues)
        if self.provider_status['anthropic']['healthy'] and self.anthropic_client:
            return 'anthropic'
        if self.provider_status['openai']['healthy'] and self.openai_client:
            return 'openai'
        # If both unhealthy, try the one with fewer consecutive failures
        if self.anthropic_client and self.openai_client:
            if self.provider_status['anthropic']['consecutive_failures'] <= \
               self.provider_status['openai']['consecutive_failures']:
                return 'anthropic'
            return 'openai'
        # Return whatever is available
        return 'anthropic' if self.anthropic_client else 'openai'
    
    def _mark_provider_error(self, provider: str, error: Exception, 
                             character_id: str = None, user_id: int = None):
        """Mark a provider as having an error and log it"""
        self.provider_status[provider]['consecutive_failures'] += 1
        self.provider_status[provider]['last_error'] = datetime.now()
        
        # Mark as unhealthy after 3 consecutive failures
        if self.provider_status[provider]['consecutive_failures'] >= 3:
            self.provider_status[provider]['healthy'] = False
            print(f"[ADMIN ALERT] {provider.upper()} marked unhealthy after 3 consecutive failures")
        
        # Determine error type and code
        error_str = str(error)
        error_type = 'unknown'
        error_code = None
        
        if '429' in error_str or 'quota' in error_str.lower():
            error_type = 'quota_exceeded'
            error_code = '429'
        elif '401' in error_str or 'auth' in error_str.lower():
            error_type = 'authentication'
            error_code = '401'
        elif '500' in error_str or '502' in error_str or '503' in error_str:
            error_type = 'server_error'
            error_code = error_str[:3] if error_str[:3].isdigit() else None
        elif 'timeout' in error_str.lower():
            error_type = 'timeout'
        elif 'rate' in error_str.lower():
            error_type = 'rate_limit'
        
        # Log to admin error log
        self.error_log.log_error(
            provider=provider,
            error_type=error_type,
            error_message=error_str[:500],  # Truncate long messages
            error_code=error_code,
            character_id=character_id,
            user_id=user_id
        )
    
    def _mark_provider_success(self, provider: str):
        """Mark a provider as successful, resetting failure count"""
        self.provider_status[provider]['consecutive_failures'] = 0
        self.provider_status[provider]['healthy'] = True
    
    def call_ai_direct(self, system_prompt: str, user_message: str, 
                       character_id: str = 'coordinator') -> Optional[str]:
        """
        Direct AI call without needing a character object.
        Used for generating context-aware prompts, greetings, etc.
        
        Args:
            system_prompt: System instructions for the AI
            user_message: The user message/request
            character_id: Optional character ID for logging
            
        Returns:
            AI-generated response string, or None on failure
        """
        # Auto-select best provider
        provider = self._get_best_provider()
        
        # Try providers with automatic failover
        providers_to_try = [provider]
        fallback = 'openai' if provider == 'anthropic' else 'anthropic'
        if fallback not in providers_to_try:
            providers_to_try.append(fallback)
        
        for try_provider in providers_to_try:
            try:
                if try_provider == 'anthropic' and self.anthropic_client:
                    response, metadata = self._generate_anthropic(system_prompt, user_message, {})
                    self._mark_provider_success('anthropic')
                    return response
                elif try_provider == 'openai' and self.openai_client:
                    response, metadata = self._generate_openai(system_prompt, user_message, {})
                    self._mark_provider_success('openai')
                    return response
            except Exception as e:
                print(f"[AI DIRECT] {try_provider} failed: {e}")
                self._mark_provider_error(try_provider, e, character_id, None)
                continue
        
        return None
    
    def generate_response(self, character: BaseCharacter, message: str, 
                         context: Dict, provider: str = None) -> CharacterResponse:
        """
        Generate AI response for a domain character with automatic failover.
        
        Args:
            character: The domain character instance
            message: User's message
            context: Conversation context
            provider: AI provider to use (None = auto-select best)
            
        Returns:
            CharacterResponse with AI-generated content
        """
        user_id = context.get('user_id')
        is_admin = context.get('is_admin', False)
        
        # Debug log admin status
        print(f"[AI-INTEGRATION] User {user_id} is_admin={is_admin} (from context)")
        
        # Check AI budget if available
        if self.ai_budget:
            allowed, deny_reason = self.ai_budget.can_make_ai_call(
                user_id=user_id,
                is_admin=is_admin,
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
        
        # Auto-select best provider if not specified
        if provider is None:
            provider = self._get_best_provider()
        
        # Try providers with automatic failover
        providers_to_try = [provider]
        # Add fallback provider
        fallback = 'openai' if provider == 'anthropic' else 'anthropic'
        if fallback not in providers_to_try:
            providers_to_try.append(fallback)
        
        ai_response = None
        ai_metadata = {}
        used_provider = None
        last_error = None
        
        for try_provider in providers_to_try:
            try:
                if try_provider == 'anthropic' and self.anthropic_client:
                    ai_response, ai_metadata = self._generate_anthropic(full_system_prompt, message, context)
                    used_provider = 'anthropic'
                    self._mark_provider_success('anthropic')
                    break
                elif try_provider == 'openai' and self.openai_client:
                    ai_response, ai_metadata = self._generate_openai(full_system_prompt, message, context)
                    used_provider = 'openai'
                    self._mark_provider_success('openai')
                    break
            except Exception as e:
                last_error = e
                print(f"[AI FAILOVER] {try_provider} failed: {e}")
                self._mark_provider_error(try_provider, e, character.character_id, user_id)
                # Continue to try next provider
                continue
        
        # If no AI response, use fallback
        if ai_response is None:
            if last_error:
                print(f"[ADMIN ALERT] All AI providers failed. Using fallback response.")
            ai_response = self._generate_fallback(character, message)
            used_provider = 'fallback'
        
        # Log AI call if budget manager available
        if self.ai_budget and used_provider != 'fallback':
            self.ai_budget.log_ai_call(
                call_type='domain_character',
                purpose=f'{character.character_id} chat',
                success=True,
                user_id=user_id,
                character=character.character_id,
                is_background=False,
                input_tokens=ai_metadata.get('input_tokens', 0),
                output_tokens=ai_metadata.get('output_tokens', 0),
                model=ai_metadata.get('model'),
                response_time_ms=ai_metadata.get('response_time_ms')
            )
        
        # Create character response
        concern_level = character.analyze_context(message, context)
        interpretation = character.interpret_context(message, context)
        
        # Generate summary for long responses (>300 chars)
        summary = None
        if ai_response and len(ai_response) > 300 and used_provider != 'fallback':
            summary = self._generate_summary(ai_response, used_provider)
        
        return CharacterResponse(
            character_id=character.character_id,
            display_name=character.display_name,
            content=ai_response,
            concern_level=concern_level,
            interpretation=interpretation,
            should_display=True,
            metadata={
                'provider': used_provider,
                'domain': getattr(character, 'domain', 'general'),
                'ai_generated': used_provider != 'fallback',
                'failover_used': used_provider != provider if provider else False,
                'summary': summary,
                'has_summary': summary is not None
            }
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
            user_profile = context.get('user_profile')
            if isinstance(user_profile, str):
                parts.append(f"\nUser context:\n{user_profile}")
            else:
                parts.append(f"\nUser context: {json.dumps(user_profile)}")
        
        # Reply context (WhatsApp-style - user is responding to a specific message)
        if context.get('reply_to'):
            reply_to = context['reply_to']
            sender = "your previous message" if reply_to.get('sender_type') == 'assistant' else "their previous message"
            parts.append(f"\n⚠️ IMPORTANT: The user is REPLYING to {sender}:")
            parts.append(f'"{reply_to.get("content", "")}"')
            parts.append("Address this specific context in your response.")
        
        # Recent conversation summary
        if context.get('conversation_summary'):
            parts.append(f"\nRecent conversation: {context['conversation_summary']}")
        
        # Goal coaching context (proactive engagement)
        if context.get('coaching_context'):
            parts.append(f"\n{context['coaching_context']}")
        
        # File attachments context (user-uploaded files for AI reference)
        if context.get('file_attachments'):
            parts.append(f"\n{context['file_attachments']}")
        
        # ADAPTIVE COMPANION CONTEXT - understanding implicit needs & adapting tone
        if context.get('adaptive_context'):
            ac = context['adaptive_context']
            
            # Response strategy based on implicit needs
            if ac.get('response_strategy'):
                parts.append(f"\n🎯 RESPONSE APPROACH:\n{ac['response_strategy']}")
            
            # Tone guidance based on user's style
            if ac.get('tone_guidance'):
                parts.append(f"\n💬 COMMUNICATION STYLE:\n{ac['tone_guidance']}")
            
            # Suggested micro-steps (if user is ready for action)
            if ac.get('suggested_micro_steps'):
                steps = ac['suggested_micro_steps']
                steps_text = "\n".join([f"  - {s['action']} ({s.get('time', '5 min')})" for s in steps[:3]])
                parts.append(f"\n✨ SMALL ACHIEVABLE STEPS you could suggest:\n{steps_text}")
                parts.append("(Only share these if appropriate - sometimes they just need to be heard first)")
        
        return "\n".join(parts)
    
    def _generate_openai(self, system_prompt: str, message: str, 
                        context: Dict) -> Tuple[str, Dict]:
        """Generate response using OpenAI. Returns (response, metadata)"""
        model = "gpt-4o-mini"  # Cost-effective model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # Add conversation history if available (use all provided history)
        history = context.get('message_history', [])
        if history:
            for hist_msg in history:
                messages.insert(-1, {
                    "role": hist_msg.get('role', 'user'),
                    "content": hist_msg.get('content', '')
                })
        
        # Token estimation for monitoring
        prompt_tokens = sum(len(m['content']) // 4 for m in messages)
        history_tokens = context.get('history_token_estimate', 0)
        print(f"[TOKENS] OpenAI request: ~{prompt_tokens} prompt tokens (history: ~{history_tokens})")
        
        import time
        start_time = time.time()
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Get actual token usage
        input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else 0
        output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else 0
        
        if input_tokens or output_tokens:
            print(f"[TOKENS] OpenAI actual: {input_tokens} in, {output_tokens} out ({response_time_ms}ms)")
        
        metadata = {
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'response_time_ms': response_time_ms
        }
        
        return response.choices[0].message.content, metadata
    
    def _generate_anthropic(self, system_prompt: str, message: str,
                           context: Dict) -> Tuple[str, Dict]:
        """Generate response using Anthropic Claude. Returns (response, metadata)"""
        model = "claude-3-haiku-20240307"  # Cost-effective model
        messages = [{"role": "user", "content": message}]
        
        # Add conversation history if available (use all provided history)
        history = context.get('message_history', [])
        if history:
            for hist_msg in history:
                role = "user" if hist_msg.get('role') == 'user' else "assistant"
                messages.insert(-1, {
                    "role": role,
                    "content": hist_msg.get('content', '')
                })
        
        # Token estimation for monitoring
        prompt_tokens = len(system_prompt) // 4 + sum(len(m['content']) // 4 for m in messages)
        history_tokens = context.get('history_token_estimate', 0)
        print(f"[TOKENS] Anthropic request: ~{prompt_tokens} prompt tokens (history: ~{history_tokens})")
        
        import time
        start_time = time.time()
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Get actual token usage
        input_tokens = response.usage.input_tokens if hasattr(response, 'usage') and response.usage else 0
        output_tokens = response.usage.output_tokens if hasattr(response, 'usage') and response.usage else 0
        
        if input_tokens or output_tokens:
            print(f"[TOKENS] Anthropic actual: {input_tokens} in, {output_tokens} out ({response_time_ms}ms)")
        
        metadata = {
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'response_time_ms': response_time_ms
        }
        
        return response.content[0].text, metadata
    
    def _generate_summary(self, full_response: str, provider: str) -> Optional[str]:
        """Generate a concise summary with action items from a long AI response"""
        try:
            summary_prompt = """Summarize the following response in 2-3 concise sentences. 
Focus on: 1) Key insight or answer, 2) Recommended next action (if any).
Keep it under 100 words. Be direct and actionable.

Response to summarize:
"""
            if provider == 'openai' and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a concise summarizer. Create brief, actionable summaries."},
                        {"role": "user", "content": summary_prompt + full_response}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            elif provider == 'anthropic' and self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    system="You are a concise summarizer. Create brief, actionable summaries.",
                    messages=[{"role": "user", "content": summary_prompt + full_response}]
                )
                return response.content[0].text.strip()
        except Exception as e:
            print(f"[SUMMARY] Failed to generate summary: {e}")
        return None
    
    def _generate_fallback(self, character: BaseCharacter, message: str) -> str:
        """Generate fallback response when no AI is available"""
        config = DOMAIN_CHARACTER_CONFIGS.get(character.character_id, {})
        display_name = config.get('display_name', 'Advisor')
        domain = config.get('domain', 'general')
        
        return f"[{display_name}] I notice this relates to {domain}. While I'm currently limited in my responses, I'm here to listen and support you. What aspect would you like to explore further?"


def create_ai_integration(ai_budget_manager=None, db_connection: sqlite3.Connection = None) -> DomainCharacterAI:
    """Create and return a DomainCharacterAI instance"""
    return DomainCharacterAI(ai_budget_manager, db_connection)
