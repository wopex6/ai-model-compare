# CRITICAL: Load .env FIRST before any other imports!
# This must be at the top because ai_compare modules also call load_dotenv()
from pathlib import Path
from dotenv import load_dotenv

# Load with ABSOLUTE path (critical for WSGI/PythonAnywhere)
_env_path = Path(__file__).parent / '.env'
load_dotenv(_env_path, override=True)

# Fix Windows console encoding for Unicode characters (emojis, checkmarks, etc.)
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Now import everything else
from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory
from flask_cors import CORS
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
from automated_greeting_system import AutomatedGreetingSystem
from database_backup import BackupManager
from email_service import EmailService

# Import Personality Systems
from smart_response.trait_inference import TraitInferenceEngine

# Import Smart Response System
from smart_response.handler import SmartResponseHandler
# Import Domain Character System
from smart_response.characters import CharacterManager, DOMAIN_CHARACTER_CONFIGS, create_ai_integration
# Import User Personalization System
from smart_response.user_personalization import UserPersonalization
# Import new modules (optional - graceful degradation)
try:
    from smart_response.cache_manager import get_cache, cached
    from smart_response.rate_limiter import get_rate_limiter, InputValidator, get_csrf
    from smart_response.monitoring import get_error_tracker, get_uptime_monitor, get_alert_manager, track_error
    from smart_response.context_window import create_context_window, create_multi_turn_memory, create_character_switcher
    NEW_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: New modules not available: {e}")
    NEW_MODULES_AVAILABLE = False
    # Provide dummy functions
    def get_cache(): return None
    def get_rate_limiter(): return None
    def get_error_tracker(): return None
    def get_uptime_monitor(): return None
    def get_alert_manager(db=None): return None
    def track_error(*args, **kwargs): pass
import sqlite3

# Disable auto-docs in production
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
ALLOWED_EXTENSIONS = {
    # Text/Documents
    'txt', 'md', 'pdf', 'doc', 'docx', 'rtf',
    # Data formats (AI-readable)
    'json', 'csv', 'xml', 'yaml', 'yml',
    # Code files
    'py', 'js', 'ts', 'html', 'css', 'sql', 'sh', 'bat',
    # Spreadsheets
    'xls', 'xlsx',
    # Images
    'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp',
    # Audio/Video
    'mp3', 'wav', 'ogg', 'm4a', 'mp4', 'avi', 'mov', 'webm',
    # Archives
    'zip', 'rar'
}
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

# Initialize analytics tables at startup
try:
    from smart_response.user_analytics import create_user_analytics
    _analytics_conn = integrated_db.get_connection()
    _analytics = create_user_analytics(_analytics_conn)
    _analytics_conn.close()
    print("[STARTUP] Analytics tables initialized")
except Exception as e:
    print(f"[STARTUP] Analytics init warning: {e}")

# Initialize user personalization system (per-user adaptive parameters)
# Pass integrated_db instance (not connection) for thread-safe access
user_personalization = UserPersonalization(integrated_db)
print("✓ User personalization system initialized")

# Pre-declare variables used by greeting_ai_call (initialized later in Smart Response section)
domain_character_ai = None
ai_budget = None

# AI call wrapper function for greeting system (initialized later after ai_budget is available)
def greeting_ai_call(system_prompt: str, user_message: str, purpose: str = 'greeting', character: str = 'coordinator'):
    """Wrapper function to call AI for context-aware greeting generation"""
    try:
        if not domain_character_ai:
            return None
        
        # Check budget before AI call (system call - suppress notifications)
        if ai_budget:
            allowed, reason = ai_budget.can_make_ai_call(
                user_id=None, 
                is_admin=True,  # System calls use admin limits
                is_background=True,
                suppress_notifications=True  # Never show notifications for greeting calls
            )
            if not allowed:
                print(f"⏭️ AI greeting call denied: {reason}")
                return None
        
        # Use domain character AI to generate response
        response = domain_character_ai.call_ai_direct(
            system_prompt=system_prompt,
            user_message=user_message,
            character_id=character
        )
        
        if response:
            # Log successful call
            if ai_budget:
                ai_budget.log_ai_call(
                    call_type='context_prompt',
                    purpose=purpose,
                    success=True,
                    character=character,
                    is_background=True
                )
            return {'success': True, 'response': response}
        return None
    except Exception as e:
        print(f"❌ Error in greeting AI call: {e}")
        return None

greeting_system = AutomatedGreetingSystem(integrated_db, ai_call_func=greeting_ai_call)
email_service = EmailService()
ai_compare = AICompare()
chatbot = AIChatbot()

# Initialize Goal Coaching System for proactive user engagement
from goal_coaching_system import create_goal_coaching_system
goal_coaching_system = create_goal_coaching_system(integrated_db, ai_call_func=greeting_ai_call)
print("✓ Goal Coaching System initialized (proactive engagement)")

# Initialize backup system
backup_manager = BackupManager()
# Backup on startup
backup_manager.backup_all(reason="startup")
# Start automatic backup scheduler (every 4 hours)
backup_manager.start_scheduler()

# Initialize and start greeting scheduler (pass greeting_system with AI call func)
from greeting_scheduler import GreetingScheduler
greeting_scheduler = GreetingScheduler(check_interval_seconds=60, greeting_system=greeting_system)
greeting_scheduler.start()

# Run greeting cleanup on startup (removes old non-context greetings)
print("🧹 Running greeting cleanup on startup...")
greeting_system.cleanup_old_greetings(days_to_keep=7)

# Initialize Trait Inference Engine
trait_inference = TraitInferenceEngine(integrated_db)

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
background_scheduler = None  # Will be initialized if available
try:
    from smart_response.handler import SmartResponseHandler
    from smart_response.conversation_context import ConversationContextManager
    from smart_response.dual_layer_history import DualLayerHistorySystem
    from smart_response.ai_budget_manager import AIBudgetManager
    from smart_response.user_context_manager import create_user_context_manager
    from smart_response.proactive_clarification import create_clarification_system
    from smart_response.character_traits import create_character_trait_system
    from smart_response.developer_analytics import create_developer_analytics
    from smart_response.personality_context_integrator import create_personality_integrator
    from smart_response.explicit_context_handler import ExplicitContextHandler
    smart_response_conn = sqlite3.connect('integrated_users.db', check_same_thread=False)
    smart_handler = SmartResponseHandler(smart_response_conn)
    context_manager = ConversationContextManager(smart_response_conn)
    history_system = DualLayerHistorySystem(smart_response_conn)
    ai_budget = AIBudgetManager(smart_response_conn)
    user_context_mgr = create_user_context_manager(smart_response_conn, ai_budget)
    clarification_system = create_clarification_system(smart_response_conn)
    character_trait_system = create_character_trait_system(smart_response_conn)
    developer_analytics = create_developer_analytics(smart_response_conn)
    personality_integrator = create_personality_integrator(smart_response_conn, integrated_db)
    explicit_context_handler = ExplicitContextHandler(smart_response_conn)
    print("✓ User Context Manager initialized (preferences, goals, language learning)")
    print("✓ Proactive Clarification System initialized")
    print("✓ Character Trait System initialized (12D trait-space matching)")
    print("✓ Developer Analytics initialized")
    print("✓ Personality Context Integrator initialized (Big5 + profile → conversations)")
    
    # Clear ALL AI budget notifications on startup (prevents stale notifications)
    try:
        cursor = smart_response_conn.cursor()
        # DELETE instead of just marking acknowledged - more reliable
        cursor.execute('DELETE FROM ai_budget_notifications')
        deleted = cursor.rowcount
        smart_response_conn.commit()
        print(f"✓ Deleted ALL {deleted} AI budget notifications on startup", flush=True)
    except Exception as e:
        print(f"⚠️ Could not clear notifications: {e}", flush=True)
    
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
    
    # Initialize Domain Character Manager
    domain_character_manager = CharacterManager(smart_response_conn)
    domain_character_manager.save_domain_characters_to_db()
    print("✓ Domain Character Manager initialized")
    
    # Initialize Domain Character AI Integration (with db for error logging)
    domain_character_ai = create_ai_integration(ai_budget, smart_response_conn)
    print("✓ Domain Character AI Integration initialized")
except Exception as e:
    print(f"✗ Error initializing Smart Response: {e}")
    import traceback
    traceback.print_exc()
    smart_handler = None
    context_manager = None
    history_system = None
    ai_budget = None
    user_context_mgr = None
    clarification_system = None
    character_trait_system = None
    developer_analytics = None
    personality_integrator = None
    explicit_context_handler = None
    domain_character_manager = None
    domain_character_ai = None
    background_scheduler = None
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
    print(f"🔵 process_with_smart_response called: character={character_name}, msg={message[:50]}...")
    
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
    
    # Load from database if not in memory (after server restart)
    if not message_history and user_id and history_key and history_system:
        try:
            # Load last 20 messages from dual-layer history
            db_history = history_system.get_conversation_history(
                user_id, character_name, layer='primary', limit=20
            )
            
            # Convert to message_history format (chronological order)
            db_history.reverse()  # Oldest first
            message_history = []
            for msg in db_history:
                # Add user message
                message_history.append({
                    'role': 'user',
                    'content': msg['user_message'],
                    'timestamp': msg['timestamp']
                })
                # Add assistant response
                message_history.append({
                    'role': 'assistant',
                    'content': msg['assistant_response'],
                    'timestamp': msg['timestamp']
                })
            
            # Cache in memory for this session
            message_histories[history_key] = message_history
            
            if message_history:
                print(f"📚 Loaded {len(message_history)//2} conversation turns from database for {character_name}")
        except Exception as e:
            print(f"⚠️ Failed to load history from database: {e}")
            message_history = []
    
    # Smart Response only for authenticated users
    clarification_questions = []  # Store any clarification questions to append to response
    situation_analysis = None  # Store situation analysis for context
    
    # DEBUG: Check what's available
    print(f"🔍 smart_handler={smart_handler is not None}, user_id={user_id}, context_manager={context_manager is not None}")
    
    if smart_handler and user_id and context_manager:
        # Get conversation context
        context = context_manager.get_context_for_ai(user_id, character_name, message_history)
        print(f"📚 Context loaded: {len(context.get('recent_topics', []))} topics, {context.get('message_count', 0)} messages")
        
        # PROACTIVE CLARIFICATION: Analyze message for ambiguity
        if clarification_system:
            try:
                confidence, questions = clarification_system.analyze_message(message, context)
                print(f"❓ Confidence: {confidence.overall:.0%} (goal={confidence.goal_clarity:.0%}, emotion={confidence.emotional_clarity:.0%})")
                if questions:
                    clarification_questions = questions[:1]  # Max 1 question per response
                    print(f"   → Question: {questions[0].question}")
            except Exception as e:
                print(f"⚠️ Clarification analysis failed: {e}")
        else:
            print("⚠️ clarification_system not initialized")
        
        # CHARACTER TRAIT ANALYSIS: Understand user's situation
        if character_trait_system:
            try:
                situation_analysis = character_trait_system.analyze_situation(message, context)
                # Log with flags for consistency with Domain Characters
                flags = []
                if situation_analysis.needs_validation:
                    flags.append("needs_validation")
                if situation_analysis.needs_action:
                    flags.append("needs_action")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"🎭 Situation: {situation_analysis.emotional_state} ({situation_analysis.goal_type}){flag_str}")
            except Exception as e:
                print(f"⚠️ Situation analysis failed: {e}")
        else:
            print("⚠️ character_trait_system not initialized")
        
        # EXPLICIT CONTEXT EXTRACTION: Capture user's explicit statements with CRITICAL priority
        explicit_context_items = []
        past_explicit_context = ""
        if explicit_context_handler:
            try:
                # Extract new explicit context from current message
                explicit_context_items = explicit_context_handler.extract_explicit_context(
                    user_id, character_name, message
                )
                if explicit_context_items:
                    print(f"📌 [EXPLICIT] Extracted {len(explicit_context_items)} explicit context items")
                    for item in explicit_context_items:
                        print(f"   → {item['type']}: {item['value']} ({item['priority']})")
                
                # Retrieve ALL past explicit context (goals, preferences, values user has stated)
                past_explicit_context = explicit_context_handler.format_for_ai_prompt(user_id, character_name)
                if past_explicit_context:
                    print(f"📚 [EXPLICIT] Retrieved past user statements for AI")
            except Exception as e:
                print(f"⚠️ Explicit context extraction failed: {e}")
        
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
            
            # OUTCOME RECORDING: Learn from follow-up patterns
            if character_trait_system and 'situation' in prev:
                try:
                    # Import config for thresholds
                    from smart_response.config import (
                        QUICK_FOLLOWUP_THRESHOLD, NORMAL_FOLLOWUP_THRESHOLD,
                        SATISFACTION_QUICK_FOLLOWUP, SATISFACTION_NORMAL_FOLLOWUP,
                        SATISFACTION_SLOW_FOLLOWUP
                    )
                    # Infer satisfaction from follow-up timing
                    if time_diff < QUICK_FOLLOWUP_THRESHOLD:
                        satisfaction = SATISFACTION_QUICK_FOLLOWUP  # Quick engagement
                    elif time_diff < NORMAL_FOLLOWUP_THRESHOLD:
                        satisfaction = SATISFACTION_NORMAL_FOLLOWUP  # Normal pace
                    else:
                        satisfaction = SATISFACTION_SLOW_FOLLOWUP  # Long gap
                    
                    character_trait_system.record_outcome(
                        user_id=user_id,
                        character_id=character_name,
                        situation=prev['situation'],
                        conversation_length=prev.get('conv_length', 1),
                        satisfaction=satisfaction
                    )
                except Exception as e:
                    print(f"⚠️ Outcome recording failed: {e}")
        
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
            
            # Store for learning (including situation for outcome recording)
            previous_interactions[prev_key] = {
                'message': message,
                'response_type': 'quick_reply',
                'timestamp': datetime.now(),
                'situation': situation_analysis,
                'conv_length': len(message_history)
            }
            
            return result
        
        # Log that we're using full AI
        print(f"💸 API CALL ({character_name}) - Full AI for: '{message}' (confidence: {response_data['confidence']:.2f})")
        
        # Format context for AI prompt
        context_prompt = context_manager.format_context_for_prompt(context)
        
        # Add situation analysis to context (from character trait system)
        situation_context = ""
        response_style_hint = ""
        if situation_analysis:
            situation_parts = []
            if situation_analysis.emotional_state != 'neutral':
                situation_parts.append(f"User appears: {situation_analysis.emotional_state}")
            if situation_analysis.goal_type != 'general':
                situation_parts.append(f"Seeking: {situation_analysis.goal_type}")
            if situation_analysis.needs_validation:
                situation_parts.append("Needs emotional validation")
            if situation_analysis.needs_action:
                situation_parts.append("Wants actionable steps")
            if situation_parts:
                situation_context = "\n[Current Situation]\n" + "\n".join(f"- {p}" for p in situation_parts)
            
            # DYNAMIC CHARACTER MATCHING: Adjust response style based on situation
            if character_trait_system:
                try:
                    from smart_response.config import CHARACTER_MATCH_THRESHOLD, URGENCY_THRESHOLD
                    matched_char, match_score, reasoning = character_trait_system.match_character(situation_analysis)
                    if match_score > CHARACTER_MATCH_THRESHOLD:  # Good match - use character's style
                        response_style_hint = f"\n[Response Style Guidance]\n"
                        response_style_hint += f"- Approach: {matched_char.philosophical_lens}\n"
                        if situation_analysis.needs_validation:
                            response_style_hint += f"- Prioritize emotional acknowledgment before solutions\n"
                        if situation_analysis.needs_action:
                            response_style_hint += f"- Include concrete, actionable next steps\n"
                        if situation_analysis.urgency > URGENCY_THRESHOLD:
                            response_style_hint += f"- Be direct and concise - user needs quick help\n"
                        print(f"🎯 Character match: {matched_char.display_name} ({match_score:.0%}) - {reasoning}")
                except Exception as e:
                    print(f"⚠️ Character matching failed: {e}")
        
        # Add explicit context (user's own words - CRITICAL priority)
        # This includes BOTH current message extractions AND past stated context
        explicit_context = ""
        if past_explicit_context:
            # Past context from database (goals, preferences, values user has stated before)
            explicit_context = f"\n{past_explicit_context}"
        if explicit_context_items:
            # Add current message extractions
            explicit_parts = []
            for item in explicit_context_items:
                if item['priority'] == 'CRITICAL':
                    explicit_parts.append(f"User just stated: \"{item['value']}\" ({item['type']})")
            if explicit_parts:
                explicit_context += "\n[From This Message]\n" + "\n".join(f"- {p}" for p in explicit_parts)
        
        if context_prompt or situation_context or explicit_context or response_style_hint:
            # Prepend context to message so AI receives it
            # This makes AI aware of user's emotional state, goals, and preferences
            full_context = (context_prompt + situation_context + explicit_context + response_style_hint).strip()
            enhanced_message = f"{full_context}\n\nUser's current message: {message}"
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
        
        # Provide user-friendly error messages based on error type
        if "timeout" in ai_error.lower():
            user_message = "The AI is taking longer than usual to respond. Please try again - it should work on the next attempt."
        elif "api" in ai_error.lower() or "key" in ai_error.lower():
            user_message = "There's a temporary issue with the AI service. Our team has been notified. Please try again in a few moments."
        elif "rate limit" in ai_error.lower():
            user_message = "We're getting a lot of requests right now. Please wait a moment and try again."
        elif "connection" in ai_error.lower() or "network" in ai_error.lower():
            user_message = "Having trouble connecting to the AI service. Please check your internet connection and try again."
        else:
            user_message = "I'm having trouble processing your request right now. Please try again in a moment."
        
        response = {
            'response': user_message,
            'type': 'api_error',
            'error': ai_error,  # Technical details for debugging
            'retry_suggested': True
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
            'timestamp': datetime.now(),
            'situation': situation_analysis,
            'conv_length': len(message_history)
        }
    
    # Add metadata
    if isinstance(response, dict):
        response['type'] = 'full_ai'
        response['smart_response'] = True
    
    # PROACTIVE CLARIFICATION: Append clarification question to response
    if clarification_questions and clarification_system:
        try:
            clarification_text = clarification_system.format_clarification_for_response(
                clarification_questions, 
                context.get('user_language') if context else None
            )
            if clarification_text:
                if isinstance(response, dict) and 'response' in response:
                    response['response'] += clarification_text
                    response['has_clarification'] = True
                elif isinstance(response, str):
                    response += clarification_text
                print(f"✅ Added clarification question to response")
        except Exception as e:
            print(f"⚠️ Failed to append clarification: {e}")
    
    # Add situation analysis to response metadata
    if situation_analysis and isinstance(response, dict):
        response['situation'] = {
            'emotional_state': situation_analysis.emotional_state,
            'goal_type': situation_analysis.goal_type,
            'needs_validation': situation_analysis.needs_validation,
            'needs_action': situation_analysis.needs_action
        }
    
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

def has_admin_access(user_role):
    """Check if user has admin-level access (administrator or developer)"""
    return user_role in ('administrator', 'developer')

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
        
        # Get user role (new users are 'guest' by default)
        user_role = integrated_db.get_user_role(user_id)
        
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
            'role': user_role,  # Include role in signup response
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
        
        # Get user role
        user_role = integrated_db.get_user_role(user['id'])
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        
        # Also set session for cross-page compatibility
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user_role
        
        print(f"🔐 Login successful for user {user['id']} ({user['username']})")
        print(f"   Session set: {dict(session)}")
        print(f"   Token generated: {token[:20]}...")
        
        return jsonify({
            'success': True,
            'token': token,
            'user_id': user['id'],
            'username': user['username'],
            'role': user_role  # Include role in login response
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
        if not has_admin_access(user_role):
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
        if not has_admin_access(user_role):
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
        if not has_admin_access(user_role):
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
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        new_role = data.get('role')
        
        # Validate role
        valid_roles = ['guest', 'user', 'paid', 'master', 'administrator', 'developer']
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
        if not has_admin_access(user_role):
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
        if not has_admin_access(user_role):
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
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        stats = integrated_db.get_usage_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/smart-response-analytics')
@require_auth
def get_smart_response_analytics():
    """Get analytics for smart response system (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        analytics = {
            'character_system': None,
            'explicit_context': None,
            'character_expansion': None
        }
        
        # Character trait system stats
        if character_trait_system:
            try:
                cursor = character_trait_system.db.cursor()
                
                # Character usage stats
                cursor.execute('''
                    SELECT character_id, COUNT(*) as uses, 
                           AVG(user_satisfaction) as avg_satisfaction
                    FROM character_usage_outcomes
                    GROUP BY character_id
                    ORDER BY uses DESC
                ''')
                char_usage = [{'character': r[0], 'uses': r[1], 'avg_satisfaction': r[2]} 
                             for r in cursor.fetchall()]
                
                # Total characters
                cursor.execute('SELECT COUNT(*) FROM character_library')
                total_chars = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM character_library WHERE is_base = 1')
                base_chars = cursor.fetchone()[0]
                
                # Character effectiveness scores
                cursor.execute('''
                    SELECT character_id, display_name, effectiveness_score, usage_count
                    FROM character_library
                    ORDER BY effectiveness_score DESC
                ''')
                effectiveness = [{'character': r[0], 'name': r[1], 
                                 'effectiveness': r[2], 'usage_count': r[3]} 
                                for r in cursor.fetchall()]
                
                # Best performing situations
                cursor.execute('''
                    SELECT character_id, situation_json, AVG(user_satisfaction) as avg_sat,
                           COUNT(*) as count
                    FROM character_usage_outcomes
                    WHERE user_satisfaction IS NOT NULL
                    GROUP BY character_id, situation_json
                    HAVING count >= 3
                    ORDER BY avg_sat DESC
                    LIMIT 10
                ''')
                best_situations = [{'character': r[0], 'situation': r[1], 
                                   'avg_satisfaction': r[2], 'count': r[3]} 
                                  for r in cursor.fetchall()]
                
                analytics['character_system'] = {
                    'total_characters': total_chars,
                    'base_characters': base_chars,
                    'ai_generated_characters': total_chars - base_chars,
                    'usage_by_character': char_usage,
                    'effectiveness_ranking': effectiveness,
                    'best_performing_situations': best_situations
                }
            except Exception as e:
                analytics['character_system'] = {'error': str(e)}
        
        # Explicit context stats
        if explicit_context_handler:
            try:
                cursor = explicit_context_handler.db.cursor()
                
                cursor.execute('''
                    SELECT context_type, COUNT(*) as count,
                           COUNT(DISTINCT user_id) as unique_users
                    FROM explicit_context
                    WHERE active = 1
                    GROUP BY context_type
                    ORDER BY count DESC
                ''')
                context_types = [{'type': r[0], 'count': r[1], 'unique_users': r[2]} 
                                for r in cursor.fetchall()]
                
                cursor.execute('SELECT COUNT(*) FROM explicit_context WHERE active = 1')
                total_active = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM explicit_context')
                users_with_context = cursor.fetchone()[0]
                
                analytics['explicit_context'] = {
                    'total_active_items': total_active,
                    'users_with_context': users_with_context,
                    'by_type': context_types
                }
            except Exception as e:
                analytics['explicit_context'] = {'error': str(e)}
        
        # Character expansion stats (if available)
        if character_trait_system:
            try:
                cursor = character_trait_system.db.cursor()
                
                cursor.execute('''
                    SELECT COUNT(*) FROM trait_space_gaps WHERE filled_by IS NULL
                ''')
                unfilled = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM trait_space_gaps WHERE filled_by IS NOT NULL
                ''')
                filled = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM character_generation_log WHERE success = 1
                ''')
                successful_gens = cursor.fetchone()[0]
                
                analytics['character_expansion'] = {
                    'unfilled_gaps': unfilled,
                    'filled_gaps': filled,
                    'successful_generations': successful_gens
                }
            except Exception as e:
                analytics['character_expansion'] = {'error': str(e)}
        
        # Domain character usage stats
        domain_char_stats = {}
        try:
            cursor = smart_response_conn.cursor()
            cursor.execute('''
                SELECT character, COUNT(*) as uses, 
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                       AVG(response_time_ms) as avg_response
                FROM ai_usage_log
                WHERE character IS NOT NULL
                AND timestamp > datetime('now', '-30 days')
                GROUP BY character
                ORDER BY uses DESC
            ''')
            for row in cursor.fetchall():
                char_name = row[0]
                uses = row[1]
                successes = row[2] or 0
                avg_resp = row[3]
                domain_char_stats[char_name] = {
                    'uses': uses,
                    'success_rate': round((successes / uses) * 100, 1) if uses > 0 else 0,
                    'avg_response_ms': round(avg_resp) if avg_resp else None
                }
        except Exception as e:
            print(f"Domain char stats error: {e}")
        
        # Format response for frontend compatibility
        explicit_ctx = analytics.get('explicit_context') or {}
        by_type_list = explicit_ctx.get('by_type', [])
        # Convert list to dict for frontend: {type: count}
        by_type_dict = {item['type']: item['count'] for item in by_type_list} if by_type_list else {}
        
        char_system = analytics.get('character_system') or {}
        effectiveness_list = char_system.get('effectiveness_ranking', [])
        # Convert to dict for frontend: {character_name: score}
        effectiveness_dict = {item['name']: item['effectiveness'] for item in effectiveness_list} if effectiveness_list else {}
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            # Frontend-compatible format
            'explicit_context_stats': {
                'total_items': explicit_ctx.get('total_active_items', 0),
                'users_with_context': explicit_ctx.get('users_with_context', 0),
                'by_type': by_type_dict
            },
            'character_stats': {
                'total': char_system.get('total_characters', 0),
                'effectiveness': effectiveness_dict
            },
            'domain_character_stats': domain_char_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/populate-test-data', methods=['POST'])
@require_auth
def populate_test_data():
    """Populate test data for analytics dashboard (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        results = {'character_effectiveness': [], 'background_tasks': [], 'tokens': []}
        import random
        
        # 1. Update character effectiveness
        if character_trait_system:
            cursor = character_trait_system.db.cursor()
            cursor.execute('SELECT character_id, display_name FROM character_library')
            characters = cursor.fetchall()
            
            effectiveness_map = {
                'The Cheerleader': 0.88, 'The Coach': 0.82, 'The Mentor': 0.76,
                'The Philosopher': 0.71, 'The Realist': 0.67, 'The Sage': 0.63,
                'The Stoic': 0.58, 'The Strategist': 0.54, 'The Therapist': 0.49
            }
            
            for char_id, name in characters:
                score = effectiveness_map.get(name, round(0.45 + (hash(name) % 40) / 100, 2))
                usage = random.randint(15, 80)
                cursor.execute('''
                    UPDATE character_library 
                    SET effectiveness_score = ?, usage_count = ?
                    WHERE character_id = ?
                ''', (score, usage, char_id))
                results['character_effectiveness'].append({'name': name, 'score': score})
            
            character_trait_system.db.commit()
        
        # 2. Create background task log
        cursor = smart_response_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS background_task_log (
                id INTEGER PRIMARY KEY, task_name TEXT, last_run TIMESTAMP,
                next_run TIMESTAMP, status TEXT, run_count INTEGER, last_duration_ms INTEGER
            )
        ''')
        cursor.execute('DELETE FROM background_task_log')
        
        from datetime import timedelta
        now = datetime.now()
        tasks = [
            ('context_maintenance', now - timedelta(hours=2), now + timedelta(hours=4), 'completed', 15),
            ('pattern_expansion', now - timedelta(hours=6), now + timedelta(hours=18), 'completed', 8),
            ('character_expansion', now - timedelta(days=1), now + timedelta(days=6), 'completed', 2),
            ('monthly_cleanup', now - timedelta(days=15), now + timedelta(days=15), 'completed', 1),
        ]
        for task_name, last_run, next_run, status, run_count in tasks:
            cursor.execute('''
                INSERT INTO background_task_log (task_name, last_run, next_run, status, run_count)
                VALUES (?, ?, ?, ?, ?)
            ''', (task_name, last_run.isoformat(), next_run.isoformat(), status, run_count))
            results['background_tasks'].append({'task': task_name, 'status': status})
        
        # 3. Add missing columns, then update tokens and costs
        try:
            cursor.execute('ALTER TABLE ai_usage_log ADD COLUMN model TEXT')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE ai_usage_log ADD COLUMN response_time_ms INTEGER')
        except:
            pass
        
        models = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo', 'claude-3-haiku']
        model_costs = {
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        }
        
        cursor.execute('SELECT id, call_type FROM ai_usage_log ORDER BY timestamp DESC LIMIT 50')
        rows = cursor.fetchall()
        for i, (row_id, call_type) in enumerate(rows):
            in_tok = 120 + random.randint(0, 80)
            out_tok = 200 + random.randint(0, 150)
            model = models[i % len(models)]
            costs = model_costs[model]
            cost = round((in_tok / 1000) * costs['input'] + (out_tok / 1000) * costs['output'], 6)
            response_time = 800 + random.randint(0, 1200)  # 800-2000ms
            cursor.execute('UPDATE ai_usage_log SET input_tokens = ?, output_tokens = ?, model = ?, estimated_cost = ?, response_time_ms = ? WHERE id = ?',
                          (in_tok, out_tok, model, cost, response_time, row_id))
        results['tokens'].append({'updated': len(rows)})
        
        smart_response_conn.commit()
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/background-tasks/run', methods=['POST'])
@require_auth
def run_background_task():
    """Manually trigger a background task (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        task_name = data.get('task')
        
        valid_tasks = ['context_maintenance', 'pattern_expansion', 
                       'character_expansion', 'monthly_cleanup']
        
        if not task_name:
            return jsonify({
                'error': 'Task name required',
                'valid_tasks': valid_tasks
            }), 400
        
        if task_name not in valid_tasks:
            return jsonify({
                'error': f'Invalid task: {task_name}',
                'valid_tasks': valid_tasks
            }), 400
        
        # Run the task
        if background_scheduler:
            result = background_scheduler.run_manual_task(task_name)
            return jsonify({
                'success': True,
                'task': task_name,
                'result': result
            })
        else:
            return jsonify({'error': 'Background scheduler not available'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/cost-alert', methods=['POST'])
@require_auth
def set_cost_alert():
    """Set cost alert threshold (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        threshold = data.get('threshold', 1.0)
        
        if threshold < 0.10:
            return jsonify({'error': 'Minimum threshold is $0.10'}), 400
        
        # Store in settings
        cursor = smart_response_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            INSERT OR REPLACE INTO admin_settings (key, value, updated_at)
            VALUES ('cost_alert_threshold', ?, CURRENT_TIMESTAMP)
        ''', (str(threshold),))
        smart_response_conn.commit()
        
        return jsonify({'success': True, 'threshold': threshold})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/background-tasks/status', methods=['GET'])
@require_auth
def get_background_task_status():
    """Get background task scheduler status (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get last run times from database if available
        task_info = {}
        try:
            cursor = smart_response_conn.cursor()
            cursor.execute('''
                SELECT task_name, last_run, next_run, status, run_count
                FROM background_task_log
                ORDER BY last_run DESC
            ''')
            for row in cursor.fetchall():
                task_info[row[0]] = {
                    'last_run': row[1],
                    'next_run': row[2],
                    'status': row[3],
                    'run_count': row[4],
                    'running': row[3] == 'running'
                }
        except:
            pass  # Table might not exist
        
        # Default tasks with status
        default_tasks = {
            'context_maintenance': {'status': 'available', 'running': False},
            'pattern_expansion': {'status': 'available', 'running': False},
            'character_expansion': {'status': 'available', 'running': False},
            'monthly_cleanup': {'status': 'available', 'running': False}
        }
        
        # Merge with actual task info
        for task_name, info in task_info.items():
            if task_name in default_tasks:
                default_tasks[task_name].update(info)
            else:
                default_tasks[task_name] = info
        
        if background_scheduler:
            return jsonify({
                'success': True,
                'running': background_scheduler.running,
                'tasks': default_tasks
            })
        else:
            return jsonify({
                'success': True,
                'running': False,
                'tasks': default_tasks
            })
    except Exception as e:
        print(f"Error in get_background_task_status: {e}")
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

# ==================== AI FILE ATTACHMENT ENDPOINTS ====================

@app.route('/api/ai-attachments/upload', methods=['POST'])
@require_auth
def upload_ai_attachment():
    """
    Upload a file for AI processing with context description.
    User specifies what the content is about and how AI should use it.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get context from form data
        content_description = request.form.get('content_description', '')
        ai_instructions = request.form.get('ai_instructions', '')
        character_id = request.form.get('character_id')
        
        if not content_description:
            return jsonify({'error': 'Please describe what this file contains'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"ai_{unique_id}.{file_extension}"
            
            # Save file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Get file info
            file_size = os.path.getsize(filepath)
            file_type = file_extension
            
            # Extract text content for supported file types
            extracted_text = None
            text_formats = {'txt', 'md', 'json', 'csv', 'xml', 'yaml', 'yml', 
                           'py', 'js', 'ts', 'html', 'css', 'sql', 'sh', 'bat'}
            if file_type in text_formats:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        extracted_text = f.read()[:10000]  # Limit to 10k chars
                except:
                    pass
            
            # Save to database
            user_id = request.current_user.get('user_id')
            attachment_id = integrated_db.save_ai_attachment(
                user_id=user_id,
                filename=unique_filename,
                original_filename=original_filename,
                file_type=file_type,
                file_size=file_size,
                content_description=content_description,
                ai_instructions=ai_instructions,
                extracted_text=extracted_text,
                character_id=character_id
            )
            
            if attachment_id:
                print(f"[AI_ATTACHMENT] ✓ User {user_id} uploaded: {original_filename}")
                print(f"  Description: {content_description[:50]}...")
                print(f"  Instructions: {ai_instructions[:50] if ai_instructions else 'None'}...")
                
                return jsonify({
                    'success': True,
                    'attachment_id': attachment_id,
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'file_size': file_size,
                    'file_type': file_type,
                    'content_description': content_description,
                    'ai_instructions': ai_instructions,
                    'file_url': f'/api/files/{unique_filename}'
                })
            else:
                return jsonify({'error': 'Failed to save attachment'}), 500
        else:
            return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        print(f"Error uploading AI attachment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-attachments', methods=['GET'])
@require_auth
def get_ai_attachments():
    """Get user's active AI attachments"""
    try:
        user_id = request.current_user.get('user_id')
        character_id = request.args.get('character_id')
        
        attachments = integrated_db.get_active_attachments(user_id, character_id)
        
        return jsonify({
            'success': True,
            'attachments': attachments
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-attachments/<int:attachment_id>', methods=['DELETE'])
@require_auth
def delete_ai_attachment(attachment_id):
    """Deactivate an AI attachment"""
    try:
        user_id = request.current_user.get('user_id')
        
        success = integrated_db.deactivate_attachment(attachment_id, user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Attachment removed'})
        else:
            return jsonify({'error': 'Attachment not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def format_attachments_for_ai(attachments):
    """Format active attachments into context for AI prompt"""
    if not attachments:
        return None
    
    context_parts = ["USER'S ATTACHED FILES FOR REFERENCE:"]
    
    for att in attachments:
        context_parts.append(f"\n--- FILE: {att['original_filename']} ---")
        context_parts.append(f"Description: {att['content_description']}")
        
        if att['ai_instructions']:
            context_parts.append(f"User's instructions: {att['ai_instructions']}")
        
        if att['extracted_text']:
            # Limit text to avoid token explosion
            text_preview = att['extracted_text'][:3000]
            if len(att['extracted_text']) > 3000:
                text_preview += "\n... [content truncated]"
            context_parts.append(f"Content:\n{text_preview}")
    
    context_parts.append("\n--- END OF ATTACHED FILES ---")
    context_parts.append("Use these files to inform your response when relevant.")
    
    return "\n".join(context_parts)

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
        if not has_admin_access(user_role):
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
        if not has_admin_access(user_role):
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
        if not has_admin_access(user_role):
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
        user_id = request.current_user['user_id']
        success = integrated_db.update_user_profile(user_id, profile_data)
        if success:
            # Invalidate personality cache so profile changes take effect
            if personality_integrator:
                personality_integrator.invalidate_cache(user_id)
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        else:
            return jsonify({'error': 'Failed to update profile'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Comprehensive profile routes (integrating original 3-page system)
@app.route('/api/user/comprehensive-profile')
@require_auth
def get_comprehensive_profile():
    """Get comprehensive profile from database"""
    try:
        user_id = request.current_user['user_id']
        
        # Load from database
        profile = integrated_db.get_user_profile(user_id)
        if profile:
            return jsonify({
                'personal_info': profile.get('personal_info', {}),
                'preferences': profile.get('preferences', {}),
                'privacy_settings': profile.get('privacy_settings', {}),
                'metadata': {'profile_completion': profile.get('profile_completion', 0)}
            })
        
        # Return empty structure if no profile exists
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
        user_id = request.current_user['user_id']
        
        # Save to database using integrated_db
        success = integrated_db.update_user_profile(user_id, {'personal_info': data})
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/comprehensive-profile/preferences', methods=['PUT'])
@require_auth
def update_comprehensive_preferences():
    """Update comprehensive profile preferences"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']
        
        # Save to database using integrated_db
        success = integrated_db.update_user_profile(user_id, {'preferences': data})
        
        # Invalidate personality cache so preference/goal changes take effect
        if success and personality_integrator:
            personality_integrator.invalidate_cache(user_id)
        
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/comprehensive-profile/privacy', methods=['PUT'])
@require_auth
def update_comprehensive_privacy():
    """Update comprehensive profile privacy settings"""
    try:
        data = request.get_json()
        user_id = request.current_user['user_id']
        
        # Save to database using integrated_db
        success = integrated_db.update_user_profile(user_id, {'privacy_settings': data})
        return jsonify({'success': success})
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

# ==================== USER EXPLICIT CONTEXT ====================

@app.route('/api/user/explicit-context', methods=['GET'])
@require_auth
def get_user_explicit_context():
    """Get user's explicit context (goals, preferences, values they've stated)"""
    try:
        user_id = request.current_user['user_id']
        character = request.args.get('character', 'general')
        context_type = request.args.get('type')  # Optional filter by type
        
        if not explicit_context_handler:
            return jsonify({'error': 'Explicit context handler not available'}), 500
        
        context_items = explicit_context_handler.get_explicit_context(
            user_id, character, context_type
        )
        
        return jsonify({
            'success': True,
            'context_items': context_items,
            'count': len(context_items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/explicit-context/summary', methods=['GET'])
@require_auth
def get_explicit_context_summary():
    """Get formatted summary of user's explicit context for display"""
    try:
        user_id = request.current_user['user_id']
        character = request.args.get('character', 'general')
        
        if not explicit_context_handler:
            return jsonify({'error': 'Explicit context handler not available'}), 500
        
        # Get formatted summary
        summary = explicit_context_handler.format_for_ai_prompt(user_id, character)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'has_context': bool(summary)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/explicit-context/<int:context_id>', methods=['DELETE'])
@require_auth
def delete_explicit_context(context_id):
    """Delete/deactivate a specific explicit context item"""
    try:
        user_id = request.current_user['user_id']
        
        if not explicit_context_handler:
            return jsonify({'error': 'Explicit context handler not available'}), 500
        
        # Verify ownership before deleting
        cursor = explicit_context_handler.db.cursor()
        cursor.execute('''
            SELECT user_id FROM explicit_context WHERE id = ?
        ''', (context_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Context item not found'}), 404
        if row[0] != user_id:
            return jsonify({'error': 'Not authorized to delete this item'}), 403
        
        # Deactivate (soft delete)
        explicit_context_handler.deactivate_context(context_id)
        
        return jsonify({
            'success': True,
            'message': 'Context item removed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/explicit-context/stats', methods=['GET'])
@require_auth
def get_explicit_context_stats():
    """Get user's explicit context statistics"""
    try:
        user_id = request.current_user['user_id']
        character = request.args.get('character', 'general')
        
        if not explicit_context_handler:
            return jsonify({'error': 'Explicit context handler not available'}), 500
        
        stats = explicit_context_handler.get_stats(user_id, character)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/explicit-context/ui-data', methods=['GET'])
@require_auth
def get_explicit_context_ui_data():
    """Get explicit context formatted for frontend UI display"""
    try:
        user_id = request.current_user['user_id']
        character = request.args.get('character', 'general')
        
        if not explicit_context_handler:
            return jsonify({'has_context': False, 'groups': {}})
        
        # Get raw context items
        cursor = explicit_context_handler.db.cursor()
        cursor.execute('''
            SELECT id, context_type, context_key, context_value, 
                   original_statement, priority, confidence, timestamp
            FROM explicit_context
            WHERE user_id = ? AND (character = ? OR character = 'general')
            AND active = 1
            ORDER BY priority DESC, timestamp DESC
        ''', (user_id, character))
        
        rows = cursor.fetchall()
        
        # Group by type with display-friendly labels
        type_labels = {
            'emotional_state': {'label': '💭 Current Feelings', 'icon': 'heart', 'color': 'pink'},
            'goal': {'label': '🎯 Your Goals', 'icon': 'target', 'color': 'blue'},
            'preference': {'label': '⚙️ Preferences', 'icon': 'settings', 'color': 'gray'},
            'need': {'label': '🤝 What You Need', 'icon': 'hand', 'color': 'green'},
            'value': {'label': '💎 Your Values', 'icon': 'gem', 'color': 'purple'},
            'self_description': {'label': '👤 About You', 'icon': 'user', 'color': 'indigo'},
            'intention': {'label': '📋 Intentions', 'icon': 'list', 'color': 'orange'},
        }
        
        groups = {}
        for row in rows:
            ctx_type = row[1]
            if ctx_type not in groups:
                meta = type_labels.get(ctx_type, {'label': ctx_type.title(), 'icon': 'info', 'color': 'gray'})
                groups[ctx_type] = {
                    'label': meta['label'],
                    'icon': meta['icon'],
                    'color': meta['color'],
                    'items': []
                }
            
            groups[ctx_type]['items'].append({
                'id': row[0],
                'key': row[2],
                'value': row[3],
                'original': row[4],
                'priority': row[5],
                'confidence': row[6],
                'timestamp': row[7],
                'can_delete': True
            })
        
        return jsonify({
            'success': True,
            'has_context': len(rows) > 0,
            'total_items': len(rows),
            'groups': groups,
            'help_text': "These are things you've told me about yourself. I use this to give you better responses. You can remove anything that's no longer accurate."
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== CONVERSATION HIGHLIGHTS ====================

@app.route('/api/user/highlights', methods=['GET'])
@require_auth
def get_highlights():
    """Get user's saved highlights"""
    try:
        user_id = request.current_user['user_id']
        character_id = request.args.get('character_id')
        limit = request.args.get('limit', 50, type=int)
        
        highlights = integrated_db.get_highlights(user_id, character_id, limit)
        return jsonify({'highlights': highlights})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/highlights', methods=['POST'])
@require_auth
def save_highlight():
    """Save a highlighted portion of conversation"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        highlighted_text = data.get('highlighted_text')
        if not highlighted_text or not highlighted_text.strip():
            return jsonify({'error': 'Highlighted text is required'}), 400
        
        highlight_id = integrated_db.save_highlight(
            user_id=user_id,
            highlighted_text=highlighted_text.strip(),
            character_id=data.get('character_id'),
            message_id=data.get('message_id'),
            full_message=data.get('full_message'),
            message_role=data.get('message_role'),
            note=data.get('note'),
            color=data.get('color', 'green')
        )
        
        if highlight_id:
            return jsonify({'success': True, 'highlight_id': highlight_id})
        else:
            return jsonify({'error': 'Failed to save highlight'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/highlights/<int:highlight_id>', methods=['PUT'])
@require_auth
def update_highlight(highlight_id):
    """Update a highlight's note"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        note = data.get('note', '')
        
        success = integrated_db.update_highlight_note(highlight_id, user_id, note)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Highlight not found or unauthorized'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/highlights/<int:highlight_id>', methods=['DELETE'])
@require_auth
def delete_highlight(highlight_id):
    """Delete a highlight"""
    try:
        user_id = request.current_user['user_id']
        
        success = integrated_db.delete_highlight(highlight_id, user_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Highlight not found or unauthorized'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== FOLLOW-UP SUGGESTIONS ====================

@app.route('/api/user/suggestion-selected', methods=['POST'])
@require_auth
def record_suggestion_selection():
    """
    Record when user selects a follow-up suggestion.
    This tracks their choice path to learn implicit preferences over time.
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        selected_text = data.get('text', '')
        category = data.get('category')
        character_id = data.get('character_id')
        
        if not selected_text:
            return jsonify({'error': 'No suggestion text provided'}), 400
        
        from smart_response.follow_up_suggestions import get_suggestion_system
        conn = integrated_db.get_connection()
        suggestion_system = get_suggestion_system(conn)
        
        suggestion_system.record_selection(
            user_id=user_id,
            selected_text=selected_text,
            suggestion_category=category,
            character_id=character_id
        )
        conn.close()
        
        return jsonify({'success': True, 'message': 'Selection recorded'})
    except Exception as e:
        print(f"Error recording suggestion selection: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/preferences', methods=['GET'])
@require_auth
def get_learned_preferences():
    """Get user's learned preferences from their suggestion choices."""
    try:
        user_id = request.current_user['user_id']
        
        from smart_response.follow_up_suggestions import get_suggestion_system
        conn = integrated_db.get_connection()
        suggestion_system = get_suggestion_system(conn)
        
        preferences = suggestion_system.get_user_preferences(user_id)
        journey = suggestion_system.get_user_journey_insights(user_id)
        conn.close()
        
        return jsonify({
            'success': True,
            'preferences': preferences,
            'journey_insights': journey
        })
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

# ==================== USER INTELLIGENCE (Social Media-inspired) ====================

@app.route('/api/user/intelligence/profile', methods=['GET'])
@require_auth
def get_intelligence_profile():
    """
    Get user's complete intelligence profile.
    Like viewing your YouTube/Spotify taste profile.
    """
    try:
        user_id = request.current_user['user_id']
        
        from smart_response.user_intelligence import get_intelligence_system
        conn = integrated_db.get_connection()
        intel = get_intelligence_system(conn)
        
        profile = intel.build_intelligence_context(user_id)
        conn.close()
        
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/intelligence/engagement', methods=['GET'])
@require_auth
def get_engagement_metrics():
    """Get engagement metrics (YouTube Analytics style)."""
    try:
        user_id = request.current_user['user_id']
        days = request.args.get('days', 30, type=int)
        
        from smart_response.user_intelligence import get_intelligence_system
        conn = integrated_db.get_connection()
        intel = get_intelligence_system(conn)
        
        summary = intel.get_engagement_summary(user_id, days)
        conn.close()
        
        return jsonify({'success': True, 'engagement': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/intelligence/patterns', methods=['GET'])
@require_auth
def get_behavioral_patterns():
    """Get discovered behavioral patterns."""
    try:
        user_id = request.current_user['user_id']
        
        from smart_response.user_intelligence import get_intelligence_system
        conn = integrated_db.get_connection()
        intel = get_intelligence_system(conn)
        
        patterns = {
            'temporal': intel.analyze_temporal_patterns(user_id),
            'communication': intel.analyze_communication_style(user_id),
            'topics': intel.analyze_topic_patterns(user_id)
        }
        conn.close()
        
        return jsonify({'success': True, 'patterns': patterns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/intelligence/recommendations', methods=['GET'])
@require_auth
def get_character_recommendations():
    """Get character recommendations based on chemistry scores."""
    try:
        user_id = request.current_user['user_id']
        
        from smart_response.user_intelligence import get_intelligence_system
        conn = integrated_db.get_connection()
        intel = get_intelligence_system(conn)
        
        recommendations = intel.get_character_recommendations(user_id)
        conn.close()
        
        return jsonify({'success': True, 'recommendations': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/intelligence/predictions', methods=['GET'])
@require_auth
def get_need_predictions():
    """Get predictions about user's likely needs (proactive suggestions)."""
    try:
        user_id = request.current_user['user_id']
        
        from smart_response.user_intelligence import get_intelligence_system
        conn = integrated_db.get_connection()
        intel = get_intelligence_system(conn)
        
        predictions = intel.predict_user_needs(user_id)
        proactive = intel.get_proactive_suggestions(user_id)
        conn.close()
        
        return jsonify({
            'success': True, 
            'predictions': predictions,
            'proactive_suggestions': proactive
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/intelligence/record', methods=['POST'])
@require_auth
def record_engagement_signal():
    """
    Record an engagement signal (for frontend to report user actions).
    Like Instagram tracking saves, shares, time spent.
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        
        signal_type = data.get('signal_type', 'message_sent')
        character_id = data.get('character_id')
        topic = data.get('topic')
        context = data.get('context', {})
        
        from smart_response.user_intelligence import get_intelligence_system
        conn = integrated_db.get_connection()
        intel = get_intelligence_system(conn)
        
        intel.record_engagement(
            user_id=user_id,
            signal_type=signal_type,
            context=context,
            character_id=character_id,
            topic=topic
        )
        conn.close()
        
        return jsonify({'success': True, 'message': f'Recorded {signal_type}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PINNED MESSAGES (WhatsApp-style) ====================

@app.route('/api/user/pinned-messages', methods=['GET'])
@require_auth
def get_pinned_messages():
    """Get user's pinned messages"""
    try:
        user_id = request.current_user['user_id']
        character_id = request.args.get('character_id')
        
        conn = integrated_db.get_connection()
        cursor = conn.cursor()
        
        if character_id:
            cursor.execute('''
                SELECT id, message_id, character_id, message_content, message_role, 
                       message_timestamp, pin_note, pinned_at, display_order
                FROM pinned_messages
                WHERE user_id = ? AND character_id = ?
                ORDER BY display_order ASC, pinned_at DESC
            ''', (user_id, character_id))
        else:
            cursor.execute('''
                SELECT id, message_id, character_id, message_content, message_role, 
                       message_timestamp, pin_note, pinned_at, display_order
                FROM pinned_messages
                WHERE user_id = ?
                ORDER BY display_order ASC, pinned_at DESC
            ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        pinned = []
        for row in rows:
            pinned.append({
                'id': row[0],
                'message_id': row[1],
                'character_id': row[2],
                'content': row[3],
                'role': row[4],
                'timestamp': row[5],
                'note': row[6],
                'pinned_at': row[7],
                'display_order': row[8]
            })
        
        return jsonify({'success': True, 'pinned_messages': pinned, 'count': len(pinned)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/pinned-messages', methods=['POST'])
@require_auth
def pin_message():
    """Pin a message"""
    conn = None
    try:
        user_id = request.current_user['user_id']
        data = request.json
        
        message_id = data.get('message_id')
        character_id = data.get('character_id', 'coordinator')
        message_content = data.get('content')
        message_role = data.get('role', 'assistant')
        message_timestamp = data.get('timestamp')
        pin_note = data.get('note', '')
        
        if not message_content:
            return jsonify({'error': 'Message content is required'}), 400
        
        conn = integrated_db.get_connection()
        cursor = conn.cursor()
        
        # Check for duplicate - same content already pinned for this user (ignore character_id)
        cursor.execute('''
            SELECT id FROM pinned_messages 
            WHERE user_id = ? AND message_content = ?
        ''', (user_id, message_content))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return jsonify({'error': 'Message already pinned', 'existing_id': existing[0]}), 409
        
        # Get current max display_order
        cursor.execute('''
            SELECT COALESCE(MAX(display_order), 0) + 1 FROM pinned_messages WHERE user_id = ?
        ''', (user_id,))
        next_order = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO pinned_messages 
            (user_id, message_id, character_id, message_content, message_role, message_timestamp, pin_note, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, message_id or 0, character_id, message_content, message_role, message_timestamp, pin_note, next_order))
        
        pin_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({'success': True, 'pin_id': pin_id})
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': 'Message already pinned'}), 409
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/user/pinned-messages/<int:pin_id>', methods=['PUT'])
@require_auth
def update_pinned_message(pin_id):
    """Update a pinned message's note or order"""
    conn = None
    try:
        user_id = request.current_user['user_id']
        data = request.json
        
        conn = integrated_db.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if 'note' in data:
            updates.append('pin_note = ?')
            params.append(data['note'])
        if 'display_order' in data:
            updates.append('display_order = ?')
            params.append(data['display_order'])
        
        if updates:
            params.extend([pin_id, user_id])
            cursor.execute(f'''
                UPDATE pinned_messages SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
            ''', params)
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/user/pinned-messages/check', methods=['POST'])
@require_auth
def check_if_pinned():
    """Check if a message is already pinned"""
    conn = None
    try:
        user_id = request.current_user['user_id']
        data = request.json
        message_content = data.get('content')
        
        if not message_content:
            return jsonify({'error': 'Content is required'}), 400
        
        conn = integrated_db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM pinned_messages WHERE user_id = ? AND message_content = ?
        ''', (user_id, message_content))
        existing = cursor.fetchone()
        
        return jsonify({'is_pinned': existing is not None, 'pin_id': existing[0] if existing else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/user/pinned-messages/cleanup-duplicates', methods=['POST'])
@require_auth
def cleanup_duplicate_pins():
    """Remove duplicate pinned messages, keeping the oldest one"""
    conn = None
    try:
        user_id = request.current_user['user_id']
        
        conn = integrated_db.get_connection()
        cursor = conn.cursor()
        
        # Find and delete duplicates (keep the one with lowest id)
        cursor.execute('''
            DELETE FROM pinned_messages 
            WHERE id NOT IN (
                SELECT MIN(id) FROM pinned_messages 
                WHERE user_id = ?
                GROUP BY message_content, character_id
            ) AND user_id = ?
        ''', (user_id, user_id))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return jsonify({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/user/pinned-messages/<int:pin_id>', methods=['DELETE'])
@require_auth
def unpin_message(pin_id):
    """Unpin a message"""
    conn = None
    try:
        user_id = request.current_user['user_id']
        
        conn = integrated_db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM pinned_messages WHERE id = ? AND user_id = ?
        ''', (pin_id, user_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        
        if deleted:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Pin not found or unauthorized'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/greetings/check', methods=['POST'])
@require_auth
def check_greetings():
    """Check and send any pending automated greetings"""
    try:
        user_id = request.current_user['user_id']
        sent_greetings = greeting_system.check_and_send_greetings(user_id)
        return jsonify({'success': True, 'greetings': sent_greetings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/greetings/pending')
@require_auth
def get_pending_greetings():
    """Get pending greetings for the user"""
    try:
        user_id = request.current_user['user_id']
        since_param = request.args.get('since')
        since = None
        if since_param:
            # Handle ISO format with 'Z' suffix (UTC)
            since_str = since_param.replace('Z', '+00:00')
            try:
                since = datetime.fromisoformat(since_str)
            except ValueError:
                # Fallback: ignore invalid date
                since = None
        
        greetings = greeting_system.get_pending_greetings(user_id, since)
        return jsonify({'success': True, 'greetings': greetings})
    except Exception as e:
        print(f"Error in get_pending_greetings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/greetings/activity', methods=['POST'])
@require_auth
def update_user_activity():
    """Update user activity timestamp"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        activity_type = data.get('activity_type', 'message_sent')
        metadata = data.get('metadata', {})
        
        greeting_system.update_user_activity(user_id, activity_type, metadata)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/greetings/ai-prompt', methods=['POST'])
@require_auth
def generate_ai_context_prompt():
    """
    Generate an AI-powered context-aware prompt for the user.
    Uses conversation history to create meaningful follow-ups that:
    - Reinforce previous suggestions
    - Dive deeper into discussed topics
    - Track user feedback and preferences
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        character_id = data.get('character_id', 'coordinator')
        
        # Get user's first name
        profile = integrated_db.get_user_profile(user_id)
        user_name = 'there'
        if profile and profile.get('first_name'):
            user_name = profile['first_name'].split()[0]
        
        # Try AI-generated prompt
        ai_prompt = greeting_system.generate_ai_context_prompt(user_id, user_name, character_id)
        
        if ai_prompt:
            return jsonify({
                'success': True,
                'prompt': ai_prompt,
                'type': 'ai_generated'
            })
        else:
            # Fallback to template-based
            fallback = greeting_system.generate_inactivity_greeting(user_id, use_ai=False)
            return jsonify({
                'success': True,
                'prompt': fallback,
                'type': 'template'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/greetings/feedback', methods=['POST'])
@require_auth
def track_greeting_feedback():
    """
    Track user's response to a greeting/prompt for learning preferences.
    Called after user responds to track engagement and topic interest.
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json()
        user_message = data.get('user_message', '')
        character_id = data.get('character_id', 'coordinator')
        previous_prompt = data.get('previous_prompt')
        
        if user_message:
            greeting_system.process_user_response_feedback(
                user_id=user_id,
                character_id=character_id,
                user_message=user_message,
                previous_prompt=previous_prompt
            )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/greetings/cleanup', methods=['POST'])
@require_auth
def cleanup_old_greetings():
    """
    Clean up old non-context greetings from the database.
    Only admins can trigger this, or it runs automatically.
    """
    try:
        user_role = request.current_user.get('role', 'guest')
        if user_role not in ['administrator', 'master']:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 7)
        
        deleted_count = greeting_system.cleanup_old_greetings(days_to_keep)
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'days_kept': days_to_keep
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/greetings/extract-themes', methods=['POST'])
@require_auth
def extract_themes_from_history():
    """
    Extract themes from user's conversation history.
    Useful for initializing themes for existing users.
    """
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        character_id = data.get('character_id')  # None = all characters
        limit = data.get('limit', 50)
        
        if not greeting_system.context_prompt_generator:
            return jsonify({'error': 'Context prompt generator not available'}), 500
        
        result = greeting_system.context_prompt_generator.bulk_extract_themes_from_history(
            user_id=user_id,
            character_id=character_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            **result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# USER PERSONALIZATION API
# ============================================

@app.route('/api/user/personalization', methods=['GET'])
@require_auth
def get_user_personalization():
    """Get user's personalized parameters"""
    try:
        user_id = request.current_user['user_id']
        params = user_personalization.get_user_parameters(user_id)
        return jsonify({
            'success': True,
            'user_id': user_id,
            'parameters': params
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/personalization', methods=['PUT'])
@require_auth
def update_user_personalization():
    """Update user's personalized parameters"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        updates = data.get('parameters', {})
        reason = data.get('reason', 'User update')
        
        if not updates:
            return jsonify({'error': 'No parameters provided'}), 400
        
        user_personalization.update_parameters(user_id, updates, reason)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'updated': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/personalization/parameter', methods=['PUT'])
@require_auth
def set_user_parameter():
    """Set a specific parameter by path"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        path = data.get('path')
        value = data.get('value')
        reason = data.get('reason', 'User update')
        
        if not path:
            return jsonify({'error': 'Parameter path required'}), 400
        
        user_personalization.set_parameter(user_id, path, value, reason)
        
        return jsonify({
            'success': True,
            'path': path,
            'value': value
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/personalization/history', methods=['GET'])
@require_auth
def get_personalization_history():
    """Get history of parameter changes"""
    try:
        user_id = request.current_user['user_id']
        path = request.args.get('path')
        limit = int(request.args.get('limit', 20))
        
        history = user_personalization.get_parameter_history(user_id, path, limit)
        
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/personalization/signal', methods=['POST'])
@require_auth
def record_interaction_signal():
    """Record an interaction signal for adaptive learning"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        signal_type = data.get('signal_type')
        signal_value = data.get('signal_value')
        context = data.get('context')
        
        if not signal_type:
            return jsonify({'error': 'Signal type required'}), 400
        
        user_personalization.record_signal(user_id, signal_type, signal_value, context)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/personalization/adapt', methods=['POST'])
@require_auth
def trigger_adaptation():
    """Trigger adaptive learning from recorded signals"""
    try:
        user_id = request.current_user['user_id']
        result = user_personalization.process_signals_and_adapt(user_id)
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/personalization/reset', methods=['POST'])
@require_auth
def reset_personalization():
    """Reset parameters to defaults"""
    try:
        user_id = request.current_user['user_id']
        data = request.get_json() or {}
        category = data.get('category')  # Optional: reset only one category
        
        user_personalization.reset_to_defaults(user_id, category)
        
        return jsonify({
            'success': True,
            'reset': category or 'all'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/personalization/export', methods=['GET'])
@require_auth
def export_personalization():
    """Export complete personalization profile"""
    try:
        user_id = request.current_user['user_id']
        profile = user_personalization.export_user_profile(user_id)
        return jsonify({
            'success': True,
            **profile
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/greetings/debug-context', methods=['GET'])
@require_auth
def debug_context_prompts():
    """
    Debug endpoint to see why AI context prompts aren't being generated.
    Shows the context that would be used for AI prompt generation.
    """
    try:
        user_id = request.current_user['user_id']
        
        # Get user's first name
        profile = integrated_db.get_user_profile(user_id)
        user_name = 'there'
        if profile and profile.get('first_name'):
            user_name = profile['first_name'].split()[0]
        
        # Check if context prompt generator is available
        if not greeting_system.context_prompt_generator:
            return jsonify({
                'success': False,
                'error': 'Context prompt generator not initialized',
                'ai_call_func_available': greeting_system.ai_call_func is not None
            })
        
        # Build prompt request to see what context we have
        from smart_response.ai_context_prompts import AIContextPromptGenerator
        conn = integrated_db.get_connection()
        debug_generator = AIContextPromptGenerator(conn)
        
        context = debug_generator.get_conversation_context_for_ai(user_id, 'coordinator')
        prompt_request = debug_generator.build_ai_prompt_request(user_id, user_name, 'coordinator')
        
        # DEBUG: Check raw database counts
        cursor = conn.cursor()
        
        # Count conversations for this user
        cursor.execute('SELECT COUNT(*) FROM ai_conversations WHERE user_id = ?', (user_id,))
        conv_count = cursor.fetchone()[0]
        
        # Count messages for this user
        cursor.execute('''
            SELECT COUNT(*) FROM messages m
            JOIN ai_conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
        ''', (user_id,))
        msg_count = cursor.fetchone()[0]
        
        # Get sample conversations
        cursor.execute('''
            SELECT id, session_id, title, character_id FROM ai_conversations 
            WHERE user_id = ? LIMIT 5
        ''', (user_id,))
        sample_convs = [{'id': r[0], 'session_id': r[1], 'title': r[2], 'character_id': r[3]} 
                        for r in cursor.fetchall()]
        
        # Get sample messages
        cursor.execute('''
            SELECT m.id, m.sender_type, substr(m.content, 1, 50) as content_preview
            FROM messages m
            JOIN ai_conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
            ORDER BY m.timestamp DESC
            LIMIT 5
        ''', (user_id,))
        sample_msgs = [{'id': r[0], 'sender': r[1], 'preview': r[2]} for r in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'user_name': user_name,
            'meaningful_exchange_count': context.get('meaningful_exchange_count', 0),
            'has_sufficient_context': context.get('has_sufficient_context', False),
            'themes_count': len(context.get('themes', [])),
            'themes': context.get('themes', []),
            'feedback_patterns': context.get('feedback_patterns', []),
            'recent_suggestions_count': len(context.get('recent_suggestions', [])),
            'should_use_ai': prompt_request.get('should_use_ai', False),
            'skip_reason': prompt_request.get('reason') if not prompt_request.get('should_use_ai') else None,
            'ai_call_func_available': greeting_system.ai_call_func is not None,
            'context_prompt_generator_available': greeting_system.context_prompt_generator is not None,
            # DEBUG info
            'debug': {
                'raw_conversation_count': conv_count,
                'raw_message_count': msg_count,
                'sample_conversations': sample_convs,
                'sample_messages': sample_msgs
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        
        # Update user activity when they send a message
        user_id = request.current_user['user_id']
        greeting_system.update_user_activity(user_id, 'message_sent', {'session_id': session_id})
        
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

@app.route('/login')
def login_page():
    """Login-only page (no signup option)"""
    return render_template('chatchat.html', login_only=True)

@app.route('/life-companion')
def life_companion_interface():
    """Domain characters life companion interface"""
    return render_template('domain_characters.html')


@app.route('/admin/settings')
def admin_settings_page():
    """Admin settings configuration page"""
    return render_template('admin_settings.html')

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
            
            # Run trait inference if needed (Phase 3.2.2)
            try:
                inference_result = trait_inference.run_inference_if_needed(user_id)
                if inference_result:
                    print(f"✅ Trait inference updated for user {user_id}: confidence={inference_result['confidence']}")
            except Exception as e:
                print(f"⚠️ Trait inference error (non-critical): {e}")
        
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

@app.route('/personality-dashboard')
def personality_dashboard_page():
    """Personality Insights Dashboard (Master/Admin only)"""
    # Note: Authentication is handled client-side via JavaScript
    # The dashboard will check auth token and redirect to login if needed
    return render_template('personality_dashboard.html')

@app.route('/psychological-profile')
def psychological_profile_redirect():
    """Redirect to unified personality test page"""
    return redirect('/personality-test', code=302)

@app.route('/psychological-assessment')
def psychological_assessment_redirect():
    """Redirect to unified personality test page"""
    return redirect('/personality-test', code=302)

# ==================== ASSESSMENT HISTORY API (PHASE 3.2 ENHANCEMENT) ====================

@app.route('/api/personality/history', methods=['GET'])
def get_personality_assessment_history():
    """Get assessment history for a user (supports both token and session auth)"""
    try:
        # Try token authentication first
        user_data = authenticate_token()
        
        print(f"🔐 Auth Debug:")
        print(f"   Token auth result: {user_data}")
        print(f"   Session contents: {dict(session)}")
        print(f"   Has user_id in session: {'user_id' in session}")
        
        if user_data:
            user_id = user_data['user_id']
            print(f"   ✅ Using token auth for user {user_id}")
        elif 'user_id' in session:
            # Fall back to session-based authentication
            user_id = session['user_id']
            print(f"   ✅ Using session auth for user {user_id}")
        else:
            print(f"   ❌ No authentication found")
            return jsonify({'error': 'Authentication required'}), 401
        
        limit = request.args.get('limit', 10, type=int)
        
        print(f"📊 Fetching assessment history for user {user_id} (limit: {limit})")
        history = integrated_db.get_assessment_history(user_id, limit)
        print(f"   Found {len(history)} assessment(s)")
        
        # Flatten the response - move traits to top level for frontend compatibility
        # Also normalize values to 0-1 scale if they're on 0-10 scale
        flattened_history = []
        for item in history:
            # Detect if values are on 0-10 scale (any value > 1.0)
            traits = item['traits']
            needs_normalization = any(v > 1.0 for v in traits.values())
            
            flat_item = {
                'id': item['id'],
                'completed_at': item['completed_at'],
                'started_at': item['started_at'],
                'openness': traits['openness'] / 10.0 if needs_normalization else traits['openness'],
                'conscientiousness': traits['conscientiousness'] / 10.0 if needs_normalization else traits['conscientiousness'],
                'extraversion': traits['extraversion'] / 10.0 if needs_normalization else traits['extraversion'],
                'agreeableness': traits['agreeableness'] / 10.0 if needs_normalization else traits['agreeableness'],
                'neuroticism': traits['neuroticism'] / 10.0 if needs_normalization else traits['neuroticism'],
                'notes': item.get('notes')
            }
            flattened_history.append(flat_item)
        
        return jsonify({
            'success': True,
            'history': flattened_history,
            'count': len(flattened_history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality/compare', methods=['GET'])
@require_auth
def compare_personality_assessments():
    """Compare two assessments or compare an assessment to current profile"""
    try:
        user_id = request.current_user['user_id']
        assessment1_id = request.args.get('assessment1_id', type=int)
        assessment2_id = request.args.get('assessment2_id', type=int)
        
        if not assessment1_id:
            return jsonify({'error': 'assessment1_id is required'}), 400
        
        comparison = integrated_db.compare_assessments(user_id, assessment1_id, assessment2_id)
        
        if 'error' in comparison:
            return jsonify(comparison), 404
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality/trends/<trait_name>', methods=['GET'])
@require_auth
def get_personality_trait_trends(trait_name):
    """Get trend data for a specific trait over time"""
    try:
        user_id = request.current_user['user_id']
        
        valid_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        if trait_name not in valid_traits:
            return jsonify({'error': f'Invalid trait. Must be one of: {", ".join(valid_traits)}'}), 400
        
        trend = integrated_db.get_trait_trends(user_id, trait_name)
        return jsonify({
            'success': True,
            'trend': trend
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
def delete_explicit_context_legacy(context_id):
    """Delete (deactivate) an explicit context item (legacy endpoint)"""
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
@require_auth
def get_ai_budget_status():
    """Get current AI budget status and usage"""
    try:
        # Check if user is admin to show correct limit
        is_admin = False
        user_id = request.current_user.get('user_id') if request.current_user else None
        try:
            user_role = integrated_db.get_user_role(user_id)
            is_admin = has_admin_access(user_role)
            print(f"[AI-BUDGET] User {user_id} role={user_role} is_admin={is_admin}")
        except Exception as e:
            print(f"[AI-BUDGET] Error checking admin: {e}")
        
        if not ai_budget:
            # Return default values when not initialized
            daily_limit = 1000 if is_admin else 100
            return jsonify({
                'daily_usage': 0,
                'daily_limit': daily_limit,
                'monthly_usage': 0,
                'monthly_limit': 1000,
                'status': 'not_initialized'
            })
        
        report = ai_budget.get_usage_report()
        
        # Override limit based on user role
        if is_admin:
            admin_limit = ai_budget.DAILY_CALL_LIMIT_ADMIN
            report['today']['limit'] = admin_limit
            report['today']['remaining'] = admin_limit - report['today']['calls']
            report['today']['percentage_used'] = round((report['today']['calls'] / admin_limit) * 100, 1)
        
        # Add avg response time
        try:
            cursor = smart_response_conn.cursor()
            cursor.execute('''
                SELECT AVG(response_time_ms) FROM ai_usage_log 
                WHERE DATE(timestamp) = DATE('now') AND response_time_ms IS NOT NULL
            ''')
            avg_ms = cursor.fetchone()[0]
            report['avg_response_ms'] = round(avg_ms) if avg_ms else None
        except:
            report['avg_response_ms'] = None
        
        return jsonify(report)
    except Exception as e:
        print(f"Error in get_ai_budget_status: {e}")
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

@app.route('/api/ai-budget/notifications/clear', methods=['POST'])
@require_auth
def clear_ai_notifications():
    """Clear all AI budget notifications (admin only)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        if not ai_budget:
            return jsonify({'error': 'AI Budget Manager not initialized'}), 500
        
        cursor = smart_response_conn.cursor()
        cursor.execute('UPDATE ai_budget_notifications SET acknowledged = 1')
        smart_response_conn.commit()
        
        return jsonify({'success': True, 'message': 'All notifications cleared'})
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
        # Require authentication
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        
        # Admin only
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        # Reset circuit breaker
        ai_budget_manager.reset_circuit_breaker()
        
        return jsonify({
            'success': True,
            'message': 'Circuit breaker reset successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-budget/limits', methods=['GET'])
@require_auth
def get_ai_limits():
    """Get current AI call limits"""
    try:
        if not ai_budget:
            return jsonify({'error': 'AI Budget Manager not initialized'}), 500
        
        limits = ai_budget.get_limits()
        return jsonify(limits)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-budget/limits', methods=['PUT'])
@require_auth
def update_ai_limits():
    """Update AI call limits (admin only)"""
    try:
        # Admin only
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        if not ai_budget:
            return jsonify({'error': 'AI Budget Manager not initialized'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        updated = []
        errors = []
        
        for key, value in data.items():
            try:
                value = int(value)
                if value < 1:
                    errors.append(f"{key}: must be at least 1")
                    continue
                if value > 10000:
                    errors.append(f"{key}: cannot exceed 10000")
                    continue
                    
                if ai_budget.update_limit(key, value):
                    updated.append(key)
                else:
                    errors.append(f"{key}: invalid key")
            except (ValueError, TypeError):
                errors.append(f"{key}: must be a valid integer")
        
        return jsonify({
            'success': len(updated) > 0,
            'updated': updated,
            'errors': errors,
            'current_limits': ai_budget.get_limits()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality/profile', methods=['GET'])
@app.route('/api/personality/profile/<int:user_id>', methods=['GET'])
@require_auth
def get_personality_profile(user_id=None):
    """Get personality profile with Big 5 traits (Master/Admin only)"""
    try:
        
        # Check personality access (master or admin)
        if not integrated_db.has_personality_access(request.current_user['user_id']):
            return jsonify({'error': 'Master or Admin access required for personality features'}), 403
        
        # Default to current user, admins can query others
        target_user_id = user_id if user_id else request.current_user['user_id']
        
        # Get profile
        profile = integrated_db.get_personality_profile(target_user_id)
        
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality/interpretations', methods=['GET'])
@app.route('/api/personality/interpretations/<int:user_id>', methods=['GET'])
@require_auth
def get_personality_interpretations(user_id=None):
    """Get recent personality interpretations (Master/Admin only)"""
    try:
        
        # Check personality access (master or admin)
        if not integrated_db.has_personality_access(request.current_user['user_id']):
            return jsonify({'error': 'Master or Admin access required for personality features'}), 403
        
        # Default to current user, admins can query others
        target_user_id = user_id if user_id else request.current_user['user_id']
        
        # Get limit from query params
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Cap at 50
        
        # Get interpretations
        interpretations = integrated_db.get_personality_interpretations(target_user_id, limit)
        
        return jsonify({
            'user_id': target_user_id,
            'count': len(interpretations),
            'interpretations': interpretations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality/stats', methods=['GET'])
@app.route('/api/personality/stats/<int:user_id>', methods=['GET'])
@require_auth
def get_personality_stats(user_id=None):
    """Get personality interpretation statistics (Master/Admin only)"""
    try:
        
        # Check personality access (master or admin)
        if not integrated_db.has_personality_access(request.current_user['user_id']):
            return jsonify({'error': 'Master or Admin access required for personality features'}), 403
        
        # Default to current user, admins can query others
        target_user_id = user_id if user_id else request.current_user['user_id']
        
        # Get stats
        stats = integrated_db.get_personality_stats(target_user_id)
        stats['user_id'] = target_user_id
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personality/conversation-stats', methods=['GET'])
@require_auth
def get_personality_conversation_stats():
    """Get personality interpretation counts by conversation (Master/Admin only)"""
    try:
        # Check personality access (master or admin)
        if not integrated_db.has_personality_access(request.current_user['user_id']):
            return jsonify({'error': 'Master or Admin access required for personality features'}), 403
        
        # Get interpretation counts per conversation for current user
        user_id = request.current_user['user_id']
        
        # Query database for interpretation counts by conversation
        conn = integrated_db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT conversation_id, COUNT(*) as count
            FROM personality_interpretations
            WHERE user_id = ?
            GROUP BY conversation_id
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary
        by_conversation = {row[0]: row[1] for row in results if row[0]}
        
        return jsonify({
            'user_id': user_id,
            'by_conversation': by_conversation,
            'total_conversations': len(by_conversation)
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
    """
    Save psychological assessment results (Phase 3.2 Enhanced)
    Now saves to both assessment_history and current profile
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        scores = data.get('scores', {})
        started_at = data.get('started_at')  # ISO timestamp when started
        completion_time_seconds = data.get('completion_time_seconds')
        notes = data.get('notes', '')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        from datetime import datetime
        
        # Phase 3.2: Big 5 scores (0-1 scale)
        trait_scores = {
            'openness': scores.get('openness', 0.5),
            'conscientiousness': scores.get('conscientiousness', 0.5),
            'extraversion': scores.get('extraversion', 0.5),
            'agreeableness': scores.get('agreeableness', 0.5),
            'neuroticism': scores.get('neuroticism', 0.5)
        }
        
        # SAVE TO ASSESSMENT HISTORY (Phase 3.2 - never overwrite!)
        history_id = integrated_db.save_assessment_to_history(
            user_id=user_id,
            trait_scores=trait_scores,
            started_at=started_at,
            completion_time_seconds=completion_time_seconds,
            notes=notes
        )
        
        # Get comparison to previous assessment (if exists)
        previous_assessments = integrated_db.get_assessment_history(user_id, limit=2)
        comparison = None
        if len(previous_assessments) >= 2:
            # Compare newest (just saved) to second newest
            comparison = integrated_db.compare_assessments(
                user_id,
                previous_assessments[1]['id'],  # Previous assessment
                previous_assessments[0]['id']   # Just saved
            )
        
        # Maintain old system compatibility
        current_timestamp = datetime.now().isoformat()
        existing_profile = user_profile_manager.get_user_profile(user_id)
        old_assessment_history = existing_profile.get('preferences', {}).get('assessment_history', []) if existing_profile else []
        
        # Create entry for old system
        new_assessment = {
            'timestamp': current_timestamp,
            'big_five': {
                'openness': trait_scores['openness'],
                'conscientiousness': trait_scores['conscientiousness'],
                'extraversion': trait_scores['extraversion'],
                'agreeableness': trait_scores['agreeableness'],
                'neuroticism': trait_scores['neuroticism']
            }
        }
        
        old_assessment_history.append(new_assessment)
        if len(old_assessment_history) > 10:
            old_assessment_history = old_assessment_history[-10:]
        
        # Update old system for compatibility
        psychological_attributes = {
            'big_five': trait_scores,
            'assessment_completed_at': current_timestamp,
            'assessment_history': old_assessment_history
        }
        
        user_profile_manager.update_preferences(user_id, psychological_attributes)
        
        # Invalidate personality context cache so new assessment takes effect immediately
        if personality_integrator:
            personality_integrator.invalidate_cache(user_id)
            print(f"[PERSONALITY] Cache invalidated for user {user_id} after assessment")
        
        # Build response with comparison if available
        response_data = {
            'success': True,
            'message': 'Assessment saved successfully!',
            'history_id': history_id,
            'assessment_count': len(previous_assessments)
        }
        
        if comparison:
            response_data['comparison'] = {
                'overall_change': comparison['overall_change'],
                'stability': comparison['stability_assessment'],
                'time_between': comparison['time_between'],
                'significant_changes': [
                    {'trait': trait, 'change': data['change'], 'direction': data['direction']}
                    for trait, data in comparison['comparison'].items()
                    if abs(data['change']) >= 5  # 5%+ change
                ]
            }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Register dynamic character routes for ALL characters with Smart Response and Database
print("\n=== Registering Character Routes ===")
register_character_routes(app, all_characters, process_with_smart_response, integrated_db)
print("✓ Dynamic routes registered for all 8 characters with Smart Response + Database")


# ============================================
# DOMAIN CHARACTER API (Phase 1)
# ============================================

@app.route('/api/domain-characters')
def get_domain_characters():
    """Get list of all domain characters with their info"""
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        characters = domain_character_manager.get_character_info()
        return jsonify({
            'success': True,
            'characters': characters,
            'total': len(characters)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/session')
@require_auth
def get_domain_session():
    """Get session info for domain characters (like ConversationBox session endpoints)"""
    try:
        user_id = request.current_user['user_id']
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Domain characters don't need a specific session_id like single characters
        # They use user_id + character_id for history lookup
        # But we return user_id for consistency with ConversationBox pattern
        return jsonify({
            'success': True,
            'user_id': user_id,
            'session_id': None,  # Domain uses per-character history, not single session
            'message': 'Domain characters use per-character conversation tracking'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/<character_id>')
def get_domain_character(character_id):
    """Get info for a specific domain character"""
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        character = domain_character_manager.get_character(character_id)
        if not character:
            return jsonify({'error': f'Character {character_id} not found'}), 404
        
        config = DOMAIN_CHARACTER_CONFIGS.get(character_id, {})
        return jsonify({
            'success': True,
            'character': {
                'id': character_id,
                'display_name': character.display_name,
                'domain': config.get('domain', 'general'),
                'description': config.get('description', ''),
                'focus_areas': config.get('focus_areas', []),
                'is_coordinator': character_id == 'coordinator'
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/route', methods=['POST'])
@require_auth
def route_to_domain_characters():
    """
    Route a message to domain characters based on threshold triggers.
    Returns responses from characters that exceed their concern threshold.
    """
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        data = request.get_json()
        message = data.get('message', '')
        requested_character = data.get('character_id')  # Optional: specific character
        use_ai = data.get('use_ai', True)  # Whether to use AI for responses
        reply_to_message_id = data.get('reply_to_message_id')  # WhatsApp-style reply reference
        
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        user_id = request.current_user.get('user_id')
        
        # Check if user is admin for AI budget limits
        is_admin = False
        try:
            user_role = integrated_db.get_user_role(user_id)
            is_admin = has_admin_access(user_role)
            print(f"[DOMAIN-CHAT] User {user_id} role={user_role} is_admin={is_admin}")
        except Exception as e:
            print(f"[DOMAIN-CHAT] Error getting user role: {e}")
        
        # Build context for routing
        context = {
            'user_id': user_id,
            'is_admin': is_admin,
            'timestamp': datetime.now().isoformat()
        }
        print(f"[DOMAIN-CHAT] Context built with is_admin={is_admin}")
        
        # If replying to a specific message, fetch it and add to context
        reply_context = None
        if reply_to_message_id:
            replied_message = integrated_db.get_message_by_id(reply_to_message_id)
            if replied_message:
                reply_context = {
                    'id': replied_message['id'],
                    'content': replied_message['content'],
                    'sender_type': replied_message['sender_type'],
                    'timestamp': replied_message['timestamp']
                }
                context['reply_to'] = reply_context
                print(f"[REPLY] User replying to message {reply_to_message_id}: {replied_message['content'][:50]}...")

        # Store user message using centralized integrated_db (same as regular characters)
        target_character = requested_character or 'coordinator'
        try:
            message_id = integrated_db.save_character_message(user_id, target_character, 'user', message, 
                                                  reply_to_message_id=reply_to_message_id)
            # CRITICAL: Set history_id in context so interpretations can be stored
            if message_id:
                context['history_id'] = message_id
            print(f"[HISTORY] ✓ Saved user message for {target_character} (id={message_id})")
            
            # Log activity for analytics
            try:
                from smart_response.user_analytics import create_user_analytics
                conn = integrated_db.get_connection()
                analytics = create_user_analytics(conn)
                analytics.log_activity(user_id, 'message_sent', 
                                       {'character': target_character, 'message_length': len(message)},
                                       page='life-companion')
                conn.close()
            except Exception as ae:
                print(f"[ANALYTICS] Could not log activity: {ae}")
            
            # Extract and store themes from user message (for context-aware prompts)
            if greeting_system and greeting_system.context_prompt_generator:
                try:
                    themes = greeting_system.context_prompt_generator.extract_and_store_themes(
                        user_id, target_character, message, is_user_message=True
                    )
                    if themes:
                        print(f"[THEMES] ✓ Extracted themes: {[t['theme'] for t in themes]}")
                except Exception as te:
                    print(f"[THEMES] Theme extraction error: {te}")
        except Exception as e:
            print(f"Warning: Could not store user message: {e}")
        
        # Process message through user context manager (extracts preferences, goals, language patterns)
        # This runs on EVERY message (cheap, rule-based extraction)
        if user_context_mgr:
            try:
                user_context = user_context_mgr.process_message(
                    user_id, message, requested_character or 'coordinator',
                    message_id=context.get('history_id')
                )
                # Merge user context into main context
                context.update(user_context)
                
                # Format user context for AI prompt
                user_context_prompt = user_context_mgr.format_context_for_prompt(user_context)
                if user_context_prompt:
                    context['user_profile'] = user_context_prompt
                    print(f"[USER_CONTEXT] Added user profile for AI")
                
                # Check if user references past - may need more history
                if user_context.get('references_past'):
                    print(f"[USER_CONTEXT] User references past conversation - expanding context")
            except Exception as e:
                print(f"Warning: User context processing failed: {e}")
        
        # GOAL COACHING: Add adaptive coaching context (invisible to user)
        # Detects user's psychological state and adapts guidance approach
        if goal_coaching_system:
            try:
                # Pass message so it can detect user state and adapt
                coaching_context = goal_coaching_system.get_coaching_context_for_prompt(user_id, message)
                if coaching_context:
                    context['coaching_context'] = coaching_context
                    print(f"[COACHING] Added adaptive coaching context for user {user_id}")
            except Exception as e:
                print(f"Warning: Goal coaching context failed: {e}")
        
        # PERSONALITY INTEGRATION: Add Big5 traits, goals, profile to AI context
        # This adapts thresholds dynamically based on conversation state
        if personality_integrator:
            try:
                # Analyze current message for conversation state
                conversation_state = personality_integrator.get_conversation_state_from_message(message)
                
                # Get personality context with adaptive thresholds
                personality_context = personality_integrator.get_personality_context(
                    user_id, conversation_state
                )
                
                # Format for AI prompt and add to context
                personality_prompt = personality_integrator.format_for_prompt(personality_context)
                if personality_prompt:
                    # Combine with existing user_profile if present
                    existing_profile = context.get('user_profile', '')
                    if existing_profile:
                        context['user_profile'] = f"{existing_profile}\n\n{personality_prompt}"
                    else:
                        context['user_profile'] = personality_prompt
                    
                    print(f"[PERSONALITY] Added personality context (source: {personality_context.trait_source}, confidence: {personality_context.trait_confidence:.0%})")
                    
                    # Log if significant change detected
                    if personality_context.change_detected:
                        print(f"[PERSONALITY] Change detected: {personality_context.change_summary}")
            except Exception as e:
                print(f"Warning: Personality integration failed: {e}")
        
        # AI FILE ATTACHMENTS: Include user's uploaded files in context
        # These are files the user uploaded with descriptions of what they contain
        try:
            attachments = integrated_db.get_active_attachments(user_id, target_character)
            if attachments:
                attachment_context = format_attachments_for_ai(attachments)
                if attachment_context:
                    context['file_attachments'] = attachment_context
                    print(f"[ATTACHMENTS] Added {len(attachments)} file(s) to context")
        except Exception as e:
            print(f"Warning: File attachment context failed: {e}")
        
        # CHARACTER HISTORY INSIGHTS: Add historical patterns from past interpretations
        # This helps characters remember and personalize based on user's history
        if domain_character_manager:
            try:
                target_char = requested_character or 'coordinator'
                character = domain_character_manager.characters.get(target_char) or domain_character_manager.coordinator
                if character and hasattr(character, 'get_personalization_context'):
                    personalization = character.get_personalization_context(user_id)
                    if personalization:
                        existing_profile = context.get('user_profile', '')
                        if existing_profile:
                            context['user_profile'] = f"{existing_profile}\n\n{personalization}"
                        else:
                            context['user_profile'] = personalization
                        print(f"[HISTORY_INSIGHTS] Added personalization from past interpretations")
            except Exception as e:
                print(f"Warning: Character history insights failed: {e}")
        
        # ADAPTIVE COMPANION: Understand implicit needs, adapt tone, suggest micro-steps
        # Core philosophy: Truly understand users and inspire them with achievable actions
        try:
            from smart_response.adaptive_companion import get_adaptive_companion
            adaptive = get_adaptive_companion(smart_response_conn)
            target_char = requested_character or 'coordinator'
            adaptive_context = adaptive.build_adaptive_context(
                user_id, message, target_char,
                user_history=context.get('message_history', [])
            )
            if adaptive_context:
                context['adaptive_context'] = adaptive_context
                implicit_need = adaptive_context.get('implicit_needs', {}).get('primary_need', 'unknown')
                print(f"[ADAPTIVE] Detected implicit need: {implicit_need}")
        except Exception as e:
            print(f"Warning: Adaptive companion failed: {e}")
        
        # FOLLOW-UP SUGGESTIONS: Add learned user preferences to AI context
        # This tracks user's choice paths to understand their implicit needs over time
        try:
            from smart_response.follow_up_suggestions import get_suggestion_system
            suggestion_system = get_suggestion_system(smart_response_conn)
            # Add db_connection for suggestion storage
            context['db_connection'] = smart_response_conn
            # Get learned preferences for AI context
            pref_summary = suggestion_system.get_preference_summary_for_prompt(user_id)
            if pref_summary:
                existing_profile = context.get('user_profile', '')
                if existing_profile:
                    context['user_profile'] = f"{existing_profile}\n\n{pref_summary}"
                else:
                    context['user_profile'] = pref_summary
                print(f"[SUGGESTIONS] Added learned preferences to AI context")
        except Exception as e:
            print(f"Warning: Suggestion preferences failed: {e}")
        
        # USER INTELLIGENCE: Social-media-inspired behavioral understanding
        # Learns from engagement patterns, temporal habits, topic interests, character chemistry
        try:
            from smart_response.user_intelligence import get_intelligence_system
            intel_system = get_intelligence_system(smart_response_conn)
            context['intelligence_system'] = intel_system
            
            # Record engagement signal for this message
            topic = requested_character or 'general'
            is_long_message = len(message) > 100
            intel_system.record_engagement(
                user_id, 
                'long_message' if is_long_message else 'message_sent',
                context={'message_length': len(message)},
                character_id=requested_character,
                topic=topic
            )
            
            # Get intelligence context for AI prompt
            intel_context = intel_system.get_ai_prompt_context(user_id)
            if intel_context:
                existing_profile = context.get('user_profile', '')
                if existing_profile:
                    context['user_profile'] = f"{existing_profile}\n\n{intel_context}"
                else:
                    context['user_profile'] = intel_context
                print(f"[INTELLIGENCE] Added behavioral insights to AI context")
        except Exception as e:
            print(f"Warning: User intelligence failed: {e}")
        
        # Configurable: Number of conversation exchanges to include for AI context
        # Can be set via environment variable AI_CONTEXT_EXCHANGES (default: 5)
        # Expand if user references past conversation
        base_exchanges = int(os.environ.get('AI_CONTEXT_EXCHANGES', 5))
        context_exchanges = base_exchanges * 2 if context.get('references_past') else base_exchanges
        
        target_char = requested_character or 'coordinator'
        try:
            cursor = smart_response_conn.cursor()
            cursor.execute('''
                SELECT hp.user_message, hp.assistant_response, hp.character
                FROM history_primary hp
                LEFT JOIN message_visibility mv ON hp.id = mv.history_id AND mv.character_id = ?
                WHERE hp.user_id = ? 
                  AND (mv.character_id = ? OR hp.character = ?)
                  AND hp.assistant_response IS NOT NULL 
                  AND hp.assistant_response != ''
                ORDER BY hp.timestamp DESC
                LIMIT ?
            ''', (target_char, user_id, target_char, target_char, context_exchanges))
            
            rows = cursor.fetchall()
            message_history = []
            history_token_estimate = 0
            
            for row in reversed(rows):  # Chronological order
                user_msg, ai_resp, char = row
                if user_msg:
                    message_history.append({'role': 'user', 'content': user_msg})
                    history_token_estimate += len(user_msg) // 4  # ~4 chars per token
                if ai_resp:
                    message_history.append({'role': 'assistant', 'content': ai_resp})
                    history_token_estimate += len(ai_resp) // 4
            
            if message_history:
                context['message_history'] = message_history
                context['history_token_estimate'] = history_token_estimate
                print(f"[CONTEXT] Added {len(message_history)} history messages (~{history_token_estimate} tokens)")
        except Exception as e:
            print(f"Warning: Could not fetch conversation history: {e}")
        
        # Route message to characters (get which ones should respond)
        responses = domain_character_manager.route_message(
            message, context, requested_character
        )
        
        # PROACTIVE CLARIFICATION: Analyze message for ambiguity (Domain Characters)
        domain_clarification_questions = []
        if clarification_system:
            try:
                confidence, questions = clarification_system.analyze_message(message, context)
                if questions:
                    domain_clarification_questions = questions[:1]
                    print(f"❓ [DOMAIN] Clarification needed (confidence: {confidence.overall:.0%}): {questions[0].question}")
            except Exception as e:
                print(f"⚠️ Domain clarification analysis failed: {e}")
        
        # CHARACTER TRAIT ANALYSIS: Understand user's situation (Domain Characters)
        domain_situation = None
        if character_trait_system:
            try:
                domain_situation = character_trait_system.analyze_situation(message, context)
                # Always log situation analysis with flags
                flags = []
                if domain_situation.needs_validation:
                    flags.append("needs_validation")
                if domain_situation.needs_action:
                    flags.append("needs_action")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"🎭 [DOMAIN] Situation: {domain_situation.emotional_state} ({domain_situation.goal_type}){flag_str}")
                if domain_situation.emotional_state != 'neutral':
                    # Add to context for AI when not neutral
                    context['situation_analysis'] = {
                        'emotional_state': domain_situation.emotional_state,
                        'goal_type': domain_situation.goal_type,
                        'needs_validation': domain_situation.needs_validation,
                        'needs_action': domain_situation.needs_action
                    }
            except Exception as e:
                print(f"⚠️ Domain situation analysis failed: {e}")
        
        # EXPLICIT CONTEXT EXTRACTION: Capture user's explicit statements (Domain Characters)
        domain_explicit_context = []
        if explicit_context_handler:
            try:
                # Extract new explicit context from current message
                domain_explicit_context = explicit_context_handler.extract_explicit_context(
                    user_id, requested_character, message
                )
                if domain_explicit_context:
                    print(f"📌 [DOMAIN] Extracted {len(domain_explicit_context)} explicit context items")
                
                # Retrieve ALL past explicit context for AI prompt (user's stated goals, preferences, etc.)
                past_context_prompt = explicit_context_handler.format_for_ai_prompt(user_id, requested_character)
                if past_context_prompt:
                    context['explicit_user_context'] = past_context_prompt
                    print(f"📚 [DOMAIN] Retrieved past explicit context for AI")
            except Exception as e:
                print(f"⚠️ Domain explicit context extraction failed: {e}")
        
        # If AI integration available and use_ai is True, generate AI responses
        if use_ai and domain_character_ai and responses:
            ai_responses = []
            for resp in responses:
                if resp.should_display:
                    character = domain_character_manager.get_character(resp.character_id)
                    if character:
                        ai_resp = domain_character_ai.generate_response(
                            character, message, context
                        )
                        ai_responses.append(ai_resp)
                    else:
                        ai_responses.append(resp)
                else:
                    ai_responses.append(resp)
            responses = ai_responses
        
        # Format responses for frontend
        formatted_responses = []
        for resp in responses:
            formatted_responses.append({
                'character_id': resp.character_id,
                'display_name': resp.display_name,
                'content': resp.content,
                'concern_level': resp.concern_level,
                'should_display': resp.should_display,
                'metadata': resp.metadata
            })
        
        # Store AI responses using centralized integrated_db (same as regular characters)
        responding_chars = [r for r in formatted_responses if r.get('should_display')]
        
        # Record signal for which characters responded (for adaptive learning)
        if user_personalization and responding_chars:
            for resp in responding_chars:
                char_id = resp.get('character_id')
                if char_id and char_id != 'coordinator':
                    user_personalization.record_signal(
                        user_id, 'preferred_character', char_id,
                        context=f'Character responded to user message'
                    )
        
        for resp in responding_chars:
            char_id = resp.get('character_id')
            response_content = resp.get('content', '')
            display_name = resp.get('display_name', char_id)
            
            try:
                # If routed from coordinator, ALSO save user message to domain character's history
                # This ensures the original question appears when viewing that character's chat
                if target_character == 'coordinator' and char_id != 'coordinator':
                    integrated_db.save_character_message(user_id, char_id, 'user', message)
                    print(f"[HISTORY] ✓ Saved routed user message to {char_id}")
                
                # Save to the specific character's history
                integrated_db.save_character_message(user_id, char_id, 'assistant', response_content)
                print(f"[HISTORY] ✓ Saved AI response for {char_id}")
                
                # Log AI response for analytics
                try:
                    from smart_response.user_analytics import create_user_analytics
                    conn = integrated_db.get_connection()
                    analytics = create_user_analytics(conn)
                    analytics.log_activity(user_id, 'ai_response', 
                                           {'character': char_id, 'response_length': len(response_content)},
                                           page='life-companion')
                    conn.close()
                except Exception as ae:
                    pass  # Silent fail for analytics
                
                # ALSO save to coordinator's history if user was talking to coordinator
                # This ensures coordinator view shows complete conversation
                if target_character == 'coordinator' and char_id != 'coordinator':
                    # Include character attribution in coordinator's view
                    attributed_response = f"[{display_name}] {response_content}"
                    integrated_db.save_character_message(user_id, 'coordinator', 'assistant', attributed_response)
                    print(f"[HISTORY] ✓ Also saved to coordinator view")
            except Exception as e:
                print(f"[HISTORY] ✗ Failed to save response for {char_id}: {e}")
                
                # Add visibility: coordinator sees all responses
                try:
                    for hist_id, char_id in stored_ids:
                        # Character sees their own response
                        cursor.execute('''
                            INSERT OR IGNORE INTO message_visibility (history_id, character_id, role)
                            VALUES (?, ?, 'responder')
                        ''', (hist_id, char_id))
                        # Coordinator sees all
                        cursor.execute('''
                            INSERT OR IGNORE INTO message_visibility (history_id, character_id, role)
                            VALUES (?, 'coordinator', 'viewer')
                        ''', (hist_id,))
                    smart_response_conn.commit()
                    print(f"[VISIBILITY] ✓ {len(stored_ids)} responses stored")
                except Exception as e:
                    print(f"[VISIBILITY] ✗ Failed: {e}")
        
        # CONTINUOUS TRAIT REFINEMENT: Analyze conversation to update inferred personality
        # Runs periodically (not every message) to refine Big5 traits from conversation patterns
        if trait_inference:
            try:
                inference_result = trait_inference.run_inference_if_needed(user_id)
                if inference_result:
                    print(f"[TRAIT_INFERENCE] ✓ Updated traits for user {user_id} (confidence: {inference_result['confidence']:.0%})")
                    # Invalidate personality cache so new inferred traits take effect
                    if personality_integrator:
                        personality_integrator.invalidate_cache(user_id)
            except Exception as e:
                print(f"[TRAIT_INFERENCE] ⚠️ Failed: {e}")
        
        # AI Summarization (throttled - only when needed)
        # Triggers: every 8 messages, user references past, or summary is stale
        if user_context_mgr and context.get('needs_summary_refresh'):
            try:
                # Fetch recent messages for summary
                cursor = smart_response_conn.cursor()
                target_char = requested_character or 'coordinator'
                cursor.execute('''
                    SELECT hp.user_message, hp.assistant_response
                    FROM history_primary hp
                    LEFT JOIN message_visibility mv ON hp.id = mv.history_id AND mv.character_id = ?
                    WHERE hp.user_id = ?
                      AND (mv.character_id = ? OR hp.character = ?)
                      AND hp.assistant_response IS NOT NULL
                      AND hp.assistant_response != ''
                    ORDER BY hp.timestamp DESC
                    LIMIT 15
                ''', (target_char, user_id, target_char, target_char))
                recent_msgs = [{'user_message': r[0], 'assistant_response': r[1]} for r in cursor.fetchall()]
                
                if recent_msgs and len(recent_msgs) >= 3:
                    # Generate summary (uses AI - counts against budget)
                    summary = user_context_mgr.generate_summary(
                        user_id, target_char,
                        list(reversed(recent_msgs)),
                        context.get('history_id')
                    )
                    if summary:
                        print(f"[SUMMARY] ✓ Generated conversation summary")
            except Exception as e:
                print(f"[SUMMARY] ✗ Failed: {e}")
        
        # PROACTIVE CLARIFICATION: Append clarification to last response (Domain Characters)
        if domain_clarification_questions and clarification_system and formatted_responses:
            try:
                clarification_text = clarification_system.format_clarification_for_response(
                    domain_clarification_questions, 
                    context.get('user_language')
                )
                if clarification_text:
                    # Append to last displaying response
                    for resp in reversed(formatted_responses):
                        if resp.get('should_display'):
                            resp['content'] += clarification_text
                            resp['has_clarification'] = True
                            print(f"✅ [DOMAIN] Added clarification question to response")
                            break
            except Exception as e:
                print(f"⚠️ Failed to append domain clarification: {e}")
        
        response_data = {
            'success': True,
            'responses': formatted_responses,
            'responding_count': len([r for r in formatted_responses if r['should_display']]),
            'message': message,
            'ai_generated': use_ai and domain_character_ai is not None
        }
        
        # Add situation analysis to response metadata
        if domain_situation:
            response_data['situation'] = {
                'emotional_state': domain_situation.emotional_state,
                'goal_type': domain_situation.goal_type,
                'needs_validation': domain_situation.needs_validation,
                'needs_action': domain_situation.needs_action
            }
        
        return jsonify(response_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/analyze', methods=['POST'])
@require_auth
def analyze_with_domain_characters():
    """
    Analyze a message with all domain characters without generating responses.
    Returns concern levels for each character.
    """
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        user_id = request.current_user.get('user_id')
        context = {'user_id': user_id}
        
        # Analyze with all domain characters
        analysis = []
        for char_id, character in domain_character_manager.get_domain_characters().items():
            concern_level = character.analyze_context(message, context)
            would_respond = character.should_respond(concern_level)
            
            analysis.append({
                'character_id': char_id,
                'display_name': character.display_name,
                'domain': character.domain,
                'concern_level': concern_level,
                'would_respond': would_respond,
                'threshold': character.threshold_config.base_threshold
            })
        
        # Sort by concern level descending
        analysis.sort(key=lambda x: x['concern_level'], reverse=True)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'responding_characters': [a['character_id'] for a in analysis if a['would_respond']],
            'message': message
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/interpretations/<int:history_id>')
@require_auth
def get_character_interpretations(history_id):
    """Get all character interpretations for a specific message"""
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        interpretations = domain_character_manager.get_interpretations_for_message(history_id)
        critical = domain_character_manager.get_critical_perspectives(history_id)
        
        return jsonify({
            'success': True,
            'history_id': history_id,
            'interpretations': interpretations,
            'critical_perspectives': critical
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/cross-domain', methods=['POST'])
@require_auth
def get_cross_domain_insights():
    """
    Get cross-domain insights for a message.
    Returns correlations between domains and multi-domain patterns.
    """
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        user_id = request.current_user['user_id']
        context = {'user_id': user_id}
        
        # Get coordinator's cross-domain analysis
        coordinator = domain_character_manager.coordinator
        if coordinator:
            cross_domain = coordinator.get_cross_domain_insights(message, context)
            domain_insights = coordinator._get_domain_insights({**context, 'message': message})
        else:
            cross_domain = {'domains_affected': [], 'correlations': []}
            domain_insights = []
        
        # Separate characters into responded vs silent observers
        # Threshold for responding is typically 0.15 (from character config)
        response_threshold = 0.15
        
        responded = []
        silent_observers = []
        
        for insight in domain_insights:
            char_info = {
                'character': insight['display_name'],
                'domain': insight['domain'],
                'concern_level': round(insight['concern_level'], 2)
            }
            
            if insight['concern_level'] >= response_threshold:
                # This character would have responded
                char_info['status'] = 'responded'
                responded.append(char_info)
            elif insight['concern_level'] >= 0.05:
                # Noticed but didn't respond (below threshold but still detected something)
                char_info['status'] = 'noticed'
                silent_observers.append(char_info)
        
        return jsonify({
            'success': True,
            'cross_domain': cross_domain,
            'responded': responded,
            'silent_observers': silent_observers,
            'domain_insights': domain_insights
        })
    except Exception as e:
        print(f"Error in cross-domain insights: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/user-insights', methods=['GET'])
@require_auth
def get_user_insights():
    """
    Get accumulated insights about the user from all characters.
    Shows what each character has learned about the user over time.
    """
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        user_id = request.current_user['user_id']
        
        all_insights = {}
        
        # Get insights from each domain character
        for char_id, character in domain_character_manager.domain_characters.items():
            if hasattr(character, 'get_user_history_insights'):
                insights = character.get_user_history_insights(user_id)
                if insights and insights.get('total_interactions', 0) > 0:
                    all_insights[char_id] = {
                        'display_name': character.display_name,
                        'domain': getattr(character, 'domain', 'general'),
                        'total_interactions': insights.get('total_interactions', 0),
                        'responded_count': insights.get('responded_count', 0),
                        'engagement_rate': round(insights.get('engagement_rate', 0) * 100),
                        'avg_concern': round(insights.get('avg_concern', 0) * 100),
                        'common_emotions': [{'emotion': e[0], 'count': e[1]} for e in insights.get('common_emotions', [])],
                        'common_themes': [{'theme': t[0], 'count': t[1]} for t in insights.get('common_themes', [])],
                        'common_tags': [{'tag': t[0], 'count': t[1]} for t in insights.get('common_tags', [])]
                    }
        
        # Get coordinator insights too
        if domain_character_manager.coordinator and hasattr(domain_character_manager.coordinator, 'get_user_history_insights'):
            coord_insights = domain_character_manager.coordinator.get_user_history_insights(user_id)
            if coord_insights and coord_insights.get('total_interactions', 0) > 0:
                all_insights['coordinator'] = {
                    'display_name': domain_character_manager.coordinator.display_name,
                    'domain': 'coordinator',
                    'total_interactions': coord_insights.get('total_interactions', 0),
                    'responded_count': coord_insights.get('responded_count', 0),
                    'engagement_rate': round(coord_insights.get('engagement_rate', 0) * 100),
                    'avg_concern': round(coord_insights.get('avg_concern', 0) * 100),
                    'common_emotions': [{'emotion': e[0], 'count': e[1]} for e in coord_insights.get('common_emotions', [])],
                    'common_themes': [{'theme': t[0], 'count': t[1]} for t in coord_insights.get('common_themes', [])],
                    'common_tags': [{'tag': t[0], 'count': t[1]} for t in coord_insights.get('common_tags', [])]
                }
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'insights': all_insights
        })
    except Exception as e:
        print(f"Error getting user insights: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# ADMIN SETTINGS API
# =============================================================================

@app.route('/api/admin/settings', methods=['GET'])
@require_auth
def get_admin_settings():
    """Get all admin settings (admin only)"""
    try:
        user = request.current_user
        if user.get('username') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        from smart_response.admin_settings import get_admin_settings as get_settings_instance
        settings = get_settings_instance()
        
        return jsonify({
            'success': True,
            'settings': settings.get_all(),
            'categories': settings.get_categories()
        })
    except Exception as e:
        print(f"Error getting admin settings: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/settings/<key>', methods=['PUT'])
@require_auth
def update_admin_setting(key):
    """Update a single admin setting (admin only)"""
    try:
        user = request.current_user
        if user.get('username') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        value = data.get('value')
        
        if value is None:
            return jsonify({'error': 'Value is required'}), 400
        
        from smart_response.admin_settings import get_admin_settings as get_settings_instance
        settings = get_settings_instance()
        
        # Validate the setting
        is_valid, error = settings.validate_setting(key, value)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Update the setting
        success = settings.set(key, value, updated_by=user.get('username'))
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Setting {key} updated successfully'
            })
        else:
            return jsonify({'error': 'Setting not found'}), 404
            
    except Exception as e:
        print(f"Error updating admin setting: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/data-cleanup/stats', methods=['GET'])
@require_auth
def get_data_cleanup_stats():
    """Get data cleanup statistics (admin only)"""
    try:
        user = request.current_user
        if user.get('username') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        from smart_response.data_cleanup import get_cleanup_manager
        cleanup = get_cleanup_manager()
        
        return jsonify({
            'success': True,
            'stats': cleanup.get_cleanup_stats()
        })
    except Exception as e:
        print(f"Error getting cleanup stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/data-cleanup/run', methods=['POST'])
@require_auth
def run_data_cleanup():
    """Run data cleanup (admin only)"""
    try:
        user = request.current_user
        if user.get('username') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        dry_run = data.get('dry_run', True)  # Default to dry run for safety
        
        from smart_response.data_cleanup import get_cleanup_manager
        cleanup = get_cleanup_manager()
        
        result = cleanup.cleanup_expired_interpretations(dry_run=dry_run)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        print(f"Error running cleanup: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# USER DATA CONTROL API (Privacy/GDPR)
# =============================================================================

@app.route('/api/user/my-data', methods=['GET'])
@require_auth
def get_user_data():
    """Get user's own data (for viewing/export)"""
    try:
        from smart_response.admin_settings import get_setting
        
        # Check if viewing is enabled
        if not get_setting('user_can_view_insights', True):
            return jsonify({'error': 'This feature is currently disabled'}), 403
        
        user_id = request.current_user.get('user_id')
        
        from smart_response.data_cleanup import get_cleanup_manager
        cleanup = get_cleanup_manager()
        
        export_data = cleanup.export_user_data(user_id)
        
        return jsonify({
            'success': True,
            'data': export_data
        })
    except Exception as e:
        print(f"Error getting user data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/my-data/export', methods=['GET'])
@require_auth
def export_user_data():
    """Export user's own data as JSON download"""
    try:
        from smart_response.admin_settings import get_setting
        
        # Check if export is enabled
        if not get_setting('user_can_export_data', True):
            return jsonify({'error': 'Data export is currently disabled'}), 403
        
        user_id = request.current_user.get('user_id')
        username = request.current_user.get('username', 'user')
        
        from smart_response.data_cleanup import get_cleanup_manager
        cleanup = get_cleanup_manager()
        
        export_data = cleanup.export_user_data(user_id)
        
        # Return as downloadable JSON
        response = make_response(json.dumps(export_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename={username}_data_export.json'
        
        return response
    except Exception as e:
        print(f"Error exporting user data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/my-data/delete', methods=['DELETE'])
@require_auth
def delete_user_insights():
    """Delete user's interpretation/insight data"""
    try:
        from smart_response.admin_settings import get_setting
        
        # Check if deletion is enabled
        if not get_setting('user_can_delete_insights', True):
            return jsonify({'error': 'Data deletion is currently disabled'}), 403
        
        user_id = request.current_user.get('user_id')
        
        from smart_response.data_cleanup import get_cleanup_manager
        cleanup = get_cleanup_manager()
        
        result = cleanup.cleanup_user_data(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Your insight data has been deleted',
            'details': result
        })
    except Exception as e:
        print(f"Error deleting user data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/feedback', methods=['POST'])
@require_auth
def submit_character_feedback():
    """Submit feedback for a character's response"""
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        data = request.get_json()
        character_id = data.get('character_id')
        feedback = data.get('feedback')  # 'positive' or 'negative'
        
        if not character_id or feedback not in ['positive', 'negative']:
            return jsonify({'error': 'Invalid character_id or feedback'}), 400
        
        user_id = request.current_user.get('user_id')
        
        # Update user preference for this character
        domain_character_manager.update_user_preference(user_id, character_id, feedback)
        
        # Record signal for adaptive personalization
        if user_personalization:
            signal_type = 'preferred_character' if feedback == 'positive' else 'topic_avoid'
            user_personalization.record_signal(
                user_id, signal_type, character_id,
                context=f'User gave {feedback} feedback'
            )
        
        return jsonify({
            'success': True,
            'message': f'Feedback recorded for {character_id}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/preferences')
@require_auth
def get_character_preferences():
    """Get user's preference scores for all characters"""
    try:
        if not domain_character_manager:
            return jsonify({'error': 'Domain character system not initialized'}), 500
        
        user_id = request.current_user.get('user_id')
        preferences = domain_character_manager.get_user_preferences(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'preferences': preferences
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/domain-characters/history/<character_id>')
@require_auth
def get_character_history(character_id):
    """Get conversation history for a specific character - uses centralized integrated_db"""
    try:
        user_id = request.current_user.get('user_id')
        limit = request.args.get('limit', 50, type=int)
        
        # Use centralized integrated_db.get_character_messages() - same as regular characters
        # This ensures consistency across all character types
        messages = integrated_db.get_character_messages(user_id, character_id, limit)
        
        # Convert to history format expected by frontend
        history = []
        for msg in messages:
            history.append({
                'id': msg.get('id'),
                'user_message': msg.get('content') if msg.get('sender_type') == 'user' else '',
                'ai_response': msg.get('content') if msg.get('sender_type') == 'assistant' else '',
                'timestamp': msg.get('timestamp'),
                'character': character_id,
                'role': 'owner'
            })
        
        # Group consecutive user/assistant messages into pairs
        paired_history = []
        i = 0
        while i < len(history):
            entry = {'id': None, 'user_message': '', 'ai_response': '', 'timestamp': '', 'character': character_id}
            
            # Get user message
            if i < len(history) and history[i].get('user_message'):
                entry['user_message'] = history[i]['user_message']
                entry['timestamp'] = history[i]['timestamp']
                entry['id'] = history[i]['id']
                i += 1
            
            # Get assistant response
            if i < len(history) and history[i].get('ai_response'):
                entry['ai_response'] = history[i]['ai_response']
                if not entry['timestamp']:
                    entry['timestamp'] = history[i]['timestamp']
                if not entry['id']:
                    entry['id'] = history[i]['id']
                i += 1
            
            if entry['user_message'] or entry['ai_response']:
                paired_history.append(entry)
        
        # Sort by timestamp to ensure chronological order
        # This handles edge cases where pairing/filtering might disrupt order
        def parse_timestamp(ts):
            if not ts:
                return ''
            # Normalize timestamp for sorting
            ts_str = str(ts).replace('Z', '').replace('+00:00', '')
            return ts_str
        
        paired_history.sort(key=lambda x: parse_timestamp(x.get('timestamp', '')))
        
        return jsonify({
            'success': True,
            'character_id': character_id,
            'history': paired_history,
            'count': len(paired_history)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


print("✓ Domain Character API endpoints registered")


# ============================================
# ADMIN: AI PROVIDER ERROR LOG API
# ============================================

@app.route('/api/admin/ai-errors')
@require_auth
def get_ai_provider_errors():
    """Get AI provider errors for admin review"""
    try:
        # Check if user is admin (for now, allow any authenticated user to view)
        limit = request.args.get('limit', 50, type=int)
        provider = request.args.get('provider')
        unresolved_only = request.args.get('unresolved', 'false').lower() == 'true'
        
        if domain_character_ai and hasattr(domain_character_ai, 'error_log'):
            errors = domain_character_ai.error_log.get_recent_errors(
                limit=limit,
                provider=provider,
                unresolved_only=unresolved_only
            )
            stats = domain_character_ai.error_log.get_error_stats()
            
            return jsonify({
                'success': True,
                'errors': errors,
                'stats': stats,
                'provider_status': domain_character_ai.provider_status
            })
        else:
            return jsonify({
                'success': True,
                'errors': [],
                'stats': {},
                'provider_status': {},
                'message': 'Error logging not initialized'
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ai-errors/<int:error_id>/resolve', methods=['POST'])
@require_auth
def resolve_ai_error(error_id):
    """Mark an AI provider error as resolved"""
    try:
        data = request.get_json() or {}
        admin_notes = data.get('notes', '')
        
        if domain_character_ai and hasattr(domain_character_ai, 'error_log'):
            success = domain_character_ai.error_log.mark_resolved(error_id, admin_notes)
            return jsonify({'success': success})
        else:
            return jsonify({'error': 'Error logging not initialized'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ai-provider-status')
@require_auth
def get_ai_provider_status():
    """Get current AI provider health status"""
    try:
        if domain_character_ai:
            return jsonify({
                'success': True,
                'provider_status': domain_character_ai.provider_status,
                'openai_available': domain_character_ai.openai_client is not None,
                'anthropic_available': domain_character_ai.anthropic_client is not None
            })
        else:
            return jsonify({
                'success': False,
                'error': 'AI integration not initialized'
            }), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/ai-errors')
def admin_ai_errors_page():
    """Admin page for viewing AI provider errors - auth handled client-side"""
    return render_template('admin_ai_errors.html')

@app.route('/admin/analytics')
def admin_analytics_page():
    """Admin analytics dashboard - auth handled client-side"""
    return render_template('admin_analytics.html')


print("✓ Admin AI Error Log API endpoints registered")


# ============================================
# USER CONTEXT API (PHASE 2 POLISH)
# ============================================

@app.route('/api/user/context')
@require_auth
def get_user_context():
    """
    Get all explicit context (ADMIN ONLY)
    Returns context organized by type (emotional_states, goals, preferences, etc.)
    """
    try:
        # Admin only
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        # Allow admin to query any user's context
        user_id = request.args.get('user_id')
        if not user_id:
            user_id = request.current_user['user_id']
        
        character = request.args.get('character', 'all')
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Build query
        if character == 'all':
            cursor.execute('''
                SELECT id, user_id, character, timestamp, context_type, context_key, 
                       context_value, original_statement, priority, confidence, 
                       active, expires_at
                FROM explicit_context
                WHERE user_id = ? AND active = 1
                ORDER BY timestamp DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT id, user_id, character, timestamp, context_type, context_key, 
                       context_value, original_statement, priority, confidence, 
                       active, expires_at
                FROM explicit_context
                WHERE user_id = ? AND character = ? AND active = 1
                ORDER BY timestamp DESC
            ''', (user_id, character))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Organize by context type
        context_by_type = {}
        for row in rows:
            item = {
                'id': row[0],
                'user_id': row[1],
                'character': row[2],
                'timestamp': row[3],
                'context_type': row[4],
                'context_key': row[5],
                'context_value': row[6],
                'original_statement': row[7],
                'priority': row[8],
                'confidence': row[9],
                'active': bool(row[10]),
                'expires_at': row[11]
            }
            
            context_type = row[4]
            if context_type not in context_by_type:
                context_by_type[context_type] = []
            context_by_type[context_type].append(item)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'context_by_type': context_by_type,
            'total_items': len(rows)
        })
        
    except Exception as e:
        print(f"❌ Error in get_user_context: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/context/<int:context_id>', methods=['PUT'])
@require_auth
def update_user_context(context_id):
    """
    Update a specific context item (ADMIN ONLY)
    Admins can update any context item
    """
    try:
        # Admin only
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.json
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Verify context exists
        cursor.execute('''
            SELECT user_id FROM explicit_context WHERE id = ?
        ''', (context_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Context item not found'}), 404
        
        # Update allowed fields
        update_fields = []
        update_values = []
        
        if 'context_value' in data:
            update_fields.append('context_value = ?')
            update_values.append(data['context_value'])
        
        if 'active' in data:
            update_fields.append('active = ?')
            update_values.append(1 if data['active'] else 0)
        
        if not update_fields:
            conn.close()
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Perform update
        update_values.append(context_id)
        cursor.execute(f'''
            UPDATE explicit_context
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Context updated successfully',
            'context_id': context_id
        })
        
    except Exception as e:
        print(f"❌ Error in update_user_context: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/context/<int:context_id>', methods=['DELETE'])
@require_auth
def delete_user_context(context_id):
    """
    Delete (deactivate) a specific context item (ADMIN ONLY)
    Soft delete: sets active = 0 instead of removing from database
    Admins can delete any context item
    """
    try:
        # Admin only
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Verify context exists
        cursor.execute('''
            SELECT user_id FROM explicit_context WHERE id = ?
        ''', (context_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Context item not found'}), 404
        
        # Soft delete (set active = 0)
        cursor.execute('''
            UPDATE explicit_context
            SET active = 0
            WHERE id = ?
        ''', (context_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Context item deleted successfully',
            'context_id': context_id
        })
        
    except Exception as e:
        print(f"❌ Error in delete_user_context: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================
# PATTERN EXPANSION & ARCHIVAL (ADMIN ONLY)
# ============================================

@app.route('/admin/pattern-manager')
def pattern_manager_page():
    """Pattern Manager Dashboard (Admin Only)"""
    return render_template('pattern_manager.html')


@app.route('/api/admin/patterns/suggestions')
@require_auth
def get_pattern_suggestions():
    """Get pending pattern suggestions"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        from smart_response.pattern_expander import PatternExpander
        expander = PatternExpander()
        suggestions = expander.get_pending_suggestions()
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
    except Exception as e:
        print(f"❌ Error getting pattern suggestions: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/patterns/analyze', methods=['POST'])
@require_auth
def run_pattern_analysis():
    """Manually trigger pattern analysis"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.json or {}
        days = data.get('days', 7)
        limit = data.get('limit', 50)
        
        from smart_response.pattern_expander import PatternExpander
        expander = PatternExpander()
        suggestions = expander.analyze_recent_messages(days=days, limit=limit)
        
        return jsonify({
            'success': True,
            'suggestions_count': len(suggestions),
            'message': f'Analyzed messages from last {days} days'
        })
    except Exception as e:
        print(f"❌ Error running pattern analysis: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/patterns/<int:pattern_id>/approve', methods=['POST'])
@require_auth
def approve_pattern(pattern_id):
    """Approve a pattern suggestion"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.json or {}
        notes = data.get('notes')
        
        from smart_response.pattern_expander import PatternExpander
        expander = PatternExpander()
        expander.approve_pattern(pattern_id, request.current_user['user_id'], notes)
        
        return jsonify({
            'success': True,
            'message': 'Pattern approved'
        })
    except Exception as e:
        print(f"❌ Error approving pattern: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/patterns/<int:pattern_id>/reject', methods=['POST'])
@require_auth
def reject_pattern(pattern_id):
    """Reject a pattern suggestion"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.json or {}
        reason = data.get('reason')
        
        from smart_response.pattern_expander import PatternExpander
        expander = PatternExpander()
        expander.reject_pattern(pattern_id, request.current_user['user_id'], reason)
        
        return jsonify({
            'success': True,
            'message': 'Pattern rejected'
        })
    except Exception as e:
        print(f"❌ Error rejecting pattern: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/archival/run', methods=['POST'])
@require_auth
def run_archival_maintenance():
    """Manually trigger archival maintenance"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        from smart_response.context_archival import ContextArchival
        archival = ContextArchival()
        results = archival.run_maintenance()
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        print(f"❌ Error running archival: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/archival/stats')
@require_auth
def get_archival_stats():
    """Get archival statistics"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        from smart_response.context_archival import ContextArchival
        archival = ContextArchival()
        stats = archival.get_archival_statistics()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        print(f"❌ Error getting archival stats: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================
# DATABASE BACKUP SYSTEM (ADMIN ONLY)
# ============================================

@app.route('/admin/backup-manager')
def backup_manager_page():
    """Database Backup Manager Dashboard (Admin Only)"""
    return render_template('backup_manager.html')


@app.route('/api/admin/backup/status')
@require_auth
def get_backup_status():
    """Get current backup status for all databases"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        status = backup_manager.get_backup_status()
        return jsonify({'success': True, **status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backup/list')
@require_auth
def list_backups():
    """List all available backups"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        db_name = request.args.get('database')  # Optional filter
        backups = backup_manager.list_backups(db_name)
        return jsonify({'success': True, 'backups': backups, 'count': len(backups)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backup/run', methods=['POST'])
@require_auth
def run_backup():
    """Manually trigger a backup of all databases"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        reason = data.get('reason', 'manual')
        db_name = data.get('database')  # Optional: backup specific database
        
        if db_name:
            result = backup_manager.backup_database(db_name, reason)
            results = [result]
        else:
            results = backup_manager.backup_all(reason=reason)
        
        success_count = sum(1 for r in results if r['success'])
        return jsonify({
            'success': True,
            'message': f'Backed up {success_count}/{len(results)} databases',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backup/restore', methods=['POST'])
@require_auth
def restore_backup():
    """Restore a database from backup (DANGEROUS - requires confirmation)"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required for restore'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        db_name = data.get('database')
        backup_file = data.get('backup_file')  # Optional: specific backup
        confirm = data.get('confirm')
        
        if not db_name:
            return jsonify({'error': 'Database name required'}), 400
        
        if confirm != 'RESTORE':
            return jsonify({'error': 'Confirmation required: set confirm="RESTORE"'}), 400
        
        result = backup_manager.restore_database(db_name, backup_file)
        
        if result['success']:
            return jsonify({'success': True, 'message': f'Restored {db_name}', 'result': result})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/backup/download/<path:backup_path>')
@require_auth
def download_backup(backup_path):
    """Download a specific backup file"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        # Security: ensure path is within backup directory
        full_path = Path(backup_manager.backup_dir) / backup_path
        if not str(full_path.resolve()).startswith(str(backup_manager.backup_dir.resolve())):
            return jsonify({'error': 'Invalid backup path'}), 400
        
        if not full_path.exists():
            return jsonify({'error': 'Backup not found'}), 404
        
        return send_file(
            full_path,
            as_attachment=True,
            download_name=full_path.name
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# AI USAGE MONITORING (ADMIN ONLY)
# ============================================

@app.route('/admin/ai-usage-monitor')
def ai_usage_monitor_page():
    """AI Usage Monitoring Dashboard (Admin Only)
    
    Note: Page itself is not authenticated - authentication happens via JavaScript
    when calling the API endpoints. This allows the page to load and then the
    JavaScript can check localStorage for the token and make authenticated API calls.
    """
    return render_template('ai_usage_monitor.html')


@app.route('/admin/context-manager')
def context_manager_page():
    """Context Manager Dashboard (Admin Only)
    
    Note: Page itself is not authenticated - authentication happens via JavaScript
    when calling the API endpoints. This allows the page to load and then the
    JavaScript can check localStorage for the token and make authenticated API calls.
    """
    return render_template('context_manager.html')


@app.route('/api/admin/ai-usage/summary')
@require_auth
def get_ai_usage_summary():
    """Get summary statistics for AI usage"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
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
        print(f"❌ Error in get_ai_usage_summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ai-usage/daily-chart')
@require_auth
def get_daily_chart_data():
    """Get daily AI usage for last 7 days with interactive vs background breakdown"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Get daily breakdown for last 7 days
        # Infer background from purpose field for historical data where is_background wasn't set
        cursor.execute('''
            SELECT 
                DATE(timestamp) as call_date,
                COUNT(CASE WHEN (
                    is_background = 0 AND is_automated = 0 
                    AND purpose NOT LIKE '%greeting%' 
                    AND purpose NOT LIKE '%summary%'
                    AND purpose NOT LIKE '%context_prompt%'
                    AND purpose NOT LIKE '%character_expansion%'
                    AND purpose LIKE '%chat%'
                ) THEN 1 END) as interactive_calls,
                COUNT(CASE WHEN (
                    is_background = 1 OR is_automated = 1
                    OR purpose LIKE '%greeting%' 
                    OR purpose LIKE '%summary%'
                    OR purpose LIKE '%context_prompt%'
                    OR purpose LIKE '%character_expansion%'
                    OR purpose NOT LIKE '%chat%'
                ) THEN 1 END) as background_calls,
                COUNT(*) as total_calls
            FROM ai_usage_log
            WHERE timestamp >= DATE('now', '-7 days')
            AND success = 1
            GROUP BY DATE(timestamp)
            ORDER BY call_date ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Build response with all 7 days (fill missing days with 0)
        from datetime import datetime, timedelta
        result = []
        today = datetime.now().date()
        
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            day_label = day.strftime('%a %d/%m')
            
            # Find matching row
            matching = next((r for r in rows if r[0] == day_str), None)
            if matching:
                result.append({
                    'date': day_str,
                    'label': day_label,
                    'interactive': matching[1],
                    'background': matching[2],
                    'total': matching[3]
                })
            else:
                result.append({
                    'date': day_str,
                    'label': day_label,
                    'interactive': 0,
                    'background': 0,
                    'total': 0
                })
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ Error in get_daily_chart_data: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ai-usage/daily')
@require_auth
def get_daily_ai_usage():
    """Get today's AI usage by user"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        sort_by = request.args.get('sort', 'calls_desc')
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Get today's usage per user
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.user_role,
                COUNT(CASE WHEN (a.is_background = 0 AND a.is_automated = 0) THEN 1 END) as user_calls,
                COUNT(CASE WHEN (a.is_background = 1 OR a.is_automated = 1) THEN 1 END) as auto_calls,
                COUNT(a.id) as total_calls
            FROM users u
            LEFT JOIN ai_usage_log a ON u.id = a.user_id 
                AND DATE(a.timestamp) = DATE('now')
                AND a.success = 1
            GROUP BY u.id, u.username, u.user_role
            HAVING total_calls > 0
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'is_admin': row[2] == 'administrator',
                'user_calls': row[3],
                'auto_calls': row[4],
                'total_calls': row[5]
            })
        
        conn.close()
        
        # Sort
        if sort_by == 'calls_desc':
            users.sort(key=lambda x: x['total_calls'], reverse=True)
        elif sort_by == 'calls_asc':
            users.sort(key=lambda x: x['total_calls'])
        elif sort_by == 'username':
            users.sort(key=lambda x: x['username'].lower())
        elif sort_by == 'role':
            users.sort(key=lambda x: (not x['is_admin'], x['username'].lower()))
        
        return jsonify(users)
    except Exception as e:
        print(f"❌ Error in get_daily_ai_usage: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/ai-usage/monthly')
@require_auth
def get_monthly_ai_usage():
    """Get this month's AI usage by user"""
    try:
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        if not has_admin_access(user_role):
            return jsonify({'error': 'Admin access required'}), 403
        
        sort_by = request.args.get('sort', 'calls_desc')
        
        conn = sqlite3.connect('integrated_users.db')
        cursor = conn.cursor()
        
        # Get month's usage per user
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.user_role,
                COUNT(CASE WHEN (a.is_background = 0 AND a.is_automated = 0) THEN 1 END) as user_calls,
                COUNT(CASE WHEN (a.is_background = 1 OR a.is_automated = 1) THEN 1 END) as auto_calls,
                COUNT(a.id) as total_calls,
                DATE(a.timestamp) as call_date
            FROM users u
            LEFT JOIN ai_usage_log a ON u.id = a.user_id 
                AND DATE(a.timestamp, 'start of month') = DATE('now', 'start of month')
                AND a.success = 1
            GROUP BY u.id, u.username, u.user_role, call_date
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
                    'user_calls': 0,
                    'auto_calls': 0,
                    'total_calls': 0,
                    'daily_calls': []
                }
            user_data[user_id]['user_calls'] += row[3]
            user_data[user_id]['auto_calls'] += row[4]
            user_data[user_id]['total_calls'] += row[5]
            if row[6]:  # If there's a date
                user_data[user_id]['daily_calls'].append(row[5])
        
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
                    'user_calls': data['user_calls'],
                    'auto_calls': data['auto_calls'],
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
        print(f"❌ Error in get_monthly_ai_usage: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =============================================================================
# DEVELOPER API ENDPOINTS (developer role only - beyond admin)
# =============================================================================

def require_developer(f):
    """Decorator to require developer or admin role"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or not request.current_user:
            return jsonify({'error': 'Authentication required'}), 401
        user_role = integrated_db.get_user_role(request.current_user['user_id'])
        # Allow both developer and administrator roles
        if user_role not in ('developer', 'administrator'):
            return jsonify({'error': 'Developer/Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/api/developer/metrics', methods=['GET'])
@require_auth
@require_developer
def get_developer_metrics():
    """Get comprehensive system metrics (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        developer_analytics.log_access(
            request.current_user['user_id'], 'get_metrics', '/api/developer/metrics'
        )
        metrics = developer_analytics.get_system_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/ai-calls', methods=['GET'])
@require_auth
@require_developer
def get_developer_ai_calls():
    """Get detailed AI call logs (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        limit = request.args.get('limit', 100, type=int)
        filters = {}
        
        # Support days parameter for date range
        days = request.args.get('days', type=int)
        if days:
            from datetime import datetime, timedelta
            filters['date_from'] = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        if request.args.get('call_type'):
            filters['call_type'] = request.args.get('call_type')
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id', type=int)
        
        developer_analytics.log_access(
            request.current_user['user_id'], 'get_ai_calls', '/api/developer/ai-calls',
            {'limit': limit, 'filters': filters}
        )
        calls = developer_analytics.get_ai_call_details(limit, filters if filters else None)
        return jsonify(calls)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/user-context', methods=['GET'])
@require_auth
@require_developer
def get_developer_user_context():
    """Get user context analysis (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        user_id = request.args.get('user_id', type=int)
        developer_analytics.log_access(
            request.current_user['user_id'], 'get_user_context', '/api/developer/user-context',
            {'target_user_id': user_id}
        )
        analysis = developer_analytics.get_user_context_analysis(user_id)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/character-effectiveness', methods=['GET'])
@require_auth
@require_developer
def get_developer_character_effectiveness():
    """Get character effectiveness scores (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        developer_analytics.log_access(
            request.current_user['user_id'], 'get_character_effectiveness', 
            '/api/developer/character-effectiveness'
        )
        effectiveness = developer_analytics.get_character_effectiveness()
        return jsonify(effectiveness)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/clarification-stats', methods=['GET'])
@require_auth
@require_developer
def get_developer_clarification_stats():
    """Get clarification system effectiveness (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        developer_analytics.log_access(
            request.current_user['user_id'], 'get_clarification_stats',
            '/api/developer/clarification-stats'
        )
        stats = developer_analytics.get_clarification_effectiveness()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/export/<table>', methods=['GET'])
@require_auth
@require_developer
def export_developer_data(table):
    """Export table data for analysis (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        format_type = request.args.get('format', 'json')
        limit = request.args.get('limit', type=int)
        
        developer_analytics.log_access(
            request.current_user['user_id'], 'export_data',
            f'/api/developer/export/{table}',
            {'format': format_type, 'limit': limit}
        )
        
        filters = {'limit': limit} if limit else None
        data = developer_analytics.export_data(table, format_type, filters)
        
        if format_type == 'csv':
            from flask import Response
            return Response(data, mimetype='text/csv',
                          headers={'Content-Disposition': f'attachment; filename={table}.csv'})
        return jsonify(data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/query', methods=['POST'])
@require_auth
@require_developer
def run_developer_query():
    """Run custom SELECT query (developer only - DANGEROUS)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        data = request.get_json()
        query = data.get('query', '')
        params = tuple(data.get('params', []))
        
        developer_analytics.log_access(
            request.current_user['user_id'], 'custom_query',
            '/api/developer/query',
            {'query': query[:200]}  # Log first 200 chars
        )
        
        result = developer_analytics.run_custom_query(query, params if params else None)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/debug', methods=['GET'])
@require_auth
@require_developer
def get_developer_debug():
    """Get debug information (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        component = request.args.get('component', 'all')
        developer_analytics.log_access(
            request.current_user['user_id'], 'get_debug',
            '/api/developer/debug', {'component': component}
        )
        debug_info = developer_analytics.get_debug_info(component)
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/health-snapshot', methods=['POST'])
@require_auth
@require_developer
def take_health_snapshot():
    """Take a health snapshot (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        developer_analytics.log_access(
            request.current_user['user_id'], 'take_snapshot',
            '/api/developer/health-snapshot'
        )
        snapshot_id = developer_analytics.take_health_snapshot()
        return jsonify({'success': True, 'snapshot_id': snapshot_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/health-history', methods=['GET'])
@require_auth
@require_developer
def get_health_history():
    """Get health snapshot history (developer only)"""
    try:
        if not developer_analytics:
            return jsonify({'error': 'Developer analytics not initialized'}), 500
        
        days = request.args.get('days', 7, type=int)
        developer_analytics.log_access(
            request.current_user['user_id'], 'get_health_history',
            '/api/developer/health-history', {'days': days}
        )
        history = developer_analytics.get_health_history(days)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/developer/access-log', methods=['GET'])
@require_auth
@require_developer
def get_developer_access_log():
    """Get developer access audit log (developer only)"""
    try:
        cursor = smart_response_conn.cursor()
        cursor.execute('''
            SELECT id, user_id, action, endpoint, parameters, result_summary, timestamp
            FROM developer_access_log
            ORDER BY timestamp DESC LIMIT 100
        ''')
        logs = [
            {'id': r[0], 'user_id': r[1], 'action': r[2], 'endpoint': r[3],
             'parameters': r[4], 'result_summary': r[5], 'timestamp': r[6]}
            for r in cursor.fetchall()
        ]
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# ==================== API SELF-DOCUMENTATION ====================

def _get_category_for_route(rule_path):
    """Determine category based on route path"""
    category_prefixes = [
        ('/api/auth/', 'authentication'),
        ('/api/admin/', 'admin'),
        ('/api/developer/', 'developer'),
        ('/api/user/explicit-context', 'explicit_context'),
        ('/api/user/', 'user'),
        ('/api/ai-budget/', 'ai_budget'),
        ('/api/domain-characters/', 'domain_characters'),
        ('/api/personality/', 'personality'),
        ('/api/smart-response/', 'smart_response'),
        ('/api/history/', 'history'),
        ('/api/context/', 'context'),
        ('/api/profile/', 'profile'),
        ('/api/explicit-context/', 'explicit_context'),
        ('/chat/', 'chat'),
        ('/personality/', 'personality'),
        ('/api/', 'other'),
    ]
    for prefix, category in category_prefixes:
        if rule_path.startswith(prefix):
            return category
    return None

def _get_category_description(category):
    """Get human-readable description for category"""
    descriptions = {
        'authentication': 'User authentication and session management',
        'admin': 'Administrative functions (requires admin role)',
        'developer': 'Developer analytics and debugging (requires developer role)',
        'explicit_context': 'User-stated goals, preferences, and values',
        'user': 'User profile and preferences',
        'ai_budget': 'AI usage budget and cost control',
        'domain_characters': 'AI characters with specific domains/expertise',
        'personality': 'Personality assessment and profiling',
        'smart_response': 'Smart response system analytics',
        'history': 'Conversation history and analytics',
        'context': 'Conversation context management',
        'profile': 'User profile management',
        'chat': 'Main chat functionality',
        'other': 'Other API endpoints',
    }
    return descriptions.get(category, category.replace('_', ' ').title())

@app.route('/api')
def api_documentation():
    """Self-documenting API endpoint - dynamically lists all available APIs"""
    categories = {}
    excluded_methods = {'HEAD', 'OPTIONS'}
    excluded_endpoints = {'static', 'api_documentation'}
    
    for rule in app.url_map.iter_rules():
        # Skip static files and this endpoint
        if rule.endpoint in excluded_endpoints:
            continue
        
        # Get category for this route
        category = _get_category_for_route(rule.rule)
        if not category:
            continue
        
        # Initialize category if needed
        if category not in categories:
            categories[category] = {
                'description': _get_category_description(category),
                'endpoints': []
            }
        
        # Get methods (excluding HEAD, OPTIONS)
        methods = [m for m in rule.methods if m not in excluded_methods]
        
        # Get docstring from view function
        view_func = app.view_functions.get(rule.endpoint)
        description = ''
        if view_func and view_func.__doc__:
            # Get first line of docstring
            description = view_func.__doc__.strip().split('\n')[0]
        
        # Add endpoint for each method
        for method in methods:
            categories[category]['endpoints'].append({
                'method': method,
                'path': rule.rule,
                'description': description,
                'endpoint': rule.endpoint
            })
    
    # Sort endpoints within each category by path
    for cat in categories.values():
        cat['endpoints'].sort(key=lambda x: (x['path'], x['method']))
    
    # Sort categories
    category_order = ['authentication', 'user', 'explicit_context', 'chat', 
                      'domain_characters', 'personality', 'smart_response', 
                      'history', 'context', 'ai_budget', 'admin', 'developer', 'other']
    sorted_categories = {}
    for cat in category_order:
        if cat in categories:
            sorted_categories[cat] = categories[cat]
    # Add any remaining categories
    for cat in categories:
        if cat not in sorted_categories:
            sorted_categories[cat] = categories[cat]
    
    api_docs = {
        'version': '1.0 (auto-generated)',
        'base_url': request.host_url.rstrip('/'),
        'total_endpoints': sum(len(c['endpoints']) for c in categories.values()),
        'categories': sorted_categories,
        'authentication': {
            'type': 'JWT Bearer Token',
            'header': 'Authorization: Bearer <token>',
            'obtain_token': 'POST /api/auth/login with {email, password}'
        },
        'rate_limits': {
            'ai_calls_per_day': 100,
            'ai_calls_per_hour': 30,
            'messages_per_minute': 20
        }
    }
    return jsonify(api_docs)

# ============================================================
# NEW FEATURE ENDPOINTS: Monitoring, Cache, Health
# ============================================================

@app.route('/api/system/health')
def system_health():
    """Get system health status"""
    try:
        uptime = get_uptime_monitor()
        if uptime:
            health = uptime.get_health_status()
        else:
            health = {'status': 'healthy', 'checks': {}, 'uptime_formatted': 'N/A'}
        
        # Check database
        try:
            cursor = db.connection.cursor()
            cursor.execute("SELECT 1")
            health['checks']['database'] = {'status': 'healthy'}
        except:
            health['checks']['database'] = {'status': 'unhealthy'}
        
        health['new_modules_available'] = NEW_MODULES_AVAILABLE
        return jsonify(health)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/system/errors')
def system_errors():
    """Get recent system errors (admin only)"""
    try:
        limit = request.args.get('limit', 50, type=int)
        error_type = request.args.get('type')
        
        tracker = get_error_tracker()
        errors = tracker.get_recent_errors(limit, error_type)
        summary = tracker.get_error_summary()
        
        return jsonify({
            'errors': errors,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/cache')
def cache_stats():
    """Get cache statistics"""
    try:
        cache = get_cache()
        return jsonify(cache.get_stats())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the cache"""
    try:
        cache = get_cache()
        cache.clear()
        return jsonify({'status': 'success', 'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# USER ANALYTICS ENDPOINTS
# ============================================================

@app.route('/api/analytics/user/<int:user_id>')
def get_user_analytics(user_id):
    """Get analytics for a specific user"""
    try:
        from smart_response.user_analytics import create_user_analytics
        conn = integrated_db.get_connection()
        analytics = create_user_analytics(conn)
        days = request.args.get('days', 30, type=int)
        stats = analytics.get_user_stats(user_id, days)
        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/engagement')
def get_engagement_analytics():
    """Get overall engagement metrics"""
    try:
        from smart_response.user_analytics import create_user_analytics
        conn = integrated_db.get_connection()
        analytics = create_user_analytics(conn)
        days = request.args.get('days', 7, type=int)
        metrics = analytics.get_engagement_metrics(days)
        conn.close()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/conversations')
def get_conversation_analytics():
    """Get conversation pattern insights"""
    try:
        from smart_response.user_analytics import create_user_analytics
        conn = integrated_db.get_connection()
        analytics = create_user_analytics(conn)
        days = request.args.get('days', 30, type=int)
        insights = analytics.get_conversation_insights(days)
        conn.close()
        return jsonify(insights)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/hourly')
def get_hourly_analytics():
    """Get hourly activity breakdown"""
    try:
        from smart_response.user_analytics import create_user_analytics
        conn = integrated_db.get_connection()
        analytics = create_user_analytics(conn)
        days = request.args.get('days', 7, type=int)
        hourly = analytics.get_hourly_activity(days)
        conn.close()
        return jsonify(hourly)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/trends/<metric>')
def get_trend_analytics(metric):
    """Get trend data for a specific metric"""
    try:
        from smart_response.user_analytics import create_user_analytics
        conn = integrated_db.get_connection()
        analytics = create_user_analytics(conn)
        days = request.args.get('days', 30, type=int)
        trends = analytics.get_trend_data(metric, days)
        conn.close()
        return jsonify({'metric': metric, 'days': days, 'data': trends})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GITHUB WEBHOOK FOR AUTO-DEPLOYMENT (DISABLED - use deploy_anywhere.py instead)
# Uncomment to enable automatic deployment on GitHub push
# ============================================================

# @app.route('/deploy-webhook', methods=['POST'])
# def deploy_webhook():
#     """GitHub webhook endpoint for auto-deployment with database migrations"""
#     import hmac
#     import hashlib
#     import subprocess
#     
#     signature = request.headers.get('X-Hub-Signature-256')
#     if signature:
#         secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
#         if secret:
#             expected_signature = 'sha256=' + hmac.new(
#                 secret.encode(), request.data, hashlib.sha256
#             ).hexdigest()
#             if not hmac.compare_digest(signature, expected_signature):
#                 return jsonify({'error': 'Invalid signature'}), 401
#     
#     try:
#         result = subprocess.run(['git', 'pull', 'origin', 'main'],
#             cwd='/home/trabcd/ai-model-compare', capture_output=True, text=True)
#         if 'requirements.txt' in result.stdout:
#             subprocess.run(['pip', 'install', '-r', 'requirements.txt'],
#                 cwd='/home/trabcd/ai-model-compare')
#         migrate_result = subprocess.run(['python', 'migrate_all_tables.py'],
#             cwd='/home/trabcd/ai-model-compare', capture_output=True, text=True)
#         subprocess.run(['touch', '/var/www/trabcd_pythonanywhere_com_wsgi.py'])
#         return jsonify({'status': 'success', 'message': 'Deployment triggered',
#             'git_output': result.stdout,
#             'migration_output': migrate_result.stdout if migrate_result else 'skipped'}), 200
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)}), 500


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
    
    app.run(debug=True, host='0.0.0.0', port=5050)
