"""
Playwright Test: Phase 5 Character Trait System - LOCAL
Tests against localhost:5000
"""

import asyncio
from playwright.async_api import async_playwright
import json

BASE_URL = "http://localhost:5050"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

class Phase5LocalTests:
    def __init__(self):
        self.results = {'passed': 0, 'failed': 0, 'errors': []}
    
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
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            await page.fill('input[name="username"]', TEST_USER)
            await page.fill('input[name="password"]', TEST_PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)
            
            self.log_pass("Login")
            return True
        except Exception as e:
            self.log_fail("Login", str(e))
            return False
    
    async def test_characters_endpoint(self, context):
        """Test GET /api/character-traits/characters"""
        print("\n📊 Test: Get All Characters")
        try:
            response = await context.request.get(f"{BASE_URL}/api/character-traits/characters")
            
            if response.status == 200:
                data = await response.json()
                if 'characters' in data and len(data['characters']) > 0:
                    self.log_pass(f"Get characters ({data['count']} found)")
                    char = data['characters'][0]
                    if all(k in char for k in ['id', 'display_name', 'traits']):
                        self.log_pass("Character structure valid")
                    else:
                        self.log_fail("Character structure", "Missing fields")
                else:
                    self.log_fail("Get characters", "No characters returned")
            else:
                self.log_fail("Get characters", f"Status {response.status}")
        except Exception as e:
            self.log_fail("Get characters", str(e))
    
    async def test_analyze_endpoint(self, context):
        """Test POST /api/character-traits/analyze"""
        print("\n📊 Test: Analyze Situation")
        test_messages = [
            ("I'm really anxious about my job interview", "anxious"),
            ("Help me plan my fitness routine", "planning"),
            ("I'm so frustrated with my boss", "angry"),
        ]
        
        for msg, expected in test_messages:
            try:
                response = await context.request.post(
                    f"{BASE_URL}/api/character-traits/analyze",
                    data=json.dumps({"message": msg}),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status == 200:
                    data = await response.json()
                    if 'situation' in data:
                        state = data['situation'].get('emotional_state', 'unknown')
                        self.log_pass(f"Analyze → {state}")
                    else:
                        self.log_fail(f"Analyze", "No situation")
                else:
                    self.log_fail(f"Analyze", f"Status {response.status}")
                    break
            except Exception as e:
                self.log_fail(f"Analyze", str(e))
    
    async def test_match_endpoint(self, context):
        """Test POST /api/character-traits/match"""
        print("\n📊 Test: Character Matching")
        test_cases = [
            {"message": "I need help calming down, I'm so anxious"},
            {"message": "Give me an action plan for my career"},
            {"situation": {"emotional_state": "sad", "goal_type": "support"}},
        ]
        
        for i, payload in enumerate(test_cases, 1):
            try:
                response = await context.request.post(
                    f"{BASE_URL}/api/character-traits/match",
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status == 200:
                    data = await response.json()
                    if 'matched_character' in data:
                        char = data['matched_character']['display_name']
                        score = data['match_score']
                        self.log_pass(f"Match #{i}: {char} ({score})")
                    else:
                        self.log_fail(f"Match #{i}", "No match")
                else:
                    self.log_fail(f"Match #{i}", f"Status {response.status}")
                    break
            except Exception as e:
                self.log_fail(f"Match #{i}", str(e))
    
    async def test_effectiveness_endpoint(self, context):
        """Test GET /api/character-traits/effectiveness"""
        print("\n📊 Test: Character Effectiveness")
        try:
            response = await context.request.get(f"{BASE_URL}/api/character-traits/effectiveness")
            
            if response.status == 200:
                data = await response.json()
                if 'characters' in data:
                    self.log_pass(f"Effectiveness ({len(data['characters'])} chars)")
                else:
                    self.log_fail("Effectiveness", "No characters")
            else:
                self.log_fail("Effectiveness", f"Status {response.status}")
        except Exception as e:
            self.log_fail("Effectiveness", str(e))
    
    async def run_all(self):
        print("=" * 60)
        print("PHASE 5: CHARACTER TRAIT SYSTEM - LOCAL TESTS")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                if await self.login(page):
                    # Run API tests using context to maintain cookies
                    await self.test_characters_endpoint(context)
                    await self.test_analyze_endpoint(context)
                    await self.test_match_endpoint(context)
                    await self.test_effectiveness_endpoint(context)
            except Exception as e:
                print(f"\n❌ Error: {e}")
            finally:
                await browser.close()
        
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
    asyncio.run(Phase5LocalTests().run_all())
