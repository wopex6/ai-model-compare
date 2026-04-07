"""
Character Suggester
===================

Maps a user's detected need type (from ResponseNeedClassifier) to the most
suitable AI character available in the system.

This makes the platform "exceptional" — instead of always responding with
the same character, the system nudges users toward the character best
equipped for their current situation.

Design:
  - Need → Character mapping based on character philosophy/strengths
  - Returns suggestion only when the current character is a poor match
  - Never forces a switch — always a gentle suggestion
  - Falls back gracefully when character data is unavailable
"""

from dataclasses import dataclass
from typing import Optional, Dict, List


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CharacterSuggestion:
    should_suggest: bool
    suggested_character_id: str
    suggested_character_name: str
    reason: str                   # User-facing explanation
    confidence: float             # 0.0 – 1.0


# ---------------------------------------------------------------------------
# Need → Character mapping
# ---------------------------------------------------------------------------

# Primary mapping: which character is BEST for each need type
# Values are (character_id, character_name, user_facing_reason)
_NEED_TO_CHARACTER: Dict[str, List[tuple]] = {
    'sympathy': [
        ('psychologist', 'The Psychologist', 'specialises in emotional support and active listening'),
        ('sage', 'The Sage', 'offers a calm, non-judgmental presence'),
    ],
    'direction': [
        ('coach', 'The Life Coach', 'helps you weigh options and make confident decisions'),
        ('marcus', 'Marcus Aurelius', 'cuts through noise with stoic clarity'),
    ],
    'action_plan': [
        ('coach', 'The Life Coach', 'excels at turning goals into concrete action plans'),
        ('strategist', 'The Strategist', 'builds structured plans step by step'),
    ],
    'immediate_result': [
        ('sage', 'The Sage', 'gives direct, distilled answers without filler'),
        ('coach', 'The Life Coach', 'cuts straight to what matters'),
    ],
    'inspiration': [
        ('sage', 'The Sage', 'opens new perspectives with powerful questions'),
        ('philosopher', 'The Philosopher', 'challenges assumptions and sparks new thinking'),
    ],
    'small_steps': [
        ('coach', 'The Life Coach', 'breaks overwhelming goals into achievable micro-steps'),
        ('psychologist', 'The Psychologist', 'understands anxiety and helps you start small'),
    ],
    'information': [
        ('sage', 'The Sage', 'provides clear, well-structured explanations'),
        ('philosopher', 'The Philosopher', 'goes deep on complex topics'),
    ],
    'validation': [
        ('coach', 'The Life Coach', 'gives honest, constructive feedback'),
        ('psychologist', 'The Psychologist', 'validates feelings while offering grounded perspective'),
    ],
}

# Characters that are broadly capable (won't suggest switching away from these)
_GENERAL_PURPOSE_CHARACTERS = {'sage', 'coach', 'psychologist'}

# Characters that are highly specialised (more likely to suggest alternatives)
_SPECIALIST_CHARACTERS = {'marcus', 'philosopher', 'strategist', 'stoic'}


# ---------------------------------------------------------------------------
# Suggester
# ---------------------------------------------------------------------------

class CharacterSuggester:
    """
    Suggests a better-suited character based on detected user need.

    Only suggests when:
    - Current character is a poor match for the detected need
    - Confidence in the need detection is high enough (>= 0.5)
    - The suggested character is different from current

    Never raises — always returns a CharacterSuggestion.
    """

    def __init__(self, suggestion_confidence_threshold: float = 0.5):
        self.threshold = suggestion_confidence_threshold

    def get_effectiveness_scores(
        self,
        primary_need: str,
        db_path: str = 'integrated_users.db',
        min_signals: int = 3,
    ) -> Dict[str, float]:
        """
        Query historical character_switch engagement signals and return
        a {character_id: effectiveness_score} dict for the given need type.
        Returns empty dict if insufficient data or any error.
        """
        try:
            import sqlite3, json
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT character_id, COUNT(*) as switches
                FROM user_engagement_signals
                WHERE signal_type = 'character_switch'
                  AND topic = ?
                  AND character_id IS NOT NULL
                GROUP BY character_id
                HAVING COUNT(*) >= ?
                ORDER BY switches DESC
            ''', (primary_need, min_signals))
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                return {}
            total = sum(r[1] for r in rows)
            return {r[0]: round(r[1] / total, 3) for r in rows}
        except Exception:
            return {}

    def suggest(
        self,
        current_character_id: str,
        primary_need: str,
        need_confidence: float,
        available_characters: Optional[List[str]] = None,
        db_path: str = 'integrated_users.db',
    ) -> CharacterSuggestion:
        """
        Returns a character suggestion, or should_suggest=False if current is fine.

        Args:
            current_character_id:  The character the user is currently talking to
            primary_need:          Detected need type
            need_confidence:       Confidence in the need detection
            available_characters:  List of character IDs available in this deployment
        """
        try:
            effectiveness = self.get_effectiveness_scores(primary_need, db_path=db_path)
            return self._suggest_safe(
                current_character_id, primary_need, need_confidence,
                available_characters, effectiveness
            )
        except Exception:
            return CharacterSuggestion(
                should_suggest=False,
                suggested_character_id='',
                suggested_character_name='',
                reason='',
                confidence=0.0,
            )

    def _suggest_safe(
        self,
        current_character_id: str,
        primary_need: str,
        need_confidence: float,
        available_characters: Optional[List[str]],
        effectiveness: Optional[Dict[str, float]] = None,
    ) -> CharacterSuggestion:
        # Don't suggest if need confidence is too low
        if need_confidence < self.threshold:
            return CharacterSuggestion(
                should_suggest=False,
                suggested_character_id='',
                suggested_character_name='',
                reason='need_confidence_too_low',
                confidence=0.0,
            )

        # Get candidates for this need type
        candidates = _NEED_TO_CHARACTER.get(primary_need, [])
        if not candidates:
            return CharacterSuggestion(
                should_suggest=False,
                suggested_character_id='',
                suggested_character_name='',
                reason='no_candidates_for_need',
                confidence=0.0,
            )

        # Filter to available characters (if list provided)
        if available_characters:
            candidates = [c for c in candidates if c[0] in available_characters]
            if not candidates:
                return CharacterSuggestion(
                    should_suggest=False,
                    suggested_character_id='',
                    suggested_character_name='',
                    reason='no_available_candidates',
                    confidence=0.0,
                )

        # Re-rank candidates by effectiveness score if live data available
        if effectiveness:
            candidates = sorted(
                candidates,
                key=lambda c: effectiveness.get(c[0], 0.0),
                reverse=True,
            ) or candidates  # Fall back to static order if sort empties list

        # Best candidate is first in list
        best_id, best_name, reason = candidates[0]

        # Don't suggest switching to the same character
        if best_id == current_character_id:
            return CharacterSuggestion(
                should_suggest=False,
                suggested_character_id=best_id,
                suggested_character_name=best_name,
                reason='already_with_best_character',
                confidence=need_confidence,
            )

        # General-purpose characters handle most needs well — only suggest if
        # the current character is a poor fit (specialist for a different domain)
        if current_character_id in _GENERAL_PURPOSE_CHARACTERS:
            return CharacterSuggestion(
                should_suggest=False,
                suggested_character_id=best_id,
                suggested_character_name=best_name,
                reason='current_character_is_capable',
                confidence=need_confidence,
            )

        return CharacterSuggestion(
            should_suggest=True,
            suggested_character_id=best_id,
            suggested_character_name=best_name,
            reason=reason,
            confidence=round(need_confidence, 2),
        )

    def format_suggestion_message(self, suggestion: CharacterSuggestion) -> str:
        """
        Format a suggestion as a short, non-pushy user-facing message.
        Returned as part of the response metadata — frontend decides whether to show it.
        """
        if not suggestion.should_suggest:
            return ''
        return (
            f"Based on what you've shared, {suggestion.suggested_character_name} "
            f"({suggestion.reason}) might be especially helpful here. "
            f"You can switch any time."
        )

    def get_best_character_for_need(
        self,
        primary_need: str,
        available_characters: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Utility: just return the best character ID for a need, or None."""
        candidates = _NEED_TO_CHARACTER.get(primary_need, [])
        if available_characters:
            candidates = [c for c in candidates if c[0] in available_characters]
        return candidates[0][0] if candidates else None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_suggester: Optional[CharacterSuggester] = None


def get_character_suggester() -> CharacterSuggester:
    """Get or create the module-level CharacterSuggester singleton."""
    global _suggester
    if _suggester is None:
        _suggester = CharacterSuggester()
    return _suggester
