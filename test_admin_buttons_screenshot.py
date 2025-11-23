#!/usr/bin/env python3
"""
Test script to login as admin, navigate to Admin tab, and take screenshots
showing where the bulk delete and permanent delete buttons are located.
"""

from playwright.sync_api import sync_playwright
import time

def test_admin_buttons_with_screenshots():
    """Login as admin and take screenshots of the buttons"""
    
    print("\n" + "=" * 60)
    print("📸 Admin Buttons Screenshot Test")
    print("=" * 60 + "\n")
    
    with sync_playwright() as p:
        # Launch browser
        print("🌐 Launching browser...")
        browser = p.chromium.launch(headless=False)  # headless=False to see it
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        try:
            # Step 1: Go to application
            print("📱 Navigating to login page...")
            page.goto("http://localhost:5000/chatchat")
            
            # Wait for login screen to be visible
            print("⏳ Waiting for login screen...")
            page.wait_for_selector('#login-screen', state='visible', timeout=10000)
            time.sleep(1)
            
            # Take screenshot of initial page
            page.screenshot(path="test_screenshots/00_initial_page.png")
            print("  ✅ Screenshot saved: 00_initial_page.png")
            
            # Step 2: Login as administrator
            print("🔐 Logging in as administrator...")
            page.wait_for_selector('#login-username', state='visible', timeout=5000)
            page.fill('#login-username', 'administrator')
            page.fill('#login-password', 'admin123')
            
            # Take screenshot of login screen
            page.screenshot(path="test_screenshots/01_login_screen.png")
            print("  ✅ Screenshot saved: 01_login_screen.png")
            
            page.click('button[type="submit"]')
            time.sleep(3)
            
            # Step 3: Check if logged in
            print("✅ Logged in, checking dashboard...")
            page.screenshot(path="test_screenshots/02_dashboard_after_login.png")
            print("  ✅ Screenshot saved: 02_dashboard_after_login.png")
            
            # Step 4: Look for Admin tab
            print("🔍 Looking for Admin tab...")
            admin_tab = page.locator('#admin-tab-btn')
            
            if admin_tab.is_visible():
                print("  ✅ Admin tab found!")
                
                # Highlight the admin tab
                page.evaluate("""
                    const adminTab = document.querySelector('#admin-tab-btn');
                    if (adminTab) {
                        adminTab.style.border = '3px solid red';
                        adminTab.style.boxShadow = '0 0 10px red';
                    }
                """)
                time.sleep(1)
                
                page.screenshot(path="test_screenshots/03_admin_tab_highlighted.png")
                print("  ✅ Screenshot saved: 03_admin_tab_highlighted.png")
                
                # Step 5: Click Admin tab
                print("👆 Clicking Admin tab...")
                admin_tab.click()
                time.sleep(3)
                
                page.screenshot(path="test_screenshots/04_admin_tab_opened.png")
                print("  ✅ Screenshot saved: 04_admin_tab_opened.png")
                
                # Step 6: Scroll to users table
                print("📜 Scrolling to users table...")
                page.evaluate("window.scrollTo(0, 500)")
                time.sleep(1)
                
                # Step 7: Scroll to top to see bulk delete button
                print("🔍 Scrolling to top to find Bulk Delete button...")
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                
                # Now scroll down to users section
                page.evaluate("""
                    const usersSection = document.querySelector('.admin-section');
                    if (usersSection) {
                        usersSection.scrollIntoView({behavior: 'smooth', block: 'start'});
                    }
                """)
                time.sleep(2)
                
                # Look for bulk delete button
                print("🔍 Looking for Bulk Delete button...")
                bulk_delete_btn = page.locator('#bulk-delete-users-btn')
                
                if bulk_delete_btn.is_visible():
                    print("  ✅ Bulk Delete button FOUND!")
                    
                    # Highlight the bulk delete button
                    page.evaluate("""
                        const bulkBtn = document.querySelector('#bulk-delete-users-btn');
                        if (bulkBtn) {
                            bulkBtn.style.border = '5px solid lime';
                            bulkBtn.style.boxShadow = '0 0 20px lime';
                        }
                    """)
                    time.sleep(1)
                    
                    page.screenshot(path="test_screenshots/05_bulk_delete_button_highlighted.png")
                    print("  ✅ Screenshot saved: 05_bulk_delete_button_highlighted.png")
                else:
                    print("  ❌ Bulk Delete button NOT visible")
                    page.screenshot(path="test_screenshots/05_bulk_delete_NOT_FOUND.png")
                
                # Step 8: Look for deleted users with permanent delete button
                print("🔍 Looking for deleted users and permanent delete buttons...")
                time.sleep(1)
                
                # Check if there are deleted users
                deleted_users = page.locator('tr[style*="opacity: 0.5"]')
                count = deleted_users.count()
                
                print(f"  Found {count} deleted users")
                
                if count > 0:
                    # Highlight first deleted user row
                    page.evaluate("""
                        const deletedRow = document.querySelector('tr[style*="opacity: 0.5"]');
                        if (deletedRow) {
                            deletedRow.style.border = '3px solid orange';
                            deletedRow.style.boxShadow = '0 0 15px orange';
                            deletedRow.scrollIntoView({behavior: 'smooth', block: 'center'});
                        }
                    """)
                    time.sleep(2)
                    
                    page.screenshot(path="test_screenshots/06_deleted_user_highlighted.png")
                    print("  ✅ Screenshot saved: 06_deleted_user_highlighted.png")
                    
                    # Look for "Delete Forever" button using Playwright locator
                    delete_forever_btn = page.locator('button:has-text("Delete Forever")')
                    if delete_forever_btn.count() > 0:
                        print(f"  ✅ Found {delete_forever_btn.count()} 'Delete Forever' button(s)")
                        
                        # Highlight the first Delete Forever button using plain JavaScript
                        page.evaluate("""
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const deleteBtn = buttons.find(btn => btn.textContent.includes('Delete Forever'));
                            if (deleteBtn) {
                                deleteBtn.style.border = '3px solid red';
                                deleteBtn.style.boxShadow = '0 0 15px red';
                            }
                        """)
                        time.sleep(1)
                        
                        page.screenshot(path="test_screenshots/07_delete_forever_button_highlighted.png")
                        print("  ✅ Screenshot saved: 07_delete_forever_button_highlighted.png")
                    else:
                        print("  ❌ 'Delete Forever' button NOT found")
                else:
                    print("  ℹ️  No deleted users to show permanent delete button")
                    page.screenshot(path="test_screenshots/06_no_deleted_users.png")
                
                # Step 9: Full page screenshot
                print("📸 Taking full page screenshot...")
                page.screenshot(path="test_screenshots/08_full_admin_page.png", full_page=True)
                print("  ✅ Screenshot saved: 08_full_admin_page.png")
                
            else:
                print("  ❌ Admin tab NOT visible (may not have admin permissions)")
                page.screenshot(path="test_screenshots/03_NO_ADMIN_TAB.png")
            
            # Summary
            print("\n" + "=" * 60)
            print("✅ Screenshot test complete!")
            print("=" * 60)
            print("\n📁 Screenshots saved to: test_screenshots/")
            print("\nScreenshots taken:")
            print("  1. 01_login_screen.png")
            print("  2. 02_dashboard_after_login.png")
            print("  3. 03_admin_tab_highlighted.png (or 03_NO_ADMIN_TAB.png)")
            print("  4. 04_admin_tab_opened.png")
            print("  5. 05_bulk_delete_button_highlighted.png")
            print("  6. 06_deleted_user_highlighted.png (or 06_no_deleted_users.png)")
            print("  7. 07_delete_forever_button_highlighted.png")
            print("  8. 08_full_admin_page.png")
            
            # Keep browser open for a moment
            print("\n⏱️  Keeping browser open for 5 seconds...")
            time.sleep(5)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="test_screenshots/ERROR_screenshot.png")
            print("  ✅ Error screenshot saved: ERROR_screenshot.png")
            raise
        finally:
            browser.close()
            print("\n👋 Browser closed")

if __name__ == "__main__":
    import sys
    import os
    
    # Create screenshots directory
    os.makedirs("test_screenshots", exist_ok=True)
    
    try:
        test_admin_buttons_with_screenshots()
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)
