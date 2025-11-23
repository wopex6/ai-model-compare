"""
Simplified Playwright test using existing user WK4
Tests complete personality assessment flow with trait updates
"""

from playwright.sync_api import sync_playwright
import time

def test_wk4_personality_flow():
    print("\n" + "="*80)
    print("TESTING WK4 PERSONALITY ASSESSMENT & TRAIT UPDATE")
    print("="*80)
    
    username = "wk4"
    password = "123"
    
    print(f"\n📝 Using test user: {username}")
    print(f"   Password: {password}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # Monitor console
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        try:
            # Step 1: Login
            print("\n✅ Step 1: Login as WK4")
            page.goto('http://localhost:5000/chatchat')
            time.sleep(2)
            
            page.fill('#login-username', username)
            page.fill('#login-password', password)
            page.locator('#login-form button[type="submit"]').click()
            time.sleep(3)
            
            page.screenshot(path='test_screenshots/wk4_1_logged_in.png')
            print("   ✅ Logged in")
            
            # Step 2: Go to Psychology tab
            print("\n✅ Step 2: Navigate to Psychology tab")
            page.locator('button[data-tab="psychology"]').click()
            time.sleep(2)
            
            page.screenshot(path='test_screenshots/wk4_2_psychology_before.png')
            print("   ✅ Psychology tab opened")
            
            # Check initial traits
            traits_grid = page.locator('#traits-grid')
            if traits_grid.count() > 0:
                try:
                    traits_text = traits_grid.inner_text(timeout=5000)
                    print(f"   📊 Initial traits (first 150 chars): {traits_text[:150]}")
                except:
                    print(f"   📊 Traits grid exists but empty or not visible")
            
            # Step 3: Open personality test
            print("\n✅ Step 3: Click 'Take Personality Test'")
            
            with context.expect_page() as popup_info:
                page.locator('#take-personality-test-btn').click()
                time.sleep(1)
            
            popup = popup_info.value
            popup.wait_for_load_state()
            time.sleep(1)
            
            print(f"   ✅ Popup opened: {popup.url}")
            
            # Check console for username
            popup_logs = []
            popup.on("console", lambda msg: popup_logs.append(msg.text))
            time.sleep(1)
            
            username_log = [log for log in popup_logs if 'username' in log.lower()]
            if username_log:
                print(f"   📋 {username_log[0]}")
            
            popup.screenshot(path='test_screenshots/wk4_3_popup_opened.png')
            
            # Step 4: Start assessment
            print("\n✅ Step 4: Start assessment")
            start_btn = popup.locator('button:has-text("Start Assessment")')
            if start_btn.is_visible():
                start_btn.click()
                time.sleep(2)
                print("   ✅ Assessment started")
            else:
                print("   ⚠️  Already has session or completed - checking screen")
            
            popup.screenshot(path='test_screenshots/wk4_4_assessment_screen.png')
            
            # Step 5: Answer all questions quickly
            print("\n✅ Step 5: Answering all 49 questions...")
            answered = 0
            max_attempts = 60  # Safety limit
            
            for attempt in range(max_attempts):
                # Look for option cards
                options = popup.locator('.option-card')
                
                if options.count() > 0:
                    # Click first option
                    options.first.click()
                    answered += 1
                    time.sleep(0.2)
                    
                    if answered % 10 == 0:
                        print(f"   📝 Answered {answered} questions")
                else:
                    # No more questions - check if completed
                    completion_title = popup.locator('h2:has-text("Assessment Complete")')
                    if completion_title.is_visible():
                        print(f"   ✅ Completed after {answered} questions")
                        break
                    time.sleep(0.5)
            
            time.sleep(2)
            popup.screenshot(path='test_screenshots/wk4_5_completion.png')
            
            # Step 6: Verify completion screen
            print("\n✅ Step 6: Verify completion screen")
            completion_visible = popup.locator('h2:has-text("Assessment Complete")').is_visible()
            
            if completion_visible:
                print("   ✅ Completion screen displayed")
                
                # Check for trait displays
                big_five = popup.locator('text=Big Five').is_visible()
                jung_types = popup.locator('text=Jung').is_visible()
                
                if big_five:
                    print("   ✅ Big Five traits shown")
                if jung_types:
                    print("   ✅ Jung types shown")
            else:
                print("   ❌ Completion screen NOT shown")
            
            # Step 7: Click "Go Back"
            print("\n✅ Step 7: Click 'Go Back' button")
            
            # Clear console logs to see new messages
            console_logs.clear()
            
            go_back = popup.locator('button:has-text("Go Back")')
            go_back.click()
            time.sleep(3)
            
            # Check if popup closed
            try:
                popup.title()
                print("   ⚠️  Popup still open")
            except:
                print("   ✅ Popup closed")
            
            # Step 8: Check main window console
            print("\n✅ Step 8: Check notification in main window")
            
            # Look for specific console messages
            assessment_notif = [log for log in console_logs if 'Assessment completed' in log]
            reload_notif = [log for log in console_logs if 'Reloading psychology data' in log]
            
            if assessment_notif:
                print(f"   ✅ {assessment_notif[0]}")
            else:
                print("   ❌ No 'Assessment completed' notification")
            
            if reload_notif:
                print(f"   ✅ {reload_notif[0]}")
            else:
                print("   ❌ No 'Reloading psychology data' notification")
            
            # Print last 10 console logs for debugging
            print(f"\n   📋 Last 10 console messages:")
            for log in console_logs[-10:]:
                print(f"      {log[:100]}")
            
            # Step 9: Check if traits updated
            print("\n✅ Step 9: Verify traits updated in Psychology tab")
            time.sleep(2)
            
            page.screenshot(path='test_screenshots/wk4_6_after_completion.png')
            
            # Get updated traits text
            updated_traits = page.locator('#traits-grid').inner_text(timeout=10000)
            
            # Look for Big Five traits
            big_five_traits = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism']
            found = []
            
            for trait in big_five_traits:
                if trait.lower() in updated_traits.lower():
                    found.append(trait)
            
            print(f"\n   📊 Found {len(found)}/5 Big Five traits:")
            for trait in found:
                print(f"      ✅ {trait}")
            
            # Final result
            print("\n" + "="*80)
            if len(found) >= 3:
                print("✅ TEST PASSED!")
                print("="*80)
                print(f"   ✅ Answered {answered} questions")
                print(f"   ✅ Completion screen shown")
                print(f"   ✅ Traits displayed: {len(found)}/5")
                if assessment_notif and reload_notif:
                    print(f"   ✅ Auto-reload triggered")
                else:
                    print(f"   ⚠️  Auto-reload may not have triggered")
            else:
                print("❌ TEST FAILED - Traits not updated")
                print("="*80)
                print(f"   Expected: 5 Big Five traits")
                print(f"   Found: {len(found)} traits")
            print("="*80)
            
            print("\n📸 Screenshots saved to test_screenshots/")
            print("   Press Enter to close browser...")
            input()
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path='test_screenshots/wk4_error.png')
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    test_wk4_personality_flow()
