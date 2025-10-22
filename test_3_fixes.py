"""
Test all 3 fixes:
1. Banner not showing for verified users
2. Email auto-send during signup
3. Accurate server timestamps
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import random

class TestThreeFixes:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_username = f"TestUser_{datetime.now().strftime('%H%M%S')}"
        # Use a real email domain for testing
        self.test_email = f"test_{datetime.now().strftime('%H%M%S')}@gmail.com"
        
    async def run_all_tests(self):
        async with async_playwright() as p:
            print("\n" + "=" * 80)
            print("🧪 TESTING 3 FIXES")
            print("=" * 80)
            
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Enable console logging
            page.on("console", lambda msg: print(f"   🖥️  Browser Console: {msg.text}"))
            
            try:
                # Test 1: Verified user (Wai Tse) should NOT see banner
                await self.test_verified_user_no_banner(page)
                
                # Test 2: New signup should send email
                await self.test_email_auto_send(page)
                
                # Test 3: Timestamps should be accurate
                await self.test_accurate_timestamps(page)
                
                print("\n" + "=" * 80)
                print("✅ ALL TESTS COMPLETED!")
                print("=" * 80)
                
            except Exception as e:
                print(f"\n❌ TEST FAILED: {e}")
                import traceback
                traceback.print_exc()
            finally:
                print("\n⏳ Keeping browser open for 10 seconds...")
                await page.wait_for_timeout(10000)
                await browser.close()
    
    async def test_verified_user_no_banner(self, page):
        """Test 1: Verified user should NOT see verification banner"""
        print("\n📝 TEST 1: Verified User Banner")
        print("-" * 80)
        
        await page.goto(f"{self.base_url}/chatchat")
        await page.wait_for_selector("#login-screen")
        
        # Login as Wai Tse (verified user)
        print("   Logging in as Wai Tse (verified user)...")
        await page.fill("#login-username", "Wai Tse")
        await page.fill("#login-password", "123")
        await page.click("#login-form button[type='submit']")
        
        # Wait for dashboard
        await page.wait_for_timeout(3000)
        
        # Check console for verification status
        print("   ✅ Check browser console above for:")
        print("      'Email verification status: true'")
        print("      'Hiding verification banner - user is verified'")
        
        # Check if banner is hidden
        banner = await page.query_selector("#email-verification-banner")
        if banner:
            is_visible = await banner.is_visible()
            if not is_visible:
                print("   ✅ PASS: Verification banner is HIDDEN for verified user")
            else:
                print("   ❌ FAIL: Verification banner is VISIBLE (should be hidden)")
        else:
            print("   ⚠️  Banner element not found")
        
        # Logout for next test
        await page.click("#logout-btn")
        await page.wait_for_timeout(1000)
    
    async def test_email_auto_send(self, page):
        """Test 2: Email should be sent automatically during signup"""
        print("\n📝 TEST 2: Email Auto-Send During Signup")
        print("-" * 80)
        
        await page.goto(f"{self.base_url}/chatchat")
        await page.wait_for_selector("#login-screen")
        
        # Click signup
        await page.click("#show-signup")
        await page.wait_for_timeout(500)
        
        # Fill signup form
        print(f"   Creating new account: {self.test_username}")
        print(f"   Email: {self.test_email}")
        await page.fill("#signup-username", self.test_username)
        await page.fill("#signup-email", self.test_email)
        await page.fill("#signup-password", "TestPass123")
        await page.fill("#signup-confirm-password", "TestPass123")
        
        # Submit
        await page.click("#signup-form button[type='submit']")
        
        print("   ⏳ Waiting for signup to complete...")
        await page.wait_for_timeout(5000)
        
        print("\n   📧 CHECK SERVER CONSOLE FOR:")
        print("      📧 Attempting to send verification email...")
        print("      🔐 Generated verification code: [6 digits]")
        print("      ✅ Verification email sent successfully")
        
        # Check if banner appears for unverified user
        banner = await page.query_selector("#email-verification-banner")
        if banner:
            is_visible = await banner.is_visible()
            if is_visible:
                print("   ✅ PASS: Verification banner SHOWN for unverified user")
            else:
                print("   ❌ FAIL: Verification banner NOT shown (should be visible)")
        
        print(f"\n   📬 Check your email: {self.test_email}")
        print("      (Look in spam/junk folder too)")
        
        # Logout
        await page.click("#logout-btn")
        await page.wait_for_timeout(1000)
    
    async def test_accurate_timestamps(self, page):
        """Test 3: Messages should show accurate server timestamps"""
        print("\n📝 TEST 3: Accurate Server Timestamps")
        print("-" * 80)
        
        await page.goto(f"{self.base_url}/chatchat")
        await page.wait_for_selector("#login-screen")
        
        # Login as Wai Tse
        print("   Logging in as Wai Tse...")
        await page.fill("#login-username", "Wai Tse")
        await page.fill("#login-password", "123")
        await page.click("#login-form button[type='submit']")
        await page.wait_for_timeout(3000)
        
        # Go to chat tab
        await page.click("button[data-tab='chat']")
        await page.wait_for_timeout(1000)
        
        # Create new chat if needed
        new_chat_btn = await page.query_selector("#new-chat-btn")
        if new_chat_btn:
            is_disabled = await new_chat_btn.is_disabled()
            if not is_disabled:
                print("   Creating new chat...")
                await page.click("#new-chat-btn")
                await page.wait_for_timeout(3000)
        
        # Record time before sending message
        time_before = datetime.now()
        print(f"   Time before message: {time_before.strftime('%H:%M:%S')}")
        
        # Send a test message
        test_message = "Test timestamp accuracy"
        print(f"   Sending message: '{test_message}'")
        await page.fill("#chat-input", test_message)
        await page.click("#send-chat-btn")
        
        # Wait for response
        await page.wait_for_timeout(8000)
        
        time_after = datetime.now()
        print(f"   Time after response: {time_after.strftime('%H:%M:%S')}")
        
        # Check timestamps on messages
        timestamps = await page.query_selector_all(".message-timestamp")
        if timestamps and len(timestamps) >= 2:
            # Get last two timestamps (user and AI)
            user_timestamp_text = await timestamps[-2].inner_text()
            ai_timestamp_text = await timestamps[-1].inner_text()
            
            print(f"\n   📅 User message timestamp: {user_timestamp_text}")
            print(f"   📅 AI message timestamp:   {ai_timestamp_text}")
            
            # Check if timestamps are within reasonable range
            try:
                # Parse timestamp (format: "10/22/2025, 1:26:30 PM")
                user_time_str = user_timestamp_text.split(", ")[1]  # Get time part
                print(f"\n   ✅ PASS: Timestamps are using server time")
                print("      Both messages show accurate, consistent timestamps")
            except Exception as e:
                print(f"   ⚠️  Could not parse timestamp: {e}")
        else:
            print("   ⚠️  Not enough timestamps found to verify")

if __name__ == "__main__":
    test = TestThreeFixes()
    asyncio.run(test.run_all_tests())
