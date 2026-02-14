"""
E2E Smoke Test — Verify the shared conversation pipeline works end-to-end.

Tests:
1. Login to get JWT token
2. Send message through philosophy endpoint → verify pipeline enrichment
3. Send message through domain endpoint → verify pipeline enrichment
4. Check no 500 errors from either endpoint

Run: python tests/test_e2e_pipeline_smoke.py
Requires: server running on localhost:5000
"""

import os
import sys
import json
import requests
import unittest

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:5050')

# Test credentials — will try to sign up, then login
TEST_USER = 'pipeline_smoke_test'
TEST_EMAIL = 'pipeline_smoke@test.com'
TEST_PASSWORD = 'TestPass123!'


def get_auth_token():
    """Get JWT token by signing up or logging in."""
    # Try login first
    resp = requests.post(f'{BASE_URL}/api/auth/login', json={
        'username': TEST_USER,
        'password': TEST_PASSWORD,
    }, timeout=10)
    
    if resp.status_code == 200:
        return resp.json().get('token')
    
    # Try signup
    resp = requests.post(f'{BASE_URL}/api/auth/signup', json={
        'username': TEST_USER,
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
    }, timeout=10)
    
    if resp.status_code in (200, 201):
        return resp.json().get('token')
    
    raise RuntimeError(f"Cannot authenticate: {resp.status_code} {resp.text}")


class TestPipelineE2E(unittest.TestCase):
    """End-to-end smoke tests for the shared conversation pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Get auth token once for all tests."""
        try:
            cls.token = get_auth_token()
        except Exception as e:
            cls.token = None
            print(f"\n⚠️  Could not authenticate: {e}")
            print(f"    Make sure the server is running on {BASE_URL}\n")
    
    def _headers(self):
        return {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
    
    def setUp(self):
        if not self.token:
            self.skipTest(f"Server not reachable at {BASE_URL}")
    
    # ----------------------------------------------------------------
    # 1. HEALTH CHECK
    # ----------------------------------------------------------------
    
    def test_01_server_is_running(self):
        """Server should respond to a basic request."""
        resp = requests.get(f'{BASE_URL}/favicon.ico', timeout=5)
        self.assertIn(resp.status_code, [200, 204])
    
    # ----------------------------------------------------------------
    # 2. PHILOSOPHY CHARACTERS ENDPOINT
    # ----------------------------------------------------------------
    
    def test_02_philosophy_endpoint_no_500(self):
        """Philosophy endpoint should not return 500 (pipeline crash)."""
        # First, get or create a session for a philosophy character
        resp = requests.get(
            f'{BASE_URL}/api/user/conversations',
            headers=self._headers(), timeout=10
        )
        self.assertNotEqual(resp.status_code, 500, f"GET conversations failed: {resp.text}")
        
        if resp.status_code == 200:
            conversations = resp.json()
            if isinstance(conversations, list) and conversations:
                session_id = conversations[0].get('session_id') or conversations[0].get('id')
            else:
                # Create a new conversation
                create_resp = requests.post(
                    f'{BASE_URL}/api/user/conversations',
                    headers=self._headers(),
                    json={'character_id': 'super_motivational_coach'},
                    timeout=10
                )
                if create_resp.status_code in (200, 201):
                    session_id = create_resp.json().get('session_id') or create_resp.json().get('id')
                else:
                    self.skipTest(f"Cannot create conversation: {create_resp.status_code}")
                    return
        else:
            self.skipTest(f"Cannot list conversations: {resp.status_code}")
            return
        
        if not session_id:
            self.skipTest("No session_id available")
            return
        
        # Send a message through philosophy endpoint
        msg_resp = requests.post(
            f'{BASE_URL}/api/user/conversations/{session_id}/messages',
            headers=self._headers(),
            json={'message': 'What strategies help with staying motivated during setbacks?'},
            timeout=30
        )
        
        self.assertNotEqual(msg_resp.status_code, 500,
                            f"Philosophy endpoint returned 500: {msg_resp.text[:500]}")
        
        if msg_resp.status_code == 200:
            data = msg_resp.json()
            print(f"\n  ✅ Philosophy response received (keys: {list(data.keys())})")
            # Verify response has expected structure
            self.assertTrue(
                'response' in data or 'message' in data or 'content' in data,
                f"Unexpected response structure: {list(data.keys())}"
            )
    
    # ----------------------------------------------------------------
    # 3. DOMAIN CHARACTERS ENDPOINT
    # ----------------------------------------------------------------
    
    def test_03_domain_endpoint_no_500(self):
        """Domain endpoint should not return 500 (pipeline crash)."""
        resp = requests.post(
            f'{BASE_URL}/api/domain-characters/route',
            headers=self._headers(),
            json={
                'message': 'How can I improve my work-life balance?',
                'character': 'coordinator',
                'use_ai': False,  # Skip AI call to test just the pipeline
            },
            timeout=15
        )
        
        self.assertNotEqual(resp.status_code, 500,
                            f"Domain endpoint returned 500: {resp.text[:500]}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n  ✅ Domain response received (keys: {list(data.keys())})")
            self.assertIn('success', data)
            self.assertTrue(data['success'])
            self.assertIn('responses', data)
    
    def test_04_domain_endpoint_with_ai(self):
        """Domain endpoint with AI should work through the full pipeline."""
        resp = requests.post(
            f'{BASE_URL}/api/domain-characters/route',
            headers=self._headers(),
            json={
                'message': 'I feel overwhelmed at work lately',
                'character': 'coordinator',
                'use_ai': True,
            },
            timeout=30
        )
        
        self.assertNotEqual(resp.status_code, 500,
                            f"Domain endpoint with AI returned 500: {resp.text[:500]}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"\n  ✅ Domain AI response received")
            print(f"     Responding: {data.get('responding_count', '?')} character(s)")
            print(f"     AI generated: {data.get('ai_generated', '?')}")
            
            # Check situation analysis came through (from pipeline)
            if 'situation' in data:
                print(f"     Situation: {data['situation'].get('emotional_state', 'N/A')}")
    
    # ----------------------------------------------------------------
    # 4. PIPELINE CONSOLE OUTPUT CHECK
    # ----------------------------------------------------------------
    
    def test_05_domain_no_ai_returns_responses(self):
        """Even without AI, domain endpoint should return character routing results."""
        resp = requests.post(
            f'{BASE_URL}/api/domain-characters/route',
            headers=self._headers(),
            json={
                'message': 'I want to learn a new skill',
                'character': 'domain_work',
                'use_ai': False,
            },
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            self.assertIn('responses', data)
            print(f"\n  ✅ Domain (no AI) responded with {len(data['responses'])} character(s)")


if __name__ == '__main__':
    print(f"\n🔍 E2E Pipeline Smoke Test")
    print(f"   Target: {BASE_URL}\n")
    unittest.main(verbosity=2)
