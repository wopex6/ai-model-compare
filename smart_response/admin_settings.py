"""
Admin Settings Module
Centralized configuration management with database persistence.
All settings are admin-configurable via UI - no hardcoding.
"""

import sqlite3
import json
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path


# Default settings with descriptions (used only for initialization)
DEFAULT_SETTINGS = {
    # Data Retention Settings
    'data_retention_years': {
        'value': 3,
        'type': 'integer',
        'min': 1,
        'max': 10,
        'category': 'data_retention',
        'label': 'Data Retention Period (Years)',
        'description': 'How long to keep character interpretations and user insights before automatic cleanup'
    },
    'auto_cleanup_enabled': {
        'value': True,
        'type': 'boolean',
        'category': 'data_retention',
        'label': 'Enable Automatic Data Cleanup',
        'description': 'Automatically remove old interpretation data beyond retention period'
    },
    'cleanup_batch_size': {
        'value': 1000,
        'type': 'integer',
        'min': 100,
        'max': 10000,
        'category': 'data_retention',
        'label': 'Cleanup Batch Size',
        'description': 'Number of records to delete per cleanup run (prevents database locks)'
    },
    
    # Character Analysis Settings
    'concern_threshold_respond': {
        'value': 0.15,
        'type': 'float',
        'min': 0.05,
        'max': 0.50,
        'category': 'character_analysis',
        'label': 'Response Threshold',
        'description': 'Minimum concern level (0-1) for a character to respond to a message'
    },
    'concern_per_keyword': {
        'value': 0.08,
        'type': 'float',
        'min': 0.01,
        'max': 0.20,
        'category': 'character_analysis',
        'label': 'Concern Per Keyword',
        'description': 'How much each detected keyword adds to concern level'
    },
    'max_responding_characters': {
        'value': 3,
        'type': 'integer',
        'min': 1,
        'max': 10,
        'category': 'character_analysis',
        'label': 'Max Responding Characters',
        'description': 'Maximum number of characters that can respond to a single message'
    },
    
    # Emotion Detection Settings
    'emotion_detection_method': {
        'value': 'hybrid',
        'type': 'select',
        'options': ['keyword', 'ai', 'hybrid'],
        'category': 'emotion_detection',
        'label': 'Emotion Detection Method',
        'description': 'Method for detecting user emotions: keyword-based, AI-based, or hybrid'
    },
    'emotion_ai_confidence_threshold': {
        'value': 0.7,
        'type': 'float',
        'min': 0.5,
        'max': 0.95,
        'category': 'emotion_detection',
        'label': 'AI Emotion Confidence Threshold',
        'description': 'Minimum confidence for AI emotion detection to be used'
    },
    'emotion_keywords_stress': {
        'value': 'stress,stressed,overwhelm,overwhelmed,pressure,anxious,anxiety,worried,worry,tense,nervous',
        'type': 'text',
        'category': 'emotion_detection',
        'label': 'Stress Keywords',
        'description': 'Comma-separated keywords that indicate stress (used in keyword/hybrid mode)'
    },
    'emotion_keywords_positive': {
        'value': 'happy,excited,grateful,thankful,joy,pleased,delighted,optimistic,hopeful,confident',
        'type': 'text',
        'category': 'emotion_detection',
        'label': 'Positive Keywords',
        'description': 'Comma-separated keywords that indicate positive emotions'
    },
    'emotion_keywords_negative': {
        'value': 'sad,angry,frustrated,upset,disappointed,hurt,lonely,depressed,hopeless,helpless',
        'type': 'text',
        'category': 'emotion_detection',
        'label': 'Negative Keywords',
        'description': 'Comma-separated keywords that indicate negative emotions'
    },
    
    # Personalization Settings
    'personalization_enabled': {
        'value': True,
        'type': 'boolean',
        'category': 'personalization',
        'label': 'Enable Personalization',
        'description': 'Use historical insights to personalize AI responses'
    },
    'personalization_min_interactions': {
        'value': 5,
        'type': 'integer',
        'min': 1,
        'max': 50,
        'category': 'personalization',
        'label': 'Minimum Interactions for Personalization',
        'description': 'Number of interactions required before personalization kicks in'
    },
    'personalization_history_limit': {
        'value': 100,
        'type': 'integer',
        'min': 10,
        'max': 500,
        'category': 'personalization',
        'label': 'History Lookup Limit',
        'description': 'Maximum number of past interpretations to analyze for personalization'
    },
    'personalization_max_context_tokens': {
        'value': 200,
        'type': 'integer',
        'min': 50,
        'max': 500,
        'category': 'personalization',
        'label': 'Max Context Tokens',
        'description': 'Maximum tokens to add to AI prompt for personalization context'
    },
    
    # Privacy Settings
    'user_can_view_insights': {
        'value': True,
        'type': 'boolean',
        'category': 'privacy',
        'label': 'Users Can View Their Insights',
        'description': 'Allow users to see what characters have learned about them'
    },
    'user_can_delete_insights': {
        'value': True,
        'type': 'boolean',
        'category': 'privacy',
        'label': 'Users Can Delete Their Insights',
        'description': 'Allow users to delete their interpretation/insight data'
    },
    'user_can_export_data': {
        'value': True,
        'type': 'boolean',
        'category': 'privacy',
        'label': 'Users Can Export Data',
        'description': 'Allow users to export their personal data'
    },
    
    # Cost Management
    'cost_alert_threshold': {
        'value': 10.0,
        'type': 'float',
        'min': 1.0,
        'max': 100.0,
        'category': 'cost_management',
        'label': 'Cost Alert Threshold ($)',
        'description': 'Daily cost threshold for alerts'
    },
    'ai_calls_per_message_limit': {
        'value': 5,
        'type': 'integer',
        'min': 1,
        'max': 20,
        'category': 'cost_management',
        'label': 'Max AI Calls Per Message',
        'description': 'Maximum AI API calls allowed per user message'
    }
}

# Category metadata for UI organization
SETTING_CATEGORIES = {
    'data_retention': {
        'label': 'Data Retention',
        'icon': '🗄️',
        'description': 'Configure how long user data is kept'
    },
    'character_analysis': {
        'label': 'Character Analysis',
        'icon': '🎭',
        'description': 'Control how characters analyze and respond to messages'
    },
    'emotion_detection': {
        'label': 'Emotion Detection',
        'icon': '😊',
        'description': 'Configure emotion detection methods and keywords'
    },
    'personalization': {
        'label': 'Personalization',
        'icon': '✨',
        'description': 'Settings for AI response personalization'
    },
    'privacy': {
        'label': 'Privacy & User Control',
        'icon': '🔒',
        'description': 'User data access and control settings'
    },
    'cost_management': {
        'label': 'Cost Management',
        'icon': '💰',
        'description': 'AI usage and cost control settings'
    }
}


class AdminSettings:
    """Manages admin-configurable settings with database persistence"""
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = str(Path(__file__).parent.parent / 'smart_response.db')
        self._cache = {}
        self._cache_time = None
        self._cache_ttl = 60  # Cache for 60 seconds
        self._ensure_table()
        self._initialize_defaults()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        return conn
    
    def _ensure_table(self):
        """Create settings table if it doesn't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                category TEXT DEFAULT 'general',
                label TEXT,
                description TEXT,
                min_value REAL,
                max_value REAL,
                options TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _initialize_defaults(self):
        """Initialize default settings if not already set"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for key, config in DEFAULT_SETTINGS.items():
            cursor.execute('SELECT key FROM admin_settings WHERE key = ?', (key,))
            if not cursor.fetchone():
                value = json.dumps(config['value']) if isinstance(config['value'], (list, dict)) else str(config['value'])
                options = json.dumps(config.get('options', [])) if config.get('options') else None
                
                cursor.execute('''
                    INSERT INTO admin_settings (key, value, setting_type, category, label, description, min_value, max_value, options)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key,
                    value,
                    config.get('type', 'string'),
                    config.get('category', 'general'),
                    config.get('label', key),
                    config.get('description', ''),
                    config.get('min'),
                    config.get('max'),
                    options
                ))
        
        conn.commit()
        conn.close()
    
    def _invalidate_cache(self):
        """Clear the settings cache"""
        self._cache = {}
        self._cache_time = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value with type conversion"""
        # Check cache first
        if self._cache_time and (datetime.now() - self._cache_time).seconds < self._cache_ttl:
            if key in self._cache:
                return self._cache[key]
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value, setting_type FROM admin_settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return default
        
        value, setting_type = row
        
        # Type conversion
        if setting_type == 'integer':
            result = int(value)
        elif setting_type == 'float':
            result = float(value)
        elif setting_type == 'boolean':
            result = value.lower() in ('true', '1', 'yes')
        elif setting_type == 'json':
            result = json.loads(value)
        else:
            result = value
        
        # Update cache
        self._cache[key] = result
        if not self._cache_time:
            self._cache_time = datetime.now()
        
        return result
    
    def set(self, key: str, value: Any, updated_by: str = 'system') -> bool:
        """Set a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Convert value to string for storage
        if isinstance(value, bool):
            str_value = 'true' if value else 'false'
        elif isinstance(value, (list, dict)):
            str_value = json.dumps(value)
        else:
            str_value = str(value)
        
        cursor.execute('''
            UPDATE admin_settings 
            SET value = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
            WHERE key = ?
        ''', (str_value, updated_by, key))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        # Invalidate cache
        self._invalidate_cache()
        
        return success
    
    def get_all(self) -> Dict[str, Dict]:
        """Get all settings with their metadata"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT key, value, setting_type, category, label, description, 
                   min_value, max_value, options, updated_at
            FROM admin_settings
            ORDER BY category, key
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for row in rows:
            key, value, setting_type, category, label, description, min_val, max_val, options, updated_at = row
            
            # Convert value based on type
            if setting_type == 'integer':
                typed_value = int(value)
            elif setting_type == 'float':
                typed_value = float(value)
            elif setting_type == 'boolean':
                typed_value = value.lower() in ('true', '1', 'yes')
            elif setting_type == 'json':
                typed_value = json.loads(value)
            else:
                typed_value = value
            
            settings[key] = {
                'value': typed_value,
                'type': setting_type,
                'category': category,
                'label': label or key,
                'description': description or '',
                'min': min_val,
                'max': max_val,
                'options': json.loads(options) if options else None,
                'updated_at': updated_at
            }
        
        return settings
    
    def get_by_category(self, category: str) -> Dict[str, Dict]:
        """Get all settings in a specific category"""
        all_settings = self.get_all()
        return {k: v for k, v in all_settings.items() if v['category'] == category}
    
    def get_categories(self) -> Dict[str, Dict]:
        """Get category metadata"""
        return SETTING_CATEGORIES
    
    def validate_setting(self, key: str, value: Any) -> tuple:
        """Validate a setting value. Returns (is_valid, error_message)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT setting_type, min_value, max_value, options
            FROM admin_settings WHERE key = ?
        ''', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False, f"Unknown setting: {key}"
        
        setting_type, min_val, max_val, options = row
        
        # Type validation
        if setting_type == 'integer':
            try:
                int_val = int(value)
                if min_val is not None and int_val < min_val:
                    return False, f"Value must be at least {int(min_val)}"
                if max_val is not None and int_val > max_val:
                    return False, f"Value must be at most {int(max_val)}"
            except ValueError:
                return False, "Value must be an integer"
        
        elif setting_type == 'float':
            try:
                float_val = float(value)
                if min_val is not None and float_val < min_val:
                    return False, f"Value must be at least {min_val}"
                if max_val is not None and float_val > max_val:
                    return False, f"Value must be at most {max_val}"
            except ValueError:
                return False, "Value must be a number"
        
        elif setting_type == 'select' and options:
            valid_options = json.loads(options)
            if value not in valid_options:
                return False, f"Value must be one of: {', '.join(valid_options)}"
        
        return True, None


# Singleton instance
_settings_instance = None

def get_admin_settings(db_path: str = None) -> AdminSettings:
    """Get or create the singleton AdminSettings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AdminSettings(db_path)
    return _settings_instance


def get_setting(key: str, default: Any = None) -> Any:
    """Convenience function to get a setting value"""
    return get_admin_settings().get(key, default)
