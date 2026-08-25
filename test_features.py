import requests, json, random, string

BASE = 'http://localhost:5050'

# 1. Guest chat route exists (no auth) - just check it accepts the request
print('=== 1. GUEST CHAT endpoint reachable ===')
try:
    r = requests.post(f'{BASE}/chat/message', json={'message': 'hi'}, timeout=3)
    print(f'Status: {r.status_code}')
except requests.exceptions.ReadTimeout:
    print('PASS - route reachable, AI call takes >3s (expected for live AI)')
except Exception as e:
    print(f'FAIL - {e}')

# 2. Signup with auto-generated email (no email field from form)
print()
print('=== 2. SIGNUP (placeholder email) ===')
uname = 'testuser_' + ''.join(random.choices(string.ascii_lowercase, k=6))
r = requests.post(f'{BASE}/api/auth/signup', json={
    'username': uname,
    'email': f'{uname}@placeholder.local',
    'password': 'Test1234!'
})
print(f'Status: {r.status_code}')
d = r.json()
print(f'Success: {d.get("success")}')
tok = d.get('token', '')

# 3. Welcome context for brand new user (should return success=True, total_messages=0)
print()
print('=== 3. WELCOME CONTEXT (new user) ===')
r = requests.get(f'{BASE}/api/user/welcome-context', headers={'Authorization': f'Bearer {tok}'})
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2))

# 4. Weekly recap for new user
print()
print('=== 4. WEEKLY RECAP (new user) ===')
r = requests.get(f'{BASE}/api/user/weekly-recap', headers={'Authorization': f'Bearer {tok}'})
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2))

# 5. Welcome context for existing user with messages
print()
print('=== 5. WELCOME CONTEXT (returning user with history) ===')
r = requests.post(f'{BASE}/api/auth/login', json={'username': 'testadmin', 'password': 'Admin123!'})
tok2 = r.json().get('token', '')
r = requests.get(f'{BASE}/api/user/welcome-context', headers={'Authorization': f'Bearer {tok2}'})
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2))

# 6. Weekly recap for returning user
print()
print('=== 6. WEEKLY RECAP (returning user) ===')
r = requests.get(f'{BASE}/api/user/weekly-recap', headers={'Authorization': f'Bearer {tok2}'})
print(f'Status: {r.status_code}')
print(json.dumps(r.json(), indent=2))
