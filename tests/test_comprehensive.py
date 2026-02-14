"""
Comprehensive Playwright Test Suite
Tests all major features of the application.

Run with: pytest tests/test_comprehensive.py -v --headed
Or standalone: python tests/test_comprehensive.py
"""
import pytest
from playwright.sync_api import sync_playwright, expect, Page
import time
import os

# Configuration
BASE_URL = os.environ.get("TEST_URL", "https://trabcd.pythonanywhere.com")
ADMIN_USER = os.environ.get("TEST_USER", "Wai Tse")
ADMIN_PASSWORD = os.environ.get("TEST_PASS", "123")


def _login(page):
    """Login helper — navigates and authenticates via form."""
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state('networkidle')
    page.fill('input[name="username"]', ADMIN_USER)
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_timeout(3000)
    assert page.query_selector('.dashboard') or page.url != f"{BASE_URL}/", "Login failed — dashboard not loaded"


def _ensure_logged_in(page):
    """Re-login if the session is not active."""
    if not page.query_selector('.dashboard, .chat-container, #message-input'):
        login_input = page.query_selector('input[name="username"]:visible')
        if login_input:
            login_input.fill(ADMIN_USER)
            page.fill('input[name="password"]:visible', ADMIN_PASSWORD)
            page.click('button[type="submit"]:visible')
            page.wait_for_timeout(3000)


def test_analytics_dashboard(page: Page):
    """Test analytics dashboard features"""
    _login(page)

    page.goto(f"{BASE_URL}/admin/analytics")
    page.wait_for_timeout(3000)

    # Stats loading
    users_el = page.query_selector('#total-users')
    assert users_el and users_el.inner_text() != '-', "Stats not loaded"

    # Chart container exists and has height
    usage_chart = page.query_selector('#usage-chart-container')
    assert usage_chart, "Usage chart container not found"
    box = usage_chart.bounding_box()
    assert box and box['height'] > 0, "Usage chart not visible"

    # Filters exist
    assert page.query_selector('#date-range'), "Date filter not found"

    # Export button
    assert page.query_selector('button:has-text("Export CSV")'), "Export button not found"


def test_life_companion(page: Page):
    """Test Life Companion / Domain Characters page"""
    _login(page)

    page.goto(f"{BASE_URL}/life-companion")
    page.wait_for_timeout(4000)

    # Page loads with recognisable elements
    char_list = page.query_selector('.character-list, #character-list, .characters-grid, .domain-characters, [class*="character"]')
    page_loaded = page.query_selector('h1, .page-title, #contextBtn')
    assert char_list or page_loaded, "Life Companion page elements not found"

    # Context button opens panel
    context_btn = page.query_selector('#contextBtn')
    if context_btn:
        context_btn.click()
        page.wait_for_timeout(500)
        context_panel = page.query_selector('#explicit-context-panel')
        assert context_panel and context_panel.is_visible(), "Context panel not visible after click"

    # Message input present
    assert page.query_selector('#user-input, textarea[placeholder*="message"]'), "Message input not found"


def test_chat_interface(page: Page):
    """Test main chat interface"""
    _login(page)

    page.goto(f"{BASE_URL}/")
    page.wait_for_timeout(3000)
    _ensure_logged_in(page)

    # Chat tabs
    assert page.query_selector('[data-tab="chat"], .nav-btn:has-text("Chat")'), "Chat tab not found"

    # Admin features visible
    personality_btn = page.query_selector('#personality-btn, .personality-insights-btn, [class*="personality"], button:has-text("Personality")')
    admin_tools = page.query_selector('.admin-tools-btn, #admin-tools-btn, [class*="admin"]')
    assert personality_btn or admin_tools, "Admin features not visible"


def test_admin_features(page: Page):
    """Test admin-specific features"""
    _login(page)

    page.goto(f"{BASE_URL}/")
    page.wait_for_timeout(3000)
    _ensure_logged_in(page)

    # Admin tools button
    assert page.query_selector('.admin-tools-btn, #admin-tools-btn, button:has-text("Admin")'), "Admin tools button not found"

    # AI errors page loads
    page.goto(f"{BASE_URL}/admin/ai-errors")
    page.wait_for_timeout(2000)
    assert page.query_selector('.error-card, #error-list, h1'), "AI errors page not loaded"


def test_api_endpoints(page: Page):
    """Test critical API endpoints via the analytics page"""
    _login(page)

    page.goto(f"{BASE_URL}/admin/analytics")
    page.wait_for_timeout(3000)

    # Stats populated
    users = page.query_selector('#total-users')
    assert users and users.inner_text() not in ['-', ''], "Statistics not populated"

    # Budget status
    budget = page.query_selector('#budget-label')
    assert budget and budget.inner_text() not in ['Loading...', ''], "Budget not loaded"


def test_responsive_design(page: Page):
    """Test responsive design at mobile viewport"""
    _login(page)

    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(f"{BASE_URL}/admin/analytics")
    page.wait_for_timeout(2000)

    assert page.query_selector('h1, .dashboard-header'), "Page elements not visible at mobile size"

    # Reset
    page.set_viewport_size({"width": 1280, "height": 720})


# ---- Standalone runner (python tests/test_comprehensive.py) ----

class _StandaloneResults:
    def __init__(self):
        self.passed = []
        self.failed = []
    def add_pass(self, n): self.passed.append(n); print(f"  PASS: {n}")
    def add_fail(self, n, e=""): self.failed.append((n, e)); print(f"  FAIL: {n} - {e}")


def run_all_tests():
    """Run all tests in standalone mode."""
    print("=" * 60)
    print("COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    os.makedirs("screenshots", exist_ok=True)

    results = _StandaloneResults()
    test_fns = [
        test_analytics_dashboard, test_life_companion,
        test_chat_interface, test_admin_features,
        test_api_endpoints, test_responsive_design,
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1280, 'height': 720})
        page.on("console", lambda msg: None)

        for fn in test_fns:
            try:
                fn(page)
                results.add_pass(fn.__name__)
            except Exception as e:
                results.add_fail(fn.__name__, str(e))

        time.sleep(2)
        browser.close()

    total = len(results.passed) + len(results.failed)
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(results.passed)}/{total} passed")
    print(f"{'='*60}")
    return 0 if not results.failed else 1


if __name__ == "__main__":
    exit(run_all_tests())
