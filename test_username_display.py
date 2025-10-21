"""
Test username display in navbar
"""

import asyncio
from playwright.async_api import async_playwright
import random
import string

async def test_username_display():
    async with async_playwright() as p:
        print("🧪 Testing Username Display...\n")
        
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Go to app
        await page.goto("http://localhost:5000/multi-user")
        await page.wait_for_load_state("networkidle")
        
        # Create a new test user
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        test_username = f"UsernameTest_{random_id}"
        test_email = f"test_{random_id}@example.com"
        
        print(f"📝 Creating test user: {test_username}...")
        await page.click("#show-signup")
        await page.wait_for_timeout(500)
        
        await page.fill("#signup-username", test_username)
        await page.fill("#signup-email", test_email)
        await page.fill("#signup-password", "test123")
        await page.fill("#signup-confirm-password", "test123")
        await page.click("#signup-form button[type='submit']")
        
        # Wait for dashboard
        await page.wait_for_timeout(3000)
        
        # Check if dashboard is visible
        dashboard = await page.query_selector("#dashboard-screen")
        if dashboard and await dashboard.is_visible():
            print("✅ Dashboard loaded\n")
            
            # Check username display
            username_element = await page.query_selector("#nav-username")
            if username_element:
                username_text = await username_element.inner_text()
                print(f"👤 Username displayed: '{username_text}'")
                print(f"👤 Expected username: '{test_username}'")
                
                if username_text == test_username:
                    print("✅ Username is correct!")
                elif username_text == "Loading...":
                    print("⚠️  Username still showing 'Loading...'")
                else:
                    print(f"⚠️  Username mismatch!")
            else:
                print("❌ Username element not found!")
            
            # Take screenshot
            await page.screenshot(path="test_screenshots/username_display.png")
            print("\n📸 Screenshot saved: test_screenshots/username_display.png")
        else:
            print("❌ Dashboard not visible - login failed")
        
        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open for 5 seconds...")
        await page.wait_for_timeout(5000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_username_display())
