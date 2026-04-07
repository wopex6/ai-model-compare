"""
Progress Context Builder
========================

Builds a compact "LONG-TERM CONTEXT" prompt block from the dual-layer
history system's secondary (analytical) layer.

Purpose: Let the AI reference a user's progress over time so it can say
things like "You mentioned last week you were anxious about your review —
how did that go?" or "You've been working on this goal for 3 weeks."

Design principles:
- Never more than 6 lines of context (avoid bloating the prompt)
- Only surfaces themes that appear 2+ times (signal over noise)
- Graceful degradation: empty string if no history / any error
- Zero new dependencies — uses existing dual_layer_history tables
"""

import json
from collections import Counter
from typing import Optional


# How many recent secondary records to analyse
_RECENT_RECORDS = 20


def build_progress_context(
    user_id: int,
    character_id: str,
    db_path: str = 'integrated_users.db',
    min_occurrences: int = 2,
) -> str:
    """
    Return a compact LONG-TERM CONTEXT block for the AI prompt,
    or an empty string if there is nothing meaningful to surface.

    Args:
        user_id:         User ID
        character_id:    Character being chatted with
        db_path:         Path to the SQLite database
        min_occurrences: Minimum times a topic/concern must appear to be included
    """
    try:
        return _build_safe(user_id, character_id, db_path, min_occurrences)
    except Exception:
        return ""


def _build_safe(user_id: int, character_id: str, db_path: str, min_occurrences: int) -> str:
    import sqlite3
    from smart_response.dual_layer_history import DualLayerHistorySystem

    conn = sqlite3.connect(db_path)
    try:
        history = DualLayerHistorySystem(conn)
        records = history.get_conversation_history(
            user_id, character_id, layer='secondary', limit=_RECENT_RECORDS
        )
    finally:
        conn.close()

    if not records:
        return ""

    # Aggregate topics, concerns, progress indicators, and recent tones
    all_topics: list  = []
    all_concerns: list = []
    all_tones: list    = []
    progress_signals: dict = {}

    for rec in records:
        all_topics.extend(rec.get('topics', []))
        all_concerns.extend(rec.get('concerns', []))
        tone = rec.get('emotional_tone')
        if tone and tone != 'neutral':
            all_tones.append(tone)
        prog = rec.get('progress', {})
        if isinstance(prog, dict):
            for k, v in prog.items():
                progress_signals[k] = progress_signals.get(k, 0) + (1 if v else 0)

    # Filter to recurring themes only (appear >= min_occurrences)
    topic_counts   = Counter(all_topics)
    concern_counts = Counter(all_concerns)

    recurring_topics   = [t for t, c in topic_counts.most_common(4) if c >= min_occurrences]
    recurring_concerns = [c for c, n in concern_counts.most_common(3) if n >= min_occurrences]
    dominant_tone      = Counter(all_tones).most_common(1)[0][0] if all_tones else None

    # Nothing meaningful yet
    if not recurring_topics and not recurring_concerns and not dominant_tone:
        return ""

    lines = ["LONG-TERM CONTEXT (from previous conversations):"]

    if recurring_topics:
        lines.append(f"- Topics this user often discusses: {', '.join(recurring_topics)}")

    if recurring_concerns:
        lines.append(f"- Recurring concerns: {', '.join(recurring_concerns)}")

    if dominant_tone and dominant_tone not in ('neutral', 'mixed'):
        lines.append(f"- Emotional trend in recent sessions: {dominant_tone}")

    if progress_signals.get('goal_mentioned', 0) >= min_occurrences:
        lines.append("- User has been working toward a goal across multiple sessions.")

    if progress_signals.get('obstacle_present', 0) >= min_occurrences:
        lines.append("- User has encountered recurring obstacles — approach with patience.")

    lines.append("(Use this context naturally — reference it when relevant, not mechanically.)")

    return "\n".join(lines) + "\n"
