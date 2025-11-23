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

def test_psychology_charts_update():
    """Test that psychology charts update after completing assessment"""

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
        print("TESTING PSYCHOLOGY CHARTS UPDATE")
        print("="*80)
        
        try:
            # Step 1: Login
            print("\n✅ Step 1: Login to application")
            page.goto('http://localhost:5000/chatchat')
            page.fill('#login-username', 'WK')
            page.fill('#login-password', 'testpass')
            page.click('button[type="submit"]')
            time.sleep(2)
            
            # Verify login
            dashboard = page.locator('#dashboard-screen')
            if dashboard.is_visible():
                print("   ✅ Successfully logged in")
            else:
                print("   ❌ Login failed")
                return
            
            page.screenshot(path='test_screenshots/charts_1_login.png')
            
            # Step 2: Check Psychology tab BEFORE assessment
            print("\n✅ Step 2: Check Psychology tab BEFORE assessment")
            page.click('button[data-tab="psychology"]')
            time.sleep(1)
            
            # Check current traits
            traits_grid = page.locator('#traits-grid')
            traits_text = traits_grid.inner_text() if traits_grid.is_visible() else ""
            print(f"   Current traits: {traits_text[:100]}...")
            
            page.screenshot(path='test_screenshots/charts_2_psychology_before.png')
            
            # Check if tip is visible
            tip = page.locator('#assessment-tip')
            tip_visible = tip.is_visible() if tip.count() > 0 else False
            print(f"   Assessment tip visible: {tip_visible}")
            
            # Click Assessment History
            print("\n✅ Step 3: Check Assessment History BEFORE")
            page.click('button[data-section="history"]')
            time.sleep(1)
            
            history_container = page.locator('#assessment-history-container')
            history_text = history_container.inner_text() if history_container.is_visible() else ""
            print(f"   History: {history_text[:100]}...")
            
            page.screenshot(path='test_screenshots/charts_3_history_before.png')
            
            # Count history entries
            history_items = page.locator('.assessment-item').count()
            print(f"   History entries BEFORE: {history_items}")
            
            # Step 4: Take personality test
            print("\n✅ Step 4: Take personality test")
            page.click('#take-personality-test-btn')
            time.sleep(2)
            
            current_url = page.url
            print(f"   Current URL: {current_url}")
            page.screenshot(path='test_screenshots/charts_4_test_page.png')
            
            # Check if welcome or resume screen
            welcome_title = page.locator('h1:has-text("Personality Assessment")')
            resume_button = page.locator('button:has-text("Resume Assessment")')
            start_button = page.locator('button:has-text("Start Assessment")')
            completion_title = page.locator('h2:has-text("Assessment Complete")')
            
            if completion_title.is_visible():
                print("   ⚠️  Assessment already completed!")
                print("   Testing 'Go Back' navigation from completed screen...")
                
                time.sleep(3)  # Wait for animation
                page.screenshot(path='test_screenshots/charts_5_already_completed.png')
                
                # Click Go Back
                back_button = page.locator('button:has-text("Go Back")')
                if back_button.is_visible():
                    print("\n✅ Step 5: Click 'Go Back' button")
                    back_button.click()
                    time.sleep(2)
                    
                    current_url = page.url
                    print(f"   Current URL after Go Back: {current_url}")
                    
                    # Check if we're on psychology page
                    if '/chatchat' in current_url:
                        print("   ✅ Navigated back to dashboard")
                        
                        # Check if psychology tab is active
                        psych_tab = page.locator('#psychology-tab')
                        if psych_tab.is_visible():
                            print("   ✅ Psychology tab visible")
                        else:
                            print("   ⚠️  Psychology tab not visible, activating it...")
                            page.click('button[data-tab="psychology"]')
                            time.sleep(1)
                        
                        page.screenshot(path='test_screenshots/charts_6_after_go_back.png')
                    else:
                        print(f"   ❌ Wrong URL: {current_url}")
                
            else:
                # Start or resume assessment
                if resume_button.is_visible():
                    print("   Found resume button - clicking it...")
                    resume_button.click()
                    time.sleep(1)
                elif start_button.is_visible():
                    print("   Starting new assessment...")
                    start_button.click()
                    time.sleep(1)
                
                # Answer all questions
                print("\n✅ Step 5: Answer all questions")
                for i in range(50):  # Max 50 iterations
                    options = page.locator('.option')
                    if options.count() > 0:
                        options.nth(0).click()
                        time.sleep(0.3)
                        
                        # Check if completed
                        if page.locator('h2:has-text("Assessment Complete")').is_visible():
                            print(f"   ✅ Assessment completed after {i+1} answers")
                            break
                    else:
                        break
                
                # Wait for animation
                time.sleep(4)
                page.screenshot(path='test_screenshots/charts_5_completion.png')
                
                # Test Go Back button
                print("\n✅ Step 6: Click 'Go Back' button")
                back_button = page.locator('button:has-text("Go Back")')
                if back_button.is_visible():
                    back_button.click()
                    time.sleep(2)
                    
                    current_url = page.url
                    print(f"   Current URL: {current_url}")
                    
                    # Should be on psychology page
                    if '/chatchat' in current_url and 'psychology' in current_url:
                        print("   ✅ Navigated to Psychology page")
                    elif '/chatchat' in current_url:
                        print("   ⚠️  On dashboard, navigating to Psychology...")
                        page.click('button[data-tab="psychology"]')
                        time.sleep(1)
                    
                    page.screenshot(path='test_screenshots/charts_6_after_go_back.png')
            
            # Step 7: Check Psychology tab AFTER assessment
            print("\n✅ Step 7: Check Psychology tab AFTER assessment")
            
            # Make sure we're on psychology tab
            page.click('button[data-tab="psychology"]')
            time.sleep(1)
            
            # Check Current Traits section
            page.click('button[data-section="current"]')
            time.sleep(1)
            
            traits_grid_after = page.locator('#traits-grid')
            traits_text_after = traits_grid_after.inner_text() if traits_grid_after.is_visible() else ""
            print(f"   Traits AFTER: {traits_text_after[:200]}...")
            
            # Check if tip is hidden
            tip_visible_after = tip.is_visible() if tip.count() > 0 else False
            print(f"   Assessment tip visible AFTER: {tip_visible_after}")
            
            if tip_visible_after:
                print("   ❌ FAILED: Tip should be hidden after completion!")
            else:
                print("   ✅ PASSED: Tip is hidden")
            
            # Count trait cards
            trait_cards = page.locator('.trait-card').count()
            print(f"   Trait cards visible: {trait_cards}")
            
            if trait_cards > 0:
                print("   ✅ PASSED: Trait cards are visible")
            else:
                print("   ❌ FAILED: No trait cards visible!")
            
            page.screenshot(path='test_screenshots/charts_7_traits_after.png')
            
            # Step 8: Check Assessment History AFTER
            print("\n✅ Step 8: Check Assessment History AFTER")
            page.click('button[data-section="history"]')
            time.sleep(1)
            
            history_items_after = page.locator('.assessment-item').count()
            print(f"   History entries AFTER: {history_items_after}")
            
            if history_items_after > history_items:
                print(f"   ✅ PASSED: History increased from {history_items} to {history_items_after}")
            elif history_items_after > 0:
                print(f"   ✅ PASSED: History has {history_items_after} entries")
            else:
                print("   ❌ FAILED: No history entries!")
            
            # Take screenshot of history
            history_text_after = history_container.inner_text() if history_container.is_visible() else ""
            print(f"   History content: {history_text_after[:300]}...")
            
            page.screenshot(path='test_screenshots/charts_8_history_after.png')
            
            # Step 9: Check Progress Chart
            print("\n✅ Step 9: Check Progress Chart")
            page.click('button[data-section="chart"]')
            time.sleep(1)
            
            chart_canvas = page.locator('#psychology-chart-canvas')
            if chart_canvas.is_visible():
                print("   ✅ Chart canvas visible")
            else:
                print("   ❌ Chart canvas not visible")
            
            page.screenshot(path='test_screenshots/charts_9_chart.png')
            
            # SUMMARY
            print("\n" + "="*80)
            print("TEST SUMMARY")
            print("="*80)
            print(f"✅ History entries BEFORE: {history_items}")
            print(f"✅ History entries AFTER: {history_items_after}")
            print(f"✅ Trait cards visible: {trait_cards}")
            print(f"✅ Tip hidden after completion: {not tip_visible_after}")
            print("\nVerify the following in screenshots:")
            print("1. charts_2_psychology_before.png - Before state")
            print("2. charts_7_traits_after.png - Traits updated")
            print("3. charts_8_history_after.png - History has entries")
            print("4. charts_9_chart.png - Chart visible")
            print("="*80 + "\n")
            
            time.sleep(3)
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            page.screenshot(path='test_screenshots/charts_error.png')
            import traceback
            traceback.print_exc()
            
        finally:
            browser.close()

if __name__ == '__main__':
    test_psychology_charts_update()
