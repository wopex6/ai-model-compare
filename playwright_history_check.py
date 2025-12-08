"""
Playwright test for conversation history persistence
Tests the actual browser behavior, not just the API
"""
from playwright.sync_api import sync_playwright, expect
import time

def test_conversation_history_in_browser():
    """Test conversation history with real browser automation"""
    
    print("="*60)
    print("PLAYWRIGHT BROWSER TEST - Conversation History")
    print("="*60)
    
    with sync_playwright() as p:
        # Launch browser
        print("\n1️⃣ Launching browser...")
        browser = p.chromium.launch(headless=False)  # Set to True to run without UI
        context = browser.new_context()
        page = context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"   [Browser Console] {msg.type}: {msg.text}"))
        
        # Navigate to scientist page
        print("\n2️⃣ Navigating to scientist page...")
        page.goto("http://localhost:5000/scientist")
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Check if page loaded
        print("   ✅ Page loaded")
        
        # DEBUG: Check what's actually on the page
        print("\n🔍 Debugging page content...")
        page_title = page.title()
        print(f"   Page title: {page_title}")
        
        # Take screenshot to see what's showing
        page.screenshot(path="debug_page_load.png")
        print("   📸 Screenshot: debug_page_load.png")
        
        # Check for login screen
        if page.locator("#login-form").is_visible(timeout=1000):
            print("   ⚠️  Login screen detected!")
            print("   You need to be logged in to access character pages")
            browser.close()
            return False
        
        # Check if input field exists
        input_exists = page.locator("#userInput").is_visible(timeout=5000)
        print(f"   Input field visible: {input_exists}")
        
        # Check if button exists
        button_exists = page.locator(".send-btn").is_visible(timeout=5000)
        print(f"   Send button visible: {button_exists}")
        
        if not button_exists:
            print("\n   ❌ Send button not found! Page structure:")
            # Print page HTML for debugging
            html = page.content()
            if "login" in html.lower():
                print("   🔐 Login page detected - authentication required!")
            else:
                print(f"   Page HTML length: {len(html)} chars")
                # Save HTML for inspection
                with open("debug_page_content.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("   📄 Saved HTML to: debug_page_content.html")
            browser.close()
            return False
        
        # Send first message
        print("\n3️⃣ Sending first message: 'Hello, my name is Alice'...")
        input_field = page.locator("#userInput")
        input_field.fill("Hello, my name is Alice")
        
        send_button = page.locator(".send-btn")
        send_button.click()
        
        # Wait for response
        print("   ⏳ Waiting for AI response...")
        time.sleep(5)  # Wait for quick reply or AI response
        
        # Check if message appears in chat
        messages = page.locator(".message")
        message_count = messages.count()
        print(f"   ✅ Messages in chat: {message_count}")
        
        # Send second message
        print("\n4️⃣ Sending second message: 'I like quantum physics'...")
        input_field.fill("I like quantum physics")
        send_button.click()
        
        print("   ⏳ Waiting for AI response...")
        time.sleep(5)
        
        # Check message count increased
        messages = page.locator(".message")
        new_count = messages.count()
        print(f"   ✅ Messages in chat: {new_count}")
        
        # Check cookies - THIS IS CRITICAL!
        print("\n5️⃣ Checking session cookie...")
        cookies = context.cookies()
        session_cookie = None
        
        for cookie in cookies:
            if cookie['name'].startswith('session_'):
                session_cookie = cookie
                print(f"   ✅ Found cookie: {cookie['name']} = {cookie['value'][:30]}...")
                break
        
        if not session_cookie:
            print("   ❌ ERROR: No session cookie found!")
            print(f"   Available cookies: {[c['name'] for c in cookies]}")
        
        # Get current message count before leaving
        messages_before = page.locator(".message").count()
        print(f"\n6️⃣ Current message count: {messages_before}")
        
        # CRITICAL TEST: Leave the page
        print("\n7️⃣ Leaving page (navigating to home)...")
        page.goto("http://localhost:5000/")
        time.sleep(1)
        
        # Return to scientist page
        print("\n8️⃣ Returning to scientist page...")
        page.goto("http://localhost:5000/scientist")
        page.wait_for_load_state("networkidle")
        time.sleep(3)  # Wait for history to load
        
        # Check if messages are still there
        print("\n9️⃣ Checking if history loaded...")
        messages_after = page.locator(".message").count()
        print(f"   Messages after return: {messages_after}")
        print(f"   Messages before leaving: {messages_before}")
        
        # Take screenshot for debugging
        page.screenshot(path="history_check_screenshot.png")
        print("\n   📸 Screenshot saved: history_check_screenshot.png")
        
        # Check for error messages in console
        print("\n🔍 Checking browser console for errors...")
        
        # Verify history
        if messages_after >= messages_before - 1:  # -1 because welcome message might be cleared
            print("\n✅ SUCCESS! History persisted!")
            
            # Print message contents
            print("\n📋 Messages displayed:")
            for i in range(messages_after):
                msg = messages.nth(i).inner_text()
                print(f"   {i+1}. {msg[:100]}...")
            
            success = True
        else:
            print(f"\n❌ FAILURE! History NOT persisted!")
            print(f"   Expected: {messages_before} messages")
            print(f"   Got: {messages_after} messages")
            success = False
        
        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
        time.sleep(10)
        
        # Close browser
        browser.close()
        
        return success

if __name__ == "__main__":
    print("\n🎭 Starting Playwright Browser Test")
    print("Make sure Flask app is running on http://localhost:5000\n")
    
    try:
        result = test_conversation_history_in_browser()
        
        print("\n" + "="*60)
        print("FINAL RESULT")
        print("="*60)
        
        if result:
            print("✅ BROWSER TEST PASSED - History works in real browser!")
        else:
            print("❌ BROWSER TEST FAILED - History does NOT work in browser!")
            print("\nCheck:")
            print("1. Browser console (red errors?)")
            print("2. Network tab (history endpoint called?)")
            print("3. Application tab → Cookies (session cookie exists?)")
            print("4. Screenshot: history_check_screenshot.png")
        
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
