"""
Phase 6.5 API Tests: Character Collaboration System
Tests multi-agent collaboration endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:5050"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

class Phase65Tests:
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
    
    def test_get_rules(self):
        """Test GET /api/collaboration/rules"""
        print("\n📊 Test: Get Collaboration Rules")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/rules")
            if response.status_code == 200:
                data = response.json()
                rules = data.get('rules', [])
                self.log_pass(f"Get rules ({len(rules)} found)")
                if rules:
                    print(f"    Rules: {[r['rule_name'] for r in rules]}")
            else:
                self.log_fail("Get rules", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Get rules", str(e))
    
    def test_get_domains(self):
        """Test GET /api/collaboration/domains"""
        print("\n📊 Test: Get Domain Definitions")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/domains")
            if response.status_code == 200:
                data = response.json()
                domains = data.get('domains', [])
                self.log_pass(f"Get domains ({len(domains)} found)")
                if domains:
                    print(f"    Domains: {[d['domain_name'] for d in domains]}")
            else:
                self.log_fail("Get domains", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Get domains", str(e))
    
    def test_check_trigger(self):
        """Test POST /api/collaboration/check"""
        print("\n📊 Test: Check Collaboration Triggers")
        
        test_cases = [
            ("I'm stressed about my deadline and also fighting with my partner", True, "multi_domain"),
            ("What's the weather like?", False, None),
            ("Help me decide between two job offers", True, "complex_problem"),
        ]
        
        for msg, expected_collab, expected_rule in test_cases:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/collaboration/check",
                    json={"message": msg}
                )
                if response.status_code == 200:
                    data = response.json()
                    should_collab = data.get('should_collaborate', False)
                    rule = data.get('triggered_rule')
                    domains = data.get('detected_domains', [])
                    
                    if should_collab == expected_collab:
                        if expected_rule and rule == expected_rule:
                            self.log_pass(f"Trigger: '{msg[:30]}...' → {rule} ({domains})")
                        elif not expected_collab:
                            self.log_pass(f"No trigger: '{msg[:30]}...'")
                        else:
                            self.log_pass(f"Triggered: '{msg[:30]}...' → {rule}")
                    else:
                        self.log_fail(f"Trigger check", f"Expected {expected_collab}, got {should_collab}")
                else:
                    self.log_fail("Trigger check", f"Status {response.status_code}")
            except Exception as e:
                self.log_fail("Trigger check", str(e))
    
    def test_orchestrate(self):
        """Test POST /api/collaboration/orchestrate"""
        print("\n📊 Test: Orchestrate Collaboration")
        
        test_cases = [
            {
                "message": "I'm stressed about my job deadline and my relationship is falling apart",
                "mode": "visible"
            },
            {
                "message": "What should I do - I'm torn between staying at my job or pursuing my dream",
                "mode": "debate"
            },
            {
                "message": "I need help with work-life balance",
                "mode": "silent",
                "force": True
            }
        ]
        
        for case in test_cases:
            try:
                response = self.session.post(
                    f"{BASE_URL}/api/collaboration/orchestrate",
                    json=case
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('collaborated'):
                        chars = data.get('participating_characters', [])
                        mode = data.get('mode')
                        self.log_pass(f"Orchestrate ({mode}): {len(chars)} chars - {', '.join(chars)}")
                        
                        # Show snippet of response
                        resp = data.get('response', '')[:100]
                        print(f"    Response: {resp}...")
                    else:
                        reason = data.get('reason', 'Unknown')
                        self.log_pass(f"No collaboration: {reason}")
                else:
                    self.log_fail("Orchestrate", f"Status {response.status_code}")
            except Exception as e:
                self.log_fail("Orchestrate", str(e))
    
    def test_history(self):
        """Test GET /api/collaboration/history"""
        print("\n📊 Test: Collaboration History")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/history")
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                self.log_pass(f"History ({count} events)")
            else:
                self.log_fail("History", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("History", str(e))
    
    def test_stats(self):
        """Test GET /api/collaboration/stats"""
        print("\n📊 Test: Collaboration Statistics")
        try:
            response = self.session.get(f"{BASE_URL}/api/collaboration/stats")
            if response.status_code == 200:
                data = response.json()
                total = data.get('total_collaborations', 0)
                by_mode = data.get('by_mode', {})
                self.log_pass(f"Stats: {total} total, modes: {by_mode}")
            else:
                self.log_fail("Stats", f"Status {response.status_code}")
        except Exception as e:
            self.log_fail("Stats", str(e))
    
    def run_all(self):
        print("=" * 60)
        print("PHASE 6.5: CHARACTER COLLABORATION - API TESTS")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        
        if self.login():
            self.test_get_rules()
            self.test_get_domains()
            self.test_check_trigger()
            self.test_orchestrate()
            self.test_history()
            self.test_stats()
        
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
    Phase65Tests().run_all()
