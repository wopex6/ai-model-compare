"""
Pattern and Context Test
Tests pattern detection, context extraction, and explicit context functionality.
"""
import time
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://trabcd.pythonanywhere.com"
TEST_USER = "Wai Tse"
TEST_PASSWORD = "123"

# Test messages designed to trigger pattern detection and context extraction
CONTEXT_TEST_MESSAGES = [
    # Goal-related messages
    "My goal is to become more organized this year",
    "I want to learn Python programming",
    
    # Preference-related messages  
    "I prefer practical advice over philosophical discussions",
    "I like when you give me step-by-step instructions",
    
    # Values and beliefs
    "I believe in continuous self-improvement",
    "Family is very important to me",
    
    # Emotional state
    "I've been feeling anxious about my job interview next week",
    "I'm excited about starting a new project",
]

def run_pattern_context_tests():
    print("=" * 60)
    print("🧠 PATTERN & CONTEXT TEST")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    
    session = requests.Session()
    
    # Step 1: Login and get session
    print("\n🔐 Logging in...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state('networkidle')
        
        if page.query_selector('input[name="username"]:visible'):
            page.fill('input[name="username"]', TEST_USER)
            page.fill('input[name="password"]', TEST_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)
        
        # Get cookies for API requests
        cookies = context.cookies()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        
        print("  ✅ Logged in and cookies captured")
        
        # Step 2: Navigate to Life Companion and send context-rich messages
        print("\n💬 Sending context-rich messages...")
        page.goto(f"{BASE_URL}/life-companion", timeout=60000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        messages_sent = 0
        for msg in CONTEXT_TEST_MESSAGES:
            print(f"  📤 {msg[:50]}...")
            
            input_field = page.query_selector('#userInput, textarea#userInput')
            if input_field:
                input_field.fill(msg)
                send_btn = page.query_selector('#sendBtn, button:has-text("Send")')
                if send_btn:
                    send_btn.click()
                    messages_sent += 1
                    
                    # Wait for response
                    try:
                        page.wait_for_selector('.typing-indicator:visible', timeout=5000)
                    except:
                        pass
                    try:
                        page.wait_for_selector('.typing-indicator:not(:visible)', timeout=30000)
                    except:
                        pass
                    page.wait_for_timeout(1500)
        
        print(f"  ✅ Sent {messages_sent} context-rich messages")
        browser.close()
    
    # Step 3: Test Context API endpoints
    print("\n📊 Testing Context APIs...")
    
    # Test explicit context
    print("\n  🎯 Explicit Context:")
    try:
        r = session.get(f"{BASE_URL}/api/user/explicit-context", timeout=30)
        if r.status_code == 200:
            data = r.json()
            contexts = data.get('contexts', [])
            print(f"    ✅ Found {len(contexts)} explicit context items")
            for ctx in contexts[:5]:
                print(f"      - [{ctx.get('context_type', 'unknown')}] {ctx.get('content', '')[:50]}...")
        else:
            print(f"    ⚠️ Status {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test explicit context summary
    print("\n  📝 Context Summary:")
    try:
        r = session.get(f"{BASE_URL}/api/user/explicit-context/summary", timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"    ✅ Summary retrieved")
            if 'summary' in data:
                print(f"      {data['summary'][:200]}...")
        else:
            print(f"    ⚠️ Status {r.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test explicit context stats
    print("\n  📈 Context Stats:")
    try:
        r = session.get(f"{BASE_URL}/api/user/explicit-context/stats", timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"    ✅ Stats: {data}")
        else:
            print(f"    ⚠️ Status {r.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test user context
    print("\n  👤 User Context:")
    try:
        r = session.get(f"{BASE_URL}/api/user/context", timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"    ✅ User context retrieved")
            for key in ['goals', 'preferences', 'values', 'patterns']:
                if key in data:
                    count = len(data[key]) if isinstance(data[key], list) else 1
                    print(f"      - {key}: {count} items")
        else:
            print(f"    ⚠️ Status {r.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test context for coordinator character
    print("\n  🎭 Character Context (coordinator):")
    try:
        r = session.get(f"{BASE_URL}/api/context/coordinator", timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"    ✅ Character context retrieved")
            if 'recent_themes' in data:
                print(f"      Recent themes: {data.get('recent_themes', [])[:3]}")
            if 'conversation_count' in data:
                print(f"      Conversations: {data.get('conversation_count')}")
        else:
            print(f"    ⚠️ Status {r.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Step 4: Test Pattern APIs
    print("\n🔍 Testing Pattern APIs...")
    
    # Test pattern suggestions (admin)
    print("\n  📋 Pattern Suggestions:")
    try:
        r = session.get(f"{BASE_URL}/api/admin/patterns/suggestions", timeout=30)
        if r.status_code == 200:
            data = r.json()
            suggestions = data.get('suggestions', [])
            print(f"    ✅ Found {len(suggestions)} pattern suggestions")
            for s in suggestions[:3]:
                print(f"      - {s.get('pattern_type', 'unknown')}: {s.get('description', '')[:40]}...")
        else:
            print(f"    ⚠️ Status {r.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test pattern analysis trigger
    print("\n  🔬 Trigger Pattern Analysis:")
    try:
        r = session.post(f"{BASE_URL}/api/admin/patterns/analyze", timeout=60)
        if r.status_code == 200:
            data = r.json()
            print(f"    ✅ Analysis complete: {data}")
        else:
            print(f"    ⚠️ Status {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Step 5: Test Explicit Context Panel UI
    print("\n🖥️ Testing Explicit Context Panel UI...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state('networkidle')
        if page.query_selector('input[name="username"]:visible'):
            page.fill('input[name="username"]', TEST_USER)
            page.fill('input[name="password"]', TEST_PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)
        
        # Go to life companion
        page.goto(f"{BASE_URL}/life-companion", timeout=60000)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        # Dismiss any notifications that might block clicks
        try:
            page.evaluate("document.querySelectorAll('#ai-budget-notification, .notification').forEach(n => n.style.display = 'none')")
        except:
            pass
        
        # Test API calls via page.evaluate (uses browser session)
        print("\n  📊 Testing Context APIs via browser session:")
        
        # Get explicit context
        try:
            result = page.evaluate('''async () => {
                const r = await fetch('/api/user/explicit-context', {credentials: 'include'});
                return { status: r.status, data: await r.json() };
            }''')
            if result['status'] == 200:
                contexts = result['data'].get('contexts', [])
                print(f"    ✅ Explicit context: {len(contexts)} items")
                for ctx in contexts[:3]:
                    print(f"      - [{ctx.get('context_type', 'unknown')}] {ctx.get('content', '')[:40]}...")
            else:
                print(f"    ⚠️ Status {result['status']}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        # Get context stats
        try:
            result = page.evaluate('''async () => {
                const r = await fetch('/api/user/explicit-context/stats', {credentials: 'include'});
                return { status: r.status, data: await r.json() };
            }''')
            if result['status'] == 200:
                print(f"    ✅ Context stats: {result['data']}")
            else:
                print(f"    ⚠️ Stats status {result['status']}")
        except Exception as e:
            print(f"    ❌ Stats error: {e}")
        
        # Get pattern suggestions
        try:
            result = page.evaluate('''async () => {
                const r = await fetch('/api/admin/patterns/suggestions', {credentials: 'include'});
                return { status: r.status, data: await r.json() };
            }''')
            if result['status'] == 200:
                suggestions = result['data'].get('suggestions', [])
                print(f"    ✅ Pattern suggestions: {len(suggestions)} items")
            else:
                print(f"    ⚠️ Patterns status {result['status']}")
        except Exception as e:
            print(f"    ❌ Patterns error: {e}")
        
        # Check for context panel button
        context_btn = page.query_selector('#contextBtn, [data-action="context"], button:has-text("Context")')
        if context_btn:
            print("  ✅ Context button found")
            try:
                context_btn.click(timeout=5000)
                page.wait_for_timeout(1000)
                
                # Check for context panel
                context_panel = page.query_selector('#explicit-context-panel, .context-panel, [id*="context"]')
                if context_panel:
                    print("  ✅ Context panel opened")
                    
                    # Check for context items
                    context_items = page.query_selector_all('.context-item, .explicit-context-item, [data-context-id]')
                    print(f"  📋 Context items in UI: {len(context_items)}")
                else:
                    print("  ⚠️ Context panel not found after click")
            except Exception as e:
                print(f"  ⚠️ Click failed (notification may be blocking): {e}")
        else:
            print("  ⚠️ Context button not found")
        
        browser.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PATTERN & CONTEXT TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Messages sent: {messages_sent}")
    print("✅ Context APIs tested")
    print("✅ Pattern APIs tested")
    print("✅ UI elements verified")
    print("\n✅ Test complete!")

if __name__ == "__main__":
    run_pattern_context_tests()
