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

from .character_traits import CharacterTraitSystem, CharacterProfile, TraitVector, SituationAnalysis


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
    situation_context: Optional[str] = None  # Phase 6 enhancement: situation awareness
    personality_resonance: Optional[float] = None  # Phase 6 enhancement: how well this matches user personality


class CharacterSpecificContext:
    """
    Generates character-specific interpretations of user events.
    Same event → multiple perspectives stored in history.
    """
    
    # Trait-to-interpretation mapping (no hardcoding of character IDs)
    # Phase 6 Enhancement: Dynamic event-responsive interpretations
    TRAIT_INTERPRETATIONS = {
        'stoicism': {
            'lens': 'Stoic acceptance',
            'frame': lambda event: f"This is a test of character. Focus on what you can control.",
            'emotion': "Your feelings are natural responses, but they need not control your actions.",
            'action': "Identify what is within your control and act on that alone.",
            'situation_frames': {
                'stressed': "External pressures test your inner fortress. Your response is the only thing truly yours.",
                'anxious': "Anxiety speaks of things beyond your control. Return to what you can influence.",
                'sad': "Grief and sadness are natural - feel them, but don't let them become your identity.",
                'angry': "Anger reveals where your expectations clash with reality. Examine the expectation.",
                'confused': "Confusion is the beginning of clarity. Sit with not-knowing.",
                'overwhelmed': "Strip away everything except the next right action. One step at a time.",
                'neutral': "Every moment is practice. Use calm times to build inner resilience."
            }
        },
        'optimism': {
            'lens': 'Optimistic growth',
            'frame': lambda event: f"Every setback contains the seeds of opportunity.",
            'emotion': "It's okay to feel this way - these feelings are fuel for positive change.",
            'action': "Let's turn this into a stepping stone toward something better.",
            'situation_frames': {
                'stressed': "Pressure creates diamonds. This stress is building your strength for what's ahead.",
                'anxious': "What feels scary now is actually your next growth opportunity in disguise.",
                'sad': "Even in darkness, seeds are growing. This sadness will give way to new understanding.",
                'angry': "That fire in you? It's passion waiting to be channeled into something great.",
                'confused': "Not knowing is the first step to discovering something amazing.",
                'overwhelmed': "You've overcome challenges before. This one is just the next chapter in your success story.",
                'neutral': "Great time to dream big! What exciting possibility could you explore?"
            }
        },
        'empathy': {
            'lens': 'Empathetic validation',
            'frame': lambda event: f"Your experience and feelings are completely valid.",
            'emotion': "I hear you. These emotions make complete sense given what you're going through.",
            'action': "Take the time you need to process this. What would feel supportive right now?",
            'situation_frames': {
                'stressed': "I can feel the weight you're carrying. It's real, and it matters.",
                'anxious': "Anxiety is your mind trying to protect you. It's okay to feel this way.",
                'sad': "Your sadness deserves space and respect. You don't have to rush through it.",
                'angry': "Your anger is telling you something important about what you value.",
                'confused': "It's completely normal to feel lost sometimes. You're not alone in this.",
                'overwhelmed': "That feeling of too-much is valid. Let's find a safe place to breathe.",
                'neutral': "How are you really doing beneath the surface? I'm here to listen."
            }
        },
        'structure': {
            'lens': 'Analytical planning',
            'frame': lambda event: f"Let's break this down systematically.",
            'emotion': "Understanding the situation clearly will help manage these feelings.",
            'action': "Here's a structured approach: first assess, then plan, then act.",
            'situation_frames': {
                'stressed': "Let's map out exactly what's causing the stress and prioritize systematically.",
                'anxious': "Anxiety often comes from uncertainty. Let's identify the unknowns and create a plan.",
                'sad': "Understanding the root cause can help. What specifically triggered this feeling?",
                'angry': "Let's analyze what happened objectively before deciding on a response.",
                'confused': "Let's organize the information you have and identify what's missing.",
                'overwhelmed': "We need to triage. What's urgent vs. important vs. can wait?",
                'neutral': "Good time for a systems check. What areas of life need attention?"
            }
        },
        'depth': {
            'lens': 'Philosophical reflection',
            'frame': lambda event: f"This moment invites deeper contemplation.",
            'emotion': "Emotions are teachers - what is this feeling trying to show you?",
            'action': "Sit with this experience. Understanding often comes from patient reflection.",
            'situation_frames': {
                'stressed': "What does this stress reveal about what truly matters to you?",
                'anxious': "Anxiety often points to the gap between who we are and who we think we should be.",
                'sad': "Sadness is the soul's way of honoring what we value. What is being mourned here?",
                'angry': "Beneath anger lies a boundary that was crossed. What sacred value was violated?",
                'confused': "Embrace not-knowing. The deepest wisdom often emerges from confusion.",
                'overwhelmed': "Perhaps the overwhelm is asking you to reconsider what you truly need.",
                'neutral': "In stillness, the deepest truths surface. What's quietly asking for your attention?"
            }
        },
        'action_oriented': {
            'lens': 'Action-focused momentum',
            'frame': lambda event: f"What matters now is the next step forward.",
            'emotion': "Channel this energy into movement. Action dissolves doubt.",
            'action': "Let's identify one concrete thing you can do right now.",
            'situation_frames': {
                'stressed': "Stress means it's time to act. What's the single most impactful thing you can do now?",
                'anxious': "The antidote to anxiety is action. Even a small step breaks the spell.",
                'sad': "When you're ready, even the smallest action can shift your energy.",
                'angry': "Use that fire. What constructive action can you take right now?",
                'confused': "When in doubt, experiment. Try something small and learn from the result.",
                'overwhelmed': "Pick the ONE thing that moves the needle most. Everything else can wait.",
                'neutral': "No time like the present. What goal have you been putting off?"
            }
        },
        'supportiveness': {
            'lens': 'Nurturing support',
            'frame': lambda event: f"You're not alone in this.",
            'emotion': "It's okay to lean on others. Seeking support is strength, not weakness.",
            'action': "Who in your life can you reach out to? What would help you feel supported?",
            'situation_frames': {
                'stressed': "You don't have to carry this alone. Let's talk about who can help.",
                'anxious': "I'm right here with you. Together we can face whatever's worrying you.",
                'sad': "It's okay to not be okay. I'm here, and I care about how you're feeling.",
                'angry': "Your feelings matter. Let's work through this together when you're ready.",
                'confused': "We'll figure this out together. You have more support than you realize.",
                'overwhelmed': "Let me help you lighten this load. What can I take off your plate?",
                'neutral': "Just checking in - how can I support you today?"
            }
        },
        'directness': {
            'lens': 'Straightforward honesty',
            'frame': lambda event: f"Let me be direct with you about this.",
            'emotion': "These feelings are signals. Let's look at what they're really telling you.",
            'action': "Here's what I think you need to do - no sugarcoating.",
            'situation_frames': {
                'stressed': "Here's the truth: you're stressed because something needs to change. Let's name it.",
                'anxious': "Let's cut through the anxiety and face what you're actually afraid of.",
                'sad': "Sadness is honest. Don't fight it, but also don't let it make decisions for you.",
                'angry': "You're angry. Good - that means you still care. Now what are you going to do about it?",
                'confused': "Stop overthinking. Here's what I see from the outside.",
                'overwhelmed': "You've taken on too much. Something needs to go. What's it going to be?",
                'neutral': "No fluff: where are you honestly at with your goals right now?"
            }
        }
    }
    
    # Big5 → trait resonance mapping (which character traits resonate with which personality types)
    PERSONALITY_TRAIT_RESONANCE = {
        'openness': {'depth': 1.3, 'optimism': 1.1, 'structure': 0.8},
        'conscientiousness': {'structure': 1.3, 'action_oriented': 1.2, 'directness': 1.1},
        'extraversion': {'optimism': 1.2, 'action_oriented': 1.2, 'supportiveness': 1.1},
        'agreeableness': {'empathy': 1.3, 'supportiveness': 1.3, 'directness': 0.7},
        'neuroticism': {'empathy': 1.2, 'supportiveness': 1.2, 'stoicism': 0.8, 'directness': 0.8}
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
                'created_at': "ALTER TABLE character_interpretations ADD COLUMN created_at DATETIME DEFAULT ''",
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
        user_context: Dict = None,
        situation: SituationAnalysis = None,
        personality: Dict[str, float] = None
    ) -> CharacterInterpretation:
        """
        Generate a character-specific interpretation of an event.
        
        Phase 6 Enhanced:
        - Uses situation analysis for contextual interpretations
        - Considers user personality for resonance scoring
        - Blends primary + secondary trait perspectives
        """
        dominant_traits = self._get_dominant_traits(character)
        
        # Find the most influential trait for interpretation
        primary_trait = dominant_traits[0][0] if dominant_traits else 'empathy'
        primary_value = dominant_traits[0][1] if dominant_traits else 0.5
        
        # Get interpretation template based on primary trait
        if primary_trait in self.TRAIT_INTERPRETATIONS:
            template = self.TRAIT_INTERPRETATIONS[primary_trait]
        else:
            template = self.TRAIT_INTERPRETATIONS['empathy']
        
        # Phase 6 Enhancement: Situation-aware interpretation
        situation_context = None
        if situation:
            emotional_state = situation.emotional_state or 'neutral'
            situation_frames = template.get('situation_frames', {})
            interpretation = situation_frames.get(emotional_state, template['frame'](event_text))
            situation_context = f"{emotional_state} ({situation.emotional_intensity:.0%} intensity)"
            if situation.goal_type != 'general':
                situation_context += f", goal: {situation.goal_type}"
        else:
            # Try to infer emotional state from event text for situation framing
            emotional_state = self._infer_emotional_state(event_text)
            situation_frames = template.get('situation_frames', {})
            if emotional_state != 'neutral' and emotional_state in situation_frames:
                interpretation = situation_frames[emotional_state]
                situation_context = f"inferred: {emotional_state}"
            else:
                interpretation = template['frame'](event_text)
        
        # Blend secondary trait perspective
        if len(dominant_traits) > 1:
            secondary_trait = dominant_traits[1][0]
            if secondary_trait in self.TRAIT_INTERPRETATIONS:
                secondary = self.TRAIT_INTERPRETATIONS[secondary_trait]
                secondary_action = secondary['action']
                interpretation += f" {secondary_action[:60]}..."
        
        # Calculate confidence based on trait extremity
        trait_extremity = sum(abs(v - 0.5) for _, v in dominant_traits) / len(dominant_traits)
        confidence = min(0.5 + trait_extremity, 0.95)
        
        # Phase 6 Enhancement: Personality resonance scoring
        personality_resonance = None
        if personality:
            personality_resonance = self._compute_personality_resonance(
                character, dominant_traits, personality
            )
            # Boost confidence if character resonates well with user personality
            confidence = min(confidence + personality_resonance * 0.1, 0.98)
        
        return CharacterInterpretation(
            character_id=character.character_id,
            character_name=character.display_name,
            interpretation=interpretation,
            emotional_framing=template['emotion'],
            action_suggestion=template['action'],
            philosophical_lens=character.philosophical_lens or template['lens'],
            dominant_traits=[t[0] for t in dominant_traits],
            confidence=confidence,
            situation_context=situation_context,
            personality_resonance=round(personality_resonance, 3) if personality_resonance else None
        )
    
    def _infer_emotional_state(self, text: str) -> str:
        """Quick emotional state inference from text keywords"""
        text_lower = text.lower()
        emotion_keywords = {
            'stressed': ['stress', 'pressure', 'deadline', 'busy', 'hectic'],
            'anxious': ['anxi', 'worr', 'nervous', 'afraid', 'fear', 'scar'],
            'sad': ['sad', 'depress', 'lonely', 'grief', 'loss', 'miss'],
            'angry': ['angry', 'furious', 'frustrat', 'annoy', 'mad', 'upset'],
            'confused': ['confus', 'lost', 'uncertain', "don't know", 'unsure'],
            'overwhelmed': ['overwhelm', 'too much', 'can\'t cope', 'drowning']
        }
        for emotion, keywords in emotion_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return emotion
        return 'neutral'
    
    def _compute_personality_resonance(
        self, 
        character: CharacterProfile,
        dominant_traits: List[Tuple[str, float]],
        personality: Dict[str, float]
    ) -> float:
        """
        Compute how well a character's approach resonates with user personality.
        Returns 0-1 score (higher = better resonance).
        """
        resonance_score = 0.0
        total_weight = 0.0
        
        for big5_trait, big5_score in personality.items():
            if big5_trait not in self.PERSONALITY_TRAIT_RESONANCE:
                continue
            
            trait_map = self.PERSONALITY_TRAIT_RESONANCE[big5_trait]
            
            for dom_trait, dom_value in dominant_traits:
                if dom_trait in trait_map:
                    multiplier = trait_map[dom_trait]
                    # High Big5 score + high multiplier = good resonance
                    # Low Big5 score + low multiplier = also good resonance (opposites)
                    if big5_score > 0.6 and multiplier > 1.0:
                        resonance_score += big5_score * (multiplier - 1.0) * dom_value
                    elif big5_score < 0.4 and multiplier < 1.0:
                        resonance_score += (1 - big5_score) * (1.0 - multiplier) * dom_value
                    total_weight += 1.0
        
        if total_weight == 0:
            return 0.5  # Neutral resonance
        
        return min(0.5 + resonance_score / total_weight, 1.0)
    
    def get_multi_perspective_interpretations(
        self,
        event_text: str,
        characters: List[CharacterProfile] = None,
        max_perspectives: int = 4,
        situation: SituationAnalysis = None,
        personality: Dict[str, float] = None
    ) -> List[CharacterInterpretation]:
        """
        Generate interpretations from multiple characters.
        
        Phase 6 Enhanced:
        - If personality provided, selects characters that resonate + contrast with user
        - Passes situation and personality to each interpretation for richer results
        - Sorts results by confidence (best-fit characters first)
        """
        if characters is None:
            if personality:
                characters = self._select_personality_aware_characters(
                    max_perspectives, personality, event_text
                )
            else:
                characters = self._select_diverse_characters(max_perspectives)
        
        interpretations = []
        for character in characters[:max_perspectives]:
            interp = self.interpret_event_as_character(
                event_text, character, 
                situation=situation, personality=personality
            )
            interpretations.append(interp)
        
        # Sort by confidence (highest first)
        interpretations.sort(key=lambda i: i.confidence, reverse=True)
        
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
    
    def _select_personality_aware_characters(
        self, count: int, personality: Dict[str, float], event_text: str = None
    ) -> List[CharacterProfile]:
        """
        Select characters that balance resonance with user personality AND diversity.
        Picks ~60% resonant characters + ~40% contrasting (for fresh perspectives).
        """
        all_chars = list(self.trait_system.characters.values())
        
        if len(all_chars) <= count:
            return all_chars
        
        # Score each character for personality resonance
        scored = []
        for char in all_chars:
            dominant = self._get_dominant_traits(char)
            resonance = self._compute_personality_resonance(char, dominant, personality)
            scored.append((char, resonance))
        
        # Sort by resonance
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Pick resonant characters (top ~60%)
        resonant_count = max(1, int(count * 0.6))
        contrast_count = count - resonant_count
        
        selected = [s[0] for s in scored[:resonant_count]]
        
        # Pick contrasting characters (most different from selected, from bottom of resonance)
        remaining = [s[0] for s in scored[resonant_count:]]
        for _ in range(contrast_count):
            if not remaining:
                break
            best_char = None
            best_distance = -1
            for char in remaining:
                min_dist = min(char.traits.distance_to(s.traits) for s in selected)
                if min_dist > best_distance:
                    best_distance = min_dist
                    best_char = char
            if best_char:
                selected.append(best_char)
                remaining.remove(best_char)
        
        return selected
    
    def compare_interpretations(
        self,
        event_text: str,
        character_ids: List[str],
        situation: SituationAnalysis = None,
        personality: Dict[str, float] = None
    ) -> Dict:
        """
        Compare how specific characters interpret the same event.
        Returns side-by-side comparison with differences highlighted.
        """
        interpretations = []
        for char_id in character_ids:
            char = self.trait_system.get_character(char_id)
            if char:
                interp = self.interpret_event_as_character(
                    event_text, char, situation=situation, personality=personality
                )
                interpretations.append(interp)
        
        if len(interpretations) < 2:
            return {
                'event_text': event_text,
                'error': 'Need at least 2 valid character IDs for comparison',
                'interpretations': [{
                    'character_id': i.character_id,
                    'character_name': i.character_name,
                    'interpretation': i.interpretation
                } for i in interpretations]
            }
        
        # Analyze differences
        differences = []
        for i in range(len(interpretations)):
            for j in range(i + 1, len(interpretations)):
                a, b = interpretations[i], interpretations[j]
                
                # Trait overlap/difference
                a_traits = set(a.dominant_traits)
                b_traits = set(b.dominant_traits)
                shared = a_traits & b_traits
                unique_a = a_traits - b_traits
                unique_b = b_traits - a_traits
                
                # Philosophical difference
                diff = {
                    'characters': [a.character_name, b.character_name],
                    'shared_traits': list(shared),
                    'unique_traits': {
                        a.character_name: list(unique_a),
                        b.character_name: list(unique_b)
                    },
                    'lens_contrast': f"{a.philosophical_lens} vs {b.philosophical_lens}",
                    'confidence_gap': round(abs(a.confidence - b.confidence), 3),
                    'complementary': len(shared) < len(unique_a | unique_b)
                }
                
                if personality:
                    diff['resonance_comparison'] = {
                        a.character_name: a.personality_resonance,
                        b.character_name: b.personality_resonance
                    }
                
                differences.append(diff)
        
        return {
            'event_text': event_text,
            'interpretations': [{
                'character_id': i.character_id,
                'character_name': i.character_name,
                'interpretation': i.interpretation,
                'emotional_framing': i.emotional_framing,
                'action_suggestion': i.action_suggestion,
                'philosophical_lens': i.philosophical_lens,
                'dominant_traits': i.dominant_traits,
                'confidence': round(i.confidence, 3),
                'situation_context': i.situation_context,
                'personality_resonance': i.personality_resonance
            } for i in interpretations],
            'differences': differences,
            'recommendation': self._generate_comparison_recommendation(interpretations, personality)
        }
    
    def _generate_comparison_recommendation(
        self, 
        interpretations: List[CharacterInterpretation],
        personality: Dict[str, float] = None
    ) -> str:
        """Generate a recommendation based on the comparison"""
        if not interpretations:
            return "No interpretations to compare."
        
        # Sort by confidence
        sorted_interps = sorted(interpretations, key=lambda i: i.confidence, reverse=True)
        best = sorted_interps[0]
        
        if personality and best.personality_resonance:
            if best.personality_resonance > 0.6:
                return (f"{best.character_name}'s perspective is likely to resonate most with you "
                        f"(resonance: {best.personality_resonance:.0%}), but consider "
                        f"{sorted_interps[-1].character_name}'s contrasting view for balance.")
            else:
                return (f"All perspectives offer value here. {best.character_name} has the highest "
                        f"confidence ({best.confidence:.0%}), while other views add important nuance.")
        
        return (f"{best.character_name} offers the most confident perspective ({best.confidence:.0%}). "
                f"Consider multiple viewpoints for a well-rounded understanding.")
    
    def get_situation_aware_perspectives(
        self,
        message: str,
        max_perspectives: int = 4,
        personality: Dict[str, float] = None
    ) -> Dict:
        """
        All-in-one enhanced endpoint: analyze situation, get diverse perspectives.
        Combines Phase 5 situation analysis with Phase 6 multi-perspective interpretation.
        """
        # Phase 5: Analyze the situation
        situation = self.trait_system.analyze_situation(message)
        
        # Get enhanced perspectives
        interpretations = self.get_multi_perspective_interpretations(
            message, max_perspectives=max_perspectives,
            situation=situation, personality=personality
        )
        
        return {
            'message': message,
            'situation_analysis': {
                'emotional_state': situation.emotional_state,
                'emotional_intensity': situation.emotional_intensity,
                'goal_type': situation.goal_type,
                'challenge_type': situation.challenge_type,
                'urgency': situation.urgency,
                'needs_action': situation.needs_action,
                'needs_validation': situation.needs_validation
            },
            'perspectives': [{
                'character_id': i.character_id,
                'character_name': i.character_name,
                'interpretation': i.interpretation,
                'emotional_framing': i.emotional_framing,
                'action_suggestion': i.action_suggestion,
                'philosophical_lens': i.philosophical_lens,
                'dominant_traits': i.dominant_traits,
                'confidence': round(i.confidence, 3),
                'situation_context': i.situation_context,
                'personality_resonance': i.personality_resonance
            } for i in interpretations],
            'perspective_count': len(interpretations),
            'personality_provided': personality is not None
        }
    
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
