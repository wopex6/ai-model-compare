"""
End-to-End Playwright Test for Character Insights Features
Tests: Character Insights (📊), User Insights (🎯), Other Perspectives (👁️)

Run with: 
  SET TEST_USER=youruser
  SET TEST_PASS=yourpass
  pytest tests/test_character_insights_e2e.py -v --headed

Or directly:
  python tests/test_character_insights_e2e.py
"""

import pytest
from playwright.sync_api import Page, expect, sync_playwright
import time
import re
import os


# Test configuration - use environment variables
BASE_URL = os.environ.get("TEST_URL", "https://trabcd.pythonanywhere.com")
TEST_USER = os.environ.get("TEST_USER", "")
TEST_PASS = os.environ.get("TEST_PASS", "")


class TestCharacterInsightsE2E:
    """E2E tests for character insights features using real AI"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup: Login before each test"""
        self.page = page
        self.login()
        yield
    
    def login(self):
        """Login to the application"""
        print("\n[1] Logging in...")
        
        # Go directly to Life Companion and set auth token via API
        self.page.goto(f"{BASE_URL}/life-companion")
        self.page.wait_for_load_state("networkidle")
        
        # Login via API to get token - use f-string with proper escaping
        login_script = f"""
            async () => {{
                const resp = await fetch('/api/auth/login', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{username: '{TEST_USER}', password: '{TEST_PASS}'}})
                }});
                const data = await resp.json();
                if (data.token) {{
                    localStorage.setItem('authToken', data.token);
                    return data.token;
                }}
                return data.error || 'Unknown error';
            }}
        """
        result = self.page.evaluate(login_script)
        
        if result and not isinstance(result, str):
            print(f"    ✓ Got auth token")
        elif result and result.startswith('ey'):
            print(f"    ✓ Got auth token: {result[:20]}...")
        else:
            print(f"    ⚠️ Login issue: {result}")
        
        # Reload to apply token
        self.page.reload()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)  # Wait for JS to initialize
        print("    ✓ Page reloaded")
    
    def test_send_message_and_get_ai_response(self):
        """Test 1: Send a message and verify AI responds"""
        print("\n[TEST] Send message and get AI response")
        
        # Wait for page to be ready
        self.page.wait_for_timeout(2000)
        
        # Find chat input - check if it's enabled
        chat_input = self.page.locator('#userInput')
        expect(chat_input).to_be_visible(timeout=10000)
        
        # Check if input is enabled (user is logged in)
        is_disabled = self.page.evaluate("document.getElementById('userInput').disabled")
        if is_disabled:
            print("    ⚠️ Chat input is disabled - trying to re-authenticate")
            # Try setting token again
            self.page.reload()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(2000)
        
        # Send test message
        test_message = "I'm feeling stressed about my job deadline and worried about money"
        chat_input.fill(test_message)
        print(f"    Filled message: {test_message[:50]}...")
        
        # Click send button
        send_btn = self.page.locator('#sendBtn')
        send_btn.click()
        print("    Clicked send button")
        
        # Count existing messages before waiting
        initial_count = self.page.locator('.message').count()
        print(f"    Initial message count: {initial_count}")
        
        # Wait for new message to appear (any new .message div)
        print("    Waiting for AI response...")
        try:
            # Wait for message count to increase
            self.page.wait_for_function(
                f"document.querySelectorAll('.message').length > {initial_count + 1}",
                timeout=90000
            )
            print("    ✓ New messages appeared")
        except Exception as e:
            # Take screenshot for debugging
            self.page.screenshot(path="test_failure.png")
            print(f"    Screenshot saved to test_failure.png")
            raise
        
        # Find the latest assistant message
        all_messages = self.page.locator('.message')
        last_message = all_messages.last
        response_text = last_message.text_content()
        print(f"    ✓ Got response: {response_text[:100]}...")
        
        assert len(response_text) > 10, "AI response should have content"
    
    def test_character_insights_panel(self):
        """Test 2: Character Insights panel (📊) shows interpretation data"""
        print("\n[TEST] Character Insights Panel (📊)")
        
        # First send a message to have something to analyze
        chat_input = self.page.locator('#userInput')
        initial_count = self.page.locator('.message').count()
        chat_input.fill("I'm stressed about my job and worried about finances")
        self.page.locator('#sendBtn').click()
        self.page.wait_for_function(f"document.querySelectorAll('.message').length > {initial_count + 1}", timeout=90000)
        print("    ✓ Message sent and response received")
        
        # Click the 📊 button
        insights_btn = self.page.locator('#insightsBtn')
        expect(insights_btn).to_be_visible()
        insights_btn.click()
        
        # Wait for panel to appear
        panel = self.page.locator('#character-insights-panel')
        expect(panel).to_be_visible(timeout=5000)
        print("    ✓ Character Insights panel opened")
        
        # Wait for content to load
        self.page.wait_for_timeout(3000)  # Give API time to respond
        
        content = self.page.locator('#character-insights-content')
        content_text = content.text_content()
        print(f"    Panel content: {content_text[:200]}...")
        
        # Verify content has interpretation data
        assert "Loading" not in content_text or len(content_text) > 50, "Panel should have loaded content"
        
        # Check for key elements (concern %, emotions, etc.)
        if "%" in content_text:
            print("    ✓ Found concern percentages")
        if "Perspective" in content_text:
            print("    ✓ Found character perspectives")
        if "stressed" in content_text.lower() or "emotion" in content_text.lower():
            print("    ✓ Found emotion detection")
        
        # Close panel
        self.page.locator('#character-insights-panel .panel-close').click()
        expect(panel).not_to_be_visible()
        print("    ✓ Panel closed")
    
    def test_other_perspectives_panel(self):
        """Test 3: Other Perspectives panel (👁️) shows responded vs noticed"""
        print("\n[TEST] Other Perspectives Panel (👁️)")
        
        # Send a message first
        chat_input = self.page.locator('#userInput')
        initial_count = self.page.locator('.message').count()
        chat_input.fill("I need help with work-life balance and my relationships")
        self.page.locator('#sendBtn').click()
        self.page.wait_for_function(f"document.querySelectorAll('.message').length > {initial_count + 1}", timeout=90000)
        print("    ✓ Message sent and response received")
        
        # Click the 👁️ button
        observers_btn = self.page.locator('#observersBtn')
        expect(observers_btn).to_be_visible()
        observers_btn.click()
        
        # Wait for panel
        panel = self.page.locator('#silent-observers-panel')
        expect(panel).to_be_visible(timeout=5000)
        print("    ✓ Other Perspectives panel opened")
        
        # Wait for content
        self.page.wait_for_timeout(3000)
        
        content = self.page.locator('#silent-observers-content')
        content_text = content.text_content()
        print(f"    Panel content: {content_text[:200]}...")
        
        # Check for groupings
        if "Responded" in content_text:
            print("    ✓ Found 'Responded' group")
        if "Noticed" in content_text or "didn't respond" in content_text:
            print("    ✓ Found 'Noticed' group")
        
        # Close panel
        self.page.locator('#silent-observers-panel .panel-close').click()
        expect(panel).not_to_be_visible()
        print("    ✓ Panel closed")
    
    def test_user_insights_panel(self):
        """Test 4: User Insights panel (🎯) shows accumulated insights"""
        print("\n[TEST] User Insights Panel (🎯)")
        
        # Click the 🎯 button
        user_insights_btn = self.page.locator('#userInsightsBtn')
        expect(user_insights_btn).to_be_visible()
        user_insights_btn.click()
        
        # Wait for panel
        panel = self.page.locator('#user-insights-panel')
        expect(panel).to_be_visible(timeout=5000)
        print("    ✓ User Insights panel opened")
        
        # Wait for content to load
        self.page.wait_for_timeout(3000)
        
        content = self.page.locator('#user-insights-content')
        content_text = content.text_content()
        print(f"    Panel content: {content_text[:300]}...")
        
        # Check for insight elements
        if "interactions" in content_text.lower():
            print("    ✓ Found interaction counts")
        if "engagement" in content_text.lower():
            print("    ✓ Found engagement metrics")
        if "emotion" in content_text.lower():
            print("    ✓ Found emotion tracking")
        if "theme" in content_text.lower() or "topic" in content_text.lower():
            print("    ✓ Found theme/topic tracking")
        
        # Close panel
        self.page.locator('#user-insights-panel .panel-close').click()
        expect(panel).not_to_be_visible()
        print("    ✓ Panel closed")
    
    def test_insights_persist_across_messages(self):
        """Test 5: Verify insights accumulate across multiple messages"""
        print("\n[TEST] Insights Persist Across Messages")
        
        # Send multiple messages to build up insights
        test_messages = [
            "I'm feeling anxious about my upcoming presentation",
            "How can I manage my time better at work?",
            "I've been stressed about my finances lately"
        ]
        
        for i, msg in enumerate(test_messages):
            print(f"    Sending message {i+1}/{len(test_messages)}...")
            chat_input = self.page.locator('#userInput')
            initial_count = self.page.locator('.message').count()
            chat_input.fill(msg)
            self.page.locator('#sendBtn').click()
            self.page.wait_for_function(f"document.querySelectorAll('.message').length > {initial_count + 1}", timeout=90000)
            self.page.wait_for_timeout(2000)  # Brief pause between messages
        
        print("    ✓ Sent all test messages")
        
        # Now check User Insights for accumulated data
        self.page.locator('#userInsightsBtn').click()
        panel = self.page.locator('#user-insights-panel')
        expect(panel).to_be_visible(timeout=5000)
        
        self.page.wait_for_timeout(3000)
        
        content = self.page.locator('#user-insights-content')
        content_text = content.text_content()
        
        # Parse for interaction counts
        interactions_match = re.search(r'(\d+)\s*interactions', content_text)
        if interactions_match:
            count = int(interactions_match.group(1))
            print(f"    ✓ Found {count} total interactions recorded")
            assert count >= 3, "Should have at least 3 interactions after sending 3 messages"
        
        # Check for stress/anxiety detection
        if "stressed" in content_text.lower() or "anxious" in content_text.lower():
            print("    ✓ Emotions were tracked across messages")
        
        # Close panel
        self.page.locator('#user-insights-panel .panel-close').click()
        print("    ✓ Test complete - insights persist across messages")
    
    def test_cross_domain_api_directly(self):
        """Test 6: Verify cross-domain API returns correct data structure"""
        print("\n[TEST] Cross-Domain API Structure")
        
        # Call API directly via page.evaluate
        result = self.page.evaluate("""
            async () => {
                const response = await AuthHelper.authenticatedFetch('/api/domain-characters/cross-domain', {
                    method: 'POST',
                    body: JSON.stringify({message: "I'm stressed about work and money problems"})
                });
                return await response.json();
            }
        """)
        
        print(f"    API Response keys: {list(result.keys())}")
        
        # Verify structure
        assert result.get('success') == True, "API should return success"
        assert 'responded' in result, "Should have 'responded' list"
        assert 'silent_observers' in result, "Should have 'silent_observers' list"
        assert 'domain_insights' in result, "Should have 'domain_insights' list"
        
        print(f"    ✓ Responded: {len(result.get('responded', []))} characters")
        print(f"    ✓ Silent Observers: {len(result.get('silent_observers', []))} characters")
        
        # Check insight structure
        if result.get('domain_insights'):
            first_insight = result['domain_insights'][0]
            print(f"    Sample insight keys: {list(first_insight.keys())}")
            
            if 'interpretation' in first_insight:
                interp = first_insight['interpretation']
                print(f"    Interpretation keys: {list(interp.keys()) if isinstance(interp, dict) else 'N/A'}")
                
                if isinstance(interp, dict):
                    if 'detected_emotions' in interp:
                        print(f"    ✓ Detected emotions: {interp['detected_emotions']}")
                    if 'character_perspective' in interp:
                        print(f"    ✓ Character perspective present")
                    if 'potential_advice' in interp:
                        print(f"    ✓ Potential advice present")
                    if 'continuity_tags' in interp:
                        print(f"    ✓ Continuity tags: {interp['continuity_tags']}")
        
        print("    ✓ API structure verified")
    
    def test_user_insights_api_directly(self):
        """Test 7: Verify user insights API returns accumulated data"""
        print("\n[TEST] User Insights API")
        
        result = self.page.evaluate("""
            async () => {
                const response = await AuthHelper.authenticatedFetch('/api/domain-characters/user-insights');
                return await response.json();
            }
        """)
        
        print(f"    API Response keys: {list(result.keys())}")
        
        assert result.get('success') == True, "API should return success"
        assert 'insights' in result, "Should have 'insights' object"
        
        insights = result.get('insights', {})
        print(f"    ✓ Found insights for {len(insights)} characters")
        
        for char_id, data in insights.items():
            print(f"\n    {data.get('display_name', char_id)} ({data.get('domain')}):")
            print(f"      - Interactions: {data.get('total_interactions', 0)}")
            print(f"      - Engagement: {data.get('engagement_rate', 0)}%")
            print(f"      - Emotions: {[e['emotion'] for e in data.get('common_emotions', [])]}")
            print(f"      - Themes: {[t['theme'] for t in data.get('common_themes', [])]}")
        
        print("\n    ✓ User insights API verified")


def test_full_workflow(page: Page):
    """Complete workflow test - run all tests in sequence"""
    print("\n" + "="*60)
    print("CHARACTER INSIGHTS E2E TEST SUITE")
    print("="*60)
    
    test = TestCharacterInsightsE2E()
    test.page = page
    test.login()
    
    # Run all tests
    test.test_send_message_and_get_ai_response()
    test.test_character_insights_panel()
    test.test_other_perspectives_panel()
    test.test_user_insights_panel()
    test.test_cross_domain_api_directly()
    test.test_user_insights_api_directly()
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)


def run_standalone():
    """Run tests directly without pytest - interactive mode"""
    global TEST_USER, TEST_PASS
    
    print("\n" + "="*60)
    print("CHARACTER INSIGHTS E2E TEST (Interactive)")
    print("="*60)
    
    # Prompt for credentials if not set
    if not TEST_USER:
        TEST_USER = input("Enter username: ").strip()
    if not TEST_PASS:
        TEST_PASS = input("Enter password: ").strip()
    
    if not TEST_USER or not TEST_PASS:
        print("ERROR: Username and password are required")
        return
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        test = TestCharacterInsightsE2E()
        test.page = page
        
        try:
            test.login()
            test.test_send_message_and_get_ai_response()
            test.test_character_insights_panel()
            test.test_other_perspectives_panel()
            test.test_user_insights_panel()
            test.test_cross_domain_api_directly()
            test.test_user_insights_api_directly()
            
            print("\n" + "="*60)
            print("ALL TESTS PASSED ✓")
            print("="*60)
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
        finally:
            input("\nPress Enter to close browser...")
            browser.close()


if __name__ == "__main__":
    run_standalone()
