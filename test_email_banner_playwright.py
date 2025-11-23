"""
Test Email Verification Banner with Playwright
"""

from playwright.sync_api import sync_playwright
import time

def test_email_banner():
    """Test if masked email appears in verification banner"""
    
    with sync_playwright() as p:
        # Launch browser
        print("\n🌐 Launching browser...")
        browser = p.chromium.launch(headless=False)  # headless=False to see what's happening
        context = browser.new_context()
        page = context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"🖥️  Console: {msg.text}"))
        
        try:
            # Navigate to login page
            print("\n📍 Navigating to http://localhost:5000/chatchat")
            page.goto("http://localhost:5000/chatchat", timeout=10000)
            
            # Wait for page to load
            page.wait_for_selector("#login-form", timeout=5000)
            print("✅ Login page loaded")
            
            # Login with test user
            print("\n🔐 Logging in as 'Wai Tse'...")
            page.fill("#login-username", "Wai Tse")
            page.fill("#login-password", ".//")
            page.click("button[type='submit']")
            
            # Wait for dashboard to load
            print("\n⏳ Waiting for dashboard...")
            page.wait_for_selector("#dashboard-screen", timeout=10000)
            print("✅ Dashboard loaded")
            
            # Wait a bit for verification check to complete
            time.sleep(3)
            
            # Check if banner exists
            print("\n🔍 Checking for verification banner...")
            banner = page.query_selector("#email-verification-banner")
            
            if banner:
                is_visible = banner.is_visible()
                print(f"✅ Banner found! Visible: {is_visible}")
                
                if is_visible:
                    # Get banner text
                    banner_text_element = page.query_selector("#verification-banner-email")
                    
                    if banner_text_element:
                        banner_text = banner_text_element.inner_text()
                        print(f"\n📧 Banner text: {banner_text}")
                        
                        # Check if it contains masked email pattern (****) 
                        if "****" in banner_text:
                            print("✅ SUCCESS! Masked email is displaying in banner!")
                            print(f"   Full text: {banner_text}")
                        else:
                            print("❌ FAIL: No masked email pattern (****) found in banner")
                            print(f"   Banner shows: {banner_text}")
                    else:
                        print("❌ Banner email span element not found")
                else:
                    print("⚠️  Banner exists but is not visible (user might be verified)")
            else:
                print("❌ Banner element not found in DOM")
            
            # Get page screenshot
            print("\n📸 Taking screenshot...")
            page.screenshot(path="email_banner_test.png")
            print("✅ Screenshot saved as 'email_banner_test.png'")
            
            # Keep browser open for inspection
            print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            page.screenshot(path="email_banner_error.png")
            print("📸 Error screenshot saved")
        
        finally:
            # Cleanup
            print("\n🧹 Closing browser...")
            browser.close()
            print("✅ Test complete!")

if __name__ == "__main__":
    print("="*60)
    print("🧪 EMAIL VERIFICATION BANNER TEST")
    print("="*60)
    test_email_banner()
