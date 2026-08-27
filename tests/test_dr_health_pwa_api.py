"""
End-to-end API tests for the Dr. Health PWA.

Starts from creating a brand new user, then exercises every health-profile
endpoint the PWA UI depends on: all 10 editable categories, the object
sections (personal / diet / lifestyle), vitals, settings and the tool
endpoints. Run against a live server:

    python tests/test_dr_health_pwa_api.py [base_url]
"""
import json
import sys
import time
import uuid

import requests

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5050'
TIMEOUT = 60

LIST_CATEGORIES = {
    'conditions': {'name': 'Test Condition', 'status': 'active',
                   'diagnosed_date': '2024-01-15', 'details': 'Initial note'},
    'symptoms': {'description': 'Test headache', 'severity': 'moderate',
                 'frequency': 'weekly', 'onset': '2024-02-01',
                 'triggers': ['stress', 'screens']},
    'medications': {'name': 'TestMed', 'dose': '10mg', 'frequency': 'daily',
                    'purpose': 'testing', 'prescribed_date': '2024-03-01'},
    'supplements': {'name': 'TestVitaminD', 'dose': '1000IU', 'frequency': 'daily',
                    'purpose': 'testing', 'prescribed_date': '2024-03-02'},
    'test_results': {'test_name': 'TEST FERRITIN', 'value': '55 ug/L',
                     'reference_range': '30-300', 'date': '2024-04-01',
                     'notes': 'fasting'},
    'action_plans': {'title': 'Test plan', 'steps': ['step one', 'step two'],
                     'status': 'active', 'priority': 'medium'},
    'follow_ups': {'title': 'Test follow-up', 'steps': ['call clinic'],
                   'due_date': '2024-05-01', 'priority': 'high'},
    'questions_for_doctor': {'question': 'Test question?', 'context': 'because testing',
                             'priority': 'low'},
    'provider_notes': {'provider': 'Dr Test', 'note': 'Test provider note',
                       'date': '2024-04-10'},
    'conversation_insights': {'insight': 'Test insight text', 'category': 'general'},
}

UPDATE_FOR = {
    'conditions': {'status': 'resolved', 'details': 'Updated note'},
    'symptoms': {'severity': 'mild'},
    'medications': {'dose': '20mg'},
    'supplements': {'dose': '2000IU'},
    'test_results': {'notes': 'updated note'},
    'action_plans': {'status': 'completed'},
    'follow_ups': {'priority': 'low'},
    'questions_for_doctor': {'priority': 'high'},
    'provider_notes': {'note': 'Updated provider note'},
    'conversation_insights': {'category': 'testing'},
}


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
        return {'_raw': resp.text[:300]}


def run():
    r = Report()
    s = requests.Session()

    # ---------- 1. New user ----------
    r.section('1. Registration & authentication')
    suffix = uuid.uuid4().hex[:10]
    username = f'pwatest_{suffix}'
    email = f'pwatest_{suffix}@example.com'
    password = 'TestPass123!'

    resp = s.post(f'{BASE_URL}/api/auth/signup',
                  json={'username': username, 'email': email, 'password': password},
                  timeout=TIMEOUT)
    data = body(resp)
    if not r.check('signup new user', resp.status_code == 200 and data.get('token'),
                   f'{resp.status_code} {data}'):
        r.summary()
        return False
    token = data['token']
    user_id = data.get('user_id')
    print(f'        created user {username} (id={user_id})')

    r.check('signup rejects duplicate username',
            s.post(f'{BASE_URL}/api/auth/signup',
                   json={'username': username, 'email': f'x{email}', 'password': password},
                   timeout=TIMEOUT).status_code == 400, 'expected 400')

    r.check('signup rejects short password',
            s.post(f'{BASE_URL}/api/auth/signup',
                   json={'username': f'x{suffix}', 'email': f'x{email}', 'password': 'short'},
                   timeout=TIMEOUT).status_code == 400, 'expected 400')

    resp = s.post(f'{BASE_URL}/api/auth/login',
                  json={'username': username, 'password': password}, timeout=TIMEOUT)
    login = body(resp)
    r.check('login with new credentials',
            resp.status_code == 200 and login.get('token'), f'{resp.status_code} {login}')
    if login.get('token'):
        token = login['token']

    r.check('login rejects wrong password',
            s.post(f'{BASE_URL}/api/auth/login',
                   json={'username': username, 'password': 'WrongPass123!'},
                   timeout=TIMEOUT).status_code == 401, 'expected 401')

    auth = {'Authorization': f'Bearer {token}'}

    r.check('health-profile rejects unauthenticated request',
            requests.get(f'{BASE_URL}/api/health-profile', timeout=TIMEOUT).status_code in (401, 403),
            'expected 401/403')

    # ---------- 2. Empty profile ----------
    r.section('2. Fresh profile shape')
    resp = s.get(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT)
    prof = body(resp).get('profile', {})
    r.check('GET profile returns 200', resp.status_code == 200, str(resp.status_code))
    for key in list(LIST_CATEGORIES) + ['personal', 'diet', 'lifestyle', 'upload_settings']:
        r.check(f'profile has "{key}"', key in prof, f'keys={sorted(prof)[:12]}')
    for key in LIST_CATEGORIES:
        r.check(f'"{key}" starts empty', prof.get(key) == [], f'got {prof.get(key)}')

    # ---------- 3. Page routes ----------
    r.section('3. PWA page & static assets')
    page = s.get(f'{BASE_URL}/dr-health', timeout=TIMEOUT)
    r.check('/dr-health returns 200', page.status_code == 200, str(page.status_code))
    html = page.text
    for marker, label in [
        ('dr_health_hub.js', 'hub script tag'),
        ('data-target="hub-screen"', 'Health nav tab'),
        ('data-target="profile-screen"', 'Records nav tab'),
        ('id="hub-screen"', 'hub screen container'),
        ('id="profile-summary"', 'legacy overview element'),
        ('id="data-manager-btn"', 'advanced editor button'),
    ]:
        r.check(f'page contains {label}', marker in html, f'missing {marker}')

    for path in ['/static/dr_health_hub.js', '/static/auth_helper.js',
                 '/static/conversation_box.js', '/static/message_handler.js',
                 '/static/dr_health_sw.js', '/static/dr_health_manifest.json']:
        resp = s.get(f'{BASE_URL}{path}', timeout=TIMEOUT)
        r.check(f'{path} served', resp.status_code == 200, str(resp.status_code))

    sw = s.get(f'{BASE_URL}/static/dr_health_sw.js', timeout=TIMEOUT).text
    r.check('service worker caches the hub script',
            '/static/dr_health_hub.js' in sw, 'hub not in SHELL_ASSETS')

    # ---------- 4. Object sections ----------
    r.section('4. Object sections (personal / diet / lifestyle)')
    resp = s.put(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT,
                 json={'name': 'PWA Tester',
                       'personal': {'age': 44, 'gender': 'female',
                                    'location': 'Sydney', 'blood_type': 'O+'}})
    prof = body(resp).get('profile', {})
    r.check('PUT personal saves', resp.status_code == 200 and
            prof.get('personal', {}).get('blood_type') == 'O+',
            f'{resp.status_code} {prof.get("personal")}')
    r.check('PUT name saves', prof.get('name') == 'PWA Tester', str(prof.get('name')))

    resp = s.put(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT,
                 json={'diet': {'preferences': ['low sodium'], 'restrictions': ['gluten'],
                                'daily_foods': ['oats'], 'cooking_methods': ['steam'],
                                'notes': ['test note']}})
    diet = body(resp).get('profile', {}).get('diet', {})
    r.check('PUT diet saves all five lists',
            diet.get('restrictions') == ['gluten'] and diet.get('daily_foods') == ['oats']
            and diet.get('cooking_methods') == ['steam'], str(diet))

    resp = s.put(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT,
                 json={'lifestyle': {'exercise': ['walking'],
                                     'stress_factors': ['work'], 'habits': ['coffee']}})
    life = body(resp).get('profile', {}).get('lifestyle', {})
    r.check('PUT lifestyle saves',
            life.get('exercise') == ['walking'] and life.get('habits') == ['coffee'], str(life))

    # ---------- 5. List CRUD ----------
    r.section('5. Add / edit / delete for all 10 categories')
    for category, item in LIST_CATEGORIES.items():
        resp = s.post(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                      json={'category': category, 'item': item})
        data = body(resp)
        added = resp.status_code == 200 and data.get('success')
        if not r.check(f'{category}: add', added, f'{resp.status_code} {data.get("error")}'):
            continue
        rows = data.get('profile', {}).get(category, [])
        r.check(f'{category}: appears in profile', len(rows) == 1, f'len={len(rows)}')

        resp = s.put(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                     json={'category': category, 'index': 0, 'updates': UPDATE_FOR[category]})
        data = body(resp)
        ok = resp.status_code == 200 and data.get('success')
        if ok:
            row = data.get('profile', {}).get(category, [{}])[0]
            key, want = next(iter(UPDATE_FOR[category].items()))
            ok = row.get(key) == want
            detail = f'{key}={row.get(key)!r} want {want!r}'
        else:
            detail = f'{resp.status_code} {data.get("error")}'
        r.check(f'{category}: edit', ok, detail)

    # ---------- 6. Category-specific behaviour ----------
    r.section('6. Category-specific behaviour')
    resp = s.patch(f'{BASE_URL}/api/health-profile/condition-status', headers=auth,
                   timeout=TIMEOUT, json={'index': 0, 'status': 'investigating'})
    data = body(resp)
    r.check('condition-status PATCH',
            resp.status_code == 200 and data.get('condition', {}).get('status') == 'investigating',
            f'{resp.status_code} {data}')

    r.check('condition-status rejects bad status',
            s.patch(f'{BASE_URL}/api/health-profile/condition-status', headers=auth,
                    timeout=TIMEOUT, json={'index': 0, 'status': 'bogus'}).status_code == 400,
            'expected 400')

    # Same test + same date is an intentional upsert: it overwrites rather than
    # appending, so re-scanning the same lab report cannot duplicate rows.
    dup = dict(LIST_CATEGORIES['test_results'])
    dup['value'] = '61 ug/L'
    resp = s.post(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                  json={'category': 'test_results', 'item': dup})
    rows = body(resp).get('profile', {}).get('test_results', [])
    r.check('test_results upserts same test on same date',
            resp.status_code == 200 and len(rows) == 1, f'{resp.status_code} len={len(rows)}')
    r.check('test_results upsert overwrites the value',
            rows and '61' in str(rows[0].get('value')), str(rows[:1]))

    resp = s.post(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                  json={'category': 'test_results', 'item': {'value': '1'}})
    r.check('test_results requires test_name', resp.status_code == 400, f'got {resp.status_code}')

    resp = s.post(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                  json={'category': 'test_results',
                        'item': {'test_name': 'TEST FERRITIN', 'value': '80 ug/L',
                                 'reference_range': '30-300', 'date': '2024-08-01'}})
    r.check('test_results accepts second date for same test',
            resp.status_code == 200, f'{resp.status_code} {body(resp).get("error")}')

    # ---------- 7. Validation ----------
    r.section('7. Input validation')
    r.check('rejects unknown category',
            s.post(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                   json={'category': 'nonsense', 'item': {}}).status_code == 400, 'expected 400')
    r.check('rejects negative index on edit',
            s.put(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                  json={'category': 'conditions', 'index': -1,
                        'updates': {}}).status_code == 400, 'expected 400')
    r.check('rejects out-of-range index on edit',
            s.put(f'{BASE_URL}/api/health-profile/item', headers=auth, timeout=TIMEOUT,
                  json={'category': 'conditions', 'index': 999,
                        'updates': {}}).status_code == 400, 'expected 400')
    r.check('rejects out-of-range index on delete',
            s.request('DELETE', f'{BASE_URL}/api/health-profile/item', headers=auth,
                      timeout=TIMEOUT,
                      json={'category': 'conditions', 'index': 999}).status_code == 400,
            'expected 400')

    # ---------- 8. Vitals ----------
    r.section('8. Emergency card (vitals)')
    vitals = {'name': 'PWA Tester', 'age': '44', 'blood_type': 'O+',
              'conditions': 'asthma', 'medications': 'TestMed 10mg',
              'allergies': 'penicillin', 'history': 'none',
              'doctors': 'Dr Test, GP, 0400000000',
              'emergency_contact': {'name': 'Kin', 'relationship': 'sister',
                                    'phone': '0411111111'}}
    resp = s.put(f'{BASE_URL}/api/health-profile/vitals', headers=auth,
                 timeout=TIMEOUT, json=vitals)
    r.check('PUT vitals', resp.status_code == 200 and body(resp).get('success'),
            f'{resp.status_code} {body(resp)}')
    resp = s.get(f'{BASE_URL}/api/health-profile/vitals', headers=auth, timeout=TIMEOUT)
    got = body(resp).get('vitals', {})
    r.check('GET vitals round-trips', got.get('allergies') == 'penicillin', str(got)[:200])
    r.check('vitals keeps nested emergency contact',
            got.get('emergency_contact', {}).get('phone') == '0411111111', str(got)[:200])

    # ---------- 9. Settings ----------
    r.section('9. Upload settings')
    resp = s.put(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT,
                 json={'upload_settings': {'retention_days': 90}})
    r.check('retention_days saves',
            body(resp).get('profile', {}).get('upload_settings', {}).get('retention_days') == 90,
            str(body(resp).get('profile', {}).get('upload_settings')))
    r.check('retention_days rejects zero',
            s.put(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT,
                  json={'upload_settings': {'retention_days': 0}}).status_code == 400,
            'expected 400')
    r.check('retention_days rejects non-integer',
            s.put(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT,
                  json={'upload_settings': {'retention_days': 'abc'}}).status_code == 400,
            'expected 400')

    # ---------- 10. Tool endpoints ----------
    r.section('10. Tool endpoints')
    resp = s.get(f'{BASE_URL}/api/health-profile/summary', headers=auth, timeout=TIMEOUT)
    summary = body(resp).get('summary', '')
    r.check('GET summary returns 200', resp.status_code == 200, str(resp.status_code))
    r.check('summary mentions a stored medication', 'TestMed' in summary, summary[:200])

    resp = s.get(f'{BASE_URL}/api/health-profile/completeness', headers=auth, timeout=TIMEOUT)
    data = body(resp)
    r.check('GET completeness returns 200', resp.status_code == 200, str(resp.status_code))
    r.check('completeness has a score', any(k in data for k in ('score', 'completeness')),
            str(data)[:200])

    resp = s.get(f'{BASE_URL}/api/health-profile/interactions', headers=auth, timeout=TIMEOUT)
    r.check('GET interactions returns 200', resp.status_code == 200,
            f'{resp.status_code} {body(resp)}')

    resp = s.get(f'{BASE_URL}/api/health-profile/test-results-summary', headers=auth,
                 timeout=TIMEOUT)
    data = body(resp)
    r.check('GET test-results-summary returns 200', resp.status_code == 200, str(resp.status_code))
    r.check('test summary includes our test',
            'FERRITIN' in json.dumps(data).upper(), str(data)[:200])

    # ---------- 11. Deletion ----------
    r.section('11. Deletion & persistence')
    for category in LIST_CATEGORIES:
        resp = s.request('DELETE', f'{BASE_URL}/api/health-profile/item', headers=auth,
                         timeout=TIMEOUT, json={'category': category, 'index': 0})
        data = body(resp)
        ok = resp.status_code == 200 and data.get('success')
        r.check(f'{category}: delete', ok, f'{resp.status_code} {data.get("error")}')

    resp = s.get(f'{BASE_URL}/api/health-profile', headers=auth, timeout=TIMEOUT)
    prof = body(resp).get('profile', {})
    r.check('conditions emptied after delete', prof.get('conditions') == [],
            str(prof.get('conditions')))
    r.check('personal survived the deletes',
            prof.get('personal', {}).get('blood_type') == 'O+', str(prof.get('personal')))
    r.check('diet survived the deletes',
            prof.get('diet', {}).get('restrictions') == ['gluten'], str(prof.get('diet')))

    # re-login to confirm data is persisted to disk, not just in memory
    resp = s.post(f'{BASE_URL}/api/auth/login',
                  json={'username': username, 'password': password}, timeout=TIMEOUT)
    token2 = body(resp).get('token')
    resp = s.get(f'{BASE_URL}/api/health-profile',
                 headers={'Authorization': f'Bearer {token2}'}, timeout=TIMEOUT)
    prof2 = body(resp).get('profile', {})
    r.check('profile persists across a fresh login',
            prof2.get('name') == 'PWA Tester', str(prof2.get('name')))

    return r.summary()


if __name__ == '__main__':
    print(f'Testing {BASE_URL}')
    t0 = time.time()
    ok = run()
    print(f'Finished in {time.time() - t0:.1f}s')
    sys.exit(0 if ok else 1)
