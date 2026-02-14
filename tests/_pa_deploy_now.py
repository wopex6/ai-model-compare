"""Deploy to PythonAnywhere: git pull via console + touch WSGI"""
import os, requests, time
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'

# 1. Kill existing consoles
r = requests.get(f'{base}/consoles/', headers=headers)
if r.status_code == 200:
    for c in r.json():
        cid = c.get('id')
        if cid:
            requests.delete(f'{base}/consoles/{cid}/', headers=headers)
    print(f"Killed {len(r.json())} old consoles")

time.sleep(3)

# 2. Create new bash console
r = requests.post(f'{base}/consoles/', headers=headers, json={'executable': 'bash'})
if r.status_code not in (200, 201):
    print(f"Failed to create console: {r.status_code} {r.text}")
    exit(1)

console_id = r.json()['id']
print(f"Created console {console_id}")

# 3. Send git pull command
cmd = f'cd /home/{username}/ai-model-compare && git pull origin main 2>&1\n'
r = requests.post(f'{base}/consoles/{console_id}/send_input/', headers=headers, json={'input': cmd})
print(f"Sent git pull: {r.status_code}")

time.sleep(12)

# 4. Read output
r = requests.get(f'{base}/consoles/{console_id}/latest_output/', headers=headers)
if r.status_code == 200:
    output = r.json().get('output', '')
    print(f"Git output:\n{output[-600:]}")

# 5. Touch WSGI to trigger reload (bypasses the reload API rate limit)
wsgi = f'/var/www/{username}_pythonanywhere_com_wsgi.py'
cmd2 = f'touch {wsgi} && echo "WSGI touched OK"\n'
r = requests.post(f'{base}/consoles/{console_id}/send_input/', headers=headers, json={'input': cmd2})
print(f"Sent touch WSGI: {r.status_code}")

time.sleep(5)

r = requests.get(f'{base}/consoles/{console_id}/latest_output/', headers=headers)
if r.status_code == 200:
    output = r.json().get('output', '')
    print(f"Final output:\n{output[-400:]}")

# 6. Quick health check
time.sleep(10)
try:
    r = requests.get(f'https://{username}.pythonanywhere.com/', timeout=20)
    print(f"\nHealth check: {r.status_code} (length: {len(r.text)})")
except Exception as e:
    print(f"\nHealth check failed: {e}")
