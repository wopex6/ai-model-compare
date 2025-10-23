"""
Comprehensive test script for all messaging features including video playback
"""
from playwright.sync_api import sync_playwright, expect
import time

def test_messaging_features():
    with sync_playwright() as p:
        print("🚀 Starting comprehensive messaging feature tests...")
        
        # Launch browser
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to app
            print("\n📍 Step 1: Navigate to application...")
            page.goto('http://localhost:5000/chatchat')
            page.wait_for_load_state('networkidle')
            
            # Check if already logged in or need to login
            print("\n📍 Step 2: Check authentication...")
            time.sleep(2)
            
            # Try to find login form
            login_form = page.locator('#login-username')
            if login_form.is_visible():
                print("   ➜ Not logged in, attempting login...")
                
                # Login with admin credentials
                page.fill('#login-username', 'administrator')
                page.fill('#login-password', 'admin')
                page.click('button[type="submit"]')
                
                print("   ✅ Login submitted")
                page.wait_for_load_state('networkidle')
                time.sleep(2)
            else:
                print("   ✅ Already logged in")
            
            # Navigate to Contact Admin
            print("\n📍 Step 3: Navigate to Contact Admin...")
            admin_chat_btn = page.locator('#admin-chat-tab-btn')
            if admin_chat_btn.is_visible():
                admin_chat_btn.click()
                print("   ✅ Clicked Contact Admin tab")
                time.sleep(2)
            
            # TEST 1: Send a text message
            print("\n📍 TEST 1: Send text message...")
            message_input = page.locator('#admin-chat-input')
            message_input.fill('Test message from automated test')
            page.click('#send-admin-message-btn')
            print("   ✅ Text message sent")
            time.sleep(2)
            
            # TEST 2: Test reply feature
            print("\n📍 TEST 2: Test reply feature...")
            reply_buttons = page.locator('button[title="Reply to this message"]')
            if reply_buttons.count() > 0:
                reply_buttons.first.click()
                print("   ✅ Clicked reply button")
                time.sleep(1)
                
                # Check if reply indicator is visible
                reply_indicator = page.locator('#admin-chat-reply-indicator')
                if reply_indicator.is_visible():
                    print("   ✅ Reply indicator visible")
                    
                    # Send reply
                    message_input.fill('This is a reply to the previous message')
                    page.click('#send-admin-message-btn')
                    print("   ✅ Reply sent")
                    time.sleep(2)
                else:
                    print("   ⚠️  Reply indicator not visible")
            else:
                print("   ⚠️  No messages to reply to")
            
            # TEST 3: Test delete message
            print("\n📍 TEST 3: Test delete message...")
            delete_buttons = page.locator('button[title="Delete message"]')
            if delete_buttons.count() > 0:
                initial_count = delete_buttons.count()
                print(f"   ➜ Found {initial_count} messages")
                
                # Click first delete button
                page.on("dialog", lambda dialog: dialog.accept())  # Auto-accept confirmation
                delete_buttons.first.click()
                print("   ✅ Clicked delete button")
                time.sleep(2)
                
                # Check if message was deleted
                new_count = page.locator('button[title="Delete message"]').count()
                if new_count < initial_count:
                    print(f"   ✅ Message deleted (was {initial_count}, now {new_count})")
                else:
                    print(f"   ⚠️  Message not deleted (still {new_count})")
            else:
                print("   ⚠️  No messages to delete")
            
            # TEST 4: Upload and test video file
            print("\n📍 TEST 4: Test video upload and playback...")
            
            # Check for existing videos first
            videos = page.locator('video')
            if videos.count() > 0:
                print(f"   ➜ Found {videos.count()} video(s) in messages")
                
                # TEST 4a: Check video attributes
                first_video = videos.first
                preload_attr = first_video.get_attribute('preload')
                controls_attr = first_video.get_attribute('controls')
                print(f"   ➜ Video preload: {preload_attr}")
                print(f"   ➜ Video controls: {controls_attr}")
                
                if preload_attr == 'none':
                    print("   ✅ Video preload correctly set to 'none'")
                else:
                    print(f"   ⚠️  Video preload is '{preload_attr}', should be 'none'")
                
                # TEST 4b: Test video doesn't auto-play
                print("   ➜ Checking video doesn't auto-play...")
                time.sleep(3)
                is_paused = first_video.evaluate('video => video.paused')
                if is_paused:
                    print("   ✅ Video is paused (not auto-playing)")
                else:
                    print("   ⚠️  Video is playing (should not auto-play)")
                
                # TEST 4c: Play video and check it doesn't reset
                print("   ➜ Playing video manually...")
                first_video.evaluate('video => video.play()')
                time.sleep(2)
                
                current_time_1 = first_video.evaluate('video => video.currentTime')
                print(f"   ➜ Video time: {current_time_1:.2f}s")
                
                # Wait for auto-refresh (5 seconds)
                print("   ➜ Waiting for auto-refresh (5 seconds)...")
                time.sleep(5)
                
                # Check if video is still playing and hasn't reset
                videos_after = page.locator('video')
                if videos_after.count() > 0:
                    current_time_2 = videos_after.first.evaluate('video => video.currentTime')
                    print(f"   ➜ Video time after refresh: {current_time_2:.2f}s")
                    
                    if current_time_2 > current_time_1:
                        print("   ✅ Video continued playing (not interrupted)")
                    elif current_time_2 > 0:
                        print("   ⚠️  Video time preserved but not playing")
                    else:
                        print("   ❌ Video reset to 0 (playback interrupted)")
                else:
                    print("   ❌ Video element disappeared after refresh")
                    
            else:
                print("   ⚠️  No videos found in messages")
                print("   ➜ You can manually upload a video to test playback")
            
            # TEST 5: Test scroll behavior
            print("\n📍 TEST 5: Test scroll behavior...")
            messages_container = page.locator('#admin-chat-messages')
            
            # Scroll to top
            messages_container.evaluate('el => el.scrollTop = 0')
            scroll_pos_1 = messages_container.evaluate('el => el.scrollTop')
            print(f"   ➜ Scrolled to top: {scroll_pos_1}")
            
            # Wait for auto-refresh
            print("   ➜ Waiting for auto-refresh (5 seconds)...")
            time.sleep(5)
            
            # Check scroll position
            scroll_pos_2 = messages_container.evaluate('el => el.scrollTop')
            print(f"   ➜ Scroll position after refresh: {scroll_pos_2}")
            
            if scroll_pos_2 == scroll_pos_1:
                print("   ✅ Scroll position preserved (no jumping)")
            else:
                print(f"   ❌ Scroll position changed (jumped by {scroll_pos_2 - scroll_pos_1}px)")
            
            # TEST 6: Check for notifications
            print("\n📍 TEST 6: Check notification system...")
            notification = page.locator('#message-notification')
            print(f"   ➜ Notification element exists: {notification.count() > 0}")
            
            if notification.count() > 0:
                is_visible = notification.is_visible()
                print(f"   ➜ Notification currently visible: {is_visible}")
            
            print("\n" + "="*60)
            print("✅ ALL TESTS COMPLETED!")
            print("="*60)
            
            # Keep browser open for manual inspection
            print("\n⏳ Browser will stay open for 30 seconds for manual inspection...")
            time.sleep(30)
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(10)
        finally:
            browser.close()
            print("\n✅ Browser closed")

if __name__ == '__main__':
    test_messaging_features()
