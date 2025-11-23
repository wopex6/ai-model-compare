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

def test_personality_navigation():
    """Test different paths into and out of personality test"""

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
        print("TESTING PERSONALITY TEST NAVIGATION")
        print("="*80)
        
        try:
            # Step 1: Login
            print("\n✅ Step 1: Login to application")
            page.goto('http://localhost:5000/chatchat')
            page.fill('#login-username', 'test_user')
            page.fill('#login-password', 'testpass')
            page.click('button[type="submit"]')
            time.sleep(2)
            
            # Verify we're in dashboard (not login screen)
            dashboard = page.locator('#dashboard-screen')
            if dashboard.is_visible():
                print("   ✅ Successfully logged in to dashboard")
            else:
                print("   ❌ Login failed - still on login screen")
                return
            
            page.screenshot(path='test_screenshots/nav_1_dashboard.png')
            
            # Step 2: Go to Psychology tab
            print("\n✅ Step 2: Navigate to Psychology tab")
            page.click('button[data-tab="psychology"]')
            time.sleep(1)
            page.screenshot(path='test_screenshots/nav_2_psychology.png')
            
            # Check if charts are visible
            traits_grid = page.locator('#traits-grid')
            print(f"   Traits grid visible: {traits_grid.is_visible()}")
            
            # Step 3: Click "Take Personality Test" button
            print("\n✅ Step 3: Click 'Take Personality Test' button")
            page.click('#take-personality-test-btn')
            time.sleep(2)
            
            # Verify we're on personality test page
            current_url = page.url
            print(f"   Current URL: {current_url}")
            if '/personality-test' in current_url:
                print("   ✅ Successfully navigated to personality test")
            else:
                print(f"   ❌ Wrong URL: {current_url}")
            
            page.screenshot(path='test_screenshots/nav_3_test_welcome.png')
            
            # Step 4: Start assessment
            print("\n✅ Step 4: Start assessment")
            start_button = page.locator('button:has-text("Start Assessment")')
            if start_button.is_visible():
                start_button.click()
                time.sleep(1)
                page.screenshot(path='test_screenshots/nav_4_question1.png')
                print("   ✅ Assessment started")
            
            # Step 5: Answer a few questions
            print("\n✅ Step 5: Answer 3 questions")
            for i in range(3):
                options = page.locator('.option')
                if options.count() > 0:
                    options.nth(0).click()
                    time.sleep(0.5)
                    print(f"   Question {i+1} answered")
                else:
                    print(f"   ❌ No options found for question {i+1}")
                    break
            
            page.screenshot(path='test_screenshots/nav_5_answered_3.png')
            
            # TEST PATH 1: Click "Go Back" button
            print("\n" + "="*80)
            print("TEST PATH 1: Click 'Go Back' Button")
            print("="*80)
            
            # Find the appropriate back button
            back_button = page.locator('button:has-text("Go Back"), button:has-text("⬅️")')
            if back_button.count() > 0:
                # There might be multiple back buttons, click the completion one if available
                # For now in questions, use Pause
                print("\n   Pausing assessment first...")
                page.click('button:has-text("Pause Assessment")')
                time.sleep(1.5)
                
                # Should be back at dashboard
                current_url = page.url
                print(f"   Current URL after pause: {current_url}")
                
                if '/chatchat' in current_url:
                    print("   ✅ Returned to dashboard via Pause")
                    
                    # Check if we're still logged in
                    dashboard_visible = page.locator('#dashboard-screen').is_visible()
                    print(f"   Dashboard visible: {dashboard_visible}")
                    
                    if not dashboard_visible:
                        login_screen = page.locator('#login-screen').is_visible()
                        print(f"   ❌ FAILED: Went to login screen ({login_screen})")
                    else:
                        print("   ✅ PASSED: Still on dashboard")
                    
                    page.screenshot(path='test_screenshots/nav_6_back_from_pause.png')
                    
                    # Check if Psychology tab still has data
                    psych_button = page.locator('button[data-tab="psychology"]')
                    if psych_button.is_visible():
                        psych_button.click()
                        time.sleep(1)
                        
                        traits_visible = page.locator('#traits-grid').is_visible()
                        print(f"   Traits grid still visible: {traits_visible}")
                        
                        if traits_visible:
                            print("   ✅ PASSED: Psychology data preserved")
                        else:
                            print("   ❌ FAILED: Psychology data disappeared")
                        
                        page.screenshot(path='test_screenshots/nav_7_psychology_after_pause.png')
            
            # TEST PATH 2: Complete assessment and use "Start Chatting"
            print("\n" + "="*80)
            print("TEST PATH 2: Complete Assessment → 'Start Chatting'")
            print("="*80)
            
            # Go back to personality test
            print("\n   Returning to personality test...")
            page.click('#take-personality-test-btn')
            time.sleep(2)
            
            # Should see resume option
            resume_button = page.locator('button:has-text("Resume Assessment")')
            if resume_button.is_visible():
                print("   ✅ Resume button found")
                resume_button.click()
                time.sleep(1)
            else:
                print("   Starting new assessment...")
                page.click('button:has-text("Start Assessment")')
                time.sleep(1)
            
            # Answer remaining questions to complete
            print("   Answering all remaining questions...")
            for i in range(40):
                options = page.locator('.option')
                if options.count() > 0:
                    options.nth(0).click()
                    time.sleep(0.3)
                    
                    # Check if we've reached completion
                    completion_title = page.locator('h2:has-text("Assessment Complete")')
                    if completion_title.is_visible():
                        print(f"   ✅ Assessment completed after {i+1} questions")
                        break
                else:
                    break
            
            time.sleep(4)  # Wait for animation
            page.screenshot(path='test_screenshots/nav_8_completion_screen.png')
            
            # Click "Start Chatting"
            print("\n   Clicking 'Start Chatting' button...")
            chat_button = page.locator('button:has-text("Start Chatting")')
            if chat_button.is_visible():
                chat_button.click()
                time.sleep(2)
                
                current_url = page.url
                print(f"   Current URL: {current_url}")
                
                # Should be on chatchat with ?tab=chat
                if '/chatchat' in current_url and 'tab=chat' in current_url:
                    print("   ✅ PASSED: Navigated to Conversations tab")
                elif '/chatchat' in current_url:
                    print("   ⚠️  On chatchat but not Conversations tab")
                else:
                    print(f"   ❌ FAILED: Wrong URL: {current_url}")
                
                # Check not on login screen
                login_visible = page.locator('#login-screen').is_visible()
                dashboard_visible = page.locator('#dashboard-screen').is_visible()
                
                print(f"   Login screen visible: {login_visible}")
                print(f"   Dashboard visible: {dashboard_visible}")
                
                if not login_visible and dashboard_visible:
                    print("   ✅ PASSED: Not on login screen")
                else:
                    print("   ❌ FAILED: On login screen or dashboard missing")
                
                page.screenshot(path='test_screenshots/nav_9_after_start_chatting.png')
            
            # TEST PATH 3: Return to completed test → Use "Go Back"
            print("\n" + "="*80)
            print("TEST PATH 3: Return to Completed Test → 'Go Back'")
            print("="*80)
            
            # Go to Psychology tab first
            print("\n   Going to Psychology tab...")
            page.click('button[data-tab="psychology"]')
            time.sleep(1)
            
            # Click personality test again
            print("   Clicking 'Take Personality Test' again...")
            page.click('#take-personality-test-btn')
            time.sleep(3)
            
            # Should show completion screen immediately
            completion_visible = page.locator('h2:has-text("Assessment Complete")').is_visible()
            print(f"   Completion screen shown: {completion_visible}")
            
            if completion_visible:
                print("   ✅ PASSED: Shows completion screen for completed test")
                time.sleep(3)  # Wait for animation
                page.screenshot(path='test_screenshots/nav_10_return_to_completed.png')
                
                # Click "Go Back"
                back_button = page.locator('button:has-text("Go Back")')
                if back_button.is_visible():
                    print("   Clicking 'Go Back' button...")
                    back_button.click()
                    time.sleep(2)
                    
                    current_url = page.url
                    print(f"   Current URL: {current_url}")
                    
                    # Should be back at previous page
                    if '/chatchat' in current_url:
                        print("   ✅ PASSED: Went back to dashboard")
                        
                        # Check not on login
                        login_visible = page.locator('#login-screen').is_visible()
                        dashboard_visible = page.locator('#dashboard-screen').is_visible()
                        
                        if not login_visible and dashboard_visible:
                            print("   ✅ PASSED: Still logged in")
                        else:
                            print("   ❌ FAILED: Went to login screen")
                        
                        # Check Psychology data still there
                        psych_tab_visible = page.locator('#psychology-tab').is_visible()
                        if psych_tab_visible:
                            traits_visible = page.locator('#traits-grid').is_visible()
                            print(f"   Traits visible: {traits_visible}")
                            
                            if traits_visible:
                                print("   ✅ PASSED: Psychology data still visible")
                            else:
                                print("   ❌ FAILED: Psychology data disappeared")
                        
                        page.screenshot(path='test_screenshots/nav_11_final_state.png')
            
            # SUMMARY
            print("\n" + "="*80)
            print("TEST SUMMARY")
            print("="*80)
            print("✅ All navigation paths tested")
            print("✅ Screenshots saved in test_screenshots/")
            print("\nVerify the following:")
            print("1. Never goes to login screen during navigation")
            print("2. Psychology traits/charts don't disappear")
            print("3. 'Start Chatting' goes to Conversations tab")
            print("4. 'Go Back' returns to previous page")
            print("="*80 + "\n")
            
            time.sleep(3)
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            page.screenshot(path='test_screenshots/nav_error.png')
            import traceback
            traceback.print_exc()
            
        finally:
            browser.close()

if __name__ == '__main__':
    test_personality_navigation()
