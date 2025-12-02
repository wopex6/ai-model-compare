"""
Explicit Context Handler
Extracts and prioritizes user's explicit statements

USER REQUIREMENT: "For context explicitly stated by the user has to be taken seriously"
This system captures explicit user statements with CRITICAL priority.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import sqlite3


class ExplicitContextHandler:
    """
    Extracts and manages explicitly stated user context
    
    Patterns captured:
    - "I'm feeling X" → emotional_state
    - "My goal is X" → goal
    - "I want to X" → intention
    - "I prefer X" → preference
    - "I need X" → need
    - "I'm X" (personality traits) → self_description
    """
    
    # Priority levels
    PRIORITY_CRITICAL = 'CRITICAL'  # User's explicit words
    PRIORITY_HIGH = 'HIGH'  # Strong inference
    PRIORITY_NORMAL = 'NORMAL'  # Weak inference
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_tables()
    
    def _init_tables(self):
        """Create explicit context storage table"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS explicit_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character TEXT NOT NULL,
                
                -- When and what
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context_type TEXT NOT NULL,
                context_key TEXT NOT NULL,
                context_value TEXT NOT NULL,
                
                -- The actual words user said
                original_statement TEXT NOT NULL,
                
                -- Priority and confidence
                priority TEXT NOT NULL,
                confidence FLOAT DEFAULT 1.0,
                
                -- Lifecycle
                active BOOLEAN DEFAULT 1,
                expires_at TIMESTAMP,
                
                -- Metadata
                extracted_via TEXT
                
                -- NO UNIQUE CONSTRAINT - allow historical tracking!
                -- Old constraint was deleting history instead of preserving it
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_explicit_user_active
            ON explicit_context(user_id, character, active)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_explicit_priority
            ON explicit_context(priority, active)
        ''')
        
        self.db.commit()
        print("✓ Explicit Context Handler initialized")
    
    def _normalize_message(self, message: str) -> str:
        """
        Normalize message for pattern matching
        Strips quotes and handles punctuation transparently
        
        Users should be able to type:
        - "I'm stressed" or I'm stressed
        - "I want success" or I want success
        And both work the same way.
        """
        # Handle None and invalid input
        if message is None:
            return ""
        
        # Strip leading/trailing whitespace
        normalized = message.strip()
        
        # Remove surrounding quotes (single or double)
        if (normalized.startswith('"') and normalized.endswith('"')) or \
           (normalized.startswith("'") and normalized.endswith("'")):
            normalized = normalized[1:-1].strip()
        
        # Remove quotes around specific phrases (common in typed messages)
        # e.g., 'I want "success"' → 'I want success'
        normalized = normalized.replace('"', '').replace("'s ", "'s ")  # Keep possessives
        
        return normalized
    
    def extract_explicit_context(self, user_id: int, character: str, message: str) -> List[Dict]:
        """
        Extract explicit context from user message
        
        Returns:
            List of extracted context items
        """
        extracted = []
        
        # Normalize message: strip quotes and clean punctuation for pattern matching
        # This makes the system transparent to formatting variations
        message_normalized = self._normalize_message(message)
        message_lower = message_normalized.lower()
        
        # Pattern 1: Emotional state - "I'm feeling X"
        emotional = self._extract_emotional_state(message, message_lower)
        if emotional:
            extracted.append(emotional)
        
        # Pattern 2: Goals - "My goal is X" / "I want to X"
        goals = self._extract_goals(message, message_lower)
        extracted.extend(goals)
        
        # Pattern 3: Preferences - "I prefer X" / "I like X"
        preferences = self._extract_preferences(message, message_lower)
        extracted.extend(preferences)
        
        # Pattern 4: Needs - "I need X"
        needs = self._extract_needs(message, message_lower)
        extracted.extend(needs)
        
        # Pattern 5: Self-descriptions - "I'm X" (personality traits)
        self_desc = self._extract_self_descriptions(message, message_lower)
        extracted.extend(self_desc)
        
        # Pattern 6: Intentions - "I plan to X" / "I will X"
        intentions = self._extract_intentions(message, message_lower)
        extracted.extend(intentions)
        
        # Pattern 7: Values - "I value X" / "X is important to me"
        values = self._extract_values(message, message_lower)
        extracted.extend(values)
        
        # Store all extracted context
        for item in extracted:
            self.store_explicit_context(
                user_id, character,
                item['type'], item['key'], item['value'],
                message,  # Original statement
                item['priority'],
                item.get('confidence', 1.0),
                item.get('extracted_via', 'pattern_matching')
            )
        
        return extracted
    
    def _extract_emotional_state(self, message: str, message_lower: str) -> Optional[Dict]:
        """Extract emotional state from message"""
        patterns = [
            (r"i'?m feeling (very |really |extremely |quite |a bit |somewhat )?([\w\s]+?)(?:\.|,|because|and|but|$)", 0.95),
            (r"i feel (very |really |extremely |quite |a bit |somewhat )?([\w\s]+?)(?:\.|,|because|and|but|$)", 0.95),
            (r"i'?m (very |really |extremely |quite |a bit |somewhat )?(stressed|anxious|worried|happy|excited|sad|depressed|angry|frustrated|overwhelmed|tired|exhausted|motivated|inspired|confident|nervous|scared|hopeful|grateful|proud|disappointed|confused)", 0.90),
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Extract the emotion (last group)
                emotion = match.group(match.lastindex).strip()
                
                # Clean up
                emotion = emotion.split()[0] if emotion.split() else emotion
                emotion = emotion.strip('.,;!?')
                
                if len(emotion) > 2 and len(emotion) < 30:  # Reasonable length
                    return {
                        'type': 'emotional_state',
                        'key': 'current_emotion',
                        'value': emotion,
                        'priority': self.PRIORITY_CRITICAL,
                        'confidence': confidence,
                        'extracted_via': 'emotion_pattern'
                    }
        
        return None
    
    def _extract_goals(self, message: str, message_lower: str) -> List[Dict]:
        """Extract goals and aspirations"""
        goals = []
        
        patterns = [
            (r"my goal is (?:to |that )?(.*?)(?:\.|,|and|but|$)", 'goal', 0.95),
            (r"i want to (.*?)(?:\.|,|and|but|because|$)", 'intention', 0.90),
            (r"i want (.*?)(?:\.|,|and|but|because|$)", 'intention', 0.88),  # Without "to"
            (r"i'?m trying to (.*?)(?:\.|,|and|but|because|$)", 'effort', 0.90),
            (r"i hope to (.*?)(?:\.|,|and|but|$)", 'aspiration', 0.85),
            (r"i need to (.*?)(?:\.|,|and|but|because|$)", 'requirement', 0.85),
        ]
        
        for pattern, goal_type, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                goal_text = match.group(1).strip()
                
                # Clean up
                goal_text = goal_text.strip('.,;!?')
                
                if len(goal_text) > 3 and len(goal_text) < 200:
                    goals.append({
                        'type': 'goal',
                        'key': goal_type,
                        'value': goal_text,
                        'priority': self.PRIORITY_CRITICAL,
                        'confidence': confidence,
                        'extracted_via': 'goal_pattern'
                    })
        
        return goals
    
    def _extract_preferences(self, message: str, message_lower: str) -> List[Dict]:
        """Extract preferences and likes/dislikes"""
        preferences = []
        
        patterns = [
            (r"i (?:really |strongly )?prefer (.*?)(?:\.|,|over|than|and|but|to|$)", 'preference', 0.90),
            (r"i'?d prefer (.*?)(?:\.|,|over|than|and|but|to|$)", 'preference', 0.88),
            (r"i like (to |that )?(.*?)(?:\.|,|and|but|because|$)", 'like', 0.85),
            (r"i don'?t like (to |that )?(.*?)(?:\.|,|and|but|because|$)", 'dislike', 0.85),
            (r"i love (to |that )?(.*?)(?:\.|,|and|but|because|$)", 'love', 0.90),
            (r"i hate (to |that )?(.*?)(?:\.|,|and|but|because|$)", 'hate', 0.85),
            (r"i enjoy (.*?)(?:\.|,|and|but|because|$)", 'enjoy', 0.85),
        ]
        
        for pattern, pref_type, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                pref_text = match.group(match.lastindex).strip()
                
                # Clean up
                pref_text = pref_text.strip('.,;!?')
                
                if len(pref_text) > 2 and len(pref_text) < 150:
                    preferences.append({
                        'type': 'preference',
                        'key': pref_type,
                        'value': pref_text,
                        'priority': self.PRIORITY_CRITICAL,
                        'confidence': confidence,
                        'extracted_via': 'preference_pattern'
                    })
        
        return preferences
    
    def _extract_needs(self, message: str, message_lower: str) -> List[Dict]:
        """Extract stated needs"""
        needs = []
        
        patterns = [
            (r"i need (.*?)(?:\.|,|and|but|because|$)", 0.90),
            (r"i require (.*?)(?:\.|,|and|but|$)", 0.85),
            (r"i must (.*?)(?:\.|,|and|but|$)", 0.85),
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                need_text = match.group(1).strip()
                
                # Clean up
                need_text = need_text.strip('.,;!?')
                
                if len(need_text) > 2 and len(need_text) < 150:
                    needs.append({
                        'type': 'need',
                        'key': 'stated_need',
                        'value': need_text,
                        'priority': self.PRIORITY_CRITICAL,
                        'confidence': confidence,
                        'extracted_via': 'need_pattern'
                    })
        
        return needs
    
    def _extract_self_descriptions(self, message: str, message_lower: str) -> List[Dict]:
        """Extract self-descriptions and personality traits"""
        descriptions = []
        
        # Common personality descriptors
        traits = [
            'introvert', 'extrovert', 'perfectionist', 'procrastinator',
            'optimist', 'pessimist', 'realist', 'ambitious', 'lazy',
            'organized', 'disorganized', 'creative', 'analytical',
            'emotional', 'logical', 'sensitive', 'tough', 'shy',
            'confident', 'anxious', 'calm', 'energetic', 'patient',
            'impatient', 'detail-oriented', 'big-picture'
        ]
        
        pattern = r"i'?m (?:a |an |very |really |quite )?([\w\s-]+?)(?:\.|,|and|but|person|$)"
        matches = re.finditer(pattern, message_lower)
        
        # Words that indicate emotional state or temporary condition, not personality
        emotional_words = [
            'feeling', 'thinking', 'going', 'doing', 'trying', 'working',
            'stressed', 'worried', 'excited', 'happy', 'sad', 'angry',
            'frustrated', 'overwhelmed', 'tired', 'motivated', 'inspired',
            'exhausted', 'nervous', 'scared', 'hopeful', 'disappointed'
        ]
        
        for match in matches:
            trait = match.group(1).strip()
            
            # Skip if it contains emotional words (handled by emotional_state extraction)
            if any(emo in trait for emo in emotional_words):
                continue
            
            # Skip if it contains context words like "about", "for", "with" 
            # e.g., "feeling stressed about deadlines" should not be a trait
            if 'about' in trait or 'for' in trait or 'with' in trait:
                continue
            
            # Check if it's a known trait or long enough to be meaningful
            if trait in traits or (len(trait) > 4 and len(trait) < 40):
                descriptions.append({
                    'type': 'self_description',
                    'key': 'personality_trait',
                    'value': trait,
                    'priority': self.PRIORITY_CRITICAL,
                    'confidence': 0.85 if trait in traits else 0.70,
                    'extracted_via': 'self_description_pattern'
                })
        
        return descriptions
    
    def _extract_intentions(self, message: str, message_lower: str) -> List[Dict]:
        """Extract intentions and plans"""
        intentions = []
        
        patterns = [
            (r"i plan to (.*?)(?:\.|,|and|but|$)", 0.90),
            (r"i will (.*?)(?:\.|,|and|but|because|$)", 0.85),
            (r"i'?m going to (.*?)(?:\.|,|and|but|because|$)", 0.85),
            (r"i intend to (.*?)(?:\.|,|and|but|$)", 0.90),
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                intention_text = match.group(1).strip()
                
                # Clean up
                intention_text = intention_text.strip('.,;!?')
                
                if len(intention_text) > 3 and len(intention_text) < 150:
                    intentions.append({
                        'type': 'intention',
                        'key': 'planned_action',
                        'value': intention_text,
                        'priority': self.PRIORITY_CRITICAL,
                        'confidence': confidence,
                        'extracted_via': 'intention_pattern'
                    })
        
        return intentions
    
    def _extract_values(self, message: str, message_lower: str) -> List[Dict]:
        """Extract values and what's important to user"""
        values = []
        
        patterns = [
            (r"i value (.*?)(?:\.|,|and|but|$)", 0.90),
            (r"(.*?) is important to me", 0.85),
            (r"i care about (.*?)(?:\.|,|and|but|$)", 0.85),
            (r"i believe in (.*?)(?:\.|,|and|but|$)", 0.80),
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, message_lower)
            if match:
                value_text = match.group(1).strip()
                
                # Clean up
                value_text = value_text.strip('.,;!?')
                
                if len(value_text) > 2 and len(value_text) < 100:
                    values.append({
                        'type': 'value',
                        'key': 'personal_value',
                        'value': value_text,
                        'priority': self.PRIORITY_CRITICAL,
                        'confidence': confidence,
                        'extracted_via': 'value_pattern'
                    })
        
        return values
    
    def store_explicit_context(self, user_id: int, character: str,
                               context_type: str, context_key: str, 
                               context_value: str, original_statement: str,
                               priority: str = PRIORITY_CRITICAL,
                               confidence: float = 1.0,
                               extracted_via: str = 'manual') -> int:
        """
        Store explicit context with CRITICAL priority
        Implements context merging: new emotional states/goals replace old ones
        
        Returns:
            ID of stored context
        """
        cursor = self.db.cursor()
        
        try:
            # For certain context types, deactivate old values before storing new
            # (emotional state and current goals are transient, not cumulative)
            merge_types = ['emotional_state']  # Emotional state should be current
            
            if context_type in merge_types:
                # Deactivate previous context of same type/key
                cursor.execute('''
                    UPDATE explicit_context
                    SET active = 0
                    WHERE user_id = ? AND character = ? 
                    AND context_type = ? AND context_key = ?
                    AND active = 1
                ''', (user_id, character, context_type, context_key))
                
                deactivated = cursor.rowcount
                if deactivated > 0:
                    print(f"   ↻ Updated {context_type}.{context_key} (deactivated {deactivated} old)", flush=True)
            
            # Use INSERT to always create new row (preserve history for pattern analysis)
            # Previous rows are deactivated above, not deleted
            cursor.execute('''
                INSERT INTO explicit_context
                (user_id, character, context_type, context_key, context_value,
                 original_statement, priority, confidence, extracted_via,
                 timestamp, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
            ''', (
                user_id, character, context_type, context_key, context_value,
                original_statement, priority, confidence, extracted_via
            ))
            
            self.db.commit()
            
            context_id = cursor.lastrowid
            
            # Log what was captured
            print(f"📝 EXPLICIT CONTEXT: {context_type}.{context_key} = '{context_value}' (priority: {priority}, confidence: {confidence:.2f})", flush=True)
            
            return context_id
            
        except Exception as e:
            print(f"⚠️ Error storing explicit context: {e}", flush=True)
            return 0
    
    def get_explicit_context(self, user_id: int, character: str,
                            context_type: Optional[str] = None,
                            include_inactive: bool = False) -> List[Dict]:
        """
        Retrieve explicit context for user
        
        Args:
            user_id: User ID
            character: Character name
            context_type: Optional filter by type
            include_inactive: Include expired/inactive context
            
        Returns:
            List of context items sorted by priority
        """
        cursor = self.db.cursor()
        
        query = '''
            SELECT id, timestamp, context_type, context_key, context_value,
                   original_statement, priority, confidence, extracted_via
            FROM explicit_context
            WHERE user_id = ? AND character = ?
        '''
        params = [user_id, character]
        
        if context_type:
            query += ' AND context_type = ?'
            params.append(context_type)
        
        if not include_inactive:
            query += ' AND active = 1'
        
        # Order by priority (CRITICAL first) then recency
        query += '''
            ORDER BY 
                CASE priority
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    ELSE 3
                END,
                timestamp DESC
        '''
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'timestamp': row[1],
                'type': row[2],
                'key': row[3],
                'value': row[4],
                'original_statement': row[5],
                'priority': row[6],
                'confidence': row[7],
                'extracted_via': row[8]
            })
        
        return results
    
    def format_for_ai_prompt(self, user_id: int, character: str) -> str:
        """
        Format explicit context for AI prompt
        This goes at the TOP of context (highest priority)
        
        Returns:
            Formatted string for AI prompt
        """
        context_items = self.get_explicit_context(user_id, character)
        
        if not context_items:
            return ""
        
        # Group by type
        by_type = {}
        for item in context_items:
            t = item['type']
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(item)
        
        # Format for prompt
        prompt_parts = ["USER'S EXPLICIT STATEMENTS (TRUST THESE):"]
        
        # Emotional state (most recent)
        if 'emotional_state' in by_type:
            emotion = by_type['emotional_state'][0]['value']
            prompt_parts.append(f"- Current emotional state: {emotion}")
        
        # Goals
        if 'goal' in by_type:
            for goal in by_type['goal'][:3]:  # Top 3
                prompt_parts.append(f"- Goal: {goal['value']}")
        
        # Preferences
        if 'preference' in by_type:
            for pref in by_type['preference'][:3]:
                prompt_parts.append(f"- {pref['key'].capitalize()}: {pref['value']}")
        
        # Needs
        if 'need' in by_type:
            for need in by_type['need'][:2]:
                prompt_parts.append(f"- Needs: {need['value']}")
        
        # Values
        if 'value' in by_type:
            for val in by_type['value'][:2]:
                prompt_parts.append(f"- Values: {val['value']}")
        
        # Self-descriptions
        if 'self_description' in by_type:
            traits = [item['value'] for item in by_type['self_description'][:3]]
            if traits:
                prompt_parts.append(f"- Self-describes as: {', '.join(traits)}")
        
        return "\n".join(prompt_parts)
    
    def deactivate_context(self, context_id: int):
        """Mark context as no longer active (expired or superseded)"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE explicit_context
            SET active = 0
            WHERE id = ?
        ''', (context_id,))
        self.db.commit()
    
    def get_stats(self, user_id: int, character: str) -> Dict:
        """Get statistics about explicit context"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN active = 1 THEN 1 END) as active,
                COUNT(CASE WHEN priority = 'CRITICAL' THEN 1 END) as critical
            FROM explicit_context
            WHERE user_id = ? AND character = ?
        ''', (user_id, character))
        
        row = cursor.fetchone()
        
        return {
            'total_captured': row[0],
            'currently_active': row[1],
            'critical_priority': row[2]
        }
