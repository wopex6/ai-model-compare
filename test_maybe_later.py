from playwright.sync_api import sync_playwright
import time

def test_maybe_later():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Go to personality test page
        print("1. Navigating to personality test page...")
        page.goto('http://localhost:5000/personality-test')
        time.sleep(2)
        
        # Take screenshot before clicking
        page.screenshot(path='test_screenshots/before_maybe_later.png')
        print("2. Screenshot taken: before_maybe_later.png")
        
        # Click Maybe Later button
        print("3. Clicking 'Maybe Later' button...")
        page.click('text=Maybe Later')
        time.sleep(2)
        
        # Take screenshot after clicking
        page.screenshot(path='test_screenshots/after_maybe_later.png')
        print("4. Screenshot taken: after_maybe_later.png")
        
        # Check current URL
        current_url = page.url
        print(f"5. Current URL: {current_url}")
        
        # Check page content
        page_title = page.title()
        print(f"6. Page title: {page_title}")
        
        time.sleep(2)
        browser.close()

if __name__ == '__main__':
    test_maybe_later()
