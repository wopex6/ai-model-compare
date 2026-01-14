"""
Playwright test for Character Interpretation Storage
Tests that both responded and noticed characters store rich context

Run with: python test_character_interpretations.py
"""

import asyncio
import json
from playwright.async_api import async_playwright

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "admin"
TEST_PASS = "admin"


async def test_character_interpretations():
    """Test that character interpretations are stored with rich context"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for debugging
        context = await browser.new_context()
        page = await context.new_page()
        
        print("\n" + "="*60)
        print("CHARACTER INTERPRETATION STORAGE TEST")
        print("="*60)
        
        # Step 1: Login via API
        print("\n[1] Logging in via API...")
        await page.goto(f"{BASE_URL}/user_logon")
        
        # Submit login form
        await page.wait_for_selector('input[name="username"]', timeout=10000)
        await page.fill('input[name="username"]', TEST_USER)
        await page.fill('input[name="password"]', TEST_PASS)
        
        # Click submit and wait for navigation
        async with page.expect_navigation(timeout=15000):
            await page.click('button[type="submit"]')
        
        print(f"    ✓ Redirected to: {page.url}")
        
        # Step 2: Go to Life Companion
        print("\n[2] Navigating to Life Companion...")
        await page.goto(f"{BASE_URL}/life-companion")
        await page.wait_for_timeout(5000)
        
        # Check if input is enabled (indicates logged in)
        input_placeholder = await page.get_attribute('#userInput', 'placeholder')
        print(f"    Input placeholder: {input_placeholder}")
        
        if 'log in' in input_placeholder.lower():
            print("    ❌ Not logged in - input is disabled")
            await browser.close()
            return None
        
        print("    ✓ Life Companion loaded and authenticated")
        
        # Step 3: Send test message that triggers multiple domains
        test_message = "I'm stressed about my job deadline and worried about money"
        print(f"\n[3] Sending test message: '{test_message}'")
        
        # Find the chat input
        await page.fill('#userInput', test_message)
        await page.click('#sendBtn')
        print("    ✓ Message sent")
        
        # Wait for AI response
        print("    ⏳ Waiting for AI response (15 seconds)...")
        await page.wait_for_timeout(15000)
        print("    ✓ Response should be received")
        
        # Step 4: Check cross-domain API for interpretations
        print("\n[4] Checking cross-domain insights API...")
        
        # Get auth token from cookies
        cookies = await context.cookies()
        
        # Make API call
        response = await page.evaluate('''async (message) => {
            const response = await fetch('/api/domain-characters/cross-domain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            return await response.json();
        }''', test_message)
        
        print(f"    ✓ API response received")
        
        # Step 5: Analyze results
        print("\n[5] ANALYSIS OF STORED INTERPRETATIONS:")
        print("-"*50)
        
        if response.get('success'):
            # Responded characters
            responded = response.get('responded', [])
            print(f"\n    ✓ RESPONDED ({len(responded)} characters):")
            for char in responded:
                print(f"      - {char['character']} ({char['domain']}): {char['concern_level']*100:.0f}%")
            
            # Silent observers
            silent = response.get('silent_observers', [])
            print(f"\n    👁️ NOTICED BUT DIDN'T RESPOND ({len(silent)} characters):")
            for char in silent:
                print(f"      - {char['character']} ({char['domain']}): {char['concern_level']*100:.0f}%")
            
            # Cross-domain patterns
            cross = response.get('cross_domain', {})
            if cross.get('correlations'):
                print(f"\n    🔗 CROSS-DOMAIN PATTERNS DETECTED:")
                for corr in cross['correlations']:
                    print(f"      - {corr['description']}")
            
            # Domain insights (full interpretation data)
            insights = response.get('domain_insights', [])
            print(f"\n    📊 FULL INTERPRETATION DATA ({len(insights)} characters):")
            for insight in insights[:3]:  # Show first 3
                print(f"\n      {insight.get('display_name', 'Unknown')}:")
                interp = insight.get('interpretation', {})
                print(f"        Domain: {interp.get('domain', 'N/A')}")
                print(f"        Emotions detected: {interp.get('detected_emotions', [])}")
                print(f"        User state: {interp.get('user_emotional_state', 'N/A')}")
                print(f"        Perspective: {interp.get('character_perspective', 'N/A')}")
                print(f"        Potential advice: {interp.get('potential_advice', 'N/A')}")
                print(f"        Continuity tags: {interp.get('continuity_tags', [])}")
        else:
            print(f"    ❌ Error: {response.get('error', 'Unknown error')}")
        
        # Step 6: Check database for stored interpretations
        print("\n[6] Checking database storage via API...")
        
        # Get latest history to find history_id
        history_response = await page.evaluate('''async () => {
            const response = await fetch('/api/domain-characters/history/coordinator?limit=1');
            return await response.json();
        }''')
        
        if history_response.get('success') and history_response.get('history'):
            latest = history_response['history'][0]
            history_id = latest.get('id')
            print(f"    ✓ Latest history ID: {history_id}")
            
            # Get interpretations for this message
            interp_response = await page.evaluate('''async (historyId) => {
                const response = await fetch('/api/domain-characters/interpretations/' + historyId);
                return await response.json();
            }''', history_id)
            
            if interp_response.get('success'):
                interps = interp_response.get('interpretations', [])
                print(f"    ✓ {len(interps)} interpretations stored in database")
                
                for interp in interps:
                    status = "✓ Responded" if interp.get('responded') else "👁️ Noticed"
                    print(f"      {status}: {interp.get('character_id')} (concern: {interp.get('concern_level', 0)*100:.0f}%)")
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        
        await browser.close()
        return response


if __name__ == "__main__":
    result = asyncio.run(test_character_interpretations())
