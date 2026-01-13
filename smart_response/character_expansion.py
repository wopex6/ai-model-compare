"""
Character Expansion System
===========================
Identifies gaps in character trait-space coverage and generates new characters
to fill those gaps using AI (strictly budget-controlled).

Key Features:
- Gap detection in 12D trait-space
- AI-powered character generation (max 10 calls/day for background tasks)
- New characters based on historical/theoretical figures
- Automatic integration with CharacterTraitSystem
"""

import sqlite3
import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Import from character_traits module
try:
    from smart_response.character_traits import (
        TraitVector, CharacterProfile, CharacterTraitSystem, BASE_CHARACTERS
    )
except ImportError:
    from character_traits import (
        TraitVector, CharacterProfile, CharacterTraitSystem, BASE_CHARACTERS
    )


@dataclass
class TraitSpaceGap:
    """Represents a gap in trait-space that needs filling"""
    centroid: TraitVector  # Center point of the gap
    gap_score: float       # How severe the gap is (0-1)
    nearest_character: str # ID of nearest existing character
    nearest_distance: float
    recommended_traits: Dict[str, str]  # Human-readable trait recommendations
    situation_types: List[str]  # What situations this gap affects


@dataclass 
class CharacterCandidate:
    """A candidate character to fill a gap"""
    name: str
    inspiration: str  # Historical/theoretical figure that inspired this
    traits: TraitVector
    domain: str
    description: str
    philosophical_lens: str
    gap_filled: TraitSpaceGap


class CharacterExpansionSystem:
    """
    Manages character library expansion through gap detection and AI generation.
    
    Budget Control:
    - Maximum 10 AI calls per day for background character expansion
    - Requires approval from AIBudgetManager before any generation
    - All operations logged for audit
    """
    
    # Famous figures that can inspire new characters
    INSPIRATION_SOURCES = [
        # Philosophers
        {"name": "Marcus Aurelius", "domain": "mental_health", "style": "stoic emperor"},
        {"name": "Socrates", "domain": "learning", "style": "questioning teacher"},
        {"name": "Confucius", "domain": "relationships", "style": "wise harmonizer"},
        {"name": "Buddha", "domain": "mental_health", "style": "mindful guide"},
        {"name": "Aristotle", "domain": "learning", "style": "systematic thinker"},
        
        # Psychologists/Therapists
        {"name": "Carl Rogers", "domain": "mental_health", "style": "unconditional positive regard"},
        {"name": "Viktor Frankl", "domain": "mental_health", "style": "meaning-focused"},
        {"name": "Brené Brown", "domain": "relationships", "style": "vulnerability expert"},
        
        # Business/Leadership
        {"name": "Peter Drucker", "domain": "work", "style": "effective manager"},
        {"name": "Simon Sinek", "domain": "work", "style": "purpose-driven leader"},
        {"name": "Warren Buffett", "domain": "finance", "style": "patient investor"},
        
        # Creatives
        {"name": "Leonardo da Vinci", "domain": "creativity", "style": "renaissance polymath"},
        {"name": "Maya Angelou", "domain": "creativity", "style": "wise storyteller"},
        
        # Health/Wellness
        {"name": "Hippocrates", "domain": "physical_health", "style": "holistic healer"},
        {"name": "Wim Hof", "domain": "physical_health", "style": "extreme wellness"},
    ]
    
    def __init__(self, db_connection: sqlite3.Connection, ai_budget_manager=None):
        self.db = db_connection
        self.ai_budget = ai_budget_manager
        self._init_tables()
        
    def _init_tables(self):
        """Create tables for expansion tracking"""
        cursor = self.db.cursor()
        
        # Track gap analysis results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trait_space_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gap_json TEXT NOT NULL,
                gap_score REAL NOT NULL,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                filled_by TEXT,  -- character_id if filled
                filled_at DATETIME
            )
        ''')
        
        # Track character generation attempts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_generation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gap_id INTEGER,
                inspiration_source TEXT,
                generated_character_json TEXT,
                ai_tokens_used INTEGER,
                success BOOLEAN,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gap_id) REFERENCES trait_space_gaps(id)
            )
        ''')
        
        self.db.commit()
    
    def analyze_trait_space_coverage(self, character_system: CharacterTraitSystem) -> List[TraitSpaceGap]:
        """
        Analyze current trait-space coverage and identify gaps.
        
        Uses a grid-based approach to sample the 12D space and find areas
        where no existing character provides good coverage.
        """
        gaps = []
        characters = character_system.get_all_characters()
        
        if len(characters) < 3:
            print("⚠️ Not enough characters for gap analysis")
            return gaps
        
        # Sample key points in trait-space that represent common user needs
        sample_situations = self._get_sample_situations()
        
        for situation_name, ideal_traits in sample_situations.items():
            # Find nearest character to this ideal
            min_distance = float('inf')
            nearest_char = None
            
            for char in characters:
                dist = char.traits.distance_to(ideal_traits)
                if dist < min_distance:
                    min_distance = dist
                    nearest_char = char
            
            # If nearest character is too far, we have a gap
            # Threshold: distance > 1.5 in 12D space indicates significant gap
            if min_distance > 1.5:
                gap_score = min(1.0, (min_distance - 1.5) / 2.0)  # Normalize to 0-1
                
                gap = TraitSpaceGap(
                    centroid=ideal_traits,
                    gap_score=gap_score,
                    nearest_character=nearest_char.character_id if nearest_char else "none",
                    nearest_distance=min_distance,
                    recommended_traits=self._describe_traits(ideal_traits),
                    situation_types=[situation_name]
                )
                gaps.append(gap)
        
        # Sort by gap severity
        gaps.sort(key=lambda g: g.gap_score, reverse=True)
        
        # Store gaps in database
        cursor = self.db.cursor()
        for gap in gaps:
            cursor.execute('''
                INSERT INTO trait_space_gaps (gap_json, gap_score)
                VALUES (?, ?)
            ''', (json.dumps({
                'centroid': gap.centroid.to_dict(),
                'situation_types': gap.situation_types,
                'recommended_traits': gap.recommended_traits
            }), gap.gap_score))
        self.db.commit()
        
        return gaps
    
    def _get_sample_situations(self) -> Dict[str, TraitVector]:
        """Generate sample situations that represent common user needs"""
        return {
            # High empathy, low action (pure emotional support)
            'emotional_crisis': TraitVector(
                stoicism=0.1, optimism=0.4, directness=0.2, supportiveness=0.95,
                structure=0.2, depth=0.6, formality=0.3, verbosity=0.5,
                action_oriented=0.1, present_focus=0.9, empathy=0.95, intensity=0.3
            ),
            # High structure, high action (crisis management)
            'urgent_problem': TraitVector(
                stoicism=0.7, optimism=0.5, directness=0.9, supportiveness=0.4,
                structure=0.9, depth=0.4, formality=0.6, verbosity=0.3,
                action_oriented=0.95, present_focus=0.9, empathy=0.3, intensity=0.7
            ),
            # High depth, low action (philosophical exploration)
            'existential_question': TraitVector(
                stoicism=0.5, optimism=0.5, directness=0.4, supportiveness=0.5,
                structure=0.3, depth=0.95, formality=0.5, verbosity=0.8,
                action_oriented=0.2, present_focus=0.3, empathy=0.6, intensity=0.4
            ),
            # High optimism, high intensity (celebration/motivation)
            'celebration_moment': TraitVector(
                stoicism=0.1, optimism=0.95, directness=0.6, supportiveness=0.8,
                structure=0.3, depth=0.3, formality=0.2, verbosity=0.6,
                action_oriented=0.7, present_focus=0.8, empathy=0.7, intensity=0.9
            ),
            # Balanced with high structure (methodical learning)
            'skill_development': TraitVector(
                stoicism=0.5, optimism=0.6, directness=0.6, supportiveness=0.6,
                structure=0.85, depth=0.7, formality=0.5, verbosity=0.6,
                action_oriented=0.7, present_focus=0.5, empathy=0.4, intensity=0.5
            ),
            # High empathy, moderate action (relationship guidance)
            'relationship_conflict': TraitVector(
                stoicism=0.3, optimism=0.5, directness=0.5, supportiveness=0.8,
                structure=0.5, depth=0.7, formality=0.4, verbosity=0.6,
                action_oriented=0.5, present_focus=0.6, empathy=0.85, intensity=0.4
            ),
            # Low verbosity, high directness (quick decisions)
            'quick_decision': TraitVector(
                stoicism=0.6, optimism=0.5, directness=0.9, supportiveness=0.4,
                structure=0.7, depth=0.3, formality=0.5, verbosity=0.2,
                action_oriented=0.9, present_focus=0.8, empathy=0.3, intensity=0.6
            ),
            # High formality, high depth (professional mentoring)
            'career_guidance': TraitVector(
                stoicism=0.5, optimism=0.6, directness=0.7, supportiveness=0.6,
                structure=0.7, depth=0.7, formality=0.8, verbosity=0.5,
                action_oriented=0.7, present_focus=0.4, empathy=0.5, intensity=0.5
            ),
        }
    
    def _describe_traits(self, traits: TraitVector) -> Dict[str, str]:
        """Convert trait vector to human-readable descriptions"""
        descriptions = {}
        
        trait_descriptions = {
            'stoicism': ('emotionally engaged', 'emotionally detached'),
            'optimism': ('realistic/cautious', 'optimistic/hopeful'),
            'directness': ('gentle/indirect', 'direct/blunt'),
            'supportiveness': ('challenging', 'supportive'),
            'structure': ('flexible/intuitive', 'structured/methodical'),
            'depth': ('practical/surface', 'deep/philosophical'),
            'formality': ('casual', 'formal'),
            'verbosity': ('concise', 'detailed'),
            'action_oriented': ('reflective', 'action-focused'),
            'present_focus': ('future/past focused', 'present focused'),
            'empathy': ('analytical', 'empathetic'),
            'intensity': ('calm/gentle', 'intense/passionate'),
        }
        
        trait_dict = traits.to_dict()
        for trait_name, (low_desc, high_desc) in trait_descriptions.items():
            value = trait_dict[trait_name]
            if value < 0.3:
                descriptions[trait_name] = f"Very {low_desc}"
            elif value < 0.45:
                descriptions[trait_name] = f"Somewhat {low_desc}"
            elif value > 0.7:
                descriptions[trait_name] = f"Very {high_desc}"
            elif value > 0.55:
                descriptions[trait_name] = f"Somewhat {high_desc}"
            else:
                descriptions[trait_name] = "Balanced"
        
        return descriptions
    
    def generate_character_for_gap(self, gap: TraitSpaceGap, 
                                   ai_generate_func=None) -> Optional[CharacterCandidate]:
        """
        Generate a new character to fill a trait-space gap.
        
        Args:
            gap: The gap to fill
            ai_generate_func: Optional AI function for generating character details
                             If None, uses template-based generation
        
        Returns:
            CharacterCandidate if successful, None if budget exceeded or failed
        """
        # Check budget if AI generation requested (system call - suppress notifications)
        if ai_generate_func and self.ai_budget:
            allowed, reason = self.ai_budget.can_make_ai_call(
                user_id=0,  # System call
                is_admin=True,  # System calls use admin limits
                is_background=True,  # Background task
                suppress_notifications=True  # Don't show notifications for system calls
            )
            if not allowed:
                print(f"⛔ Character generation denied: {reason}")
                self._log_generation_attempt(gap, None, False, reason)
                return None
        
        # Find best inspiration source for this gap
        inspiration = self._find_best_inspiration(gap)
        
        if ai_generate_func:
            # AI-powered generation
            candidate = self._generate_with_ai(gap, inspiration, ai_generate_func)
        else:
            # Template-based generation (no AI cost)
            candidate = self._generate_from_template(gap, inspiration)
        
        if candidate:
            self._log_generation_attempt(gap, candidate, True, None)
        
        return candidate
    
    def _find_best_inspiration(self, gap: TraitSpaceGap) -> Dict:
        """Find the best historical/theoretical figure to inspire a character for this gap"""
        # Match gap's situation types to domains
        situation_to_domain = {
            'emotional_crisis': 'mental_health',
            'urgent_problem': 'work',
            'existential_question': 'learning',
            'celebration_moment': 'relationships',
            'skill_development': 'learning',
            'relationship_conflict': 'relationships',
            'quick_decision': 'work',
            'career_guidance': 'work',
        }
        
        target_domain = None
        for situation in gap.situation_types:
            if situation in situation_to_domain:
                target_domain = situation_to_domain[situation]
                break
        
        # Filter inspirations by domain if possible
        candidates = [i for i in self.INSPIRATION_SOURCES if i['domain'] == target_domain]
        if not candidates:
            candidates = self.INSPIRATION_SOURCES
        
        # Pick one randomly (could be smarter based on traits)
        return random.choice(candidates)
    
    def _generate_from_template(self, gap: TraitSpaceGap, inspiration: Dict) -> CharacterCandidate:
        """Generate character using templates (no AI cost)"""
        
        # Create character ID from inspiration name
        char_id = inspiration['name'].lower().replace(' ', '_').replace('.', '')
        
        # Build description from gap traits
        trait_highlights = []
        for trait, desc in gap.recommended_traits.items():
            if 'Very' in desc:
                trait_highlights.append(desc.lower())
        
        description = f"Inspired by {inspiration['name']}'s {inspiration['style']} approach. "
        if trait_highlights:
            description += f"Particularly {', '.join(trait_highlights[:3])}."
        
        # Create philosophical lens based on inspiration
        lenses = {
            'Marcus Aurelius': "What is within your control? Focus there, accept the rest.",
            'Socrates': "The unexamined life is not worth living. Let's question together.",
            'Confucius': "Harmony comes from understanding our roles and relationships.",
            'Buddha': "Suffering comes from attachment. Let's find the middle way.",
            'Carl Rogers': "You have the answers within you. I'm here to help you find them.",
            'Viktor Frankl': "Even in suffering, we can find meaning and purpose.",
            'Brené Brown': "Vulnerability is not weakness, it's our greatest measure of courage.",
            'Peter Drucker': "Efficiency is doing things right; effectiveness is doing the right things.",
            'Simon Sinek': "Start with why. Purpose drives sustainable success.",
            'Warren Buffett': "Be fearful when others are greedy, greedy when others are fearful.",
            'Leonardo da Vinci': "Learning never exhausts the mind. Let's explore together.",
            'Maya Angelou': "There is no greater agony than bearing an untold story inside you.",
            'Hippocrates': "Let food be thy medicine. Healing is a matter of time and nature.",
            'Wim Hof': "The cold is your warm friend. Push your limits to find your strength.",
        }
        
        philosophical_lens = lenses.get(inspiration['name'], 
            f"Drawing from {inspiration['name']}'s wisdom to guide you.")
        
        return CharacterCandidate(
            name=f"The {inspiration['style'].title()}",
            inspiration=inspiration['name'],
            traits=gap.centroid,
            domain=inspiration['domain'],
            description=description,
            philosophical_lens=philosophical_lens,
            gap_filled=gap
        )
    
    def _generate_with_ai(self, gap: TraitSpaceGap, inspiration: Dict, 
                          ai_func) -> Optional[CharacterCandidate]:
        """Generate character using AI (costs API tokens)"""
        # Build prompt for AI
        prompt = f"""Create a therapeutic AI character inspired by {inspiration['name']}.

Target traits (0-1 scale):
{json.dumps(gap.centroid.to_dict(), indent=2)}

This character should help users in situations like: {', '.join(gap.situation_types)}

Respond with JSON containing:
- display_name: A title like "The [Role]"
- description: 2 sentences describing their approach
- philosophical_lens: Their core belief/approach in one sentence

Keep responses focused and practical."""

        try:
            # Call AI (this is tracked by budget manager)
            response = ai_func(prompt)
            
            # Parse response
            # (In real implementation, parse the AI JSON response)
            # For now, fall back to template
            return self._generate_from_template(gap, inspiration)
            
        except Exception as e:
            print(f"⚠️ AI character generation failed: {e}")
            return self._generate_from_template(gap, inspiration)
    
    def _log_generation_attempt(self, gap: TraitSpaceGap, 
                                candidate: Optional[CharacterCandidate],
                                success: bool, error: Optional[str]):
        """Log character generation attempt"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT INTO character_generation_log
            (inspiration_source, generated_character_json, success, error_message)
            VALUES (?, ?, ?, ?)
        ''', (
            candidate.inspiration if candidate else None,
            json.dumps(candidate.traits.to_dict()) if candidate else None,
            success,
            error
        ))
        self.db.commit()
    
    def add_character_to_system(self, candidate: CharacterCandidate,
                                character_system: CharacterTraitSystem) -> bool:
        """Add a generated character to the character system"""
        cursor = self.db.cursor()
        
        char_id = candidate.inspiration.lower().replace(' ', '_').replace('.', '')
        
        try:
            # Insert into character_library
            cursor.execute('''
                INSERT INTO character_library
                (character_id, display_name, traits_json, domain, description,
                 philosophical_lens, is_base)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            ''', (
                char_id,
                candidate.name,
                json.dumps(candidate.traits.to_dict()),
                candidate.domain,
                candidate.description,
                candidate.philosophical_lens
            ))
            self.db.commit()
            
            # Add to in-memory cache
            character_system.characters[char_id] = CharacterProfile(
                character_id=char_id,
                display_name=candidate.name,
                traits=candidate.traits,
                domain=candidate.domain,
                description=candidate.description,
                philosophical_lens=candidate.philosophical_lens
            )
            
            print(f"✅ Added new character: {candidate.name} ({char_id})")
            return True
            
        except sqlite3.IntegrityError:
            print(f"⚠️ Character {char_id} already exists")
            return False
        except Exception as e:
            print(f"❌ Failed to add character: {e}")
            return False
    
    def get_expansion_stats(self) -> Dict:
        """Get statistics about character expansion"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM trait_space_gaps WHERE filled_by IS NULL
        ''')
        unfilled_gaps = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM trait_space_gaps WHERE filled_by IS NOT NULL
        ''')
        filled_gaps = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM character_generation_log WHERE success = 1
        ''')
        successful_generations = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM character_library WHERE is_base = 0
        ''')
        custom_characters = cursor.fetchone()[0]
        
        return {
            'unfilled_gaps': unfilled_gaps,
            'filled_gaps': filled_gaps,
            'successful_generations': successful_generations,
            'custom_characters': custom_characters,
            'base_characters': len(BASE_CHARACTERS)
        }


def create_character_expansion_system(db_connection: sqlite3.Connection,
                                      ai_budget_manager=None) -> CharacterExpansionSystem:
    """Factory function"""
    return CharacterExpansionSystem(db_connection, ai_budget_manager)
