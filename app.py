from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import asyncio
import os
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from ai_compare.compare import AICompare
from ai_compare.chatbot import AIChatbot
from ai_compare.motivational_chatbot import MotivationalChatbot
from ai_compare.wisdom_chatbot import WisdomChatbot
from ai_compare.stoic_chatbot import StoicChatbot
from ai_compare.psychologist_chatbot import PsychologistChatbot
from ai_compare.conversation_manager import ConversationManager
from ai_compare.personality_profiler import PersonalityProfiler
from ai_compare.personality_ui import PersonalityFeedbackWindow, PersonalityAssessmentUI
from ai_compare.user_profile_manager import UserProfileManager
from auto_doc_hook import enable_auto_docs, update_docs_now

# New character system
from ai_compare.character_factory import CharacterFactory
from ai_compare.character_routes import register_character_routes
from ai_compare.character_configs import CHARACTER_CONFIGS

# Import the integrated database system
from integrated_database import IntegratedDatabase
from email_service import EmailService

# Import Smart Response System
from smart_response.handler import SmartResponseHandler
import sqlite3

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

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mp4', 'avi', 'mov', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar', 'svg', 'webp', 'ogg', 'm4a', 'webm'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-change-in-production')

# Enable CORS for better browser compatibility
CORS(app, supports_credentials=True)

# Initialize integrated database
integrated_db = IntegratedDatabase()
email_service = EmailService()
ai_compare = AICompare()
chatbot = AIChatbot()

# Initialize ALL characters through factory (unified system)
print("\n=== Initializing All Characters ===")
all_characters = {}
character_ids = [
    "super_motivational_coach",  # Max
    "wisdom_sage",                # Sage Wei
    "stoic_philosopher",          # Marcus
    "psychologist",               # Dr. Elena
    "zen_master",                 # Master Kai
    "business_coach",             # Coach Ryan
    "life_coach",                 # Coach Jordan
    "scientist"                   # Dr. Nova
]

for char_id in character_ids:
    try:
        all_characters[char_id] = CharacterFactory.create_character(char_id)
        config = CHARACTER_CONFIGS.get(char_id, {})
        display_name = config.get("display_name", char_id)
        print(f"✓ {display_name} ({char_id}) initialized")
    except Exception as e:
        print(f"✗ Error initializing {char_id}: {e}")

# Keep legacy references for backward compatibility in existing routes
motivational_bot = all_characters.get("super_motivational_coach")
wisdom_bot = all_characters.get("wisdom_sage")
stoic_bot = all_characters.get("stoic_philosopher")
psychologist_bot = all_characters.get("psychologist")

# Initialize personality system
personality_profiler = PersonalityProfiler()
personality_assessment_ui = PersonalityAssessmentUI(personality_profiler)

# Initialize user profile system
user_profile_manager = UserProfileManager()

# Initialize Smart Response System with Context Manager, Dual-Layer History, and AI Budget Manager
try:
    from smart_response.handler import SmartResponseHandler
    from smart_response.conversation_context import ConversationContextManager
    from smart_response.dual_layer_history import DualLayerHistorySystem
    from smart_response.ai_budget_manager import AIBudgetManager
    smart_response_conn = sqlite3.connect('integrated_users.db', check_same_thread=False)
    smart_handler = SmartResponseHandler(smart_response_conn)
    context_manager = ConversationContextManager(smart_response_conn)
    history_system = DualLayerHistorySystem(smart_response_conn)
    ai_budget = AIBudgetManager(smart_response_conn)
    
    # Initialize frontend error logging table
    cursor = smart_response_conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frontend_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            error_message TEXT NOT NULL,
            character TEXT,
            context TEXT,
            user_agent TEXT,
            url TEXT,
            stack_trace TEXT
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_frontend_errors_timestamp
        ON frontend_errors(timestamp DESC)
    ''')
    smart_response_conn.commit()
    
    # Track previous interactions for learning
    previous_interactions = {}
    # Store recent message history for context
    message_histories = {}  # {user_id_character: [{role, content, timestamp}, ...]}
    print("✓ Smart Response System with AI Budget Control initialized")
    print("✓ Frontend error logging initialized")
except Exception as e:
    print(f"✗ Error initializing Smart Response: {e}")
    import traceback
    traceback.print_exc()
    smart_handler = None
    context_manager = None
    history_system = None
    ai_budget = None
    previous_interactions = {}
    message_histories = {}

# Helper function for Smart Response integration with Context
def process_with_smart_response(message, character_name, ai_chat_function):
    """
    Common Smart Response processing for all characters WITH CONTEXT
    
    Args:
        message: User's message
        character_name: Character identifier (coach, sage, marcus, etc.)
        ai_chat_function: Function that accepts enhanced_message and returns AI response
    
    Returns:
        Response dict with 'response', 'type', etc.
        
    Note: ai_chat_function will receive enhanced_message (with context prepended)
    instead of the original message when context is available.
    """
    # Check if user is authenticated (optional)
    user_data = authenticate_token()
    user_id = user_data.get('user_id') if user_data else None
    
    # DEBUG: Log authentication status
    if user_id:
        print(f"✓ Authenticated user_id={user_id} for character={character_name}")
    else:
        print(f"⚠️ No authentication for character={character_name}")
    
    # Get message history for this user/character
    history_key = f"{user_id}_{character_name}" if user_id else None
    message_history = message_histories.get(history_key, []) if history_key else []
    
    # Smart Response only for authenticated users
    if smart_handler and user_id and context_manager:
        # Get conversation context
        context = context_manager.get_context_for_ai(user_id, character_name, message_history)
        print(f"📚 Context loaded: {len(context.get('recent_topics', []))} topics, {context.get('message_count', 0)} messages")
        
        # Track previous interaction for learning
        prev_key = f"{user_id}_{character_name}"
        if prev_key in previous_interactions:
            prev = previous_interactions[prev_key]
            time_diff = (datetime.now() - prev['timestamp']).total_seconds()
            smart_handler.track_response(
                user_id=user_id,
                message=prev['message'],
                response_type=prev['response_type'],
                character=character_name,
                user_followup=message,
                time_to_followup=time_diff
            )
        
        # Check if this is small talk
        response_type, response_data = smart_handler.process_message(
            user_id, message, character_name
        )
        
        if response_type == 'quick_reply':
            # Use quick reply (instant, no API cost!)
            print(f"💰 COST SAVED ({character_name}) - Quick reply for: '{message}'")
            
            # Add user message to history
            message_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Add assistant response to history
            message_history.append({
                'role': 'assistant',
                'content': response_data['text'],
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 20 messages
            message_history = message_history[-20:]
            message_histories[history_key] = message_history
            
            result = {
                'response': response_data['text'],
                'type': 'quick_reply',
                'confidence': response_data['confidence'],
                'smart_response': True
            }
            
            # Add follow-up suggestion if available
            if 'suggestion' in response_data and response_data['suggestion']:
                result['suggestion'] = response_data['suggestion']
                print(f"   💭 Suggestion: '{response_data['suggestion']}'")
            
            # Update context after exchange
            context_manager.update_context(
                user_id, character_name, message, response_data['text']
            )
            
            # DUAL-LAYER HISTORY: Store interaction
            if history_system:
                primary_id = history_system.store_interaction(
                    user_id, character_name,
                    message, response_data['text'],
                    'quick_reply',
                    metadata={'session_id': history_key}
                )
                # Store analytical layer
                history_system.analyze_and_store_secondary(
                    primary_id, user_id, character_name,
                    interpretation=None,  # Auto-analyze
                    context=context
                )
            
            # Store for learning
            previous_interactions[prev_key] = {
                'message': message,
                'response_type': 'quick_reply',
                'timestamp': datetime.now()
            }
            
            return result
        
        # Log that we're using full AI
        print(f"💸 API CALL ({character_name}) - Full AI for: '{message}' (confidence: {response_data['confidence']:.2f})")
        
        # Format context for AI prompt
        context_prompt = context_manager.format_context_for_prompt(context)
        if context_prompt:
            print(f"   📝 Passing context to AI: {len(context_prompt)} chars")
            # Prepend context to message so AI receives it
            # This makes AI aware of user's emotional state, goals, and preferences
            enhanced_message = f"{context_prompt}\n\nUser's current message: {message}"
            print(f"   ✓ Context prepended to message for AI awareness")
        else:
            enhanced_message = message
    else:
        context_prompt = None
        context = None
        enhanced_message = message
    
    # AI BUDGET CONTROL: Check if AI call is allowed
    if ai_budget and user_id:
        # Check if user is admin
        is_admin = False
        try:
            user_role = integrated_db.get_user_role(user_id)
            is_admin = (user_role == 'administrator')
            print(f"   🔑 User role: {user_role} (admin={is_admin})")
        except:
            is_admin = False
        
        allowed, deny_reason = ai_budget.can_make_ai_call(
            user_id=user_id,
            is_admin=is_admin,
            is_background=False
        )
        
        if not allowed:
            # BUDGET EXCEEDED - Use fallback response
            print(f"⛔ AI call denied: {deny_reason}")
            limit_type = "1000/day admin limit" if is_admin else "100/day limit"
            fallback_response = {
                'response': f"I've reached my conversation {limit_type} for today. I'll be back tomorrow with full energy! Try our quick reply suggestions or come back later.",
                'type': 'budget_limited',
                'reason': deny_reason,
                'is_admin': is_admin
            }
            # Log the denied call
            ai_budget.log_ai_call(
                call_type='user_chat',
                purpose=f'{character_name} chat (DENIED)',
                success=False,
                user_id=user_id,
                character=character_name,
                is_background=False,
                error_message=deny_reason
            )
            return fallback_response
    
    # Use full AI (with context if available)
    ai_call_success = False
    ai_error = None
    try:
        response = ai_chat_function(enhanced_message)
        ai_call_success = True
    except Exception as e:
        ai_error = str(e)
        ai_call_success = False
        # Notify user of API failure
        response = {
            'response': f"I'm having trouble connecting right now. Please try again in a moment. ({ai_error[:50]})",
            'type': 'api_error',
            'error': ai_error
        }
    
    # Log AI call result
    if ai_budget:
        ai_budget.log_ai_call(
            call_type='user_chat',
            purpose=f'{character_name} chat',
            success=ai_call_success,
            user_id=user_id,
            character=character_name,
            is_background=False,
            error_message=ai_error
        )
    
    # Store for learning and context (only if authenticated)
    if smart_handler and user_id and context_manager:
        # Add to message history
        if history_key:
            message_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            message_history.append({
                'role': 'assistant',
                'content': response if isinstance(response, str) else response.get('response', ''),
                'timestamp': datetime.now().isoformat()
            })
            message_history = message_history[-20:]
            message_histories[history_key] = message_history
        
        # Update context
        response_text = response if isinstance(response, str) else response.get('response', '')
        context_manager.update_context(
            user_id, character_name, message, response_text
        )
        
        # DUAL-LAYER HISTORY: Store interaction
        if history_system:
            primary_id = history_system.store_interaction(
                user_id, character_name,
                message, response_text,
                'full_ai',
                metadata={'session_id': history_key}
            )
            # Store analytical layer
            history_system.analyze_and_store_secondary(
                primary_id, user_id, character_name,
                interpretation=None,  # Auto-analyze
                context=context
            )
        
        prev_key = f"{user_id}_{character_name}"
        previous_interactions[prev_key] = {
            'message': message,
            'response_type': 'full_ai',
            'timestamp': datetime.now()
        }
    
    # Add metadata
    if isinstance(response, dict):
        response['type'] = 'full_ai'
        response['smart_response'] = True
    
    return response

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

# Favicon route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    """Serve favicon or return 204 No Content"""
    return '', 204

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
        
        # Generate and send verification code
        print(f"📧 Attempting to send verification email to {email}")
        try:
            verification_code = integrated_db.create_verification_code(user_id)
            print(f"🔐 Generated verification code: {verification_code}")
            email_sent = email_service.send_verification_code(email, username, verification_code)
            
            if email_sent:
                print(f"✅ Verification email sent successfully to {email}")
            else:
                print(f"⚠️  Warning: Could not send verification email to {email}")
        except Exception as e:
            print(f"❌ Error sending verification email: {e}")
            import traceback
            traceback.print_exc()
            email_sent = False
        
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
            'username': username,
            'email_verified': False,
            'verification_sent': email_sent
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

@app.route('/api/auth/change-email', methods=['POST'])
@require_auth
def change_email():
    """Change user email"""
    try:
        data = request.get_json()
        new_email = data.get('newEmail')
        password = data.get('password')
        
        if not new_email or not password:
            return jsonify({'error': 'New email and password are required'}), 400
        
        # Verify password
        user = integrated_db.authenticate_user(request.current_user['username'], password)
        if not user:
            return jsonify({'error': 'Password is incorrect'}), 401
        
        # Check if email is already in use
        existing_user = integrated_db.get_user_by_email(new_email)
        if existing_user and existing_user['id'] != request.current_user['user_id']:
            return jsonify({'error': 'Email address is already in use'}), 400
        
        # Update email
        success = integrated_db.update_user_email(request.current_user['user_id'], new_email)
        if success:
            # Send verification email
            verification_code = integrated_db.create_verification_code(request.current_user['user_id'])
            email_sent = email_service.send_verification_code(new_email, request.current_user['username'], verification_code)
            
            return jsonify({
                'success': True, 
                'message': 'Email updated successfully. Please verify your new email address.',
                'email_sent': email_sent
            })
        else:
            return jsonify({'error': 'Failed to update email'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users')
@require_auth
def get_all_users():
    """Get all users with statistics (admin only)"""
    try:
        # Check if user is administrator
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        users = integrated_db.get_all_users_stats()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/delete', methods=['POST'])
@require_auth
def delete_user(user_id):
    """Soft delete a user (admin only)"""
    try:
        # Check if user is administrator
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Don't allow deleting yourself
        if user_id == request.current_user['user_id']:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        success = integrated_db.soft_delete_user(user_id)
        if success:
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/restore', methods=['POST'])
@require_auth
def restore_user(user_id):
    """Restore a soft-deleted user (admin only)"""
    try:
        # Check if user is administrator
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        success = integrated_db.restore_user(user_id)
        if success:
            return jsonify({'success': True, 'message': 'User restored successfully'})
        else:
            return jsonify({'error': 'Failed to restore user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/role', methods=['POST'])
@require_auth
def change_user_role(user_id):
    """Change a user's role (admin only)"""
    try:
        # Check if user is administrator
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        new_role = data.get('role')
        
        # Validate role
        valid_roles = ['guest', 'user', 'paid', 'administrator']
        if new_role not in valid_roles:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Don't allow changing own role
        if user_id == request.current_user['user_id']:
            return jsonify({'error': 'Cannot change your own role'}), 400
        
        success = integrated_db.update_user_role(user_id, new_role)
        if success:
            return jsonify({'success': True, 'message': f'User role changed to {new_role}'})
        else:
            return jsonify({'error': 'Failed to change user role'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>/permanent-delete', methods=['POST'])
@require_auth
def permanent_delete_user(user_id):
    """Permanently delete a user and all their data (admin only)"""
    try:
        # Check if user is administrator
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Don't allow deleting yourself
        if user_id == request.current_user['user_id']:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        success = integrated_db.permanent_delete_user(user_id)
        if success:
            return jsonify({'success': True, 'message': 'User permanently deleted'})
        else:
            return jsonify({'error': 'Failed to permanently delete user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/bulk-delete-deleted', methods=['POST'])
@require_auth
def bulk_delete_deleted_users():
    """Permanently delete all logically deleted users (admin only)"""
    try:
        # Check if user is administrator
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        deleted_count = integrated_db.bulk_delete_deleted_users()
        return jsonify({
            'success': True, 
            'message': f'Permanently deleted {deleted_count} users',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/statistics')
@require_auth
def get_statistics():
    """Get overall usage statistics (admin only)"""
    try:
        # Check if user is administrator
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        stats = integrated_db.get_usage_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/verify-email', methods=['POST'])
@require_auth
def verify_email():
    """Verify email with code"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'Verification code is required'}), 400
        
        success, message = integrated_db.verify_email_code(request.current_user['user_id'], code)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'error': message}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/resend-verification', methods=['POST'])
@require_auth
def resend_verification():
    """Resend verification code"""
    try:
        user = integrated_db.get_user_by_id(request.current_user['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already verified
        if integrated_db.is_email_verified(request.current_user['user_id']):
            return jsonify({'error': 'Email already verified'}), 400
        
        # Generate and send new code
        verification_code = integrated_db.create_verification_code(request.current_user['user_id'])
        email_sent = email_service.send_verification_code(user['email'], user['username'], verification_code)
        
        if email_sent:
            return jsonify({'success': True, 'message': 'Verification code sent'})
        else:
            return jsonify({'error': 'Failed to send verification email'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/check-verification')
@require_auth
def check_verification():
    """Check if email is verified"""
    try:
        is_verified = integrated_db.is_email_verified(request.current_user['user_id'])
        return jsonify({'verified': is_verified})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# File Upload/Download Endpoints
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-file', methods=['POST'])
@require_auth
def upload_file():
    """Upload a file and return file info"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{unique_id}.{file_extension}"
            
            # Save file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Get file info
            file_size = os.path.getsize(filepath)
            
            return jsonify({
                'success': True,
                'filename': unique_filename,
                'original_filename': original_filename,
                'file_size': file_size,
                'file_url': f'/api/files/{unique_filename}'
            })
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<filename>', methods=['GET'])
def download_file(filename):
    """Download or view a file"""
    try:
        # Get original filename from query parameter if provided
        original_filename = request.args.get('original_name', filename)
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            filename,
            as_attachment=False,  # Allow inline viewing for images/videos
            download_name=original_filename  # Use original filename for download
        )
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return jsonify({'error': 'File not found'}), 404

# Admin Messaging Endpoints
@app.route('/api/admin-chat/messages', methods=['GET'])
@require_auth
def get_admin_chat_messages():
    """Get all messages between user and admin"""
    try:
        messages = integrated_db.get_admin_messages(request.current_user['user_id'])
        # Mark admin messages as read
        integrated_db.mark_admin_messages_read(request.current_user['user_id'], 'admin')
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin-chat/send', methods=['POST'])
@require_auth
def send_admin_chat_message():
    """Send a message to admin with optional file attachment and reply"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        file_size = data.get('file_size')
        reply_to = data.get('reply_to')
        
        # Must have either message or file
        if not message and not file_url:
            return jsonify({'error': 'Message or file is required'}), 400
        
        success = integrated_db.send_admin_message(
            request.current_user['user_id'],
            'user',
            message,
            file_url,
            file_name,
            file_size,
            reply_to
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Message sent'})
        else:
            return jsonify({'error': 'Failed to send message'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin-chat/unread-count', methods=['GET'])
@require_auth
def get_unread_admin_messages():
    """Get count of unread messages from admin"""
    try:
        count = integrated_db.get_unread_admin_message_count(request.current_user['user_id'], 'admin')
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin-only endpoints
@app.route('/api/admin/chats', methods=['GET'])
@require_auth
def get_all_admin_chats():
    """Get all user-admin chats (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        chats = integrated_db.get_all_user_admin_chats()
        return jsonify(chats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/chats/<int:user_id>/messages', methods=['GET'])
@require_auth
def get_user_admin_messages(user_id):
    """Get messages for a specific user (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        messages = integrated_db.get_admin_messages(user_id)
        # Mark user messages as read by admin
        integrated_db.mark_admin_messages_read(user_id, 'user')
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/chats/<int:user_id>/send', methods=['POST'])
@require_auth
def send_admin_reply(user_id):
    """Send a message to user (admin only) with optional file attachment and reply"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        message = data.get('message', '')
        file_url = data.get('file_url')
        file_name = data.get('file_name')
        file_size = data.get('file_size')
        reply_to = data.get('reply_to')
        
        # Must have either message or file
        if not message and not file_url:
            return jsonify({'error': 'Message or file is required'}), 400
        
        success = integrated_db.send_admin_message(user_id, 'admin', message, file_url, file_name, file_size, reply_to)
        
        if success:
            return jsonify({'success': True, 'message': 'Message sent'})
        else:
            return jsonify({'error': 'Failed to send message'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin-chat/message/<int:message_id>', methods=['DELETE'])
@require_auth
def delete_admin_message(message_id):
    """Delete an admin chat message"""
    try:
        user_id = request.current_user['user_id']
        success = integrated_db.delete_admin_message(message_id, user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Message deleted'})
        else:
            return jsonify({'error': 'Message not found or already deleted'}), 404
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
        # First check psychology_traits table
        traits = integrated_db.get_psychology_traits(request.current_user['user_id'])
        
        # If empty, check user_profiles.preferences for assessment data
        if not traits:
            profile = integrated_db.get_user_profile(request.current_user['user_id'])
            if profile and profile.get('preferences'):
                prefs = profile['preferences']
                
                # Convert Big Five from preferences to traits format
                if 'big_five' in prefs:
                    big_five = prefs['big_five']
                    for trait_name, trait_value in big_five.items():
                        traits.append({
                            'trait_name': trait_name,
                            'trait_value': trait_value / 10.0,  # Convert from 0-10 to 0-1
                            'trait_description': f'{trait_name.capitalize()} trait',
                            'created_at': prefs.get('assessment_completed_at', ''),
                            'updated_at': prefs.get('assessment_completed_at', '')
                        })
                
                # Convert Jung Types from preferences
                if 'jung_types' in prefs:
                    jung = prefs['jung_types']
                    for trait_name, trait_value in jung.items():
                        traits.append({
                            'trait_name': f'jung_{trait_name}',
                            'trait_value': (trait_value + 10) / 20.0,  # Convert from -10 to +10 to 0-1
                            'trait_description': f'Jung {trait_name.replace("_", " ").title()}',
                            'created_at': prefs.get('assessment_completed_at', ''),
                            'updated_at': prefs.get('assessment_completed_at', '')
                        })
        
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
            
            # Get current server timestamp
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            
            return jsonify({
                'success': True, 
                'message': 'Message added successfully',
                'ai_response': ai_response.get('response', 'Sorry, I could not generate a response.'),
                'usage': usage,
                'timestamp': timestamp
            })
        
        return jsonify({'success': True, 'message': 'Message added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Redirect home to chatchat interface"""
    return redirect('/chatchat', code=302)

@app.route('/chatchat')
def chatchat_interface():
    """Integrated multi-user AI chatbot interface"""
    return render_template('chatchat.html')

@app.route('/user_logon')
def user_logon_interface():
    """User login interface - same as chatchat but without signup option"""
    return render_template('user_logon.html')

@app.route('/multi-user')
def multi_user_redirect():
    """Redirect old /multi-user URL to /chatchat for backward compatibility"""
    return redirect('/chatchat', code=301)

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

@app.route('/personality-test')
def personality_test_page():
    """Direct access to personality assessment interface"""
    return render_template('personality_test.html')

@app.route('/test-session')
def test_session_page():
    """Debug page for testing session restoration"""
    return render_template('test_session_restoration.html')

# Special endpoint for coach-specific reminder toggle (not in dynamic system)
@app.route('/coach/toggle-reminders', methods=['POST'])
def toggle_reminders():
    try:
        data = request.get_json()
        active = data.get('active', True)
        motivational_bot.toggle_reminders(active)
        return jsonify({'success': True, 'reminders_active': active})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Smart Response System Stats Endpoint
@app.route('/api/smart-response/stats', methods=['GET'])
@require_auth
def smart_response_stats():
    """Get Smart Response statistics for current user"""
    try:
        user_id = request.current_user['user_id']
        
        if not smart_handler:
            return jsonify({'error': 'Smart Response not initialized'}), 500
        
        stats = smart_handler.get_user_stats(user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/context/<character>', methods=['GET'])
@require_auth
def get_conversation_context(character):
    """Get conversation context for a character"""
    try:
        user_id = request.current_user['user_id']
        
        if not context_manager:
            return jsonify({'error': 'Context Manager not initialized'}), 500
        
        summary = context_manager.get_context_summary(user_id, character)
        context = context_manager.get_context_for_ai(user_id, character, [])
        
        return jsonify({
            'summary': summary,
            'recent_topics': context.get('recent_topics', []),
            'ongoing_threads': context.get('ongoing_threads', []),
            'emotional_state': context.get('emotional_state', 'neutral'),
            'last_session': context.get('last_session', 'Never'),
            'message_count': context.get('message_count', 0)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Frontend Error Logging Endpoint
@app.route('/api/log-error', methods=['POST'])
def log_frontend_error():
    """Log frontend errors to database for monitoring and debugging"""
    try:
        data = request.get_json()
        
        # Get user_id if authenticated
        user_data = authenticate_token()
        user_id = user_data.get('user_id') if user_data else None
        
        if not smart_response_conn:
            return jsonify({'status': 'error', 'message': 'Database not initialized'}), 500
        
        cursor = smart_response_conn.cursor()
        cursor.execute('''
            INSERT INTO frontend_errors 
            (user_id, error_message, character, context, user_agent, url, stack_trace)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('error', 'Unknown error'),
            data.get('character'),
            data.get('context'),
            data.get('user_agent'),
            data.get('url'),
            data.get('stack_trace')
        ))
        smart_response_conn.commit()
        
        # Log to console for immediate visibility
        print(f"🐛 Frontend Error: {data.get('error')} (character: {data.get('character')}, user: {user_id})")
        
        return jsonify({'status': 'logged'})
    except Exception as e:
        # Silent fail - don't break frontend if logging fails
        print(f"⚠️ Error logging frontend error: {e}")
        return jsonify({'status': 'failed'}), 200  # Return 200 to not disrupt frontend

# Explicit Context Control Endpoints
@app.route('/api/explicit-context', methods=['GET'])
@require_auth
def get_explicit_context():
    """Get all explicit context for the authenticated user"""
    try:
        user_id = request.current_user['user_id']
        character = request.args.get('character', None)
        context_type = request.args.get('type', None)
        
        if not context_manager or not context_manager.explicit_handler:
            return jsonify({'error': 'Context Manager not initialized'}), 500
        
        context_items = context_manager.explicit_handler.get_explicit_context(
            user_id, character if character else '', context_type
        )
        
        return jsonify({
            'count': len(context_items),
            'items': context_items
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/explicit-context/<int:context_id>', methods=['PUT'])
@require_auth
def update_explicit_context(context_id):
    """Update an explicit context item"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        if not context_manager or not context_manager.explicit_handler:
            return jsonify({'error': 'Context Manager not initialized'}), 500
        
        # Verify ownership
        cursor = context_manager.db.cursor()
        cursor.execute('''
            SELECT user_id FROM explicit_context WHERE id = ?
        ''', (context_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Context not found'}), 404
        
        if row[0] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update the context
        cursor.execute('''
            UPDATE explicit_context
            SET context_value = ?,
                original_statement = ?,
                timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('value'),
            data.get('original_statement', 'Manually updated'),
            context_id
        ))
        context_manager.db.commit()
        
        return jsonify({'success': True, 'message': 'Context updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/explicit-context/<int:context_id>', methods=['DELETE'])
@require_auth
def delete_explicit_context(context_id):
    """Delete (deactivate) an explicit context item"""
    try:
        user_id = request.current_user['user_id']
        
        if not context_manager or not context_manager.explicit_handler:
            return jsonify({'error': 'Context Manager not initialized'}), 500
        
        # Verify ownership
        cursor = context_manager.db.cursor()
        cursor.execute('''
            SELECT user_id FROM explicit_context WHERE id = ?
        ''', (context_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Context not found'}), 404
        
        if row[0] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Deactivate the context
        context_manager.explicit_handler.deactivate_context(context_id)
        
        return jsonify({'success': True, 'message': 'Context removed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/explicit-context/<int:context_id>/reclassify', methods=['POST'])
@require_auth
def reclassify_explicit_context(context_id):
    """Reclassify an explicit context item (change its type)"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        new_type = data.get('context_type')
        new_key = data.get('context_key')
        
        if not context_manager or not context_manager.explicit_handler:
            return jsonify({'error': 'Context Manager not initialized'}), 500
        
        # Verify ownership
        cursor = context_manager.db.cursor()
        cursor.execute('''
            SELECT user_id FROM explicit_context WHERE id = ?
        ''', (context_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Context not found'}), 404
        
        if row[0] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Update type/key
        cursor.execute('''
            UPDATE explicit_context
            SET context_type = ?,
                context_key = ?,
                timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_type, new_key, context_id))
        context_manager.db.commit()
        
        return jsonify({'success': True, 'message': 'Context reclassified'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/explicit-context', methods=['POST'])
@require_auth
def add_explicit_context():
    """Manually add explicit context"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        if not context_manager or not context_manager.explicit_handler:
            return jsonify({'error': 'Context Manager not initialized'}), 500
        
        context_id = context_manager.explicit_handler.store_explicit_context(
            user_id=user_id,
            character=data.get('character', ''),
            context_type=data.get('context_type'),
            context_key=data.get('context_key'),
            context_value=data.get('context_value'),
            original_statement=data.get('original_statement', 'Manually added'),
            priority='CRITICAL',
            confidence=data.get('confidence', 1.0),
            extracted_via='manual_entry'
        )
        
        return jsonify({
            'success': True,
            'context_id': context_id,
            'message': 'Context added'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dual-Layer History Endpoints
@app.route('/api/history/<character>', methods=['GET'])
@require_auth
def get_conversation_history(character):
    """Get conversation history (dual-layer) for a character"""
    try:
        user_id = request.current_user['user_id']
        
        if not history_system:
            return jsonify({'error': 'History System not initialized'}), 500
        
        layer = request.args.get('layer', 'both')  # primary, secondary, or both
        limit = int(request.args.get('limit', 20))
        
        history = history_system.get_conversation_history(
            user_id, character, layer=layer, limit=limit
        )
        
        return jsonify({
            'layer': layer,
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<character>/stats', methods=['GET'])
@require_auth
def get_history_stats(character):
    """Get statistics about conversation history"""
    try:
        user_id = request.current_user['user_id']
        
        if not history_system:
            return jsonify({'error': 'History System not initialized'}), 500
        
        stats = history_system.get_stats(user_id, character)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI Budget Management Endpoints
@app.route('/api/ai-budget/status', methods=['GET'])
def get_ai_budget_status():
    """Get current AI budget status and usage"""
    try:
        if not ai_budget:
            return jsonify({'error': 'AI Budget Manager not initialized'}), 500
        
        report = ai_budget.get_usage_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-budget/notifications', methods=['GET'])
def get_ai_notifications():
    """Get unread AI budget notifications"""
    try:
        if not ai_budget:
            return jsonify({'error': 'AI Budget Manager not initialized'}), 500
        
        notifications = ai_budget.get_unread_notifications()
        return jsonify({
            'count': len(notifications),
            'notifications': notifications
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-budget/notifications/acknowledge', methods=['POST'])
def acknowledge_ai_notifications():
    """Acknowledge AI budget notifications"""
    try:
        if not ai_budget:
            return jsonify({'error': 'AI Budget Manager not initialized'}), 500
        
        data = request.get_json()
        notification_id = data.get('notification_id')
        
        if notification_id == 'all':
            ai_budget.acknowledge_all_notifications()
            return jsonify({'success': True, 'message': 'All notifications acknowledged'})
        elif notification_id:
            ai_budget.acknowledge_notification(int(notification_id))
            return jsonify({'success': True, 'message': 'Notification acknowledged'})
        else:
            return jsonify({'error': 'notification_id required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-budget/reset-circuit-breaker', methods=['POST'])
def reset_ai_circuit_breaker():
    """Reset AI circuit breaker (admin only)"""
    try:
        if not ai_budget:
            return jsonify({'error': 'AI Budget Manager not initialized'}), 500
        
        data = request.get_json()
        reason = data.get('reason', 'Manual reset via API')
        
        # In production: verify admin authorization here
        ai_budget.reset_circuit_breaker(reason)
        
        return jsonify({
            'success': True,
            'message': 'Circuit breaker reset',
            'reason': reason
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Note: Coach, Sage, Marcus, Psychologist routes now handled by dynamic character system

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

@app.route('/personality/assessment/back/<user_id>', methods=['POST'])
def go_back_assessment(user_id):
    """Go back to previous question in assessment"""
    try:
        success = personality_profiler.go_back(user_id)
        if success:
            question_ui = personality_assessment_ui.get_current_question_ui(user_id)
            return jsonify(question_ui)
        else:
            return jsonify({'error': 'Cannot go back'}), 400
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

# Register dynamic character routes for ALL characters with Smart Response
print("\n=== Registering Character Routes ===")
register_character_routes(app, all_characters, process_with_smart_response)
print("✓ Dynamic routes registered for all 8 characters with Smart Response")

if __name__ == '__main__':
    # Enable auto-documentation only in development (not production)
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    if not is_production:
        enable_auto_docs()
        update_docs_now()
    else:
        print("📚 Auto-docs disabled in production mode")
    
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


# ============================================
# AI USAGE MONITORING (ADMIN ONLY)
# ============================================

@app.route('/admin/ai-usage-monitor')
@require_auth
def ai_usage_monitor_page():
    """AI Usage Monitoring Dashboard (Admin Only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return "Access Denied: Administrator access required", 403
        
        return render_template('ai_usage_monitor.html')
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/api/admin/ai-usage/summary')
@require_auth
def get_ai_usage_summary():
    """Get summary statistics for AI usage"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Today's calls
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE DATE(timestamp) = DATE('now')
            AND success = 1
        ''')
        today_calls = cursor.fetchone()[0]
        
        # Month's calls
        cursor.execute('''
            SELECT COUNT(*) FROM ai_usage_log
            WHERE DATE(timestamp, 'start of month') = DATE('now', 'start of month')
            AND success = 1
        ''')
        month_calls = cursor.fetchone()[0]
        
        # Costs (assuming $0.002 per call)
        today_cost = today_calls * 0.002
        month_cost = month_calls * 0.002
        
        conn.close()
        
        return jsonify({
            'today_calls': today_calls,
            'month_calls': month_calls,
            'today_cost': today_cost,
            'month_cost': month_cost,
            'system_cap': 2000,
            'month_cap_dollars': 120
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ai-usage/daily')
@require_auth
def get_daily_ai_usage():
    """Get today's AI usage by user"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        sort_by = request.args.get('sort', 'calls_desc')
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Get today's usage per user
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.role,
                COUNT(a.id) as call_count
            FROM users u
            LEFT JOIN ai_usage_log a ON u.id = a.user_id 
                AND DATE(a.timestamp) = DATE('now')
                AND a.success = 1
            GROUP BY u.id, u.username, u.role
            HAVING call_count > 0
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'is_admin': row[2] == 'administrator',
                'calls': row[3]
            })
        
        conn.close()
        
        # Sort
        if sort_by == 'calls_desc':
            users.sort(key=lambda x: x['calls'], reverse=True)
        elif sort_by == 'calls_asc':
            users.sort(key=lambda x: x['calls'])
        elif sort_by == 'username':
            users.sort(key=lambda x: x['username'].lower())
        elif sort_by == 'role':
            users.sort(key=lambda x: (not x['is_admin'], x['username'].lower()))
        
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ai-usage/monthly')
@require_auth
def get_monthly_ai_usage():
    """Get this month's AI usage by user"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if user_role != 'administrator':
            return jsonify({'error': 'Admin access required'}), 403
        
        sort_by = request.args.get('sort', 'calls_desc')
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Get month's usage per user
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.role,
                COUNT(a.id) as total_calls,
                DATE(a.timestamp) as call_date
            FROM users u
            LEFT JOIN ai_usage_log a ON u.id = a.user_id 
                AND DATE(a.timestamp, 'start of month') = DATE('now', 'start of month')
                AND a.success = 1
            GROUP BY u.id, u.username, u.role, call_date
        ''')
        
        # Aggregate by user
        user_data = {}
        for row in cursor.fetchall():
            user_id = row[0]
            if user_id not in user_data:
                user_data[user_id] = {
                    'user_id': user_id,
                    'username': row[1],
                    'is_admin': row[2] == 'administrator',
                    'total_calls': 0,
                    'daily_calls': []
                }
            user_data[user_id]['total_calls'] += row[3]
            if row[4]:  # If there's a date
                user_data[user_id]['daily_calls'].append(row[3])
        
        # Calculate stats
        users = []
        for user_id, data in user_data.items():
            if data['total_calls'] > 0:
                daily_calls = data['daily_calls']
                avg_daily = data['total_calls'] / max(len(daily_calls), 1)
                peak_day = max(daily_calls) if daily_calls else 0
                
                # Determine trend (simple: compare first half vs second half)
                if len(daily_calls) >= 4:
                    mid = len(daily_calls) // 2
                    first_half_avg = sum(daily_calls[:mid]) / mid
                    second_half_avg = sum(daily_calls[mid:]) / (len(daily_calls) - mid)
                    if second_half_avg > first_half_avg * 1.2:
                        trend = 'up'
                    elif second_half_avg < first_half_avg * 0.8:
                        trend = 'down'
                    else:
                        trend = 'stable'
                else:
                    trend = 'stable'
                
                users.append({
                    'user_id': user_id,
                    'username': data['username'],
                    'is_admin': data['is_admin'],
                    'total_calls': data['total_calls'],
                    'avg_daily': avg_daily,
                    'peak_day': peak_day,
                    'trend': trend
                })
        
        conn.close()
        
        # Sort
        if sort_by == 'calls_desc':
            users.sort(key=lambda x: x['total_calls'], reverse=True)
        elif sort_by == 'calls_asc':
            users.sort(key=lambda x: x['total_calls'])
        elif sort_by == 'username':
            users.sort(key=lambda x: x['username'].lower())
        elif sort_by == 'cost_desc':
            users.sort(key=lambda x: x['total_calls'], reverse=True)
        
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
