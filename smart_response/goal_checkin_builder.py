"""
GoalCheckInBuilder
==================
Detects active goals / intentions set by the user 7+ days ago that haven't
been mentioned recently, and injects a soft "GOAL CHECK-IN" hint into the AI
prompt.  The AI can weave this naturally into its response if the conversation
allows — it is never forced.

Conditions that must ALL be true before firing:
    1. User has an active goal or intention in explicit_context
    2. The goal was set at least MIN_DAYS_OLD days ago
    3. The goal hasn't been referenced in the last MIN_DAYS_SINCE_LAST_REF days
       (rough check: no message containing the goal text in recent history)
    4. At least MIN_SESSIONS sessions have occurred (user is not brand-new)

All errors return empty string — never blocks a response.
"""

from __future__ import annotations
from typing import Optional
import sqlite3

MIN_DAYS_OLD              = 7    # goal must be at least this old
MIN_DAYS_SINCE_LAST_REF   = 5    # don't re-ask if mentioned within this window
MIN_SESSIONS              = 3    # don't fire for brand-new users


class GoalCheckInBuilder:
    """
    Builds a compact GOAL CHECK-IN prompt block from explicit_context.
    Returns empty string when conditions are not met.
    """

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None):
        self.db = db_conn

    def build_checkin_block(
        self,
        user_id: int,
        character_id: str = '',
        db_path: str = 'integrated_users.db',
    ) -> str:
        """
        Return a GOAL CHECK-IN prompt block, or '' if conditions not met.

        Args:
            user_id:       Authenticated user ID
            character_id:  Current character (used for context scoping)
            db_path:       Path to the SQLite DB (used if no connection injected)
        """
        try:
            conn = self.db
            _opened = False
            if conn is None:
                conn = sqlite3.connect(db_path)
                _opened = True
            try:
                return self._build_safe(conn, user_id, character_id)
            finally:
                if _opened:
                    conn.close()
        except Exception:
            return ''

    def _build_safe(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        character_id: str,
    ) -> str:
        cursor = conn.cursor()

        # 1. Check session count — skip for brand-new users
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM character_sessions WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row and row[0] < MIN_SESSIONS:
                return ''
        except Exception:
            pass  # table may not exist — continue

        # 2. Find the oldest active goal / intention not recently referenced
        try:
            cursor.execute('''
                SELECT context_type, context_key, context_value, timestamp
                FROM explicit_context
                WHERE user_id = ?
                  AND context_type IN ('goal', 'intention')
                  AND active = 1
                  AND timestamp < datetime('now', ? || ' days')
                ORDER BY timestamp ASC
                LIMIT 5
            ''', (user_id, f'-{MIN_DAYS_OLD}'))
        except Exception:
            return ''

        candidates = cursor.fetchall()
        if not candidates:
            return ''

        # 3. Filter out goals recently mentioned in conversation history
        try:
            cursor.execute('''
                SELECT content FROM character_messages
                WHERE user_id = ?
                  AND role = 'user'
                  AND timestamp > datetime('now', ? || ' days')
                ORDER BY timestamp DESC
                LIMIT 30
            ''', (user_id, f'-{MIN_DAYS_SINCE_LAST_REF}'))
            recent_messages = [r[0].lower() for r in cursor.fetchall() if r[0]]
        except Exception:
            recent_messages = []

        stale_goals = []
        for ctx_type, ctx_key, ctx_value, ts in candidates:
            # Skip if the goal text appears in recent messages
            if any(ctx_value.lower() in msg for msg in recent_messages):
                continue
            stale_goals.append((ctx_type, ctx_value, ts))

        if not stale_goals:
            return ''

        # 4. Build the prompt block (max 1 check-in at a time)
        ctx_type, ctx_value, ts = stale_goals[0]
        kind = "goal" if ctx_type == "goal" else "intention"

        # Calculate rough age in days from timestamp string
        try:
            from datetime import datetime
            set_date = datetime.fromisoformat(ts.split('.')[0])
            days_ago = (datetime.now() - set_date).days
            age_str = f"{days_ago} day{'s' if days_ago != 1 else ''} ago"
        except Exception:
            age_str = "some time ago"

        block = (
            f"GOAL CHECK-IN:\n"
            f"This user set a {kind} {age_str}: \"{ctx_value}\"\n"
            f"They haven't mentioned it recently. If the conversation allows it naturally,\n"
            f"gently ask how it's going or acknowledge their progress.\n"
            f"(Don't force it — only reference if genuinely relevant to what they're saying now.)\n"
        )
        return block


# ---------------------------------------------------------------------------
# Module-level singleton (lazy, thread-safe via GIL for CPython)
# ---------------------------------------------------------------------------
_instance: Optional[GoalCheckInBuilder] = None


def get_goal_checkin_builder(db_conn: Optional[sqlite3.Connection] = None) -> GoalCheckInBuilder:
    global _instance
    if _instance is None or db_conn is not None:
        _instance = GoalCheckInBuilder(db_conn)
    return _instance
