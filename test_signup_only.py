"""
Quick test to debug signup issues
"""

import asyncio
from playwright.async_api import async_playwright
import random
import string

async def test_signup():
    async with async_playwright() as p:
        print("🧪 Testing Signup...")
        
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capture console logs
        page.on("console", lambda msg: print(f"   [Browser] {msg.type}: {msg.text}"))
        
        # Go to signup page
        await page.goto("http://localhost:5000/multi-user")
        await page.wait_for_load_state("networkidle")
        
        # Click signup link
        await page.click("#show-signup")
        await page.wait_for_timeout(1000)
        
        # Generate unique credentials
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        username = f"TestUser_{random_id}"
        email = f"test_{random_id}@example.com"
        password = "TestPassword123!"
        
        print(f"\n📝 Attempting signup:")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Password: {password}\n")
        
        # Fill form
        await page.fill("#signup-username", username)
        await page.fill("#signup-email", email)
        await page.fill("#signup-password", password)
        await page.fill("#signup-confirm-password", password)
        
        # Take screenshot before submit
        await page.screenshot(path="test_screenshots/signup_before.png")
        print("📸 Screenshot: signup_before.png")
        
        # Submit
        print("\n🖱️  Clicking signup button...")
        await page.click("#signup-form button[type='submit']")
        
        # Wait for response
        await page.wait_for_timeout(3000)
        
        # Take screenshot after submit
        await page.screenshot(path="test_screenshots/signup_after.png")
        print("📸 Screenshot: signup_after.png")
        
        # Check what screen we're on
        login_screen = await page.query_selector("#login-screen")
        signup_screen = await page.query_selector("#signup-screen")
        dashboard_screen = await page.query_selector("#dashboard-screen")
        
        login_visible = login_screen and await login_screen.is_visible()
        signup_visible = signup_screen and await signup_screen.is_visible()
        dashboard_visible = dashboard_screen and await dashboard_screen.is_visible()
        
        print(f"\n📊 Screen Status:")
        print(f"   Login: {login_visible}")
        print(f"   Signup: {signup_visible}")
        print(f"   Dashboard: {dashboard_visible}")
        
        # Check for error notifications
        notification = await page.query_selector("#notification")
        if notification:
            notification_visible = await notification.is_visible()
            if notification_visible:
                text = await notification.inner_text()
                print(f"\n⚠️  Notification visible: {text}")
        
        if dashboard_visible:
            print("\n✅ SUCCESS! Signup worked - dashboard is visible")
        else:
            print("\n❌ FAILED! Still on signup/login screen")
        
        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_signup())
