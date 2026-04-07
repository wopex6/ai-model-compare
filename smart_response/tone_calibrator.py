"""
ToneCalibrator
==============
Detects whether a user writes formally or casually (based on recent messages)
and returns a compact tone instruction for the AI prompt.

Signals used (all keyword-based, no ML):
  CASUAL:  contractions, slang, emoji presence, short avg sentence length,
           lowercase-heavy, filler words (lol, btw, gonna, wanna, ya, ngl, tbh)
  FORMAL:  full sentences with capital starts, no contractions, professional
           vocabulary, longer avg message length

Returns one of three states: 'casual', 'formal', or '' (neutral / insufficient data).

Threshold: at least MIN_MSGS messages needed before inferring a tone.
All errors return '' — never blocks a response.
"""

from __future__ import annotations
from typing import Optional
import re
import sqlite3

MIN_MSGS = 4  # minimum sample before inferring tone

CASUAL_MARKERS = [
    'lol', 'lmao', 'btw', 'ngl', 'tbh', 'gonna', 'wanna', 'gotta', 'kinda',
    'sorta', 'yeah', 'yep', 'ya ', 'nah', 'ok ', 'ok!', 'omg', 'wtf', 'idk',
    'imo', 'irl', 'rn ', 'smh', 'fwiw', 'ugh', 'hmm', "i'm", "it's", "don't",
    "can't", "won't", "i've", "i'd", "you're", "that's", "isn't", "wasn't",
    "didn't", "wouldn't", "couldn't", "shouldn't",
]

FORMAL_MARKERS = [
    'therefore', 'furthermore', 'consequently', 'nevertheless', 'however',
    'additionally', 'regarding', 'concerning', 'pursuant', 'accordingly',
    'herein', 'aforementioned', 'subsequent', 'notwithstanding', 'thereof',
    'in accordance', 'with respect to', 'it is important', 'one should',
    'it would be advisable', 'i would like to', 'i am looking to',
    'i am seeking', 'could you please', 'would you be able',
]


class ToneCalibrator:
    """
    Infers user tone from recent messages and returns a prompt instruction.
    """

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None):
        self.db = db_conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_tone_instruction(
        self,
        user_id: int,
        character_id: str = '',
        db_path: str = 'integrated_users.db',
    ) -> str:
        """
        Return a tone instruction string, or '' if tone is neutral / unknown.
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_safe(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        character_id: str,
    ) -> str:
        messages = self._load_recent_messages(conn, user_id)
        if len(messages) < MIN_MSGS:
            return ''

        casual_score, formal_score = 0, 0
        for msg in messages:
            casual_score += self._count_casual(msg)
            formal_score += self._count_formal(msg)

        if casual_score == 0 and formal_score == 0:
            return ''

        ratio = casual_score / max(1, casual_score + formal_score)

        if ratio >= 0.65:
            return (
                "TONE NOTE: This user writes casually and informally. "
                "Match their energy — be conversational, warm, and direct. "
                "Avoid stiff or overly formal language."
            )
        elif ratio <= 0.25:
            return (
                "TONE NOTE: This user writes formally and professionally. "
                "Match their register — be precise, structured, and professional. "
                "Avoid slang or overly casual phrasing."
            )
        return ''

    def _load_recent_messages(
        self,
        conn: sqlite3.Connection,
        user_id: int,
    ):
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content FROM character_messages
                WHERE user_id = ? AND role = 'user'
                ORDER BY timestamp DESC LIMIT 10
            ''', (user_id,))
            return [r[0] for r in cursor.fetchall() if r and r[0]]
        except Exception:
            return []

    @staticmethod
    def _count_casual(text: str) -> int:
        t = text.lower()
        score = 0
        for m in CASUAL_MARKERS:
            if ' ' in m or "'" in m:
                # multi-word phrases and contractions: substring OK
                if m in t:
                    score += 1
            else:
                # single tokens: require word boundary to avoid "ugh" in "through"
                if re.search(r'\b' + re.escape(m.strip()) + r'\b', t):
                    score += 1
        # emoji presence adds casual weight
        if re.search(r'[\U0001F300-\U0001FAFF]', text):
            score += 2
        return score

    @staticmethod
    def _count_formal(text: str) -> int:
        t = text.lower()
        return sum(1 for m in FORMAL_MARKERS if m in t)

    def _conn(self, db_path: str):
        if self.db is not None:
            return self.db, False
        return sqlite3.connect(db_path), True


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance: Optional[ToneCalibrator] = None


def get_tone_calibrator(
    db_conn: Optional[sqlite3.Connection] = None,
) -> ToneCalibrator:
    global _instance
    if _instance is None or db_conn is not None:
        _instance = ToneCalibrator(db_conn)
    return _instance
