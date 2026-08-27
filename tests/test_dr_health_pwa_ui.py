"""
Browser UI tests for the Dr. Health PWA hub, driven with Playwright.

Creates a brand new user, logs in through the real login form on a mobile
viewport, then exercises the hub navigation, every section page, and the
add / edit / delete flows. Console errors are collected for the whole run.

    python tests/test_dr_health_pwa_ui.py [base_url]
"""
import sys
import time
import uuid

import requests
from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'

LIST_SECTIONS = [
    'conditions', 'symptoms', 'medications', 'supplements', 'test_results',
    'action_plans', 'follow_ups', 'questions_for_doctor', 'provider_notes',
    'conversation_insights',
]
OBJECT_SECTIONS = ['personal', 'diet', 'lifestyle']
TOOL_SECTIONS = ['interactions', 'ai_summary', 'settings']
ALL_SECTIONS = ['vitals'] + OBJECT_SECTIONS[:1] + LIST_SECTIONS + OBJECT_SECTIONS[1:] + TOOL_SECTIONS


class Report:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []

    def check(self, name, ok, detail=''):
        if ok:
            self.passed += 1
            print(f'  PASS  {name}')
        else:
            self.failed += 1
            self.failures.append((name, detail))
            print(f'  FAIL  {name}  -> {detail}')
        return ok

    def section(self, title):
        print(f'\n=== {title} ===')

    def summary(self):
        total = self.passed + self.failed
        print('\n' + '=' * 60)
        print(f'TOTAL {total}   PASSED {self.passed}   FAILED {self.failed}')
        if self.failures:
            print('\nFailures:')
            for name, detail in self.failures:
                print(f'  - {name}: {detail}')
        print('=' * 60)
        return self.failed == 0


def make_user():
    suffix = uuid.uuid4().hex[:10]
    username = f'uitest_{suffix}'
    resp = requests.post(f'{BASE_URL}/api/auth/signup', timeout=60, json={
        'username': username,
        'email': f'{username}@example.com',
        'password': 'TestPass123!',
    })
    resp.raise_for_status()
    return username, 'TestPass123!'


def open_section(page, section_id):
    page.click(f'.hub-card[data-section="{section_id}"]')
    page.wait_for_selector('#hub-back', timeout=10000)


def back_to_index(page):
    page.click('#hub-back')
    page.wait_for_selector('.hub-card', timeout=10000)


def run():
    r = Report()

    r.section('1. Create user')
    username, password = make_user()
    print(f'        created {username}')

    console_errors = []
    page_errors = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={'width': 393, 'height': 851},
            device_scale_factor=2.75,
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()
        page.on('console', lambda m: console_errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: page_errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())

        # ---------- 2. Login ----------
        r.section('2. Login screen')
        page.goto(f'{BASE_URL}/dr-health', wait_until='networkidle', timeout=60000)
        r.check('login screen visible', page.is_visible('#login-screen'))
        r.check('username field present', page.is_visible('#login-username'))
        r.check('password field present', page.is_visible('#login-password'))

        page.fill('#login-username', username)
        page.fill('#login-password', password)
        page.click('#login-btn')
        page.wait_for_selector('#login-screen.hidden', state='attached', timeout=30000)
        r.check('login hides the login screen', not page.is_visible('#login-screen'))
        page.wait_for_selector('#chat-screen.active', timeout=30000)
        r.check('chat screen active after login',
                page.is_visible('#chat-screen'), 'chat screen not shown')
        r.check('auth token stored',
                bool(page.evaluate("localStorage.getItem('authToken')")), 'no token')

        # ---------- 3. Bottom nav ----------
        r.section('3. Bottom navigation')
        tabs = page.eval_on_selector_all(
            '.nav-btn', 'els => els.map(e => e.dataset.target)')
        r.check('three tabs present', len(tabs) == 3, str(tabs))
        r.check('Health tab exists', 'hub-screen' in tabs, str(tabs))
        r.check('Records tab exists', 'profile-screen' in tabs, str(tabs))

        page.click('.nav-btn[data-target="hub-screen"]')
        page.wait_for_selector('.hub-card', timeout=15000)
        r.check('Health tab opens the hub', page.is_visible('#hub-screen'))
        r.check('top bar title updates',
                page.inner_text('#topbar-title').strip() == 'My Health',
                page.inner_text('#topbar-title'))

        # ---------- 4. Hub index ----------
        r.section('4. Hub index')
        cards = page.eval_on_selector_all(
            '.hub-card', 'els => els.map(e => e.dataset.section)')
        r.check(f'all {len(ALL_SECTIONS)} section cards render',
                len(cards) == len(ALL_SECTIONS), f'got {len(cards)}: {cards}')
        for sid in ALL_SECTIONS:
            r.check(f'card "{sid}" present', sid in cards, str(cards))

        groups = page.eval_on_selector_all(
            '.hub-group-label', 'els => els.map(e => e.textContent.trim())')
        r.check('five group headings', len(groups) == 5, str(groups))

        r.check('every list card shows a count badge',
                page.eval_on_selector_all(
                    '.hub-card[data-section="conditions"] .hub-badge', 'e => e.length') == 1,
                'badge missing')

        sticky = page.eval_on_selector(
            '.hub-subheader', 'e => getComputedStyle(e).position')
        r.check('sub-header is sticky', sticky == 'sticky', sticky)

        # ---------- 5. Every section opens ----------
        r.section('5. Every section opens and returns')
        for sid in ALL_SECTIONS:
            before = len(page_errors)
            try:
                open_section(page, sid)
                title = page.inner_text('.hub-sub-title').strip()
                ok = bool(title) and len(page_errors) == before
                r.check(f'{sid}: opens ("{title}")', ok,
                        page_errors[before:] if len(page_errors) > before else 'empty title')
                back_to_index(page)
            except Exception as e:
                r.check(f'{sid}: opens', False, str(e)[:200])
                page.click('.nav-btn[data-target="hub-screen"]')
                page.wait_for_selector('.hub-card', timeout=10000)

        # ---------- 6. Empty state + add ----------
        r.section('6. Add flow (conditions)')
        open_section(page, 'conditions')
        r.check('empty state shown', page.is_visible('.hub-empty'))
        r.check('back button present', page.is_visible('#hub-back'))
        r.check('add button present', page.is_visible('#hub-add'))

        page.click('#hub-add')
        page.wait_for_selector('.hub-form', timeout=10000)
        r.check('add form opens', page.is_visible('.hub-form'))
        r.check('form has the Condition field', page.is_visible('#hf-name'))
        r.check('form has a status dropdown', page.is_visible('select#hf-status'))
        r.check('form has a date picker',
                page.get_attribute('#hf-diagnosed_date', 'type') == 'date')

        # required-field validation
        page.click('[data-save]')
        page.wait_for_timeout(400)
        r.check('empty required field is rejected',
                'required' in page.inner_text('#hub-status').lower(),
                page.inner_text('#hub-status'))

        page.fill('#hf-name', 'Playwright Condition')
        page.select_option('select#hf-status', 'active')
        page.fill('#hf-diagnosed_date', '2024-06-01')
        page.fill('#hf-details', 'Created by the UI test')
        page.click('[data-save]')
        page.wait_for_selector('.hub-row', timeout=15000)
        r.check('row appears after save', page.is_visible('.hub-row'))
        r.check('row shows the title',
                'Playwright Condition' in page.inner_text('.hub-row-title'),
                page.inner_text('.hub-row-title'))
        r.check('status pill rendered', page.is_visible('.hub-pill'))

        # ---------- 7. Expand + edit ----------
        r.section('7. Expand and edit')
        page.click('.hub-row-head')
        page.wait_for_selector('.hub-row-body', timeout=10000)
        r.check('row expands', page.is_visible('.hub-row-body'))
        body_text = page.inner_text('.hub-row-body')
        r.check('expanded row shows details', 'Created by the UI test' in body_text, body_text[:150])
        r.check('expanded row shows the date', '2024-06-01' in body_text, body_text[:150])
        r.check('Edit button present', page.is_visible('[data-edit]'))
        r.check('Delete button present', page.is_visible('[data-delete]'))

        page.click('[data-edit]')
        page.wait_for_selector('.hub-form', timeout=10000)
        r.check('edit form prefills the name',
                page.input_value('#hf-name') == 'Playwright Condition',
                page.input_value('#hf-name'))
        page.select_option('select#hf-status', 'resolved')
        page.click('[data-save]')
        page.wait_for_selector('.hub-row', timeout=15000)
        r.check('edited status persisted in UI',
                'resolved' in page.inner_text('.hub-row').lower(),
                page.inner_text('.hub-row')[:150])

        resp = requests.get(
            f'{BASE_URL}/api/health-profile',
            headers={'Authorization': 'Bearer ' + page.evaluate("localStorage.getItem('authToken')")},
            timeout=60)
        conds = resp.json().get('profile', {}).get('conditions', [])
        r.check('edit persisted to the server',
                len(conds) == 1 and conds[0].get('status') == 'resolved', str(conds))

        # ---------- 8. Badge count ----------
        r.section('8. Badge counts')
        back_to_index(page)
        badge = page.inner_text('.hub-card[data-section="conditions"] .hub-badge').strip()
        r.check('conditions badge reads 1', badge == '1', badge)

        # ---------- 9. Filter bar ----------
        r.section('9. Filter bar appears past 6 rows')
        token = page.evaluate("localStorage.getItem('authToken')")
        for i in range(7):
            requests.post(f'{BASE_URL}/api/health-profile/item',
                          headers={'Authorization': f'Bearer {token}'}, timeout=60,
                          json={'category': 'symptoms',
                                'item': {'description': f'UI symptom {i}', 'severity': 'mild'}})
        page.click('#hub-refresh')
        page.wait_for_timeout(1200)
        open_section(page, 'symptoms')
        r.check('filter bar shown for long lists', page.is_visible('#hub-filter'))
        r.check('all 7 rows render',
                page.eval_on_selector_all('.hub-row', 'e => e.length') == 7,
                str(page.eval_on_selector_all('.hub-row', 'e => e.length')))
        page.fill('#hub-filter', 'symptom 3')
        page.wait_for_timeout(400)
        r.check('filter narrows the list',
                page.eval_on_selector_all('.hub-row', 'e => e.length') == 1,
                str(page.eval_on_selector_all('.hub-row', 'e => e.length')))
        page.fill('#hub-filter', '')
        page.wait_for_timeout(400)
        back_to_index(page)

        # ---------- 10. Grouped test results ----------
        r.section('10. Grouped lab results')
        for date, val in [('2024-01-01', '30 ug/L'), ('2024-06-01', '45 ug/L')]:
            requests.post(f'{BASE_URL}/api/health-profile/item',
                          headers={'Authorization': f'Bearer {token}'}, timeout=60,
                          json={'category': 'test_results',
                                'item': {'test_name': 'UI FERRITIN', 'value': val,
                                         'reference_range': '30-300', 'date': date}})
        page.click('#hub-refresh')
        page.wait_for_timeout(1200)
        open_section(page, 'test_results')
        r.check('results are grouped by test name', page.is_visible('.hub-tgroup'))
        r.check('group header shows the test name',
                'UI FERRITIN' in page.inner_text('.hub-tgroup-name'),
                page.inner_text('.hub-tgroup-name'))
        r.check('group shows both dated rows',
                page.eval_on_selector_all('.hub-tgroup .hub-row', 'e => e.length') == 2,
                str(page.eval_on_selector_all('.hub-tgroup .hub-row', 'e => e.length')))
        r.check('newest result is listed first',
                '2024-06-01' in page.eval_on_selector_all(
                    '.hub-tgroup .hub-row-title', 'e => e.map(x => x.textContent)')[0],
                str(page.eval_on_selector_all(
                    '.hub-tgroup .hub-row-title', 'e => e.map(x => x.textContent)')))
        back_to_index(page)

        # ---------- 11. Object sections ----------
        r.section('11. Object section editing')
        open_section(page, 'personal')
        page.fill('#hf-age', '52')
        page.fill('#hf-blood_type', 'A-')
        page.click('#hub-obj-save')
        page.wait_for_timeout(1200)
        r.check('personal save confirms',
                'saved' in page.inner_text('#hub-status').lower(),
                page.inner_text('#hub-status'))
        prof = requests.get(f'{BASE_URL}/api/health-profile',
                            headers={'Authorization': f'Bearer {token}'},
                            timeout=60).json().get('profile', {})
        r.check('personal persisted to the server',
                str(prof.get('personal', {}).get('blood_type')) == 'A-',
                str(prof.get('personal')))
        back_to_index(page)

        open_section(page, 'diet')
        page.fill('#hf-restrictions', 'dairy\nshellfish')
        page.click('#hub-obj-save')
        page.wait_for_timeout(1200)
        prof = requests.get(f'{BASE_URL}/api/health-profile',
                            headers={'Authorization': f'Bearer {token}'},
                            timeout=60).json().get('profile', {})
        r.check('multi-line list field splits into an array',
                prof.get('diet', {}).get('restrictions') == ['dairy', 'shellfish'],
                str(prof.get('diet', {}).get('restrictions')))
        back_to_index(page)

        # ---------- 12. Tools ----------
        r.section('12. Tool pages')
        open_section(page, 'ai_summary')
        page.wait_for_timeout(2000)
        r.check('AI summary renders content',
                page.is_visible('.hub-pre') or page.is_visible('.hub-note'),
                page.inner_text('.hub-scroll')[:150])
        back_to_index(page)

        open_section(page, 'interactions')
        page.wait_for_timeout(3000)
        r.check('interactions page renders a result',
                page.is_visible('.hub-note'), page.inner_text('.hub-scroll')[:150])
        back_to_index(page)

        open_section(page, 'settings')
        page.fill('#hub-retention', '120')
        page.click('#hub-settings-save')
        page.wait_for_timeout(1200)
        prof = requests.get(f'{BASE_URL}/api/health-profile',
                            headers={'Authorization': f'Bearer {token}'},
                            timeout=60).json().get('profile', {})
        r.check('retention setting saves from the UI',
                prof.get('upload_settings', {}).get('retention_days') == 120,
                str(prof.get('upload_settings')))
        back_to_index(page)

        # ---------- 13. Emergency card ----------
        r.section('13. Emergency card')
        open_section(page, 'vitals')
        page.click('#hub-open-vitals')
        page.wait_for_timeout(1500)
        r.check('emergency modal opens from the hub',
                page.is_visible('#emergency-modal.active'), 'modal not active')
        page.click('#emergency-close')
        page.wait_for_timeout(500)
        r.check('emergency modal closes',
                not page.is_visible('#emergency-modal.active'))
        back_to_index(page)

        # ---------- 14. Delete ----------
        r.section('14. Delete flow')
        open_section(page, 'conditions')
        page.click('.hub-row-head')
        page.wait_for_selector('[data-delete]', timeout=10000)
        page.click('[data-delete]')
        page.wait_for_timeout(1500)
        r.check('empty state returns after delete', page.is_visible('.hub-empty'))
        conds = requests.get(f'{BASE_URL}/api/health-profile',
                             headers={'Authorization': f'Bearer {token}'},
                             timeout=60).json().get('profile', {}).get('conditions', [])
        r.check('delete persisted to the server', conds == [], str(conds))
        back_to_index(page)

        # ---------- 15. Records tab ----------
        r.section('15. Records tab')
        page.click('.nav-btn[data-target="profile-screen"]')
        page.wait_for_timeout(1500)
        r.check('records screen visible', page.is_visible('#profile-screen'))
        r.check('paste box present', page.is_visible('#profile-text'))
        r.check('file upload present', page.is_visible('#profile-file'))
        r.check('advanced editor button present', page.is_visible('#data-manager-btn'))
        r.check('full overview collapsed by default',
                page.eval_on_selector('#overview-card', 'e => !e.open'))
        page.click('#overview-card summary')
        page.wait_for_timeout(800)
        r.check('full overview expands',
                page.eval_on_selector('#overview-card', 'e => e.open'))

        page.click('#data-manager-btn')
        page.wait_for_timeout(2000)
        r.check('advanced data manager opens',
                page.is_visible('#data-manager-modal.active'), 'modal not active')
        page.click('#dm-close')
        page.wait_for_timeout(500)

        # ---------- 16. Persistence across reload ----------
        r.section('16. Reload persistence')
        page.reload(wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(2000)
        r.check('stays logged in after reload',
                not page.is_visible('#login-screen'), 'login screen shown again')
        page.click('.nav-btn[data-target="hub-screen"]')
        page.wait_for_selector('.hub-card', timeout=15000)
        badge = page.inner_text('.hub-card[data-section="symptoms"] .hub-badge').strip()
        r.check('symptom count survives reload', badge == '7', badge)

        # ---------- 17. Console ----------
        r.section('17. Console health')
        ignorable = ('favicon', 'manifest', 'net::ERR_INTERNET_DISCONNECTED')
        real_console = [e for e in console_errors if not any(i in e for i in ignorable)]
        r.check('no uncaught page exceptions', not page_errors, str(page_errors[:3]))
        r.check('no console errors', not real_console, str(real_console[:3]))

        browser.close()

    return r.summary()


if __name__ == '__main__':
    print(f'Testing {BASE_URL}')
    t0 = time.time()
    ok = run()
    print(f'Finished in {time.time() - t0:.1f}s')
    sys.exit(0 if ok else 1)
