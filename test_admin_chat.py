"""
Comprehensive test for:
1. Password clearing on logout
2. User-Admin chat system (both sides)
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

class TestAdminChat:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_username = f"ChatTest_{datetime.now().strftime('%H%M%S')}"
        self.test_email = f"chattest_{datetime.now().strftime('%H%M%S')}@test.com"
        
    async def run_all_tests(self):
        async with async_playwright() as p:
            print("\n" + "=" * 80)
            print("🧪 TESTING: Password Clear & Admin Chat System")
            print("=" * 80)
            
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Enable console logging
            page.on("console", lambda msg: print(f"   🖥️  Console: {msg.text}"))
            
            try:
                # Test 1: Password clearing on logout
                await self.test_password_clear(page)
                
                # Test 2: User sends message to admin
                await self.test_user_sends_message(page)
                
                # Test 3: Admin views and replies
                await self.test_admin_reply(page)
                
                # Test 4: User sees admin reply with badge
                await self.test_user_sees_reply(page)
                
                print("\n" + "=" * 80)
                print("✅ ALL TESTS COMPLETED!")
                print("=" * 80)
                
            except Exception as e:
                print(f"\n❌ TEST FAILED: {e}")
                import traceback
                traceback.print_exc()
            finally:
                print("\n⏳ Keeping browser open for 15 seconds...")
                await page.wait_for_timeout(15000)
                await browser.close()
    
    async def test_password_clear(self, page):
        """Test 1: Password field clears on logout"""
        print("\n📝 TEST 1: Password Clearing on Logout")
        print("-" * 80)
        
        await page.goto(f"{self.base_url}/chatchat")
        await page.wait_for_selector("#login-screen")
        
        # Login as Wai Tse
        print("   Logging in as Wai Tse...")
        await page.fill("#login-username", "Wai Tse")
        await page.fill("#login-password", "123")
        await page.click("#login-form button[type='submit']")
        
        await page.wait_for_timeout(3000)
        
        # Logout
        print("   Logging out...")
        await page.click("#logout-btn")
        await page.wait_for_timeout(1000)
        
        # Check if password field is empty
        password_value = await page.input_value("#login-password")
        if password_value == "":
            print("   ✅ PASS: Password field is EMPTY after logout")
        else:
            print(f"   ❌ FAIL: Password field contains: '{password_value}'")
    
    async def test_user_sends_message(self, page):
        """Test 2: User sends message to admin"""
        print("\n📝 TEST 2: User Sends Message to Admin")
        print("-" * 80)
        
        # Create new user
        print(f"   Creating new user: {self.test_username}")
        await page.click("#show-signup")
        await page.wait_for_timeout(500)
        
        await page.fill("#signup-username", self.test_username)
        await page.fill("#signup-email", self.test_email)
        await page.fill("#signup-password", "Test123")
        await page.fill("#signup-confirm-password", "Test123")
        await page.click("#signup-form button[type='submit']")
        
        await page.wait_for_timeout(3000)
        
        # Go to Contact Admin tab
        print("   Navigating to Contact Admin...")
        await page.click("button[data-tab='admin-chat']")
        await page.wait_for_timeout(2000)
        
        # Send message
        test_message = f"Hello Admin! This is a test message from {self.test_username}"
        print(f"   Sending message: '{test_message}'")
        await page.fill("#admin-chat-input", test_message)
        await page.click("#send-admin-message-btn")
        
        await page.wait_for_timeout(2000)
        
        # Check if message appears
        messages = await page.query_selector_all("#admin-chat-messages > div")
        if len(messages) > 0:
            print("   ✅ PASS: Message sent and displayed")
        else:
            print("   ❌ FAIL: Message not displayed")
        
        # Logout
        await page.click("#logout-btn")
        await page.wait_for_timeout(1000)
    
    async def test_admin_reply(self, page):
        """Test 3: Admin views messages and replies"""
        print("\n📝 TEST 3: Admin Views and Replies to User Message")
        print("-" * 80)
        
        # Login as admin
        print("   Logging in as Wai Tse (Admin)...")
        await page.fill("#login-username", "Wai Tse")
        await page.fill("#login-password", "123")
        await page.click("#login-form button[type='submit']")
        
        await page.wait_for_timeout(3000)
        
        # Go to Admin tab
        print("   Navigating to Admin Dashboard...")
        await page.click("button[data-tab='admin']")
        await page.wait_for_timeout(2000)
        
        # Check if user appears in list
        print("   Looking for user in admin chat list...")
        user_items = await page.query_selector_all(".admin-chat-user-item")
        
        if len(user_items) > 0:
            print(f"   ✅ Found {len(user_items)} user(s) with messages")
            
            # Click on the first user (our test user)
            print("   Clicking on user to view messages...")
            await user_items[0].click()
            await page.wait_for_timeout(2000)
            
            # Check if messages loaded
            messages = await page.query_selector_all("#admin-chat-messages-view > div")
            print(f"   Found {len(messages)} message(s)")
            
            # Send reply
            reply_message = "Hello! This is an admin reply to your message."
            print(f"   Sending admin reply: '{reply_message}'")
            await page.fill("#admin-reply-input", reply_message)
            await page.click("#send-admin-reply-btn")
            
            await page.wait_for_timeout(2000)
            
            # Check if reply appears
            messages_after = await page.query_selector_all("#admin-chat-messages-view > div")
            if len(messages_after) > len(messages):
                print("   ✅ PASS: Admin reply sent successfully")
            else:
                print("   ❌ FAIL: Admin reply not sent")
        else:
            print("   ❌ FAIL: No users found in admin chat list")
        
        # Logout
        await page.click("#logout-btn")
        await page.wait_for_timeout(1000)
    
    async def test_user_sees_reply(self, page):
        """Test 4: User sees admin reply with badge"""
        print("\n📝 TEST 4: User Sees Admin Reply with Badge")
        print("-" * 80)
        
        # Login as test user
        print(f"   Logging back in as {self.test_username}...")
        await page.fill("#login-username", self.test_username)
        await page.fill("#login-password", "Test123")
        await page.click("#login-form button[type='submit']")
        
        await page.wait_for_timeout(3000)
        
        # Check for unread badge
        print("   Checking for unread message badge...")
        badge = await page.query_selector("#admin-chat-badge")
        
        if badge:
            is_visible = await badge.is_visible()
            if is_visible:
                badge_text = await badge.inner_text()
                print(f"   ✅ PASS: Badge is visible with count: {badge_text}")
            else:
                print("   ⚠️  Badge exists but not visible")
        else:
            print("   ⚠️  Badge element not found")
        
        # Go to Contact Admin tab
        print("   Opening Contact Admin tab...")
        await page.click("button[data-tab='admin-chat']")
        await page.wait_for_timeout(2000)
        
        # Check if admin reply is visible
        messages = await page.query_selector_all("#admin-chat-messages > div")
        print(f"   Found {len(messages)} message(s) in conversation")
        
        if len(messages) >= 2:
            print("   ✅ PASS: User can see both their message and admin reply")
        else:
            print("   ❌ FAIL: Not enough messages visible")
        
        # Check if badge disappeared
        await page.wait_for_timeout(1000)
        badge_after = await page.query_selector("#admin-chat-badge")
        if badge_after:
            is_visible_after = await badge_after.is_visible()
            if not is_visible_after:
                print("   ✅ PASS: Badge hidden after viewing messages")
            else:
                print("   ⚠️  Badge still visible")

if __name__ == "__main__":
    test = TestAdminChat()
    asyncio.run(test.run_all_tests())
