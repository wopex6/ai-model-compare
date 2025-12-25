"""
AI-Powered Context Prompts Generator

Generates intelligent, context-aware prompts using AI to:
- Reinforce previous suggestions
- Dive deeper into discussed topics
- Guide and inspire users based on conversation history
- Track feedback direction and preferences

Author: AI Life Companion Team
Date: December 2025
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3


class AIContextPromptGenerator:
    """
    Generates AI-powered context-aware prompts instead of simple template greetings.
    
    Key features:
    - Uses conversation history to create meaningful follow-ups
    - Tracks user feedback direction (positive/negative responses)
    - Remembers suggestions made and their outcomes
    - Skips bot greetings when counting meaningful exchanges
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create tables for tracking prompts and feedback"""
        cursor = self.db.cursor()
        
        # Track suggestions made to users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_suggestions_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                suggestion_type TEXT NOT NULL,
                suggestion_text TEXT NOT NULL,
                context_summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                followed_up BOOLEAN DEFAULT 0,
                user_response TEXT,
                response_sentiment TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Track user feedback patterns and preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT,
                topic TEXT NOT NULL,
                feedback_direction TEXT NOT NULL,
                feedback_strength REAL DEFAULT 0.5,
                occurrence_count INTEGER DEFAULT 1,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                UNIQUE(user_id, character_id, topic),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Track conversation themes for deeper engagement
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT,
                theme TEXT NOT NULL,
                depth_level INTEGER DEFAULT 1,
                last_explored DATETIME DEFAULT CURRENT_TIMESTAMP,
                exploration_notes TEXT,
                user_interest_score REAL DEFAULT 0.5,
                UNIQUE(user_id, character_id, theme),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_suggestions_user 
            ON ai_suggestions_tracking(user_id, created_at DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_feedback_user 
            ON user_feedback_tracking(user_id, topic)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_themes_user 
            ON conversation_themes(user_id, user_interest_score DESC)
        ''')
        
        self.db.commit()
    
    def get_meaningful_message_count(self, user_id: int, character_id: str = None, 
                                      limit: int = 20) -> Tuple[int, List[Dict]]:
        """
        Get count of MEANINGFUL messages, excluding bot greetings.
        
        Returns:
            Tuple of (count, list of meaningful messages)
        """
        cursor = self.db.cursor()
        
        # Get recent messages from ALL conversations for this user
        # (not just coordinator - user might talk to other characters)
        cursor.execute('''
            SELECT m.id, m.sender_type, m.content, m.metadata, m.timestamp
            FROM messages m
            JOIN ai_conversations c ON m.conversation_id = c.id
            WHERE c.user_id = ?
            ORDER BY m.timestamp DESC
            LIMIT ?
        ''', (user_id, limit * 2))  # Get extra to filter
        
        rows = cursor.fetchall()
        meaningful_messages = []
        
        for row in rows:
            msg_id, sender_type, content, metadata, timestamp = row
            
            # Skip automated greetings
            if metadata:
                try:
                    meta = json.loads(metadata)
                    if meta.get('is_automated_greeting'):
                        continue
                except:
                    pass
            
            # Skip very short bot responses that are likely greetings
            if sender_type == 'assistant':
                content_lower = content.lower().strip()
                # Skip generic greetings
                greeting_patterns = [
                    'hey there', 'hi there', 'hello!', 'good morning',
                    'good afternoon', 'good evening', 'welcome back',
                    'how are you', "how's it going", 'checking in',
                    'just checking', "i'm here if you need"
                ]
                is_greeting = any(content_lower.startswith(p) for p in greeting_patterns)
                if is_greeting and len(content) < 100:
                    continue
            
            meaningful_messages.append({
                'id': msg_id,
                'sender': sender_type,
                'content': content,
                'timestamp': timestamp
            })
            
            if len(meaningful_messages) >= limit:
                break
        
        return len(meaningful_messages), meaningful_messages
    
    def get_conversation_context_for_ai(self, user_id: int, character_id: str = 'coordinator') -> Dict:
        """
        Build rich context for AI prompt generation.
        Focuses on meaningful exchanges and tracked themes.
        """
        cursor = self.db.cursor()
        
        # Get meaningful message count and recent messages
        msg_count, recent_messages = self.get_meaningful_message_count(user_id, character_id, limit=15)
        
        # Get tracked themes with interest scores
        cursor.execute('''
            SELECT theme, depth_level, user_interest_score, exploration_notes
            FROM conversation_themes
            WHERE user_id = ? AND (character_id = ? OR character_id IS NULL)
            ORDER BY user_interest_score DESC, last_explored DESC
            LIMIT 5
        ''', (user_id, character_id))
        
        themes = [{'theme': r[0], 'depth': r[1], 'interest': r[2], 'notes': r[3]} 
                  for r in cursor.fetchall()]
        
        # Get user feedback patterns
        cursor.execute('''
            SELECT topic, feedback_direction, feedback_strength
            FROM user_feedback_tracking
            WHERE user_id = ? AND (character_id = ? OR character_id IS NULL)
            ORDER BY last_updated DESC
            LIMIT 10
        ''', (user_id, character_id))
        
        feedback_patterns = [{'topic': r[0], 'direction': r[1], 'strength': r[2]} 
                            for r in cursor.fetchall()]
        
        # Get recent suggestions made
        cursor.execute('''
            SELECT suggestion_type, suggestion_text, followed_up, response_sentiment
            FROM ai_suggestions_tracking
            WHERE user_id = ? AND (character_id = ? OR character_id IS NULL)
            ORDER BY created_at DESC
            LIMIT 5
        ''', (user_id, character_id))
        
        recent_suggestions = [{'type': r[0], 'text': r[1], 'followed_up': r[2], 'sentiment': r[3]} 
                             for r in cursor.fetchall()]
        
        # Extract key topics from recent messages
        user_messages = [m['content'] for m in recent_messages if m['sender'] == 'user']
        
        return {
            'meaningful_exchange_count': msg_count,
            'recent_user_messages': user_messages[:5],
            'themes': themes,
            'feedback_patterns': feedback_patterns,
            'recent_suggestions': recent_suggestions,
            'has_sufficient_context': msg_count >= 5
        }
    
    def build_ai_prompt_request(self, user_id: int, user_name: str, 
                                 character_id: str = 'coordinator') -> Dict:
        """
        Build the request to send to AI for generating a context-aware prompt.
        
        Returns a dict with:
        - system_prompt: Instructions for the AI
        - context: User conversation context
        - should_use_ai: Whether we have enough context for AI
        """
        context = self.get_conversation_context_for_ai(user_id, character_id)
        
        # If not enough meaningful exchanges, don't use AI (save budget)
        # Threshold: 3 meaningful exchanges (lowered from 5 for better responsiveness)
        min_exchanges = 3
        if context['meaningful_exchange_count'] < min_exchanges:
            return {
                'should_use_ai': False,
                'reason': f'Need {min_exchanges}+ meaningful exchanges (have {context["meaningful_exchange_count"]})',
                'fallback_type': 'simple_greeting'
            }
        
        # Build system prompt for AI
        system_prompt = f"""You are generating a thoughtful, context-aware follow-up message for {user_name}.

Your goal is to create a message that:
1. References something specific from their recent conversations
2. Reinforces or follows up on any suggestions previously made
3. Shows genuine interest in their progress or thoughts
4. Gently guides them toward constructive action or reflection
5. Is warm but not overly effusive

DO NOT:
- Use generic greetings like "How are you?" or "Hope you're doing well"
- Be vague or generic
- Make up topics not mentioned in the context
- Be pushy or demanding

The message should be 1-3 sentences, conversational, and specific to their context.
"""
        
        # Build context string
        context_parts = []
        
        if context['recent_user_messages']:
            context_parts.append("RECENT TOPICS FROM USER:")
            for i, msg in enumerate(context['recent_user_messages'][:3], 1):
                # Truncate long messages
                snippet = msg[:150] + '...' if len(msg) > 150 else msg
                context_parts.append(f"  {i}. {snippet}")
        
        if context['themes']:
            context_parts.append("\nTHEMES THEY'RE INTERESTED IN:")
            for t in context['themes'][:3]:
                interest = "high" if t['interest'] > 0.7 else "moderate" if t['interest'] > 0.4 else "exploring"
                context_parts.append(f"  - {t['theme']} (interest: {interest}, depth: {t['depth']})")
        
        if context['feedback_patterns']:
            context_parts.append("\nFEEDBACK PATTERNS:")
            for f in context['feedback_patterns'][:3]:
                context_parts.append(f"  - {f['topic']}: {f['direction']} ({f['strength']:.0%} strength)")
        
        if context['recent_suggestions']:
            unfollowed = [s for s in context['recent_suggestions'] if not s['followed_up']]
            if unfollowed:
                context_parts.append("\nPREVIOUS SUGGESTIONS NOT YET FOLLOWED UP:")
                for s in unfollowed[:2]:
                    context_parts.append(f"  - {s['text'][:100]}...")
        
        return {
            'should_use_ai': True,
            'system_prompt': system_prompt,
            'context': '\n'.join(context_parts),
            'user_name': user_name,
            'meaningful_exchanges': context['meaningful_exchange_count']
        }
    
    def track_suggestion(self, user_id: int, character_id: str, 
                         suggestion_type: str, suggestion_text: str,
                         context_summary: str = None):
        """Track a suggestion made to the user for future follow-up"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO ai_suggestions_tracking 
            (user_id, character_id, suggestion_type, suggestion_text, context_summary)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, character_id, suggestion_type, suggestion_text, context_summary))
        self.db.commit()
    
    def update_suggestion_response(self, user_id: int, suggestion_id: int,
                                    user_response: str, sentiment: str):
        """Update a suggestion with user's response and sentiment"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE ai_suggestions_tracking
            SET followed_up = 1, user_response = ?, response_sentiment = ?
            WHERE id = ? AND user_id = ?
        ''', (user_response, sentiment, suggestion_id, user_id))
        self.db.commit()
    
    def track_feedback(self, user_id: int, character_id: str, topic: str,
                       direction: str, strength: float = 0.5, notes: str = None):
        """
        Track user feedback direction on a topic.
        
        Args:
            direction: 'positive', 'negative', 'interested', 'disengaged'
            strength: 0.0 to 1.0 indicating how strong the signal
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO user_feedback_tracking 
            (user_id, character_id, topic, feedback_direction, feedback_strength, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, character_id, topic) DO UPDATE SET
                feedback_direction = ?,
                feedback_strength = (feedback_strength + ?) / 2,
                occurrence_count = occurrence_count + 1,
                last_updated = CURRENT_TIMESTAMP,
                notes = COALESCE(?, notes)
        ''', (user_id, character_id, topic, direction, strength, notes,
              direction, strength, notes))
        self.db.commit()
    
    def update_theme(self, user_id: int, character_id: str, theme: str,
                     interest_delta: float = 0.1, notes: str = None):
        """
        Update or create a conversation theme with interest tracking.
        
        Args:
            interest_delta: Positive to increase interest, negative to decrease
        """
        cursor = self.db.cursor()
        
        # Check if theme exists
        cursor.execute('''
            SELECT id, depth_level, user_interest_score 
            FROM conversation_themes
            WHERE user_id = ? AND character_id = ? AND theme = ?
        ''', (user_id, character_id, theme))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing
            new_interest = max(0.0, min(1.0, row[2] + interest_delta))
            new_depth = row[1] + 1 if interest_delta > 0 else row[1]
            cursor.execute('''
                UPDATE conversation_themes
                SET depth_level = ?, user_interest_score = ?, 
                    last_explored = CURRENT_TIMESTAMP,
                    exploration_notes = COALESCE(?, exploration_notes)
                WHERE id = ?
            ''', (new_depth, new_interest, notes, row[0]))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO conversation_themes 
                (user_id, character_id, theme, user_interest_score, exploration_notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, character_id, theme, 0.5 + interest_delta, notes))
        
        self.db.commit()
    
    def analyze_user_response_sentiment(self, response: str) -> str:
        """
        Simple sentiment analysis of user response.
        Returns: 'positive', 'negative', 'neutral', 'engaged', 'disengaged'
        """
        response_lower = response.lower().strip()
        
        # Check for engagement signals
        engagement_signals = ['yes', 'sure', 'definitely', 'absolutely', 'great idea',
                             'good point', 'interesting', "i'll try", 'makes sense',
                             'thank you', 'thanks', 'helpful', 'exactly', 'right']
        
        disengagement_signals = ['no', 'not really', 'maybe later', "don't want",
                                'not interested', 'stop', 'enough', 'whatever',
                                'ok', 'okay', 'fine', 'sure whatever']
        
        positive_signals = ['love', 'great', 'amazing', 'wonderful', 'excited',
                          'happy', 'glad', 'perfect', 'awesome']
        
        negative_signals = ['hate', 'terrible', 'awful', 'frustrated', 'annoyed',
                          'angry', 'sad', 'disappointed', 'wrong']
        
        # Count signals
        engaged = sum(1 for s in engagement_signals if s in response_lower)
        disengaged = sum(1 for s in disengagement_signals if s in response_lower)
        positive = sum(1 for s in positive_signals if s in response_lower)
        negative = sum(1 for s in negative_signals if s in response_lower)
        
        # Determine sentiment
        if positive > negative and engaged > disengaged:
            return 'positive'
        elif negative > positive:
            return 'negative'
        elif engaged > disengaged:
            return 'engaged'
        elif disengaged > engaged:
            return 'disengaged'
        else:
            return 'neutral'
    
    def get_user_preferences_summary(self, user_id: int) -> Dict:
        """Get summary of user's tracked preferences and feedback patterns"""
        cursor = self.db.cursor()
        
        # Get positive topics
        cursor.execute('''
            SELECT topic, feedback_strength
            FROM user_feedback_tracking
            WHERE user_id = ? AND feedback_direction IN ('positive', 'interested')
            ORDER BY feedback_strength DESC
            LIMIT 5
        ''', (user_id,))
        positive_topics = [{'topic': r[0], 'strength': r[1]} for r in cursor.fetchall()]
        
        # Get topics to avoid
        cursor.execute('''
            SELECT topic, feedback_strength
            FROM user_feedback_tracking
            WHERE user_id = ? AND feedback_direction IN ('negative', 'disengaged')
            ORDER BY feedback_strength DESC
            LIMIT 5
        ''', (user_id,))
        avoid_topics = [{'topic': r[0], 'strength': r[1]} for r in cursor.fetchall()]
        
        # Get high-interest themes
        cursor.execute('''
            SELECT theme, user_interest_score, depth_level
            FROM conversation_themes
            WHERE user_id = ? AND user_interest_score > 0.6
            ORDER BY user_interest_score DESC
            LIMIT 5
        ''', (user_id,))
        high_interest = [{'theme': r[0], 'interest': r[1], 'depth': r[2]} 
                        for r in cursor.fetchall()]
        
        return {
            'positive_topics': positive_topics,
            'topics_to_avoid': avoid_topics,
            'high_interest_themes': high_interest
        }
