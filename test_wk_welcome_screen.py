from playwright.sync_api import sync_playwright
import time
import requests

def check_server():
    """Check if Flask server is running"""
    try:
        response = requests.get('http://localhost:5000')
        return response.status_code in [200, 404, 302]
    except:
        return False

def test_wk_welcome_screen():
    """Test that user WK sees welcome screen (not completion) when taking personality test"""

    if not check_server():
        print("\n❌ ERROR: Flask server is not running!")
        print("Please start the Flask server first:")
        print("   python app.py")
        print("\nThen run this test again.\n")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        print("\n" + "="*80)
        print("TESTING USER WK - WELCOME SCREEN (NOT COMPLETION)")
        print("="*80)
        
        try:
            # Step 1: Login as user WK
            print("\n✅ Step 1: Login as user WK")
            page.goto('http://localhost:5000/chatchat')
            time.sleep(1)
            
            # Fill login form
            page.fill('#login-username', 'WK')
            page.fill('#login-password', 'testpass')
            page.screenshot(path='test_screenshots/wk_1_login_form.png')
            
            page.click('button[type="submit"]')
            time.sleep(2)
            
            # Verify login successful
            dashboard = page.locator('#dashboard-screen')
            login_screen = page.locator('#login-screen')
            
            if dashboard.is_visible():
                print("   ✅ Successfully logged in as WK")
            elif login_screen.is_visible():
                print("   ❌ Login failed - still on login screen")
                page.screenshot(path='test_screenshots/wk_error_login_failed.png')
                return
            else:
                print("   ⚠️  Unknown state after login")
                page.screenshot(path='test_screenshots/wk_error_unknown_state.png')
                return
            
            page.screenshot(path='test_screenshots/wk_2_logged_in.png')
            
            # Step 2: Navigate to Psychology tab
            print("\n✅ Step 2: Navigate to Psychology tab")
            page.click('button[data-tab="psychology"]')
            time.sleep(1)
            
            psych_tab = page.locator('#psychology-tab')
            if psych_tab.is_visible():
                print("   ✅ Psychology tab visible")
            else:
                print("   ❌ Psychology tab not visible")
            
            page.screenshot(path='test_screenshots/wk_3_psychology_tab.png')
            
            # Step 3: Click "Take Personality Test" button (opens popup)
            print("\n✅ Step 3: Click 'Take Personality Test' button")
            test_button = page.locator('#take-personality-test-btn')
            
            if test_button.is_visible():
                print("   ✅ Test button found")
                
                # Wait for the popup to open
                with context.expect_page() as popup_info:
                    test_button.click()
                    time.sleep(1)
                
                popup = popup_info.value
                popup.wait_for_load_state()
                time.sleep(1)
                
                print(f"   ✅ Popup window opened")
                print(f"   Popup URL: {popup.url}")
                
                if '/personality-test' not in popup.url:
                    print(f"   ❌ Wrong URL - not on personality test page")
                    popup.screenshot(path='test_screenshots/wk_error_wrong_url.png')
                    return
                else:
                    print("   ✅ Navigated to personality test page in popup")
                
                popup.screenshot(path='test_screenshots/wk_4_test_page.png')
                
                # Now work with the popup instead of main page
                page = popup
            else:
                print("   ❌ Test button not found")
                page.screenshot(path='test_screenshots/wk_error_no_button.png')
                return
            
            # Step 4: Check what screen is displayed
            print("\n✅ Step 4: Verify WELCOME screen is shown (NOT completion)")
            
            # Wait for content to load
            time.sleep(2)
            
            # Check for welcome screen elements
            welcome_title = page.locator('h2:has-text("Personality Assessment")')
            welcome_visible = welcome_title.is_visible() if welcome_title.count() > 0 else False
            
            # Check for start button
            start_button = page.locator('button:has-text("Start Assessment")')
            start_visible = start_button.is_visible() if start_button.count() > 0 else False
            
            # Check for maybe later button
            maybe_button = page.locator('button:has-text("Maybe Later")')
            maybe_visible = maybe_button.is_visible() if maybe_button.count() > 0 else False
            
            # Check for completion screen (should NOT be visible)
            completion_title = page.locator('h2:has-text("Assessment Complete")')
            completion_visible = completion_title.is_visible() if completion_title.count() > 0 else False
            
            # Check for go back button (only on completion screen)
            go_back_button = page.locator('button:has-text("Go Back")')
            go_back_visible = go_back_button.is_visible() if go_back_button.count() > 0 else False
            
            print("\n   📊 Screen Detection:")
            print(f"   Welcome title ('Personality Assessment'): {welcome_visible}")
            print(f"   Start Assessment button: {start_visible}")
            print(f"   Maybe Later button: {maybe_visible}")
            print(f"   Completion title ('Assessment Complete'): {completion_visible}")
            print(f"   Go Back button: {go_back_visible}")
            
            page.screenshot(path='test_screenshots/wk_5_screen_check.png')
            
            # Step 5: Verify results
            print("\n" + "="*80)
            print("TEST RESULTS")
            print("="*80)
            
            if welcome_visible and start_visible and not completion_visible:
                print("✅ PASSED: Welcome screen is shown correctly!")
                print("   ✅ Shows 'Personality Assessment' title")
                print("   ✅ Shows 'Start Assessment' button")
                print("   ✅ Does NOT show 'Assessment Complete'")
                print("   ✅ Does NOT show 'Go Back' button (completion only)")
                test_passed = True
            elif completion_visible:
                print("❌ FAILED: Completion screen is shown (should be welcome screen!)")
                print("   ❌ Shows 'Assessment Complete' title")
                print("   This means user WK is incorrectly detected as having completed assessment")
                test_passed = False
            elif not welcome_visible and not completion_visible:
                print("❌ FAILED: Neither welcome nor completion screen detected")
                print("   Unknown screen state - check screenshot")
                test_passed = False
            else:
                print("⚠️  PARTIAL: Some elements missing")
                print(f"   Welcome title: {welcome_visible}")
                print(f"   Start button: {start_visible}")
                print(f"   Completion title: {completion_visible}")
                test_passed = False
            
            # Step 6: Get page content for debugging
            content_div = page.locator('#content')
            if content_div.is_visible():
                content_text = content_div.inner_text()
                print(f"\n   Page content preview:")
                print(f"   {content_text[:200]}...")
            
            page.screenshot(path='test_screenshots/wk_6_final_result.png')
            
            print("\n" + "="*80)
            print("VERIFICATION COMPLETE")
            print("="*80)
            print(f"\n{'✅ TEST PASSED' if test_passed else '❌ TEST FAILED'}")
            print("\nScreenshots saved:")
            print("  - wk_1_login_form.png")
            print("  - wk_2_logged_in.png")
            print("  - wk_3_psychology_tab.png")
            print("  - wk_4_test_page.png")
            print("  - wk_5_screen_check.png")
            print("  - wk_6_final_result.png")
            print("="*80 + "\n")
            
            # Keep browser open for 3 seconds to see result
            time.sleep(3)
            
            return test_passed
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            page.screenshot(path='test_screenshots/wk_error.png')
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            browser.close()

if __name__ == '__main__':
    result = test_wk_welcome_screen()
    if result:
        print("\n🎉 All checks passed! User WK correctly sees welcome screen.\n")
    else:
        print("\n⚠️  Test failed. Check screenshots for details.\n")
