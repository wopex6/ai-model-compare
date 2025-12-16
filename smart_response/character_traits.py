"""
Character Trait System
12-dimensional trait-space for dynamic character matching.
Characters are points in trait-space, matched to situations via distance calculation.
"""

import math
import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


@dataclass
class TraitVector:
    """
    12-dimensional trait vector for character positioning.
    All values are 0.0 - 1.0 continuous scale.
    """
    stoicism: float = 0.5        # Emotional detachment vs emotional engagement
    optimism: float = 0.5        # Pessimistic vs optimistic outlook
    directness: float = 0.5      # Indirect/gentle vs direct/blunt communication
    supportiveness: float = 0.5  # Challenging vs supportive approach
    structure: float = 0.5       # Flexible/intuitive vs structured/methodical
    depth: float = 0.5           # Surface-level vs deep philosophical
    formality: float = 0.5       # Casual vs formal tone
    verbosity: float = 0.5       # Concise vs verbose responses
    action_oriented: float = 0.5 # Reflective vs action-focused
    present_focus: float = 0.5   # Past/future focused vs present focused
    empathy: float = 0.5         # Analytical vs empathetic
    intensity: float = 0.5       # Gentle/calm vs intense/passionate
    
    def to_list(self) -> List[float]:
        """Convert to list for distance calculations"""
        return [
            self.stoicism, self.optimism, self.directness, self.supportiveness,
            self.structure, self.depth, self.formality, self.verbosity,
            self.action_oriented, self.present_focus, self.empathy, self.intensity
        ]
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'stoicism': self.stoicism, 'optimism': self.optimism,
            'directness': self.directness, 'supportiveness': self.supportiveness,
            'structure': self.structure, 'depth': self.depth,
            'formality': self.formality, 'verbosity': self.verbosity,
            'action_oriented': self.action_oriented, 'present_focus': self.present_focus,
            'empathy': self.empathy, 'intensity': self.intensity
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> 'TraitVector':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
    
    def distance_to(self, other: 'TraitVector', weights: Dict[str, float] = None) -> float:
        """Calculate weighted Euclidean distance to another trait vector"""
        self_list = self.to_list()
        other_list = other.to_list()
        
        trait_names = list(self.to_dict().keys())
        
        if weights:
            weighted_sum = sum(
                weights.get(trait_names[i], 1.0) * (self_list[i] - other_list[i]) ** 2
                for i in range(len(self_list))
            )
        else:
            weighted_sum = sum((a - b) ** 2 for a, b in zip(self_list, other_list))
        
        return math.sqrt(weighted_sum)


@dataclass
class CharacterProfile:
    """Complete character profile with traits and metadata"""
    character_id: str
    display_name: str
    traits: TraitVector
    domain: str = "general"
    description: str = ""
    philosophical_lens: str = ""  # How they interpret situations
    effectiveness_score: float = 0.5  # Learned from outcomes
    usage_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'character_id': self.character_id,
            'display_name': self.display_name,
            'traits': self.traits.to_dict(),
            'domain': self.domain,
            'description': self.description,
            'philosophical_lens': self.philosophical_lens,
            'effectiveness_score': self.effectiveness_score,
            'usage_count': self.usage_count
        }


@dataclass
class SituationAnalysis:
    """Analysis of current user situation for character matching"""
    emotional_state: str = "neutral"  # calm, stressed, anxious, excited, sad, angry
    emotional_intensity: float = 0.5  # 0-1 scale
    goal_type: str = "general"        # advice, support, planning, venting, learning
    challenge_type: str = "none"      # work, relationship, health, finance, personal
    urgency: float = 0.5              # 0-1 scale
    complexity: float = 0.5           # 0-1 scale
    user_energy: float = 0.5          # Low energy vs high energy
    needs_action: bool = False        # Does user need actionable steps?
    needs_validation: bool = False    # Does user need emotional validation?
    
    def get_ideal_traits(self) -> TraitVector:
        """Calculate ideal trait vector for this situation"""
        # Start with balanced defaults
        ideal = TraitVector()
        
        # Emotional state adjustments
        if self.emotional_state in ('stressed', 'anxious', 'sad'):
            ideal.empathy = 0.8
            ideal.supportiveness = 0.8
            ideal.intensity = 0.3
            ideal.stoicism = 0.3
        elif self.emotional_state == 'angry':
            ideal.stoicism = 0.7
            ideal.empathy = 0.7
            ideal.directness = 0.4  # More gentle
        elif self.emotional_state == 'excited':
            ideal.optimism = 0.8
            ideal.intensity = 0.7
        
        # Goal type adjustments
        if self.goal_type == 'support':
            ideal.supportiveness = 0.9
            ideal.empathy = 0.9
            ideal.action_oriented = 0.3
        elif self.goal_type == 'planning':
            ideal.structure = 0.8
            ideal.action_oriented = 0.8
            ideal.depth = 0.6
        elif self.goal_type == 'venting':
            ideal.empathy = 0.9
            ideal.supportiveness = 0.9
            ideal.directness = 0.2
            ideal.action_oriented = 0.2
        elif self.goal_type == 'advice':
            ideal.directness = 0.7
            ideal.structure = 0.7
            ideal.action_oriented = 0.7
        elif self.goal_type == 'learning':
            ideal.depth = 0.8
            ideal.structure = 0.7
            ideal.verbosity = 0.7
        
        # Urgency adjustments
        if self.urgency > 0.7:
            ideal.directness = max(ideal.directness, 0.7)
            ideal.action_oriented = max(ideal.action_oriented, 0.8)
            ideal.verbosity = min(ideal.verbosity, 0.4)
        
        # Complexity adjustments
        if self.complexity > 0.7:
            ideal.depth = max(ideal.depth, 0.7)
            ideal.structure = max(ideal.structure, 0.7)
        
        # User energy adjustments
        if self.user_energy < 0.3:
            ideal.verbosity = min(ideal.verbosity, 0.4)
            ideal.intensity = min(ideal.intensity, 0.4)
        
        # Validation needs
        if self.needs_validation:
            ideal.empathy = max(ideal.empathy, 0.8)
            ideal.supportiveness = max(ideal.supportiveness, 0.8)
        
        # Action needs
        if self.needs_action:
            ideal.action_oriented = max(ideal.action_oriented, 0.8)
            ideal.structure = max(ideal.structure, 0.7)
        
        return ideal


# Pre-defined base characters with their trait vectors
BASE_CHARACTERS = {
    'stoic': CharacterProfile(
        character_id='stoic',
        display_name='The Stoic',
        traits=TraitVector(
            stoicism=0.9, optimism=0.5, directness=0.7, supportiveness=0.4,
            structure=0.6, depth=0.8, formality=0.6, verbosity=0.4,
            action_oriented=0.6, present_focus=0.8, empathy=0.4, intensity=0.3
        ),
        domain='mental_health',
        description='Calm, rational perspective. Focuses on what you can control.',
        philosophical_lens='Setbacks are tests of character. Focus on your response, not the event.'
    ),
    'coach': CharacterProfile(
        character_id='coach',
        display_name='The Coach',
        traits=TraitVector(
            stoicism=0.3, optimism=0.8, directness=0.8, supportiveness=0.6,
            structure=0.8, depth=0.5, formality=0.4, verbosity=0.5,
            action_oriented=0.9, present_focus=0.7, empathy=0.5, intensity=0.7
        ),
        domain='work',
        description='Action-focused motivator. Turns problems into goals.',
        philosophical_lens='Every setback is a learning opportunity. What can you do next?'
    ),
    'sage': CharacterProfile(
        character_id='sage',
        display_name='The Sage',
        traits=TraitVector(
            stoicism=0.6, optimism=0.6, directness=0.4, supportiveness=0.5,
            structure=0.4, depth=0.9, formality=0.5, verbosity=0.7,
            action_oriented=0.3, present_focus=0.5, empathy=0.6, intensity=0.4
        ),
        domain='learning',
        description='Deep thinker. Offers wisdom and broader perspective.',
        philosophical_lens='Life flows naturally. Accept what is, understand the deeper meaning.'
    ),
    'therapist': CharacterProfile(
        character_id='therapist',
        display_name='The Therapist',
        traits=TraitVector(
            stoicism=0.2, optimism=0.6, directness=0.3, supportiveness=0.9,
            structure=0.5, depth=0.7, formality=0.5, verbosity=0.6,
            action_oriented=0.4, present_focus=0.6, empathy=0.9, intensity=0.3
        ),
        domain='mental_health',
        description='Empathetic listener. Validates emotions and explores patterns.',
        philosophical_lens='Your feelings are valid. Let\'s understand what this means for you.'
    ),
    'strategist': CharacterProfile(
        character_id='strategist',
        display_name='The Strategist',
        traits=TraitVector(
            stoicism=0.6, optimism=0.5, directness=0.7, supportiveness=0.4,
            structure=0.9, depth=0.6, formality=0.6, verbosity=0.5,
            action_oriented=0.8, present_focus=0.4, empathy=0.3, intensity=0.5
        ),
        domain='finance',
        description='Analytical planner. Breaks down complex problems systematically.',
        philosophical_lens='Every problem has a solution. Let\'s find the optimal path.'
    ),
    'cheerleader': CharacterProfile(
        character_id='cheerleader',
        display_name='The Cheerleader',
        traits=TraitVector(
            stoicism=0.1, optimism=0.9, directness=0.5, supportiveness=0.9,
            structure=0.3, depth=0.3, formality=0.2, verbosity=0.6,
            action_oriented=0.6, present_focus=0.8, empathy=0.7, intensity=0.8
        ),
        domain='relationships',
        description='Enthusiastic supporter. Celebrates wins and encourages action.',
        philosophical_lens='You\'ve got this! Every step forward counts!'
    ),
    'mentor': CharacterProfile(
        character_id='mentor',
        display_name='The Mentor',
        traits=TraitVector(
            stoicism=0.5, optimism=0.7, directness=0.6, supportiveness=0.7,
            structure=0.6, depth=0.7, formality=0.5, verbosity=0.6,
            action_oriented=0.7, present_focus=0.5, empathy=0.6, intensity=0.5
        ),
        domain='learning',
        description='Experienced guide. Shares wisdom from experience.',
        philosophical_lens='I\'ve been there. Let me share what I\'ve learned.'
    ),
    'realist': CharacterProfile(
        character_id='realist',
        display_name='The Realist',
        traits=TraitVector(
            stoicism=0.7, optimism=0.4, directness=0.8, supportiveness=0.3,
            structure=0.7, depth=0.5, formality=0.5, verbosity=0.4,
            action_oriented=0.7, present_focus=0.7, empathy=0.3, intensity=0.5
        ),
        domain='finance',
        description='Practical truth-teller. Focuses on facts and realistic options.',
        philosophical_lens='Let\'s look at this objectively. What are the real options?'
    ),
}


class CharacterTraitSystem:
    """
    Manages character trait matching and effectiveness learning.
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self.characters = dict(BASE_CHARACTERS)  # Copy base characters
        self._init_tables()
        self._load_custom_characters()
    
    def _init_tables(self):
        """Create tables for character trait storage and effectiveness tracking"""
        cursor = self.db.cursor()
        
        # Character library (custom/expanded characters)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_library (
                character_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                traits_json TEXT NOT NULL,
                domain TEXT DEFAULT 'general',
                description TEXT,
                philosophical_lens TEXT,
                effectiveness_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                is_base BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Track character usage outcomes for learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_usage_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                situation_json TEXT,
                conversation_length INTEGER,
                user_satisfaction REAL,
                goal_achieved BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Situation analysis cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS situation_analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                analysis_json TEXT NOT NULL,
                matched_character TEXT,
                match_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_char_outcomes_user ON character_usage_outcomes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_char_outcomes_char ON character_usage_outcomes(character_id)')
        
        self.db.commit()
        
        # Save base characters to DB if not exists
        for char_id, profile in BASE_CHARACTERS.items():
            cursor.execute('''
                INSERT OR IGNORE INTO character_library
                (character_id, display_name, traits_json, domain, description, 
                 philosophical_lens, is_base)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (
                char_id, profile.display_name, json.dumps(profile.traits.to_dict()),
                profile.domain, profile.description, profile.philosophical_lens
            ))
        self.db.commit()
    
    def _load_custom_characters(self):
        """Load custom characters from DB"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT character_id, display_name, traits_json, domain, description,
                   philosophical_lens, effectiveness_score, usage_count
            FROM character_library WHERE is_base = 0
        ''')
        
        for row in cursor.fetchall():
            traits = TraitVector.from_dict(json.loads(row[2]))
            self.characters[row[0]] = CharacterProfile(
                character_id=row[0],
                display_name=row[1],
                traits=traits,
                domain=row[3],
                description=row[4],
                philosophical_lens=row[5],
                effectiveness_score=row[6],
                usage_count=row[7]
            )
    
    def analyze_situation(self, message: str, user_context: Dict = None) -> SituationAnalysis:
        """Analyze the user's message to understand their situation"""
        import re
        message_lower = message.lower()
        
        analysis = SituationAnalysis()
        
        # Detect emotional state
        emotion_patterns = {
            'stressed': [r'\b(stressed|overwhelmed|pressure|too much)\b'],
            'anxious': [r'\b(anxious|worried|nervous|scared|afraid)\b'],
            'sad': [r'\b(sad|depressed|down|lonely|hopeless)\b'],
            'angry': [r'\b(angry|frustrated|annoyed|furious|pissed)\b'],
            'excited': [r'\b(excited|thrilled|happy|great|amazing)\b'],
        }
        
        for emotion, patterns in emotion_patterns.items():
            if any(re.search(p, message_lower) for p in patterns):
                analysis.emotional_state = emotion
                break
        
        # Detect intensity
        intensity_words = [r'\b(very|really|extremely|so|incredibly|absolutely)\b']
        if any(re.search(p, message_lower) for p in intensity_words):
            analysis.emotional_intensity = 0.8
        
        # Detect goal type
        if re.search(r'\b(help me|advice|suggest|recommend|what should)\b', message_lower):
            analysis.goal_type = 'advice'
        elif re.search(r'\b(plan|steps|how to|strategy|approach)\b', message_lower):
            analysis.goal_type = 'planning'
        elif re.search(r'\b(just need to vent|listen|understand|hear me)\b', message_lower):
            analysis.goal_type = 'venting'
            analysis.needs_validation = True
        elif re.search(r'\b(learn|understand|explain|teach|why)\b', message_lower):
            analysis.goal_type = 'learning'
        elif re.search(r'\b(support|comfort|feeling|emotions?)\b', message_lower):
            analysis.goal_type = 'support'
            analysis.needs_validation = True
        
        # Detect challenge type
        challenge_patterns = {
            'work': [r'\b(work|job|boss|career|office|colleague|deadline)\b'],
            'relationship': [r'\b(relationship|partner|friend|family|spouse|dating)\b'],
            'health': [r'\b(health|fitness|sleep|energy|tired|sick)\b'],
            'finance': [r'\b(money|budget|debt|savings|financial|afford)\b'],
            'personal': [r'\b(myself|self|identity|purpose|meaning)\b'],
        }
        
        for challenge, patterns in challenge_patterns.items():
            if any(re.search(p, message_lower) for p in patterns):
                analysis.challenge_type = challenge
                break
        
        # Detect urgency
        if re.search(r'\b(urgent|asap|immediately|right now|today|deadline)\b', message_lower):
            analysis.urgency = 0.9
        elif re.search(r'\b(soon|quickly|fast)\b', message_lower):
            analysis.urgency = 0.7
        
        # Detect action needs
        if re.search(r'\b(do|action|steps|next|plan|start|begin)\b', message_lower):
            analysis.needs_action = True
        
        # Adjust based on user context
        if user_context:
            # If user has expressed brevity preference
            if user_context.get('user_language', {}).get('preferred_length') in ('brief', 'very_brief'):
                analysis.user_energy = 0.4  # Assume lower energy / less patience
        
        return analysis
    
    def match_character(self, situation: SituationAnalysis, 
                       user_history: Dict = None) -> Tuple[CharacterProfile, float, str]:
        """
        Find the best matching character for the given situation.
        
        Returns:
            (best_character, match_score, reasoning)
        """
        ideal_traits = situation.get_ideal_traits()
        
        # Calculate distances to all characters
        matches = []
        for char_id, profile in self.characters.items():
            distance = profile.traits.distance_to(ideal_traits)
            
            # Adjust by effectiveness score (learned from outcomes)
            adjusted_score = distance * (1 - profile.effectiveness_score * 0.2)
            
            matches.append((profile, adjusted_score, distance))
        
        # Sort by adjusted score (lower is better)
        matches.sort(key=lambda x: x[1])
        
        best = matches[0][0]
        raw_distance = matches[0][2]
        
        # Convert distance to similarity score (0-1, higher is better)
        # Max possible distance in 12D unit space is sqrt(12) ≈ 3.46
        similarity = max(0, 1 - (raw_distance / 3.46))
        
        # Generate reasoning
        reasoning = self._generate_match_reasoning(situation, best, similarity)
        
        return best, similarity, reasoning
    
    def _generate_match_reasoning(self, situation: SituationAnalysis, 
                                  character: CharacterProfile, score: float) -> str:
        """Generate human-readable reasoning for the character match"""
        parts = [f"Selected {character.display_name} (match: {score:.0%})"]
        
        if situation.emotional_state != 'neutral':
            parts.append(f"User seems {situation.emotional_state}")
        
        if situation.goal_type != 'general':
            parts.append(f"Goal type: {situation.goal_type}")
        
        if situation.needs_validation:
            parts.append("User needs emotional validation")
        
        if situation.needs_action:
            parts.append("User needs actionable steps")
        
        parts.append(f"Character approach: {character.philosophical_lens}")
        
        return " | ".join(parts)
    
    def record_outcome(self, user_id: int, character_id: str, 
                      situation: SituationAnalysis, 
                      conversation_length: int,
                      satisfaction: float = None,
                      goal_achieved: bool = None):
        """Record the outcome of a character interaction for learning"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO character_usage_outcomes
            (user_id, character_id, situation_json, conversation_length,
             user_satisfaction, goal_achieved)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, character_id, json.dumps({
                'emotional_state': situation.emotional_state,
                'goal_type': situation.goal_type,
                'challenge_type': situation.challenge_type
            }),
            conversation_length, satisfaction, goal_achieved
        ))
        
        # Update usage count
        cursor.execute('''
            UPDATE character_library 
            SET usage_count = usage_count + 1, updated_at = CURRENT_TIMESTAMP
            WHERE character_id = ?
        ''', (character_id,))
        
        self.db.commit()
        
        # Recalculate effectiveness if we have enough data
        self._update_effectiveness(character_id)
    
    def _update_effectiveness(self, character_id: str):
        """Update character effectiveness based on outcome history"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT AVG(user_satisfaction), AVG(CASE WHEN goal_achieved THEN 1.0 ELSE 0.0 END),
                   AVG(conversation_length), COUNT(*)
            FROM character_usage_outcomes
            WHERE character_id = ? AND user_satisfaction IS NOT NULL
        ''', (character_id,))
        
        row = cursor.fetchone()
        if row and row[3] >= 5:  # Minimum 5 interactions for reliability
            avg_satisfaction = row[0] or 0.5
            avg_goal = row[1] or 0.5
            
            # Weighted effectiveness score
            effectiveness = avg_satisfaction * 0.6 + avg_goal * 0.4
            
            cursor.execute('''
                UPDATE character_library
                SET effectiveness_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE character_id = ?
            ''', (effectiveness, character_id))
            
            self.db.commit()
            
            # Update in-memory cache
            if character_id in self.characters:
                self.characters[character_id].effectiveness_score = effectiveness
    
    def get_character(self, character_id: str) -> Optional[CharacterProfile]:
        """Get a character by ID"""
        return self.characters.get(character_id)
    
    def get_all_characters(self) -> List[CharacterProfile]:
        """Get all available characters"""
        return list(self.characters.values())
    
    def get_characters_for_domain(self, domain: str) -> List[CharacterProfile]:
        """Get characters specialized for a domain"""
        return [c for c in self.characters.values() if c.domain == domain]


def create_character_trait_system(db_connection: sqlite3.Connection) -> CharacterTraitSystem:
    """Factory function"""
    return CharacterTraitSystem(db_connection)
