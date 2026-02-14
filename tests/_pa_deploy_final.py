"""Upload app.py + all fixes to PythonAnywhere and reload"""
import os, requests, time
from dotenv import load_dotenv
load_dotenv(override=True)

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
project = f'/home/{username}/ai-model-compare'
local_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

files_to_upload = [
    '.env',
    'app.py',
    'smart_response/characters/base.py',
    'ai_compare/model_config.py',
    'ai_compare/model_discovery.py',
]

print("Uploading files to PythonAnywhere...")
for rel_path in files_to_upload:
    local_path = os.path.join(local_base, rel_path)
    remote_path = f'{project}/{rel_path}'
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    r = requests.post(f'{base}/files/path{remote_path}', headers=headers, files={'content': content})
    status = "OK" if r.status_code in (200, 201) else "FAIL"
    print(f"  [{status}] {rel_path}: {r.status_code} ({len(content)} bytes)")

# Reload
print("\nReloading webapp...")
r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
print(f"Reload: {r.status_code} {r.text[:100]}")

if r.status_code == 200:
    print("Reload successful! Waiting 20s for startup...")
    time.sleep(20)
else:
    print("Reload API still rate-limited. Please reload manually from PythonAnywhere dashboard.")
    print("Checking if app is serving anyway...")
    time.sleep(5)

# Health check
try:
    r = requests.get(f'https://{username}.pythonanywhere.com/', timeout=30)
    print(f"\nHealth: {r.status_code} ({len(r.text)} bytes)")
except Exception as e:
    print(f"\nHealth: {e}")
