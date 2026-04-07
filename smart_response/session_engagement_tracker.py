"""
SessionEngagementTracker
========================
Detects engagement patterns from conversation history and returns two types of
prompt hints that help the AI adapt in real time:

1. RE-ENGAGEMENT block — injected when the user hasn't appeared in ABSENCE_DAYS
   or more days.  Reminds the AI to reference previous context and check on old
   goals / concerns.

2. Automatic verbosity signal — if the user's last N messages average < SHORT_MSG_WORDS
   words, records a 'brief' signal into UserPersonalization so the verbosity system
   picks it up on the next calibration pass.

All errors return '' / no-op — never blocks a response.
"""

from __future__ import annotations
from typing import Optional
import sqlite3

ABSENCE_DAYS      = 7     # days gap before "re-engagement" hint fires
SHORT_MSG_WORDS   = 12    # avg words threshold to infer "brief" preference
LONG_MSG_WORDS    = 60    # avg words threshold to infer "detailed" preference
MIN_MSG_SAMPLE    = 5     # minimum messages needed before inferring verbosity


class SessionEngagementTracker:
    """
    Analyses session gaps and message-length trends to produce prompt hints
    and feed verbosity signals.
    """

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None):
        self.db = db_conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_engagement_block(
        self,
        user_id: int,
        character_id: str = '',
        db_path: str = 'integrated_users.db',
    ) -> str:
        """
        Return a re-engagement prompt block when the user has been absent, or ''
        if conditions are not met.
        """
        try:
            conn, _opened = self._conn(db_path)
            try:
                return self._build_safe(conn, user_id, character_id)
            finally:
                if _opened:
                    conn.close()
        except Exception:
            return ''

    def record_verbosity_signal(
        self,
        user_id: int,
        character_id: str = '',
        db_path: str = 'integrated_users.db',
    ) -> None:
        """
        Measure avg message length from recent user messages and record a
        verbosity signal into UserPersonalization when a strong pattern exists.
        """
        try:
            conn, _opened = self._conn(db_path)
            try:
                self._record_verbosity_safe(conn, user_id, character_id)
            finally:
                if _opened:
                    conn.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _conn(self, db_path: str):
        if self.db is not None:
            return self.db, False
        return sqlite3.connect(db_path), True

    def _build_safe(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        character_id: str,
    ) -> str:
        cursor = conn.cursor()

        # Find last message timestamp for this user
        try:
            cursor.execute('''
                SELECT MAX(timestamp) FROM character_messages
                WHERE user_id = ? AND role = 'user'
            ''', (user_id,))
            row = cursor.fetchone()
            if not row or not row[0]:
                return ''
            last_ts_str = row[0]
        except Exception:
            return ''

        # Calculate days since last message
        try:
            from datetime import datetime
            last_ts = datetime.fromisoformat(last_ts_str.split('.')[0])
            days_absent = (datetime.now() - last_ts).days
        except Exception:
            return ''

        if days_absent < ABSENCE_DAYS:
            return ''

        # Build context from last session
        summary_fragments = []
        try:
            # Fetch last 5 user messages before the gap for context
            cursor.execute('''
                SELECT content FROM character_messages
                WHERE user_id = ? AND role = 'user'
                ORDER BY timestamp DESC LIMIT 5
            ''', (user_id,))
            msgs = [r[0] for r in cursor.fetchall() if r and r[0]]
            if msgs:
                summary_fragments.append(f"Last discussed: {msgs[0][:80]}")
        except Exception:
            pass

        context_str = ("\n  - " + "\n  - ".join(summary_fragments)) if summary_fragments else ""
        block = (
            f"RE-ENGAGEMENT NOTE:\n"
            f"This user is returning after a {days_absent}-day absence.{context_str}\n"
            f"Consider briefly acknowledging their return and checking in on any "
            f"ongoing goals or concerns from previous sessions before moving forward.\n"
            f"(Keep it warm, not clinical.)\n"
        )
        return block

    def _record_verbosity_safe(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        character_id: str,
    ) -> None:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT content FROM character_messages
                WHERE user_id = ? AND role = 'user'
                ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, MIN_MSG_SAMPLE * 2))
            msgs = [r[0] for r in cursor.fetchall() if r and r[0]]
        except Exception:
            return

        if len(msgs) < MIN_MSG_SAMPLE:
            return

        avg_words = sum(len(m.split()) for m in msgs) / len(msgs)

        if avg_words < SHORT_MSG_WORDS:
            signal_value = 'brief'
        elif avg_words > LONG_MSG_WORDS:
            signal_value = 'detailed'
        else:
            return  # balanced — no signal needed

        try:
            from smart_response.user_personalization import UserPersonalization
            UserPersonalization().record_signal(
                user_id, 'response_length_feedback', signal_value,
                context=character_id
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance: Optional[SessionEngagementTracker] = None


def get_engagement_tracker(
    db_conn: Optional[sqlite3.Connection] = None,
) -> SessionEngagementTracker:
    global _instance
    if _instance is None or db_conn is not None:
        _instance = SessionEngagementTracker(db_conn)
    return _instance
