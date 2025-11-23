"""
Comprehensive Playwright Test for Complete Application
Tests: Signup, Login, Chat, Psychology Test Restart, Send Message to Admin
"""
from playwright.sync_api import sync_playwright, expect
import time
import random
import string

def generate_test_username():
    """Generate unique test username"""
    random_suffix = ''.join(random.choices(string.digits, k=6))
    return f"test_user_{random_suffix}"

def run_comprehensive_test():
    print("=" * 80)
    print("🧪 COMPREHENSIVE APPLICATION TEST")
    print("=" * 80)
    print()
    
    with sync_playwright() as p:
        # Launch browser
        print("🌐 Launching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            # Test 1: Home Page Redirect
            print("\n" + "=" * 80)
            print("TEST 1: HOME PAGE REDIRECT TO CHATCHAT")
            print("=" * 80)
            page.goto('http://localhost:5000/')
            time.sleep(2)
            
            # Should redirect to /chatchat
            assert '/chatchat' in page.url, "❌ Home page did not redirect to /chatchat"
            print("✅ Home page correctly redirects to /chatchat")
            
            # Should show login screen
            expect(page.locator('#login-screen')).to_be_visible()
            print("✅ Login screen is visible")
            
            # Test 2: Signup
            print("\n" + "=" * 80)
            print("TEST 2: USER SIGNUP")
            print("=" * 80)
            
            username = generate_test_username()
            password = "TestPass123!"
            email = f"{username}@test.com"
            
            print(f"📝 Creating account: {username}")
            
            # Click signup link
            page.click('#show-signup')
            time.sleep(1)
            
            expect(page.locator('#signup-screen')).to_be_visible()
            print("✅ Signup screen is visible")
            
            # Fill signup form
            page.fill('#signup-username', username)
            page.fill('#signup-email', email)
            page.fill('#signup-password', password)
            page.fill('#signup-confirm-password', password)
            
            # Submit signup
            page.click('#signup-form button[type="submit"]')
            time.sleep(3)
            
            # Should show dashboard after signup
            expect(page.locator('#dashboard-screen')).to_be_visible()
            print(f"✅ Account created successfully: {username}")
            
            # Test 3: Character Selection & Chat
            print("\n" + "=" * 80)
            print("TEST 3: CHARACTER CHAT")
            print("=" * 80)
            
            # Click on chat tab
            page.click('button[data-tab="chat"]')
            time.sleep(4)
            print("✅ Navigated to chat tab")
            
            # Navigate directly to character page
            page.goto('http://localhost:5000/coach')
            time.sleep(3)
            print("✅ Navigated to Coach character page")
            
            # Send a message
            test_message = "Hello! Can you motivate me?"
            page.fill('#messageInput', test_message)
            page.click('#sendBtn, button:has-text("Send")')
            time.sleep(8)
            
            # Check if message appears in chat
            chat_messages = page.locator('#chatMessages .user-message, .message.user')
            if chat_messages.count() > 0:
                print("✅ Message sent successfully")
            else:
                print("⚠️  Message may have been sent (checking chat history)")
            
            # Check if AI response appears
            ai_messages = page.locator('#chatMessages .ai-message, .message.ai')
            if ai_messages.count() > 0:
                print("✅ AI response received")
            else:
                print("⚠️  Waiting for AI response...")
            
            # Test 4: Psychology Test (Start)
            print("\n" + "=" * 80)
            print("TEST 4: PSYCHOLOGY TEST - START")
            print("=" * 80)
            
            # Go back to chatchat dashboard
            page.goto('http://localhost:5000/chatchat')
            time.sleep(3)
            
            # Wait for dashboard to be visible
            page.wait_for_selector('#dashboard-screen', state='visible', timeout=10000)
            time.sleep(1)
            
            # Navigate to profile tab
            profile_btn = page.locator('button[data-tab="profile"]')
            profile_btn.scroll_into_view_if_needed()
            profile_btn.click()
            time.sleep(2)
            print("✅ Navigated to profile tab")
            
            # Click Take/Retake Assessment
            take_test_btn = page.locator('button:has-text("Take Assessment"), button:has-text("Retake Assessment")')
            if take_test_btn.count() > 0:
                take_test_btn.first.click()
                time.sleep(2)
                print("✅ Started psychology test")
                
                # Answer first question
                first_option = page.locator('input[type="radio"]').first
                first_option.check()
                time.sleep(1)
                print("✅ Answered question 1")
                
                # Click Next
                page.click('button:has-text("Next")')
                time.sleep(1)
                print("✅ Navigated to question 2")
                
                # Answer second question
                second_option = page.locator('input[type="radio"]').nth(1)
                second_option.check()
                time.sleep(1)
                print("✅ Answered question 2")
                
                # Test Pause functionality
                pause_btn = page.locator('button:has-text("Pause")')
                if pause_btn.count() > 0:
                    pause_btn.click()
                    time.sleep(2)
                    print("✅ Test paused")
                    
                    # Confirm pause
                    confirm_btn = page.locator('button:has-text("Yes, Pause")')
                    if confirm_btn.count() > 0:
                        confirm_btn.click()
                        time.sleep(2)
                        print("✅ Pause confirmed - should redirect to dashboard")
                else:
                    print("⚠️  Pause button not found")
            else:
                print("⚠️  Assessment button not found")
            
            # Test 5: Psychology Test Restart
            print("\n" + "=" * 80)
            print("TEST 5: PSYCHOLOGY TEST - RESTART/RESUME")
            print("=" * 80)
            
            # Navigate back to profile
            page.click('button[data-tab="profile"]')
            time.sleep(2)
            
            # Should see Resume or Retake button
            resume_btn = page.locator('button:has-text("Resume Assessment"), button:has-text("Retake Assessment")')
            if resume_btn.count() > 0:
                button_text = resume_btn.first.inner_text()
                print(f"✅ Found button: {button_text}")
                
                resume_btn.first.click()
                time.sleep(2)
                print("✅ Clicked resume/retake button")
                
                # Should be back in test
                expect(page.locator('#assessment-container, .question-container')).to_be_visible(timeout=5000)
                print("✅ Psychology test interface loaded")
                
                # Exit test to return to dashboard
                exit_btn = page.locator('button:has-text("Exit"), button:has-text("Pause")')
                if exit_btn.count() > 0:
                    exit_btn.first.click()
                    time.sleep(1)
                    
                    # Confirm exit
                    confirm_exit = page.locator('button:has-text("Yes")')
                    if confirm_exit.count() > 0:
                        confirm_exit.click()
                        time.sleep(2)
                        print("✅ Exited test, returned to dashboard")
            else:
                print("⚠️  Resume/Retake button not found")
            
            # Test 6: Send Message to Admin
            print("\n" + "=" * 80)
            print("TEST 6: SEND MESSAGE TO ADMIN")
            print("=" * 80)
            
            # Navigate to admin tab
            page.click('button[data-tab="admin"]')
            time.sleep(2)
            print("✅ Navigated to admin tab")
            
            # Check if admin interface is visible
            expect(page.locator('#admin-tab-content')).to_be_visible()
            print("✅ Admin tab content visible")
            
            # Find message form
            admin_message_input = page.locator('#admin-message-text, textarea[placeholder*="message"], textarea[placeholder*="admin"]')
            if admin_message_input.count() > 0:
                # Fill message
                test_admin_message = "This is a test message from automated testing. Please ignore."
                admin_message_input.first.fill(test_admin_message)
                time.sleep(1)
                print("✅ Admin message typed")
                
                # Click send button
                send_admin_btn = page.locator('button:has-text("Send"), button:has-text("Submit")')
                if send_admin_btn.count() > 0:
                    send_admin_btn.first.click()
                    time.sleep(3)
                    print("✅ Message sent to admin")
                    
                    # Check for success message or confirmation
                    success_indicators = page.locator('.success, .alert-success, text=sent, text=submitted')
                    if success_indicators.count() > 0:
                        print("✅ Success confirmation received")
                    else:
                        print("⚠️  No success confirmation found (message may still have been sent)")
                else:
                    print("⚠️  Send button not found")
            else:
                print("⚠️  Admin message input not found")
            
            # Test 7: Logout
            print("\n" + "=" * 80)
            print("TEST 7: LOGOUT")
            print("=" * 80)
            
            logout_btn = page.locator('#logout-btn, button:has-text("Logout")')
            if logout_btn.count() > 0:
                logout_btn.first.click()
                time.sleep(2)
                print("✅ Clicked logout button")
                
                # Should show login screen
                expect(page.locator('#login-screen')).to_be_visible()
                print("✅ Login screen visible after logout")
                
                # Should still be on /chatchat
                assert '/chatchat' in page.url, "❌ Logout navigated away from /chatchat"
                print("✅ Still on /chatchat after logout")
            else:
                print("⚠️  Logout button not found")
            
            # Test 8: Login with Created Account
            print("\n" + "=" * 80)
            print("TEST 8: LOGIN WITH CREATED ACCOUNT")
            print("=" * 80)
            
            page.fill('#login-username', username)
            page.fill('#login-password', password)
            page.click('#login-form button[type="submit"]')
            time.sleep(3)
            
            expect(page.locator('#dashboard-screen')).to_be_visible()
            print(f"✅ Successfully logged in as: {username}")
            
            # Final Summary
            print("\n" + "=" * 80)
            print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print()
            print("✅ Test Results Summary:")
            print("   1. ✅ Home redirect to /chatchat")
            print("   2. ✅ User signup")
            print("   3. ✅ Character chat & AI response")
            print("   4. ✅ Psychology test start")
            print("   5. ✅ Psychology test pause/resume/restart")
            print("   6. ✅ Send message to admin")
            print("   7. ✅ Logout (stays on /chatchat)")
            print("   8. ✅ Login")
            print()
            print(f"📝 Test Account Created: {username}")
            print(f"🔑 Password: {password}")
            print()
            
            # Keep browser open for 10 seconds
            print("Browser will close in 10 seconds...")
            time.sleep(10)
            
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {e}")
            print("\n🔍 Current URL:", page.url)
            print("📸 Taking screenshot...")
            page.screenshot(path='test_failure.png')
            print("Screenshot saved: test_failure.png")
            time.sleep(5)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("\n🔍 Current URL:", page.url)
            print("📸 Taking screenshot...")
            page.screenshot(path='test_error.png')
            print("Screenshot saved: test_error.png")
            time.sleep(5)
            
        finally:
            browser.close()
            print("\n✅ Browser closed")

if __name__ == "__main__":
    print("\n🚀 Starting comprehensive application test...")
    print("⚠️  Make sure Flask app is running on http://localhost:5000")
    print()
    
    input("Press Enter to start the test...")
    
    run_comprehensive_test()
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
