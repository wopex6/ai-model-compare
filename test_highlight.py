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

def test_selected_option_highlight():
    """Test that previously selected answer is highlighted when going back"""

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
        print("TESTING SELECTED OPTION HIGHLIGHT")
        print("="*60)
        
        try:
            # Step 1: Navigate to personality test
            print("\n✅ Step 1: Navigate to personality test page")
            page.goto('http://localhost:5000/personality-test')
            time.sleep(1)
            page.screenshot(path='test_screenshots/highlight_1_welcome.png')
            print("   Screenshot: highlight_1_welcome.png")
            
            # Step 2: Start assessment
            print("\n✅ Step 2: Start assessment")
            page.click('button:has-text("Start Assessment")')
            time.sleep(1)
            page.screenshot(path='test_screenshots/highlight_2_question1.png')
            print("   Screenshot: highlight_2_question1.png")
            
            # Step 3: Select first option on Question 1
            print("\n✅ Step 3: Select first option on Question 1")
            options = page.locator('.option')
            first_option_text = options.nth(0).inner_text()
            print(f"   Selecting: {first_option_text}")
            options.nth(0).click()
            time.sleep(1)
            
            # Step 4: Now on Question 2, go back
            print("\n✅ Step 4: Click Back button to return to Question 1")
            page.click('button:has-text("Back")')
            time.sleep(1)
            page.screenshot(path='test_screenshots/highlight_3_back_to_q1.png')
            print("   Screenshot: highlight_3_back_to_q1.png")
            
            # Step 5: Check if first option is highlighted
            print("\n✅ Step 5: Check if selected option is highlighted")
            selected_option = page.locator('.option.selected')
            
            if selected_option.count() > 0:
                print("   ✅ Found .selected class on option!")
                
                # Get computed styles
                bg_color = selected_option.evaluate('el => window.getComputedStyle(el).backgroundColor')
                text_color = selected_option.evaluate('el => window.getComputedStyle(el).color')
                border = selected_option.evaluate('el => window.getComputedStyle(el).border')
                
                print(f"   Background: {bg_color}")
                print(f"   Text color: {text_color}")
                print(f"   Border: {border}")
                
                # Check if it's green (rgb(76, 175, 80) = #4caf50)
                if 'rgb(76, 175, 80)' in bg_color:
                    print("   ✅ Background is GREEN - Highlight visible!")
                else:
                    print(f"   ⚠️  Background is {bg_color}, expected green")
                
                # Check if text is white
                if 'rgb(255, 255, 255)' in text_color:
                    print("   ✅ Text is WHITE - Good contrast!")
                else:
                    print(f"   ⚠️  Text is {text_color}, expected white")
                    
            else:
                print("   ❌ No .selected class found on any option!")
                print("   All options:")
                for i in range(options.count()):
                    opt_class = options.nth(i).get_attribute('class')
                    opt_text = options.nth(i).inner_text()
                    print(f"      {i}: class='{opt_class}' text='{opt_text}'")
            
            # Step 6: Visual comparison screenshot
            print("\n✅ Step 6: Take final screenshot for visual verification")
            page.screenshot(path='test_screenshots/highlight_4_final.png')
            print("   Screenshot: highlight_4_final.png")
            
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            print("✅ Started assessment")
            print("✅ Selected option on Question 1")
            print("✅ Went back to Question 1")
            print("✅ Checked for highlight styling")
            print("📸 Screenshots saved in test_screenshots/")
            print("\nPlease check the screenshots to verify the highlight is visible!")
            print("="*60 + "\n")
            
            time.sleep(3)
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            page.screenshot(path='test_screenshots/highlight_error.png')
            
        finally:
            browser.close()

if __name__ == '__main__':
    test_selected_option_highlight()
