"""
HTTP-level (Flask test client) tests for /api/user/conversation-summary
-----------------------------------------------------------------------
These tests exercise the full request/response cycle using a real Flask
test client and an in-memory SQLite DB injected via mock, so they can run
without a live server or real credentials.
"""
import sys
import os
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import jwt as _jwt  # PyJWT

JWT_SECRET = 'your-jwt-secret-change-in-production'
TEST_USER_ID = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id=TEST_USER_ID, username='testuser'):
    """Return a signed JWT accepted by the app's require_auth decorator."""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return _jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def _make_test_db():
    """
    Fresh in-memory SQLite DB with required tables pre-populated for TEST_USER_ID.
    Returns a new connection every call so each test gets its own isolated DB.
    """
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE character_messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            character_id TEXT,
            role      TEXT,
            content   TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE explicit_context (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER,
            context_type  TEXT,
            context_key   TEXT,
            context_value TEXT,
            priority      TEXT,
            active        INTEGER DEFAULT 1,
            timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE history_secondary (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER,
            character_id  TEXT,
            analysis_data TEXT,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    now  = datetime.now(timezone.utc).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

    # 3 user messages (coach x2, scientist x1) + 1 assistant message (excluded from counts)
    c.executemany(
        "INSERT INTO character_messages(user_id, character_id, role, content, timestamp)"
        " VALUES (?,?,?,?,?)",
        [
            (TEST_USER_ID, 'coach',     'user',      'Hello coach',    now),
            (TEST_USER_ID, 'coach',     'user',      'Help me plan',   now),
            (TEST_USER_ID, 'scientist', 'user',      'Science query',  past),
            (TEST_USER_ID, 'coach',     'assistant', 'Sure!',          now),
        ],
    )

    # 1 active HIGH goal + 1 emotional state
    c.executemany(
        "INSERT INTO explicit_context"
        "(user_id, context_type, context_key, context_value, priority, active, timestamp)"
        " VALUES (?,?,?,?,?,?,?)",
        [
            (TEST_USER_ID, 'goal',           'main',    'Run a marathon', 'HIGH', 1, now),
            (TEST_USER_ID, 'emotional_state','current', 'motivated',      'HIGH', 1, now),
        ],
    )

    # 1 secondary-history record with topics JSON
    c.execute(
        "INSERT INTO history_secondary(user_id, character_id, analysis_data, created_at)"
        " VALUES (?,?,?,?)",
        (TEST_USER_ID, 'coach', '{"topics": ["fitness", "planning"]}', now),
    )

    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestConversationSummaryHTTP(unittest.TestCase):
    """End-to-end HTTP tests for GET /api/user/conversation-summary."""

    @classmethod
    def setUpClass(cls):
        import app as _app        # noqa: F401 — triggers app initialisation once
        cls.flask_app = _app.app

    # ------------------------------------------------------------------
    # Internal helper — makes one request with a fresh mocked DB
    # ------------------------------------------------------------------
    def _get(self, user_id=TEST_USER_ID, db=None):
        db = db or _make_test_db()
        token = _make_token(user_id=user_id)
        with patch('app.get_db_conn', return_value=db):
            with self.flask_app.test_client() as client:
                return client.get(
                    '/api/user/conversation-summary',
                    headers={'Authorization': f'Bearer {token}'},
                )

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    def test_unauthenticated_returns_401(self):
        with self.flask_app.test_client() as client:
            resp = client.get('/api/user/conversation-summary')
        self.assertEqual(resp.status_code, 401)

    def test_invalid_token_returns_401(self):
        with self.flask_app.test_client() as client:
            resp = client.get(
                '/api/user/conversation-summary',
                headers={'Authorization': 'Bearer not-a-real-token'},
            )
        self.assertEqual(resp.status_code, 401)

    # ------------------------------------------------------------------
    # Happy-path response shape
    # ------------------------------------------------------------------
    def test_authenticated_returns_200(self):
        self.assertEqual(self._get().status_code, 200)

    def test_success_flag_true(self):
        self.assertTrue(self._get().get_json().get('success'))

    def test_summary_key_present(self):
        self.assertIn('summary', self._get().get_json())

    def test_all_expected_fields_present(self):
        s = self._get().get_json()['summary']
        for field in [
            'total_messages', 'characters_used', 'most_active_character',
            'first_interaction', 'last_interaction',
            'active_goals', 'recent_topics', 'emotional_state',
        ]:
            self.assertIn(field, s, f"'{field}' missing from summary")

    # ------------------------------------------------------------------
    # Data correctness
    # ------------------------------------------------------------------
    def test_total_messages_counts_only_user_role(self):
        """assistant rows must NOT be included in the total."""
        s = self._get().get_json()['summary']
        self.assertEqual(s['total_messages'], 3)

    def test_characters_used_breakdown(self):
        cu = self._get().get_json()['summary']['characters_used']
        self.assertEqual(cu.get('coach'), 2)
        self.assertEqual(cu.get('scientist'), 1)

    def test_most_active_character_is_coach(self):
        self.assertEqual(
            self._get().get_json()['summary']['most_active_character'], 'coach'
        )

    def test_first_and_last_interaction_not_none(self):
        s = self._get().get_json()['summary']
        self.assertIsNotNone(s['first_interaction'])
        self.assertIsNotNone(s['last_interaction'])

    def test_active_goals_contain_seeded_goal(self):
        goals = self._get().get_json()['summary']['active_goals']
        self.assertIn('Run a marathon', goals)

    def test_emotional_state_populated(self):
        self.assertEqual(
            self._get().get_json()['summary']['emotional_state'], 'motivated'
        )

    def test_recent_topics_from_history_secondary(self):
        topics = self._get().get_json()['summary'].get('recent_topics', [])
        self.assertIn('fitness', topics)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------
    def test_unknown_user_returns_200_with_zeros(self):
        """User with no data at all still gets a valid 200 with empty fields."""
        s = self._get(user_id=9999).get_json()['summary']
        self.assertEqual(s['total_messages'], 0)
        self.assertEqual(s['characters_used'], {})
        self.assertIsNone(s['most_active_character'])
        self.assertIsNone(s['first_interaction'])
        self.assertEqual(s['active_goals'], [])
        self.assertIsNone(s['emotional_state'])


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main(verbosity=2)
