"""
Character Routes - Dynamic route generator for all characters
Eliminates need to manually create routes for each character
"""
from flask import render_template, request, jsonify
import asyncio
import threading
from .character_factory import CharacterFactory

# Create a persistent event loop for async operations
# This prevents "Event loop is closed" warnings
_event_loop = None
_loop_thread = None
_loop_lock = threading.Lock()

def _get_event_loop():
    """Get or create a persistent event loop running in a separate thread"""
    global _event_loop, _loop_thread
    
    with _loop_lock:
        if _event_loop is None or not _event_loop.is_running():
            def run_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_forever()
            
            _event_loop = asyncio.new_event_loop()
            _loop_thread = threading.Thread(target=run_loop, args=(_event_loop,), daemon=True)
            _loop_thread.start()
    
    return _event_loop

def _run_async(coroutine):
    """Run an async coroutine in the persistent event loop"""
    loop = _get_event_loop()
    future = asyncio.run_coroutine_threadsafe(coroutine, loop)
    return future.result()


def register_character_routes(app, characters_dict, smart_response_processor=None, integrated_db=None, ai_budget=None):
    """
    Dynamically register routes for all characters
    
    Args:
        app: Flask app instance
        characters_dict: Dict mapping character_id to chatbot instance
        smart_response_processor: Optional Smart Response processing function
        integrated_db: IntegratedDatabase instance for user+character sessions
        ai_budget: Optional AIBudgetManager instance for call enforcement
    """
    
    # Get all character IDs
    character_ids = CharacterFactory.get_all_character_ids()
    
    # Register routes for each character
    for char_id in character_ids:
        # Skip psychologist if using old implementation
        if char_id == "psychologist" and char_id not in characters_dict:
            continue
            
        # Create route functions with proper closures
        _register_character_page(app, char_id)
        _register_session_endpoint(app, char_id, integrated_db)  # NEW: Session management
        _register_chat_endpoint(app, char_id, characters_dict, smart_response_processor, integrated_db, ai_budget)
        _register_insight_endpoint(app, char_id, characters_dict)
        _register_stats_endpoint(app, char_id, characters_dict)
        _register_history_endpoint(app, char_id, characters_dict, integrated_db)  # Updated with database


def _register_session_endpoint(app, character_id, integrated_db):
    """Register session endpoint to get/create session for authenticated user+character"""
    
    def get_character_session():
        """Get or create session for authenticated user + character"""
        try:
            # Import here to avoid circular dependency
            from flask import request, jsonify
            from app import authenticate_token
            
            # Get user from auth token
            user_data = authenticate_token()
            if not user_data:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = user_data.get('user_id')
            if not user_id:
                return jsonify({'error': 'Invalid user data'}), 401
            
            if not integrated_db:
                return jsonify({'error': 'Database not configured'}), 500
            
            # Get or create session in database
            session_id = integrated_db.get_or_create_character_session(user_id, character_id)
            
            return jsonify({
                'session_id': session_id,
                'user_id': user_id,
                'character_id': character_id
            })
            
        except Exception as e:
            print(f"Error in {character_id} session: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Register route
    app.add_url_rule(
        f'/{character_id}/session',
        endpoint=f'{character_id}_session',
        view_func=get_character_session,
        methods=['GET']
    )


def _register_character_page(app, character_id):
    """Register main character page route"""
    
    def character_page():
        from .character_configs import CHARACTER_CONFIGS
        character_info = CharacterFactory.get_character_info(character_id)
        
        # Check if character has custom template, otherwise use universal
        config = CHARACTER_CONFIGS.get(character_id, {})
        template = config.get('custom_template', 'character_universal.html')
        
        return render_template(
            template,
            character=character_info,
            character_id=character_id
        )
    
    # Set proper endpoint name  and register
    app.add_url_rule(
        f'/{character_id}',
        endpoint=f'{character_id}_page',
        view_func=character_page
    )


def _register_chat_endpoint(app, character_id, characters_dict, smart_response_processor=None, integrated_db=None, ai_budget=None):
    """Register chat endpoint for character with Smart Response support and database integration"""
    
    def character_chat():
        try:
            from app import authenticate_token
            
            data = request.get_json()
            message = data.get('message', '')
            include_context = data.get('include_context', True)
            
            if not message.strip():
                return jsonify({'error': 'Message cannot be empty'}), 400
            
            # Get character instance
            bot = characters_dict.get(character_id)
            if not bot:
                return jsonify({'error': f'Character {character_id} not initialized'}), 500
            
            # DATABASE MIGRATION: Get user from auth token
            user_data = authenticate_token()
            if not user_data:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = user_data.get('user_id')
            if not user_id:
                return jsonify({'error': 'Invalid user data'}), 401
            
            # DATABASE MIGRATION: Get or create session for this user+character
            if integrated_db:
                session_id = integrated_db.get_or_create_character_session(user_id, character_id)
                print(f"✓ Using database session: {session_id} for user {user_id}, character {character_id}")
            else:
                # Fallback to old system if database not available
                session_id = bot.conversation_manager.create_session(character_id)
                print(f"⚠️ Fallback: Using JSON session: {session_id}")
            
            # Set the bot's session_id
            bot.session_id = session_id
            
            # ── Save user message (always, regardless of path) ───────────────
            if integrated_db:
                integrated_db.save_character_message(user_id, character_id, "user", message, {"source": "user"})
                print(f"💾 Saved user message to DATABASE for user {user_id}, character {character_id}")
            else:
                bot.conversation_manager.save_message(session_id, "user", message, {"source": "user"})

            # ── Explicit Context Extraction (always) ─────────────────────────
            try:
                from smart_response.explicit_context_handler import ExplicitContextHandler
                if integrated_db:
                    _ec_conn = integrated_db.get_connection()
                    _ech = ExplicitContextHandler(_ec_conn)
                    _ech.extract_explicit_context(user_id, character_id, message)
                    _ec_conn.close()
            except Exception:
                pass

            # ── Verbosity signal recording (always) ──────────────────────────
            _msg_lower = message.lower()
            if any(p in _msg_lower for p in ['keep it short', 'be brief', 'briefly', 'quick answer', 'in short']):
                try:
                    from smart_response.user_personalization import UserPersonalization
                    UserPersonalization().record_signal(user_id, 'response_length_feedback', 'brief', context=character_id)
                except Exception:
                    pass
            elif any(p in _msg_lower for p in ['in detail', 'detailed', 'explain fully', 'thorough', 'elaborate']):
                try:
                    from smart_response.user_personalization import UserPersonalization
                    UserPersonalization().record_signal(user_id, 'response_length_feedback', 'detailed', context=character_id)
                except Exception:
                    pass

            # ── Proactive Clarification (always) ────────────────────────────
            _clarification_response = None
            try:
                from smart_response.response_need_classifier import get_need_classifier
                from smart_response.proactive_clarifier import get_clarifier
                _classification = get_need_classifier().classify(message)
                _clarifier_decision = get_clarifier().decide(
                    message,
                    need_confidence=_classification.confidence,
                    primary_need=_classification.primary_need,
                    secondary_need=_classification.secondary_need,
                )
                if _clarifier_decision.should_clarify:
                    _clarification_response = get_clarifier().format_clarification_response(_clarifier_decision)
            except Exception:
                _classification = None
                _clarifier_decision = None

            if _clarification_response:
                _clarification_response['session_id'] = session_id
                if integrated_db:
                    integrated_db.save_character_message(
                        user_id, character_id, "assistant",
                        _clarification_response['response'],
                        {"source": "proactive_clarification", "urgency": _clarification_response.get('urgency', 'normal')}
                    )
                return jsonify(_clarification_response)

            # ── Budget check (before AI call) ────────────────────────────────
            if ai_budget:
                try:
                    _is_admin = False
                    if integrated_db:
                        _role_conn = integrated_db.get_connection()
                        _role_cur = _role_conn.cursor()
                        _role_cur.execute('SELECT role FROM users WHERE id = ?', (user_id,))
                        _role_row = _role_cur.fetchone()
                        if _role_row:
                            _is_admin = _role_row[0] in ('administrator', 'developer')
                        _role_conn.close()
                    _allowed, _budget_reason = ai_budget.can_make_ai_call(
                        user_id=user_id, is_admin=_is_admin
                    )
                    if not _allowed:
                        print(f"[AI-BUDGET] ❌ Denied for user {user_id}: {_budget_reason}")
                        return jsonify({
                            'response': 'Daily AI limit reached. Please try again tomorrow or contact an admin to adjust your quota.',
                            'budget_exceeded': True,
                            'reason': _budget_reason
                        }), 429
                except Exception as _be:
                    print(f"[AI-BUDGET] Warning: budget check failed: {_be}")

            # ── AI call ──────────────────────────────────────────────────────
            _ai_call_start = __import__('time').time()
            if smart_response_processor:
                def ai_function(enhanced_message):
                    # Use persistent event loop (no create/close warnings)
                    # enhanced_message includes explicit context prepended by Smart Response
                    # Pass save_user_message=False to prevent double-saving user message
                    # Pass message_source to tag where the response came from
                    return _run_async(bot.chat(enhanced_message, include_context, save_user_message=False, message_source="smart_response", user_id=user_id))
                
                try:
                    response = smart_response_processor(message, character_id, ai_function)
                    
                    # Log successful AI call to budget manager
                    if ai_budget:
                        try:
                            ai_budget.log_ai_call(
                                call_type='chat',
                                purpose=f'character_chat_{character_id}',
                                success=True,
                                user_id=user_id,
                                character=character_id
                            )
                        except Exception:
                            pass

                    # DATABASE MIGRATION: Save ALL bot responses to database
                    if isinstance(response, dict) and response.get('response'):
                        response_text = response.get('response', '')
                        response_type = response.get('type', 'direct_ai')
                        response_source = f"smart_response_{response_type}" if response_type == 'quick_reply' else "smart_response"
                        
                        # Save to database (not JSON)
                        if integrated_db:
                            integrated_db.save_character_message(
                                user_id, character_id, "assistant", response_text,
                                {"source": response_source, "confidence": response.get('confidence', 0), "type": response_type}
                            )
                            print(f"💾 Saved {response_type} to DATABASE: '{response_text[:50]}...'")
                        else:
                            # Fallback
                            bot.conversation_manager.save_message(
                                session_id, "assistant", response_text,
                                {"source": response_source, "confidence": response.get('confidence', 0)}
                            )
                    # FIXED: Now saves ALL responses (quick_reply AND full AI) to database
                except Exception as e:
                    print(f"❌ Error in Smart Response for {character_id}: {e}")
                    # Save error as assistant response to keep history balanced
                    error_msg = "I apologize, but I encountered an error. Please try again."
                    
                    # DATABASE MIGRATION: Save error to database
                    if integrated_db:
                        integrated_db.save_character_message(
                            user_id, character_id, "assistant", error_msg,
                            {"error": str(e), "error_type": "smart_response_failure", "source": "smart_response"}
                        )
                    else:
                        # Fallback
                        bot.conversation_manager.save_message(session_id, "assistant", error_msg, 
                                                             {"error": str(e), "error_type": "smart_response_failure", "source": "smart_response"})
                    return jsonify({'error': str(e), 'response': error_msg}), 500
            else:
                # Fallback to direct AI if Smart Response not available
                # Use persistent event loop (no create/close warnings)
                try:
                    response = _run_async(bot.chat(message, include_context, user_id=user_id))
                    if ai_budget:
                        try:
                            ai_budget.log_ai_call(
                                call_type='chat',
                                purpose=f'character_chat_{character_id}_direct',
                                success=True,
                                user_id=user_id,
                                character=character_id
                            )
                        except Exception:
                            pass
                except Exception as e:
                    print(f"❌ Error in direct chat for {character_id}: {e}")
                    return jsonify({'error': str(e)}), 500
            
            # Add session_id to response
            if isinstance(response, dict):
                response['session_id'] = session_id
            else:
                response = {'response': response, 'session_id': session_id}

            # ── Character Suggestion ─────────────────────────────────────────
            try:
                from smart_response.response_need_classifier import get_need_classifier
                from smart_response.character_suggester import get_character_suggester
                _cls = get_need_classifier().classify(message)
                if _cls.confidence >= 0.5:
                    _suggestion = get_character_suggester().suggest(
                        current_character_id=character_id,
                        primary_need=_cls.primary_need,
                        need_confidence=_cls.confidence,
                    )
                    if _suggestion.should_suggest:
                        response['character_suggestion'] = {
                            'character_id': _suggestion.suggested_character_id,
                            'character_name': _suggestion.suggested_character_name,
                            'reason': _suggestion.reason,
                            'message': get_character_suggester().format_suggestion_message(_suggestion),
                        }
                    response['detected_need'] = _cls.primary_need
            except Exception:
                pass

            # ── Dual-Layer History Storage ────────────────────────────────────
            # Store interaction in the analytical history layer so
            # ProgressContextBuilder and long-term trend analysis have data
            try:
                from smart_response.dual_layer_history import DualLayerHistorySystem
                if integrated_db:
                    _dlh_conn = integrated_db.get_connection()
                    _dlh = DualLayerHistorySystem(_dlh_conn)
                    _ai_text = response.get('response', '') if isinstance(response, dict) else str(response)
                    _response_type = response.get('type', 'direct_ai') if isinstance(response, dict) else 'direct_ai'
                    _primary_id = _dlh.store_interaction(
                        user_id, character_id,
                        message, _ai_text,
                        _response_type,
                        metadata={'session_id': session_id}
                    )
                    if _primary_id:
                        _dlh.analyze_and_store_secondary(_primary_id, user_id, character_id)
                    _dlh_conn.close()
            except Exception:
                pass

            # ── Expire stale explicit context (emotional states, intentions) ──
            try:
                from smart_response.explicit_context_handler import ExplicitContextHandler
                if integrated_db:
                    _exp_conn = integrated_db.get_connection()
                    _ech_exp = ExplicitContextHandler(_exp_conn)
                    _ech_exp.expire_old_context()
                    _exp_conn.close()
            except Exception:
                pass

            # Process accumulated signals to adapt user preferences (non-blocking)
            try:
                from smart_response.user_personalization import UserPersonalization
                UserPersonalization().process_signals_and_adapt(user_id)
            except Exception:
                pass

            return jsonify(response)
        except Exception as e:
            print(f"Error in {character_id} chat: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Register route
    app.add_url_rule(
        f'/{character_id}/chat',
        endpoint=f'{character_id}_chat',
        view_func=character_chat,
        methods=['POST']
    )


def _register_insight_endpoint(app, character_id, characters_dict):
    """Register daily insight endpoint"""
    
    def character_insight():
        try:
            bot = characters_dict.get(character_id)
            if not bot:
                return jsonify({'error': f'Character {character_id} not initialized'}), 500
            
            insight = bot.get_daily_insight()
            return jsonify({"insight": insight})
        except Exception as e:
            print(f"Error in {character_id} insight: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Register route
    app.add_url_rule(
        f'/{character_id}/daily-insight',
        endpoint=f'{character_id}_insight',
        view_func=character_insight
    )


def _register_stats_endpoint(app, character_id, characters_dict):
    """Register stats endpoint"""
    
    def character_stats():
        try:
            bot = characters_dict.get(character_id)
            if not bot:
                return jsonify({'error': f'Character {character_id} not initialized'}), 500
            
            stats = bot.get_character_stats()
            return jsonify(stats)
        except Exception as e:
            print(f"Error in {character_id} stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Register route
    app.add_url_rule(
        f'/{character_id}/stats',
        endpoint=f'{character_id}_stats',
        view_func=character_stats
    )


def _register_history_endpoint(app, character_id, characters_dict, integrated_db=None):
    """Register conversation history endpoint with database support"""
    
    def character_history():
        try:
            from app import authenticate_token
            
            # DATABASE MIGRATION: Get user from auth token
            user_data = authenticate_token()
            if not user_data:
                return jsonify({'error': 'Authentication required'}), 401
            
            user_id = user_data.get('user_id')
            if not user_id:
                return jsonify({'error': 'Invalid user data'}), 401
            
            # DATABASE MIGRATION: Get messages from database for this user+character
            if integrated_db:
                messages = integrated_db.get_character_messages(user_id, character_id)
                print(f"✓ Loaded {len(messages)} messages from DATABASE for user {user_id}, character {character_id}")
            else:
                # Fallback to old system
                session_id = request.args.get('session_id')
                if not session_id:
                    return jsonify({'messages': []}), 200
                
                bot = characters_dict.get(character_id)
                if not bot:
                    return jsonify({'error': f'Character {character_id} not initialized'}), 500
                
                messages = bot.conversation_manager.get_conversation_history(session_id, force_reload=True)
                print(f"⚠️ Fallback: Loaded {len(messages)} messages from JSON")
            
            return jsonify({'messages': messages})
        except Exception as e:
            print(f"Error in {character_id} history: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Register route
    app.add_url_rule(
        f'/{character_id}/history',
        endpoint=f'{character_id}_history',
        view_func=character_history,
        methods=['GET']
    )
