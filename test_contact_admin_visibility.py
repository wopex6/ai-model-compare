"""
Deep dive test to investigate Contact Admin button visibility issue
"""

from playwright.sync_api import sync_playwright
import time

def test_contact_admin_visibility():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        print("\n" + "="*70)
        print("🔍 Investigating Contact Admin Button Visibility")
        print("="*70)
        
        page.goto('http://localhost:5000/chatchat')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Login as regular user
        print("\n1. Logging in as Wai Tse...")
        page.fill('#login-username', 'Wai Tse')
        page.fill('#login-password', './/')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        print("   ✓ Logged in")
        
        # Get detailed CSS properties
        print("\n2. Getting detailed CSS properties of Contact Admin button...")
        contact_btn = page.query_selector('#admin-chat-tab-btn')
        
        if contact_btn:
            css_props = page.evaluate('''(el) => {
                const style = window.getComputedStyle(el);
                return {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    width: style.width,
                    height: style.height,
                    position: style.position,
                    zIndex: style.zIndex,
                    overflow: style.overflow,
                    pointerEvents: style.pointerEvents
                };
            }''', contact_btn)
            
            print("\n   CSS Properties:")
            for prop, value in css_props.items():
                print(f"   - {prop}: {value}")
            
            # Check parent elements
            print("\n3. Checking parent element properties...")
            parent_props = page.evaluate('''(el) => {
                const parent = el.parentElement;
                const style = window.getComputedStyle(parent);
                return {
                    tagName: parent.tagName,
                    className: parent.className,
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity
                };
            }''', contact_btn)
            
            print(f"\n   Parent Element:")
            for prop, value in parent_props.items():
                print(f"   - {prop}: {value}")
            
            # Check bounding box
            print("\n4. Checking element bounding box...")
            bbox = contact_btn.bounding_box()
            if bbox:
                print(f"   - x: {bbox['x']}")
                print(f"   - y: {bbox['y']}")
                print(f"   - width: {bbox['width']}")
                print(f"   - height: {bbox['height']}")
                
                viewport = page.viewport_size()
                print(f"\n   Viewport size:")
                print(f"   - width: {viewport['width']}")
                print(f"   - height: {viewport['height']}")
                
                in_viewport = (
                    bbox['x'] >= 0 and
                    bbox['y'] >= 0 and
                    bbox['x'] + bbox['width'] <= viewport['width'] and
                    bbox['y'] + bbox['height'] <= viewport['height']
                )
                print(f"\n   In viewport: {in_viewport}")
            else:
                print("   ⚠️  No bounding box (element might be hidden)")
            
            # Check if element is covered by other elements
            print("\n5. Checking if element is covered...")
            is_covered = page.evaluate('''(el) => {
                const rect = el.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const topElement = document.elementFromPoint(centerX, centerY);
                return topElement !== el && !el.contains(topElement);
            }''', contact_btn)
            
            print(f"   Element is covered by another element: {is_covered}")
            
            # Try to click with force
            print("\n6. Attempting to click button...")
            try:
                contact_btn.click(timeout=2000)
                print("   ✅ Click successful")
                time.sleep(2)
                
                # Check if admin chat tab is now visible
                admin_chat_tab = page.query_selector('#admin-chat-tab')
                if admin_chat_tab and admin_chat_tab.is_visible():
                    print("   ✅ Admin chat tab opened successfully")
                else:
                    print("   ❌ Admin chat tab did not open")
            except Exception as e:
                print(f"   ❌ Click failed: {str(e)}")
                
                # Try force click
                print("\n7. Attempting force click...")
                try:
                    contact_btn.click(force=True)
                    print("   ✅ Force click successful")
                    time.sleep(2)
                    
                    admin_chat_tab = page.query_selector('#admin-chat-tab')
                    if admin_chat_tab and admin_chat_tab.is_visible():
                        print("   ✅ Admin chat tab opened with force click")
                    else:
                        print("   ❌ Admin chat tab did not open even with force click")
                except Exception as e2:
                    print(f"   ❌ Force click also failed: {str(e2)}")
        else:
            print("   ❌ Contact Admin button not found")
        
        # Check all navigation buttons
        print("\n8. Checking all navigation buttons...")
        all_nav_btns = page.query_selector_all('.nav-btn')
        print(f"\n   Found {len(all_nav_btns)} navigation buttons:")
        
        for i, btn in enumerate(all_nav_btns):
            text = btn.inner_text().strip()
            is_visible = btn.is_visible()
            display = page.evaluate('(el) => window.getComputedStyle(el).display', btn)
            data_tab = btn.get_attribute('data-tab')
            btn_id = btn.get_attribute('id')
            
            print(f"\n   Button {i+1}:")
            print(f"   - Text: {text}")
            print(f"   - ID: {btn_id}")
            print(f"   - data-tab: {data_tab}")
            print(f"   - is_visible(): {is_visible}")
            print(f"   - display: {display}")
        
        print("\n" + "="*70)
        print("⏸ Browser will remain open for 10 seconds...")
        time.sleep(10)
        
        browser.close()

if __name__ == '__main__':
    test_contact_admin_visibility()
