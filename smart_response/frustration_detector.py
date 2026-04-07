"""
FrustrationDetector
===================
Detects user frustration signals in recent messages and injects a
FRUSTRATION DETECTED prompt block so the AI can explicitly acknowledge
and pivot approach.

Two complementary signals are checked:
1. CORRECTION PHRASES — explicit correction language in the current message
   (e.g., "no that's wrong", "you're not understanding me", "not what I asked")
2. REPEATED TOPIC — the user has sent 3+ similar short messages in a row
   without the topic changing, indicating the AI hasn't resolved their need.

All errors return '' — never blocks a response.
"""

from __future__ import annotations
from typing import Optional, List
import re
import sqlite3

# Phrases that directly signal the AI misunderstood or frustrated the user
CORRECTION_PHRASES = [
    "no that", "no that's", "not what i", "not what i asked", "not what i meant",
    "you're not", "you don't", "you didn't", "that's not right", "that's wrong",
    "wrong answer", "you misunderstood", "you don't understand", "that's not helpful",
    "not helpful", "didn't help", "that doesn't help", "still not", "still doesn't",
    "i said", "i already said", "i told you", "as i said", "like i said",
    "i'm frustrated", "this is frustrating", "keep repeating", "same answer",
    "give me a different", "try again", "try something else", "stop repeating",
]

REPETITION_WINDOW   = 4   # messages to scan for repetition
REPETITION_THRESHOLD = 3  # ≥ this many similar messages = frustrated


class FrustrationDetector:
    """
    Detects frustration signals and builds a compact FRUSTRATION DETECTED block.
    """

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None):
        self.db = db_conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_frustration_block(
        self,
        current_message: str,
        user_id: int,
        character_id: str = '',
        db_path: str = 'integrated_users.db',
    ) -> str:
        """
        Return a FRUSTRATION DETECTED prompt block, or '' if no frustration found.
        """
        try:
            if self._has_correction_phrase(current_message):
                return self._make_block('correction')

            conn, _opened = self._conn(db_path)
            try:
                if self._has_repeated_topic(conn, current_message, user_id):
                    return self._make_block('repetition')
            finally:
                if _opened:
                    conn.close()

            return ''
        except Exception:
            return ''

    # ------------------------------------------------------------------
    # Detection helpers
    # ------------------------------------------------------------------

    def _has_correction_phrase(self, message: str) -> bool:
        msg_lower = message.lower().strip()
        return any(phrase in msg_lower for phrase in CORRECTION_PHRASES)

    def _has_repeated_topic(
        self,
        conn: sqlite3.Connection,
        current_message: str,
        user_id: int,
    ) -> bool:
        """True if the last N user messages share significant word overlap."""
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content FROM character_messages
                WHERE user_id = ? AND role = 'user'
                ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, REPETITION_WINDOW))
            rows = cursor.fetchall()
        except Exception:
            return False

        if len(rows) < REPETITION_THRESHOLD:
            return False

        recent_msgs = [r[0].lower() for r in rows if r and r[0]]
        current_words = set(self._content_words(current_message))
        if not current_words:
            return False

        similar_count = sum(
            1 for msg in recent_msgs
            if self._similarity(current_words, set(self._content_words(msg))) >= 0.40
        )
        return similar_count >= REPETITION_THRESHOLD

    def _content_words(self, text: str) -> List[str]:
        """Return meaningful words (strip stopwords, punctuation)."""
        stopwords = {
            'i', 'me', 'my', 'the', 'a', 'an', 'is', 'it', 'to', 'do',
            'of', 'in', 'on', 'at', 'and', 'or', 'but', 'not', 'no', 'can',
            'be', 'are', 'was', 'for', 'with', 'that', 'this', 'you', 'your',
        }
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in stopwords and len(w) > 2]

    @staticmethod
    def _similarity(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    @staticmethod
    def _make_block(signal_type: str) -> str:
        if signal_type == 'correction':
            return (
                "FRUSTRATION DETECTED:\n"
                "The user is explicitly correcting your previous response — they feel misunderstood.\n"
                "Do NOT repeat the same type of answer. Instead:\n"
                "  1. Briefly acknowledge that you may have missed what they needed.\n"
                "  2. Ask ONE specific clarifying question to make sure you understand.\n"
                "  3. Try a completely different angle if you re-answer.\n"
            )
        else:
            return (
                "FRUSTRATION DETECTED:\n"
                "The user seems to be asking the same thing repeatedly — they may feel unheard.\n"
                "Do NOT repeat your previous approach. Instead:\n"
                "  1. Acknowledge that your answers so far may not have hit the mark.\n"
                "  2. Try a fundamentally different angle or framing.\n"
                "  3. Ask what specifically would actually help them right now.\n"
            )

    def _conn(self, db_path: str):
        if self.db is not None:
            return self.db, False
        return sqlite3.connect(db_path), True


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance: Optional[FrustrationDetector] = None


def get_frustration_detector(
    db_conn: Optional[sqlite3.Connection] = None,
) -> FrustrationDetector:
    global _instance
    if _instance is None or db_conn is not None:
        _instance = FrustrationDetector(db_conn)
    return _instance
