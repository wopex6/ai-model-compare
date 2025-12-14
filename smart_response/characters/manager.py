"""
Character Manager

Manages all characters and coordinates their responses based on:
1. User requests (explicit character selection)
2. Threshold triggers (concern level exceeds threshold)
3. Coordinator fallback (no other character responding)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import sqlite3

from .base import BaseCharacter, DomainCharacter, CoordinatorCharacter, CharacterResponse
from .configs import DOMAIN_CHARACTER_CONFIGS, PHILOSOPHY_CHARACTER_CONFIGS


class CharacterManager:
    """
    Manages all characters and coordinates their responses
    
    Response Rules:
    1. If user requests specific character → that character responds
    2. Characters above threshold respond (critical concern)
    3. If no one responds → coordinator synthesizes or requests domain input
    4. Others remain silent observers (store interpretation)
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self.characters: Dict[str, BaseCharacter] = {}
        self.domain_characters: Dict[str, DomainCharacter] = {}
        self.coordinator: Optional[CoordinatorCharacter] = None
        
        self._initialize_characters()
    
    def _initialize_characters(self):
        """Initialize all domain characters from configurations"""
        print("\n=== Initializing Domain Characters ===")
        
        for char_id, config in DOMAIN_CHARACTER_CONFIGS.items():
            try:
                if char_id == "coordinator":
                    # Create coordinator with special handling
                    self.coordinator = CoordinatorCharacter(
                        character_id=char_id,
                        config=config,
                        db_connection=self.db
                    )
                    self.characters[char_id] = self.coordinator
                    print(f"✓ {config.get('display_name', char_id)} (Coordinator) initialized")
                else:
                    # Create domain character
                    character = DomainCharacter(
                        character_id=char_id,
                        config=config,
                        db_connection=self.db
                    )
                    self.characters[char_id] = character
                    self.domain_characters[char_id] = character
                    print(f"✓ {config.get('display_name', char_id)} ({config.get('domain', 'general')}) initialized")
            except Exception as e:
                print(f"✗ Error initializing {char_id}: {e}")
        
        # Set coordinator's reference to this manager
        if self.coordinator:
            self.coordinator.set_character_manager(self)
        
        print(f"\n📊 Total characters initialized: {len(self.characters)}")
        print(f"   - Domain characters: {len(self.domain_characters)}")
        print(f"   - Coordinator: {'Yes' if self.coordinator else 'No'}")
    
    def route_message(self, message: str, context: Dict,
                      requested_character: Optional[str] = None) -> List[CharacterResponse]:
        """
        Route message to appropriate characters based on rules
        
        Args:
            message: User's message
            context: Full conversation context including user_id, history, etc.
            requested_character: Specific character ID if user requested one
            
        Returns:
            List of CharacterResponse objects from responding characters
        """
        responses = []
        history_id = context.get('history_id')
        
        # Rule 1: User requested specific character
        if requested_character:
            if requested_character in self.characters:
                character = self.characters[requested_character]
                response = character.generate_response(message, context)
                response.should_display = True
                responses.append(response)
                
                # Store interpretation
                if history_id:
                    character.store_interpretation(
                        history_id, 
                        response.interpretation,
                        response.concern_level,
                        responded=True
                    )
                
                # Still let other characters observe silently
                self._record_silent_observations(message, context, exclude=[requested_character])
                
                return responses
        
        # Rule 2: Check all domain characters for threshold triggers
        triggered_characters = []
        
        for char_id, character in self.domain_characters.items():
            concern_level = character.analyze_context(message, context)
            
            if character.should_respond(concern_level):
                response = character.generate_response(message, context)
                response.concern_level = concern_level
                response.should_display = True
                triggered_characters.append(char_id)
                responses.append(response)
                
                # Store interpretation as responder
                if history_id:
                    character.store_interpretation(
                        history_id,
                        response.interpretation,
                        concern_level,
                        responded=True
                    )
            else:
                # Silent observer - store interpretation without responding
                interpretation = character.interpret_context(message, context)
                if history_id:
                    character.store_interpretation(
                        history_id,
                        interpretation,
                        concern_level,
                        responded=False
                    )
        
        # Rule 3: If no domain characters triggered, coordinator responds
        if not responses and self.coordinator:
            response = self.coordinator.generate_response(message, context)
            response.should_display = True
            responses.append(response)
            
            if history_id:
                self.coordinator.store_interpretation(
                    history_id,
                    response.interpretation,
                    response.concern_level,
                    responded=True
                )
        
        return responses
    
    def _record_silent_observations(self, message: str, context: Dict, 
                                   exclude: List[str] = None):
        """Record interpretations from non-responding characters"""
        exclude = exclude or []
        history_id = context.get('history_id')
        
        if not history_id:
            return
        
        for char_id, character in self.characters.items():
            if char_id in exclude:
                continue
            
            concern_level = character.analyze_context(message, context)
            interpretation = character.interpret_context(message, context)
            
            character.store_interpretation(
                history_id,
                interpretation,
                concern_level,
                responded=False
            )
    
    def get_character(self, character_id: str) -> Optional[BaseCharacter]:
        """Get a specific character by ID"""
        return self.characters.get(character_id)
    
    def get_all_characters(self) -> Dict[str, BaseCharacter]:
        """Get all characters"""
        return self.characters
    
    def get_domain_characters(self) -> Dict[str, DomainCharacter]:
        """Get only domain characters (excluding coordinator)"""
        return self.domain_characters
    
    def get_coordinator(self) -> Optional[CoordinatorCharacter]:
        """Get the coordinator character"""
        return self.coordinator
    
    def get_character_info(self) -> List[Dict]:
        """Get info about all characters for display"""
        info = []
        
        for char_id, character in self.characters.items():
            config = DOMAIN_CHARACTER_CONFIGS.get(char_id, {})
            info.append({
                'id': char_id,
                'display_name': character.display_name,
                'domain': config.get('domain', 'general'),
                'description': config.get('description', ''),
                'is_coordinator': char_id == 'coordinator'
            })
        
        return info
    
    def get_interpretations_for_message(self, history_id: int) -> Dict[str, Dict]:
        """Get all character interpretations for a specific message"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT character_id, interpretation, concern_level, responded
            FROM character_interpretations
            WHERE primary_history_id = ?
        ''', (history_id,))
        
        interpretations = {}
        for row in cursor.fetchall():
            char_id, interp_json, concern, responded = row
            interpretations[char_id] = {
                'interpretation': json.loads(interp_json) if interp_json else {},
                'concern_level': concern,
                'responded': bool(responded),
                'display_name': self.characters[char_id].display_name if char_id in self.characters else char_id
            }
        
        return interpretations
    
    def get_critical_perspectives(self, history_id: int, 
                                  threshold: float = 0.7) -> List[Dict]:
        """Get perspectives from characters with high concern levels"""
        interpretations = self.get_interpretations_for_message(history_id)
        
        critical = []
        for char_id, data in interpretations.items():
            if data['concern_level'] >= threshold:
                critical.append({
                    'character_id': char_id,
                    'display_name': data['display_name'],
                    'concern_level': data['concern_level'],
                    'interpretation': data['interpretation'],
                    'responded': data['responded']
                })
        
        # Sort by concern level descending
        critical.sort(key=lambda x: x['concern_level'], reverse=True)
        
        return critical
    
    def update_user_preference(self, user_id: int, character_id: str, 
                               feedback: str, adjustment: float = 0.05):
        """Update user's preference for a character based on feedback"""
        if feedback == 'positive':
            delta = adjustment
        elif feedback == 'negative':
            delta = -adjustment
        else:
            return
        
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO user_character_preferences (user_id, character_id, preference_score, interaction_count, last_interaction)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(user_id, character_id) DO UPDATE SET
            preference_score = preference_score + ?,
            interaction_count = interaction_count + 1,
            last_interaction = ?
        ''', (user_id, character_id, delta, datetime.now(), delta, datetime.now()))
        self.db.commit()
    
    def get_user_preferences(self, user_id: int) -> Dict[str, float]:
        """Get user's preference scores for all characters"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT character_id, preference_score
            FROM user_character_preferences
            WHERE user_id = ?
        ''', (user_id,))
        
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def save_domain_characters_to_db(self):
        """Save domain character configurations to database"""
        cursor = self.db.cursor()
        
        for char_id, config in DOMAIN_CHARACTER_CONFIGS.items():
            cursor.execute('''
                INSERT OR REPLACE INTO domain_characters 
                (id, display_name, domain, threshold_config, style_config, system_prompt, active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (
                char_id,
                config.get('display_name', char_id),
                config.get('domain', 'general'),
                json.dumps(config.get('threshold_config', {})),
                json.dumps(config.get('style_config', {})),
                config.get('system_prompt', '')
            ))
        
        self.db.commit()
        print(f"✅ Saved {len(DOMAIN_CHARACTER_CONFIGS)} domain characters to database")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_character_manager(db_path: str = 'integrated_users.db') -> CharacterManager:
    """Create a CharacterManager with database connection"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return CharacterManager(conn)


def get_responding_characters(message: str, context: Dict, 
                             manager: CharacterManager) -> List[str]:
    """Get list of character IDs that would respond to this message"""
    responding = []
    
    for char_id, character in manager.get_domain_characters().items():
        concern_level = character.analyze_context(message, context)
        if character.should_respond(concern_level):
            responding.append(char_id)
    
    return responding
