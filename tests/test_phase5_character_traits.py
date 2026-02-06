"""
Playwright Test: Phase 5 Character Trait System API Endpoints
Tests the new character matching and analysis APIs.
"""

import asyncio
from playwright.async_api import async_playwright
import json

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

class Phase5Tests:
    def __init__(self):
        self.results = {'passed': 0, 'failed': 0, 'errors': []}
        self.auth_cookies = None
    
    def log_pass(self, name):
        self.results['passed'] += 1
        print(f"  ✅ PASS: {name}")
    
    def log_fail(self, name, error=""):
        self.results['failed'] += 1
        self.results['errors'].append((name, error))
        print(f"  ❌ FAIL: {name} - {error}")
    
    async def login(self, page):
        """Login and get auth session"""
        print("\n🔐 Logging in...")
        try:
            await page.goto(f"{BASE_URL}/chatchat")
            await page.wait_for_load_state('networkidle')
            
            # Fill login form
            await page.fill('input[name="username"]', TEST_USER)
            await page.fill('input[name="password"]', TEST_PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            
            # Check if logged in
            if 'dashboard' in page.url or await page.query_selector('.chat-container'):
                self.log_pass("Login")
                return True
            else:
                self.log_fail("Login", "Could not verify login success")
                return False
        except Exception as e:
            self.log_fail("Login", str(e))
            return False
    
    async def test_characters_endpoint(self, page):
        """Test GET /api/character-traits/characters"""
        print("\n📊 Test: Get All Characters")
        try:
            response = await page.request.get(f"{BASE_URL}/api/character-traits/characters")
            
            if response.status == 200:
                data = await response.json()
                if 'characters' in data and len(data['characters']) > 0:
                    self.log_pass(f"Get characters ({data['count']} found)")
                    # Verify structure
                    char = data['characters'][0]
                    if all(k in char for k in ['id', 'display_name', 'traits']):
                        self.log_pass("Character structure valid")
                    else:
                        self.log_fail("Character structure", "Missing required fields")
                else:
                    self.log_fail("Get characters", "No characters returned")
            elif response.status == 401:
                self.log_fail("Get characters", "Auth required (401)")
            else:
                self.log_fail("Get characters", f"Status {response.status}")
        except Exception as e:
            self.log_fail("Get characters", str(e))
    
    async def test_analyze_endpoint(self, page):
        """Test POST /api/character-traits/analyze"""
        print("\n📊 Test: Analyze Situation")
        test_messages = [
            ("I'm really anxious about my job interview", "anxious"),
            ("Help me plan my fitness routine", "planning"),
            ("I'm so frustrated with my boss", "angry"),
        ]
        
        for msg, expected_state in test_messages:
            try:
                response = await page.request.post(
                    f"{BASE_URL}/api/character-traits/analyze",
                    data=json.dumps({"message": msg}),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status == 200:
                    data = await response.json()
                    if 'situation' in data:
                        state = data['situation'].get('emotional_state', '')
                        self.log_pass(f"Analyze: '{msg[:30]}...' → {state}")
                    else:
                        self.log_fail(f"Analyze: '{msg[:30]}...'", "No situation in response")
                elif response.status == 401:
                    self.log_fail(f"Analyze: '{msg[:30]}...'", "Auth required (401)")
                    break
                else:
                    self.log_fail(f"Analyze: '{msg[:30]}...'", f"Status {response.status}")
            except Exception as e:
                self.log_fail(f"Analyze: '{msg[:30]}...'", str(e))
    
    async def test_match_endpoint(self, page):
        """Test POST /api/character-traits/match"""
        print("\n📊 Test: Character Matching")
        test_cases = [
            {"message": "I need help calming down, I'm so anxious"},
            {"message": "Give me an action plan for my career"},
            {"situation": {"emotional_state": "sad", "goal_type": "support"}},
        ]
        
        for i, payload in enumerate(test_cases, 1):
            try:
                response = await page.request.post(
                    f"{BASE_URL}/api/character-traits/match",
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status == 200:
                    data = await response.json()
                    if 'matched_character' in data:
                        char_name = data['matched_character']['display_name']
                        score = data['match_score']
                        self.log_pass(f"Match #{i}: {char_name} (score: {score})")
                    else:
                        self.log_fail(f"Match #{i}", "No matched_character in response")
                elif response.status == 401:
                    self.log_fail(f"Match #{i}", "Auth required (401)")
                    break
                else:
                    self.log_fail(f"Match #{i}", f"Status {response.status}")
            except Exception as e:
                self.log_fail(f"Match #{i}", str(e))
    
    async def test_effectiveness_endpoint(self, page):
        """Test GET /api/character-traits/effectiveness"""
        print("\n📊 Test: Character Effectiveness")
        try:
            response = await page.request.get(f"{BASE_URL}/api/character-traits/effectiveness")
            
            if response.status == 200:
                data = await response.json()
                if 'characters' in data:
                    self.log_pass(f"Effectiveness stats ({len(data['characters'])} characters)")
                else:
                    self.log_fail("Effectiveness", "No characters in response")
            elif response.status == 401:
                self.log_fail("Effectiveness", "Auth required (401)")
            else:
                self.log_fail("Effectiveness", f"Status {response.status}")
        except Exception as e:
            self.log_fail("Effectiveness", str(e))
    
    async def run_all(self):
        """Run all Phase 5 tests"""
        print("=" * 60)
        print("PHASE 5: CHARACTER TRAIT SYSTEM - PLAYWRIGHT TESTS")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Login first
                if await self.login(page):
                    # Run API tests
                    await self.test_characters_endpoint(page)
                    await self.test_analyze_endpoint(page)
                    await self.test_match_endpoint(page)
                    await self.test_effectiveness_endpoint(page)
                else:
                    print("\n⚠️ Login failed, skipping API tests")
            
            except Exception as e:
                print(f"\n❌ Test suite error: {e}")
            
            finally:
                await browser.close()
        
        # Summary
        print("\n" + "=" * 60)
        total = self.results['passed'] + self.results['failed']
        print(f"RESULTS: {self.results['passed']}/{total} tests passed")
        print("=" * 60)
        
        if self.results['errors']:
            print("\nFailed tests:")
            for name, error in self.results['errors']:
                print(f"  - {name}: {error}")
        
        return self.results['failed'] == 0


if __name__ == "__main__":
    tests = Phase5Tests()
    asyncio.run(tests.run_all())
