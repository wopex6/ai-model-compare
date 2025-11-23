"""
Test Email Verification Banner - With Signup
"""

from playwright.sync_api import sync_playwright
import time
import random

def test_email_banner_with_signup():
    """Test email banner by creating a new unverified user"""
    
    # Generate random test user
    random_id = random.randint(1000, 9999)
    test_username = f"testuser{random_id}"
    test_email = f"test{random_id}@example.com"
    test_password = "TestPass123"
    
    with sync_playwright() as p:
        # Launch browser
        print("\n🌐 Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"🖥️  {msg.text}"))
        
        try:
            # Navigate to signup page
            print(f"\n📍 Navigating to http://localhost:5000/chatchat")
            page.goto("http://localhost:5000/chatchat", timeout=10000)
            
            # Wait for login page
            page.wait_for_selector("#login-form", timeout=5000)
            print("✅ Page loaded")
            
            # Click on signup link
            print("\n📝 Clicking 'Sign up here' link...")
            page.click("#show-signup")
            time.sleep(1)
            
            # Fill signup form
            print(f"\n✍️  Creating test user: {test_username}")
            print(f"   Email: {test_email}")
            page.wait_for_selector("#signup-form", timeout=5000)
            page.fill("#signup-username", test_username)
            page.fill("#signup-email", test_email)
            page.fill("#signup-password", test_password)
            page.fill("#signup-confirm-password", test_password)
            
            # Submit signup
            print("\n🚀 Submitting signup...")
            page.click("#signup-form button[type='submit']")
            
            # Wait for dashboard
            print("\n⏳ Waiting for dashboard after signup...")
            page.wait_for_selector("#dashboard-screen.active", timeout=10000)
            print("✅ Dashboard loaded!")
            
            # Wait for banner check to complete
            print("\n⏳ Waiting for email verification check...")
            time.sleep(5)
            
            # Check if banner exists and is visible
            print("\n🔍 Checking for verification banner...")
            banner = page.query_selector("#email-verification-banner")
            
            if banner:
                is_visible = banner.is_visible()
                print(f"✅ Banner element found! Visible: {is_visible}")
                
                if is_visible:
                    # Get banner text
                    banner_text_element = page.query_selector("#verification-banner-email")
                    
                    if banner_text_element:
                        banner_text = banner_text_element.inner_text()
                        print(f"\n📧 Banner text content:")
                        print(f"   '{banner_text}'")
                        
                        # Check for masked email pattern
                        if "****" in banner_text:
                            print("\n✅ SUCCESS! Masked email pattern found!")
                            
                            # Extract the masked email
                            import re
                            masked_match = re.search(r'\(([^)]+)\)', banner_text)
                            if masked_match:
                                masked_email = masked_match.group(1)
                                print(f"   Masked email: {masked_email}")
                                
                                # Verify format
                                if re.match(r'[a-z]{2}\*\*\*\*[a-z0-9]{2}@', masked_email):
                                    print("   ✅ Correct masking format: XX****XX@domain")
                                else:
                                    print("   ⚠️  Unusual masking format")
                        else:
                            print("\n❌ FAIL: No masked email (****) in banner text")
                            print("   Expected: Check your email (xx****xx@...) for code")
                            print(f"   Got: {banner_text}")
                    else:
                        print("❌ Banner email span (#verification-banner-email) not found")
                        
                        # Try to get any text from banner
                        banner_full_text = banner.inner_text()
                        print(f"   Full banner text: {banner_full_text}")
                else:
                    print("❌ Banner exists but not visible")
                    
                    # Check display style
                    style = banner.get_attribute("style")
                    print(f"   Banner style: {style}")
            else:
                print("❌ Banner element (#email-verification-banner) not found in DOM")
            
            # Take screenshot
            print("\n📸 Taking screenshot...")
            page.screenshot(path="email_banner_result.png", full_page=True)
            print("✅ Screenshot saved: email_banner_result.png")
            
            # Print page HTML for debugging
            print("\n🔍 Banner HTML:")
            banner_html = page.query_selector("#email-verification-banner")
            if banner_html:
                print(banner_html.inner_html()[:500])
            
            # Keep browser open
            print("\n⏸️  Keeping browser open for 10 seconds...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path="email_banner_error.png")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()
            print("\n✅ Test complete!")

if __name__ == "__main__":
    print("="*70)
    print("🧪 EMAIL VERIFICATION BANNER TEST - WITH SIGNUP")
    print("="*70)
    test_email_banner_with_signup()
