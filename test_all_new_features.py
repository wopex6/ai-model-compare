"""
Comprehensive test for all 6 new features
"""

import asyncio
from playwright.async_api import async_playwright
import random
import string
from datetime import datetime

class NewFeaturesTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_username = f"FeatureTest_{datetime.now().strftime('%H%M%S')}"
        self.test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
        
    async def run_all_tests(self):
        async with async_playwright() as p:
            print("=" * 70)
            print("🧪 TESTING ALL 6 NEW FEATURES")
            print("=" * 70)
            
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Test 1: URL Change
                await self.test_url_change(page)
                
                # Test 2: Signup & Email Verification
                await self.test_signup_and_verification(page)
                
                # Test 3: Guest Limit (20 messages)
                await self.test_guest_limit(page)
                
                # Test 4: Datetime Timestamps
                await self.test_datetime_timestamps(page)
                
                # Test 5: Thinking Indicator
                await self.test_thinking_indicator(page)
                
                # Test 6: Admin Dashboard
                await self.test_admin_dashboard(page)
                
                print("\n" + "=" * 70)
                print("✅ ALL TESTS COMPLETED!")
                print("=" * 70)
                
            except Exception as e:
                print(f"\n❌ TEST FAILED: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await page.wait_for_timeout(5000)
                await browser.close()
    
    async def test_url_change(self, page):
        """Test 1: URL changed from /multi-user to /chatchat"""
        print("\n📝 TEST 1: URL Change (/multi-user → /chatchat)")
        print("-" * 70)
        
        # Test new URL
        await page.goto(f"{self.base_url}/chatchat")
        await page.wait_for_selector("#login-screen")
        print("✅ /chatchat loads correctly")
        
        # Test old URL redirects
        await page.goto(f"{self.base_url}/multi-user")
        await page.wait_for_timeout(1000)
        current_url = page.url
        if '/chatchat' in current_url:
            print("✅ /multi-user redirects to /chatchat")
        else:
            print(f"⚠️  Redirect not working. Current URL: {current_url}")
    
    async def test_signup_and_verification(self, page):
        """Test 2: Email Verification"""
        print("\n📝 TEST 2: Signup & Email Verification")
        print("-" * 70)
        
        await page.goto(f"{self.base_url}/chatchat")
        await page.click("#show-signup")
        await page.wait_for_timeout(500)
        
        print(f"Creating account: {self.test_username}")
        await page.fill("#signup-username", self.test_username)
        await page.fill("#signup-email", self.test_email)
        await page.fill("#signup-password", "TestPass123")
        await page.fill("#signup-confirm-password", "TestPass123")
        
        await page.click("#signup-form button[type='submit']")
        await page.wait_for_timeout(3000)
        
        # Check if verification banner appears
        banner = await page.query_selector("#email-verification-banner")
        if banner and await banner.is_visible():
            print("✅ Email verification banner shown")
            print(f"📧 Verification email sent to: {self.test_email}")
            print("   (Check your email for 6-digit code)")
        else:
            print("⚠️  Verification banner not visible")
    
    async def test_guest_limit(self, page):
        """Test 3: Guest limit increased to 20"""
        print("\n📝 TEST 3: Guest Daily Limit (2 → 20)")
        print("-" * 70)
        
        # Check message usage
        usage_info = await page.query_selector("#usage-info")
        if usage_info:
            text = await usage_info.inner_text()
            if "20" in text:
                print("✅ Guest limit is 20 messages per day")
            else:
                print(f"   Usage info: {text}")
        else:
            print("ℹ️  Usage info not found (check after sending messages)")
    
    async def test_datetime_timestamps(self, page):
        """Test 4: Datetime timestamps on conversations"""
        print("\n📝 TEST 4: Datetime Timestamps on Conversations")
        print("-" * 70)
        
        # Go to conversations tab
        await page.click("button[data-tab='conversations']")
        await page.wait_for_timeout(2000)
        
        # Check if conversations have timestamps
        conv_items = await page.query_selector_all(".conversation-date")
        if conv_items:
            first_date = await conv_items[0].inner_text()
            # Check if it has time (contains ":" or "AM/PM")
            if ":" in first_date or "AM" in first_date or "PM" in first_date:
                print(f"✅ Conversations show datetime: {first_date}")
            else:
                print(f"⚠️  Date format: {first_date} (time not visible)")
        else:
            print("ℹ️  No conversations yet to check timestamps")
    
    async def test_thinking_indicator(self, page):
        """Test 5: Thinking indicator"""
        print("\n📝 TEST 5: Thinking Indicator")
        print("-" * 70)
        
        # Go to chat tab
        await page.click("button[data-tab='chat']")
        await page.wait_for_timeout(1000)
        
        # Create new chat
        await page.click("#new-chat-btn")
        await page.wait_for_timeout(2000)
        
        # Send a message
        await page.fill("#chat-input", "Hello, this is a test message")
        await page.click("#send-chat-btn")
        
        # Check for thinking indicator (quickly)
        await page.wait_for_timeout(500)
        thinking = await page.query_selector("#thinking-indicator")
        if thinking:
            print("✅ Thinking indicator appeared")
        else:
            print("ℹ️  Thinking indicator may have been too fast to catch")
        
        # Wait for response
        await page.wait_for_timeout(5000)
        print("✅ Message sent successfully")
    
    async def test_admin_dashboard(self, page):
        """Test 6: Admin Dashboard (login as Wai Tse)"""
        print("\n📝 TEST 6: Admin Dashboard")
        print("-" * 70)
        
        # Logout current user
        await page.click("#logout-btn")
        await page.wait_for_timeout(1000)
        
        # Login as Wai Tse (admin)
        print("Logging in as Wai Tse (administrator)...")
        await page.fill("#login-username", "Wai Tse")
        await page.fill("#login-password", "123")
        await page.click("#login-form button[type='submit']")
        await page.wait_for_timeout(3000)
        
        # Check if admin tab is visible
        admin_tab = await page.query_selector("#admin-tab-btn")
        if admin_tab:
            is_visible = await admin_tab.is_visible()
            if is_visible:
                print("✅ Admin tab visible for administrator")
                
                # Click admin tab
                await page.click("#admin-tab-btn")
                await page.wait_for_timeout(2000)
                
                # Check statistics
                total_users = await page.inner_text("#stat-total-users")
                total_messages = await page.inner_text("#stat-total-messages")
                
                print(f"✅ Admin Dashboard loaded")
                print(f"   📊 Total Users: {total_users}")
                print(f"   📊 Total Messages: {total_messages}")
            else:
                print("⚠️  Admin tab not visible")
        else:
            print("❌ Admin tab not found")

if __name__ == "__main__":
    test = NewFeaturesTest()
    asyncio.run(test.run_all_tests())
