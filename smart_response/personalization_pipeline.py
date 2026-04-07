"""
PersonalizationPipeline
=======================
Single entry-point that runs ALL personalization modules in one call.

Both chatbot.py (domain/character chatbot) and base_chatbot.py (AI-compare
fallback) call this identically — no code duplication.

Usage
-----
    from smart_response.personalization_pipeline import build_personalization
    p = build_personalization(user_message, user_id, character_id)

    # Prompt-block strings (injected into the context section)
    p.explicit_context_block
    p.progress_context_block
    p.goal_checkin_block
    p.engagement_block
    p.frustration_block
    p.milestone_block

    # Instruction strings (injected into the rules section)
    p.verbosity_instruction
    p.tone_instruction
    p.format_instruction
    p.emotional_instruction
    p.need_instruction

All fields default to '' on any error — the pipeline NEVER raises.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PersonalizationResult:
    explicit_context_block: str = ""
    progress_context_block: str = ""
    goal_checkin_block:      str = ""
    engagement_block:        str = ""
    frustration_block:       str = ""
    milestone_block:         str = ""
    verbosity_instruction:   str = ""
    tone_instruction:        str = ""
    format_instruction:      str = ""
    emotional_instruction:   str = ""
    need_instruction:        str = ""


def build_personalization(
    user_message: str,
    user_id: Optional[int],
    character_id: str = "general",
    db_path: str = "integrated_users.db",
) -> PersonalizationResult:
    """
    Run all personalization modules and return a PersonalizationResult.
    Never raises — every module is wrapped in try/except.
    """
    result = PersonalizationResult()

    # ------------------------------------------------------------------ #
    # 1. Verbosity preference                                              #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.user_personalization import UserPersonalization
            import sqlite3 as _sq
            _db = _sq.connect(db_path)
            _up = UserPersonalization(_db)
            response_length = _up.get_parameter(
                user_id, 'communication.response_length', 'medium'
            )
            _db.close()
            if response_length == 'brief':
                result.verbosity_instruction = (
                    "VERBOSITY: The user prefers SHORT, concise answers. "
                    "Use 1-3 sentences max unless complexity demands more."
                )
            elif response_length == 'detailed':
                result.verbosity_instruction = (
                    "VERBOSITY: The user prefers DETAILED, thorough answers. "
                    "Go deep with examples and context."
                )
            else:
                result.verbosity_instruction = (
                    "VERBOSITY: The user prefers MEDIUM-length balanced answers (2-4 sentences)."
                )
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 2. Explicit context (goals, feelings, preferences from DB)          #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.explicit_context_handler import ExplicitContextHandler
            import sqlite3 as _sq
            _db = _sq.connect(db_path)
            result.explicit_context_block = ExplicitContextHandler(_db).format_for_ai_prompt(
                user_id, character_id
            )
            _db.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 3. Long-term progress context                                        #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.progress_context_builder import build_progress_context
            result.progress_context_block = build_progress_context(user_id, character_id, db_path=db_path)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 4. Proactive goal check-in (old unresolved goals)                   #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.goal_checkin_builder import GoalCheckInBuilder
            import sqlite3 as _sq
            _db = _sq.connect(db_path)
            result.goal_checkin_block = GoalCheckInBuilder(_db).build_checkin_block(
                user_id, character_id
            )
            _db.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 5. Session engagement (re-engagement prompt + verbosity signal)      #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.session_engagement_tracker import SessionEngagementTracker
            import sqlite3 as _sq
            _db = _sq.connect(db_path)
            _tracker = SessionEngagementTracker(_db)
            result.engagement_block = _tracker.build_engagement_block(user_id, character_id)
            _tracker.record_verbosity_signal(user_id, character_id)
            _db.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 6. Frustration detection                                             #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.frustration_detector import FrustrationDetector
            import sqlite3 as _sq
            _db = _sq.connect(db_path)
            result.frustration_block = FrustrationDetector(_db).build_frustration_block(
                user_message, user_id, character_id
            )
            _db.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 7. Milestone detection (goal achievement)                            #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.milestone_detector import MilestoneDetector
            import sqlite3 as _sq
            _db = _sq.connect(db_path)
            result.milestone_block = MilestoneDetector(_db).build_milestone_block(
                user_message, user_id, character_id
            )
            _db.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 8. Format preference (bullet / steps / prose)                        #
    # ------------------------------------------------------------------ #
    try:
        from smart_response.format_preference_detector import get_format_detector
        result.format_instruction = get_format_detector().build_format_instruction(user_message)
    except Exception:
        pass

    # ------------------------------------------------------------------ #
    # 9. Adaptive tone calibration (casual / formal)                       #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.tone_calibrator import ToneCalibrator
            import sqlite3 as _sq
            _db = _sq.connect(db_path)
            result.tone_instruction = ToneCalibrator(_db).build_tone_instruction(
                user_id, character_id, db_path=db_path
            )
            _db.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # 10. Response need classification                                      #
    # ------------------------------------------------------------------ #
    try:
        from smart_response.response_need_classifier import get_need_classifier
        result.need_instruction = get_need_classifier().get_instruction(
            user_message, min_confidence=0.2
        )
    except Exception:
        pass

    # ------------------------------------------------------------------ #
    # 11. Emotional context (user intelligence / journey)                  #
    # ------------------------------------------------------------------ #
    if user_id:
        try:
            from smart_response.user_intelligence import get_intelligence_system
            intel = get_intelligence_system()
            if intel:
                journey = intel.analyze_emotional_journey(user_id, recent_messages=10)
                if journey.get('confidence', 0) >= 0.3:
                    trajectory    = journey.get('trajectory', 'stable')
                    had_resolution = journey.get('had_resolution', True)
                    if trajectory == 'declining':
                        result.emotional_instruction = (
                            "EMOTIONAL CONTEXT: User seems frustrated or stressed lately. "
                            "Prioritise empathy and validation BEFORE any advice or action steps."
                        )
                    elif trajectory == 'improving':
                        result.emotional_instruction = (
                            "EMOTIONAL CONTEXT: User is in a positive, receptive state. "
                            "You can be direct and action-focused."
                        )
                    elif not had_resolution:
                        result.emotional_instruction = (
                            "EMOTIONAL CONTEXT: User may feel their previous concerns were unresolved. "
                            "Check in on whether earlier topics were addressed before moving forward."
                        )
        except Exception:
            pass

    return result
