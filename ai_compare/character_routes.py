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


def register_character_routes(app, characters_dict, smart_response_processor=None):
    """
    Dynamically register routes for all characters
    
    Args:
        app: Flask app instance
        characters_dict: Dict mapping character_id to chatbot instance
        smart_response_processor: Optional Smart Response processing function
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
        _register_chat_endpoint(app, char_id, characters_dict, smart_response_processor)
        _register_insight_endpoint(app, char_id, characters_dict)
        _register_stats_endpoint(app, char_id, characters_dict)


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


def _register_chat_endpoint(app, character_id, characters_dict, smart_response_processor=None):
    """Register chat endpoint for character with Smart Response support"""
    
    def character_chat():
        try:
            data = request.get_json()
            message = data.get('message', '')
            include_context = data.get('include_context', True)
            
            if not message.strip():
                return jsonify({'error': 'Message cannot be empty'}), 400
            
            # Get character instance
            bot = characters_dict.get(character_id)
            if not bot:
                return jsonify({'error': f'Character {character_id} not initialized'}), 500
            
            # Use Smart Response if available
            if smart_response_processor:
                def ai_function():
                    # Use persistent event loop (no create/close warnings)
                    return _run_async(bot.chat(message, include_context))
                
                response = smart_response_processor(message, character_id, ai_function)
            else:
                # Fallback to direct AI if Smart Response not available
                # Use persistent event loop (no create/close warnings)
                response = _run_async(bot.chat(message, include_context))
            
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
