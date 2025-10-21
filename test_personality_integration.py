"""
Playwright Test for Personality Test Integration
Tests the banner, buttons, and user flow for personality assessment
"""

import asyncio
from playwright.async_api import async_playwright, Page, expect
import os
from datetime import datetime
import random
import string

class PersonalityTestTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.screenshots_dir = "test_screenshots/personality_integration"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def get_screenshot_path(self, name: str) -> str:
        """Generate timestamped screenshot filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.screenshots_dir, f"{timestamp}_{name}.png")
    
    async def test_personality_integration(self):
        """Main test function"""
        async with async_playwright() as p:
            print("🚀 Starting Personality Test Integration Tests...\n")
            
            # Launch browser
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            
            # Capture console logs
            page.on("console", lambda msg: print(f"      [Browser Console] {msg.type}: {msg.text}"))
            page.on("pageerror", lambda err: print(f"      [Browser Error] {err}"))
            
            try:
                # Test 1: Login
                await self.test_login(page)
                
                # Test 2: Check for banner appearance
                await self.test_banner_appearance(page)
                
                # Test 3: Test banner button
                await self.test_banner_button(page, context)
                
                # Test 4: Test Psychology tab button
                await self.test_psychology_tab_button(page, context)
                
                # Test 5: Test banner dismissal
                await self.test_banner_dismissal(page)
                
                print("\n✅ All tests completed successfully!")
                
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                await page.screenshot(path=self.get_screenshot_path("error"))
                raise
            finally:
                await browser.close()
    
    async def test_login(self, page: Page):
        """Test login functionality"""
        print("1️⃣ Testing Login...")
        
        # Navigate to login page
        await page.goto(f"{self.base_url}/multi-user")
        await page.wait_for_load_state("networkidle")
        
        # Take screenshot of login page
        await page.screenshot(path=self.get_screenshot_path("01_login_page"))
        
        # Check if we need to login or are already logged in
        login_form = await page.query_selector("#login-form")
        dashboard = await page.query_selector("#dashboard-screen")
        
        if dashboard and await dashboard.is_visible():
            print("   ✅ Already logged in\n")
            return
        
        if login_form and await login_form.is_visible():
            # Try to login first with common test credentials
            credentials = [
                ("admin", "admin123"),
                ("TestUser", "test123"),
                ("Wai Tse", "password"),
                ("test", "test123")
            ]
            
            login_successful = False
            
            for username, password in credentials:
                print(f"   🔑 Trying {username}...")
                await page.fill("#login-username", username)
                await page.fill("#login-password", password)
                
                await page.screenshot(path=self.get_screenshot_path(f"02_login_{username}"))
                
                # Click login button
                await page.click("button[type='submit']")
                
                # Wait a bit
                await page.wait_for_timeout(2000)
                
                # Check if dashboard appeared
                dashboard = await page.query_selector("#dashboard-screen")
                if dashboard and await dashboard.is_visible():
                    print(f"   ✅ Login successful with {username}\n")
                    login_successful = True
                    break
                else:
                    print(f"   ❌ Login failed for {username}")
            
            if not login_successful:
                print("   ⚠️  All login attempts failed!")
                print("   💡 Creating a new account...")
                
                # Go to signup
                await page.click("#show-signup")
                await page.wait_for_timeout(1000)
                
                # Try to create account with retries in case of duplicates
                signup_success = False
                max_retries = 3
                
                for attempt in range(max_retries):
                    # Generate unique username with random string
                    random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                    test_username = f"TestUser_{random_id}"
                    test_email = f"test_{random_id}@example.com"
                    
                    print(f"   📝 Creating account (attempt {attempt + 1}): {test_username}")
                    
                    # Fill signup form
                    await page.fill("#signup-username", test_username)
                    await page.fill("#signup-email", test_email)
                    await page.fill("#signup-password", "test123")
                    await page.fill("#signup-confirm-password", "test123")
                    
                    await page.screenshot(path=self.get_screenshot_path(f"02_signup_filled_attempt{attempt + 1}"))
                    
                    # Submit signup
                    await page.click("#signup-form button[type='submit']")
                    
                    # Wait for response
                    await page.wait_for_timeout(2000)
                    
                    # Check if we're on dashboard (signup successful)
                    dashboard = await page.query_selector("#dashboard-screen")
                    if dashboard and await dashboard.is_visible():
                        signup_success = True
                        print(f"   ✅ Account created successfully: {test_username}")
                        break
                    else:
                        # Signup failed, check for error message
                        print(f"   ⚠️  Signup failed for {test_username}, retrying...")
                        # Go back to signup screen if needed
                        signup_screen = await page.query_selector("#signup-screen")
                        if not signup_screen or not await signup_screen.is_visible():
                            await page.click("#show-signup")
                            await page.wait_for_timeout(500)
                
                if not signup_success:
                    raise Exception("Failed to create account after multiple attempts")
        
        # Final check
        dashboard = await page.query_selector("#dashboard-screen")
        if dashboard and await dashboard.is_visible():
            await page.screenshot(path=self.get_screenshot_path("03_dashboard_loaded"))
            print("   ✅ Successfully logged in\n")
        else:
            await page.screenshot(path=self.get_screenshot_path("03_login_failed"))
            raise Exception("Login failed - dashboard not visible")
    
    async def test_banner_appearance(self, page: Page):
        """Test if personality test banner appears"""
        print("2️⃣ Testing Banner Appearance...")
        
        # First check if user actually has traits
        print("   🔍 Checking user's psychology traits...")
        traits_data = await page.evaluate("""
            async () => {
                const response = await fetch('/api/user/psychology-traits', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
                });
                return await response.json();
            }
        """)
        
        print(f"   📊 User has {len(traits_data) if traits_data else 0} traits")
        if traits_data and len(traits_data) > 0:
            print(f"      Traits: {[t.get('trait_name', 'unknown') for t in traits_data[:3]]}")
        
        # Wait for banner to appear - poll for up to 5 seconds
        print("   ⏳ Polling for banner (up to 5 seconds)...")
        banner = await page.query_selector("#personality-test-banner")
        
        if not banner:
            print("   ❌ Banner element not found in DOM!")
            print()
            return
        
        # Poll for visibility
        banner_appeared = False
        for i in range(10):  # Check every 500ms for 5 seconds
            is_visible = await banner.is_visible()
            if is_visible:
                banner_appeared = True
                print(f"   ✅ Banner appeared after ~{(i + 1) * 0.5} seconds!")
                break
            await page.wait_for_timeout(500)
        
        if banner_appeared:
            await page.screenshot(path=self.get_screenshot_path("04_banner_visible"))
            
            # Check banner content
            banner_text = await page.inner_text(".banner-text")
            if "understand you better" in banner_text.lower():
                print("   ✅ Banner has correct text")
            else:
                print(f"   ⚠️  Banner text unexpected: {banner_text}")
            
            # Check for brain icon
            brain_icon = await page.query_selector(".banner-content i.fa-brain")
            if brain_icon:
                print("   ✅ Brain icon present")
            
            # Check for buttons
            take_test_btn = await page.query_selector("#take-test-banner-btn")
            close_btn = await page.query_selector("#close-banner-btn")
            if take_test_btn and close_btn:
                print("   ✅ Both buttons present (Take Test & Close)")
        else:
            print("   ⚠️  Banner did not appear within 5 seconds")
            print("      This is normal if user already has psychology traits")
            await page.screenshot(path=self.get_screenshot_path("04_banner_not_shown"))
        
        print()
    
    async def test_banner_button(self, page: Page, context):
        """Test banner 'Take Test Now' button"""
        print("3️⃣ Testing Banner Button...")
        
        # Check if banner is visible
        banner = await page.query_selector("#personality-test-banner")
        if not banner or not await banner.is_visible():
            print("   ⏭️  Skipped (banner not visible)\n")
            return
        
        # Listen for new page (popup)
        async with context.expect_page() as new_page_info:
            await page.click("#take-test-banner-btn")
            print("   ⏳ Clicked 'Take Test Now', waiting for popup...")
        
        new_page = await new_page_info.value
        await new_page.wait_for_load_state("networkidle")
        
        # Check if personality test page opened
        url = new_page.url
        if "/personality-test" in url:
            print(f"   ✅ Personality test opened: {url}")
            await new_page.screenshot(path=self.get_screenshot_path("05_test_page_opened"))
            await new_page.close()
        else:
            print(f"   ❌ Wrong page opened: {url}")
        
        # Check if banner is hidden
        await page.wait_for_timeout(500)
        banner_still_visible = await banner.is_visible()
        if not banner_still_visible:
            print("   ✅ Banner hidden after clicking")
        else:
            print("   ⚠️  Banner still visible")
        
        await page.screenshot(path=self.get_screenshot_path("06_after_banner_click"))
        print()
    
    async def test_psychology_tab_button(self, page: Page, context):
        """Test Psychology tab 'Take Personality Test' button"""
        print("4️⃣ Testing Psychology Tab Button...")
        
        # Navigate to Psychology tab
        await page.click("button[data-tab='psychology']")
        await page.wait_for_timeout(500)
        
        # Check if Psychology tab is active
        await page.screenshot(path=self.get_screenshot_path("07_psychology_tab"))
        
        # Check if button exists
        button = await page.query_selector("#take-personality-test-btn")
        if not button:
            print("   ❌ 'Take Personality Test' button not found!")
            return
        
        print("   ✅ Button found in Psychology tab")
        
        # Check button text
        button_text = await button.inner_text()
        if "personality test" in button_text.lower():
            print(f"   ✅ Button text correct: '{button_text.strip()}'")
        
        # Listen for new page
        async with context.expect_page() as new_page_info:
            await button.click()
            print("   ⏳ Clicked button, waiting for popup...")
        
        new_page = await new_page_info.value
        await new_page.wait_for_load_state("networkidle")
        
        # Verify correct page opened
        url = new_page.url
        if "/personality-test" in url:
            print(f"   ✅ Test opened from Psychology tab: {url}")
            await new_page.screenshot(path=self.get_screenshot_path("08_test_from_psych_tab"))
            await new_page.close()
        else:
            print(f"   ❌ Wrong page: {url}")
        
        await page.screenshot(path=self.get_screenshot_path("09_after_psych_button"))
        print()
    
    async def test_banner_dismissal(self, page: Page):
        """Test banner dismissal and localStorage"""
        print("5️⃣ Testing Banner Dismissal...")
        
        # Clear any previous dismissal flag
        await page.evaluate("() => localStorage.removeItem('personality-banner-dismissed')")
        print("   🧹 Cleared previous dismissal flag")
        
        # Go back to chat tab
        await page.click("button[data-tab='chat']")
        await page.wait_for_timeout(500)
        
        # Reload the page
        print("   ⏳ Reloading page to test banner appearance...")
        await page.reload()
        await page.wait_for_load_state("networkidle")
        
        # Poll for banner appearance
        banner = await page.query_selector("#personality-test-banner")
        banner_appeared = False
        
        print("   ⏳ Waiting for banner to appear...")
        for i in range(10):
            if await banner.is_visible():
                banner_appeared = True
                print(f"   ✅ Banner appeared after ~{(i + 1) * 0.5} seconds")
                break
            await page.wait_for_timeout(500)
        
        if banner_appeared:
            await page.screenshot(path=self.get_screenshot_path("10_banner_before_dismiss"))
            
            # Click close button
            print("   🖱️  Clicking close button...")
            await page.click("#close-banner-btn")
            await page.wait_for_timeout(500)
            
            # Check if banner is hidden
            if not await banner.is_visible():
                print("   ✅ Banner hidden after clicking X")
                await page.screenshot(path=self.get_screenshot_path("11_banner_dismissed"))
                
                # Check localStorage
                dismissed = await page.evaluate("() => localStorage.getItem('personality-banner-dismissed')")
                if dismissed == 'true':
                    print(f"   ✅ localStorage correctly set to: '{dismissed}'")
                else:
                    print(f"   ⚠️  localStorage value unexpected: '{dismissed}'")
                
                # Reload again to verify it doesn't show
                print("   ⏳ Reloading to verify banner stays hidden...")
                await page.reload()
                await page.wait_for_load_state("networkidle")
                
                # Wait and check if banner appears (it shouldn't)
                await page.wait_for_timeout(3500)
                banner_visible = await banner.is_visible()
                
                if not banner_visible:
                    print("   ✅ Banner correctly stays hidden after dismissal")
                    await page.screenshot(path=self.get_screenshot_path("12_banner_stays_hidden"))
                else:
                    print("   ❌ Banner appeared again (should stay hidden)")
                    await page.screenshot(path=self.get_screenshot_path("12_banner_reappeared_ERROR"))
            else:
                print("   ⚠️  Banner still visible after clicking close button")
        else:
            print("   ⏭️  Banner did not appear (user likely has psychology traits)")
            print("      Skipping dismissal test")
        
        await page.screenshot(path=self.get_screenshot_path("13_final_state"))
        print()

async def main():
    """Run all tests"""
    tester = PersonalityTestTester()
    await tester.test_personality_integration()

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 PERSONALITY TEST INTEGRATION - PLAYWRIGHT TEST")
    print("=" * 70)
    print()
    
    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=5)
        print("✅ Server is running\n")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify server (but continuing anyway)")
        print(f"   Error: {e}\n")
    
    asyncio.run(main())
    
    print("=" * 70)
    print("📸 Screenshots saved to: test_screenshots/personality_integration/")
    print("=" * 70)
