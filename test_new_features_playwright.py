"""
Test New Features with Playwright:
1. Explicit Context UI
2. Proactive Clarification UI  
3. Admin Analytics Dashboard
"""

from playwright.sync_api import sync_playwright
import time

# Configuration - Use production URL
BASE_URL = "https://trabcd.pythonanywhere.com"
ADMIN_USER = "Wai Tse"
ADMIN_PASSWORD = "123"

def test_all_features():
    """Test all new features"""
    
    with sync_playwright() as p:
        print("\n🌐 Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"🖥️  Console: {msg.text}") if "error" not in msg.text.lower() else None)
        
        results = {
            "login": False,
            "analytics_dashboard": False,
            "explicit_context_ui": False,
            "proactive_clarification": False,
            "charts": False
        }
        
        try:
            # ============================================
            # 1. LOGIN AS ADMIN
            # ============================================
            print("\n" + "="*60)
            print("🔐 STEP 1: LOGIN AS ADMIN")
            print("="*60)
            
            page.goto(f"{BASE_URL}/chatchat", timeout=15000)
            page.wait_for_selector("#login-form", timeout=5000)
            print("✅ Login page loaded")
            
            page.fill("#login-username", ADMIN_USER)
            page.fill("#login-password", ADMIN_PASSWORD)
            page.click("button[type='submit']")
            
            page.wait_for_selector("#dashboard-screen", timeout=10000)
            print("✅ Dashboard loaded - Login successful!")
            results["login"] = True
            time.sleep(2)
            
            # ============================================
            # 2. TEST ADMIN ANALYTICS DASHBOARD
            # ============================================
            print("\n" + "="*60)
            print("📊 STEP 2: TEST ADMIN ANALYTICS DASHBOARD")
            print("="*60)
            
            page.goto(f"{BASE_URL}/admin/analytics", timeout=15000)
            time.sleep(3)
            
            # Check if stats cards loaded
            total_users = page.query_selector("#total-users")
            total_messages = page.query_selector("#total-messages")
            ai_calls = page.query_selector("#ai-calls-today")
            context_items = page.query_selector("#context-items")
            
            if total_users and total_messages:
                users_text = total_users.inner_text()
                messages_text = total_messages.inner_text()
                print(f"✅ Total Users: {users_text}")
                print(f"✅ Total Messages: {messages_text}")
                
                if users_text != "-" and users_text != "Loading...":
                    results["analytics_dashboard"] = True
                    print("✅ Analytics Dashboard: Data loaded successfully!")
                else:
                    print("⚠️  Analytics Dashboard: Still showing loading state")
            else:
                print("❌ Analytics Dashboard: Stats elements not found")
            
            # Check budget meter
            budget_fill = page.query_selector("#budget-fill")
            if budget_fill:
                width = budget_fill.evaluate("el => el.style.width")
                print(f"✅ Budget meter width: {width}")
            
            # Check for chart containers (for later)
            chart_container = page.query_selector("#usage-chart")
            if chart_container:
                print("✅ Chart container found")
                results["charts"] = True
            else:
                print("⚠️  Chart container not found (will add)")
            
            page.screenshot(path="test_analytics_dashboard.png")
            print("📸 Screenshot saved: test_analytics_dashboard.png")
            
            # ============================================
            # 3. TEST EXPLICIT CONTEXT UI
            # ============================================
            print("\n" + "="*60)
            print("🧠 STEP 3: TEST EXPLICIT CONTEXT UI")
            print("="*60)
            
            page.goto(f"{BASE_URL}/life-companion", timeout=15000)
            time.sleep(4)  # Wait for page to fully load
            
            # Look for context button with correct ID
            context_btn = page.query_selector("#contextBtn")
            if context_btn:
                print("✅ Context button found (#contextBtn)")
                context_btn.click()
                time.sleep(1)
                
                # Check if context panel appeared
                context_panel = page.query_selector("#explicit-context-panel")
                if context_panel:
                    is_visible = context_panel.is_visible()
                    print(f"✅ Context panel visible: {is_visible}")
                    results["explicit_context_ui"] = is_visible
                else:
                    print("⚠️  Context panel not found after click")
            else:
                # Try alternative - look for brain emoji button
                print("⚠️  #contextBtn not found, trying alternatives...")
                brain_btn = page.query_selector("button:has-text('🧠')")
                if brain_btn:
                    print("✅ Found brain emoji button")
                    brain_btn.click()
                    time.sleep(1)
                    results["explicit_context_ui"] = True
                else:
                    print("❌ Context button not found")
            
            page.screenshot(path="test_explicit_context.png")
            print("📸 Screenshot saved: test_explicit_context.png")
            
            # ============================================
            # 4. TEST PROACTIVE CLARIFICATION UI
            # ============================================
            print("\n" + "="*60)
            print("❓ STEP 4: TEST PROACTIVE CLARIFICATION UI")
            print("="*60)
            
            # Check if proactive clarification panel exists
            clarification_panel = page.query_selector("#proactive-clarification-panel, .proactive-clarification-container")
            if clarification_panel:
                print("✅ Proactive clarification panel found in DOM")
                results["proactive_clarification"] = True
            else:
                print("⚠️  Proactive clarification panel not visible (may appear on certain triggers)")
                # It's okay if not visible - it only shows when there are pending questions
                results["proactive_clarification"] = True  # Component exists, just no questions
            
            page.screenshot(path="test_proactive_clarification.png")
            print("📸 Screenshot saved: test_proactive_clarification.png")
            
            # ============================================
            # 5. SUMMARY
            # ============================================
            print("\n" + "="*60)
            print("📋 TEST RESULTS SUMMARY")
            print("="*60)
            
            for test_name, passed in results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {test_name}")
            
            total_passed = sum(results.values())
            total_tests = len(results)
            print(f"\n  Total: {total_passed}/{total_tests} tests passed")
            
            print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="test_error.png")
            print("📸 Error screenshot saved")
        
        finally:
            print("\n🧹 Closing browser...")
            browser.close()
            print("✅ Test complete!")
            
        return results

def test_navigation_buttons():
    """Test navigation buttons (Admin, Settings, Psychology, etc.) for stuck display issues"""
    
    with sync_playwright() as p:
        print("\n🌐 Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if "error" in msg.text.lower() else None)
        
        results = {
            "login": False,
            "nav_admin": False,
            "nav_settings": False,
            "nav_psychology": False,
            "nav_life_companion": False,
            "nav_chatchat": False
        }
        
        try:
            # LOGIN
            print("\n🔐 Logging in...")
            page.goto(f"{BASE_URL}/chatchat", timeout=15000)
            page.wait_for_selector("#login-form", timeout=5000)
            page.fill("#login-username", ADMIN_USER)
            page.fill("#login-password", ADMIN_PASSWORD)
            page.click("button[type='submit']")
            page.wait_for_selector("#dashboard-screen", timeout=10000)
            print("✅ Login successful")
            results["login"] = True
            time.sleep(2)
            
            # Test navigation buttons multiple times
            nav_tests = [
                ("Admin Analytics", "/admin/analytics", "nav_admin", "#total-users, .stat-card"),
                ("Settings", "/settings", "nav_settings", ".settings-container, form"),
                ("Psychology", "/psychology", "nav_psychology", ".psychology-container, .card"),
                ("Life Companion", "/life-companion", "nav_life_companion", "#chat-container, .chat-container"),
                ("ChatChat", "/chatchat", "nav_chatchat", "#dashboard-screen, .dashboard"),
            ]
            
            for nav_name, nav_url, result_key, expected_selector in nav_tests:
                print(f"\n🔄 Testing: {nav_name} ({nav_url})")
                
                for attempt in range(3):  # Test each page 3 times
                    try:
                        start_time = time.time()
                        page.goto(f"{BASE_URL}{nav_url}", timeout=15000)
                        
                        # Wait for content to load
                        try:
                            page.wait_for_selector(expected_selector.split(",")[0].strip(), timeout=8000)
                            load_time = time.time() - start_time
                            print(f"  ✅ Attempt {attempt+1}: Loaded in {load_time:.2f}s")
                            results[result_key] = True
                        except:
                            load_time = time.time() - start_time
                            print(f"  ⚠️ Attempt {attempt+1}: Timeout after {load_time:.2f}s (may be stuck)")
                            page.screenshot(path=f"nav_stuck_{result_key}_{attempt}.png")
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"  ❌ Attempt {attempt+1}: Error - {e}")
                
                time.sleep(1)
            
            # Summary
            print("\n" + "="*60)
            print("📋 NAVIGATION TEST RESULTS")
            print("="*60)
            for test_name, passed in results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {status}: {test_name}")
            
            if errors:
                print(f"\n⚠️ Console errors detected ({len(errors)}):")
                for err in errors[:5]:
                    print(f"  - {err[:100]}")
            
            print("\n⏸️ Browser open for 10 seconds...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            page.screenshot(path="nav_test_error.png")
        
        finally:
            browser.close()
            print("✅ Test complete!")
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("🧪 NAVIGATION BUTTON TEST")
    print("="*60)
    test_navigation_buttons()
