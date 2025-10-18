#!/usr/bin/env python3
"""
Automated UI Testing for Multi-User AI Chatbot
Uses Playwright for browser automation with optional AI vision analysis
"""

import time
import base64
from pathlib import Path
from datetime import datetime
import json

try:
    from playwright.sync_api import sync_playwright, expect
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Run: pip install playwright && playwright install")

# Optional: AI Vision for advanced testing
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AutomatedTester:
    """Automated UI tester with screenshot capture and optional AI analysis"""
    
    def __init__(self, base_url="http://localhost:5000", use_ai=False, ai_provider="claude"):
        self.base_url = base_url
        self.use_ai = use_ai
        self.ai_provider = ai_provider
        self.test_results = []
        self.screenshot_dir = Path("test_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # Initialize AI client if requested
        self.ai_client = None
        if use_ai:
            if ai_provider == "claude" and CLAUDE_AVAILABLE:
                self.ai_client = anthropic.Anthropic()
                print("✅ Claude AI vision enabled")
            elif ai_provider == "openai" and OPENAI_AVAILABLE:
                self.ai_client = OpenAI()
                print("✅ OpenAI GPT-4V enabled")
            else:
                print("⚠️  AI vision requested but not available, running without AI")
    
    def log_result(self, test_name, passed, message, screenshot_path=None):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "screenshot": screenshot_path,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if screenshot_path:
            print(f"   📸 Screenshot: {screenshot_path}")
        print()
    
    def take_screenshot(self, page, name):
        """Take and save screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshot_dir / filename
        page.screenshot(path=str(filepath))
        return str(filepath)
    
    def analyze_screenshot_with_ai(self, screenshot_path, question):
        """Use AI to analyze screenshot"""
        if not self.ai_client:
            return "AI analysis not available"
        
        try:
            with open(screenshot_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            if self.ai_provider == "claude":
                response = self.ai_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": question
                            }
                        ]
                    }]
                )
                return response.content[0].text
            
            elif self.ai_provider == "openai":
                response = self.ai_client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                        ]
                    }],
                    max_tokens=1024
                )
                return response.choices[0].message.content
        
        except Exception as e:
            return f"AI analysis error: {str(e)}"
    
    def test_login_screen(self, page):
        """Test 1: Login screen loads and displays correctly"""
        try:
            page.goto(f"{self.base_url}/multi-user")
            page.wait_for_selector("#login-screen", timeout=5000)
            
            screenshot = self.take_screenshot(page, "01_login_screen")
            
            # Check for key elements with more specific selectors
            username_input = page.locator("#login-username")
            password_input = page.locator("#login-password")
            login_button = page.locator("#login-form button[type='submit']")
            
            if username_input.is_visible() and password_input.is_visible() and login_button.is_visible():
                self.log_result(
                    "Login Screen Display",
                    True,
                    "Login screen loads with all required elements",
                    screenshot
                )
                return True
            else:
                self.log_result(
                    "Login Screen Display",
                    False,
                    "Login screen missing some elements",
                    screenshot
                )
                return False
        
        except Exception as e:
            self.log_result("Login Screen Display", False, f"Error: {str(e)}")
            return False
    
    def test_signup_screen(self, page):
        """Test: Signup screen shows when clicking signup link"""
        try:
            # Should be on login screen
            login_screen = page.locator("#login-screen")
            signup_link = page.locator("#show-signup")
            
            # Click signup link
            signup_link.click()
            time.sleep(0.5)
            
            screenshot = self.take_screenshot(page, "01b_signup_screen")
            
            # Check if signup screen is visible and login screen is hidden
            signup_screen = page.locator("#signup-screen")
            
            signup_visible = signup_screen.is_visible()
            login_visible = login_screen.is_visible()
            
            # Check form fields
            username_input = page.locator("#signup-username")
            email_input = page.locator("#signup-email")
            password_input = page.locator("#signup-password")
            confirm_input = page.locator("#signup-confirm-password")
            
            all_fields_present = (
                username_input.is_visible() and 
                email_input.is_visible() and 
                password_input.is_visible() and 
                confirm_input.is_visible()
            )
            
            success = signup_visible and not login_visible and all_fields_present
            
            self.log_result(
                "Signup Screen Display",
                success,
                f"Signup visible: {signup_visible}, Login hidden: {not login_visible}, Fields present: {all_fields_present}",
                screenshot
            )
            
            return success
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "01b_signup_error")
            self.log_result("Signup Screen Display", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_signup_to_login_navigation(self, page):
        """Test: Can navigate back from signup to login"""
        try:
            # Should be on signup screen from previous test
            login_link = page.locator("#show-login")
            login_link.click()
            time.sleep(0.5)
            
            screenshot = self.take_screenshot(page, "01c_back_to_login")
            
            # Check if login screen is visible and signup is hidden
            login_screen = page.locator("#login-screen")
            signup_screen = page.locator("#signup-screen")
            
            login_visible = login_screen.is_visible()
            signup_visible = signup_screen.is_visible()
            
            success = login_visible and not signup_visible
            
            self.log_result(
                "Signup to Login Navigation",
                success,
                f"Login visible: {login_visible}, Signup hidden: {not signup_visible}",
                screenshot
            )
            
            return success
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "01c_navigation_error")
            self.log_result("Signup to Login Navigation", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_login_flow(self, page, username="AutoTest", password="test123"):
        """Test 2: Login functionality with dedicated test user"""
        try:
            # Fill login form
            page.fill("#login-username", username)
            page.fill("#login-password", password)
            
            screenshot_before = self.take_screenshot(page, "02_login_filled")
            
            # Click login
            page.click("button[type='submit']")
            
            # Wait for dashboard
            page.wait_for_selector("#dashboard-screen", timeout=10000)
            
            screenshot_after = self.take_screenshot(page, "03_dashboard_loaded")
            
            # Check if dashboard is visible
            dashboard = page.locator("#dashboard-screen")
            if dashboard.is_visible():
                self.log_result(
                    "Login Flow",
                    True,
                    f"Successfully logged in as {username}",
                    screenshot_after
                )
                return True
            else:
                self.log_result(
                    "Login Flow",
                    False,
                    "Dashboard not visible after login",
                    screenshot_after
                )
                return False
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "03_login_error")
            self.log_result("Login Flow", False, f"Login failed: {str(e)}", screenshot)
            return False
    
    def test_personality_controls(self, page):
        """Test 3: Personality controls are visible and clickable"""
        try:
            # Make sure we're on chat tab
            chat_tab = page.locator("button[data-tab='chat']")
            if chat_tab.is_visible():
                chat_tab.click()
                time.sleep(1)
            
            screenshot = self.take_screenshot(page, "04_personality_controls")
            
            # Check for personality presets
            presets = page.locator(".personality-preset")
            count = presets.count()
            
            if count >= 4:
                # Try clicking one
                presets.nth(1).click()  # Click second preset
                time.sleep(0.5)
                
                screenshot_clicked = self.take_screenshot(page, "05_personality_clicked")
                
                # Check if it became active
                is_active = "active" in presets.nth(1).get_attribute("class")
                
                self.log_result(
                    "Personality Controls",
                    True,
                    f"Found {count} personality presets, clicking works: {is_active}",
                    screenshot_clicked
                )
                return True
            else:
                self.log_result(
                    "Personality Controls",
                    False,
                    f"Expected 4 personality presets, found {count}",
                    screenshot
                )
                return False
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "04_personality_error")
            self.log_result("Personality Controls", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_textarea_expansion(self, page):
        """Test 4: Textarea auto-expansion"""
        try:
            chat_input = page.locator("#chat-input")
            
            # Get initial height
            initial_height = chat_input.evaluate("el => el.offsetHeight")
            screenshot_initial = self.take_screenshot(page, "06_textarea_initial")
            
            # Type multiple lines
            text_lines = "\n".join([f"Line {i+1} of test text" for i in range(6)])
            chat_input.fill(text_lines)
            time.sleep(0.5)
            
            # Get expanded height
            expanded_height = chat_input.evaluate("el => el.offsetHeight")
            screenshot_expanded = self.take_screenshot(page, "07_textarea_expanded")
            
            # Check if height increased
            if expanded_height > initial_height:
                # Check if scrollbar appears (height should be capped at ~120px for 5 lines)
                overflow = chat_input.evaluate("el => window.getComputedStyle(el).overflowY")
                
                self.log_result(
                    "Textarea Expansion",
                    True,
                    f"Textarea expanded from {initial_height}px to {expanded_height}px, overflow: {overflow}",
                    screenshot_expanded
                )
                
                # Clear for next test
                chat_input.fill("")
                return True
            else:
                self.log_result(
                    "Textarea Expansion",
                    False,
                    f"Textarea did not expand (stayed at {initial_height}px)",
                    screenshot_expanded
                )
                return False
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "06_textarea_error")
            self.log_result("Textarea Expansion", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_enter_key_behavior(self, page):
        """Test 5: Enter vs Shift+Enter behavior"""
        try:
            # First, create a new chat session
            new_chat_btn = page.locator("#new-chat-btn")
            new_chat_btn.click()
            time.sleep(2)  # Wait for chat to be created
            
            # Click on the newly created chat (should be first in list)
            first_chat = page.locator(".chat-session-item").first
            first_chat.click()
            time.sleep(1)
            
            # Wait for chat input to be enabled
            chat_input = page.locator("#chat-input")
            page.wait_for_selector("#chat-input:not([disabled])", timeout=5000)
            
            # Verify input is actually enabled
            is_enabled = page.evaluate("() => !document.getElementById('chat-input').disabled")
            
            if not is_enabled:
                raise Exception("Chat input is still disabled after creating chat session")
            
            # Test Shift+Enter (should add new line)
            chat_input.fill("First line")
            chat_input.press("Shift+Enter")
            chat_input.type("Second line")
            time.sleep(0.3)
            
            value_after_shift_enter = chat_input.input_value()
            screenshot_shift_enter = self.take_screenshot(page, "08_shift_enter")
            
            has_newline = "\n" in value_after_shift_enter
            
            # Clear input
            chat_input.fill("")
            
            # Test Enter alone (should trigger send - we'll just check it doesn't add newline)
            chat_input.fill("Test message")
            initial_value = chat_input.input_value()
            
            # Note: Enter will trigger send, so value might clear
            # We just verify Shift+Enter worked
            
            self.log_result(
                "Enter Key Behavior",
                has_newline,
                f"Shift+Enter adds newline: {has_newline}, Value: '{value_after_shift_enter}', Input enabled: {is_enabled}",
                screenshot_shift_enter
            )
            
            return has_newline
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "08_enter_key_error")
            self.log_result("Enter Key Behavior", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_tab_navigation(self, page):
        """Test 6: Tab navigation"""
        try:
            tabs = ["chat", "profile", "psychology", "conversations", "settings"]
            all_tabs_work = True
            
            for tab_name in tabs:
                try:
                    # Click tab button
                    tab_button = page.locator(f"button[data-tab='{tab_name}']")
                    tab_button.click()
                    time.sleep(1)
                    
                    screenshot = self.take_screenshot(page, f"09_tab_{tab_name}")
                    
                    # Check if tab content is visible
                    tab_content = page.locator(f"#{tab_name}-tab")
                    is_visible = tab_content.is_visible()
                    
                    if not is_visible:
                        all_tabs_work = False
                        self.log_result(
                            f"Tab Navigation ({tab_name})",
                            False,
                            f"Tab content not visible for {tab_name}",
                            screenshot
                        )
                    
                except Exception as e:
                    all_tabs_work = False
                    screenshot = self.take_screenshot(page, f"09_tab_{tab_name}_error")
                    self.log_result(
                        f"Tab Navigation ({tab_name})",
                        False,
                        f"Error: {str(e)}",
                        screenshot
                    )
            
            if all_tabs_work:
                self.log_result(
                    "Tab Navigation",
                    True,
                    f"All {len(tabs)} tabs navigable and display content"
                )
            
            return all_tabs_work
        
        except Exception as e:
            self.log_result("Tab Navigation", False, f"Error: {str(e)}")
            return False
    
    def test_page_refresh(self, page):
        """Test 7: Page refresh and state restoration"""
        try:
            # Navigate to psychology tab
            page.click("button[data-tab='psychology']")
            time.sleep(1)
            
            # Scroll down a bit
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(0.5)
            
            screenshot_before = self.take_screenshot(page, "10_before_refresh")
            scroll_before = page.evaluate("window.pageYOffset")
            
            # Refresh page
            page.reload()
            time.sleep(2)
            
            screenshot_after = self.take_screenshot(page, "11_after_refresh")
            
            # Check if still on psychology tab
            psychology_tab = page.locator("#psychology-tab")
            is_psychology_visible = psychology_tab.is_visible()
            
            scroll_after = page.evaluate("window.pageYOffset")
            
            # Check for flash (this is visual, hard to test automatically)
            # We'll just verify the state was restored
            
            success = is_psychology_visible and abs(scroll_after - scroll_before) < 100
            
            self.log_result(
                "Page Refresh & State Restoration",
                success,
                f"Tab restored: {is_psychology_visible}, Scroll restored: {scroll_before}→{scroll_after}",
                screenshot_after
            )
            
            return success
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "10_refresh_error")
            self.log_result("Page Refresh", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_rapid_chat_creation(self, page):
        """Test: Rapid clicking of New Chat button doesn't cause database errors or duplicates"""
        try:
            # Navigate to chat tab
            chat_tab = page.locator("button[data-tab='chat']")
            chat_tab.click()
            time.sleep(0.5)
            
            screenshot_before = self.take_screenshot(page, "11a_before_rapid_creation")
            
            # Get initial chat count and titles
            initial_chats = page.locator(".chat-session-item").count()
            
            # Get initial chat titles to detect duplicates
            initial_titles = []
            for i in range(initial_chats):
                try:
                    title = page.locator(".chat-session-item .session-title").nth(i).text_content()
                    initial_titles.append(title)
                except:
                    pass
            
            # Rapidly click "New Chat" button 5 times to really test it
            new_chat_btn = page.locator("#new-chat-btn")
            print(f"   Initial chats: {initial_chats}")
            
            for i in range(5):
                new_chat_btn.click()
                time.sleep(0.05)  # Very short delay to simulate rapid clicking
                print(f"   Click {i+1} sent")
            
            # Wait for operations to complete
            time.sleep(4)
            
            screenshot_after = self.take_screenshot(page, "11b_after_rapid_creation")
            
            # Check for error notifications (constraint failed, database locked, etc.)
            error_notification = page.locator("#notification.error, .notification.error")
            has_error = error_notification.is_visible() if error_notification.count() > 0 else False
            
            # Get final chat count and titles
            final_chats = page.locator(".chat-session-item").count()
            final_titles = []
            for i in range(final_chats):
                try:
                    title = page.locator(".chat-session-item .session-title").nth(i).text_content()
                    final_titles.append(title)
                except:
                    pass
            
            # Check for duplicate titles
            new_titles = [t for t in final_titles if t not in initial_titles]
            unique_new_titles = set(new_titles)
            has_duplicates = len(new_titles) != len(unique_new_titles)
            
            chats_created = final_chats - initial_chats
            
            # Success if:
            # 1. No error notifications appeared
            # 2. Exactly 1 chat was created (duplicate prevention should work)
            # 3. No duplicate titles in the list
            success = not has_error and chats_created == 1 and not has_duplicates
            
            error_text = ""
            if has_error:
                try:
                    error_text = error_notification.first.text_content()
                except:
                    error_text = "Error notification present"
            
            duplicate_msg = f", Duplicates: YES" if has_duplicates else ", Duplicates: NO"
            new_titles_str = ', '.join(new_titles[:3]) if new_titles else 'none'
            
            print(f"   Final chats: {final_chats}")
            print(f"   Chats created: {chats_created}")
            print(f"   New titles: {new_titles_str}")
            print(f"   Has duplicates: {has_duplicates}")
            
            self.log_result(
                "Rapid Chat Creation (No Duplicates)",
                success,
                f"Created {chats_created} chats (expected 1), No errors: {not has_error}{duplicate_msg}, Clicked 5 times. Error: '{error_text}'",
                screenshot_after
            )
            
            return success
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "11a_rapid_creation_error")
            self.log_result("Rapid Chat Creation", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_logout(self, page):
        """Test: Logout returns to login screen properly"""
        try:
            # Should be on dashboard
            logout_btn = page.locator("#logout-btn")
            logout_btn.click()
            time.sleep(1)
            
            screenshot = self.take_screenshot(page, "12_after_logout")
            
            # Check login screen is visible and dashboard is hidden
            login_screen = page.locator("#login-screen")
            dashboard_screen = page.locator("#dashboard-screen")
            
            login_visible = login_screen.is_visible()
            dashboard_visible = dashboard_screen.is_visible()
            
            # Check scroll position is at top
            scroll_position = page.evaluate("window.pageYOffset")
            
            success = login_visible and not dashboard_visible and scroll_position == 0
            
            self.log_result(
                "Logout Functionality",
                success,
                f"Login visible: {login_visible}, Dashboard hidden: {not dashboard_visible}, Scroll at top: {scroll_position == 0}",
                screenshot
            )
            
            return success
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "12_logout_error")
            self.log_result("Logout Functionality", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_signup_after_logout(self, page):
        """Test: Can navigate to signup screen after logout"""
        try:
            # Should be on login screen
            signup_link = page.locator("#show-signup")
            signup_link.click()
            time.sleep(0.5)
            
            screenshot = self.take_screenshot(page, "13_signup_after_logout")
            
            # Check signup screen is visible
            signup_screen = page.locator("#signup-screen")
            login_screen = page.locator("#login-screen")
            dashboard_screen = page.locator("#dashboard-screen")
            
            signup_visible = signup_screen.is_visible()
            login_hidden = not login_screen.is_visible()
            dashboard_hidden = not dashboard_screen.is_visible()
            
            success = signup_visible and login_hidden and dashboard_hidden
            
            self.log_result(
                "Signup After Logout",
                success,
                f"Signup visible: {signup_visible}, Login hidden: {login_hidden}, Dashboard hidden: {dashboard_hidden}",
                screenshot
            )
            
            return success
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "13_signup_after_logout_error")
            self.log_result("Signup After Logout", False, f"Error: {str(e)}", screenshot)
            return False
    
    def test_no_screen_stacking(self, page):
        """Test: Verify no screen stacking by checking body height and scrollability"""
        try:
            # Should be on signup screen
            screenshot = self.take_screenshot(page, "14_no_stacking_check")
            
            # Get page height and viewport height
            page_height = page.evaluate("document.documentElement.scrollHeight")
            viewport_height = page.evaluate("window.innerHeight")
            max_scroll = page.evaluate("document.documentElement.scrollHeight - window.innerHeight")
            
            # Try to scroll down
            page.evaluate("window.scrollTo(0, 1000)")
            time.sleep(0.5)
            
            # Check if page actually scrolled
            scroll_position = page.evaluate("window.pageYOffset")
            
            screenshot_after = self.take_screenshot(page, "15_after_scroll_attempt")
            
            # On auth screens, page should not scroll (or minimal scroll)
            no_stacking = scroll_position < 100  # Allow small scroll but not full page
            
            self.log_result(
                "No Screen Stacking",
                no_stacking,
                f"Page height: {page_height}px, Viewport: {viewport_height}px, Scroll position after attempt: {scroll_position}px, Max scroll: {max_scroll}px",
                screenshot_after
            )
            
            # Scroll back to top for cleanliness
            page.evaluate("window.scrollTo(0, 0)")
            
            return no_stacking
        
        except Exception as e:
            screenshot = self.take_screenshot(page, "14_stacking_check_error")
            self.log_result("No Screen Stacking", False, f"Error: {str(e)}", screenshot)
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        if not PLAYWRIGHT_AVAILABLE:
            print("❌ Playwright not installed!")
            print("📦 Install with: pip install playwright && playwright install")
            return
        
        # Clear old screenshots and results
        print("🧹 Cleaning up old test files...")
        for old_file in self.screenshot_dir.glob("*.png"):
            old_file.unlink()
        for old_file in self.screenshot_dir.glob("*.json"):
            old_file.unlink()
        print("✅ Old test files removed\n")
        
        print("🚀 Starting Automated UI Tests")
        print("=" * 60)
        print(f"📍 Base URL: {self.base_url}")
        print(f"🤖 AI Vision: {'Enabled' if self.use_ai else 'Disabled'}")
        print("=" * 60)
        print()
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False, slow_mo=500)  # slow_mo for visibility
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            
            try:
                # Run tests in sequence
                self.test_login_screen(page)
                self.test_signup_screen(page)
                self.test_signup_to_login_navigation(page)
                
                if self.test_login_flow(page):
                    # Only continue if login worked
                    self.test_personality_controls(page)
                    self.test_textarea_expansion(page)
                    self.test_enter_key_behavior(page)
                    self.test_tab_navigation(page)
                    self.test_page_refresh(page)
                    
                    # Test rapid chat creation (database lock/constraint test)
                    self.test_rapid_chat_creation(page)
                    
                    # Test logout and signup
                    self.test_logout(page)
                    self.test_signup_after_logout(page)
                    self.test_no_screen_stacking(page)
                
                # Keep browser open for manual inspection
                print("\n⏸️  Tests complete! Browser will stay open for 10 seconds...")
                print("   Review the screenshots in the 'test_screenshots' folder")
                time.sleep(10)
            
            finally:
                browser.close()
        
        # Print summary
        self.print_summary()
        
        # Save results to JSON
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        print()
        
        if failed > 0:
            print("❌ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("=" * 60)
    
    def save_results(self):
        """Save test results to JSON"""
        results_file = self.screenshot_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n💾 Results saved to: {results_file}")


def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🤖 Multi-User AI Chatbot - Automated UI Tester             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    BASE_URL = "http://localhost:5000"
    USE_AI = False  # Set to True if you want AI-powered analysis (requires API keys)
    AI_PROVIDER = "claude"  # or "openai"
    
    # Create and run tester
    tester = AutomatedTester(
        base_url=BASE_URL,
        use_ai=USE_AI,
        ai_provider=AI_PROVIDER
    )
    
    tester.run_all_tests()
    
    print("\n✨ Testing complete! Check the screenshots folder for visual evidence.")


if __name__ == "__main__":
    main()
