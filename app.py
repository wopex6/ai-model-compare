from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import asyncio
import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from ai_compare.compare import AICompare
from ai_compare.chatbot import AIChatbot
from ai_compare.motivational_chatbot import MotivationalChatbot
from ai_compare.conversation_manager import ConversationManager
from ai_compare.personality_profiler import PersonalityProfiler
from ai_compare.personality_ui import PersonalityFeedbackWindow, PersonalityAssessmentUI
from ai_compare.user_profile_manager import UserProfileManager
from auto_doc_hook import enable_auto_docs, update_docs_now

# Import the integrated database system
from integrated_database import IntegratedDatabase

# Load environment variables from .env file
load_dotenv()

# Disable auto-docs in production
import os
os.environ['DISABLE_AUTO_DOCS'] = 'true'

app = Flask(__name__)

# Configure Flask for better incognito browser support
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-change-in-production')

# Enable CORS for better browser compatibility
CORS(app, supports_credentials=True)

# Initialize integrated database
integrated_db = IntegratedDatabase()
ai_compare = AICompare()
chatbot = AIChatbot()
motivational_bot = MotivationalChatbot()

# Initialize personality system
personality_profiler = PersonalityProfiler()
personality_assessment_ui = PersonalityAssessmentUI(personality_profiler)

# Initialize user profile system
user_profile_manager = UserProfileManager()

# Authentication middleware
def authenticate_token():
    """Middleware to authenticate JWT tokens"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
        return None

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        user_data = authenticate_token()
        if not user_data:
            return jsonify({'error': 'Authentication required'}), 401
        request.current_user = user_data
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Authentication routes
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        user_id = integrated_db.create_user(username, email, password)
        if not user_id:
            return jsonify({'error': 'Username or email already exists'}), 400
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user_id': user_id,
            'username': username
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = integrated_db.authenticate_user(username, password)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'token': token,
            'user_id': user['id'],
            'username': user['username']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not all([current_password, new_password]):
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        # Verify current password
        user = integrated_db.authenticate_user(request.current_user['username'], current_password)
        if not user:
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        success = integrated_db.update_user_password(request.current_user['user_id'], new_password)
        if success:
            return jsonify({'success': True, 'message': 'Password updated successfully'})
        else:
            return jsonify({'error': 'Failed to update password'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/user')
@require_auth
def get_current_user():
    """Get current user info"""
    try:
        user = integrated_db.get_user_by_id(request.current_user['user_id'])
        if user:
            return jsonify(user)
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Multi-user profile routes
@app.route('/api/user/profile')
@require_auth
def get_profile():
    """Get user profile"""
    try:
        profile = integrated_db.get_user_profile(request.current_user['user_id'])
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile"""
    try:
        profile_data = request.get_json()
        success = integrated_db.update_user_profile(request.current_user['user_id'], profile_data)
        if success:
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        else:
            return jsonify({'error': 'Failed to update profile'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Comprehensive profile routes (integrating original 3-page system)
@app.route('/api/user/comprehensive-profile')
@require_auth
def get_comprehensive_profile():
    """Get comprehensive profile from original system"""
    try:
        # Load comprehensive profile for Wai Tse (for now, we'll map to the known profile)
        if request.current_user['username'] == 'Wai Tse':
            profile_id = 'eb049813-e28a-4ae6-8c7b-fa80250d0e51'
            comprehensive_profile = user_profile_manager.load_user_profile(profile_id)
            if comprehensive_profile:
                return jsonify(comprehensive_profile)
        
        # For other users, return basic profile structure
        return jsonify({
            'personal_info': {},
            'preferences': {},
            'privacy_settings': {},
            'metadata': {'profile_completion': 0}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/comprehensive-profile/personal', methods=['PUT'])
@require_auth
def update_comprehensive_personal():
    """Update comprehensive profile personal info"""
    try:
        data = request.get_json()
        if request.current_user['username'] == 'Wai Tse':
            profile_id = 'eb049813-e28a-4ae6-8c7b-fa80250d0e51'
            success = user_profile_manager.update_personal_info(profile_id, data)
            return jsonify({'success': success})
        return jsonify({'success': False, 'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/comprehensive-profile/preferences', methods=['PUT'])
@require_auth
def update_comprehensive_preferences():
    """Update comprehensive profile preferences"""
    try:
        data = request.get_json()
        if request.current_user['username'] == 'Wai Tse':
            profile_id = 'eb049813-e28a-4ae6-8c7b-fa80250d0e51'
            success = user_profile_manager.update_preferences(profile_id, data)
            return jsonify({'success': success})
        return jsonify({'success': False, 'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/comprehensive-profile/privacy', methods=['PUT'])
@require_auth
def update_comprehensive_privacy():
    """Update comprehensive profile privacy settings"""
    try:
        data = request.get_json()
        if request.current_user['username'] == 'Wai Tse':
            profile_id = 'eb049813-e28a-4ae6-8c7b-fa80250d0e51'
            success = user_profile_manager.update_privacy_settings(profile_id, data)
            return jsonify({'success': success})
        return jsonify({'success': False, 'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Psychology traits routes
@app.route('/api/user/psychology-traits')
@require_auth
def get_psychology_traits():
    """Get user's psychology traits"""
    try:
        traits = integrated_db.get_psychology_traits(request.current_user['user_id'])
        return jsonify(traits)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/psychology-traits', methods=['POST'])
@require_auth
def create_psychology_trait():
    """Create or update psychology trait"""
    try:
        data = request.get_json()
        trait_name = data.get('traitName')
        trait_value = data.get('traitValue')
        description = data.get('description', '')
        
        if not trait_name or trait_value is None:
            return jsonify({'error': 'Trait name and value are required'}), 400
        
        success = integrated_db.upsert_psychology_trait(
            request.current_user['user_id'], trait_name, float(trait_value), description
        )
        if success:
            return jsonify({'success': True, 'message': 'Psychology trait saved successfully'})
        else:
            return jsonify({'error': 'Failed to save psychology trait'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/psychology-traits/<trait_name>', methods=['PUT'])
@require_auth
def update_psychology_trait(trait_name):
    """Update psychology trait"""
    try:
        data = request.get_json()
        trait_value = data.get('traitValue')
        description = data.get('description', '')
        
        if trait_value is None:
            return jsonify({'error': 'Trait value is required'}), 400
        
        success = integrated_db.upsert_psychology_trait(
            request.current_user['user_id'], trait_name, float(trait_value), description
        )
        if success:
            return jsonify({'success': True, 'message': 'Psychology trait updated successfully'})
        else:
            return jsonify({'error': 'Failed to update psychology trait'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Multi-user conversation routes
@app.route('/api/user/conversations')
@require_auth
def get_user_conversations():
    """Get user's conversations"""
    try:
        conversations = integrated_db.get_user_conversations(request.current_user['user_id'])
        return jsonify(conversations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/conversations', methods=['POST'])
@require_auth
def create_user_conversation():
    """Create new conversation"""
    try:
        data = request.get_json()
        title = data.get('title', 'New Conversation')
        
        session_id = integrated_db.create_conversation(request.current_user['user_id'], title)
        return jsonify({'success': True, 'session_id': session_id, 'message': 'Conversation created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/conversations/<session_id>', methods=['DELETE'])
@require_auth
def delete_user_conversation(session_id):
    """Delete a conversation"""
    try:
        success = integrated_db.delete_conversation(session_id, request.current_user['user_id'])
        if success:
            return jsonify({'message': 'Conversation deleted successfully'})
        else:
            return jsonify({'error': 'Conversation not found or unauthorized'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/message-usage')
@require_auth
def get_message_usage():
    """Get user's message usage and limits"""
    try:
        usage = integrated_db.get_message_usage(request.current_user['user_id'])
        return jsonify(usage)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/conversations/<session_id>/messages')
@require_auth
def get_conversation_messages(session_id):
    """Get conversation messages"""
    try:
        messages = integrated_db.get_conversation_messages(session_id, request.current_user['user_id'])
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/conversations/<session_id>/messages', methods=['POST'])
@require_auth
def add_conversation_message(session_id):
    """Add message to conversation and get AI response"""
    try:
        data = request.get_json()
        sender_type = data.get('senderType')
        content = data.get('content')
        
        if not all([sender_type, content]):
            return jsonify({'error': 'Sender type and content are required'}), 400
        
        # Check message limit for user messages
        if sender_type == 'user':
            can_send, reason = integrated_db.can_send_message(request.current_user['user_id'])
            if not can_send:
                usage = integrated_db.get_message_usage(request.current_user['user_id'])
                return jsonify({
                    'error': reason,
                    'limit_reached': True,
                    'usage': usage
                }), 403
        
        # Add user message to database
        success = integrated_db.add_message(session_id, request.current_user['user_id'], sender_type, content)
        if not success:
            return jsonify({'error': 'Failed to save message'}), 500
        
        # If it's a user message, generate AI response
        if sender_type == 'user':
            # Get user profile for context
            profile = integrated_db.get_user_profile(request.current_user['user_id'])
            traits = integrated_db.get_psychology_traits(request.current_user['user_id'])
            
            # Create user context
            user_context = f"User: {request.current_user['username']}"
            if profile and profile.get('bio'):
                user_context += f", Bio: {profile['bio']}"
            if traits:
                trait_summary = ", ".join([f"{t['trait_name']}: {t['trait_value']}" for t in traits[:3]])
                user_context += f", Traits: {trait_summary}"
            
            # Get AI response using existing chatbot
            enhanced_message = f"{user_context}\n\nUser message: {content}"
            
            # Create chatbot instance with session
            chatbot_instance = AIChatbot(session_id=session_id)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            ai_response = loop.run_until_complete(chatbot_instance.chat(enhanced_message, True))
            loop.close()
            
            # Save AI response to database
            if ai_response.get('response'):
                integrated_db.add_message(
                    session_id, 
                    request.current_user['user_id'], 
                    'assistant', 
                    ai_response['response'],
                    {'model': ai_response.get('model', 'unknown')}
                )
            
            # Increment message count for the user
            integrated_db.increment_message_count(request.current_user['user_id'])
            
            # Get updated usage info
            usage = integrated_db.get_message_usage(request.current_user['user_id'])
            
            return jsonify({
                'success': True, 
                'message': 'Message added successfully',
                'ai_response': ai_response.get('response', 'Sorry, I could not generate a response.'),
                'usage': usage
            })
        
        return jsonify({'success': True, 'message': 'Message added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    available_models = loop.run_until_complete(ai_compare.get_available_models())
    loop.close()
    return render_template('index.html', models=available_models)

@app.route('/multi-user')
def multi_user_interface():
    """Integrated multi-user AI chatbot interface"""
    return render_template('multi_user.html')

@app.route('/login-test')
def login_test():
    """Login test page for debugging"""
    return render_template('login_test.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question.strip():
            return jsonify({'error': 'Please enter a question'})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(ai_compare.ask_all(question))
        loop.close()
        
        return jsonify({
            'success': True,
            'responses': responses,
            'question': question
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        data = request.get_json()
        responses = data.get('responses', {})
        
        if not responses:
            return jsonify({'error': 'No responses provided'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        summary = loop.run_until_complete(ai_compare.summarize_responses(responses))
        consolidated = loop.run_until_complete(ai_compare.consolidate_responses(responses))
        loop.close()
        
        return jsonify({
            'summary': summary,
            'consolidated': consolidated
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Chatbot routes
@app.route('/chat')
def chat_interface():
    return render_template('chat.html')

@app.route('/chat/session', methods=['GET', 'POST'])
def chat_session():
    """Get or create chat session"""
    try:
        if request.method == 'POST':
            # Create new session
            session_id = chatbot.conversation_manager.create_session("Chat Session")
            print(f"Created new session: {session_id}")
            return jsonify({'session_id': session_id, 'created': True})
        else:
            # Get current session info
            session_id = request.args.get('session_id')
            print(f"Checking session: {session_id}")
            
            if session_id:
                # Check if session exists by trying to load it (force reload to get latest)
                session_data = chatbot.conversation_manager.load_session(session_id, force_reload=True)
                if session_data:
                    messages = chatbot.conversation_manager.get_conversation_history(session_id, force_reload=True)
                    print(f"Found session {session_id} with {len(messages)} messages")
                    return jsonify({
                        'session_id': session_id,
                        'messages': messages,
                        'exists': True,
                        'message_count': len(messages)
                    })
                else:
                    print(f"Session {session_id} not found")
                    return jsonify({'exists': False, 'error': 'Session not found'})
            else:
                # Return list of available sessions for recovery
                sessions = chatbot.conversation_manager.list_sessions()
                return jsonify({
                    'exists': False, 
                    'error': 'No session ID provided',
                    'available_sessions': sessions[:5]  # Return 5 most recent
                })
    except Exception as e:
        print(f"Error in chat_session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/history/<session_id>')
def chat_history(session_id):
    """Get conversation history for a session"""
    try:
        # Force reload to get latest messages from disk
        messages = chatbot.conversation_manager.get_conversation_history(session_id, force_reload=True)
        return jsonify({'messages': messages, 'session_id': session_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/message', methods=['POST'])
def chat_message():
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id')
        user_id = data.get('user_id')  # Optional user ID for personalization
        include_context = data.get('include_context', True)
        
        print(f"Received message for session {session_id}: {message[:50]}...")
        
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get user context if user_id is provided
        user_context = None
        if user_id:
            user_summary = user_profile_manager.get_user_summary(user_id)
            if user_summary:
                user_context = f"User context: {user_summary['name']} is interested in {', '.join(user_summary['interests'][:3])}. Communication style: {user_summary['communication_style']}."
        
        # Validate session exists before proceeding (force reload to check latest state)
        if session_id:
            session_data = chatbot.conversation_manager.load_session(session_id, force_reload=True)
            if not session_data:
                print(f"Session {session_id} not found, creating new session")
                # Session doesn't exist, create a new one
                session_id = chatbot.conversation_manager.create_session("Chat Session")
                chatbot_instance = AIChatbot(session_id=session_id)
            else:
                print(f"Using existing session {session_id}")
                chatbot_instance = AIChatbot(session_id=session_id)
        else:
            # Create new session and use it
            print("No session ID provided, creating new session")
            chatbot_instance = AIChatbot()
            session_id = chatbot_instance.session_id
        
        # Add user context to the message if available
        if user_context and include_context:
            enhanced_message = f"{user_context}\n\nUser message: {message}"
        else:
            enhanced_message = message
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(chatbot_instance.chat(enhanced_message, include_context))
        loop.close()
        
        # Record interaction if user_id provided
        if user_id:
            interaction_data = {
                'topic': message[:50],  # First 50 chars as topic
                'model': 'chatbot',
                'session_id': session_id
            }
            user_profile_manager.record_interaction(user_id, interaction_data)
        
        # Include session_id in response
        response['session_id'] = chatbot_instance.session_id
        print(f"Response sent for session {chatbot_instance.session_id}")
        
        return jsonify(response)
    except Exception as e:
        print(f"Error in chat_message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/personality', methods=['POST'])
def change_personality():
    try:
        data = request.get_json()
        preset_name = data.get('preset', '')
        
        success = chatbot.change_personality(preset_name)
        if success:
            return jsonify({'success': True, 'message': f'Personality changed to {preset_name}'})
        else:
            return jsonify({'error': 'Invalid personality preset'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/summary')
def chat_summary():
    try:
        summary = chatbot.get_conversation_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/personality-compare', methods=['POST'])
def personality_compare():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(chatbot.get_personality_comparison(message))
        loop.close()
        
        return jsonify(responses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Session Management Routes
@app.route('/chat/sessions', methods=['GET'])
def list_chat_sessions():
    try:
        sessions = chatbot.list_sessions()
        return jsonify({'sessions': sessions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/sessions', methods=['POST'])
def create_chat_session():
    try:
        session_id = chatbot.create_new_session()
        return jsonify({'session_id': session_id, 'message': 'New session created'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/sessions/<session_id>', methods=['GET'])
def load_chat_session(session_id):
    try:
        success = chatbot.load_session(session_id)
        if success:
            summary = chatbot.get_conversation_summary()
            return jsonify({'success': True, 'session_loaded': session_id, 'summary': summary})
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/sessions/<session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    try:
        success = chatbot.delete_session(session_id)
        if success:
            return jsonify({'success': True, 'message': 'Session deleted'})
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat/export', methods=['GET'])
def export_chat_session():
    try:
        format_type = request.args.get('format', 'json')
        exported_data = chatbot.export_conversation(format_type)
        
        if exported_data:
            if format_type == 'txt':
                return exported_data, 200, {'Content-Type': 'text/plain'}
            else:
                return jsonify({'data': exported_data})
        else:
            return jsonify({'error': 'Export failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Motivational Coach routes
@app.route('/coach')
def motivational_coach():
    return render_template('motivational_coach.html')

@app.route('/personality-test')
def personality_test_page():
    """Direct access to personality assessment interface"""
    return render_template('personality_test.html')

@app.route('/test-session')
def test_session_page():
    """Debug page for testing session restoration"""
    return render_template('test_session_restoration.html')

@app.route('/coach/chat', methods=['POST'])
def coach_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        include_context = data.get('include_context', True)
        
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(motivational_bot.chat(message, include_context))
        loop.close()
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/coach/stats')
def coach_stats():
    try:
        stats = motivational_bot.get_motivational_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/coach/toggle-reminders', methods=['POST'])
def toggle_reminders():
    try:
        data = request.get_json()
        active = data.get('active', True)
        motivational_bot.toggle_reminders(active)
        return jsonify({'success': True, 'reminders_active': active})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Personality Assessment routes
@app.route('/personality/feedback/<session_id>')
def get_personality_feedback(session_id):
    """Get personality feedback for a session"""
    try:
        feedback_window = PersonalityFeedbackWindow(session_id, personality_profiler)
        feedback = feedback_window.get_current_feedback()
        return jsonify(feedback)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/personality/assessment/start', methods=['POST'])
def start_personality_assessment():
    """Start personality assessment for user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        
        assessment_ui = personality_assessment_ui.start_assessment_ui(user_id)
        return jsonify(assessment_ui)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/personality/assessment/question/<user_id>')
def get_assessment_question(user_id):
    """Get current assessment question"""
    try:
        question_ui = personality_assessment_ui.get_current_question_ui(user_id)
        if question_ui:
            return jsonify(question_ui)
        else:
            return jsonify({'error': 'No active assessment or assessment complete'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/personality/assessment/respond', methods=['POST'])
def respond_to_assessment():
    """Record response to assessment question"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        question_id = data.get('question_id')
        option_id = data.get('option_id')
        
        if not all([user_id, question_id is not None, option_id is not None]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = personality_assessment_ui.process_question_response(user_id, question_id, option_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/personality/assessment/pause/<user_id>', methods=['POST'])
def pause_assessment(user_id):
    """Pause current assessment"""
    try:
        result = personality_assessment_ui.pause_assessment(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/personality/profile/<user_id>')
def get_detailed_profile(user_id):
    """Get detailed personality profile"""
    try:
        profile_ui = personality_assessment_ui.get_detailed_profile_ui(user_id)
        return jsonify(profile_ui)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/personality/check_assessment/<user_id>')
def check_assessment_needed(user_id):
    """Check if user should be offered personality assessment"""
    try:
        chatbot_instance = AIChatbot(session_id=user_id)
        should_offer = chatbot_instance.should_offer_assessment()
        prompt = chatbot_instance.get_assessment_prompt() if should_offer else None
        
        return jsonify({
            'should_offer_assessment': should_offer,
            'assessment_prompt': prompt
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Debug and maintenance endpoints
@app.route('/debug/conversations')
def debug_conversations():
    """Debug endpoint to check conversation storage"""
    try:
        storage_path = chatbot.conversation_manager.storage_dir
        sessions = chatbot.conversation_manager.list_sessions()
        
        return jsonify({
            'storage_path': str(storage_path.absolute()),
            'storage_exists': storage_path.exists(),
            'session_count': len(sessions),
            'sessions': sessions,
            'cache_size': len(chatbot.conversation_manager.conversation_cache)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/session/<session_id>')
def debug_session(session_id):
    """Debug specific session"""
    try:
        session_data = chatbot.conversation_manager.load_session(session_id)
        if session_data:
            return jsonify({
                'found': True,
                'session_data': session_data,
                'message_count': len(session_data.get('messages', [])),
                'file_path': str(chatbot.conversation_manager.storage_dir / f"{session_id}.json")
            })
        else:
            return jsonify({
                'found': False,
                'error': 'Session not found',
                'searched_path': str(chatbot.conversation_manager.storage_dir / f"{session_id}.json")
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/restore_session', methods=['POST'])
def restore_session():
    """Attempt to restore the most recent session"""
    try:
        sessions = chatbot.conversation_manager.list_sessions()
        if sessions:
            # Get the most recent session
            latest_session = sessions[0]
            session_id = latest_session['session_id']
            session_data = chatbot.conversation_manager.load_session(session_id)
            
            if session_data:
                messages = chatbot.conversation_manager.get_conversation_history(session_id)
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'messages': messages,
                    'session_info': latest_session
                })
        
        return jsonify({
            'success': False,
            'error': 'No sessions found to restore'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Profile Management Routes
@app.route('/profile')
def user_profile_page():
    """User profile management page"""
    return render_template('user_profile.html')

@app.route('/psychological-assessment')
def psychological_assessment():
    """Psychological assessment questionnaire page"""
    return render_template('psychological_assessment.html')

@app.route('/psychological-profile')
def psychological_profile():
    """Psychological profile display page"""
    return render_template('psychological_profile.html')

@app.route('/api/profile/create', methods=['POST'])
def create_user_profile():
    """Create a new user profile"""
    try:
        user_id = user_profile_manager.create_user_profile()
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'Profile created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/<user_id>')
def get_user_profile(user_id):
    """Get user profile data"""
    try:
        profile = user_profile_manager.load_user_profile(user_id, force_reload=True)
        if profile:
            return jsonify(profile)
        else:
            return jsonify({'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/personal-info', methods=['POST'])
def update_personal_info():
    """Update user personal information"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Extract personal info (exclude user_id)
        personal_info = {k: v for k, v in data.items() if k != 'user_id'}
        
        success = user_profile_manager.update_personal_info(user_id, personal_info)
        if success:
            return jsonify({'success': True, 'message': 'Personal information updated'})
        else:
            return jsonify({'error': 'Failed to update personal information'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/preferences', methods=['POST'])
def update_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Extract preferences (exclude user_id)
        preferences = {k: v for k, v in data.items() if k != 'user_id'}
        
        success = user_profile_manager.update_preferences(user_id, preferences)
        if success:
            return jsonify({'success': True, 'message': 'Preferences updated'})
        else:
            return jsonify({'error': 'Failed to update preferences'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/privacy', methods=['POST'])
def update_privacy_settings():
    """Update privacy settings"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Extract privacy settings (exclude user_id)
        privacy_settings = {k: v for k, v in data.items() if k != 'user_id'}
        
        success = user_profile_manager.update_privacy_settings(user_id, privacy_settings)
        if success:
            return jsonify({'success': True, 'message': 'Privacy settings updated'})
        else:
            return jsonify({'error': 'Failed to update privacy settings'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/<user_id>', methods=['DELETE'])
def delete_user_profile(user_id):
    """Delete user profile"""
    try:
        success = user_profile_manager.delete_profile(user_id)
        if success:
            return jsonify({'success': True, 'message': 'Profile deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete profile'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/export/<user_id>')
def export_user_profile(user_id):
    """Export user profile"""
    try:
        format_type = request.args.get('format', 'json')
        exported_data = user_profile_manager.export_profile(user_id, format_type)
        
        if exported_data:
            if format_type == 'txt':
                return exported_data, 200, {
                    'Content-Type': 'text/plain',
                    'Content-Disposition': f'attachment; filename=profile_{user_id}.txt'
                }
            else:
                return exported_data, 200, {
                    'Content-Type': 'application/json',
                    'Content-Disposition': f'attachment; filename=profile_{user_id}.json'
                }
        else:
            return jsonify({'error': 'Profile not found or export failed'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/list')
def list_user_profiles():
    """List all user profiles"""
    try:
        profiles = user_profile_manager.list_all_profiles()
        return jsonify({'profiles': profiles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/summary/<user_id>')
def get_user_summary(user_id):
    """Get user summary for AI context"""
    try:
        summary = user_profile_manager.get_user_summary(user_id)
        if summary:
            return jsonify(summary)
        else:
            return jsonify({'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/interaction', methods=['POST'])
def record_interaction():
    """Record user interaction with AI"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        interaction_data = data.get('interaction_data', {})
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        success = user_profile_manager.record_interaction(user_id, interaction_data)
        if success:
            return jsonify({'success': True, 'message': 'Interaction recorded'})
        else:
            return jsonify({'error': 'Failed to record interaction'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/psychological-assessment', methods=['POST'])
def save_psychological_assessment():
    """Save psychological assessment results"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        scores = data.get('scores', {})
        completed_at = data.get('completed_at')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Update user profile with psychological assessment data
        from datetime import datetime
        ei_score = scores.get('extraversion', 5) - scores.get('introversion', 5)
        sn_score = scores.get('sensing', 5) - scores.get('intuition', 5)
        tf_score = scores.get('thinking', 5) - scores.get('feeling', 5)
        jp_score = scores.get('judging', 5) - scores.get('perceiving', 5)
        openness_score = scores.get('openness', 5)
        conscientiousness_score = scores.get('conscientiousness', 5)
        extraversion_score = scores.get('extraversion', 5)
        agreeableness_score = scores.get('agreeableness', 5)
        neuroticism_score = scores.get('neuroticism', 5)
        
        # Save psychological attributes to user profile with timestamp and history
        current_timestamp = datetime.now().isoformat()
        
        # Get existing profile to maintain history
        existing_profile = user_profile_manager.get_user_profile(user_id)
        assessment_history = existing_profile.get('preferences', {}).get('assessment_history', []) if existing_profile else []
        
        # Create new assessment entry
        new_assessment = {
            'timestamp': current_timestamp,
            'jung_types': {
                'extraversion_introversion': ei_score,
                'sensing_intuition': sn_score,
                'thinking_feeling': tf_score,
                'judging_perceiving': jp_score
            },
            'big_five': {
                'openness': openness_score,
                'conscientiousness': conscientiousness_score,
                'extraversion': extraversion_score,
                'agreeableness': agreeableness_score,
                'neuroticism': neuroticism_score
            }
        }
        
        # Add to history
        assessment_history.append(new_assessment)
        
        # Keep only last 10 assessments to prevent unlimited growth
        if len(assessment_history) > 10:
            assessment_history = assessment_history[-10:]
        
        psychological_attributes = {
            'jung_types': {
                'extraversion_introversion': ei_score,
                'sensing_intuition': sn_score,
                'thinking_feeling': tf_score,
                'judging_perceiving': jp_score
            },
            'big_five': {
                'openness': openness_score,
                'conscientiousness': conscientiousness_score,
                'extraversion': extraversion_score,
                'agreeableness': agreeableness_score,
                'neuroticism': neuroticism_score
            },
            'assessment_completed_at': current_timestamp,
            'assessment_history': assessment_history
        }
        
        user_profile_manager.update_preferences(user_id, psychological_attributes)
        return jsonify({
            'success': True,
            'message': 'Psychological assessment saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Enable auto-documentation on startup
    # enable_auto_docs()  # Disabled for production - causes timeouts
    
    # Force initial documentation update
    # update_docs_now()  # Disabled for production - causes timeouts
    
    # Print conversation storage info on startup
    print(f"\n=== Conversation Storage Info ===")
    print(f"Storage directory: {chatbot.conversation_manager.storage_dir.absolute()}")
    sessions = chatbot.conversation_manager.list_sessions()
    print(f"Found {len(sessions)} existing sessions")
    if sessions:
        print("Recent sessions:")
        for session in sessions[:3]:
            print(f"  - {session['session_id'][:8]}... ({session['message_count']} messages, {session['last_updated']})")
    print("=" * 35)
    
    # Print user profile storage info
    print(f"\n=== User Profile Storage Info ===")
    print(f"Storage directory: {user_profile_manager.storage_dir.absolute()}")
    profiles = user_profile_manager.list_all_profiles()
    print(f"Found {len(profiles)} user profiles")
    if profiles:
        print("Recent profiles:")
        for profile in profiles[:3]:
            print(f"  - {profile['name']} ({profile['completion']}% complete, {profile['total_conversations']} conversations)")
    print("=" * 35)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
