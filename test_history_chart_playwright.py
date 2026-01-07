"""
Use Playwright to verify what the frontend actually receives
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def test_history_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("=" * 80)
        print("PLAYWRIGHT TEST: Assessment History API")
        print("=" * 80)
        print()
        
        # Intercept API calls
        api_responses = []
        
        async def handle_response(response):
            if '/api/personality/history' in response.url:
                try:
                    data = await response.json()
                    api_responses.append(data)
                    print("✅ Intercepted API response:")
                    print(f"   URL: {response.url}")
                    print(f"   Status: {response.status}")
                    print(f"   Data: {json.dumps(data, indent=2)}")
                except:
                    print(f"⚠️  Could not parse response from {response.url}")
        
        page.on('response', handle_response)
        
        # Capture console logs
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        print("📍 Step 1: Going to localhost:5000/personality-test")
        try:
            await page.goto('http://localhost:5000/personality-test', timeout=10000)
            print("   ✅ Page loaded")
        except Exception as e:
            print(f"   ❌ Failed to load page: {e}")
            await browser.close()
            return
        
        print()
        print("📍 Step 2: Waiting for page to be fully loaded...")
        await page.wait_for_timeout(2000)
        
        # Check if auth is required
        print()
        print("📍 Step 3: Checking authentication...")
        current_url = page.url
        if 'login' in current_url:
            print("   ⚠️  Redirected to login page")
            print("   Need to login first!")
            
            # Try to login
            print()
            print("📍 Step 4: Attempting login...")
            await page.fill('input[name="username"]', 'admin')
            await page.fill('input[name="password"]', 'admin123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)
            
            # Go back to personality test
            await page.goto('http://localhost:5000/personality-test')
            await page.wait_for_timeout(2000)
        else:
            print("   ✅ No login required or already logged in")
        
        print()
        print("📍 Step 5: Checking if history chart exists...")
        
        # Check if the history chart section exists
        history_section = await page.query_selector('#history-chart-section')
        if history_section:
            is_visible = await history_section.is_visible()
            print(f"   ✅ History chart section exists")
            print(f"   Visible: {is_visible}")
            
            if is_visible:
                # Check canvas element
                canvas = await page.query_selector('#personalityHistoryChart')
                if canvas:
                    print(f"   ✅ Canvas element found")
                else:
                    print(f"   ❌ Canvas element NOT found")
        else:
            print(f"   ❌ History chart section NOT found in DOM")
        
        print()
        print("📍 Step 6: Waiting for API calls...")
        await page.wait_for_timeout(3000)
        
        print()
        print("=" * 80)
        print("RESULTS:")
        print("=" * 80)
        print()
        
        if api_responses:
            print(f"✅ Captured {len(api_responses)} API response(s):")
            for i, resp in enumerate(api_responses, 1):
                print(f"\nResponse {i}:")
                if 'history' in resp:
                    print(f"  Count: {resp.get('count', 'N/A')}")
                    print(f"  Items: {len(resp['history'])}")
                    for j, item in enumerate(resp['history'], 1):
                        print(f"    {j}. {item.get('completed_at', 'N/A')}: O={item.get('openness', 0)*100:.0f}%")
                else:
                    print(f"  {resp}")
        else:
            print("⚠️  No API responses captured")
            print("   Possible reasons:")
            print("   - API not called (check auth)")
            print("   - Endpoint not hit")
            print("   - Browser cache")
        
        print()
        print("Console logs:")
        for log in console_logs[-10:]:  # Last 10 logs
            print(f"  {log}")
        
        print()
        print("📸 Taking screenshot...")
        await page.screenshot(path='personality_test_debug.png', full_page=True)
        print("   ✅ Saved to: personality_test_debug.png")
        
        await page.wait_for_timeout(2000)
        await browser.close()

asyncio.run(test_history_api())
