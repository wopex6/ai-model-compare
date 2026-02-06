"""
Production Tests: Phase 5, 6, 6.5 on PythonAnywhere
Tests all character trait, context, and collaboration endpoints on production.
"""

import requests
import json
import sys

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

class ProductionTests:
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
            self.log_fail("Login", f"Status {response.status_code}: {response.text[:100]}")
            return False
        except Exception as e:
            self.log_fail("Login", str(e))
            return False
    
    # ===== PHASE 5: CHARACTER TRAIT SYSTEM =====
    
    def test_p5_get_characters(self):
        print("\n📊 Phase 5: Get All Characters")
        try:
            response = self.session.get(f"{BASE_URL}/api/character-traits/characters")
            if response.status_code == 200:
                data = response.json()
                chars = data.get('characters', [])
                count = len(chars)
                if count >= 8:
                    self.log_pass(f"Get characters ({count} found)")
                    # Check for domain characters
                    names = [c['display_name'] for c in chars]
                    has_domain = any('Advisor' in n or 'Guide' in n or 'Mentor' in n or 'Muse' in n or 'Aria' in n for n in names)
                    if has_domain:
                        self.log_pass("Domain characters present in unified system")
                    else:
                        self.log_fail("Domain characters missing from unified system")
                else:
                    self.log_fail("Get characters", f"Only {count} found, expected 8+")
            else:
                self.log_fail("Get characters", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Get characters", str(e))
    
    def test_p5_analyze_situation(self):
        print("\n📊 Phase 5: Analyze Situation")
        cases = [
            ("I'm feeling really anxious about my deadline", "anxious"),
            ("Can you help me plan my career?", "neutral"),
        ]
        for msg, expected_emotion in cases:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/character-traits/analyze",
                    json={"message": msg}
                )
                if response.status_code == 200:
                    data = response.json()
                    situation = data.get('situation', {})
                    if situation:
                        emotion = situation.get('emotional_state', situation.get('emotional_intensity', 'unknown'))
                        self.log_pass(f"Analyze → {emotion}")
                    else:
                        self.log_fail("Analyze", "No situation in response")
                else:
                    self.log_fail("Analyze", f"Status {response.status_code}")
            except Exception as e:
                self.log_fail("Analyze", str(e))
    
    def test_p5_match_character(self):
        print("\n📊 Phase 5: Character Matching")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/character-traits/match",
                json={"message": "I'm anxious about my exam tomorrow"}
            )
            if response.status_code == 200:
                data = response.json()
                match = data.get('match', {})
                char_name = match.get('character', {}).get('display_name', 'Unknown')
                score = match.get('match_score', 0)
                self.log_pass(f"Match: {char_name} (score={score:.3f})")
            else:
                self.log_fail("Match", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Match", str(e))
    
    def test_p5_effectiveness(self):
        print("\n📊 Phase 5: Character Effectiveness")
        try:
            response = self.session.get(f"{BASE_URL}/api/character-traits/effectiveness")
            if response.status_code == 200:
                data = response.json()
                chars = data.get('characters', [])
                self.log_pass(f"Effectiveness ({len(chars)} chars)")
            else:
                self.log_fail("Effectiveness", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Effectiveness", str(e))
    
    # ===== PHASE 6: CHARACTER-SPECIFIC CONTEXT =====
    
    def test_p6_interpret(self):
        print("\n📊 Phase 6: Multi-Perspective Interpretation")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/character-context/interpret",
                json={"event_text": "I failed my job interview today"}
            )
            if response.status_code == 200:
                data = response.json()
                perspectives = data.get('interpretations', [])
                count = len(perspectives)
                if count >= 2:
                    names = [p['character_name'] for p in perspectives]
                    self.log_pass(f"Interpret → {count} perspectives: {', '.join(names[:3])}")
                else:
                    self.log_fail("Interpret", f"Only {count} perspectives")
            else:
                self.log_fail("Interpret", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Interpret", str(e))
    
    def test_p6_store_retrieve(self):
        print("\n📊 Phase 6: Store & Retrieve Interpretations")
        try:
            # Store
            response = self.session.post(
                f"{BASE_URL}/api/character-context/interpret",
                json={
                    "event_text": "Production test event - got a raise",
                    "store": True
                }
            )
            if response.status_code == 200:
                data = response.json()
                event_id = data.get('event_id')
                if event_id:
                    self.log_pass(f"Store (event_id={event_id})")
                    
                    # Retrieve
                    response2 = self.session.get(f"{BASE_URL}/api/character-context/event/{event_id}")
                    if response2.status_code == 200:
                        data2 = response2.json()
                        perspectives = data2.get('interpretations', [])
                        self.log_pass(f"Retrieve ({len(perspectives)} perspectives)")
                    else:
                        self.log_fail("Retrieve", f"Status {response2.status_code}")
                else:
                    self.log_pass("Interpret OK (no store)")
            else:
                self.log_fail("Store", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Store & Retrieve", str(e))
    
    def test_p6_history(self):
        print("\n📊 Phase 6: Interpretation History")
        try:
            response = self.session.get(f"{BASE_URL}/api/character-context/history")
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                self.log_pass(f"History ({len(events)} events)")
            else:
                self.log_fail("History", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("History", str(e))
    
    # ===== PHASE 6.5: CHARACTER COLLABORATION =====
    
    def test_p65_rules(self):
        print("\n📊 Phase 6.5: Collaboration Rules")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/rules")
            if response.status_code == 200:
                data = response.json()
                rules = data.get('rules', [])
                self.log_pass(f"Rules ({len(rules)} found)")
            else:
                self.log_fail("Rules", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Rules", str(e))
    
    def test_p65_domains(self):
        print("\n📊 Phase 6.5: Domain Definitions")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/domains")
            if response.status_code == 200:
                data = response.json()
                domains = data.get('domains', [])
                names = [d['domain_name'] for d in domains]
                self.log_pass(f"Domains ({len(domains)} found): {names}")
            else:
                self.log_fail("Domains", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Domains", str(e))
    
    def test_p65_trigger(self):
        print("\n📊 Phase 6.5: Trigger Detection")
        cases = [
            ("I'm stressed about work and my relationship is falling apart", True),
            ("What's the weather like?", False),
        ]
        for msg, expected in cases:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/collaboration/check",
                    json={"message": msg}
                )
                if response.status_code == 200:
                    data = response.json()
                    triggered = data.get('should_collaborate', False)
                    if triggered == expected:
                        rule = data.get('triggered_rule', 'none')
                        self.log_pass(f"Trigger ({'yes' if triggered else 'no'}): '{msg[:30]}...' → {rule}")
                    else:
                        self.log_fail("Trigger", f"Expected {expected}, got {triggered}")
                else:
                    self.log_fail("Trigger", f"Status {response.status_code}")
            except Exception as e:
                self.log_fail("Trigger", str(e))
    
    def test_p65_orchestrate(self):
        print("\n📊 Phase 6.5: Orchestrate Collaboration")
        try:
            response = self.session.post(
                f"{BASE_URL}/api/collaboration/orchestrate",
                json={
                    "message": "I'm stressed about my job and my relationship is falling apart",
                    "mode": "visible"
                }
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('collaborated'):
                    chars = data.get('participating_characters', [])
                    mode = data.get('mode')
                    self.log_pass(f"Orchestrate ({mode}): {len(chars)} chars - {', '.join(chars)}")
                else:
                    self.log_pass(f"No collaboration: {data.get('reason', 'N/A')}")
            else:
                self.log_fail("Orchestrate", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Orchestrate", str(e))
    
    def test_p65_history(self):
        print("\n📊 Phase 6.5: Collaboration History")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/history")
            if response.status_code == 200:
                data = response.json()
                self.log_pass(f"History ({data.get('count', 0)} events)")
            else:
                self.log_fail("History", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("History", str(e))
    
    def test_p65_stats(self):
        print("\n📊 Phase 6.5: Collaboration Stats")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/stats")
            if response.status_code == 200:
                data = response.json()
                total = data.get('total_collaborations', 0)
                self.log_pass(f"Stats: {total} total collaborations")
            else:
                self.log_fail("Stats", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Stats", str(e))
    
    def run_all(self):
        print("=" * 60)
        print("PRODUCTION TESTS: Phase 5 + 6 + 6.5")
        print(f"Target: {BASE_URL}")
        print("=" * 60)
        
        if not self.login():
            print("\n❌ Cannot proceed without login")
            return False
        
        # Phase 5
        print("\n" + "=" * 40)
        print("PHASE 5: CHARACTER TRAIT SYSTEM")
        print("=" * 40)
        self.test_p5_get_characters()
        self.test_p5_analyze_situation()
        self.test_p5_match_character()
        self.test_p5_effectiveness()
        
        # Phase 6
        print("\n" + "=" * 40)
        print("PHASE 6: CHARACTER-SPECIFIC CONTEXT")
        print("=" * 40)
        self.test_p6_interpret()
        self.test_p6_store_retrieve()
        self.test_p6_history()
        
        # Phase 6.5
        print("\n" + "=" * 40)
        print("PHASE 6.5: CHARACTER COLLABORATION")
        print("=" * 40)
        self.test_p65_rules()
        self.test_p65_domains()
        self.test_p65_trigger()
        self.test_p65_orchestrate()
        self.test_p65_history()
        self.test_p65_stats()
        
        # Summary
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
    success = ProductionTests().run_all()
    sys.exit(0 if success else 1)
