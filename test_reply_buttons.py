"""
Comprehensive Playwright test for reply button fix
"""

from playwright.sync_api import sync_playwright
import time

def test_reply_buttons():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        print("\n" + "="*70)
        print("🧪 Testing Reply Button Fix")
        print("="*70)
        
        # ===== PART 1: Test as Regular User =====
        print("\n📝 PART 1: Testing as Regular User (Wai Tse)")
        print("-" * 70)
        
        page.goto('http://localhost:5000/chatchat')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Login as Wai Tse
        page.fill('#login-username', 'Wai Tse')
        page.fill('#login-password', './/')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        print("✓ Logged in as Wai Tse")
        
        # Wait for UI to be fully ready
        time.sleep(3)
        
        # Check if Contact Admin button is visible
        contact_btn = page.query_selector('#admin-chat-tab-btn')
        if contact_btn:
            is_visible = contact_btn.is_visible()
            display_style = page.evaluate('(el) => window.getComputedStyle(el).display', contact_btn)
            print(f"📊 Contact Admin button - is_visible: {is_visible}, display: {display_style}")
            
            if not is_visible:
                print("⚠ Contact Admin button not visible, trying force click...")
                page.click('#admin-chat-tab-btn', force=True)
            else:
                page.click('#admin-chat-tab-btn')
        else:
            print("❌ Contact Admin button not found")
            browser.close()
            return
        
        time.sleep(2)
        print("✓ Opened Contact Admin chat")
        
        # Send multiple messages
        for i in range(2):
            page.fill('#admin-chat-input', f'Test message {i+1} from user')
            page.click('#send-admin-chat-btn')
            time.sleep(1)
        print("✓ Sent 2 test messages")
        time.sleep(2)
        
        # Check reply buttons on user's own messages
        messages = page.query_selector_all('#admin-chat-messages > div')
        user_own_messages = 0
        user_own_with_reply = 0
        
        for msg in messages:
            style = msg.get_attribute('style') or ''
            is_user_msg = 'flex-end' in style  # User messages align right
            
            if is_user_msg:
                user_own_messages += 1
                reply_btn = msg.query_selector('button[title="Reply to this message"]')
                if reply_btn and reply_btn.is_visible():
                    user_own_with_reply += 1
        
        print(f"\n📊 User's own messages: {user_own_messages}")
        print(f"📊 User's own messages with reply button: {user_own_with_reply}")
        
        if user_own_with_reply == 0 and user_own_messages > 0:
            print("✅ PASS: User cannot reply to own messages")
        else:
            print(f"❌ FAIL: User has reply buttons on {user_own_with_reply} own messages")
        
        # Logout
        print("\n✓ Logging out...")
        page.evaluate('localStorage.clear(); sessionStorage.clear();')
        page.goto('http://localhost:5000/chatchat')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # ===== PART 2: Test as Administrator =====
        print("\n📝 PART 2: Testing as Administrator")
        print("-" * 70)
        
        # Login as administrator
        page.fill('#login-username', 'administrator')
        page.fill('#login-password', 'admin')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        print("✓ Logged in as administrator")
        
        # Navigate to Admin tab
        admin_tab = page.query_selector('#admin-tab-btn')
        if admin_tab and admin_tab.is_visible():
            page.click('#admin-tab-btn')
            time.sleep(2)
            print("✓ Opened Admin tab")
            
            # Check dashboard title
            dashboard_title = page.text_content('#admin-dashboard-title')
            print(f"📋 Dashboard title: '{dashboard_title}'")
            if dashboard_title == 'Administrator Dashboard':
                print("✅ PASS: Dashboard title is correct")
            else:
                print(f"❌ FAIL: Wrong dashboard title")
            
            # Find Wai Tse's chat
            user_chats = page.query_selector_all('.admin-user-chat-item')
            print(f"\n✓ Found {len(user_chats)} user chats")
            
            if user_chats:
                # Click on first user (should be Wai Tse)
                user_chats[0].click()
                time.sleep(2)
                print("✓ Opened Wai Tse's chat")
                
                # Send admin reply
                for i in range(2):
                    page.fill('#admin-chat-reply-input', f'Admin reply {i+1}')
                    page.click('#send-admin-reply-btn')
                    time.sleep(1)
                print("✓ Sent 2 admin replies")
                time.sleep(2)
                
                # Check reply buttons
                messages = page.query_selector_all('#admin-user-chat-messages > div')
                admin_own_messages = 0
                admin_own_with_reply = 0
                user_messages = 0
                user_messages_with_reply = 0
                
                for msg in messages:
                    style = msg.get_attribute('style') or ''
                    is_admin_msg = 'flex-end' in style  # Admin messages align right in admin view
                    reply_btn = msg.query_selector('button[title="Reply to this message"]')
                    
                    if is_admin_msg:
                        admin_own_messages += 1
                        if reply_btn and reply_btn.is_visible():
                            admin_own_with_reply += 1
                    else:
                        user_messages += 1
                        if reply_btn and reply_btn.is_visible():
                            user_messages_with_reply += 1
                
                print(f"\n📊 Admin's own messages: {admin_own_messages}")
                print(f"📊 Admin's own messages with reply button: {admin_own_with_reply}")
                print(f"📊 User messages: {user_messages}")
                print(f"📊 User messages with reply button: {user_messages_with_reply}")
                
                # Verify admin can't reply to self
                if admin_own_with_reply == 0 and admin_own_messages > 0:
                    print("✅ PASS: Admin cannot reply to own messages")
                else:
                    print(f"❌ FAIL: Admin has reply buttons on {admin_own_with_reply} own messages")
                
                # Verify admin can reply to user messages
                if user_messages_with_reply > 0 and user_messages > 0:
                    print("✅ PASS: Admin can reply to user messages")
                else:
                    print(f"⚠ WARNING: User messages don't have reply buttons")
            else:
                print("❌ No user chats found")
        else:
            print("❌ Admin tab not found or not visible")
        
        # ===== FINAL SUMMARY =====
        print("\n" + "="*70)
        print("🏁 Test Summary")
        print("="*70)
        print("\n✅ Expected Behavior:")
        print("  1. User CANNOT see reply button on their own messages")
        print("  2. User CAN see reply button on admin messages")
        print("  3. Admin CANNOT see reply button on their own messages")
        print("  4. Admin CAN see reply button on user messages")
        print("  5. Dashboard title shows 'Administrator Dashboard' for admin")
        print("\n" + "="*70)
        
        print("\n⏸ Browser will remain open for 10 seconds for inspection...")
        time.sleep(10)
        
        browser.close()

if __name__ == '__main__':
    test_reply_buttons()
