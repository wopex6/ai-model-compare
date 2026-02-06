"""
Phase 5 API Tests using requests session (maintains cookies)
"""

import requests
import json

BASE_URL = "http://localhost:5050"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

class Phase5APITests:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.results = {'passed': 0, 'failed': 0, 'errors': []}
    
    def log_pass(self, name):
        self.results['passed'] += 1
        print(f"  ✅ PASS: {name}")
    
    def log_fail(self, name, error=""):
        self.results['failed'] += 1
        self.results['errors'].append((name, error))
        print(f"  ❌ FAIL: {name} - {error}")
    
    def login(self):
        """Login and establish session"""
        print("\n🔐 Logging in...")
        try:
            # Get login page first (for any CSRF tokens)
            self.session.get(f"{BASE_URL}/chatchat")
            
            # Post login
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": TEST_USER, "password": TEST_PASSWORD}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data.get('token')
                    # Set auth header for all future requests
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    self.log_pass(f"Login ({data.get('username', 'OK')})")
                    return True
            
            self.log_fail("Login", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log_fail("Login", str(e))
            return False
    
    def test_characters(self):
        """Test GET /api/character-traits/characters"""
        print("\n📊 Test: Get All Characters")
        try:
            response = self.session.get(f"{BASE_URL}/api/character-traits/characters")
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                if count > 0:
                    self.log_pass(f"Get characters ({count} found)")
                    # Check structure
                    char = data['characters'][0]
                    if 'id' in char and 'display_name' in char and 'traits' in char:
                        self.log_pass("Character structure valid")
                    else:
                        self.log_fail("Character structure", "Missing fields")
                else:
                    self.log_fail("Get characters", "No characters")
            else:
                self.log_fail("Get characters", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Get characters", str(e))
    
    def test_analyze(self):
        """Test POST /api/character-traits/analyze"""
        print("\n📊 Test: Analyze Situation")
        messages = [
            "I'm really anxious about my job interview",
            "Help me plan my fitness routine",
            "I'm so frustrated with my boss",
        ]
        
        for msg in messages:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/character-traits/analyze",
                    json={"message": msg}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    state = data.get('situation', {}).get('emotional_state', '?')
                    goal = data.get('situation', {}).get('goal_type', '?')
                    self.log_pass(f"Analyze → {state}/{goal}")
                else:
                    self.log_fail(f"Analyze", f"Status {response.status_code}")
                    break
            except Exception as e:
                self.log_fail(f"Analyze", str(e))
    
    def test_match(self):
        """Test POST /api/character-traits/match"""
        print("\n📊 Test: Character Matching")
        test_cases = [
            {"message": "I need help calming down, I'm so anxious"},
            {"message": "Give me an action plan for my career"},
            {"situation": {"emotional_state": "sad", "goal_type": "support"}},
        ]
        
        for i, payload in enumerate(test_cases, 1):
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/character-traits/match",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    char = data.get('matched_character', {}).get('display_name', '?')
                    score = data.get('match_score', 0)
                    self.log_pass(f"Match #{i}: {char} ({score})")
                else:
                    self.log_fail(f"Match #{i}", f"Status {response.status_code}")
                    break
            except Exception as e:
                self.log_fail(f"Match #{i}", str(e))
    
    def test_effectiveness(self):
        """Test GET /api/character-traits/effectiveness"""
        print("\n📊 Test: Character Effectiveness")
        try:
            response = self.session.get(f"{BASE_URL}/api/character-traits/effectiveness")
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('characters', []))
                self.log_pass(f"Effectiveness ({count} chars)")
            else:
                self.log_fail("Effectiveness", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Effectiveness", str(e))
    
    def run_all(self):
        print("=" * 60)
        print("PHASE 5: CHARACTER TRAIT SYSTEM - API TESTS")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        
        if self.login():
            self.test_characters()
            self.test_analyze()
            self.test_match()
            self.test_effectiveness()
        
        print("\n" + "=" * 60)
        total = self.results['passed'] + self.results['failed']
        print(f"RESULTS: {self.results['passed']}/{total} tests passed")
        print("=" * 60)
        
        if self.results['errors']:
            print("\nFailed:")
            for name, err in self.results['errors']:
                print(f"  - {name}: {err}")
        
        return self.results['failed'] == 0

if __name__ == "__main__":
    Phase5APITests().run_all()
