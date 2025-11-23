"""
Playwright test to verify admin access control:
- Regular users should NOT see Admin tab or User Messages section
- Only administrators should see Admin tab with User Messages
"""

from playwright.sync_api import sync_playwright
import time

def test_admin_access_control():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        print("\n" + "="*70)
        print("🧪 Testing Admin Access Control")
        print("="*70)
        
        # ===== TEST 1: Regular User (Wai Tse) =====
        print("\n📝 TEST 1: Regular User Access")
        print("-" * 70)
        
        page.goto('http://localhost:5000/chatchat')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Login as regular user
        print("1. Logging in as regular user (Wai Tse)...")
        page.fill('#login-username', 'Wai Tse')
        page.fill('#login-password', './/')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        print("   ✓ Logged in successfully")
        
        # Check Admin tab visibility
        print("\n2. Checking Admin tab visibility...")
        admin_tab = page.query_selector('#admin-tab-btn')
        if admin_tab:
            is_visible = admin_tab.is_visible()
            display = page.evaluate('(el) => window.getComputedStyle(el).display', admin_tab)
            print(f"   📊 Admin tab found: {admin_tab is not None}")
            print(f"   📊 Admin tab visible: {is_visible}")
            print(f"   📊 Display style: {display}")
            
            if not is_visible and display == 'none':
                print("   ✅ PASS: Admin tab is HIDDEN for regular user")
            else:
                print("   ❌ FAIL: Admin tab is VISIBLE for regular user")
        else:
            print("   ❌ Admin tab element not found in DOM")
        
        # Check Contact Admin button visibility
        print("\n3. Checking Contact Admin button visibility...")
        contact_admin = page.query_selector('#admin-chat-tab-btn')
        if contact_admin:
            is_visible = contact_admin.is_visible()
            display = page.evaluate('(el) => window.getComputedStyle(el).display', contact_admin)
            print(f"   📊 Contact Admin button found: {contact_admin is not None}")
            print(f"   📊 Contact Admin visible: {is_visible}")
            print(f"   📊 Display style: {display}")
            
            if is_visible or display != 'none':
                print("   ✅ PASS: Contact Admin button IS VISIBLE for regular user")
            else:
                print("   ❌ FAIL: Contact Admin button is HIDDEN for regular user")
        else:
            print("   ❌ Contact Admin button not found in DOM")
        
        # Check all visible navigation tabs
        print("\n4. Listing all visible navigation tabs...")
        nav_buttons = page.query_selector_all('.nav-btn')
        visible_tabs = []
        for btn in nav_buttons:
            if btn.is_visible():
                tab_name = btn.inner_text().strip()
                visible_tabs.append(tab_name)
        
        print(f"   📊 Visible tabs: {', '.join(visible_tabs)}")
        
        if 'Admin' in visible_tabs:
            print("   ❌ FAIL: 'Admin' tab is visible to regular user")
        else:
            print("   ✅ PASS: 'Admin' tab NOT in visible tabs")
        
        if 'Contact Admin' in visible_tabs or any('Contact' in tab for tab in visible_tabs):
            print("   ✅ PASS: 'Contact Admin' IS in visible tabs")
        else:
            print("   ❌ FAIL: 'Contact Admin' NOT in visible tabs")
        
        # Try to access admin tab content directly (should not be possible)
        print("\n5. Attempting to access admin tab content...")
        admin_tab_content = page.query_selector('#admin-tab')
        if admin_tab_content:
            is_visible = admin_tab_content.is_visible()
            has_active_class = 'active' in (admin_tab_content.get_attribute('class') or '')
            print(f"   📊 Admin tab content exists: True")
            print(f"   📊 Admin tab content visible: {is_visible}")
            print(f"   📊 Has 'active' class: {has_active_class}")
            
            if not is_visible and not has_active_class:
                print("   ✅ PASS: Admin tab content is NOT accessible")
            else:
                print("   ❌ FAIL: Admin tab content IS accessible")
        else:
            print("   📊 Admin tab content not found (this is fine)")
        
        # Check if User Messages section exists but is hidden
        print("\n6. Checking User Messages section...")
        user_messages = page.query_selector('#admin-chat-users-list')
        if user_messages:
            is_visible = user_messages.is_visible()
            print(f"   📊 User Messages section found: True")
            print(f"   📊 User Messages visible: {is_visible}")
            
            if not is_visible:
                print("   ✅ PASS: User Messages section is HIDDEN")
            else:
                print("   ❌ FAIL: User Messages section is VISIBLE")
        else:
            print("   ✅ User Messages section not in DOM (good)")
        
        # Logout
        print("\n7. Logging out...")
        page.evaluate('localStorage.clear(); sessionStorage.clear();')
        page.goto('http://localhost:5000/chatchat')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        print("   ✓ Logged out")
        
        # ===== TEST 2: Administrator =====
        print("\n" + "="*70)
        print("📝 TEST 2: Administrator Access")
        print("-" * 70)
        
        # Login as administrator
        print("1. Logging in as administrator...")
        page.fill('#login-username', 'administrator')
        page.fill('#login-password', 'admin')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        print("   ✓ Logged in successfully")
        
        # Check Admin tab visibility
        print("\n2. Checking Admin tab visibility...")
        admin_tab = page.query_selector('#admin-tab-btn')
        if admin_tab:
            is_visible = admin_tab.is_visible()
            display = page.evaluate('(el) => window.getComputedStyle(el).display', admin_tab)
            print(f"   📊 Admin tab found: {admin_tab is not None}")
            print(f"   📊 Admin tab visible: {is_visible}")
            print(f"   📊 Display style: {display}")
            
            if is_visible and display == 'block':
                print("   ✅ PASS: Admin tab IS VISIBLE for administrator")
            else:
                print("   ❌ FAIL: Admin tab is HIDDEN for administrator")
        else:
            print("   ❌ FAIL: Admin tab element not found in DOM")
        
        # Check Contact Admin button visibility
        print("\n3. Checking Contact Admin button visibility...")
        contact_admin = page.query_selector('#admin-chat-tab-btn')
        if contact_admin:
            is_visible = contact_admin.is_visible()
            display = page.evaluate('(el) => window.getComputedStyle(el).display', contact_admin)
            print(f"   📊 Contact Admin button found: {contact_admin is not None}")
            print(f"   📊 Contact Admin visible: {is_visible}")
            print(f"   📊 Display style: {display}")
            
            if not is_visible and display == 'none':
                print("   ✅ PASS: Contact Admin button is HIDDEN for administrator")
            else:
                print("   ❌ FAIL: Contact Admin button IS VISIBLE for administrator")
        else:
            print("   ⚠️  Contact Admin button not found in DOM")
        
        # Check all visible navigation tabs
        print("\n4. Listing all visible navigation tabs...")
        nav_buttons = page.query_selector_all('.nav-btn')
        visible_tabs = []
        for btn in nav_buttons:
            if btn.is_visible():
                tab_name = btn.inner_text().strip()
                visible_tabs.append(tab_name)
        
        print(f"   📊 Visible tabs: {', '.join(visible_tabs)}")
        
        if 'Admin' in visible_tabs or any('Admin' in tab for tab in visible_tabs):
            print("   ✅ PASS: 'Admin' tab IS in visible tabs")
        else:
            print("   ❌ FAIL: 'Admin' tab NOT in visible tabs")
        
        if 'Contact Admin' in visible_tabs or any('Contact' in tab for tab in visible_tabs):
            print("   ❌ FAIL: 'Contact Admin' IS visible to administrator")
        else:
            print("   ✅ PASS: 'Contact Admin' NOT in visible tabs")
        
        # Click on Admin tab
        print("\n5. Clicking Admin tab...")
        if admin_tab and admin_tab.is_visible():
            admin_tab.click()
            time.sleep(2)
            print("   ✓ Clicked Admin tab")
            
            # Check if User Messages section is now visible
            print("\n6. Checking User Messages section in Admin tab...")
            user_messages = page.query_selector('#admin-chat-users-list')
            if user_messages:
                is_visible = user_messages.is_visible()
                print(f"   📊 User Messages section found: True")
                print(f"   📊 User Messages visible: {is_visible}")
                
                if is_visible:
                    print("   ✅ PASS: User Messages section IS VISIBLE in Admin tab")
                else:
                    print("   ❌ FAIL: User Messages section is HIDDEN in Admin tab")
            else:
                print("   ❌ FAIL: User Messages section not found")
            
            # Check for admin reply input
            admin_reply = page.query_selector('#admin-reply-input')
            if admin_reply:
                print("   ✅ Admin reply input found")
            else:
                print("   ⚠️  Admin reply input not found (might appear after selecting user)")
            
            # Check dashboard title
            dashboard_title = page.query_selector('#admin-dashboard-title')
            if dashboard_title:
                title_text = dashboard_title.inner_text()
                print(f"\n7. Dashboard title: '{title_text}'")
                if title_text == 'Administrator Dashboard':
                    print("   ✅ PASS: Title is 'Administrator Dashboard'")
                else:
                    print(f"   ❌ FAIL: Title is '{title_text}'")
        else:
            print("   ❌ FAIL: Cannot click Admin tab (not visible)")
        
        # ===== FINAL SUMMARY =====
        print("\n" + "="*70)
        print("🏁 Test Summary")
        print("="*70)
        print("\n✅ Expected Behavior:")
        print("  Regular User:")
        print("    - ❌ NO Admin tab visible")
        print("    - ✅ Contact Admin button visible")
        print("    - ❌ NO User Messages section accessible")
        print("\n  Administrator:")
        print("    - ✅ Admin tab visible")
        print("    - ❌ NO Contact Admin button visible")
        print("    - ✅ User Messages section accessible")
        print("    - ✅ Dashboard title: 'Administrator Dashboard'")
        print("\n" + "="*70)
        
        print("\n⏸ Browser will remain open for 10 seconds for inspection...")
        time.sleep(10)
        
        browser.close()

if __name__ == '__main__':
    test_admin_access_control()
