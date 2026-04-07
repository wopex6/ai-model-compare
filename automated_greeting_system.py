"""
Automated Greeting System for AI Life Companion

Generates personalized greeting messages for users based on:
- User role (e.g., Developer)
- Time of day (daily greetings at preferred time)
- Inactivity period (e.g., 10 minutes for development)
- Recent conversation context
- Varied message templates to avoid repetition
- AI-powered context-aware prompts (reinforces suggestions, dives deeper)

Author: AI Life Companion Team
Date: December 2025
"""

import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from integrated_database import IntegratedDatabase


class AutomatedGreetingSystem:
    """
    Manages automated greetings for users based on activity patterns and preferences.
    
    Now enhanced with AI-powered context prompts that:
    - Reinforce previous suggestions
    - Dive deeper into discussed topics
    - Track user feedback direction and preferences
    - Skip bot greetings when counting meaningful exchanges
    """
    
    def __init__(self, db: IntegratedDatabase, ai_call_func: Callable = None):
        self.db = db
        self.ai_call_func = ai_call_func  # Function to call AI (injected to avoid circular imports)
        self._context_prompt_generator = None
        
        # Greeting templates for variety
        self.daily_greeting_templates = [
            "Good {time_of_day}, {name}! 👋 Ready to continue where we left off?",
            "Hey {name}! 🌟 Hope you're having a great {time_of_day}. What's on your mind today?",
            "Welcome back, {name}! ☀️ I've been thinking about our last conversation...",
            "{time_of_day}, {name}! 💡 Excited to help you with your projects today.",
            "Hi {name}! 🚀 Let's make today productive. What would you like to work on?",
            "Hello {name}! ✨ I'm here whenever you need me. What's your focus today?",
            "Hey there, {name}! 🎯 Ready to tackle some challenges together?",
            "Good {time_of_day}! 🌈 What exciting things are you working on, {name}?",
        ]
        
        self.inactivity_greeting_templates = [
            "Hey {name}, still there? 🤔 I'm here if you need anything!",
            "Just checking in, {name}! 👋 Need any help with what you were working on?",
            "{name}, I noticed you've been quiet. Everything okay? I'm here to help! 💬",
            "Hi {name}! 🌟 If you need a break, that's totally fine. I'll be here when you're ready!",
            "Checking in, {name}! 🔔 Let me know if you'd like to continue our conversation.",
            "Hey {name}! 💭 Take your time. I'm here whenever you need assistance.",
            "Still working on that, {name}? 🛠️ I'm ready to help if you need it!",
            "{name}, just a friendly nudge! 😊 I'm here if you want to continue.",
        ]
        
        self.context_follow_up_templates = [
            "About {topic} - have you made any progress? I'd love to hear how it's going! 🎯",
            "I was thinking about {topic}... Want to dive deeper into that? 🤓",
            "Remember we were discussing {topic}? Any updates or questions? 📝",
            "How's {topic} coming along? I'm curious to know! 💡",
            "Still working on {topic}? Let me know if you need any guidance! 🚀",
            "Any breakthroughs with {topic}? I'm here to help! ✨",
        ]
    
    @property
    def context_prompt_generator(self):
        """Lazy-load the context prompt generator"""
        if self._context_prompt_generator is None:
            try:
                from smart_response.ai_context_prompts import AIContextPromptGenerator
                conn = self.db.get_connection()
                self._context_prompt_generator = AIContextPromptGenerator(conn)
            except Exception as e:
                print(f"Warning: Could not initialize AIContextPromptGenerator: {e}")
        return self._context_prompt_generator
    
    def get_time_of_day(self, hour: int = None) -> str:
        """Get time of day greeting based on hour"""
        if hour is None:
            hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def get_user_first_name(self, user_id: int) -> str:
        """Get user's first name only (not full name)"""
        profile = self.db.get_user_profile(user_id)
        if profile and profile.get('first_name'):
            # Extract just the first name (first word) from full name
            full_name = profile['first_name']
            first_name = full_name.split()[0] if full_name else None
            if first_name:
                return first_name
        
        # Fallback to username (first word only)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0].split()[0]  # First word of username
        return "there"
    
    def get_recent_conversation_context(self, user_id: int, character_id: str = 'coordinator') -> Optional[str]:
        """Extract meaningful topic from recent conversation for context-aware greetings"""
        try:
            history = self.db.get_character_messages(user_id, character_id, limit=10)
            
            if not history:
                return None
            
            # Look for user messages to extract topics (most recent first)
            for msg in reversed(history):
                if msg.get('user_message'):
                    text = msg['user_message'].strip()
                    
                    # Skip very short messages (greetings like "hi", "hello")
                    if len(text) < 15:
                        continue
                    
                    # Skip automated greeting responses
                    if text.lower() in ['hi', 'hello', 'hey', 'thanks', 'thank you', 'ok', 'okay']:
                        continue
                    
                    # Extract meaningful topic - first sentence up to 60 chars
                    # Remove leading question words for cleaner topic
                    topic = text.split('.')[0].split('?')[0]
                    topic = topic[:60].strip()
                    
                    # Clean up the topic for natural reading
                    if topic.lower().startswith(('what ', 'how ', 'why ', 'can ', 'do ', 'is ', 'are ')):
                        # Keep the question as-is for context
                        pass
                    
                    if len(topic) >= 15:
                        return topic
            
            return None
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            return None
    
    def generate_daily_greeting(self, user_id: int) -> str:
        """Generate a varied daily greeting message"""
        name = self.get_user_first_name(user_id)
        time_of_day = self.get_time_of_day()
        
        # Select random template
        template = random.choice(self.daily_greeting_templates)
        greeting = template.format(name=name, time_of_day=time_of_day)
        
        # 40% chance to add context follow-up
        if random.random() < 0.4:
            context = self.get_recent_conversation_context(user_id)
            if context:
                follow_up_template = random.choice(self.context_follow_up_templates)
                follow_up = follow_up_template.format(topic=context)
                greeting += f"\n\n{follow_up}"
        
        return greeting
    
    def generate_inactivity_greeting(self, user_id: int, use_ai: bool = True) -> str:
        """Generate a context-aware inactivity check-in message.
        
        Now enhanced with AI-powered prompts that:
        - Reinforce previous suggestions
        - Dive deeper into discussed topics
        - Track user feedback and preferences
        
        Args:
            user_id: User ID
            use_ai: Whether to try AI-generated prompt (respects budget)
        """
        name = self.get_user_first_name(user_id)
        
        # Try AI-powered context prompt first (if enabled and has sufficient history)
        if use_ai and self.ai_call_func and self.context_prompt_generator:
            ai_prompt = self.generate_ai_context_prompt(user_id, name)
            if ai_prompt:
                return ai_prompt
        
        # Fallback: Template-based context-aware greeting
        context = self.get_recent_conversation_context(user_id)
        
        if context:
            # Context available - generate context-aware question
            context_templates = [
                "Hi {name}! 👋 I was thinking about what you mentioned regarding {topic}. How's that going?",
                "Hey {name}! 💭 Still working on {topic}? I'd love to hear how it's progressing.",
                "{name}, I remember you were exploring {topic}. Any updates or new thoughts on that?",
                "Hi {name}! 🤔 Last time we talked about {topic}. Would you like to continue that discussion?",
                "Hey {name}! Just checking in. 💬 Have you made any progress on {topic}?",
                "{name}, still thinking about {topic}? I'm here if you want to dive deeper into it.",
            ]
            template = random.choice(context_templates)
            return template.format(name=name, topic=context)
        else:
            # No context available - use general greeting
            template = random.choice(self.inactivity_greeting_templates)
            return template.format(name=name)
    
    def generate_ai_context_prompt(self, user_id: int, user_name: str, 
                                    character_id: str = 'coordinator') -> Optional[str]:
        """
        Generate an AI-powered context-aware prompt.
        
        This uses AI to create meaningful follow-ups that:
        - Reference specific topics from conversation history
        - Reinforce or follow up on previous suggestions
        - Guide users toward constructive action
        
        Returns None if AI should not be used (insufficient context, budget, etc.)
        """
        if not self.context_prompt_generator or not self.ai_call_func:
            return None
        
        try:
            # Build the prompt request
            request = self.context_prompt_generator.build_ai_prompt_request(
                user_id, user_name, character_id
            )
            
            if not request.get('should_use_ai'):
                print(f"⏭️ Skipping AI prompt: {request.get('reason', 'unknown')}")
                return None
            
            # Get goal coaching context if available
            goal_context = ""
            try:
                from goal_coaching_system import create_goal_coaching_system
                goal_system = create_goal_coaching_system(self.db, self.ai_call_func)
                goal = goal_system.get_or_create_active_goal(user_id)
                if goal:
                    goal_context = f"""
ACTIVE GOAL: {goal.title}
Phase: {goal.strategy_phase} | Progress: {goal.progress_percentage:.0f}%
Next focus: {goal.next_action or 'Continue working toward goal'}

IMPORTANT: Your follow-up should help the user make progress on their goal.
Ask about their goal progress or provide actionable guidance."""
            except Exception as e:
                print(f"[COACHING] Could not get goal context: {e}")
            
            # Call AI to generate the prompt
            enhanced_context = f"{request['context']}\n{goal_context}" if goal_context else request['context']
            ai_response = self.ai_call_func(
                system_prompt=request['system_prompt'],
                user_message=f"Generate a follow-up message for {user_name}.\n\n{enhanced_context}",
                purpose='context_prompt_generation',
                character='coordinator'
            )
            
            if ai_response and ai_response.get('success'):
                generated_prompt = ai_response.get('response', '').strip()
                
                # Track the suggestion for future follow-up
                if generated_prompt and len(generated_prompt) > 10:
                    self.context_prompt_generator.track_suggestion(
                        user_id=user_id,
                        character_id=character_id,
                        suggestion_type='ai_context_prompt',
                        suggestion_text=generated_prompt,
                        context_summary=f"Generated after {request.get('meaningful_exchanges', 0)} meaningful exchanges"
                    )
                    
                    print(f"✅ AI generated context prompt for user {user_id}")
                    return generated_prompt
            
            return None
            
        except Exception as e:
            print(f"❌ Error generating AI context prompt: {e}")
            return None
    
    def process_user_response_feedback(self, user_id: int, character_id: str,
                                        user_message: str, previous_prompt: str = None):
        """
        Analyze user's response to track feedback direction and preferences.
        
        Called after user responds to a greeting/prompt to:
        - Track engagement level
        - Update topic interest scores
        - Learn user preferences
        """
        if not self.context_prompt_generator:
            return
        
        try:
            # Analyze sentiment
            sentiment = self.context_prompt_generator.analyze_user_response_sentiment(user_message)
            
            # Extract topics from the response
            topics = self._extract_topics_from_message(user_message)
            
            # Track feedback for each topic
            for topic in topics:
                direction = 'interested' if sentiment in ['positive', 'engaged'] else \
                           'disengaged' if sentiment in ['negative', 'disengaged'] else 'neutral'
                strength = 0.7 if sentiment in ['positive', 'negative'] else 0.5
                
                self.context_prompt_generator.track_feedback(
                    user_id=user_id,
                    character_id=character_id,
                    topic=topic,
                    direction=direction,
                    strength=strength
                )
                
                # Update theme interest
                interest_delta = 0.1 if direction == 'interested' else \
                                -0.1 if direction == 'disengaged' else 0
                self.context_prompt_generator.update_theme(
                    user_id=user_id,
                    character_id=character_id,
                    theme=topic,
                    interest_delta=interest_delta
                )
            
            print(f"📊 Tracked feedback for user {user_id}: {sentiment}, topics: {topics}")
            
        except Exception as e:
            print(f"Warning: Error processing user feedback: {e}")
    
    def _extract_topics_from_message(self, message: str) -> List[str]:
        """Extract topic keywords from a message"""
        topic_keywords = {
            'goals': ['goal', 'target', 'objective', 'aim', 'achieve'],
            'motivation': ['motivat', 'inspire', 'energy', 'drive', 'momentum'],
            'challenges': ['challenge', 'difficulty', 'problem', 'struggle', 'obstacle'],
            'progress': ['progress', 'improvement', 'better', 'growing', 'advancing'],
            'emotions': ['feel', 'emotion', 'mood', 'anxious', 'happy', 'sad', 'stressed'],
            'relationships': ['relationship', 'friend', 'family', 'partner', 'colleague'],
            'work': ['work', 'job', 'career', 'profession', 'project', 'business'],
            'health': ['health', 'fitness', 'exercise', 'diet', 'sleep', 'energy'],
            'mindfulness': ['meditation', 'mindful', 'peace', 'zen', 'calm', 'breathing'],
            'learning': ['learn', 'study', 'skill', 'knowledge', 'understand', 'grow'],
            'decisions': ['decide', 'choice', 'option', 'uncertain', 'direction'],
            'time': ['time', 'schedule', 'busy', 'priority', 'balance'],
        }
        
        message_lower = message.lower()
        detected = []
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected.append(topic)
                    break
        
        return list(set(detected))
    
    def update_user_activity(self, user_id: int, activity_type: str = 'message_sent', metadata: dict = None):
        """Track user activity for inactivity detection"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_activity_log (user_id, activity_type, last_activity_at, metadata)
                VALUES (?, ?, ?, ?)
            ''', (user_id, activity_type, datetime.now(), json.dumps(metadata or {})))
            
            conn.commit()
        except Exception as e:
            print(f"Error updating user activity: {e}")
        finally:
            conn.close()
    
    def get_last_activity_time(self, user_id: int) -> Optional[datetime]:
        """Get user's last activity timestamp"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_activity_at 
            FROM user_activity_log 
            WHERE user_id = ? 
            ORDER BY last_activity_at DESC 
            LIMIT 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return datetime.fromisoformat(result[0])
        return None
    
    def has_user_been_inactive_for_days(self, user_id: int, days: int = 5) -> bool:
        """
        Check if user has been inactive (no messages sent) for specified number of days.
        Used to prevent greeting spam when users don't respond.
        
        Returns True if user hasn't sent any messages in the last N days.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check for any user messages in the last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM user_activity_log 
            WHERE user_id = ? 
            AND activity_type = 'message_sent'
            AND last_activity_at > ?
        ''', (user_id, cutoff_date))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        # If count is 0, user has been inactive for N+ days
        return count == 0
    
    def get_greeting_preferences(self, user_id: int) -> Dict:
        """Get user's greeting preferences, create default if not exists"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT enabled, preferred_time_hour, inactivity_minutes, 
                   last_daily_greeting, last_inactivity_greeting
            FROM user_greeting_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            # Create default preferences
            cursor.execute('''
                INSERT INTO user_greeting_preferences 
                (user_id, enabled, preferred_time_hour, inactivity_minutes)
                VALUES (?, 1, 9, 10)
            ''', (user_id,))
            conn.commit()
            result = (1, 9, 10, None, None)
        
        conn.close()
        
        return {
            'enabled': bool(result[0]),
            'preferred_time_hour': result[1],
            'inactivity_minutes': result[2],
            'last_daily_greeting': datetime.fromisoformat(result[3]) if result[3] else None,
            'last_inactivity_greeting': datetime.fromisoformat(result[4]) if result[4] else None
        }
    
    def should_send_daily_greeting(self, user_id: int, user_role: str) -> bool:
        """
        Check if daily greeting should be sent based on role and time.
        
        Rules:
        - Only send if user has NOT been active before preferred_time_hour today
        - Skip if user already sent messages before preferred time (they're already active)
        - Don't send if user hasn't responded in 5+ days (avoid spam)
        """
        # Only for specific roles (configurable, not hardcoded)
        eligible_roles = ['developer', 'administrator', 'master']
        if user_role.lower() not in eligible_roles:
            return False
        
        prefs = self.get_greeting_preferences(user_id)
        if not prefs['enabled']:
            return False
        
        # Check if already sent today
        if prefs['last_daily_greeting']:
            if prefs['last_daily_greeting'].date() == datetime.now().date():
                return False
        
        # Check if current hour matches preferred time (±1 hour window)
        current_hour = datetime.now().hour
        preferred_hour = prefs['preferred_time_hour']
        if abs(current_hour - preferred_hour) > 1:
            return False
        
        # Check if user has been active before preferred time today
        # If they have, skip the greeting (they're already active)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        preferred_time_today = today_start.replace(hour=preferred_hour)
        
        last_activity = self.get_last_activity_time(user_id)
        if last_activity and last_activity > preferred_time_today:
            print(f"⏭️ Skipping daily greeting for user {user_id} - already active before {preferred_hour}:00")
            return False
        
        # Check if user hasn't responded in 5+ days
        # If they haven't, stop sending greetings to avoid spam
        if self.has_user_been_inactive_for_days(user_id, days=5):
            print(f"⏭️ Skipping daily greeting for user {user_id} - no response in 5+ days")
            return False
        
        return True
    
    def should_send_inactivity_greeting(self, user_id: int, user_role: str) -> bool:
        """Check if inactivity greeting should be sent"""
        # Only for specific roles
        eligible_roles = ['developer', 'administrator', 'master']
        if user_role.lower() not in eligible_roles:
            return False
        
        prefs = self.get_greeting_preferences(user_id)
        if not prefs['enabled']:
            return False
        
        last_activity = self.get_last_activity_time(user_id)
        if not last_activity:
            return False
        
        # Check if inactive for specified duration
        inactive_duration = datetime.now() - last_activity
        if inactive_duration.total_seconds() / 60 >= prefs['inactivity_minutes']:
            # Check if we haven't sent inactivity greeting recently (within last hour)
            if prefs['last_inactivity_greeting']:
                since_last_greeting = datetime.now() - prefs['last_inactivity_greeting']
                if since_last_greeting.total_seconds() < 3600:  # 1 hour
                    return False
            return True
        
        return False
    
    def send_greeting(self, user_id: int, greeting_type: str, message: str, triggered_by: str = None, context_data: dict = None) -> bool:
        """Save greeting to database, conversation history, and update last sent timestamp"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Save greeting to automated_greetings table (for tracking)
            cursor.execute('''
                INSERT INTO automated_greetings 
                (user_id, greeting_type, greeting_message, triggered_by, context_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, greeting_type, message, triggered_by, json.dumps(context_data or {})))
            
            # Also save to messages table so it appears in conversation history after refresh
            # First, get or create the coordinator conversation for this user
            cursor.execute('''
                SELECT id FROM ai_conversations 
                WHERE user_id = ? AND character_id = 'coordinator'
                ORDER BY updated_at DESC LIMIT 1
            ''', (user_id,))
            conv_result = cursor.fetchone()
            
            if conv_result:
                conversation_id = conv_result[0]
            else:
                # Create a new conversation for coordinator
                cursor.execute('''
                    INSERT INTO ai_conversations (user_id, session_id, title, character_id, created_at, updated_at)
                    VALUES (?, ?, ?, 'coordinator', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, f'coordinator_{user_id}', 'Coordinator Chat'))
                conversation_id = cursor.lastrowid
            
            # Insert the greeting as an assistant message in the messages table
            greeting_metadata = json.dumps({
                'greeting_type': greeting_type,
                'triggered_by': triggered_by,
                'is_automated_greeting': True
            })
            cursor.execute('''
                INSERT INTO messages (conversation_id, sender_type, content, metadata, timestamp)
                VALUES (?, 'assistant', ?, ?, CURRENT_TIMESTAMP)
            ''', (conversation_id, message, greeting_metadata))
            
            # Update the conversation's updated_at timestamp
            cursor.execute('''
                UPDATE ai_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (conversation_id,))
            
            # Update last sent timestamp in preferences
            if greeting_type == 'daily':
                cursor.execute('''
                    UPDATE user_greeting_preferences 
                    SET last_daily_greeting = ? 
                    WHERE user_id = ?
                ''', (datetime.now(), user_id))
            elif greeting_type == 'inactivity':
                cursor.execute('''
                    UPDATE user_greeting_preferences 
                    SET last_inactivity_greeting = ? 
                    WHERE user_id = ?
                ''', (datetime.now(), user_id))
            
            conn.commit()
            print(f"✅ Greeting saved to conversation history for user {user_id}")
            return True
        except Exception as e:
            print(f"Error sending greeting: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            conn.close()
    
    def check_and_send_greetings(self, user_id: int) -> List[Dict]:
        """Check if any greetings should be sent and send them"""
        sent_greetings = []
        user_role = self.db.get_user_role(user_id)
        
        # Check daily greeting
        if self.should_send_daily_greeting(user_id, user_role):
            message = self.generate_daily_greeting(user_id)
            if self.send_greeting(user_id, 'daily', message, triggered_by='scheduled_time'):
                sent_greetings.append({
                    'type': 'daily',
                    'message': message,
                    'sent_at': datetime.now().isoformat()
                })
        
        # Check inactivity greeting
        if self.should_send_inactivity_greeting(user_id, user_role):
            message = self.generate_inactivity_greeting(user_id)
            if self.send_greeting(user_id, 'inactivity', message, triggered_by='inactivity_timeout'):
                sent_greetings.append({
                    'type': 'inactivity',
                    'message': message,
                    'sent_at': datetime.now().isoformat()
                })
        
        return sent_greetings
    
    def get_pending_greetings(self, user_id: int, since: datetime = None) -> List[Dict]:
        """Get greetings that haven't been displayed yet"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if since:
            cursor.execute('''
                SELECT id, greeting_type, greeting_message, sent_at, triggered_by
                FROM automated_greetings
                WHERE user_id = ? AND sent_at > ?
                ORDER BY sent_at DESC
            ''', (user_id, since))
        else:
            # Get greetings from last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute('''
                SELECT id, greeting_type, greeting_message, sent_at, triggered_by
                FROM automated_greetings
                WHERE user_id = ? AND sent_at > ?
                ORDER BY sent_at DESC
            ''', (user_id, yesterday))
        
        rows = cursor.fetchall()
        conn.close()
        
        greetings = []
        for row in rows:
            greetings.append({
                'id': row[0],
                'type': row[1],
                'message': row[2],
                'sent_at': row[3],
                'triggered_by': row[4]
            })
        
        return greetings
    
    def cleanup_old_greetings(self, days_to_keep: int = 7) -> int:
        """
        Clean up old non-context greetings from both tracking table and messages.
        Keeps greetings from the last N days and any context-related greetings.
        Returns number of deleted greetings.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        deleted_count = 0
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            # Delete old greetings from automated_greetings tracking table
            # Keep context-related greetings (triggered_by contains 'context' or 'ai_prompt')
            cursor.execute('''
                DELETE FROM automated_greetings 
                WHERE sent_at < ? 
                AND (triggered_by IS NULL OR (triggered_by NOT LIKE '%context%' AND triggered_by NOT LIKE '%ai_prompt%'))
            ''', (cutoff_date,))
            deleted_count = cursor.rowcount
            
            # Delete old automated greeting messages from messages table
            # These are identified by metadata containing 'is_automated_greeting': true
            cursor.execute('''
                DELETE FROM messages 
                WHERE timestamp < ?
                AND metadata LIKE '%"is_automated_greeting": true%'
                AND metadata NOT LIKE '%"is_context_prompt": true%'
            ''', (cutoff_date,))
            deleted_count += cursor.rowcount
            
            conn.commit()
            print(f"🧹 Cleaned up {deleted_count} old non-context greetings (older than {days_to_keep} days)")
            
        except Exception as e:
            print(f"❌ Error cleaning up old greetings: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return deleted_count
