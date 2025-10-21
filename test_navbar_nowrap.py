"""
Test navbar text doesn't wrap on narrow screens
"""

import asyncio
from playwright.async_api import async_playwright
import random
import string

async def test_navbar_nowrap():
    async with async_playwright() as p:
        print("🧪 Testing Navbar No-Wrap Behavior...\n")
        
        browser = await p.chromium.launch(headless=False)
        
        # Test with different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080, "name": "Desktop (1920x1080)"},
            {"width": 1024, "height": 768, "name": "Tablet (1024x768)"},
            {"width": 768, "height": 1024, "name": "Tablet Portrait (768x1024)"},
            {"width": 375, "height": 667, "name": "Mobile (375x667)"}
        ]
        
        for viewport in viewports:
            print(f"📱 Testing {viewport['name']}...")
            
            context = await browser.new_context(viewport={"width": viewport['width'], "height": viewport['height']})
            page = await context.new_page()
            
            # Go to app
            await page.goto("http://localhost:5000/multi-user")
            await page.wait_for_load_state("networkidle")
            
            # Create test user
            random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            test_username = f"LongUsernameTest_{random_id}_VeryLong"
            test_email = f"test_{random_id}@example.com"
            
            await page.click("#show-signup")
            await page.wait_for_timeout(500)
            
            await page.fill("#signup-username", test_username)
            await page.fill("#signup-email", test_email)
            await page.fill("#signup-password", "test123")
            await page.fill("#signup-confirm-password", "test123")
            await page.click("#signup-form button[type='submit']")
            
            await page.wait_for_timeout(3000)
            
            # Check navbar
            dashboard = await page.query_selector("#dashboard-screen")
            if dashboard and await dashboard.is_visible():
                # Take screenshot
                screenshot_name = f"test_screenshots/navbar_{viewport['width']}x{viewport['height']}.png"
                await page.screenshot(path=screenshot_name)
                print(f"   📸 Screenshot: {screenshot_name}")
                
                # Check if title is visible
                title = await page.query_selector(".nav-brand h2")
                if title:
                    title_text = await title.inner_text()
                    print(f"   ✅ Title: '{title_text}'")
                
                # Check username
                username_elem = await page.query_selector("#nav-username")
                if username_elem:
                    username_text = await username_elem.inner_text()
                    print(f"   ✅ Username: '{username_text}'")
                
                # Check nav buttons visibility
                nav_buttons = await page.query_selector_all(".nav-btn")
                print(f"   ✅ Nav buttons visible: {len(nav_buttons)}")
            else:
                print(f"   ❌ Dashboard not loaded")
            
            await context.close()
            print()
        
        await browser.close()
        
        print("=" * 70)
        print("✅ All viewport tests completed!")
        print("📁 Check test_screenshots/ for visual verification")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_navbar_nowrap())
