"""
Playwright test script to verify chat fixes:
1. Users/admins cannot reply to themselves
2. Dashboard title shows correct text based on user role
"""

from playwright.sync_api import sync_playwright, expect
import time

def test_chat_fixes():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        print("\n" + "="*70)
        print("🧪 Testing Chat Fixes")
        print("="*70)
        
        # Navigate to chatchat
        print("\n1. Navigating to /chatchat...")
        page.goto('http://localhost:5000/chatchat')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Test 1: Login as regular user (Wai Tse)
        print("\n2. Testing as Regular User (Wai Tse)...")
        print("-" * 70)
        
        # Fill login form
        page.fill('#login-username', 'Wai Tse')
        page.fill('#login-password', './/')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        # Check dashboard title for regular user
        print("   ✓ Logged in as Wai Tse")
        
        # Navigate to admin tab (if visible - shouldn't be for regular user)
        admin_tab = page.query_selector('#admin-tab-btn')
        if admin_tab and admin_tab.is_visible():
            print("   ⚠ Admin tab visible for regular user (checking title...)")
            page.click('#admin-tab-btn')
            time.sleep(1)
            dashboard_title = page.text_content('#admin-dashboard-title')
            print(f"   📋 Dashboard title: '{dashboard_title}'")
            if dashboard_title == 'User Dashboard':
                print("   ✅ PASS: Dashboard title is 'User Dashboard'")
            else:
                print(f"   ❌ FAIL: Expected 'User Dashboard', got '{dashboard_title}'")
        else:
            print("   ℹ Admin tab not visible for regular user (expected)")
        
        # Go to Contact Admin to test reply buttons
        print("\n   Testing reply buttons in Contact Admin...")
        contact_admin_btn = page.query_selector('#admin-chat-tab-btn')
        if contact_admin_btn and contact_admin_btn.is_visible():
            page.click('#admin-chat-tab-btn')
            time.sleep(2)
            
            # Send a test message
            print("   ✓ Opened Contact Admin chat")
            admin_chat_input = page.query_selector('#admin-chat-input')
            if admin_chat_input:
                admin_chat_input.fill('Test message from user')
                page.click('#send-admin-chat-btn')
                time.sleep(2)
                print("   ✓ Sent test message")
                
                # Check messages container
                messages = page.query_selector_all('#admin-chat-messages > div')
                print(f"   ℹ Found {len(messages)} messages in chat")
                
                # Check for reply buttons
                user_messages_with_reply = 0
                admin_messages_with_reply = 0
                
                for msg in messages:
                    # Check if this is a user message (right-aligned)
                    is_user_msg = 'flex-end' in msg.get_attribute('style') or ''
                    reply_button = msg.query_selector('button[title="Reply to this message"]')
                    
                    if is_user_msg:
                        if reply_button and reply_button.is_visible():
                            user_messages_with_reply += 1
                    else:
                        if reply_button and reply_button.is_visible():
                            admin_messages_with_reply += 1
                
                print(f"   📊 User messages with reply button: {user_messages_with_reply}")
                print(f"   📊 Admin messages with reply button: {admin_messages_with_reply}")
                
                if user_messages_with_reply == 0:
                    print("   ✅ PASS: No reply buttons on user's own messages")
                else:
                    print(f"   ❌ FAIL: Found {user_messages_with_reply} reply buttons on user's own messages")
                
                if admin_messages_with_reply > 0:
                    print("   ✅ PASS: Reply buttons present on admin messages")
                else:
                    print("   ⚠ INFO: No admin messages found or no reply buttons")
        
        # Logout
        print("\n3. Logging out...")
        logout_btn = page.query_selector('#logout-btn')
        if logout_btn and logout_btn.is_visible():
            logout_btn.click()
            time.sleep(2)
            print("   ✓ Logged out")
        else:
            print("   ℹ Logout button not visible, clearing storage manually...")
            page.evaluate('localStorage.clear(); sessionStorage.clear();')
            page.goto('http://localhost:5000/chatchat')
            page.wait_for_load_state('networkidle')
            time.sleep(1)
        
        # Test 2: Login as administrator
        print("\n4. Testing as Administrator...")
        print("-" * 70)
        
        page.fill('#login-username', 'administrator')
        page.fill('#login-password', 'admin')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        print("   ✓ Logged in as administrator")
        
        # Wait for page to load completely
        time.sleep(3)
        
        # Check admin tab visibility
        admin_tab = page.query_selector('#admin-tab-btn')
        print(f"   📊 Admin tab element found: {admin_tab is not None}")
        if admin_tab:
            is_visible = admin_tab.is_visible()
            display_style = page.evaluate('(el) => window.getComputedStyle(el).display', admin_tab)
            print(f"   📊 Admin tab is_visible: {is_visible}, display: {display_style}")
            
        if admin_tab and admin_tab.is_visible():
            print("   ✓ Admin tab is visible")
            page.click('#admin-tab-btn')
            time.sleep(1)
            
            # Check dashboard title
            dashboard_title = page.text_content('#admin-dashboard-title')
            print(f"   📋 Dashboard title: '{dashboard_title}'")
            
            if dashboard_title == 'Administrator Dashboard':
                print("   ✅ PASS: Dashboard title is 'Administrator Dashboard'")
            else:
                print(f"   ❌ FAIL: Expected 'Administrator Dashboard', got '{dashboard_title}'")
        else:
            print("   ❌ FAIL: Admin tab not visible for administrator")
            # Try to get user role from browser console
            user_role = page.evaluate('() => { try { return window.app ? "app exists" : "no app"; } catch(e) { return e.message; } }')
            print(f"   📊 Debug - Window.app status: {user_role}")
        
        # Check Contact Admin button (should be hidden for admin)
        contact_admin_btn = page.query_selector('#admin-chat-tab-btn')
        if contact_admin_btn:
            is_visible = contact_admin_btn.is_visible()
            if not is_visible:
                print("   ✅ PASS: Contact Admin button hidden for administrator")
            else:
                print("   ❌ FAIL: Contact Admin button visible for administrator")
        
        # Test reply buttons in Admin Chat Management
        print("\n   Testing reply buttons in Admin Chat Management...")
        
        # Find and click on a user chat
        user_chat_items = page.query_selector_all('.admin-user-chat-item')
        if user_chat_items:
            print(f"   ℹ Found {len(user_chat_items)} user chats")
            # Click first user chat
            user_chat_items[0].click()
            time.sleep(2)
            print("   ✓ Opened first user's chat")
            
            # Send a test message as admin
            admin_reply_input = page.query_selector('#admin-chat-reply-input')
            if admin_reply_input:
                admin_reply_input.fill('Test admin reply')
                page.click('#send-admin-reply-btn')
                time.sleep(2)
                print("   ✓ Sent test admin message")
                
                # Check messages
                messages = page.query_selector_all('#admin-user-chat-messages > div')
                print(f"   ℹ Found {len(messages)} messages in user chat")
                
                admin_messages_with_reply = 0
                user_messages_with_reply = 0
                
                for msg in messages:
                    # Check if admin message (right-aligned in admin view)
                    is_admin_msg = 'flex-end' in (msg.get_attribute('style') or '')
                    reply_button = msg.query_selector('button[title="Reply to this message"]')
                    
                    if is_admin_msg:
                        if reply_button and reply_button.is_visible():
                            admin_messages_with_reply += 1
                    else:
                        if reply_button and reply_button.is_visible():
                            user_messages_with_reply += 1
                
                print(f"   📊 Admin messages with reply button: {admin_messages_with_reply}")
                print(f"   📊 User messages with reply button: {user_messages_with_reply}")
                
                if admin_messages_with_reply == 0:
                    print("   ✅ PASS: No reply buttons on admin's own messages")
                else:
                    print(f"   ❌ FAIL: Found {admin_messages_with_reply} reply buttons on admin's own messages")
                
                if user_messages_with_reply > 0:
                    print("   ✅ PASS: Reply buttons present on user messages")
                else:
                    print("   ⚠ INFO: No user messages with reply buttons found")
        else:
            print("   ⚠ INFO: No user chats found to test")
        
        # Final summary
        print("\n" + "="*70)
        print("🏁 Test Complete!")
        print("="*70)
        print("\n📝 Summary:")
        print("1. Regular user dashboard title should be 'User Dashboard'")
        print("2. Administrator dashboard title should be 'Administrator Dashboard'")
        print("3. Users should NOT see reply buttons on their own messages")
        print("4. Admins should NOT see reply buttons on their own messages")
        print("5. Reply buttons should ONLY appear on other party's messages")
        print("\n" + "="*70)
        
        # Keep browser open for inspection
        print("\n⏸ Browser will remain open for 5 seconds for inspection...")
        time.sleep(5)
        
        browser.close()

if __name__ == '__main__':
    test_chat_fixes()
