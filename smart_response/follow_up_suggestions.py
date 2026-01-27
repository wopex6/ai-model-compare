"""
Follow-Up Suggestions System

Generates contextual follow-up suggestions with AI responses and tracks user choices
to learn their implicit needs, goals, and preferences over time.

Key Features:
1. Generate relevant follow-up prompts based on conversation context
2. Track which suggestions users select (their "path")
3. Learn patterns from user choices to understand implicit preferences
4. Apply learned preferences to future conversations
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

DB_PATH = Path(__file__).parent.parent / 'integrated_users.db'


class FollowUpSuggestionSystem:
    """
    Generates and tracks follow-up suggestions to learn user preferences.
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create tables for tracking suggestions and user paths."""
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            
            # Track generated suggestions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS follow_up_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    message_id INTEGER,
                    character_id TEXT,
                    suggestions TEXT NOT NULL,
                    context_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Track which suggestions users clicked/selected
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suggestion_selections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    suggestion_id INTEGER,
                    selected_text TEXT NOT NULL,
                    suggestion_category TEXT,
                    character_id TEXT,
                    context_snapshot TEXT,
                    selected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (suggestion_id) REFERENCES follow_up_suggestions (id)
                )
            ''')
            
            # Learned user preferences from suggestion patterns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preference_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    preference_type TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    occurrence_count INTEGER DEFAULT 1,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, preference_type, preference_value)
                )
            ''')
            
            # Index for fast lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_suggestions_user ON follow_up_suggestions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_selections_user ON suggestion_selections(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_preferences_user ON user_preference_patterns(user_id)')
            
            self.db.commit()
        except Exception as e:
            print(f"Warning: Could not create suggestion tables: {e}")
    
    # =========================================================================
    # SUGGESTION GENERATION
    # =========================================================================
    
    def generate_suggestions(self, user_id: int, message: str, ai_response: str,
                           character_id: str, context: Dict = None) -> List[Dict[str, Any]]:
        """
        Generate contextual follow-up suggestions based on conversation.
        
        Returns list of suggestions with:
        - text: The suggestion text (what user would send)
        - category: Type of follow-up (explore, action, clarify, emotion, practical)
        - intent: What this suggestion aims to achieve
        """
        suggestions = []
        
        # Get user's learned preferences to personalize suggestions
        user_prefs = self.get_user_preferences(user_id)
        
        # Get recently used suggestions to avoid repeats
        recently_used = self._get_recently_used_suggestions(user_id, message)
        
        # Analyze conversation to determine suggestion types
        suggestion_types = self._analyze_needed_suggestions(message, ai_response, context)
        
        # Generate suggestions based on context
        domain = character_id.replace('domain_', '') if character_id else 'general'
        
        for sug_type in suggestion_types[:4]:  # Max 4 suggestions
            suggestion = self._generate_suggestion_for_type(
                sug_type, message, ai_response, domain, user_prefs, recently_used
            )
            if suggestion:
                suggestions.append(suggestion)
                # Add to recently_used to avoid duplicates within same generation
                recently_used.add(suggestion['text'].lower())
        
        # Store suggestions for tracking
        if suggestions and self.db:
            self._store_suggestions(user_id, None, character_id, suggestions, context)
        
        return suggestions
    
    def _get_recently_used_suggestions(self, user_id: int, current_message: str) -> set:
        """Get suggestions that were recently used or match the current message."""
        recently_used = set()
        
        # Always exclude the current message (in case it was a clicked suggestion)
        recently_used.add(current_message.lower().strip())
        
        # Get suggestions selected in the last 5 minutes
        if self.db:
            try:
                cursor = self.db.cursor()
                cursor.execute('''
                    SELECT selected_text FROM suggestion_selections
                    WHERE user_id = ? 
                    AND selected_at > datetime('now', '-5 minutes')
                ''', (user_id,))
                for row in cursor.fetchall():
                    if row[0]:
                        recently_used.add(row[0].lower().strip())
            except Exception:
                pass
        
        return recently_used
    
    def _analyze_needed_suggestions(self, message: str, ai_response: str, 
                                   context: Dict = None) -> List[str]:
        """Analyze what types of follow-up suggestions would be most helpful."""
        needed = []
        message_lower = message.lower()
        response_lower = ai_response.lower() if ai_response else ""
        
        # Check for exploration needs
        if any(word in message_lower for word in ['confused', 'not sure', 'don\'t know', 'maybe']):
            needed.append('clarify')
        
        # Check if user might want to go deeper
        if any(word in message_lower for word in ['feel', 'feeling', 'emotion', 'hard', 'difficult']):
            needed.append('explore_feelings')
        
        # Check if practical next steps would help
        if any(word in message_lower for word in ['how', 'what should', 'help me', 'need to']):
            needed.append('action_steps')
        
        # If AI mentioned options or choices, offer to explore them
        if any(word in response_lower for word in ['option', 'could', 'might', 'consider', 'alternatively']):
            needed.append('explore_options')
        
        # Always offer to go deeper or shift topic
        if len(needed) < 2:
            needed.append('go_deeper')
        
        if len(needed) < 3:
            needed.append('related_topic')
        
        # Add practical/action if not already there
        if 'action_steps' not in needed:
            needed.append('action_steps')
        
        return needed[:4]
    
    def _generate_suggestion_for_type(self, sug_type: str, message: str, 
                                     ai_response: str, domain: str,
                                     user_prefs: Dict, recently_used: set = None) -> Optional[Dict[str, Any]]:
        """Generate a specific suggestion based on type, excluding recently used ones."""
        if recently_used is None:
            recently_used = set()
        
        # Domain-specific suggestion templates
        templates = {
            'work': {
                'clarify': [
                    "Can you help me think through this step by step?",
                    "What questions should I be asking myself?",
                    "What am I missing here?"
                ],
                'explore_feelings': [
                    "Why does this bother me so much?",
                    "How do I usually react in situations like this?",
                    "What would make me feel better about this?"
                ],
                'action_steps': [
                    "What's the smallest step I could take right now?",
                    "What would you suggest I do first?",
                    "How do I start without feeling overwhelmed?"
                ],
                'explore_options': [
                    "Tell me more about that first option",
                    "What are the pros and cons of each?",
                    "Which would you recommend and why?"
                ],
                'go_deeper': [
                    "What's really at the root of this?",
                    "Is there a pattern here I should notice?",
                    "What would success look like?"
                ],
                'related_topic': [
                    "How does this affect my work-life balance?",
                    "Should I talk to someone about this?",
                    "What if nothing changes?"
                ]
            },
            'mental_health': {
                'clarify': [
                    "Help me understand what I'm feeling",
                    "Why do I keep feeling this way?",
                    "Is this normal?"
                ],
                'explore_feelings': [
                    "I want to explore this feeling more",
                    "What's underneath this emotion?",
                    "When did I start feeling like this?"
                ],
                'action_steps': [
                    "What can I do right now to feel better?",
                    "What's one small thing that might help?",
                    "How do I cope when this happens?"
                ],
                'explore_options': [
                    "What are some healthy ways to deal with this?",
                    "What strategies work for others?",
                    "Should I try something different?"
                ],
                'go_deeper': [
                    "What triggers these feelings?",
                    "How has this affected my life?",
                    "What am I really afraid of?"
                ],
                'related_topic': [
                    "How does this connect to my relationships?",
                    "Is this affecting other areas of my life?",
                    "Should I seek professional help?"
                ]
            },
            'relationships': {
                'clarify': [
                    "Help me see their perspective",
                    "Am I overreacting?",
                    "What am I really upset about?"
                ],
                'explore_feelings': [
                    "Why does this hurt so much?",
                    "What do I need from them?",
                    "How do I really feel about this person?"
                ],
                'action_steps': [
                    "How should I bring this up with them?",
                    "What's the best way to communicate this?",
                    "Should I give it more time?"
                ],
                'explore_options': [
                    "What are my options here?",
                    "What would happen if I did nothing?",
                    "Is this worth fighting for?"
                ],
                'go_deeper': [
                    "Is this a pattern in my relationships?",
                    "What does this say about what I need?",
                    "What would a healthy version of this look like?"
                ],
                'related_topic': [
                    "How is this affecting my mental health?",
                    "Should I set better boundaries?",
                    "How do I take care of myself through this?"
                ]
            },
            'finance': {
                'clarify': [
                    "Can you explain that in simpler terms?",
                    "What should I prioritize first?",
                    "How do I know if I'm on track?"
                ],
                'action_steps': [
                    "What's the first thing I should do?",
                    "Give me a simple action plan",
                    "What can I do this week?"
                ],
                'explore_options': [
                    "What are my options?",
                    "Which approach would you recommend?",
                    "What's the safest choice?"
                ],
                'go_deeper': [
                    "Why do I struggle with money?",
                    "What habits should I change?",
                    "How did I get here?"
                ],
                'related_topic': [
                    "How does this affect my stress levels?",
                    "Should I talk to a professional?",
                    "How do I stay motivated?"
                ]
            }
        }
        
        # Get templates for domain, fall back to general
        domain_templates = templates.get(domain, templates.get('mental_health', {}))
        type_templates = domain_templates.get(sug_type, [])
        
        if not type_templates:
            # Generic fallbacks
            fallbacks = {
                'clarify': "Can you help me understand this better?",
                'explore_feelings': "I want to explore how I feel about this",
                'action_steps': "What should I do next?",
                'explore_options': "What are my options?",
                'go_deeper': "Let's dig deeper into this",
                'related_topic': "How does this connect to other areas?"
            }
            text = fallbacks.get(sug_type, "Tell me more")
            # Check if fallback is also recently used
            if text.lower() in recently_used:
                return None  # Skip this type entirely
        else:
            # Filter out recently used suggestions before selecting
            available_templates = [t for t in type_templates if t.lower() not in recently_used]
            if not available_templates:
                return None  # All templates for this type were recently used
            # Prefer suggestions that match user preferences
            text = self._select_best_template(available_templates, user_prefs)
        
        # Final check - don't return if somehow still in recently_used
        if text.lower() in recently_used:
            return None
        
        return {
            'text': text,
            'category': sug_type,
            'intent': self._get_intent_description(sug_type)
        }
    
    def _select_best_template(self, templates: List[str], user_prefs: Dict) -> str:
        """Select the best template based on user preferences."""
        if not templates:
            return "Tell me more"
        
        # For now, simple selection - can be enhanced with preference matching
        import random
        
        # If user prefers action-oriented, prioritize action templates
        if user_prefs.get('prefers_action', False):
            action_templates = [t for t in templates if any(
                word in t.lower() for word in ['do', 'should', 'step', 'start', 'action']
            )]
            if action_templates:
                return random.choice(action_templates)
        
        # If user prefers exploration, prioritize question templates
        if user_prefs.get('prefers_exploration', False):
            explore_templates = [t for t in templates if '?' in t and any(
                word in t.lower() for word in ['why', 'what', 'how', 'feel']
            )]
            if explore_templates:
                return random.choice(explore_templates)
        
        return random.choice(templates)
    
    def _get_intent_description(self, sug_type: str) -> str:
        """Get description of what the suggestion aims to achieve."""
        intents = {
            'clarify': 'Get clarity on the situation',
            'explore_feelings': 'Understand emotions better',
            'action_steps': 'Get practical next steps',
            'explore_options': 'Consider different approaches',
            'go_deeper': 'Understand root causes',
            'related_topic': 'Explore connected areas'
        }
        return intents.get(sug_type, 'Continue the conversation')
    
    def _store_suggestions(self, user_id: int, message_id: int, character_id: str,
                          suggestions: List[Dict], context: Dict = None):
        """Store generated suggestions for tracking."""
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT INTO follow_up_suggestions 
                (user_id, message_id, character_id, suggestions, context_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, message_id, character_id,
                json.dumps(suggestions),
                context.get('adaptive_context', {}).get('implicit_needs', {}).get('primary_need') if context else None
            ))
            self.db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Warning: Could not store suggestions: {e}")
            return None
    
    # =========================================================================
    # SELECTION TRACKING
    # =========================================================================
    
    def record_selection(self, user_id: int, selected_text: str, 
                        suggestion_category: str = None, character_id: str = None,
                        context: Dict = None) -> None:
        """
        Record when a user selects a follow-up suggestion.
        This is key for learning their preferences.
        """
        if not self.db:
            return
        
        try:
            cursor = self.db.cursor()
            
            # Store the selection
            cursor.execute('''
                INSERT INTO suggestion_selections 
                (user_id, selected_text, suggestion_category, character_id, context_snapshot)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, selected_text, suggestion_category, character_id,
                json.dumps(context) if context else None
            ))
            
            # Update preference patterns based on selection
            self._update_preferences_from_selection(
                user_id, selected_text, suggestion_category, character_id
            )
            
            self.db.commit()
            print(f"[SUGGESTIONS] Recorded selection: '{selected_text[:50]}...' ({suggestion_category})")
            
        except Exception as e:
            print(f"Warning: Could not record selection: {e}")
    
    def _update_preferences_from_selection(self, user_id: int, selected_text: str,
                                          category: str, character_id: str):
        """Learn user preferences from their selection."""
        if not self.db:
            return
        
        cursor = self.db.cursor()
        
        # Track category preferences (do they prefer action vs exploration?)
        if category:
            cursor.execute('''
                INSERT INTO user_preference_patterns 
                (user_id, preference_type, preference_value, confidence, occurrence_count)
                VALUES (?, 'category_preference', ?, 0.6, 1)
                ON CONFLICT(user_id, preference_type, preference_value) DO UPDATE SET
                    occurrence_count = occurrence_count + 1,
                    confidence = MIN(0.95, confidence + 0.05),
                    last_updated = CURRENT_TIMESTAMP
            ''', (user_id, category))
        
        # Track domain engagement
        if character_id:
            domain = character_id.replace('domain_', '')
            cursor.execute('''
                INSERT INTO user_preference_patterns 
                (user_id, preference_type, preference_value, confidence, occurrence_count)
                VALUES (?, 'domain_engagement', ?, 0.6, 1)
                ON CONFLICT(user_id, preference_type, preference_value) DO UPDATE SET
                    occurrence_count = occurrence_count + 1,
                    confidence = MIN(0.95, confidence + 0.05),
                    last_updated = CURRENT_TIMESTAMP
            ''', (user_id, domain))
        
        # Detect communication style preferences from selected text
        text_lower = selected_text.lower()
        
        # Action-oriented?
        if any(word in text_lower for word in ['do', 'should', 'step', 'action', 'start', 'how']):
            cursor.execute('''
                INSERT INTO user_preference_patterns 
                (user_id, preference_type, preference_value, confidence, occurrence_count)
                VALUES (?, 'style', 'action_oriented', 0.6, 1)
                ON CONFLICT(user_id, preference_type, preference_value) DO UPDATE SET
                    occurrence_count = occurrence_count + 1,
                    confidence = MIN(0.95, confidence + 0.03),
                    last_updated = CURRENT_TIMESTAMP
            ''', (user_id,))
        
        # Exploration-oriented?
        if any(word in text_lower for word in ['why', 'feel', 'understand', 'explore', 'deeper']):
            cursor.execute('''
                INSERT INTO user_preference_patterns 
                (user_id, preference_type, preference_value, confidence, occurrence_count)
                VALUES (?, 'style', 'exploration_oriented', 0.6, 1)
                ON CONFLICT(user_id, preference_type, preference_value) DO UPDATE SET
                    occurrence_count = occurrence_count + 1,
                    confidence = MIN(0.95, confidence + 0.03),
                    last_updated = CURRENT_TIMESTAMP
            ''', (user_id,))
    
    # =========================================================================
    # PREFERENCE LEARNING
    # =========================================================================
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get learned preferences for a user based on their suggestion history.
        """
        preferences = {
            'preferred_categories': [],
            'preferred_domains': [],
            'prefers_action': False,
            'prefers_exploration': False,
            'engagement_patterns': {},
            'confidence': 0.0
        }
        
        if not self.db:
            return preferences
        
        try:
            cursor = self.db.cursor()
            
            # Get all preferences for user
            cursor.execute('''
                SELECT preference_type, preference_value, confidence, occurrence_count
                FROM user_preference_patterns
                WHERE user_id = ?
                ORDER BY occurrence_count DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            
            category_counts = {}
            domain_counts = {}
            style_counts = {}
            
            for pref_type, pref_value, confidence, count in rows:
                if pref_type == 'category_preference':
                    category_counts[pref_value] = count
                elif pref_type == 'domain_engagement':
                    domain_counts[pref_value] = count
                elif pref_type == 'style':
                    style_counts[pref_value] = count
            
            # Set preferred categories (top 3)
            if category_counts:
                sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
                preferences['preferred_categories'] = [c[0] for c in sorted_cats[:3]]
            
            # Set preferred domains (top 3)
            if domain_counts:
                sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
                preferences['preferred_domains'] = [d[0] for d in sorted_domains[:3]]
            
            # Determine action vs exploration preference
            action_count = style_counts.get('action_oriented', 0)
            explore_count = style_counts.get('exploration_oriented', 0)
            
            if action_count > explore_count * 1.5:
                preferences['prefers_action'] = True
            elif explore_count > action_count * 1.5:
                preferences['prefers_exploration'] = True
            
            # Calculate overall confidence
            total_selections = sum(category_counts.values()) if category_counts else 0
            if total_selections >= 10:
                preferences['confidence'] = min(0.9, 0.5 + (total_selections * 0.02))
            elif total_selections >= 5:
                preferences['confidence'] = 0.5 + (total_selections * 0.03)
            else:
                preferences['confidence'] = 0.3
            
        except Exception as e:
            print(f"Warning: Could not get user preferences: {e}")
        
        return preferences
    
    def get_preference_summary_for_prompt(self, user_id: int) -> str:
        """
        Get a natural language summary of user preferences for AI context.
        """
        prefs = self.get_user_preferences(user_id)
        
        if prefs['confidence'] < 0.4:
            return ""  # Not enough data yet
        
        parts = []
        
        # Communication style
        if prefs['prefers_action']:
            parts.append("This user prefers practical, action-oriented guidance. They appreciate concrete steps.")
        elif prefs['prefers_exploration']:
            parts.append("This user values emotional exploration and understanding. They appreciate being asked questions.")
        
        # Domain engagement
        if prefs['preferred_domains']:
            domains = prefs['preferred_domains'][:2]
            domain_names = [d.replace('_', ' ') for d in domains]
            parts.append(f"They most often engage with: {', '.join(domain_names)}.")
        
        # Category preferences
        if prefs['preferred_categories']:
            cats = prefs['preferred_categories'][:2]
            cat_descriptions = {
                'action_steps': 'getting practical next steps',
                'explore_feelings': 'exploring their feelings',
                'clarify': 'getting clarity',
                'go_deeper': 'understanding root causes',
                'explore_options': 'considering options'
            }
            cat_names = [cat_descriptions.get(c, c) for c in cats]
            parts.append(f"They typically want help with: {', '.join(cat_names)}.")
        
        if parts:
            return "📊 User Pattern Insights:\n" + " ".join(parts)
        
        return ""
    
    # =========================================================================
    # PATH ANALYSIS
    # =========================================================================
    
    def get_user_journey_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Analyze the user's conversation paths to understand their journey.
        """
        insights = {
            'common_starting_points': [],
            'typical_paths': [],
            'unresolved_themes': [],
            'growth_areas': []
        }
        
        if not self.db:
            return insights
        
        try:
            cursor = self.db.cursor()
            
            # Get recent selections with context
            cursor.execute('''
                SELECT suggestion_category, character_id, selected_at, context_snapshot
                FROM suggestion_selections
                WHERE user_id = ?
                ORDER BY selected_at DESC
                LIMIT 50
            ''', (user_id,))
            
            selections = cursor.fetchall()
            
            if not selections:
                return insights
            
            # Analyze category sequences
            categories = [s[0] for s in selections if s[0]]
            
            # Find common starting categories
            if len(categories) >= 5:
                first_in_sessions = categories[::5]  # Approximate session starts
                counter = Counter(first_in_sessions)
                insights['common_starting_points'] = [c[0] for c in counter.most_common(3)]
            
            # Track domains they return to
            domains = [s[1].replace('domain_', '') if s[1] else None for s in selections]
            domains = [d for d in domains if d]
            if domains:
                domain_counter = Counter(domains)
                recurring = [d for d, count in domain_counter.items() if count >= 3]
                if recurring:
                    insights['unresolved_themes'] = recurring[:3]
            
        except Exception as e:
            print(f"Warning: Could not analyze user journey: {e}")
        
        return insights


# Singleton instance
_suggestion_system = None

def get_suggestion_system(db_connection=None) -> FollowUpSuggestionSystem:
    """Get or create the suggestion system instance."""
    global _suggestion_system
    if _suggestion_system is None or db_connection is not None:
        _suggestion_system = FollowUpSuggestionSystem(db_connection)
    return _suggestion_system
