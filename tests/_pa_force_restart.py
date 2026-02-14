"""Force PythonAnywhere restart by modifying WSGI file (adds a comment with timestamp)"""
import os, requests, time
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
wsgi_path = f'/var/www/{username}_pythonanywhere_com_wsgi.py'

# 1. Read current WSGI file
print("Reading WSGI file...")
r = requests.get(f'{base}/files/path{wsgi_path}', headers=headers)
if r.status_code != 200:
    print(f"Failed to read WSGI: {r.status_code}")
    exit(1)

content = r.text
print(f"Current WSGI: {len(content)} bytes")

# 2. Add/update timestamp comment to force change detection
marker = '# DEPLOY_TIMESTAMP:'
now = datetime.utcnow().isoformat()
if marker in content:
    # Replace existing timestamp line
    lines = content.split('\n')
    lines = [l for l in lines if not l.startswith(marker)]
    lines.append(f'{marker} {now}')
    content = '\n'.join(lines)
else:
    content += f'\n{marker} {now}\n'

# 3. Upload modified WSGI file
print(f"Uploading WSGI with timestamp {now}...")
r = requests.post(
    f'{base}/files/path{wsgi_path}',
    headers=headers,
    files={'content': content}
)
print(f"Upload: {r.status_code}")

# 4. Also do git pull via files API — upload the 3 changed files directly
project = f'/home/{username}/ai-model-compare'
local_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

files_to_upload = [
    'smart_response/characters/base.py',
    'ai_compare/model_config.py',
    'ai_compare/model_discovery.py',
]

for rel_path in files_to_upload:
    local_path = os.path.join(local_base, rel_path)
    remote_path = f'{project}/{rel_path}'
    
    with open(local_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    r = requests.post(
        f'{base}/files/path{remote_path}',
        headers=headers,
        files={'content': file_content}
    )
    status = "✅" if r.status_code in (200, 201) else "❌"
    print(f"  {status} {rel_path}: {r.status_code}")

# 5. Wait and health check
print("\nWaiting 15s for restart...")
time.sleep(15)

try:
    r = requests.get(f'https://{username}.pythonanywhere.com/', timeout=20)
    print(f"Health check: {r.status_code} ({len(r.text)} bytes)")
except Exception as e:
    print(f"Health check failed: {e}")

# 6. Check error log for new entries
print("\nChecking error log...")
r = requests.get(f'{base}/files/path/var/log/{username}.pythonanywhere.com.error.log', headers=headers)
if r.status_code == 200:
    lines = r.text.strip().split('\n')
    for line in lines[-5:]:
        print(f"  {line}")
