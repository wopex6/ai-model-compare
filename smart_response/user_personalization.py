"""
User Personalization System

Stores and manages per-user adjustable parameters that adapt over time.
Every person has different:
- Character/personality preferences
- Interests and background
- Goals and aspirations
- Communication styles
- Habits and routines
- Temporary emotions, desires, and needs

This system provides:
1. Default parameters as starting points
2. Per-user parameter storage
3. Adaptive learning from interactions
4. Extensible design for future parameters

Author: AI Life Companion Team
Date: December 2025
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3


# ==================== DEFAULT PARAMETERS ====================
# These are the starting points - adjusted per-user over time

DEFAULT_USER_PARAMETERS = {
    # Character routing thresholds (0.0 to 1.0)
    "routing": {
        "coordinator_threshold": 0.1,
        "domain_mental_health_threshold": 0.25,
        "domain_finance_threshold": 0.25,
        "domain_relationships_threshold": 0.25,
        "domain_career_threshold": 0.25,
        "domain_creativity_threshold": 0.25,
        "domain_learning_threshold": 0.25,
        "domain_physical_health_threshold": 0.25,
    },
    
    # Communication style preferences
    "communication": {
        "preferred_tone": "warm",  # warm, professional, casual, direct
        "emoji_preference": "moderate",  # none, minimal, moderate, frequent
        "response_length": "medium",  # brief, medium, detailed
        "formality_level": 0.5,  # 0.0 (very casual) to 1.0 (very formal)
        "encouragement_level": 0.7,  # How much positive reinforcement
        "directness_level": 0.5,  # 0.0 (gentle hints) to 1.0 (very direct)
    },
    
    # Engagement preferences
    "engagement": {
        "proactive_prompts_enabled": True,
        "prompt_frequency_hours": 24,  # How often to send prompts
        "inactivity_check_minutes": 5,  # When to send inactivity messages
        "follow_up_enabled": True,  # Follow up on previous suggestions
        "theme_based_prompts": True,  # Use extracted themes for prompts
    },
    
    # Content preferences
    "content": {
        "preferred_topics": [],  # Auto-populated from themes
        "avoided_topics": [],  # Topics user doesn't want to discuss
        "goal_focus_areas": [],  # User's stated goals
        "sensitivity_topics": [],  # Topics requiring extra care
    },
    
    # Timing preferences
    "timing": {
        "active_hours_start": 8,  # 8 AM
        "active_hours_end": 22,  # 10 PM
        "timezone_offset": 0,  # UTC offset in hours
        "preferred_check_in_time": None,  # Specific time for daily check-in
    },
    
    # Learning/adaptation rates
    "adaptation": {
        "learning_rate": 0.1,  # How quickly to adjust parameters
        "feedback_weight": 0.3,  # How much feedback affects adjustments
        "recency_weight": 0.7,  # Weight for recent vs old interactions
        "min_interactions_to_adapt": 5,  # Minimum interactions before adapting
    }
}


class UserPersonalization:
    """
    Manages per-user personalized parameters with adaptive learning.
    Uses fresh database connections per operation for thread safety.
    """
    
    def __init__(self, db_getter):
        """
        Initialize with a database getter function or IntegratedDatabase instance.
        This ensures thread-safe database access.
        """
        self._db_getter = db_getter
        self._init_tables()
    
    def _get_db(self):
        """Get a fresh database connection (thread-safe)"""
        if hasattr(self._db_getter, 'get_connection'):
            # It's an IntegratedDatabase instance
            return self._db_getter.get_connection()
        elif callable(self._db_getter):
            # It's a function that returns a connection
            return self._db_getter()
        else:
            # It's a direct connection (legacy, not thread-safe)
            return self._db_getter
    
    def _init_tables(self):
        """Create tables for user personalization"""
        db = self._get_db()
        cursor = db.cursor()
        
        # Main personalization parameters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_personalization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                parameters TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Parameter change history (for learning and debugging)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_parameter_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                parameter_path TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                change_reason TEXT,
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Interaction signals for adaptive learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interaction_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                signal_type TEXT NOT NULL,
                signal_value TEXT,
                context TEXT,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_personalization_user 
            ON user_personalization(user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_signals_user_unprocessed 
            ON user_interaction_signals(user_id, processed)
        ''')
        
        db.commit()
    
    def get_user_parameters(self, user_id: int) -> Dict:
        """
        Get personalized parameters for a user.
        Returns defaults merged with user's customizations.
        """
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT parameters FROM user_personalization WHERE user_id = ?',
            (user_id,)
        )
        row = cursor.fetchone()
        
        # Start with defaults
        params = self._deep_copy(DEFAULT_USER_PARAMETERS)
        
        if row:
            try:
                user_params = json.loads(row[0])
                # Merge user params over defaults
                params = self._deep_merge(params, user_params)
            except json.JSONDecodeError:
                pass
        
        return params
    
    def get_parameter(self, user_id: int, path: str, default: Any = None) -> Any:
        """
        Get a specific parameter by path (e.g., 'routing.domain_mental_health_threshold')
        """
        params = self.get_user_parameters(user_id)
        
        keys = path.split('.')
        value = params
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set_parameter(self, user_id: int, path: str, value: Any, 
                      reason: str = None) -> bool:
        """
        Set a specific parameter for a user.
        Records history for learning and debugging.
        """
        db = self._get_db()
        cursor = db.cursor()
        
        # Get current parameters
        params = self.get_user_parameters(user_id)
        old_value = self.get_parameter(user_id, path)
        
        # Update the value
        keys = path.split('.')
        target = params
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        
        # Save to database
        cursor.execute('''
            INSERT INTO user_personalization (user_id, parameters, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                parameters = ?,
                updated_at = CURRENT_TIMESTAMP,
                version = version + 1
        ''', (user_id, json.dumps(params), json.dumps(params)))
        
        # Record history
        cursor.execute('''
            INSERT INTO user_parameter_history 
            (user_id, parameter_path, old_value, new_value, change_reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, path, json.dumps(old_value), json.dumps(value), reason))
        
        db.commit()
        return True
    
    def update_parameters(self, user_id: int, updates: Dict, reason: str = None) -> bool:
        """
        Update multiple parameters at once.
        """
        db = self._get_db()
        cursor = db.cursor()
        params = self.get_user_parameters(user_id)
        
        # Record each change
        def record_changes(current: Dict, new: Dict, path: str = ''):
            for key, value in new.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, dict) and key in current and isinstance(current[key], dict):
                    record_changes(current[key], value, current_path)
                else:
                    old_val = current.get(key)
                    if old_val != value:
                        cursor.execute('''
                            INSERT INTO user_parameter_history 
                            (user_id, parameter_path, old_value, new_value, change_reason)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (user_id, current_path, json.dumps(old_val), json.dumps(value), reason))
        
        record_changes(params, updates)
        
        # Merge updates
        params = self._deep_merge(params, updates)
        
        # Save
        cursor.execute('''
            INSERT INTO user_personalization (user_id, parameters, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                parameters = ?,
                updated_at = CURRENT_TIMESTAMP,
                version = version + 1
        ''', (user_id, json.dumps(params), json.dumps(params)))
        
        db.commit()
        return True
    
    # ==================== INTERACTION SIGNALS ====================
    
    def record_signal(self, user_id: int, signal_type: str, 
                      signal_value: Any, context: str = None):
        """
        Record an interaction signal for adaptive learning.
        
        Signal types:
        - 'positive_response': User responded positively
        - 'negative_response': User responded negatively
        - 'topic_interest': User showed interest in a topic
        - 'topic_avoid': User avoided or disliked a topic
        - 'preferred_character': User preferred a specific character
        - 'response_length_feedback': User indicated length preference
        - 'prompt_dismissed': User dismissed a proactive prompt
        - 'prompt_engaged': User engaged with a proactive prompt
        - 'timing_preference': User activity at specific times
        """
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO user_interaction_signals 
            (user_id, signal_type, signal_value, context)
            VALUES (?, ?, ?, ?)
        ''', (user_id, signal_type, json.dumps(signal_value), context))
        db.commit()
    
    def process_signals_and_adapt(self, user_id: int) -> Dict:
        """
        Process unprocessed signals and adapt user parameters.
        Returns summary of adaptations made.
        """
        db = self._get_db()
        cursor = db.cursor()
        
        # Get user's current parameters
        params = self.get_user_parameters(user_id)
        adaptation_config = params.get('adaptation', {})
        learning_rate = adaptation_config.get('learning_rate', 0.1)
        min_interactions = adaptation_config.get('min_interactions_to_adapt', 5)
        
        # Get unprocessed signals
        cursor.execute('''
            SELECT id, signal_type, signal_value, context
            FROM user_interaction_signals
            WHERE user_id = ? AND processed = 0
            ORDER BY recorded_at ASC
        ''', (user_id,))
        signals = cursor.fetchall()
        
        if len(signals) < min_interactions:
            return {'adapted': False, 'reason': f'Need {min_interactions} signals, have {len(signals)}'}
        
        adaptations = []
        
        # Group signals by type
        signal_groups = {}
        for sig_id, sig_type, sig_value, context in signals:
            if sig_type not in signal_groups:
                signal_groups[sig_type] = []
            signal_groups[sig_type].append({
                'id': sig_id,
                'value': json.loads(sig_value) if sig_value else None,
                'context': context
            })
        
        # Process each signal type
        for sig_type, group in signal_groups.items():
            adaptation = self._process_signal_group(user_id, sig_type, group, learning_rate)
            if adaptation:
                adaptations.append(adaptation)
        
        # Mark signals as processed
        signal_ids = [s[0] for s in signals]
        if signal_ids:
            placeholders = ','.join(['?' for _ in signal_ids])
            cursor.execute(f'''
                UPDATE user_interaction_signals 
                SET processed = 1 
                WHERE id IN ({placeholders})
            ''', signal_ids)
            db.commit()
        
        return {
            'adapted': len(adaptations) > 0,
            'adaptations': adaptations,
            'signals_processed': len(signals)
        }
    
    def _process_signal_group(self, user_id: int, signal_type: str, 
                               signals: List[Dict], learning_rate: float) -> Optional[Dict]:
        """Process a group of signals of the same type"""
        
        if signal_type == 'preferred_character':
            # Adjust character thresholds based on preference
            char_counts = {}
            for sig in signals:
                char_id = sig['value']
                char_counts[char_id] = char_counts.get(char_id, 0) + 1
            
            # Lower threshold for preferred characters
            for char_id, count in char_counts.items():
                threshold_key = f'routing.{char_id}_threshold'
                current = self.get_parameter(user_id, threshold_key)
                if current is not None:
                    # Decrease threshold (make more likely to trigger)
                    adjustment = learning_rate * (count / len(signals))
                    new_value = max(0.1, current - adjustment)
                    self.set_parameter(user_id, threshold_key, new_value,
                                      f'Adapted from {count} preferences')
            
            return {'type': 'character_preference', 'adjusted': list(char_counts.keys())}
        
        elif signal_type == 'topic_interest':
            # Add to preferred topics
            topics = [sig['value'] for sig in signals if sig['value']]
            if topics:
                current_topics = self.get_parameter(user_id, 'content.preferred_topics', [])
                new_topics = list(set(current_topics + topics))[:20]  # Keep top 20
                self.set_parameter(user_id, 'content.preferred_topics', new_topics,
                                  f'Added {len(topics)} interest topics')
                return {'type': 'topic_interest', 'added': topics}
        
        elif signal_type == 'topic_avoid':
            # Add to avoided topics
            topics = [sig['value'] for sig in signals if sig['value']]
            if topics:
                current_avoided = self.get_parameter(user_id, 'content.avoided_topics', [])
                new_avoided = list(set(current_avoided + topics))[:20]
                self.set_parameter(user_id, 'content.avoided_topics', new_avoided,
                                  f'Added {len(topics)} avoided topics')
                return {'type': 'topic_avoid', 'added': topics}
        
        elif signal_type == 'prompt_dismissed':
            # Reduce prompt frequency
            current_freq = self.get_parameter(user_id, 'engagement.prompt_frequency_hours', 24)
            dismiss_rate = len(signals) / max(1, len(signals))
            if dismiss_rate > 0.5:  # More than half dismissed
                new_freq = min(72, current_freq + 6)  # Increase interval
                self.set_parameter(user_id, 'engagement.prompt_frequency_hours', new_freq,
                                  f'Increased due to {len(signals)} dismissals')
                return {'type': 'prompt_frequency', 'new_value': new_freq}
        
        elif signal_type == 'prompt_engaged':
            # Increase prompt frequency
            current_freq = self.get_parameter(user_id, 'engagement.prompt_frequency_hours', 24)
            if len(signals) >= 3:
                new_freq = max(12, current_freq - 4)  # Decrease interval
                self.set_parameter(user_id, 'engagement.prompt_frequency_hours', new_freq,
                                  f'Decreased due to {len(signals)} engagements')
                return {'type': 'prompt_frequency', 'new_value': new_freq}
        
        elif signal_type == 'response_length_feedback':
            # Adjust response length preference
            length_prefs = [sig['value'] for sig in signals]
            if length_prefs:
                # Count preferences
                pref_counts = {}
                for pref in length_prefs:
                    pref_counts[pref] = pref_counts.get(pref, 0) + 1
                # Most common preference
                most_common = max(pref_counts, key=pref_counts.get)
                self.set_parameter(user_id, 'communication.response_length', most_common,
                                  f'Based on {len(signals)} signals')
                return {'type': 'response_length', 'new_value': most_common}
        
        return None
    
    # ==================== CHARACTER-SPECIFIC THRESHOLDS ====================
    
    def get_character_threshold(self, user_id: int, character_id: str) -> float:
        """Get the routing threshold for a specific character for this user"""
        path = f'routing.{character_id}_threshold'
        default_threshold = DEFAULT_USER_PARAMETERS['routing'].get(
            f'{character_id}_threshold', 0.25
        )
        return self.get_parameter(user_id, path, default_threshold)
    
    def adjust_character_threshold(self, user_id: int, character_id: str, 
                                    delta: float, reason: str = None):
        """Adjust a character's threshold (positive = higher/less likely, negative = lower/more likely)"""
        current = self.get_character_threshold(user_id, character_id)
        new_value = max(0.05, min(0.9, current + delta))
        path = f'routing.{character_id}_threshold'
        self.set_parameter(user_id, path, new_value, reason)
        return new_value
    
    # ==================== UTILITY METHODS ====================
    
    def _deep_copy(self, obj: Dict) -> Dict:
        """Deep copy a dictionary"""
        return json.loads(json.dumps(obj))
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge override into base"""
        result = self._deep_copy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_parameter_history(self, user_id: int, parameter_path: str = None, 
                               limit: int = 20) -> List[Dict]:
        """Get history of parameter changes for a user"""
        db = self._get_db()
        cursor = db.cursor()
        
        if parameter_path:
            cursor.execute('''
                SELECT parameter_path, old_value, new_value, change_reason, changed_at
                FROM user_parameter_history
                WHERE user_id = ? AND parameter_path = ?
                ORDER BY changed_at DESC
                LIMIT ?
            ''', (user_id, parameter_path, limit))
        else:
            cursor.execute('''
                SELECT parameter_path, old_value, new_value, change_reason, changed_at
                FROM user_parameter_history
                WHERE user_id = ?
                ORDER BY changed_at DESC
                LIMIT ?
            ''', (user_id, limit))
        
        return [{
            'path': r[0],
            'old_value': json.loads(r[1]) if r[1] else None,
            'new_value': json.loads(r[2]) if r[2] else None,
            'reason': r[3],
            'changed_at': r[4]
        } for r in cursor.fetchall()]
    
    def reset_to_defaults(self, user_id: int, category: str = None) -> bool:
        """Reset user parameters to defaults (optionally just one category)"""
        db = self._get_db()
        cursor = db.cursor()
        
        if category:
            # Reset just one category
            default_cat = DEFAULT_USER_PARAMETERS.get(category)
            if default_cat:
                params = self.get_user_parameters(user_id)
                params[category] = self._deep_copy(default_cat)
                cursor.execute('''
                    UPDATE user_personalization
                    SET parameters = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (json.dumps(params), user_id))
        else:
            # Reset all
            cursor.execute('DELETE FROM user_personalization WHERE user_id = ?', (user_id,))
        
        # Record the reset
        cursor.execute('''
            INSERT INTO user_parameter_history 
            (user_id, parameter_path, old_value, new_value, change_reason)
            VALUES (?, ?, NULL, NULL, ?)
        ''', (user_id, category or 'ALL', f'Reset to defaults'))
        
        db.commit()
        return True
    
    def export_user_profile(self, user_id: int) -> Dict:
        """Export complete user personalization profile"""
        return {
            'user_id': user_id,
            'parameters': self.get_user_parameters(user_id),
            'recent_history': self.get_parameter_history(user_id, limit=50),
            'exported_at': datetime.now().isoformat()
        }
