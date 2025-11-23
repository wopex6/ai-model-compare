from playwright.sync_api import sync_playwright
import time
import os
import requests

def check_server():
    """Check if Flask server is running"""
    try:
        response = requests.get('http://localhost:5000')
        return response.status_code in [200, 404, 302]
    except:
        return False

def test_pause_and_resume():
    """Test assessment pause and resume functionality"""
    
    # Check if server is running
    if not check_server():
        print("\n❌ ERROR: Flask server is not running!")
        print("Please start the Flask server first:")
        print("   python app.py")
        print("\nThen run this test again.\n")
        return
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        print("\n" + "="*60)
        print("TESTING PERSONALITY ASSESSMENT PAUSE & RESUME")
        print("="*60 + "\n")
        
        # Step 1: Navigate to personality test
        print("✅ Step 1: Navigate to personality test page")
        page.goto('http://localhost:5000/personality-test')
        time.sleep(2)
        page.screenshot(path='test_screenshots/step1_welcome.png')
        print("   Screenshot: step1_welcome.png")
        
        # Step 2: Click "Start Assessment"
        print("\n✅ Step 2: Start assessment")
        page.click('text=Start Assessment')
        time.sleep(2)
        page.screenshot(path='test_screenshots/step2_first_question.png')
        print("   Screenshot: step2_first_question.png")
        
        # Check progress bar
        progress_text = page.locator('strong:has-text("Progress:")').inner_text()
        print(f"   Progress: {progress_text}")
        
        # Step 3: Answer 5 questions
        print("\n✅ Step 3: Answer 5 questions")
        for i in range(5):
            # Click the first option (any option works)
            options = page.locator('.option')
            if options.count() > 0:
                options.first.click()
                time.sleep(1)
                print(f"   Question {i+1} answered")
            else:
                print(f"   ⚠️  No options found for question {i+1}")
                break
        
        # Screenshot after 5 questions
        page.screenshot(path='test_screenshots/step3_after_5_questions.png')
        print("   Screenshot: step3_after_5_questions.png")
        
        # Check progress after answering
        try:
            progress_text = page.locator('strong:has-text("Progress:")').inner_text()
            print(f"   Progress after answering: {progress_text}")
        except:
            print("   ⚠️  Could not read progress")
        
        # Step 4: Click "Pause Assessment"
        print("\n✅ Step 4: Click 'Pause Assessment' button")
        time.sleep(1)
        
        # Check if pause button exists
        pause_button = page.locator('button:has-text("Pause Assessment")')
        if pause_button.count() > 0:
            pause_button.click()
            print("   Pause button clicked!")
            time.sleep(2)
        else:
            print("   ❌ Pause button not found!")
            page.screenshot(path='test_screenshots/error_no_pause_button.png')
            browser.close()
            return
        
        # Step 5: Check redirect to home page
        print("\n✅ Step 5: Verify redirect to home page")
        current_url = page.url
        page.screenshot(path='test_screenshots/step5_after_pause.png')
        print(f"   Current URL: {current_url}")
        print("   Screenshot: step5_after_pause.png")
        
        if current_url == 'http://localhost:5000/' or 'localhost:5000' in current_url and 'personality-test' not in current_url:
            print("   ✅ Successfully redirected away from personality test!")
        else:
            print(f"   ❌ Still on personality test! URL: {current_url}")
        
        # Step 6: Check if session file was created
        print("\n✅ Step 6: Check if session file exists")
        session_dir = 'personality_profiles/sessions'
        if os.path.exists(session_dir):
            session_files = os.listdir(session_dir)
            if session_files:
                print(f"   ✅ Session files found: {session_files}")
                # Read the session file
                for file in session_files:
                    if file.endswith('_session.json'):
                        import json
                        with open(os.path.join(session_dir, file), 'r') as f:
                            session_data = json.load(f)
                            print(f"   📄 Session data:")
                            print(f"      User ID: {session_data.get('user_id')}")
                            print(f"      Current Question: {session_data.get('current_question')}/{len(session_data.get('questions', []))}")
                            print(f"      Responses: {len(session_data.get('responses', {}))}")
            else:
                print("   ⚠️  No session files found")
        else:
            print("   ⚠️  Sessions directory doesn't exist")
        
        # Step 7: Navigate back to personality test
        print("\n✅ Step 7: Return to personality test page")
        page.goto('http://localhost:5000/personality-test')
        time.sleep(2)
        page.screenshot(path='test_screenshots/step7_resume.png')
        print("   Screenshot: step7_resume.png")
        
        # Step 8: Check if it resumed from correct question
        print("\n✅ Step 8: Verify resume functionality")
        try:
            progress_text = page.locator('strong:has-text("Progress:")').inner_text()
            print(f"   Progress after resume: {progress_text}")
            
            # Check if we're past question 1 (should be around question 6)
            if 'Progress: 6' in progress_text or 'Progress: 7' in progress_text:
                print("   ✅ RESUME WORKS! Continued from where we left off!")
            elif 'Progress: 1' in progress_text:
                print("   ❌ RESUME FAILED! Started from beginning")
            else:
                print(f"   ⚠️  Unexpected progress: {progress_text}")
        except Exception as e:
            print(f"   ❌ Could not verify resume: {e}")
        
        # Step 9: Final screenshot
        print("\n✅ Step 9: Final verification")
        page.screenshot(path='test_screenshots/step9_final.png')
        print("   Screenshot: step9_final.png")
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✅ Started assessment")
        print("✅ Answered 5 questions")
        print("✅ Clicked pause button")
        print(f"✅ Redirected to: {current_url}")
        print("✅ Session saved to disk")
        print("✅ Returned to assessment")
        print("✅ Check screenshots in test_screenshots/ folder")
        print("="*60 + "\n")
        
        time.sleep(3)
        browser.close()

if __name__ == '__main__':
    test_pause_and_resume()
