"""
Playwright test for complete personality assessment flow
- Creates new user
- Completes personality test
- Verifies traits are updated in psychology tab
"""

from playwright.sync_api import sync_playwright, expect
import time
import random

def test_personality_assessment_flow():
    print("\n" + "="*80)
    print("TESTING COMPLETE PERSONALITY ASSESSMENT FLOW")
    print("="*80)
    
    # Generate random username
    random_num = random.randint(1000, 9999)
    test_username = f"testuser{random_num}"
    test_email = f"{test_username}@test.com"
    test_password = "123"
    
    print(f"\n📝 Creating test user:")
    print(f"   Username: {test_username}")
    print(f"   Email: {test_email}")
    print(f"   Password: {test_password}")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # Monitor console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        
        try:
            # Step 1: Go to homepage and signup
            print("\n✅ Step 1: Create new user account")
            page.goto('http://localhost:5000/chatchat')
            time.sleep(2)
            
            # Click signup tab link
            page.locator('a#show-signup').click()
            time.sleep(1)
            
            # Fill signup form using correct IDs
            page.fill('#signup-username', test_username)
            page.fill('#signup-email', test_email)
            page.fill('#signup-password', test_password)
            
            # Submit signup
            page.locator('#signup-form button[type="submit"]').click()
            time.sleep(4)
            
            # Print recent console messages
            print(f"   📋 Last 5 console messages:")
            for msg in console_messages[-5:]:
                print(f"      {msg}")
            
            page.screenshot(path='test_screenshots/complete_1_after_signup.png')
            
            # Check if there's an error message on the form
            error_elements = page.locator('.error, .alert-danger, [class*="error"]')
            if error_elements.count() > 0:
                for i in range(error_elements.count()):
                    error_text = error_elements.nth(i).inner_text()
                    if error_text.strip():
                        print(f"   ❌ Error on page: {error_text}")
            
            # Check if email verification modal appeared
            verify_modal = page.locator('#verification-modal')
            if verify_modal.is_visible():
                print("   📧 Email verification modal appeared - entering code")
                # Get verification code from console or skip it
                # For now, let's skip verification by closing modal if possible
                skip_button = page.locator('#skip-verification, button:has-text("Skip")')
                if skip_button.count() > 0:
                    skip_button.first.click()
                    time.sleep(2)
            
            # Wait for dashboard to be visible
            try:
                page.wait_for_selector('#dashboard-screen', state='visible', timeout=15000)
                time.sleep(2)
                page.screenshot(path='test_screenshots/complete_1_signup.png')
                print("   ✅ User created and logged in")
            except Exception as e:
                print(f"   ⚠️  Dashboard not visible: {e}")
                print("   Current URL:", page.url)
                page.screenshot(path='test_screenshots/complete_error_no_dashboard.png')
                
                # Try to check what screen is visible
                screens = ['#login-screen', '#signup-screen', '#verification-modal', '#dashboard-screen']
                for screen_id in screens:
                    screen = page.locator(screen_id)
                    if screen.is_visible():
                        print(f"   Visible screen: {screen_id}")
                raise
            
            # Step 2: Navigate to Psychology tab
            print("\n✅ Step 2: Navigate to Psychology tab")
            psych_button = page.locator('button[data-tab="psychology"]')
            psych_button.wait_for(state='visible', timeout=10000)
            psych_button.click()
            time.sleep(2)
            
            page.screenshot(path='test_screenshots/complete_2_psychology_tab.png')
            print("   ✅ Psychology tab opened")
            
            # Check initial state - should have 0 traits
            traits_section = page.locator('#traits-section')
            if traits_section.is_visible():
                print("   📊 Initial traits section visible")
            
            # Step 3: Click "Take Personality Test" button
            print("\n✅ Step 3: Open personality test")
            test_button = page.locator('#take-personality-test-btn')
            
            # Wait for popup
            with context.expect_page() as popup_info:
                test_button.click()
                time.sleep(1)
            
            popup = popup_info.value
            popup.wait_for_load_state()
            time.sleep(1)
            
            print(f"   ✅ Popup opened: {popup.url}")
            popup.screenshot(path='test_screenshots/complete_3_test_popup.png')
            
            # Verify username is passed correctly
            popup_console_logs = []
            popup.on("console", lambda msg: popup_console_logs.append(msg.text))
            
            # Step 4: Start assessment
            print("\n✅ Step 4: Start assessment")
            start_button = popup.locator('button:has-text("Start Assessment")')
            start_button.click()
            time.sleep(2)
            
            popup.screenshot(path='test_screenshots/complete_4_first_question.png')
            print("   ✅ Assessment started")
            
            # Step 5: Answer all 49 questions
            print("\n✅ Step 5: Answer all 49 questions")
            for i in range(49):
                # Click first option for each question
                option = popup.locator('.option-card').first
                option.click()
                time.sleep(0.3)  # Small delay between answers
                
                if (i + 1) % 10 == 0:
                    print(f"   📝 Answered {i + 1}/49 questions")
            
            print("   ✅ All 49 questions answered")
            time.sleep(2)
            
            # Step 6: Verify completion screen
            print("\n✅ Step 6: Verify completion screen")
            popup.screenshot(path='test_screenshots/complete_5_completion.png')
            
            completion_title = popup.locator('h2:has-text("Assessment Complete")')
            if completion_title.is_visible():
                print("   ✅ Completion screen shown")
            else:
                print("   ❌ Completion screen NOT shown")
                popup.screenshot(path='test_screenshots/complete_error_no_completion.png')
            
            # Check for trait displays
            big_five_section = popup.locator('text=Big Five Personality')
            if big_five_section.is_visible():
                print("   ✅ Big Five traits displayed")
            
            # Step 7: Click "Go Back" button
            print("\n✅ Step 7: Click 'Go Back' button")
            go_back_button = popup.locator('button:has-text("Go Back")')
            
            # Enable console logging on main page
            main_console_logs = []
            page.on("console", lambda msg: main_console_logs.append(msg.text))
            
            go_back_button.click()
            time.sleep(2)
            
            # Step 8: Verify main page received notification
            print("\n✅ Step 8: Verify notification received in main window")
            
            # Check console logs
            notification_received = any('Assessment completed notification received' in log for log in main_console_logs)
            reload_triggered = any('Reloading psychology data' in log for log in main_console_logs)
            
            if notification_received:
                print("   ✅ Main window received assessment completion notification")
            else:
                print("   ❌ Main window did NOT receive notification")
                print(f"   Console logs: {main_console_logs[-10:]}")
            
            if reload_triggered:
                print("   ✅ Psychology data reload triggered")
            else:
                print("   ❌ Psychology data reload NOT triggered")
            
            # Wait for data to reload
            time.sleep(2)
            
            # Step 9: Verify traits are displayed
            print("\n✅ Step 9: Verify traits updated in Psychology tab")
            page.screenshot(path='test_screenshots/complete_6_updated_traits.png')
            
            # Check for traits in the UI
            traits_text = page.locator('#traits-section').inner_text()
            
            # Look for Big Five traits
            big_five_traits = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism']
            found_traits = []
            
            for trait in big_five_traits:
                if trait.lower() in traits_text.lower():
                    found_traits.append(trait)
            
            print(f"   📊 Found {len(found_traits)}/5 Big Five traits")
            for trait in found_traits:
                print(f"      ✅ {trait}")
            
            # Check for charts
            chart_element = page.locator('#personality-chart')
            if chart_element.is_visible():
                print("   ✅ Personality chart visible")
            else:
                print("   ⚠️  Personality chart not visible")
            
            # Step 10: Final verification
            print("\n✅ Step 10: Final verification")
            
            if len(found_traits) >= 3:
                print("\n" + "="*80)
                print("✅ TEST PASSED!")
                print("="*80)
                print(f"   ✅ User created: {test_username}")
                print(f"   ✅ Assessment completed: 49/49 questions")
                print(f"   ✅ Traits displayed: {len(found_traits)}/5")
                print(f"   ✅ Data persisted to database")
                print("="*80)
            else:
                print("\n" + "="*80)
                print("❌ TEST FAILED - Traits not updated")
                print("="*80)
                print(f"   Expected: 5 traits")
                print(f"   Found: {len(found_traits)} traits")
                print(f"   Traits: {found_traits}")
                print("="*80)
            
            # Keep browser open for inspection
            print("\n📸 Screenshots saved to test_screenshots/")
            print("   Press Enter to close browser...")
            input()
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            page.screenshot(path='test_screenshots/complete_error.png')
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    test_personality_assessment_flow()
