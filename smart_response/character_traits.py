"""
Character Trait System
Dynamic N-dimensional trait-space for character matching.
Characters are points in trait-space, matched to situations via distance calculation.

EXTENSIBILITY: To add new traits, simply add them to TRAIT_DEFINITIONS below.
All other code adapts automatically.
"""

import math
import json
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


# ============================================================
# TRAIT DEFINITIONS - Add new traits here for easy extension
# ============================================================
# Format: 'trait_name': {'default': 0.5, 'description': '...'}
# To extend from 12D to 30D, just add more entries here!

TRAIT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    'stoicism': {'default': 0.5, 'description': 'Emotional detachment vs emotional engagement'},
    'optimism': {'default': 0.5, 'description': 'Pessimistic vs optimistic outlook'},
    'directness': {'default': 0.5, 'description': 'Indirect/gentle vs direct/blunt communication'},
    'supportiveness': {'default': 0.5, 'description': 'Challenging vs supportive approach'},
    'structure': {'default': 0.5, 'description': 'Flexible/intuitive vs structured/methodical'},
    'depth': {'default': 0.5, 'description': 'Surface-level vs deep philosophical'},
    'formality': {'default': 0.5, 'description': 'Casual vs formal tone'},
    'verbosity': {'default': 0.5, 'description': 'Concise vs verbose responses'},
    'action_oriented': {'default': 0.5, 'description': 'Reflective vs action-focused'},
    'present_focus': {'default': 0.5, 'description': 'Past/future focused vs present focused'},
    'empathy': {'default': 0.5, 'description': 'Analytical vs empathetic'},
    'intensity': {'default': 0.5, 'description': 'Gentle/calm vs intense/passionate'},
    # === ADD NEW TRAITS BELOW THIS LINE ===
    # Example future traits (uncomment to activate):
    # 'humor': {'default': 0.5, 'description': 'Serious vs humorous approach'},
    # 'spirituality': {'default': 0.5, 'description': 'Secular vs spiritual perspective'},
    # 'creativity': {'default': 0.5, 'description': 'Conventional vs creative thinking'},
    # 'risk_tolerance': {'default': 0.5, 'description': 'Risk-averse vs risk-taking'},
}

# Derived list of trait names for iteration
TRAIT_NAMES = list(TRAIT_DEFINITIONS.keys())


class TraitVector:
    """
    Dynamic N-dimensional trait vector for character positioning.
    All values are 0.0 - 1.0 continuous scale.
    
    EXTENSIBILITY: Automatically adapts to TRAIT_DEFINITIONS.
    Add new traits there, and this class works with them automatically.
    """
    
    def __init__(self, **traits):
        """Initialize with trait values. Missing traits use defaults."""
        self._traits: Dict[str, float] = {}
        for trait_name, trait_info in TRAIT_DEFINITIONS.items():
            value = traits.get(trait_name, trait_info['default'])
            # Clamp to 0.0 - 1.0 range
            self._traits[trait_name] = max(0.0, min(1.0, float(value)))
    
    def __getattr__(self, name: str) -> float:
        """Allow attribute-style access: vector.stoicism"""
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._traits:
            return self._traits[name]
        raise AttributeError(f"'{type(self).__name__}' has no trait '{name}'")
    
    def __setattr__(self, name: str, value: float):
        """Allow attribute-style setting: vector.stoicism = 0.8"""
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in TRAIT_DEFINITIONS:
            self._traits[name] = max(0.0, min(1.0, float(value)))
        else:
            super().__setattr__(name, value)
    
    def to_list(self) -> List[float]:
        """Convert to list for distance calculations (ordered by TRAIT_NAMES)"""
        return [self._traits[name] for name in TRAIT_NAMES]
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return dict(self._traits)
    
    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> 'TraitVector':
        """Create TraitVector from dictionary"""
        return cls(**d)
    
    @classmethod
    def neutral(cls) -> 'TraitVector':
        """Create a neutral trait vector (all defaults)"""
        return cls()
    
    def distance_to(self, other: 'TraitVector', weights: Dict[str, float] = None) -> float:
        """Calculate weighted Euclidean distance to another trait vector"""
        if weights:
            weighted_sum = sum(
                weights.get(name, 1.0) * (self._traits[name] - other._traits[name]) ** 2
                for name in TRAIT_NAMES
            )
        else:
            weighted_sum = sum(
                (self._traits[name] - other._traits[name]) ** 2
                for name in TRAIT_NAMES
            )
        return math.sqrt(weighted_sum)
    
    def similarity_to(self, other: 'TraitVector') -> float:
        """Calculate similarity score (0-1, higher = more similar)"""
        max_distance = math.sqrt(len(TRAIT_NAMES))  # Max possible distance
        distance = self.distance_to(other)
        return 1.0 - (distance / max_distance)
    
    def get_dominant_traits(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """Get the most extreme traits (furthest from 0.5 neutral)"""
        extremity = [(name, abs(value - 0.5), value) for name, value in self._traits.items()]
        extremity.sort(key=lambda x: x[1], reverse=True)
        return [(name, value) for name, _, value in extremity[:top_n]]
    
    def __repr__(self) -> str:
        top_traits = self.get_dominant_traits(3)
        traits_str = ', '.join(f"{n}={v:.2f}" for n, v in top_traits)
        return f"TraitVector({traits_str}, ...)"


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
    Unified system for both base characters and domain characters.
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.db = db_connection
        self.characters = dict(BASE_CHARACTERS)  # Copy base characters
        self._init_tables()
        self._load_domain_characters()  # Load domain characters with trait vectors
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
    
    def _load_domain_characters(self):
        """Load domain characters from DOMAIN_CHARACTER_CONFIGS with their trait vectors"""
        try:
            from .characters.configs import DOMAIN_CHARACTER_CONFIGS
            
            cursor = self.db.cursor()
            
            for char_id, config in DOMAIN_CHARACTER_CONFIGS.items():
                # Skip if no trait_vector defined
                if 'trait_vector' not in config:
                    continue
                
                traits = TraitVector.from_dict(config['trait_vector'])
                domain = config.get('domain', 'general')
                display_name = config.get('display_name', char_id)
                description = config.get('description', '')
                
                # Use system_prompt first line as philosophical lens, or create one
                system_prompt = config.get('system_prompt', '')
                philosophical_lens = system_prompt.split('\n')[0] if system_prompt else f"Domain expert in {domain}"
                
                # Create CharacterProfile
                profile = CharacterProfile(
                    character_id=char_id,
                    display_name=display_name,
                    traits=traits,
                    domain=domain,
                    description=description,
                    philosophical_lens=philosophical_lens
                )
                
                # Add to in-memory characters
                self.characters[char_id] = profile
                
                # Save to DB (upsert)
                cursor.execute('''
                    INSERT OR REPLACE INTO character_library
                    (character_id, display_name, traits_json, domain, description, 
                     philosophical_lens, is_base)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                ''', (
                    char_id, display_name, json.dumps(traits.to_dict()),
                    domain, description, philosophical_lens
                ))
            
            self.db.commit()
            print(f"✓ Loaded {len(DOMAIN_CHARACTER_CONFIGS)} domain characters with trait vectors")
        except ImportError:
            print("⚠️ DOMAIN_CHARACTER_CONFIGS not found, skipping domain character loading")
        except Exception as e:
            print(f"⚠️ Error loading domain characters: {e}")
    
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
        
        # Detect goal type (order matters - more specific patterns first)
        # Venting: explicit requests to be heard without advice
        if re.search(r'(just need to vent|just want to vent|need someone to listen|just listen|hear me out)', message_lower):
            analysis.goal_type = 'venting'
            analysis.needs_validation = True
        # Learning: seeking understanding (check before advice since "help me understand" is learning)
        elif re.search(r'(understand why|explain why|why does|why do|why is|teach me|learn about|want to learn)', message_lower):
            analysis.goal_type = 'learning'
        # Advice: general help requests
        elif re.search(r'\b(help me|advice|suggest|recommend|what should)\b', message_lower):
            analysis.goal_type = 'advice'
        # Planning: structured approach requests
        elif re.search(r'\b(plan|steps|how to|strategy|approach)\b', message_lower):
            analysis.goal_type = 'planning'
        # Support: emotional validation
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
    
    # ============================================================
    # PHASE 5 ENHANCEMENTS
    # ============================================================
    
    # --- Enhancement 1: Personality-Based Character Matching ---
    
    # Mapping: Big5 personality traits → character trait weight adjustments
    # Higher weight = this trait matters MORE for this personality type
    BIG5_TO_TRAIT_WEIGHTS = {
        'openness': {
            'high': {'depth': 1.5, 'verbosity': 1.3, 'formality': 0.7},
            'low': {'structure': 1.4, 'action_oriented': 1.3, 'depth': 0.7}
        },
        'conscientiousness': {
            'high': {'structure': 1.5, 'action_oriented': 1.3, 'directness': 1.2},
            'low': {'supportiveness': 1.3, 'empathy': 1.2, 'structure': 0.7}
        },
        'extraversion': {
            'high': {'intensity': 1.4, 'optimism': 1.3, 'verbosity': 1.2},
            'low': {'stoicism': 1.3, 'depth': 1.3, 'intensity': 0.7}
        },
        'agreeableness': {
            'high': {'supportiveness': 1.5, 'empathy': 1.4, 'directness': 0.7},
            'low': {'directness': 1.5, 'stoicism': 1.3, 'supportiveness': 0.7}
        },
        'neuroticism': {
            'high': {'empathy': 1.5, 'supportiveness': 1.4, 'intensity': 0.6, 'stoicism': 0.7},
            'low': {'action_oriented': 1.3, 'directness': 1.2, 'intensity': 1.1}
        }
    }
    
    def personality_weighted_match(
        self, 
        situation: SituationAnalysis,
        personality: Dict[str, float],
        user_id: int = None,
        top_n: int = 3
    ) -> Dict:
        """
        Enhanced character matching that factors in user's Big5 personality.
        
        Args:
            situation: Analyzed user situation
            personality: Big5 traits dict {openness, conscientiousness, extraversion, agreeableness, neuroticism}
            user_id: Optional user ID for preference learning
            top_n: Number of alternatives to return
            
        Returns:
            Dict with best match, alternatives, reasoning, and personality influence details
        """
        ideal_traits = situation.get_ideal_traits()
        
        # Calculate personality-based trait weights
        trait_weights = self._compute_personality_weights(personality)
        
        # Get user preference bias (if user_id provided)
        preference_bias = {}
        if user_id:
            preference_bias = self._get_user_preference_bias(user_id)
        
        # Score all characters
        scored = []
        for char_id, profile in self.characters.items():
            # Weighted distance using personality-derived weights
            distance = profile.traits.distance_to(ideal_traits, weights=trait_weights)
            
            # Effectiveness adjustment (learned from outcomes)
            eff_factor = 1.0 - (profile.effectiveness_score * 0.2)
            adjusted_distance = distance * eff_factor
            
            # User preference bonus (reduces distance for preferred characters)
            pref_bonus = preference_bias.get(char_id, 0.0)
            adjusted_distance *= (1.0 - pref_bonus * 0.15)
            
            # Convert to similarity score
            max_distance = math.sqrt(sum(w for w in trait_weights.values()))
            similarity = max(0, 1.0 - (adjusted_distance / max_distance)) if max_distance > 0 else 0
            
            scored.append({
                'profile': profile,
                'similarity': similarity,
                'raw_distance': distance,
                'preference_bonus': pref_bonus
            })
        
        # Sort by similarity (highest first)
        scored.sort(key=lambda x: x['similarity'], reverse=True)
        
        best = scored[0]
        alternatives = scored[1:top_n + 1]
        
        # Generate enhanced reasoning
        reasoning = self._generate_enhanced_reasoning(
            situation, best['profile'], best['similarity'], 
            personality, trait_weights, preference_bias
        )
        
        # Log the recommendation
        if user_id:
            self._log_recommendation(user_id, best['profile'].character_id, 
                                     situation, best['similarity'], personality)
        
        # Describe personality influence
        personality_influence = self._describe_personality_influence(personality, trait_weights)
        
        return {
            'best_match': {
                'character': best['profile'].to_dict(),
                'similarity': round(best['similarity'], 3),
                'reasoning': reasoning
            },
            'alternatives': [
                {
                    'character': s['profile'].to_dict(),
                    'similarity': round(s['similarity'], 3),
                    'why_not_top': self._explain_alternative(s['profile'], best['profile'], situation)
                }
                for s in alternatives
            ],
            'personality_influence': personality_influence,
            'trait_weights_applied': {k: round(v, 2) for k, v in trait_weights.items()},
            'situation_summary': {
                'emotional_state': situation.emotional_state,
                'goal_type': situation.goal_type,
                'challenge_type': situation.challenge_type
            }
        }
    
    def _compute_personality_weights(self, personality: Dict[str, float]) -> Dict[str, float]:
        """Convert Big5 personality scores into trait matching weights"""
        weights = {name: 1.0 for name in TRAIT_NAMES}
        
        for big5_trait, score in personality.items():
            if big5_trait not in self.BIG5_TO_TRAIT_WEIGHTS:
                continue
            
            # Determine high/low
            level = 'high' if score > 0.6 else 'low' if score < 0.4 else None
            if not level:
                continue  # Neutral Big5 → no weight change
            
            adjustments = self.BIG5_TO_TRAIT_WEIGHTS[big5_trait].get(level, {})
            for trait_name, multiplier in adjustments.items():
                if trait_name in weights:
                    weights[trait_name] *= multiplier
        
        return weights
    
    def _describe_personality_influence(self, personality: Dict[str, float], 
                                        weights: Dict[str, float]) -> Dict:
        """Describe how personality influenced the matching weights"""
        influences = []
        for big5_trait, score in personality.items():
            if big5_trait not in self.BIG5_TO_TRAIT_WEIGHTS:
                continue
            level = 'high' if score > 0.6 else 'low' if score < 0.4 else 'neutral'
            if level == 'neutral':
                continue
            influences.append({
                'trait': big5_trait,
                'level': level,
                'score': round(score, 2),
                'effect': f"{'Increased' if level == 'high' else 'Decreased'} weight on "
                         f"{', '.join(self.BIG5_TO_TRAIT_WEIGHTS[big5_trait].get(level, {}).keys())}"
            })
        
        # Find most amplified and dampened traits
        amplified = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        dampened = sorted(weights.items(), key=lambda x: x[1])[:3]
        
        return {
            'personality_effects': influences,
            'most_weighted_traits': [{'trait': t, 'weight': round(w, 2)} for t, w in amplified],
            'least_weighted_traits': [{'trait': t, 'weight': round(w, 2)} for t, w in dampened]
        }
    
    def _generate_enhanced_reasoning(self, situation: SituationAnalysis,
                                      character: CharacterProfile, score: float,
                                      personality: Dict, weights: Dict,
                                      preference_bias: Dict) -> str:
        """Generate detailed reasoning incorporating personality"""
        parts = [f"Selected {character.display_name} (match: {score:.0%})"]
        
        if situation.emotional_state != 'neutral':
            parts.append(f"User seems {situation.emotional_state}")
        
        if situation.goal_type != 'general':
            parts.append(f"Goal: {situation.goal_type}")
        
        # Personality-specific reasoning
        personality_notes = []
        if personality.get('neuroticism', 0.5) > 0.6:
            personality_notes.append("high emotional sensitivity → prioritizing empathy")
        if personality.get('conscientiousness', 0.5) > 0.6:
            personality_notes.append("detail-oriented → prioritizing structure")
        if personality.get('extraversion', 0.5) < 0.4:
            personality_notes.append("introverted → prioritizing depth over intensity")
        if personality.get('agreeableness', 0.5) < 0.4:
            personality_notes.append("values directness → prioritizing honesty")
        if personality.get('openness', 0.5) > 0.6:
            personality_notes.append("open-minded → prioritizing depth")
        
        if personality_notes:
            parts.append(f"Personality: {'; '.join(personality_notes)}")
        
        # Preference note
        char_pref = preference_bias.get(character.character_id, 0)
        if char_pref > 0.3:
            parts.append(f"User has shown preference for this character")
        
        parts.append(f"Approach: {character.philosophical_lens}")
        
        return " | ".join(parts)
    
    def _explain_alternative(self, alt: CharacterProfile, best: CharacterProfile,
                             situation: SituationAnalysis) -> str:
        """Explain why an alternative wasn't the top pick"""
        ideal = situation.get_ideal_traits()
        alt_dom = alt.traits.get_dominant_traits(2)
        best_dom = best.traits.get_dominant_traits(2)
        
        alt_trait_names = [t[0] for t in alt_dom]
        best_trait_names = [t[0] for t in best_dom]
        
        unique_alt = [t for t in alt_trait_names if t not in best_trait_names]
        
        if unique_alt:
            return f"Strong in {', '.join(unique_alt)}, but {best.display_name} was closer to ideal profile"
        return f"Similar approach, but {best.display_name} had a slightly better trait alignment"
    
    # --- Enhancement 2: User Preference Learning ---
    
    def _init_preference_tables(self):
        """Create tables for user preference tracking (with migration support)"""
        cursor = self.db.cursor()
        
        # --- character_recommendations ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='character_recommendations'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(character_recommendations)")
            existing = {row[1] for row in cursor.fetchall()}
            migrations = {
                'user_id': 'ALTER TABLE character_recommendations ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0',
                'character_id': 'ALTER TABLE character_recommendations ADD COLUMN character_id TEXT NOT NULL DEFAULT ""',
                'match_score': 'ALTER TABLE character_recommendations ADD COLUMN match_score REAL',
                'situation_json': 'ALTER TABLE character_recommendations ADD COLUMN situation_json TEXT',
                'personality_json': 'ALTER TABLE character_recommendations ADD COLUMN personality_json TEXT',
                'was_accepted': 'ALTER TABLE character_recommendations ADD COLUMN was_accepted BOOLEAN DEFAULT NULL',
                'created_at': "ALTER TABLE character_recommendations ADD COLUMN created_at DATETIME DEFAULT ''",
            }
            for col, sql in migrations.items():
                if col not in existing:
                    cursor.execute(sql)
                    print(f"  ✓ Migrated: added {col} to character_recommendations")
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS character_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    character_id TEXT NOT NULL,
                    match_score REAL,
                    situation_json TEXT,
                    personality_json TEXT,
                    was_accepted BOOLEAN DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # --- user_character_preferences ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_character_preferences'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(user_character_preferences)")
            existing = {row[1] for row in cursor.fetchall()}
            migrations = {
                'user_id': 'ALTER TABLE user_character_preferences ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0',
                'character_id': 'ALTER TABLE user_character_preferences ADD COLUMN character_id TEXT NOT NULL DEFAULT ""',
                'preference_score': 'ALTER TABLE user_character_preferences ADD COLUMN preference_score REAL DEFAULT 0.5',
                'interaction_count': 'ALTER TABLE user_character_preferences ADD COLUMN interaction_count INTEGER DEFAULT 0',
                'avg_satisfaction': 'ALTER TABLE user_character_preferences ADD COLUMN avg_satisfaction REAL DEFAULT NULL',
                'last_interaction': 'ALTER TABLE user_character_preferences ADD COLUMN last_interaction DATETIME',
                'updated_at': "ALTER TABLE user_character_preferences ADD COLUMN updated_at DATETIME DEFAULT ''",
            }
            for col, sql in migrations.items():
                if col not in existing:
                    cursor.execute(sql)
                    print(f"  ✓ Migrated: added {col} to user_character_preferences")
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_character_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    character_id TEXT NOT NULL,
                    preference_score REAL DEFAULT 0.5,
                    interaction_count INTEGER DEFAULT 0,
                    avg_satisfaction REAL DEFAULT NULL,
                    last_interaction DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, character_id)
                )
            ''')
        
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_char_rec_user ON character_recommendations(user_id)')
        except Exception:
            pass
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_pref_user ON user_character_preferences(user_id)')
        except Exception:
            pass
        
        self.db.commit()
    
    def _log_recommendation(self, user_id: int, character_id: str,
                            situation: SituationAnalysis, match_score: float,
                            personality: Dict = None):
        """Log a character recommendation for preference learning"""
        cursor = self.db.cursor()
        try:
            cursor.execute('''
                INSERT INTO character_recommendations
                (user_id, character_id, match_score, situation_json, personality_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id, character_id, match_score,
                json.dumps({
                    'emotional_state': situation.emotional_state,
                    'goal_type': situation.goal_type,
                    'challenge_type': situation.challenge_type
                }),
                json.dumps(personality) if personality else None
            ))
            self.db.commit()
        except Exception as e:
            print(f"⚠️ Error logging recommendation: {e}")
    
    def record_character_interaction(self, user_id: int, character_id: str,
                                     satisfaction: float = None):
        """Record that a user interacted with a character (for preference learning)"""
        cursor = self.db.cursor()
        
        # Upsert preference record
        cursor.execute('''
            INSERT INTO user_character_preferences (user_id, character_id, interaction_count, last_interaction)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, character_id) DO UPDATE SET
                interaction_count = interaction_count + 1,
                last_interaction = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, character_id))
        
        if satisfaction is not None:
            # Update running average satisfaction
            cursor.execute('''
                UPDATE user_character_preferences 
                SET avg_satisfaction = CASE 
                    WHEN avg_satisfaction IS NULL THEN ?
                    ELSE (avg_satisfaction * (interaction_count - 1) + ?) / interaction_count
                END,
                preference_score = CASE
                    WHEN avg_satisfaction IS NULL THEN ? * 0.6 + 0.2
                    ELSE (avg_satisfaction * (interaction_count - 1) + ?) / interaction_count * 0.6 + 0.2
                END
                WHERE user_id = ? AND character_id = ?
            ''', (satisfaction, satisfaction, satisfaction, satisfaction, user_id, character_id))
        else:
            # Boost preference slightly for each interaction (frequency-based)
            cursor.execute('''
                UPDATE user_character_preferences
                SET preference_score = MIN(0.9, preference_score + 0.02)
                WHERE user_id = ? AND character_id = ?
            ''', (user_id, character_id))
        
        self.db.commit()
    
    def _get_user_preference_bias(self, user_id: int) -> Dict[str, float]:
        """Get user's character preference scores for matching bias"""
        cursor = self.db.cursor()
        try:
            cursor.execute('''
                SELECT character_id, preference_score
                FROM user_character_preferences
                WHERE user_id = ? AND interaction_count >= 2
            ''', (user_id,))
            
            return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception:
            return {}
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """Get detailed user preference data"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT character_id, preference_score, interaction_count, 
                   avg_satisfaction, last_interaction
            FROM user_character_preferences
            WHERE user_id = ?
            ORDER BY preference_score DESC
        ''', (user_id,))
        
        preferences = []
        for row in cursor.fetchall():
            char = self.characters.get(row[0])
            preferences.append({
                'character_id': row[0],
                'display_name': char.display_name if char else row[0],
                'preference_score': round(row[1], 3),
                'interaction_count': row[2],
                'avg_satisfaction': round(row[3], 2) if row[3] else None,
                'last_interaction': row[4]
            })
        
        # Recommendation history (last 10)
        cursor.execute('''
            SELECT character_id, match_score, situation_json, created_at
            FROM character_recommendations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        history = []
        for row in cursor.fetchall():
            char = self.characters.get(row[0])
            history.append({
                'character_id': row[0],
                'display_name': char.display_name if char else row[0],
                'match_score': round(row[1], 3) if row[1] else None,
                'situation': json.loads(row[2]) if row[2] else None,
                'timestamp': row[3]
            })
        
        return {
            'user_id': user_id,
            'preferences': preferences,
            'recommendation_history': history,
            'total_interactions': sum(p['interaction_count'] for p in preferences)
        }
    
    # --- Enhancement 3: Trait Space Coverage Analysis ---
    
    def analyze_trait_space_coverage(self) -> Dict:
        """
        Analyze the trait space to identify gaps and coverage quality.
        Returns regions that are well-covered and under-served.
        """
        if not self.characters:
            return {'error': 'No characters loaded'}
        
        all_traits = {name: [] for name in TRAIT_NAMES}
        
        # Collect trait values across all characters
        for profile in self.characters.values():
            traits_dict = profile.traits.to_dict()
            for name in TRAIT_NAMES:
                all_traits[name].append(traits_dict.get(name, 0.5))
        
        # Analyze per-trait coverage
        trait_analysis = {}
        for name, values in all_traits.items():
            avg = sum(values) / len(values)
            variance = sum((v - avg) ** 2 for v in values) / len(values)
            spread = math.sqrt(variance)
            min_val = min(values)
            max_val = max(values)
            
            # Check for gaps in coverage (no character near 0 or 1)
            has_low = any(v < 0.3 for v in values)
            has_high = any(v > 0.7 for v in values)
            has_extreme_low = any(v < 0.15 for v in values)
            has_extreme_high = any(v > 0.85 for v in values)
            
            coverage = 'excellent' if (has_extreme_low and has_extreme_high) else \
                       'good' if (has_low and has_high) else \
                       'moderate' if (has_low or has_high) else 'poor'
            
            trait_analysis[name] = {
                'mean': round(avg, 3),
                'spread': round(spread, 3),
                'range': [round(min_val, 2), round(max_val, 2)],
                'coverage': coverage,
                'gap_at_low': not has_low,
                'gap_at_high': not has_high
            }
        
        # Identify under-served regions
        gaps = []
        for name, analysis in trait_analysis.items():
            if analysis['gap_at_low']:
                gaps.append({
                    'trait': name,
                    'region': 'low (0.0 - 0.3)',
                    'suggestion': f"Need a character with low {name} ({TRAIT_DEFINITIONS[name]['description'].split(' vs ')[0]})"
                })
            if analysis['gap_at_high']:
                gaps.append({
                    'trait': name,
                    'region': 'high (0.7 - 1.0)',
                    'suggestion': f"Need a character with high {name} ({TRAIT_DEFINITIONS[name]['description'].split(' vs ')[-1]})"
                })
        
        # Overall coverage score (0-1)
        coverage_scores = {'excellent': 1.0, 'good': 0.75, 'moderate': 0.5, 'poor': 0.25}
        overall_score = sum(coverage_scores[a['coverage']] for a in trait_analysis.values()) / len(trait_analysis)
        
        # Character clustering - find characters that are too similar
        clusters = self._find_similar_characters(threshold=0.85)
        
        # Diversity score based on average pairwise distance
        diversity = self._calculate_diversity_score()
        
        return {
            'total_characters': len(self.characters),
            'trait_dimensions': len(TRAIT_NAMES),
            'overall_coverage_score': round(overall_score, 3),
            'diversity_score': round(diversity, 3),
            'trait_analysis': trait_analysis,
            'coverage_gaps': gaps,
            'similar_character_clusters': clusters,
            'recommendations': self._generate_coverage_recommendations(gaps, clusters, overall_score)
        }
    
    def _find_similar_characters(self, threshold: float = 0.85) -> List[Dict]:
        """Find character pairs that are very similar (potential redundancy)"""
        chars = list(self.characters.items())
        clusters = []
        
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                id1, p1 = chars[i]
                id2, p2 = chars[j]
                similarity = p1.traits.similarity_to(p2.traits)
                
                if similarity >= threshold:
                    clusters.append({
                        'character_1': {'id': id1, 'name': p1.display_name},
                        'character_2': {'id': id2, 'name': p2.display_name},
                        'similarity': round(similarity, 3),
                        'note': 'Very similar trait profiles - consider differentiating'
                    })
        
        return clusters
    
    def _calculate_diversity_score(self) -> float:
        """Calculate overall diversity score based on average pairwise distance"""
        chars = list(self.characters.values())
        if len(chars) < 2:
            return 0.0
        
        total_distance = 0.0
        pair_count = 0
        
        for i in range(len(chars)):
            for j in range(i + 1, len(chars)):
                total_distance += chars[i].traits.distance_to(chars[j].traits)
                pair_count += 1
        
        avg_distance = total_distance / pair_count if pair_count > 0 else 0
        max_possible = math.sqrt(len(TRAIT_NAMES))
        
        return avg_distance / max_possible if max_possible > 0 else 0
    
    def _generate_coverage_recommendations(self, gaps: List, clusters: List, 
                                            overall_score: float) -> List[str]:
        """Generate actionable recommendations for improving trait coverage"""
        recommendations = []
        
        if overall_score < 0.5:
            recommendations.append("Coverage is low. Consider adding characters with extreme trait values to fill gaps.")
        elif overall_score < 0.75:
            recommendations.append("Coverage is moderate. A few targeted character additions would help.")
        else:
            recommendations.append("Coverage is good. The character library is well-balanced.")
        
        if len(gaps) > 3:
            trait_names = list(set(g['trait'] for g in gaps))[:3]
            recommendations.append(
                f"Priority gaps in: {', '.join(trait_names)}. These traits lack extreme characters."
            )
        
        if clusters:
            similar_names = [f"{c['character_1']['name']} ↔ {c['character_2']['name']}" for c in clusters[:2]]
            recommendations.append(
                f"Similar pairs detected: {'; '.join(similar_names)}. Consider differentiating their traits."
            )
        
        return recommendations


def create_character_trait_system(db_connection: sqlite3.Connection) -> CharacterTraitSystem:
    """Factory function"""
    system = CharacterTraitSystem(db_connection)
    system._init_preference_tables()  # Initialize preference tracking tables
    return system
