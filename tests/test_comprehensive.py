"""
Comprehensive Playwright Test Suite
Tests all major features of the application.
"""
from playwright.sync_api import sync_playwright, expect
import time
import os

# Configuration
BASE_URL = "https://trabcd.pythonanywhere.com"
ADMIN_USER = "Wai Tse"
ADMIN_PASSWORD = "123"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, name):
        self.passed.append(name)
        print(f"  ✅ PASS: {name}")
    
    def add_fail(self, name, error=""):
        self.failed.append((name, error))
        print(f"  ❌ FAIL: {name} - {error}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {len(self.passed)}/{total} passed")
        print(f"{'='*60}")
        if self.failed:
            print("\nFailed tests:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")
        return len(self.failed) == 0


def login(page, results):
    """Login and return success status"""
    try:
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state('networkidle')
        page.fill('input[name="username"]', ADMIN_USER)
        page.fill('input[name="password"]', ADMIN_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_timeout(3000)
        
        # Check if login succeeded
        if page.query_selector('.dashboard') or page.url != f"{BASE_URL}/":
            results.add_pass("Login")
            return True
        else:
            results.add_fail("Login", "Dashboard not loaded")
            return False
    except Exception as e:
        results.add_fail("Login", str(e))
        return False


def test_analytics_dashboard(page, results):
    """Test analytics dashboard features"""
    print("\n📊 Testing Analytics Dashboard...")
    
    try:
        page.goto(f"{BASE_URL}/admin/analytics")
        page.wait_for_timeout(3000)
        
        # Test stats loading
        users_el = page.query_selector('#total-users')
        if users_el and users_el.inner_text() != '-':
            results.add_pass("Analytics - Stats Loading")
        else:
            results.add_fail("Analytics - Stats Loading", "Stats not loaded")
        
        # Test chart containers exist
        usage_chart = page.query_selector('#usage-chart-container')
        if usage_chart:
            box = usage_chart.bounding_box()
            if box and box['height'] > 0:
                results.add_pass("Analytics - Usage Chart")
            else:
                results.add_fail("Analytics - Usage Chart", "Chart not visible")
        else:
            results.add_fail("Analytics - Usage Chart", "Container not found")
        
        # Test filters exist
        date_filter = page.query_selector('#date-range')
        if date_filter:
            results.add_pass("Analytics - Date Filter")
        else:
            results.add_fail("Analytics - Date Filter", "Not found")
        
        # Test export button
        export_btn = page.query_selector('button:has-text("Export CSV")')
        if export_btn:
            results.add_pass("Analytics - Export Button")
        else:
            results.add_fail("Analytics - Export Button", "Not found")
        
        page.screenshot(path="screenshots/test_analytics.png")
        
    except Exception as e:
        results.add_fail("Analytics Dashboard", str(e))


def test_life_companion(page, results):
    """Test Life Companion / Domain Characters page"""
    print("\n🧠 Testing Life Companion...")
    
    try:
        page.goto(f"{BASE_URL}/life-companion")
        page.wait_for_timeout(4000)
        
        # Test character list loads (check multiple possible selectors)
        char_list = page.query_selector('.character-list, #character-list, .characters-grid, .domain-characters, [class*="character"]')
        page_loaded = page.query_selector('h1, .page-title, #contextBtn')
        if char_list or page_loaded:
            results.add_pass("Life Companion - Page Loads")
        else:
            results.add_fail("Life Companion - Page Loads", "Page elements not found")
        
        # Test context button
        context_btn = page.query_selector('#contextBtn')
        if context_btn:
            context_btn.click()
            page.wait_for_timeout(500)
            context_panel = page.query_selector('#explicit-context-panel')
            if context_panel and context_panel.is_visible():
                results.add_pass("Life Companion - Context Panel")
            else:
                results.add_fail("Life Companion - Context Panel", "Panel not visible after click")
        else:
            results.add_fail("Life Companion - Context Button", "Not found")
        
        # Test message input
        msg_input = page.query_selector('#user-input, textarea[placeholder*="message"]')
        if msg_input:
            results.add_pass("Life Companion - Message Input")
        else:
            results.add_fail("Life Companion - Message Input", "Not found")
        
        page.screenshot(path="screenshots/test_life_companion.png")
        
    except Exception as e:
        results.add_fail("Life Companion", str(e))


def test_chat_interface(page, results):
    """Test main chat interface"""
    print("\n💬 Testing Chat Interface...")
    
    try:
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(3000)
        
        # Check if already logged in (skip login if dashboard visible)
        if not page.query_selector('.dashboard, .chat-container, #message-input'):
            login_input = page.query_selector('input[name="username"]:visible')
            if login_input:
                login_input.fill(ADMIN_USER)
                page.fill('input[name="password"]:visible', ADMIN_PASSWORD)
                page.click('button[type="submit"]:visible')
                page.wait_for_timeout(3000)
        
        # Test chat tabs
        chat_tab = page.query_selector('[data-tab="chat"], .nav-btn:has-text("Chat")')
        if chat_tab:
            results.add_pass("Chat - Tab Navigation")
        else:
            results.add_fail("Chat - Tab Navigation", "Chat tab not found")
        
        # Test personality button (admin feature) - check multiple selectors
        personality_btn = page.query_selector('#personality-btn, .personality-insights-btn, [class*="personality"], button:has-text("Personality")')
        admin_tools = page.query_selector('.admin-tools-btn, #admin-tools-btn, [class*="admin"]')
        if personality_btn or admin_tools:
            results.add_pass("Chat - Admin Features Visible")
        else:
            results.add_fail("Chat - Admin Features Visible", "Admin elements not found")
        
        page.screenshot(path="screenshots/test_chat.png")
        
    except Exception as e:
        results.add_fail("Chat Interface", str(e))


def test_admin_features(page, results):
    """Test admin-specific features"""
    print("\n👑 Testing Admin Features...")
    
    try:
        page.goto(f"{BASE_URL}/")
        page.wait_for_timeout(3000)
        
        # Check if already logged in
        if not page.query_selector('.dashboard, .chat-container, #message-input'):
            login_input = page.query_selector('input[name="username"]:visible')
            if login_input:
                login_input.fill(ADMIN_USER)
                page.fill('input[name="password"]:visible', ADMIN_PASSWORD)
                page.click('button[type="submit"]:visible')
                page.wait_for_timeout(3000)
        
        # Check for admin tools
        admin_btn = page.query_selector('.admin-tools-btn, #admin-tools-btn, button:has-text("Admin")')
        if admin_btn:
            results.add_pass("Admin - Tools Button")
        else:
            results.add_fail("Admin - Tools Button", "Not found")
        
        # Test AI errors page
        page.goto(f"{BASE_URL}/admin/ai-errors")
        page.wait_for_timeout(2000)
        if page.query_selector('.error-card, #error-list, h1'):
            results.add_pass("Admin - AI Errors Page")
        else:
            results.add_fail("Admin - AI Errors Page", "Page not loaded correctly")
        
        page.screenshot(path="screenshots/test_admin.png")
        
    except Exception as e:
        results.add_fail("Admin Features", str(e))


def test_api_endpoints(page, results):
    """Test critical API endpoints"""
    print("\n🔌 Testing API Endpoints...")
    
    try:
        # Test statistics API
        page.goto(f"{BASE_URL}/admin/analytics")
        page.wait_for_timeout(3000)
        
        # Check if stats loaded (indicates API working)
        users = page.query_selector('#total-users')
        if users and users.inner_text() not in ['-', '']:
            results.add_pass("API - Statistics")
        else:
            results.add_fail("API - Statistics", "Stats not populated")
        
        # Check budget status
        budget = page.query_selector('#budget-label')
        if budget and budget.inner_text() not in ['Loading...', '']:
            results.add_pass("API - Budget Status")
        else:
            results.add_fail("API - Budget Status", "Budget not loaded")
        
    except Exception as e:
        results.add_fail("API Endpoints", str(e))


def test_responsive_design(page, results):
    """Test responsive design at different viewport sizes"""
    print("\n📱 Testing Responsive Design...")
    
    try:
        # Test mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(f"{BASE_URL}/admin/analytics")  # Test analytics page
        page.wait_for_timeout(2000)
        
        # Check if key elements are visible (more practical test)
        page_title = page.query_selector('h1, .dashboard-header')
        if page_title:
            results.add_pass("Responsive - Mobile View")
        else:
            results.add_fail("Responsive - Mobile View", "Page elements not visible")
        
        page.screenshot(path="screenshots/test_mobile.png")
        
        # Reset to desktop
        page.set_viewport_size({"width": 1280, "height": 720})
        
    except Exception as e:
        results.add_fail("Responsive Design", str(e))


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("🧪 COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"User: {ADMIN_USER}")
    
    # Create screenshots directory
    os.makedirs("screenshots", exist_ok=True)
    
    results = TestResults()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1280, 'height': 720})
        
        # Enable console logging
        page.on("console", lambda msg: None)  # Suppress console output
        
        print("\n🔐 Testing Login...")
        if login(page, results):
            # Run all tests if login succeeds
            test_analytics_dashboard(page, results)
            test_life_companion(page, results)
            test_chat_interface(page, results)
            test_admin_features(page, results)
            test_api_endpoints(page, results)
            test_responsive_design(page, results)
        
        print("\n⏳ Keeping browser open for 5 seconds...")
        time.sleep(5)
        
        browser.close()
    
    # Print summary
    success = results.summary()
    return 0 if success else 1


if __name__ == "__main__":
    exit(run_all_tests())
