"""Upload changed files directly via PythonAnywhere Files API, then reload"""
import os, time, requests
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
project = f'/home/{username}/ai-model-compare'

# Files that changed since last successful deploy
files_to_upload = [
    ('smart_response/characters/base.py', 'smart_response/characters/base.py'),
    ('ai_compare/model_config.py', 'ai_compare/model_config.py'),
    ('ai_compare/model_discovery.py', 'ai_compare/model_discovery.py'),
]

print("Uploading changed files to PythonAnywhere...")
for local_rel, remote_rel in files_to_upload:
    local_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), local_rel)
    remote_path = f'{project}/{remote_rel}'
    
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    r = requests.post(
        f'{base}/files/path{remote_path}',
        headers=headers,
        files={'content': content}
    )
    
    if r.status_code == 200 or r.status_code == 201:
        print(f"  ✅ Uploaded {remote_rel} ({len(content)} bytes)")
    else:
        print(f"  ❌ Failed {remote_rel}: {r.status_code} {r.text[:200]}")

# Reload webapp
print("\nReloading webapp...")
time.sleep(2)
r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
print(f"Reload: {r.status_code} {r.text}")

if r.status_code != 200:
    print("Waiting 90s for rate limit to clear, then retrying...")
    time.sleep(90)
    r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
    print(f"Retry: {r.status_code} {r.text}")
