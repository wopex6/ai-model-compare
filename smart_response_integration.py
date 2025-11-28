"""
Flask Integration for Smart Response System
Provides easy integration into existing Flask routes
"""

from functools import wraps
from flask import request, jsonify
import sqlite3
from datetime import datetime
from smart_response.handler import SmartResponseHandler


class SmartResponseIntegration:
    """
    Wraps Smart Response System for easy Flask integration
    """
    
    def __init__(self, db_path='integrated_users.db'):
        """Initialize with database path"""
        self.db_path = db_path
        self._handler = None
        self._previous_interactions = {}  # Track for learning
    
    def get_handler(self):
        """Get or create handler instance"""
        if self._handler is None:
            conn = sqlite3.connect(self.db_path)
            self._handler = SmartResponseHandler(conn)
        return self._handler
    
    def process_chat_message(self, user_id, message, character, ai_chat_function):
        """
        Process a chat message with smart response system
        
        Args:
            user_id: User ID from auth token
            message: User's message text
            character: Character name ('coach', 'sage', etc.)
            ai_chat_function: Function to call for full AI response
                             Should accept (message) and return response dict
        
        Returns:
            Response dict with 'response', 'type', and optional metadata
        """
        handler = self.get_handler()
        
        # Track previous interaction for learning
        previous_key = f"{user_id}_{character}"
        previous_interaction = self._previous_interactions.get(previous_key)
        
        # If there was a previous interaction, track it with this followup
        if previous_interaction:
            time_diff = (datetime.now() - previous_interaction['timestamp']).total_seconds()
            
            handler.track_response(
                user_id=user_id,
                message=previous_interaction['message'],
                response_type=previous_interaction['response_type'],
                character=character,
                user_followup=message,
                time_to_followup=time_diff
            )
        
        # Process current message
        response_type, response_data = handler.process_message(
            user_id, message, character
        )
        
        if response_type == 'quick_reply':
            # Use quick reply
            result = {
                'response': response_data['text'],
                'type': 'quick_reply',
                'confidence': response_data['confidence'],
                'metadata': {
                    'smart_response': True,
                    'category': response_data.get('metadata', {}).get('category'),
                    'reasoning': response_data.get('reasoning', [])
                }
            }
            
            # Store for next interaction
            self._previous_interactions[previous_key] = {
                'message': message,
                'response_type': 'quick_reply',
                'timestamp': datetime.now()
            }
            
            return result
        
        else:
            # Use full AI
            ai_response = ai_chat_function(message)
            
            # Add metadata
            if isinstance(ai_response, dict):
                ai_response['type'] = 'full_ai'
                ai_response['metadata'] = {
                    'smart_response': True,
                    'confidence': response_data['confidence'],
                    'reasoning': response_data.get('reasoning', [])
                }
            else:
                # If AI function returns just a string
                ai_response = {
                    'response': ai_response,
                    'type': 'full_ai',
                    'metadata': {
                        'smart_response': True,
                        'confidence': response_data['confidence']
                    }
                }
            
            # Store for next interaction
            self._previous_interactions[previous_key] = {
                'message': message,
                'response_type': 'full_ai',
                'timestamp': datetime.now()
            }
            
            return ai_response
    
    def get_user_stats(self, user_id):
        """Get learning statistics for a user"""
        handler = self.get_handler()
        return handler.get_user_stats(user_id)
    
    def reset_user_learning(self, user_id):
        """Reset learning for a user"""
        handler = self.get_handler()
        handler.reset_user_learning(user_id)


# Global instance (initialized at app startup)
smart_response = SmartResponseIntegration()


def with_smart_response(character_name):
    """
    Decorator for Flask routes to add smart response functionality
    
    Usage:
        @app.route('/coach/chat', methods=['POST'])
        @require_auth  # Your auth decorator
        @with_smart_response('coach')
        def coach_chat():
            # Your existing AI chat logic
            message = request.get_json().get('message')
            response = motivational_bot.chat(message)
            return jsonify(response)
    
    The decorator will:
    1. Check if message is small talk
    2. Return quick reply if appropriate
    3. Call your function for full AI if needed
    4. Track interactions for learning
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            message = data.get('message', '')
            
            # Get user_id from request context (set by @require_auth)
            user_id = getattr(request, 'current_user', {}).get('user_id')
            
            if not user_id:
                # No auth, fall back to original function
                return func(*args, **kwargs)
            
            # AI function wrapper
            def ai_function(msg):
                # Temporarily store message back in request
                original_data = request.get_json()
                # Call original function
                response = func(*args, **kwargs)
                # Extract response from Flask response
                if hasattr(response, 'get_json'):
                    return response.get_json()
                return response
            
            # Process with smart response
            result = smart_response.process_chat_message(
                user_id=user_id,
                message=message,
                character=character_name,
                ai_chat_function=lambda msg: func(*args, **kwargs)
            )
            
            return jsonify(result)
        
        return wrapper
    return decorator
