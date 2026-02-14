"""Upload .env + code fixes to PythonAnywhere and reload"""
import os, requests, time
from dotenv import load_dotenv
load_dotenv(override=True)

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
project = f'/home/{username}/ai-model-compare'
local_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files to upload
files_to_upload = [
    '.env',
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
    
    r = requests.post(
        f'{base}/files/path{remote_path}',
        headers=headers,
        files={'content': content}
    )
    status = "✅" if r.status_code in (200, 201) else "❌"
    print(f"  {status} {rel_path}: {r.status_code}")

# Reload webapp
print("\nReloading webapp...")
r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
print(f"Reload: {r.status_code} {r.text}")

if r.status_code != 200:
    print("Waiting 90s for rate limit, then retry...")
    time.sleep(90)
    r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
    print(f"Retry: {r.status_code} {r.text}")

# Health check
print("\nWaiting 15s then health check...")
time.sleep(15)
try:
    r = requests.get(f'https://{username}.pythonanywhere.com/', timeout=30)
    print(f"Health: {r.status_code} ({len(r.text)} bytes)")
except Exception as e:
    print(f"Health check: {e}")

# Check error log
print("\nLast 5 error log lines:")
r = requests.get(f'{base}/files/path/var/log/{username}.pythonanywhere.com.error.log', headers=headers)
if r.status_code == 200:
    for line in r.text.strip().split('\n')[-5:]:
        print(f"  {line}")
