"""
Smoke test for the Gentle Companion (Sam) — boots Flask and hits the
real routes via the test client.

Covers:
- GET  /gentle_companion              → page renders, contains Sam, no sidebar
- GET  /gentle_companion/daily-insight → returns one of Sam's soft phrases
- POST /gentle_companion/chat (auth, mocked AI) → endpoint responds 200

The bot.chat() method is monkey-patched to avoid real AI calls.

Run from repo root:
    python tests\test_gentle_companion_smoke.py
or:
    python -m pytest tests/test_gentle_companion_smoke.py -v
"""
import os
import sys
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import jwt as _jwt  # PyJWT

JWT_SECRET = "your-jwt-secret-change-in-production"
TEST_USER_ID = 9991
TEST_USERNAME = "sam_smoke_user"


def _make_token(user_id=TEST_USER_ID, username=TEST_USERNAME):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return _jwt.encode(payload, JWT_SECRET, algorithm="HS256")


class GentleCompanionSmoke(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Importing app triggers all character init — good signal that
        # registering Sam didn't break anything else.
        import app as _app
        cls.flask_app = _app.app
        cls._app_module = _app

    # ──────────────────────────────────────────────────────────────────
    # Page renders
    # ──────────────────────────────────────────────────────────────────
    def test_page_renders(self):
        with self.flask_app.test_client() as client:
            resp = client.get("/gentle_companion")
        self.assertEqual(resp.status_code, 200, msg=resp.data[:300])
        body = resp.data.decode("utf-8")
        self.assertIn("Sam", body)
        self.assertIn("A friendly ear", body)
        # Minimal template should NOT have sidebar markers
        self.assertNotIn("messageCount", body)
        self.assertNotIn("Quick Topics", body)
        # Should contain the chat input element
        self.assertIn('id="userInput"', body)

    # ──────────────────────────────────────────────────────────────────
    # Daily insight (soft phrases only)
    # ──────────────────────────────────────────────────────────────────
    def test_daily_insight_is_soft(self):
        with self.flask_app.test_client() as client:
            resp = client.get("/gentle_companion/daily-insight")
        self.assertEqual(resp.status_code, 200, msg=resp.data[:300])
        data = resp.get_json()
        self.assertIn("insight", data)
        insight = (data["insight"] or "").lower()
        # Insight must be one of Sam's gentle ones, not a coaching slogan
        soft_markers = [
            "no need to have it all figured out",
            "you don't have to carry it alone",
            "it's okay to not know yet",
            "small is okay",
            "you don't have to perform",
        ]
        self.assertTrue(
            any(m in insight for m in soft_markers),
            f"Daily insight wasn't a Sam phrase: {insight!r}",
        )
        # And NOT a coaching slogan
        self.assertNotIn("crush", insight)
        self.assertNotIn("dominate", insight)
        self.assertNotIn("limitless", insight)

    # ──────────────────────────────────────────────────────────────────
    # Auth: chat requires token
    # ──────────────────────────────────────────────────────────────────
    def test_chat_requires_auth(self):
        with self.flask_app.test_client() as client:
            resp = client.post(
                "/gentle_companion/chat",
                json={"message": "hi"},
            )
        self.assertIn(resp.status_code, (401, 403),
                      msg=f"Expected 401/403, got {resp.status_code}: {resp.data[:200]}")

    # ──────────────────────────────────────────────────────────────────
    # Chat with mocked AI returns a normal-shaped response
    # ──────────────────────────────────────────────────────────────────
    def test_chat_with_mocked_ai(self):
        token = _make_token()

        # Monkey-patch the bot's chat method to avoid real AI calls
        bot = self._app_module.all_characters.get("gentle_companion")
        self.assertIsNotNone(bot, "Sam not registered in all_characters")

        fake_response = {
            "response": "Yeah, I hear you. That sounds like a lot.",
            "response_metadata": {"models_used": ["mock"]},
        }

        async def _fake_chat(*args, **kwargs):
            return fake_response

        with patch.object(bot, "chat", side_effect=_fake_chat):
            with self.flask_app.test_client() as client:
                resp = client.post(
                    "/gentle_companion/chat",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"message": "I've been feeling stuck."},
                )

        self.assertEqual(resp.status_code, 200, msg=resp.data[:400])
        data = resp.get_json()
        self.assertIn("response", data)
        # The mocked response should have flowed through (smart_response may
        # rewrite, so we just verify the endpoint succeeded with content)
        self.assertTrue(len(data["response"]) > 0)


# ──────────────────────────────────────────────────────────────────────────
# Standalone runner
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    unittest.main(verbosity=2)
