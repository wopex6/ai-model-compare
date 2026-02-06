"""
Character-Specific Context Layer (Phase 6)
Same event, different perspectives per character.

Each character interprets events through their philosophical lens,
storing multiple perspectives in history for richer analysis.
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from .character_traits import CharacterTraitSystem, CharacterProfile, TraitVector


@dataclass
class CharacterInterpretation:
    """A character's interpretation of an event"""
    character_id: str
    character_name: str
    interpretation: str
    emotional_framing: str  # How the character frames emotions
    action_suggestion: str  # What the character suggests
    philosophical_lens: str  # The underlying philosophy
    dominant_traits: List[str]  # Top 3 traits influencing this interpretation
    confidence: float  # 0-1 how well this character fits the situation


class CharacterSpecificContext:
    """
    Generates character-specific interpretations of user events.
    Same event → multiple perspectives stored in history.
    """
    
    # Trait-to-interpretation mapping (no hardcoding of character IDs)
    TRAIT_INTERPRETATIONS = {
        'stoicism': {
            'lens': 'Stoic acceptance',
            'frame': lambda event: f"This is a test of character. Focus on what you can control.",
            'emotion': "Your feelings are natural responses, but they need not control your actions.",
            'action': "Identify what is within your control and act on that alone."
        },
        'optimism': {
            'lens': 'Optimistic growth',
            'frame': lambda event: f"Every setback contains the seeds of opportunity.",
            'emotion': "It's okay to feel this way - these feelings are fuel for positive change.",
            'action': "Let's turn this into a stepping stone toward something better."
        },
        'empathy': {
            'lens': 'Empathetic validation',
            'frame': lambda event: f"Your experience and feelings are completely valid.",
            'emotion': "I hear you. These emotions make complete sense given what you're going through.",
            'action': "Take the time you need to process this. What would feel supportive right now?"
        },
        'structure': {
            'lens': 'Analytical planning',
            'frame': lambda event: f"Let's break this down systematically.",
            'emotion': "Understanding the situation clearly will help manage these feelings.",
            'action': "Here's a structured approach: first assess, then plan, then act."
        },
        'depth': {
            'lens': 'Philosophical reflection',
            'frame': lambda event: f"This moment invites deeper contemplation.",
            'emotion': "Emotions are teachers - what is this feeling trying to show you?",
            'action': "Sit with this experience. Understanding often comes from patient reflection."
        },
        'action_oriented': {
            'lens': 'Action-focused momentum',
            'frame': lambda event: f"What matters now is the next step forward.",
            'emotion': "Channel this energy into movement. Action dissolves doubt.",
            'action': "Let's identify one concrete thing you can do right now."
        },
        'supportiveness': {
            'lens': 'Nurturing support',
            'frame': lambda event: f"You're not alone in this.",
            'emotion': "It's okay to lean on others. Seeking support is strength, not weakness.",
            'action': "Who in your life can you reach out to? What would help you feel supported?"
        },
        'directness': {
            'lens': 'Straightforward honesty',
            'frame': lambda event: f"Let me be direct with you about this.",
            'emotion': "These feelings are signals. Let's look at what they're really telling you.",
            'action': "Here's what I think you need to do - no sugarcoating."
        }
    }
    
    def __init__(self, db_connection: sqlite3.Connection, trait_system: CharacterTraitSystem):
        self.db = db_connection
        self.trait_system = trait_system
        self._init_tables()
    
    def _init_tables(self):
        """Create tables for multi-perspective interpretations"""
        cursor = self.db.cursor()
        
        # Check if table exists and needs migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='character_interpretations'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Migrate: add ALL potentially missing columns
            cursor.execute("PRAGMA table_info(character_interpretations)")
            existing_cols = {row[1] for row in cursor.fetchall()}
            
            migrations = {
                'user_id': 'ALTER TABLE character_interpretations ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0',
                'event_id': 'ALTER TABLE character_interpretations ADD COLUMN event_id TEXT NOT NULL DEFAULT ""',
                'event_text': 'ALTER TABLE character_interpretations ADD COLUMN event_text TEXT NOT NULL DEFAULT ""',
                'character_id': 'ALTER TABLE character_interpretations ADD COLUMN character_id TEXT NOT NULL DEFAULT ""',
                'interpretation_json': 'ALTER TABLE character_interpretations ADD COLUMN interpretation_json TEXT NOT NULL DEFAULT "{}"',
            }
            
            for col, sql in migrations.items():
                if col not in existing_cols:
                    cursor.execute(sql)
                    print(f"  ✓ Migrated: added {col} to character_interpretations")
        else:
            # Create fresh table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS character_interpretations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_id TEXT NOT NULL,
                    event_text TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    interpretation_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Index for quick lookups (only on columns that exist)
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_char_interp_user ON character_interpretations(user_id)')
        except Exception:
            pass
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_char_interp_event ON character_interpretations(event_id)')
        except Exception:
            pass
        
        self.db.commit()
    
    def _get_dominant_traits(self, character: CharacterProfile, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get character's top N most dominant traits"""
        traits = character.traits.to_dict()
        sorted_traits = sorted(traits.items(), key=lambda x: abs(x[1] - 0.5), reverse=True)
        # Return traits that are furthest from neutral (0.5)
        return [(name, value) for name, value in sorted_traits[:top_n]]
    
    def interpret_event_as_character(
        self, 
        event_text: str, 
        character: CharacterProfile,
        user_context: Dict = None
    ) -> CharacterInterpretation:
        """
        Generate a character-specific interpretation of an event.
        Uses the character's dominant traits to shape the interpretation.
        """
        dominant_traits = self._get_dominant_traits(character)
        
        # Find the most influential trait for interpretation
        primary_trait = dominant_traits[0][0] if dominant_traits else 'empathy'
        primary_value = dominant_traits[0][1] if dominant_traits else 0.5
        
        # Get interpretation template based on primary trait
        if primary_trait in self.TRAIT_INTERPRETATIONS:
            template = self.TRAIT_INTERPRETATIONS[primary_trait]
        else:
            # Default to empathy-based interpretation
            template = self.TRAIT_INTERPRETATIONS['empathy']
        
        # Build interpretation
        interpretation = template['frame'](event_text)
        
        # Modify based on secondary traits
        if len(dominant_traits) > 1:
            secondary_trait = dominant_traits[1][0]
            if secondary_trait in self.TRAIT_INTERPRETATIONS:
                secondary = self.TRAIT_INTERPRETATIONS[secondary_trait]
                # Blend the action suggestion
                interpretation += f" {secondary['action'][:50]}..."
        
        # Calculate confidence based on how extreme the dominant traits are
        trait_extremity = sum(abs(v - 0.5) for _, v in dominant_traits) / len(dominant_traits)
        confidence = min(0.5 + trait_extremity, 0.95)  # Higher extremity = higher confidence
        
        return CharacterInterpretation(
            character_id=character.character_id,
            character_name=character.display_name,
            interpretation=interpretation,
            emotional_framing=template['emotion'],
            action_suggestion=template['action'],
            philosophical_lens=character.philosophical_lens or template['lens'],
            dominant_traits=[t[0] for t in dominant_traits],
            confidence=confidence
        )
    
    def get_multi_perspective_interpretations(
        self,
        event_text: str,
        characters: List[CharacterProfile] = None,
        max_perspectives: int = 4
    ) -> List[CharacterInterpretation]:
        """
        Generate interpretations from multiple characters.
        If no characters specified, uses diverse selection from trait system.
        """
        if characters is None:
            # Select diverse characters based on trait coverage
            characters = self._select_diverse_characters(max_perspectives)
        
        interpretations = []
        for character in characters[:max_perspectives]:
            interp = self.interpret_event_as_character(event_text, character)
            interpretations.append(interp)
        
        return interpretations
    
    def _select_diverse_characters(self, count: int) -> List[CharacterProfile]:
        """Select characters that cover different trait spaces"""
        all_chars = list(self.trait_system.characters.values())
        
        if len(all_chars) <= count:
            return all_chars
        
        # Start with the character furthest from neutral
        selected = []
        remaining = all_chars.copy()
        
        # First, pick the most "extreme" character
        def trait_extremity(char):
            traits = char.traits.to_list()
            return sum(abs(t - 0.5) for t in traits)
        
        remaining.sort(key=trait_extremity, reverse=True)
        selected.append(remaining.pop(0))
        
        # Then pick characters that are most different from selected ones
        while len(selected) < count and remaining:
            best_char = None
            best_distance = -1
            
            for char in remaining:
                # Calculate minimum distance to any selected character
                min_dist = min(
                    char.traits.distance_to(s.traits) for s in selected
                )
                if min_dist > best_distance:
                    best_distance = min_dist
                    best_char = char
            
            if best_char:
                selected.append(best_char)
                remaining.remove(best_char)
        
        return selected
    
    def store_interpretations(
        self,
        user_id: int,
        event_id: str,
        event_text: str,
        interpretations: List[CharacterInterpretation]
    ):
        """Store multiple character interpretations for an event"""
        cursor = self.db.cursor()
        
        for interp in interpretations:
            cursor.execute('''
                INSERT INTO character_interpretations
                (user_id, event_id, event_text, character_id, interpretation_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                event_id,
                event_text,
                interp.character_id,
                json.dumps({
                    'character_name': interp.character_name,
                    'interpretation': interp.interpretation,
                    'emotional_framing': interp.emotional_framing,
                    'action_suggestion': interp.action_suggestion,
                    'philosophical_lens': interp.philosophical_lens,
                    'dominant_traits': interp.dominant_traits,
                    'confidence': interp.confidence
                })
            ))
        
        self.db.commit()
    
    def get_event_interpretations(
        self,
        user_id: int,
        event_id: str
    ) -> List[CharacterInterpretation]:
        """Retrieve all interpretations for a specific event"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT character_id, interpretation_json
            FROM character_interpretations
            WHERE user_id = ? AND event_id = ?
        ''', (user_id, event_id))
        
        interpretations = []
        for row in cursor.fetchall():
            data = json.loads(row[1])
            interpretations.append(CharacterInterpretation(
                character_id=row[0],
                character_name=data['character_name'],
                interpretation=data['interpretation'],
                emotional_framing=data['emotional_framing'],
                action_suggestion=data['action_suggestion'],
                philosophical_lens=data['philosophical_lens'],
                dominant_traits=data['dominant_traits'],
                confidence=data['confidence']
            ))
        
        return interpretations
    
    def get_user_interpretation_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent multi-perspective interpretations for a user"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT event_id, event_text, 
                   GROUP_CONCAT(character_id) as characters,
                   COUNT(*) as perspective_count,
                   MAX(created_at) as latest
            FROM character_interpretations
            WHERE user_id = ?
            GROUP BY event_id
            ORDER BY latest DESC
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'event_id': row[0],
                'event_text': row[1],
                'characters': row[2].split(',') if row[2] else [],
                'perspective_count': row[3],
                'timestamp': row[4]
            })
        
        return history


def create_character_specific_context(
    db_connection: sqlite3.Connection,
    trait_system: CharacterTraitSystem
) -> CharacterSpecificContext:
    """Factory function to create CharacterSpecificContext"""
    return CharacterSpecificContext(db_connection, trait_system)
