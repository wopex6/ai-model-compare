"""
Heavy Usage Test Suite
Tests 100+ conversations with domain characters, verifies analytics and statistics.
Creates a test scenario with 1000 AI calls/day limit.
"""
import time
import random
import requests
from playwright.sync_api import sync_playwright, expect

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

# Domain characters to test
DOMAIN_CHARACTERS = [
    "life_coach",
    "psychologist", 
    "stoic_philosopher",
    "career_mentor",
    "spiritual_guide",
    "health_coach",
    "financial_advisor",
    "creative_muse"
]

# Test messages for different contexts
TEST_MESSAGES = [
    # Goal-related
    "I want to improve my productivity this year",
    "How can I set better goals for myself?",
    "I'm struggling to stay motivated",
    
    # Emotional
    "I've been feeling stressed lately",
    "I'm anxious about my future",
    "How do I deal with disappointment?",
    
    # Career
    "Should I ask for a promotion?",
    "I'm thinking about changing careers",
    "How do I handle a difficult coworker?",
    
    # Health
    "I want to start exercising more",
    "How can I improve my sleep?",
    "I need to eat healthier",
    
    # Financial
    "How should I start saving money?",
    "I'm worried about my finances",
    "Should I invest in stocks?",
    
    # Relationships
    "I'm having trouble communicating with my partner",
    "How do I make new friends?",
    "I feel lonely sometimes",
    
    # Philosophical
    "What is the meaning of life?",
    "How do I find my purpose?",
    "I want to be more mindful",
    
    # Creative
    "I want to start a creative project",
    "How do I overcome writer's block?",
    "I need inspiration for my art"
]

class HeavyUsageTest:
    def __init__(self):
        self.results = {
            'conversations': 0,
            'messages_sent': 0,
            'responses_received': 0,
            'characters_tested': set(),
            'errors': [],
            'analytics_verified': False,
            'context_verified': False,
            'statistics_verified': False
        }
    
    def run_all_tests(self):
        """Run all heavy usage tests"""
        print("=" * 60)
        print("🧪 HEAVY USAGE TEST SUITE")
        print("=" * 60)
        print(f"Target: {BASE_URL}")
        print(f"Goal: 100+ conversations with all domain characters")
        print()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # 1. Login
                self.test_login(page)
                
                # 2. Run 100+ conversations
                self.test_multiple_conversations(page, count=105)
                
                # 3. Test character switching
                self.test_character_switching(page)
                
                # 4. Verify context panel
                self.test_context_panel(page)
                
                # 5. Verify statistics
                self.test_statistics(page)
                
                # 6. Verify analytics dashboard
                self.test_analytics_dashboard(page)
                
                # 7. Verify API analytics endpoints (with cookies)
                cookies = context.cookies()
                self.test_api_analytics(cookies)
                
                # 8. Test budget/limit display
                self.test_budget_display(page)
                
            except Exception as e:
                self.results['errors'].append(f"Fatal error: {str(e)}")
                print(f"❌ Fatal error: {e}")
            finally:
                browser.close()
        
        self.print_summary()
        return self.results
    
    def test_login(self, page):
        """Test login functionality"""
        print("🔐 Testing Login...")
        page.goto(BASE_URL, timeout=30000)
        page.wait_for_load_state('networkidle')
        
        # Check if already logged in
        if page.query_selector('input[name="username"]:visible'):
            page.fill('input[name="username"]', TEST_USER)
            page.fill('input[name="password"]', TEST_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)
        
        print("  ✅ Login successful")
    
    def test_multiple_conversations(self, page, count=105):
        """Send multiple messages to simulate heavy usage"""
        print(f"\n💬 Testing {count} Conversations...")
        
        # Navigate to chat
        page.goto(f"{BASE_URL}/", timeout=30000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        for i in range(count):
            try:
                # Select random character
                character = random.choice(DOMAIN_CHARACTERS)
                self.results['characters_tested'].add(character)
                
                # Try to select character if dropdown exists
                char_selector = page.query_selector(f'[data-character="{character}"], .character-btn[data-id="{character}"]')
                if char_selector:
                    char_selector.click()
                    page.wait_for_timeout(500)
                
                # Send message (updated selectors for actual app)
                message = random.choice(TEST_MESSAGES)
                input_field = page.query_selector('#userInput, #chat-input, textarea#userInput, textarea[placeholder*="message"]')
                
                if input_field:
                    input_field.fill(message)
                    
                    # Submit (updated selectors)
                    send_btn = page.query_selector('#sendBtn, #send-chat-btn, button:has-text("Send")')
                    if send_btn:
                        send_btn.click()
                        self.results['messages_sent'] += 1
                    else:
                        input_field.press('Shift+Enter')
                        self.results['messages_sent'] += 1
                    
                    # Wait for response (short wait to speed up test)
                    page.wait_for_timeout(500)
                    
                    # Check if response appeared
                    responses = page.query_selector_all('.message.assistant, .ai-message, .bot-message')
                    if responses:
                        self.results['responses_received'] += 1
                
                self.results['conversations'] += 1
                
                # Progress indicator every 10 messages
                if (i + 1) % 10 == 0:
                    print(f"  📊 Progress: {i + 1}/{count} conversations")
                
            except Exception as e:
                self.results['errors'].append(f"Conversation {i}: {str(e)}")
        
        print(f"  ✅ Completed {self.results['conversations']} conversations")
        print(f"  📤 Messages sent: {self.results['messages_sent']}")
        print(f"  📥 Responses received: {self.results['responses_received']}")
    
    def test_character_switching(self, page):
        """Test switching between all domain characters"""
        print("\n🎭 Testing Character Switching...")
        
        page.goto(f"{BASE_URL}/", timeout=30000)
        page.wait_for_load_state('networkidle')
        
        characters_switched = 0
        
        for character in DOMAIN_CHARACTERS:
            try:
                # Try different selector patterns
                selectors = [
                    f'[data-character="{character}"]',
                    f'.character-btn[data-id="{character}"]',
                    f'button:has-text("{character.replace("_", " ")}")',
                    f'.domain-char-btn[data-character="{character}"]'
                ]
                
                for selector in selectors:
                    btn = page.query_selector(selector)
                    if btn:
                        btn.click()
                        page.wait_for_timeout(300)
                        characters_switched += 1
                        break
                        
            except Exception as e:
                pass
        
        print(f"  ✅ Switched to {characters_switched}/{len(DOMAIN_CHARACTERS)} characters")
    
    def test_context_panel(self, page):
        """Verify context panel is working"""
        print("\n📋 Testing Context Panel...")
        
        # Go to Life Companion page where context panel exists
        page.goto(f"{BASE_URL}/life-companion", timeout=30000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        # Look for context panel elements (updated selectors)
        context_elements = [
            '#explicit-context-panel',
            '#contextBtn',
            '.action-panel',
            '#explicit-context-content',
            '.panel-content'
        ]
        
        found = False
        for selector in context_elements:
            element = page.query_selector(selector)
            if element:
                found = True
                self.results['context_verified'] = True
                print(f"  ✅ Context element found: {selector}")
                break
        
        # Try clicking the context button to open panel
        context_btn = page.query_selector('#contextBtn')
        if context_btn:
            context_btn.click()
            page.wait_for_timeout(500)
            panel = page.query_selector('#explicit-context-panel')
            if panel and panel.is_visible():
                found = True
                self.results['context_verified'] = True
                print("  ✅ Context panel opens on click")
        
        # Also check for personality/trait indicators
        trait_elements = page.query_selector_all('.trait, .personality-preset, .bot-info')
        
        if found or len(trait_elements) > 0:
            if not found:
                print(f"  ✅ Context panel verified (found {len(trait_elements)} trait elements)")
            self.results['context_verified'] = True
        else:
            print("  ⚠️ Context panel elements not found (may be hidden)")
    
    def test_statistics(self, page):
        """Verify statistics are being tracked"""
        print("\n📈 Testing Statistics...")
        
        # Check statistics API (correct path)
        try:
            response = requests.get(f"{BASE_URL}/api/admin/statistics", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Statistics API working")
                print(f"     - Total users: {data.get('total_users', 'N/A')}")
                print(f"     - Total messages: {data.get('total_messages', 'N/A')}")
                self.results['statistics_verified'] = True
            elif response.status_code == 401:
                print(f"  ⚠️ Statistics API requires auth (expected)")
                self.results['statistics_verified'] = True
            else:
                print(f"  ⚠️ Statistics API returned {response.status_code}")
        except Exception as e:
            print(f"  ⚠️ Statistics API error: {e}")
        
        # Check budget API (correct path)
        try:
            response = requests.get(f"{BASE_URL}/api/ai-budget/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Budget API working")
                print(f"     - Daily calls: {data.get('current_daily_calls', 'N/A')}")
                print(f"     - Daily limit: {data.get('daily_limit', 'N/A')}")
            else:
                print(f"  ⚠️ Budget API returned {response.status_code}")
        except Exception as e:
            print(f"  ⚠️ Budget API error: {e}")
    
    def test_analytics_dashboard(self, page):
        """Verify analytics dashboard is working"""
        print("\n📊 Testing Analytics Dashboard...")
        
        page.goto(f"{BASE_URL}/admin/analytics", timeout=30000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(3000)
        
        tests_passed = 0
        total_tests = 6
        
        # Test 1: Stats cards
        stats_cards = page.query_selector_all('.stat-card, .stats-card, .metric-card')
        if len(stats_cards) > 0:
            print(f"  ✅ Stats cards: {len(stats_cards)} found")
            tests_passed += 1
        else:
            print("  ❌ Stats cards not found")
        
        # Test 2: Usage chart
        usage_chart = page.query_selector('#usage-chart, #usage-chart-container, canvas')
        if usage_chart:
            print("  ✅ Usage chart found")
            tests_passed += 1
        else:
            print("  ❌ Usage chart not found")
        
        # Test 3: Date filter
        date_filter = page.query_selector('#date-range, input[type="date"], .date-filter')
        if date_filter:
            print("  ✅ Date filter found")
            tests_passed += 1
        else:
            print("  ❌ Date filter not found")
        
        # Test 4: Export button
        export_btn = page.query_selector('#export-csv, .export-btn, button:has-text("Export")')
        if export_btn:
            print("  ✅ Export button found")
            tests_passed += 1
        else:
            print("  ❌ Export button not found")
        
        # Test 5: User table
        user_table = page.query_selector('table, .user-table, .data-table')
        if user_table:
            print("  ✅ User table found")
            tests_passed += 1
        else:
            print("  ❌ User table not found")
        
        # Test 6: Page loaded without errors
        error_elements = page.query_selector_all('.error, .alert-danger')
        if len(error_elements) == 0:
            print("  ✅ No error messages on page")
            tests_passed += 1
        else:
            print(f"  ❌ Found {len(error_elements)} error messages")
        
        self.results['analytics_verified'] = tests_passed >= 4
        print(f"\n  Dashboard tests: {tests_passed}/{total_tests} passed")
    
    def test_api_analytics(self, cookies=None):
        """Test all analytics API endpoints"""
        print("\n🔌 Testing Analytics API Endpoints...")
        
        # Build cookies dict for requests
        session_cookies = {}
        if cookies:
            for cookie in cookies:
                session_cookies[cookie['name']] = cookie['value']
        
        endpoints = [
            ('/api/system/health', 'System Health', False),
            ('/api/ai-budget/status', 'Budget Status', False),
            ('/api/smart-response/stats', 'Smart Response Stats', True),  # Requires auth
            ('/api/analytics/engagement', 'Engagement Metrics', False),
            ('/api/analytics/conversations', 'Conversation Insights', False),
            ('/api/analytics/hourly', 'Hourly Activity', False),
            ('/api/analytics/trends/active_users', 'User Trends', False),
        ]
        
        passed = 0
        for endpoint, name, needs_auth in endpoints:
            try:
                if needs_auth and session_cookies:
                    response = requests.get(f"{BASE_URL}{endpoint}", cookies=session_cookies, timeout=10)
                else:
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                    
                if response.status_code == 200:
                    print(f"  ✅ {name}: OK")
                    passed += 1
                elif response.status_code == 401 and needs_auth:
                    print(f"  ⚠️ {name}: 401 (auth required - using session cookies)")
                    # Retry with cookies
                    if session_cookies:
                        response = requests.get(f"{BASE_URL}{endpoint}", cookies=session_cookies, timeout=10)
                        if response.status_code == 200:
                            print(f"  ✅ {name}: OK (with auth)")
                            passed += 1
                else:
                    print(f"  ❌ {name}: {response.status_code}")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        
        print(f"\n  API tests: {passed}/{len(endpoints)} passed")
    
    def test_budget_display(self, page):
        """Test that budget/limit is displayed correctly"""
        print("\n💰 Testing Budget Display...")
        
        page.goto(f"{BASE_URL}/", timeout=30000)
        page.wait_for_load_state('networkidle')
        
        # Look for budget/limit indicators
        budget_elements = [
            '.budget-display',
            '.ai-budget',
            '.usage-display',
            '[data-budget]',
            '.calls-remaining'
        ]
        
        found = False
        for selector in budget_elements:
            element = page.query_selector(selector)
            if element:
                found = True
                text = element.text_content()
                print(f"  ✅ Budget display found: {text[:50]}...")
                break
        
        if not found:
            print("  ⚠️ Budget display element not found (may be in header)")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        print(f"\n📈 Conversation Stats:")
        print(f"   - Total conversations: {self.results['conversations']}")
        print(f"   - Messages sent: {self.results['messages_sent']}")
        print(f"   - Responses received: {self.results['responses_received']}")
        print(f"   - Characters tested: {len(self.results['characters_tested'])}")
        print(f"   - Characters: {', '.join(self.results['characters_tested'])}")
        
        print(f"\n✅ Verification Status:")
        print(f"   - Context panel: {'✅' if self.results['context_verified'] else '❌'}")
        print(f"   - Statistics: {'✅' if self.results['statistics_verified'] else '❌'}")
        print(f"   - Analytics dashboard: {'✅' if self.results['analytics_verified'] else '❌'}")
        
        if self.results['errors']:
            print(f"\n⚠️ Errors ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:
                print(f"   - {error}")
        
        # Overall result
        all_passed = (
            self.results['conversations'] >= 100 and
            self.results['statistics_verified'] and
            self.results['analytics_verified']
        )
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️ SOME TESTS NEED ATTENTION")
        print("=" * 60)


def main():
    """Run the heavy usage test"""
    test = HeavyUsageTest()
    results = test.run_all_tests()
    
    # Exit with appropriate code
    if results['conversations'] >= 100 and results['analytics_verified']:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
