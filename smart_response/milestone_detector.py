"""
MilestoneDetector
=================
Detects when the user's current message indicates they have achieved (or are
close to achieving) a goal or intention previously stored in explicit_context.

When a match is found the module:
1. Returns a MILESTONE ACHIEVED prompt block so the AI celebrates naturally.
2. Deactivates the achieved goal in explicit_context (marks active=0) so it
   won't appear in future prompts or goal check-in hints.

Detection strategy:
- ACHIEVEMENT_PHRASES: clear achievement language in the current message
- Substring check: the goal text appears in the current message

Both conditions must be true (phrase AND goal reference) to avoid false positives.

All errors return '' / no-op — never blocks a response.
"""

from __future__ import annotations
from typing import Optional, List, Tuple
import sqlite3

ACHIEVEMENT_PHRASES = [
    'i got', 'i got the', 'i got a', 'i finally', 'i did it', 'i made it',
    'i succeeded', 'i achieved', 'i passed', 'i finished', 'i completed',
    'i won', 'i landed', 'i was accepted', 'i was promoted', 'i got promoted',
    'they offered me', 'they gave me', 'i received', 'we launched', 'we shipped',
    'it worked', "it's done", 'it is done', 'mission accomplished',
    'good news', 'great news', 'exciting news', 'happy to share',
]


class MilestoneDetector:
    """
    Detects goal achievement and builds a MILESTONE ACHIEVED prompt block.
    """

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None):
        self.db = db_conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_milestone_block(
        self,
        current_message: str,
        user_id: int,
        character_id: str = '',
        db_path: str = 'integrated_users.db',
    ) -> str:
        """
        Return a MILESTONE ACHIEVED block and deactivate the goal, or '' if not matched.
        """
        try:
            conn, _opened = self._conn(db_path)
            try:
                return self._build_safe(conn, current_message, user_id, character_id)
            finally:
                if _opened:
                    conn.close()
        except Exception:
            return ''

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_safe(
        self,
        conn: sqlite3.Connection,
        message: str,
        user_id: int,
        character_id: str,
    ) -> str:
        msg_lower = message.lower()

        # Fast gate: must contain an achievement phrase
        if not any(phrase in msg_lower for phrase in ACHIEVEMENT_PHRASES):
            return ''

        # Load active goals / intentions for this user
        achieved = self._find_achieved_goal(conn, msg_lower, user_id, character_id)
        if not achieved:
            return ''

        goal_id, goal_text = achieved

        # Deactivate the goal in the DB (best-effort)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE explicit_context SET active = 0 WHERE id = ?", (goal_id,)
            )
            conn.commit()
        except Exception:
            pass

        block = (
            f"MILESTONE ACHIEVED:\n"
            f"The user appears to have achieved their goal: \"{goal_text}\"\n"
            f"Celebrate this with them warmly and genuinely.\n"
            f"Then ask what their next goal or focus is, if the conversation allows.\n"
        )
        return block

    def _find_achieved_goal(
        self,
        conn: sqlite3.Connection,
        msg_lower: str,
        user_id: int,
        character_id: str,
    ) -> Optional[Tuple[int, str]]:
        """Return (id, goal_text) for the first matching active goal, or None."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, context_value FROM explicit_context
                WHERE user_id = ?
                  AND context_type IN ('goal', 'intention')
                  AND active = 1
                ORDER BY
                    CASE priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END,
                    timestamp DESC
                LIMIT 10
            ''', (user_id,))
            rows = cursor.fetchall()
        except Exception:
            return None

        for row in rows:
            goal_id, goal_text = row[0], row[1]
            if not goal_text:
                continue
            # Check if key words from the goal appear in the message
            goal_words = [w.lower() for w in goal_text.split() if len(w) > 3]
            if not goal_words:
                continue
            # At least half the key goal words must appear in the message
            matches = sum(1 for w in goal_words if w in msg_lower)
            if matches >= max(1, len(goal_words) // 2):
                return (goal_id, goal_text)

        return None

    def _conn(self, db_path: str):
        if self.db is not None:
            return self.db, False
        return sqlite3.connect(db_path), True


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance: Optional[MilestoneDetector] = None


def get_milestone_detector(
    db_conn: Optional[sqlite3.Connection] = None,
) -> MilestoneDetector:
    global _instance
    if _instance is None or db_conn is not None:
        _instance = MilestoneDetector(db_conn)
    return _instance
