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
    
    # Providers that cost nothing (local/self-hosted). These are ALWAYS exempt
    # from the AI budget — both the pre-call limit check and post-call logging.
    # Add any future free/local providers here.
    FREE_PROVIDERS = frozenset({'ollama'})
    
    @classmethod
    def _is_free_provider(cls, provider: str) -> bool:
        """Return True if the provider is free/local and exempt from budget."""
        return provider in cls.FREE_PROVIDERS
    
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
        
        # Provider health tracking for smart failover
        self.provider_status = {
            'openai': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
            'anthropic': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
            'google': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
            'grok': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
            # Ollama: free, local, no API key required
            'ollama': {'healthy': True, 'last_error': None, 'consecutive_failures': 0, 'available': False},
        }
        
        # Ollama config (free local models). Auto-detected if the server is running.
        # Default to Chinese-capable DeepSeek/Qwen first, then general Llama as fallback.
        ollama_model_env = os.environ.get('OLLAMA_MODEL', 'deepseek-r1,qwen2.5,llama3.2')
        self.ollama_config = {
            'host': os.environ.get('OLLAMA_HOST', 'http://localhost:11434'),
            'models': [m.strip() for m in ollama_model_env.split(',') if m.strip()],
            'timeout': int(os.environ.get('OLLAMA_TIMEOUT', '45')),
            'max_tokens': int(os.environ.get('OLLAMA_MAX_TOKENS', '512')),
        }
        self.ollama_available = False
        
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
        
        # Ollama (free, local models — no API key). Auto-detected if reachable.
        if os.environ.get('OLLAMA_ENABLED', '1').lower() not in ('0', 'false', 'no'):
            if self._check_ollama():
                self.ollama_available = True
                self.provider_status['ollama']['available'] = True
                print(f"✓ Ollama available ({', '.join(self.ollama_config['models'])} @ {self.ollama_config['host']})")
    
    def _check_ollama(self) -> bool:
        """Check whether a local Ollama server is reachable (short timeout)."""
        try:
            import urllib.request
            url = self.ollama_config['host'].rstrip('/') + '/api/tags'
            with urllib.request.urlopen(url, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    def _build_provider_chain(self, primary: str) -> List[str]:
        """
        Build an ordered, de-duplicated list of usable providers to try.
        Cloud providers first, then Ollama (free/local) as a last resort so it
        never changes existing behavior unless the cloud providers are down.
        """
        candidate_order = [primary, 'anthropic', 'openai', 'ollama']
        chain = []
        for p in candidate_order:
            if p in chain:
                continue
            if p == 'anthropic' and self.anthropic_client:
                chain.append(p)
            elif p == 'openai' and self.openai_client:
                chain.append(p)
            elif p == 'ollama' and self.ollama_available:
                chain.append(p)
        return chain
    
    def _get_best_provider(self) -> str:
        """Determine best provider based on health status"""
        # Opt-in: prefer the free local model to minimize cost.
        prefer_free = os.environ.get('AI_PREFER_FREE', '').lower() in ('1', 'true', 'yes')
        if prefer_free and self.ollama_available and self.provider_status['ollama']['healthy']:
            return 'ollama'
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
        # Return whatever cloud client is available, else fall back to free Ollama
        if self.anthropic_client:
            return 'anthropic'
        if self.openai_client:
            return 'openai'
        return 'ollama' if self.ollama_available else 'anthropic'
    
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
        
        # Real-time quota alert — print prominent warning and publish to Event Bus
        if error_type == 'quota_exceeded':
            print(f"\n{'!'*60}")
            print(f"🚨 QUOTA EXCEEDED: {provider.upper()}")
            print(f"   Error: {error_str[:200]}")
            print(f"   ACTION REQUIRED: Please top up {provider} API credits!")
            print(f"{'!'*60}\n")
            
            # Publish to Event Bus if available
            try:
                from agents.event_bus import get_global_bus
                bus = get_global_bus()
                if bus:
                    bus.publish_async('health.critical', {
                        'alert': f'QUOTA EXCEEDED: {provider.upper()} — top up credits immediately',
                        'provider': provider,
                        'error': error_str[:200],
                        'character_id': character_id,
                    }, source='ai_integration.quota_alert')
            except ImportError:
                pass
    
    def _mark_provider_success(self, provider: str):
        """Mark a provider as successful, resetting failure count"""
        self.provider_status[provider]['consecutive_failures'] = 0
        self.provider_status[provider]['healthy'] = True
    
    def call_ai_direct(self, system_prompt: str, user_message: str, 
                       character_id: str = 'coordinator',
                       context: Dict = None,
                       count_budget: bool = False,
                       user_id: int = None,
                       is_admin: bool = False) -> Optional[str]:
        """
        Direct AI call without needing a character object.
        Used for generating context-aware prompts, greetings, deliberation, etc.
        
        Args:
            system_prompt: System instructions for the AI
            user_message: The user message/request
            character_id: Optional character ID for logging
            context: Optional context dict. Supports 'max_tokens_override' to
                     raise the output cap (e.g. for batched multi-agent calls).
            count_budget: When True, this call is checked against and logged to
                     the AI budget (PAID providers only; free/local exempt).
                     Used by Teams/deliberation so their calls respect the cap.
            user_id: User id for budget accounting.
            is_admin: Whether the caller is an admin (higher budget).
            
        Returns:
            AI-generated response string, or None on failure
        """
        context = context or {}
        # Auto-select best provider
        provider = self._get_best_provider()
        
        # Budget gate — only for PAID providers when counting is requested.
        force_free = False
        if count_budget and self.ai_budget and not self._is_free_provider(provider):
            allowed, deny_reason = self.ai_budget.can_make_ai_call(
                user_id=user_id, is_admin=is_admin, is_background=False
            )
            if not allowed:
                if self.ollama_available:
                    print("[BUDGET] Paid budget exhausted — deliberation degrading to free Ollama.")
                    provider = 'ollama'
                    force_free = True
                else:
                    print("[BUDGET] Paid budget exhausted and no free provider — deliberation call refused.")
                    return None
        
        # Try providers with automatic failover (Ollama included as free fallback)
        providers_to_try = self._build_provider_chain(provider)
        if force_free:
            providers_to_try = [p for p in providers_to_try if self._is_free_provider(p)]
        
        for try_provider in providers_to_try:
            try:
                response, metadata, used = None, {}, None
                if try_provider == 'anthropic' and self.anthropic_client:
                    response, metadata = self._generate_anthropic(system_prompt, user_message, context)
                    used = 'anthropic'
                elif try_provider == 'openai' and self.openai_client:
                    response, metadata = self._generate_openai(system_prompt, user_message, context)
                    used = 'openai'
                elif try_provider == 'ollama' and self.ollama_available:
                    response, metadata = self._generate_ollama(system_prompt, user_message, context)
                    used = 'ollama'
                else:
                    continue
                
                self._mark_provider_success(used)
                # Log against budget only for paid providers when requested.
                if count_budget and self.ai_budget and not self._is_free_provider(used):
                    self.ai_budget.log_ai_call(
                        call_type='deliberation',
                        purpose=character_id,
                        success=True,
                        user_id=user_id,
                        character=character_id,
                        is_background=False,
                        input_tokens=metadata.get('input_tokens', 0),
                        output_tokens=metadata.get('output_tokens', 0),
                        model=metadata.get('model'),
                        response_time_ms=metadata.get('response_time_ms')
                    )
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
        
        # Decide provider first so free/local models can be exempted from budget
        if provider is None:
            provider = self._get_best_provider()
        
        # Check AI budget — but only for PAID providers. Free/local providers
        # (e.g. Ollama) are always allowed and never counted.
        force_free = False
        if self.ai_budget and not self._is_free_provider(provider):
            allowed, deny_reason = self.ai_budget.can_make_ai_call(
                user_id=user_id,
                is_admin=is_admin,
                is_background=False
            )
            if not allowed:
                # Paid budget exhausted: degrade to a free local model if we have
                # one, otherwise inform the user of the limit.
                if self.ollama_available:
                    print("[BUDGET] Paid AI budget exhausted — degrading to free Ollama.")
                    provider = 'ollama'
                    force_free = True
                else:
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
        
        # Try providers with automatic failover (Ollama included as free fallback)
        providers_to_try = self._build_provider_chain(provider)
        # When degraded due to budget, restrict to free providers only so we
        # never silently spend on a paid fallback after the limit is hit.
        if force_free:
            providers_to_try = [p for p in providers_to_try if self._is_free_provider(p)]
        
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
                elif try_provider == 'ollama' and self.ollama_available:
                    ai_response, ai_metadata = self._generate_ollama(full_system_prompt, message, context)
                    used_provider = 'ollama'
                    self._mark_provider_success('ollama')
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
        
        # Log AI call if budget manager available.
        # Free/local providers (e.g. Ollama) are exempt — never counted.
        if self.ai_budget and used_provider != 'fallback' \
                and not self._is_free_provider(used_provider):
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
        
        # Generate follow-up suggestions based on conversation
        follow_up_suggestions = []
        if ai_response and used_provider != 'fallback':
            try:
                from smart_response.follow_up_suggestions import get_suggestion_system
                suggestion_system = get_suggestion_system(context.get('db_connection'))
                follow_up_suggestions = suggestion_system.generate_suggestions(
                    user_id=user_id,
                    message=message,
                    ai_response=ai_response,
                    character_id=character.character_id,
                    context=context
                )
            except Exception as e:
                print(f"Warning: Could not generate follow-up suggestions: {e}")
        
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
                'has_summary': summary is not None,
                'follow_up_suggestions': follow_up_suggestions
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
        
        # === RESPONSE QUALITY RULES (applies to ALL characters) ===
        situation = context.get('situation_analysis', {})
        emotional_state = situation.get('emotional_state', 'neutral') if isinstance(situation, dict) else 'neutral'
        
        # Determine target length based on situation
        if emotional_state in ('crisis', 'distressed', 'very_negative'):
            length_guide = "Use 3-5 sentences. The user needs support — be warm but focused."
        elif emotional_state in ('excited', 'positive', 'celebrating'):
            length_guide = "Use 2-4 sentences. Match their energy briefly, then focus."
        elif context.get('is_follow_up') or context.get('detail_requested'):
            length_guide = "Provide a thorough response (up to 6-8 sentences) since the user asked for more detail."
        else:
            length_guide = "Use 2-3 sentences. Be concise — the user can always ask for more."
        
        # Extra instruction when user indicated the previous response missed the mark
        direction_note = ""
        if context.get('direction_change'):
            direction_note = """
6. DIRECTION CHANGE REQUESTED: The user indicated your previous response was NOT what they were looking for. Take a COMPLETELY different angle. Ask what specifically they need instead of guessing. Be humble and direct: "I may have misread that — what specifically would be most helpful right now?"
"""
        
        parts.append(f"""
CRITICAL RESPONSE RULES — follow these strictly:

1. BE SPECIFIC, NOT GENERIC: Never give vague advice like "focus on what matters" or "take it one step at a time." Instead, ask what specifically they're dealing with and give targeted, actionable responses. If you don't have enough information, ASK for it.

2. RESPONSE LENGTH: {length_guide} Users lose interest reading long responses. Keep it punchy and focused. A short, specific response beats a long, generic one every time.

3. ASK FOR DIRECTION: If the user's message is vague or broad, ask ONE specific question to narrow down what they actually need. Example: Instead of giving generic stress advice, ask "Is this work stress, relationship stress, or something else?"

4. CHECK YOUR DIRECTION: Occasionally (not every message) ask a brief check-in like "Is this the kind of help you're looking for?" or "Want me to go deeper on this or try a different angle?" — keep it natural, not formulaic.

5. NO FILLER: Skip greetings, pleasantries, and throat-clearing. Get straight to the point. Every sentence should deliver value.

6. NEVER REPEAT: Even if the user sends the same message again, NEVER give the same or substantially similar response. Vary your wording, angle, examples, and approach every time. Check the conversation history above — if you've already said something similar, take a different perspective or ask a new clarifying question instead.
{direction_note}""")
        
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
    
    def _get_max_tokens(self, context: Dict) -> int:
        """Determine max_tokens dynamically based on situation and user request."""
        # Explicit override (e.g. batched multi-agent calls that need more room).
        # Clamped to a safe ceiling to stay within provider output limits.
        if context.get('max_tokens_override'):
            return max(100, min(int(context['max_tokens_override']), 4000))
        # If user explicitly asked for more detail
        if context.get('detail_requested'):
            return 700
        
        situation = context.get('situation_analysis', {})
        emotional_state = situation.get('emotional_state', 'neutral') if isinstance(situation, dict) else 'neutral'
        
        if emotional_state in ('crisis', 'distressed', 'very_negative'):
            return 400  # Supportive but focused
        elif context.get('is_follow_up'):
            return 500  # Follow-up can be slightly longer
        else:
            return 300  # Default: short and punchy, but enough for complete thoughts
    
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
        
        max_tokens = self._get_max_tokens(context)
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
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
        
        max_tokens = self._get_max_tokens(context)
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
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
    
    def _generate_ollama(self, system_prompt: str, message: str,
                         context: Dict) -> Tuple[str, Dict]:
        """
        Generate response using a local Ollama server (free, no API key).
        Tries multiple models in order so Chinese-capable DeepSeek/Qwen are used
        if available, falling back to llama3.2.
        Uses the /api/chat endpoint via urllib (no extra dependency).
        Returns (response, metadata).
        """
        import time
        import urllib.request

        host = self.ollama_config['host'].rstrip('/')
        last_error = None

        messages = [{"role": "system", "content": system_prompt}]
        # Add conversation history if available
        history = context.get('message_history', [])
        for hist_msg in history:
            role = "user" if hist_msg.get('role') == 'user' else "assistant"
            messages.append({"role": role, "content": hist_msg.get('content', '')})
        messages.append({"role": "user", "content": message})

        # Clamp output for local models so a request can't block a worker too long.
        max_tokens = min(self._get_max_tokens(context), self.ollama_config.get('max_tokens', 512))
        prompt_tokens = len(system_prompt) // 4 + sum(len(m['content']) // 4 for m in messages)

        for model in self.ollama_config['models']:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                },
            }
            print(f"[TOKENS] Ollama request: ~{prompt_tokens} prompt tokens (model: {model})")

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                host + '/api/chat',
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )

            try:
                start_time = time.time()
                with urllib.request.urlopen(req, timeout=self.ollama_config['timeout']) as resp:
                    body = json.loads(resp.read().decode('utf-8'))
                response_time_ms = int((time.time() - start_time) * 1000)

                content = (body.get('message', {}) or {}).get('content', '') or ''
                input_tokens = body.get('prompt_eval_count', 0)
                output_tokens = body.get('eval_count', 0)

                if input_tokens or output_tokens:
                    print(f"[TOKENS] Ollama actual: {input_tokens} in, {output_tokens} out ({response_time_ms}ms)")

                metadata = {
                    'model': model,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'response_time_ms': response_time_ms,
                }

                return content, metadata
            except Exception as e:
                last_error = e
                print(f"[OLLAMA] {model} failed: {e}")
                continue

        raise last_error if last_error else Exception("All Ollama models failed")
    
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
