"""
Comprehensive Playwright test for Sage Wei Wisdom Chatbot
Tests all flows including:
1. Page load and UI elements
2. Daily wisdom display
3. Chat functionality
4. Quick action buttons
5. Stats loading
6. Wisdom topics interaction
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import sys

class TestWisdomSage:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = []
        
    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"   {status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
        
    async def run_all_tests(self):
        """Run all wisdom sage tests"""
        async with async_playwright() as p:
            print("\n" + "=" * 80)
            print("🧪 TESTING: Sage Wei Wisdom Chatbot - Complete Flow")
            print("=" * 80)
            
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Enable console logging
            page.on("console", lambda msg: print(f"   🖥️  Console: {msg.text}"))
            
            # Track network requests for API calls
            api_calls = []
            page.on("response", lambda response: 
                api_calls.append(response.url) if '/sage/' in response.url else None
            )
            
            try:
                print("\n" + "=" * 80)
                print("TEST SUITE 1: Page Load & UI Elements")
                print("=" * 80)
                await self.test_page_loads(page)
                await self.test_ui_elements_present(page)
                await self.test_sidebar_elements(page)
                
                print("\n" + "=" * 80)
                print("TEST SUITE 2: Daily Wisdom")
                print("=" * 80)
                await self.test_daily_wisdom_loads(page, api_calls)
                
                print("\n" + "=" * 80)
                print("TEST SUITE 3: Stats Loading")
                print("=" * 80)
                await self.test_stats_load(page, api_calls)
                
                print("\n" + "=" * 80)
                print("TEST SUITE 4: Chat Functionality")
                print("=" * 80)
                await self.test_basic_chat(page)
                await self.test_chat_response_formatting(page)
                
                print("\n" + "=" * 80)
                print("TEST SUITE 5: Quick Action Buttons")
                print("=" * 80)
                await self.test_parable_button(page)
                await self.test_wu_wei_button(page)
                await self.test_balance_button(page)
                
                print("\n" + "=" * 80)
                print("TEST SUITE 6: Wisdom Topics")
                print("=" * 80)
                await self.test_wisdom_topics_clickable(page)
                
                print("\n" + "=" * 80)
                print("TEST SUITE 7: API Endpoints")
                print("=" * 80)
                self.verify_api_calls(api_calls)
                
                # Print summary
                self.print_summary()
                
            except Exception as e:
                print(f"\n❌ CRITICAL TEST FAILURE: {e}")
                import traceback
                traceback.print_exc()
                self.log_test("Critical Error", False, str(e))
            finally:
                print("\n⏳ Keeping browser open for 10 seconds for inspection...")
                await page.wait_for_timeout(10000)
                await browser.close()
    
    async def test_page_loads(self, page):
        """Test 1: Page loads successfully"""
        print("\n📝 TEST 1: Page Load")
        print("-" * 80)
        
        try:
            await page.goto(f"{self.base_url}/sage", wait_until="networkidle", timeout=10000)
            await page.wait_for_timeout(1000)
            
            title = await page.title()
            self.log_test("Page title correct", "Sage Wei" in title, f"Title: {title}")
            
            # Check page loaded without errors
            sage_container = await page.query_selector(".sage-container")
            self.log_test("Main container present", sage_container is not None)
            
        except Exception as e:
            self.log_test("Page load", False, str(e))
    
    async def test_ui_elements_present(self, page):
        """Test 2: All main UI elements are present"""
        print("\n📝 TEST 2: Main UI Elements")
        print("-" * 80)
        
        elements_to_check = {
            ".sage-header": "Header section",
            ".sage-avatar": "Sage avatar",
            ".daily-wisdom-card": "Daily wisdom card",
            ".main-chat": "Main chat area",
            ".chat-messages": "Chat messages container",
            "#messageInput": "Message input field",
            "#sendBtn": "Send button",
            ".wisdom-actions": "Quick action buttons container",
            ".sidebar": "Sidebar"
        }
        
        for selector, name in elements_to_check.items():
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                self.log_test(f"{name} present", element is not None)
            except Exception as e:
                self.log_test(f"{name} present", False, str(e))
    
    async def test_sidebar_elements(self, page):
        """Test 3: Sidebar elements are present"""
        print("\n📝 TEST 3: Sidebar Elements")
        print("-" * 80)
        
        sidebar_elements = {
            ".yin-yang-symbol": "Yin-Yang symbol",
            ".wisdom-topic": "Wisdom topics",
            "#conversationDepth": "Conversation depth counter",
            "#wisdomTopics": "Wisdom topics counter"
        }
        
        for selector, name in sidebar_elements.items():
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                self.log_test(f"{name} present", element is not None)
            except Exception as e:
                self.log_test(f"{name} present", False, str(e))
    
    async def test_daily_wisdom_loads(self, page, api_calls):
        """Test 4: Daily wisdom loads correctly"""
        print("\n📝 TEST 4: Daily Wisdom Loading")
        print("-" * 80)
        
        try:
            # Wait for daily wisdom to load
            await page.wait_for_selector("#dailyWisdomText", timeout=5000)
            
            wisdom_text = await page.text_content("#dailyWisdomText")
            wisdom_source = await page.text_content("#dailyWisdomSource")
            
            # Check that it's not the loading text
            is_loaded = "Loading" not in wisdom_text
            self.log_test("Daily wisdom loaded", is_loaded, f"Text length: {len(wisdom_text)}")
            
            has_source = wisdom_source and len(wisdom_source) > 0
            self.log_test("Wisdom source displayed", has_source, wisdom_source)
            
        except Exception as e:
            self.log_test("Daily wisdom loads", False, str(e))
    
    async def test_stats_load(self, page, api_calls):
        """Test 5: Stats load correctly"""
        print("\n📝 TEST 5: Stats Loading")
        print("-" * 80)
        
        try:
            # Wait for stats to load
            await page.wait_for_timeout(2000)
            
            conversation_depth = await page.text_content("#conversationDepth")
            wisdom_topics_count = await page.text_content("#wisdomTopics")
            
            self.log_test("Conversation depth displayed", conversation_depth is not None, f"Value: {conversation_depth}")
            self.log_test("Wisdom topics count displayed", wisdom_topics_count is not None, f"Value: {wisdom_topics_count}")
            
        except Exception as e:
            self.log_test("Stats load", False, str(e))
    
    async def test_basic_chat(self, page):
        """Test 6: Basic chat functionality"""
        print("\n📝 TEST 6: Basic Chat")
        print("-" * 80)
        
        try:
            # Count initial messages
            initial_messages = await page.query_selector_all(".message")
            initial_count = len(initial_messages)
            self.log_test("Initial welcome message present", initial_count > 0, f"Count: {initial_count}")
            
            # Type and send a message
            test_message = "What is wisdom?"
            await page.fill("#messageInput", test_message)
            await page.click("#sendBtn")
            
            # Wait for typing indicator
            await page.wait_for_selector(".typing-indicator", state="visible", timeout=2000)
            self.log_test("Typing indicator appears", True)
            
            # Wait for response (timeout 30 seconds for API)
            await page.wait_for_selector(".message.sage:last-child", timeout=30000)
            await page.wait_for_timeout(1000)
            
            # Count messages after response
            final_messages = await page.query_selector_all(".message")
            final_count = len(final_messages)
            
            # Should have at least 2 more messages (user + sage)
            messages_added = final_count > initial_count
            self.log_test("Chat messages sent and received", messages_added, 
                         f"Initial: {initial_count}, Final: {final_count}")
            
            # Check if response is not empty
            last_message = await page.query_selector(".message.sage:last-child .message-content")
            response_text = await last_message.text_content() if last_message else ""
            
            has_content = len(response_text) > 50
            self.log_test("Response has content", has_content, f"Length: {len(response_text)}")
            
            # Check for wisdom-related content
            has_wisdom_tone = any(word in response_text.lower() for word in 
                                 ['wisdom', 'understanding', 'path', 'journey', 'contemplat'])
            self.log_test("Response has wisdom tone", has_wisdom_tone)
            
        except Exception as e:
            self.log_test("Basic chat functionality", False, str(e))
    
    async def test_chat_response_formatting(self, page):
        """Test 7: Chat response formatting"""
        print("\n📝 TEST 7: Response Formatting")
        print("-" * 80)
        
        try:
            # Check last sage message
            last_sage_msg = await page.query_selector(".message.sage:last-child")
            
            # Check for avatar
            has_avatar = await last_sage_msg.query_selector(".message-avatar")
            self.log_test("Sage avatar present in message", has_avatar is not None)
            
            # Check for message content
            has_content = await last_sage_msg.query_selector(".message-content")
            self.log_test("Message content container present", has_content is not None)
            
            # Check for metadata
            has_meta = await last_sage_msg.query_selector(".message-meta")
            self.log_test("Message metadata present", has_meta is not None)
            
        except Exception as e:
            self.log_test("Response formatting", False, str(e))
    
    async def test_parable_button(self, page):
        """Test 8: Parable quick action button"""
        print("\n📝 TEST 8: Parable Button")
        print("-" * 80)
        
        try:
            # Get current message count
            messages_before = await page.query_selector_all(".message")
            count_before = len(messages_before)
            
            # Click parable button
            await page.click("text='📖 Parable'")
            await page.wait_for_timeout(1000)
            
            # Wait for typing indicator
            await page.wait_for_selector(".typing-indicator", state="visible", timeout=2000)
            
            # Wait for response
            await page.wait_for_timeout(15000)
            
            messages_after = await page.query_selector_all(".message")
            count_after = len(messages_after)
            
            self.log_test("Parable button triggers chat", count_after > count_before,
                         f"Before: {count_before}, After: {count_after}")
            
        except Exception as e:
            self.log_test("Parable button", False, str(e))
    
    async def test_wu_wei_button(self, page):
        """Test 9: Wu Wei quick action button"""
        print("\n📝 TEST 9: Wu Wei Button")
        print("-" * 80)
        
        try:
            messages_before = await page.query_selector_all(".message")
            count_before = len(messages_before)
            
            await page.click("text='☯️ Wu Wei'")
            await page.wait_for_timeout(1000)
            
            # Wait for response
            await page.wait_for_timeout(15000)
            
            messages_after = await page.query_selector_all(".message")
            count_after = len(messages_after)
            
            self.log_test("Wu Wei button triggers chat", count_after > count_before,
                         f"Before: {count_before}, After: {count_after}")
            
        except Exception as e:
            self.log_test("Wu Wei button", False, str(e))
    
    async def test_balance_button(self, page):
        """Test 10: Balance quick action button"""
        print("\n📝 TEST 10: Balance Button")
        print("-" * 80)
        
        try:
            messages_before = await page.query_selector_all(".message")
            count_before = len(messages_before)
            
            await page.click("text='⚖️ Balance'")
            await page.wait_for_timeout(1000)
            
            # Wait for response
            await page.wait_for_timeout(15000)
            
            messages_after = await page.query_selector_all(".message")
            count_after = len(messages_after)
            
            self.log_test("Balance button triggers chat", count_after > count_before,
                         f"Before: {count_before}, After: {count_after}")
            
        except Exception as e:
            self.log_test("Balance button", False, str(e))
    
    async def test_wisdom_topics_clickable(self, page):
        """Test 11: Wisdom topics in sidebar are clickable"""
        print("\n📝 TEST 11: Wisdom Topics Clickable")
        print("-" * 80)
        
        try:
            # Find all wisdom topic elements
            topics = await page.query_selector_all(".wisdom-topic")
            topics_count = len(topics)
            
            self.log_test("Wisdom topics present", topics_count >= 4, 
                         f"Found {topics_count} topics")
            
            # Try clicking one topic
            if topics_count > 0:
                messages_before = await page.query_selector_all(".message")
                count_before = len(messages_before)
                
                # Click first topic
                await topics[0].click()
                await page.wait_for_timeout(1000)
                
                # Wait for response
                await page.wait_for_timeout(15000)
                
                messages_after = await page.query_selector_all(".message")
                count_after = len(messages_after)
                
                self.log_test("Topic click triggers chat", count_after > count_before,
                             f"Before: {count_before}, After: {count_after}")
            
        except Exception as e:
            self.log_test("Wisdom topics clickable", False, str(e))
    
    def verify_api_calls(self, api_calls):
        """Test 12: Verify API endpoints were called"""
        print("\n📝 TEST 12: API Endpoints")
        print("-" * 80)
        
        expected_endpoints = [
            '/sage/daily-wisdom',
            '/sage/stats',
            '/sage/chat'
        ]
        
        for endpoint in expected_endpoints:
            called = any(endpoint in url for url in api_calls)
            self.log_test(f"API endpoint {endpoint} called", called)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t['passed'])
        failed_tests = total_tests - passed_tests
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test['passed']:
                    print(f"   • {test['name']}")
                    if test['message']:
                        print(f"     {test['message']}")
        
        print("\n" + "=" * 80)
        if pass_rate == 100:
            print("🎉 ALL TESTS PASSED! Sage Wei is ready for wisdom! 🌿")
        elif pass_rate >= 80:
            print("⚠️  MOSTLY PASSING - Some issues need attention")
        else:
            print("❌ MULTIPLE FAILURES - Requires debugging")
        print("=" * 80)
        
        return pass_rate >= 80

async def main():
    """Main test runner"""
    tester = TestWisdomSage()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("\n🚀 Starting Sage Wei Wisdom Chatbot Tests...")
    print("⚠️  Make sure Flask server is running on http://localhost:5000")
    print("⚠️  Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(0)
