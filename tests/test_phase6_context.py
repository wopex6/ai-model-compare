"""
Phase 6 API Tests: Character-Specific Context
Tests multi-perspective interpretation endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:5050"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

class Phase6Tests:
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
        print("\n🔐 Logging in...")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": TEST_USER, "password": TEST_PASSWORD}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data.get('token')
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    self.log_pass(f"Login ({data.get('username')})")
                    return True
            self.log_fail("Login", f"Status {response.status_code}")
            return False
        except Exception as e:
            self.log_fail("Login", str(e))
            return False
    
    def test_multi_perspective(self):
        """Test POST /api/character-context/interpret"""
        print("\n📊 Test: Multi-Perspective Interpretation")
        
        test_events = [
            "I failed my job interview today",
            "My relationship just ended",
            "I got promoted at work!",
        ]
        
        for event in test_events:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/character-context/interpret",
                    json={"event_text": event, "max_perspectives": 4}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    perspectives = data.get('perspectives', [])
                    if len(perspectives) > 0:
                        chars = [p['character_name'] for p in perspectives]
                        self.log_pass(f"'{event[:25]}...' → {len(perspectives)} perspectives: {', '.join(chars)}")
                    else:
                        self.log_fail(f"Interpret", "No perspectives returned")
                else:
                    self.log_fail(f"Interpret", f"Status {response.status_code}")
                    break
            except Exception as e:
                self.log_fail(f"Interpret", str(e))
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving interpretations"""
        print("\n📊 Test: Store & Retrieve Interpretations")
        
        event_text = "I'm feeling overwhelmed with work deadlines"
        event_id = "test-event-001"
        
        try:
            # Store interpretation
            response = self.session.post(
                f"{BASE_URL}/api/character-context/interpret",
                json={
                    "event_text": event_text,
                    "event_id": event_id,
                    "store": True,
                    "max_perspectives": 3
                }
            )
            
            if response.status_code == 200:
                self.log_pass("Store interpretations")
                
                # Retrieve by event_id
                response2 = self.session.get(
                    f"{BASE_URL}/api/character-context/event/{event_id}"
                )
                
                if response2.status_code == 200:
                    data = response2.json()
                    count = data.get('perspective_count', 0)
                    self.log_pass(f"Retrieve by event_id ({count} perspectives)")
                else:
                    self.log_fail("Retrieve by event_id", f"Status {response2.status_code}")
            else:
                self.log_fail("Store interpretations", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Store & Retrieve", str(e))
    
    def test_history(self):
        """Test GET /api/character-context/history"""
        print("\n📊 Test: Interpretation History")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/character-context/history?limit=5"
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                self.log_pass(f"History endpoint ({count} events)")
            else:
                self.log_fail("History", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("History", str(e))
    
    def test_perspective_content(self):
        """Verify perspective content is meaningful"""
        print("\n📊 Test: Perspective Content Quality")
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/character-context/interpret",
                json={"event_text": "I lost my job today", "max_perspectives": 4}
            )
            
            if response.status_code == 200:
                data = response.json()
                perspectives = data.get('perspectives', [])
                
                # Check that perspectives have required fields
                required_fields = ['character_id', 'interpretation', 'emotional_framing', 
                                   'action_suggestion', 'philosophical_lens', 'dominant_traits']
                
                all_valid = True
                for p in perspectives:
                    for field in required_fields:
                        if field not in p or not p[field]:
                            all_valid = False
                            self.log_fail(f"Missing {field}", f"in {p.get('character_name', '?')}")
                
                if all_valid:
                    self.log_pass(f"All {len(perspectives)} perspectives have complete content")
                    
                    # Show sample interpretation
                    if perspectives:
                        sample = perspectives[0]
                        print(f"\n    Sample ({sample['character_name']}):")
                        print(f"    Interpretation: {sample['interpretation'][:60]}...")
                        print(f"    Lens: {sample['philosophical_lens']}")
            else:
                self.log_fail("Content check", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Content check", str(e))
    
    def run_all(self):
        print("=" * 60)
        print("PHASE 6: CHARACTER-SPECIFIC CONTEXT - API TESTS")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        
        if self.login():
            self.test_multi_perspective()
            self.test_store_and_retrieve()
            self.test_history()
            self.test_perspective_content()
        
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
    Phase6Tests().run_all()
