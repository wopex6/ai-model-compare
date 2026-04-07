"""
Playwright UI tests for previously untested features:
  - Onboarding page (persona cards, CTA, skip)
  - Login/signup form structure + password toggle
  - FOUC prevention (localStorage persona applied instantly)
  - themes.css loading on all pages
  - Dashboard HTML structure (tabs, chat, settings persona picker)
  - Chat UI elements (welcome msg, typing indicator, personality presets)
  - Dark/light theme toggle (ThemeManager)

All tests run without authentication because:
- /onboarding is publicly accessible
- /user_logon renders the full HTML (including hidden dashboard) on first load
  so structural assertions work before login
"""
import pytest
from playwright.sync_api import Page, expect

BASE = "http://localhost:5050"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def goto_logon(page: Page):
    page.goto(f"{BASE}/user_logon")
    page.wait_for_selector("#login-screen", state="visible")
    page.wait_for_timeout(1500)   # let scripts finish executing

def goto_onboarding(page: Page):
    page.goto(f"{BASE}/onboarding")
    page.wait_for_selector(".persona-grid", state="visible")
    page.wait_for_timeout(1000)


# ─────────────────────────────────────────────
# 1. ONBOARDING PAGE
# ─────────────────────────────────────────────

class TestOnboardingPage:

    def test_page_loads_with_title(self, page: Page):
        goto_onboarding(page)
        assert "Welcome" in page.title() or "Experience" in page.title()

    def test_hero_heading_present(self, page: Page):
        goto_onboarding(page)
        hero = page.locator(".onboard-hero h1")
        expect(hero).to_be_visible()
        assert len(hero.inner_text()) > 10

    def test_all_four_persona_cards_present(self, page: Page):
        goto_onboarding(page)
        cards = page.locator(".persona-card")
        assert cards.count() == 4

    def test_each_persona_card_has_correct_data_attr(self, page: Page):
        goto_onboarding(page)
        for persona in ["serenity", "momentum", "odyssey", "spark"]:
            card = page.locator(f".persona-card[data-persona='{persona}']")
            assert card.count() == 1, f"Missing card for persona: {persona}"

    def test_cta_button_disabled_before_selection(self, page: Page):
        goto_onboarding(page)
        btn = page.locator("#btn-start")
        expect(btn).to_be_visible()
        # Before selection, button has pointer-events:none via .btn-start (no .ready class)
        has_ready = page.evaluate("() => document.getElementById('btn-start').classList.contains('ready')")
        assert not has_ready, "CTA button should be disabled before a persona is selected"

    def test_selecting_card_enables_cta(self, page: Page):
        goto_onboarding(page)
        page.locator(".persona-card[data-persona='spark']").click()
        page.wait_for_timeout(300)
        has_ready = page.evaluate("() => document.getElementById('btn-start').classList.contains('ready')")
        assert has_ready, "CTA button should be enabled after selecting a persona"

    def test_selecting_card_marks_it_selected(self, page: Page):
        goto_onboarding(page)
        page.locator(".persona-card[data-persona='momentum']").click()
        page.wait_for_timeout(300)
        selected = page.locator(".persona-card.selected")
        assert selected.count() == 1
        assert selected.get_attribute("data-persona") == "momentum"

    def test_selecting_card_applies_data_persona_to_html(self, page: Page):
        goto_onboarding(page)
        page.locator(".persona-card[data-persona='serenity']").click()
        page.wait_for_timeout(300)
        attr = page.evaluate("() => document.documentElement.dataset.persona")
        assert attr == "serenity"

    def test_check_badge_visible_only_on_selected_card(self, page: Page):
        goto_onboarding(page)
        page.locator(".persona-card[data-persona='odyssey']").click()
        page.wait_for_timeout(300)
        # Only the odyssey card should carry the 'selected' class (which drives badge display)
        selected = page.locator(".persona-card.selected")
        assert selected.count() == 1
        assert selected.get_attribute("data-persona") == "odyssey"
        # All other cards must NOT have .selected
        for persona in ["serenity", "momentum", "spark"]:
            has_selected = page.evaluate(
                "(p) => document.querySelector(`[data-persona='${p}']`).classList.contains('selected')",
                persona
            )
            assert not has_selected, f"Card '{persona}' should not be selected"

    def test_preview_strip_updated_after_selection(self, page: Page):
        goto_onboarding(page)
        page.locator(".persona-card[data-persona='spark']").click()
        page.wait_for_timeout(300)
        strip = page.locator("#preview-strip")
        # Strip should now contain colour dots
        dots = strip.locator(".color-dot")
        assert dots.count() >= 3, "Preview strip should show colour dots after selection"

    def test_skip_button_present(self, page: Page):
        goto_onboarding(page)
        skip = page.locator("button.skip")
        expect(skip).to_be_visible()
        assert "skip" in skip.inner_text().lower() or "explore" in skip.inner_text().lower()

    def test_themes_css_loaded_on_onboarding(self, page: Page):
        goto_onboarding(page)
        loaded = page.evaluate(
            "() => Array.from(document.styleSheets).some(s => s.href && s.href.includes('themes.css'))"
        )
        assert loaded, "themes.css should be loaded on the onboarding page"


# ─────────────────────────────────────────────
# 2. LOGIN PAGE STRUCTURE
# ─────────────────────────────────────────────

class TestLoginPageStructure:

    def test_login_screen_visible_on_load(self, page: Page):
        goto_logon(page)
        expect(page.locator("#login-screen")).to_be_visible()

    def test_login_form_exists(self, page: Page):
        goto_logon(page)
        expect(page.locator("#login-form")).to_be_visible()

    def test_username_and_password_fields_present(self, page: Page):
        goto_logon(page)
        expect(page.locator("#login-username")).to_be_visible()
        expect(page.locator("#login-password")).to_be_visible()

    def test_password_field_type_is_password(self, page: Page):
        goto_logon(page)
        field_type = page.locator("#login-password").get_attribute("type")
        assert field_type == "password"

    def test_password_toggle_button_present(self, page: Page):
        goto_logon(page)
        toggle = page.locator("#password-toggle")
        expect(toggle).to_be_visible()
        assert "show" in toggle.inner_text().lower()

    def test_password_toggle_reveals_password(self, page: Page):
        goto_logon(page)
        page.fill("#login-password", "mysecretpw")
        page.click("#password-toggle")
        page.wait_for_timeout(200)
        field_type = page.locator("#login-password").get_attribute("type")
        assert field_type == "text", "Password should be revealed after toggle"

    def test_password_toggle_hides_again(self, page: Page):
        goto_logon(page)
        page.fill("#login-password", "mysecretpw")
        page.click("#password-toggle")  # reveal
        page.wait_for_timeout(200)
        page.click("#password-toggle")  # hide again
        page.wait_for_timeout(200)
        field_type = page.locator("#login-password").get_attribute("type")
        assert field_type == "password", "Password should be hidden again after second toggle"

    def test_remember_username_checkbox_present(self, page: Page):
        goto_logon(page)
        expect(page.locator("#remember-username")).to_be_attached()

    def test_submit_button_present(self, page: Page):
        goto_logon(page)
        btn = page.locator("#login-form button[type='submit']")
        expect(btn).to_be_visible()
        assert "login" in btn.inner_text().lower()

    def test_themes_css_loaded_on_login_page(self, page: Page):
        goto_logon(page)
        loaded = page.evaluate(
            "() => Array.from(document.styleSheets).some(s => s.href && s.href.includes('themes.css'))"
        )
        assert loaded, "themes.css should be loaded on the user_logon page"


# ─────────────────────────────────────────────
# 3. FOUC PREVENTION (persona from localStorage)
# ─────────────────────────────────────────────

class TestFOUCPrevention:

    def test_no_persona_in_localstorage_leaves_no_attribute(self, page: Page):
        # Clear localStorage before visiting
        page.goto(f"{BASE}/user_logon")
        page.evaluate("() => localStorage.removeItem('persona')")
        page.goto(f"{BASE}/user_logon")
        page.wait_for_selector("#login-screen", state="visible")
        attr = page.evaluate("() => document.documentElement.dataset.persona || null")
        assert attr is None or attr == "", "No persona attribute when localStorage is empty"

    def test_persona_in_localstorage_applied_before_dom_ready(self, page: Page):
        # Set persona in localStorage before page load
        page.goto(f"{BASE}/user_logon")
        page.evaluate("() => localStorage.setItem('persona', 'serenity')")
        # Navigate fresh — FOUC script runs before DOMContentLoaded
        page.goto(f"{BASE}/user_logon")
        page.wait_for_selector("#login-screen", state="visible")
        attr = page.evaluate("() => document.documentElement.dataset.persona")
        assert attr == "serenity", f"Expected 'serenity', got '{attr}'"

    def test_all_four_personas_apply_correctly(self, page: Page):
        for persona in ["serenity", "momentum", "odyssey", "spark"]:
            page.goto(f"{BASE}/user_logon")
            page.evaluate(f"() => localStorage.setItem('persona', '{persona}')")
            page.goto(f"{BASE}/user_logon")
            page.wait_for_selector("#login-screen", state="visible")
            attr = page.evaluate("() => document.documentElement.dataset.persona")
            assert attr == persona, f"FOUC prevention failed for persona '{persona}'"

    def test_fouc_script_is_inline_before_body(self, page: Page):
        goto_logon(page)
        # Verify the FOUC inline script is present in the page HTML
        content = page.content()
        assert "localStorage.getItem('persona')" in content
        assert "dataset.persona" in content


# ─────────────────────────────────────────────
# 4. DASHBOARD HTML STRUCTURE (hidden, no auth needed)
# ─────────────────────────────────────────────

class TestDashboardStructure:

    def test_dashboard_nav_tabs_exist_in_dom(self, page: Page):
        goto_logon(page)
        for tab in ["chat", "profile", "psychology", "settings"]:
            btn = page.locator(f".nav-btn[data-tab='{tab}']")
            assert btn.count() > 0, f"Nav tab '{tab}' not found in DOM"

    def test_logout_button_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#logout-btn").count() > 0

    def test_nav_username_element_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#nav-username").count() > 0

    def test_chat_tab_content_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#chat-tab").count() > 0

    def test_profile_tab_content_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#profile-tab").count() > 0

    def test_psychology_tab_content_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#psychology-tab").count() > 0

    def test_settings_tab_content_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#settings-tab").count() > 0

    def test_email_verification_banner_in_dom(self, page: Page):
        goto_logon(page)
        assert page.locator("#email-verification-banner").count() > 0

    def test_personality_test_banner_in_dom(self, page: Page):
        goto_logon(page)
        assert page.locator("#personality-test-banner").count() > 0


# ─────────────────────────────────────────────
# 5. CHAT UI ELEMENTS
# ─────────────────────────────────────────────

class TestChatUIElements:

    def test_chat_messages_container_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#chat-messages").count() > 0

    def test_welcome_message_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#chat-messages .welcome-message").count() > 0

    def test_typing_indicator_exists_and_hidden(self, page: Page):
        goto_logon(page)
        indicator = page.locator("#typingIndicator")
        assert indicator.count() > 0
        # Should be hidden by default
        display = page.evaluate("() => document.getElementById('typingIndicator').style.display")
        assert display == "none"

    def test_chat_input_textarea_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#chat-input").count() > 0

    def test_send_chat_button_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#send-chat-btn").count() > 0

    def test_explicit_context_panel_exists_and_hidden(self, page: Page):
        goto_logon(page)
        panel = page.locator("#explicit-context-panel")
        assert panel.count() > 0
        # Before login/init, should be hidden
        display = page.evaluate("() => document.getElementById('explicit-context-panel').style.display")
        assert display == "none"

    def test_personality_presets_exist(self, page: Page):
        goto_logon(page)
        presets = page.locator(".personality-preset")
        assert presets.count() >= 4, "Should have at least 4 personality preset buttons"

    def test_personality_presets_have_correct_values(self, page: Page):
        goto_logon(page)
        for preset in ["helpful_assistant", "creative_mentor", "technical_expert", "curious_explorer"]:
            el = page.locator(f".personality-preset[data-preset='{preset}']")
            assert el.count() == 1, f"Missing preset: {preset}"

    def test_helpful_preset_active_by_default(self, page: Page):
        goto_logon(page)
        active = page.locator(".personality-preset.active")
        assert active.count() == 1
        assert active.get_attribute("data-preset") == "helpful_assistant"

    def test_sound_toggle_button_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#toggle-sound-quick").count() > 0

    def test_summary_button_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#showSummaryBtn").count() > 0

    def test_new_chat_button_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#new-chat-btn").count() > 0

    def test_message_usage_info_container_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#message-usage-info").count() > 0


# ─────────────────────────────────────────────
# 6. SETTINGS PERSONA PICKER
# ─────────────────────────────────────────────

class TestSettingsPersonaPicker:

    def test_persona_picker_exists_in_dom(self, page: Page):
        goto_logon(page)
        assert page.locator("#persona-picker").count() > 0

    def test_persona_picker_has_four_options(self, page: Page):
        goto_logon(page)
        options = page.locator("#persona-picker .persona-option")
        assert options.count() == 4

    def test_each_persona_option_has_correct_data_attr(self, page: Page):
        goto_logon(page)
        for persona in ["serenity", "momentum", "odyssey", "spark"]:
            el = page.locator(f"#persona-picker .persona-option[data-persona='{persona}']")
            assert el.count() == 1, f"Missing persona option: {persona}"

    def test_each_persona_option_has_radio_input(self, page: Page):
        goto_logon(page)
        radios = page.locator("#persona-picker input[type='radio'][name='persona-radio']")
        assert radios.count() == 4

    def test_persona_picker_has_icon_for_each_option(self, page: Page):
        goto_logon(page)
        # Each option should have a Font Awesome icon
        icons = page.locator("#persona-picker .persona-option i.fas")
        assert icons.count() == 4


# ─────────────────────────────────────────────
# 7. DARK / LIGHT THEME TOGGLE (ThemeManager)
# ─────────────────────────────────────────────

class TestThemeManager:

    def test_theme_toggle_button_injected(self, page: Page):
        goto_logon(page)
        # ThemeManager creates a .theme-toggle button on DOMContentLoaded
        toggle = page.locator(".theme-toggle")
        assert toggle.count() > 0, "ThemeManager should inject a .theme-toggle button"

    def test_default_theme_attribute_set(self, page: Page):
        goto_logon(page)
        theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        assert theme in ["light", "dark"], f"Expected light or dark, got: {theme}"

    def test_clicking_toggle_switches_theme(self, page: Page):
        goto_logon(page)
        initial_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        page.locator(".theme-toggle").click()
        page.wait_for_timeout(200)
        new_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        assert new_theme != initial_theme, "Theme should change after clicking toggle"
        assert new_theme in ["light", "dark"]

    def test_theme_toggle_switches_back(self, page: Page):
        goto_logon(page)
        initial_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        page.locator(".theme-toggle").click()
        page.wait_for_timeout(200)
        page.locator(".theme-toggle").click()
        page.wait_for_timeout(200)
        restored_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        assert restored_theme == initial_theme, "Theme should toggle back to original"

    def test_theme_persisted_in_localstorage(self, page: Page):
        goto_logon(page)
        page.locator(".theme-toggle").click()
        page.wait_for_timeout(200)
        stored = page.evaluate("() => localStorage.getItem('app_theme')")
        assert stored in ["light", "dark"], f"Theme should be saved in localStorage, got: {stored}"

    def test_theme_restored_on_reload(self, page: Page):
        goto_logon(page)
        page.evaluate("() => localStorage.setItem('app_theme', 'dark')")
        page.goto(f"{BASE}/user_logon")
        page.wait_for_selector("#login-screen", state="visible")
        page.wait_for_timeout(1000)
        theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        assert theme == "dark", "Dark theme should be restored from localStorage"


# ─────────────────────────────────────────────
# 8. PROFILE TAB STRUCTURE
# ─────────────────────────────────────────────

class TestProfileTabStructure:

    def test_profile_nav_buttons_exist(self, page: Page):
        goto_logon(page)
        for page_name in ["personal", "preferences", "privacy"]:
            btn = page.locator(f".profile-nav-btn[data-page='{page_name}']")
            assert btn.count() > 0, f"Profile nav button for '{page_name}' not found"

    def test_personal_info_form_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#personal-info-form").count() > 0

    def test_personal_info_fields_exist(self, page: Page):
        goto_logon(page)
        for field_id in ["personal-name", "personal-email", "personal-age", "personal-location", "personal-occupation"]:
            assert page.locator(f"#{field_id}").count() > 0, f"Missing field: #{field_id}"

    def test_preferences_form_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#preferences-form").count() > 0

    def test_privacy_form_exists(self, page: Page):
        goto_logon(page)
        assert page.locator("#privacy-form").count() > 0

    def test_privacy_checkboxes_exist(self, page: Page):
        goto_logon(page)
        for cb_id in ["privacy-data-sharing", "privacy-analytics", "privacy-personalization", "privacy-marketing"]:
            assert page.locator(f"#{cb_id}").count() > 0, f"Missing checkbox: #{cb_id}"
