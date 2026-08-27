"""
Live AI flow tests for the Dr. Health PWA.

These hit real model providers, so they are slower and kept separate from the
fast API/UI suites. Covers the chat round-trip (including that the AI receives
the user's health context) and the paste -> analyze -> review -> apply ingest
pipeline.

    python tests/test_dr_health_pwa_ai_flows.py [base_url]
"""
import json
import sys
import time
import uuid

import requests
from playwright.sync_api import sync_playwright

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
AI_TIMEOUT = 180


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


def body(resp):
    try:
        return resp.json()
    except Exception:
        return {'_raw': resp.text[:400]}


def run():
    r = Report()
    s = requests.Session()

    r.section('1. New user')
    suffix = uuid.uuid4().hex[:10]
    username = f'aitest_{suffix}'
    password = 'TestPass123!'
    resp = s.post(f'{BASE_URL}/api/auth/signup', timeout=60, json={
        'username': username, 'email': f'{username}@example.com', 'password': password})
    data = body(resp)
    if not r.check('signup', resp.status_code == 200 and data.get('token'),
                   f'{resp.status_code} {data}'):
        r.summary()
        return False
    token = data['token']
    auth = {'Authorization': f'Bearer {token}'}
    print(f'        created {username}')

    # ---------- 2. Chat ----------
    r.section('2. Chat round-trip')
    resp = s.get(f'{BASE_URL}/medical_advisor/session', headers=auth, timeout=60)
    r.check('session endpoint responds', resp.status_code == 200, str(resp.status_code))

    t0 = time.time()
    resp = s.post(f'{BASE_URL}/medical_advisor/chat', headers=auth, timeout=AI_TIMEOUT,
                  json={'message': 'In one short sentence, what is a healthy resting heart rate?',
                        'include_context': True})
    elapsed = time.time() - t0
    data = body(resp)
    reply = data.get('response') or data.get('message') or ''
    r.check('chat returns 200', resp.status_code == 200, f'{resp.status_code} {str(data)[:200]}')
    r.check('chat returns a non-empty reply', len(reply.strip()) > 20, repr(reply[:120]))
    print(f'        replied in {elapsed:.1f}s: {reply[:90]!r}')

    resp = s.get(f'{BASE_URL}/medical_advisor/history', headers=auth, timeout=60)
    hist = body(resp)
    msgs = hist.get('messages') or hist.get('history') or []
    r.check('history endpoint responds', resp.status_code == 200, str(resp.status_code))
    r.check('history contains the exchange', len(msgs) >= 2, f'{len(msgs)} messages')

    # ---------- 3. Context injection ----------
    r.section('3. Health context reaches the AI')
    s.post(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=60,
           json={'category': 'medications',
                 'item': {'name': 'Zorbaxil', 'dose': '5mg', 'frequency': 'daily',
                          'purpose': 'test marker drug'}})
    summary = body(s.get(f'{BASE_URL}/api/health-profile/summary',
                         headers=auth, timeout=60)).get('summary', '')
    r.check('context summary includes the new medication', 'Zorbaxil' in summary, summary[:200])

    resp = s.post(f'{BASE_URL}/medical_advisor/chat', headers=auth, timeout=AI_TIMEOUT,
                  json={'message': 'List only the names of the medications you have on file '
                                   'for me. If none, say none.',
                        'include_context': True})
    reply = body(resp).get('response', '')
    r.check('AI can see the stored medication', 'zorbaxil' in reply.lower(), reply[:200])

    # ---------- 4. Paste -> analyze ----------
    r.section('4. Paste and analyze')
    pasted = (
        'Visit 12 March 2024. Blood pressure 138/86. '
        'Started on Metformin 500mg twice daily for type 2 diabetes. '
        'Serum ferritin 18 ug/L (ref 30-300) - low. '
        'Patient reports frequent morning headaches.'
    )
    t0 = time.time()
    resp = s.post(f'{BASE_URL}/api/health-profile/analyze', headers=auth,
                  timeout=AI_TIMEOUT, json={'text': pasted})
    data = body(resp)
    r.check('analyze returns 200', resp.status_code == 200,
            f'{resp.status_code} {str(data)[:200]}')
    extracted = data.get('extracted') or data.get('data') or {}
    print(f'        analyzed in {time.time() - t0:.1f}s')
    r.check('analyze returned structured data', isinstance(extracted, dict) and bool(extracted),
            str(data)[:250])

    blob = json.dumps(extracted).lower()
    r.check('extracted the medication', 'metformin' in blob, blob[:250])
    r.check('extracted the lab result', 'ferritin' in blob, blob[:250])

    # ---------- 5. Apply review ----------
    r.section('5. Apply reviewed data')
    resp = s.post(f'{BASE_URL}/api/health-profile/apply-review', headers=auth,
                  timeout=AI_TIMEOUT, json={'extracted': extracted})
    data = body(resp)
    r.check('apply-review returns 200', resp.status_code == 200,
            f'{resp.status_code} {str(data)[:200]}')

    prof = body(s.get(f'{BASE_URL}/api/health-profile', headers=auth, timeout=60)).get('profile', {})
    meds = json.dumps(prof.get('medications', [])).lower()
    tests = json.dumps(prof.get('test_results', [])).lower()
    r.check('medication landed in the profile', 'metformin' in meds, meds[:200])
    r.check('lab result landed in the profile', 'ferritin' in tests, tests[:200])

    # ---------- 6. Ingested data is editable in the hub ----------
    r.section('6. Ingested data is editable through the hub UI')
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={'width': 393, 'height': 851},
                                      is_mobile=True, has_touch=True)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: d.accept())

        page.goto(f'{BASE_URL}/dr-health', wait_until='networkidle', timeout=60000)
        page.fill('#login-username', username)
        page.fill('#login-password', password)
        page.click('#login-btn')
        page.wait_for_selector('#chat-screen.active', timeout=30000)
        page.click('.nav-btn[data-target="hub-screen"]')
        page.wait_for_selector('.hub-card', timeout=15000)

        badge = page.inner_text('.hub-card[data-section="medications"] .hub-badge').strip()
        r.check('medications badge counts the ingested rows', badge.isdigit() and int(badge) >= 2,
                badge)

        page.click('.hub-card[data-section="test_results"]')
        page.wait_for_selector('#hub-back', timeout=10000)
        text = page.inner_text('.hub-scroll')
        r.check('ingested lab result is visible in the hub',
                'ferritin' in text.lower(), text[:200])

        page.click('.hub-tgroup .hub-row-head')
        page.wait_for_selector('[data-edit]', timeout=10000)
        page.click('[data-edit]')
        page.wait_for_selector('#hf-notes', timeout=10000)
        page.fill('#hf-notes', 'reviewed by test')
        page.click('[data-save]')
        page.wait_for_timeout(2000)

        tests = json.dumps(body(s.get(f'{BASE_URL}/api/health-profile',
                                      headers=auth, timeout=60)).get('profile', {})
                           .get('test_results', []))
        r.check('edit to ingested lab result saved', 'reviewed by test' in tests, tests[:250])
        r.check('no page exceptions during ingest editing', not errors, str(errors[:2]))

        browser.close()

    return r.summary()


if __name__ == '__main__':
    print(f'Testing {BASE_URL}')
    t0 = time.time()
    ok = run()
    print(f'Finished in {time.time() - t0:.1f}s')
    sys.exit(0 if ok else 1)
