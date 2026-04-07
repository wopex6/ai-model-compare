"""
Simple Playwright test to verify shared modules are loaded on user_logon page
"""
import pytest
from playwright.sync_api import Page

def test_shared_modules_loaded_on_user_logon(page: Page):
    """Test that shared modules are loaded on user_logon page"""
    page.goto("http://localhost:5050/user_logon")
    page.wait_for_selector("#login-screen", state="visible")
    page.wait_for_timeout(2000)  # Wait for scripts to load
    
    # Check that shared modules are loaded
    modules_loaded = {}
    expected_modules = [
        "AuthHelper",
        "MessageHandler", 
        "ExplicitContextUI",
        "ProactiveClarificationUI",
        "AIBudgetNotifications",
        "GreetingHandler"
    ]
    
    for module in expected_modules:
        loaded = page.evaluate(f"(name) => typeof window[name] !== 'undefined'", module)
        modules_loaded[module] = loaded
        print(f"✓ {module}: {'loaded' if loaded else 'NOT loaded'}")
    
    # All modules should be loaded
    for module, loaded in modules_loaded.items():
        assert loaded, f"{module} should be loaded on user_logon page"

def test_explicit_context_panel_exists(page: Page):
    """Test that explicit context panel exists"""
    page.goto("http://localhost:5050/user_logon")
    page.wait_for_selector("#login-screen", state="visible")
    
    panel = page.locator("#explicit-context-panel")
    assert panel.count() > 0, "explicit-context-panel should exist on user_logon page"

def test_chat_input_exists(page: Page):
    """Test that chat-input exists (user_logon page uses this, not userInput)"""
    page.goto("http://localhost:5050/user_logon")
    page.wait_for_selector("#login-screen", state="visible")
    
    chat_input = page.locator("#chat-input")
    assert chat_input.count() > 0, "chat-input should exist on user_logon page"
    
    user_input = page.locator("#userInput")
    assert user_input.count() == 0, "userInput should NOT exist on user_logon page"

def test_no_critical_js_errors(page: Page):
    """Test that there are no critical JavaScript errors (ignoring 401 auth errors)"""
    console_messages = []
    page.on("console", lambda msg: console_messages.append(msg))
    
    page.goto("http://localhost:5050/user_logon")
    page.wait_for_selector("#login-screen", state="visible")
    page.wait_for_timeout(2000)
    
    # Filter out expected 401 errors (from greeting handler trying to authenticate)
    critical_errors = [msg for msg in console_messages 
                      if msg.type == "error" 
                      and "401" not in msg.text 
                      and "UNAUTHORIZED" not in msg.text]
    
    error_texts = [msg.text for msg in critical_errors]
    assert len(critical_errors) == 0, f"Critical JavaScript errors: {error_texts}"
