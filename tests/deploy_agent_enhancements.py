"""Deploy agent enhancement files to PythonAnywhere"""
import os, time, requests
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
project = f'/home/{username}/ai-model-compare'

# All files to deploy for the agent enhancements
files_to_upload = [
    # Core app changes
    ('app.py', 'app.py'),
    ('smart_response/characters/ai_integration.py', 'smart_response/characters/ai_integration.py'),
    
    # Agent modules
    ('agents/__init__.py', 'agents/__init__.py'),
    ('agents/event_bus.py', 'agents/event_bus.py'),
    ('agents/quality_scorer.py', 'agents/quality_scorer.py'),
    ('agents/quota_monitor.py', 'agents/quota_monitor.py'),
    ('agents/admin_utils.py', 'agents/admin_utils.py'),
    ('agents/orchestrator.py', 'agents/orchestrator.py'),
    ('agents/simulated_users.py', 'agents/simulated_users.py'),
    ('agents/system_health.py', 'agents/system_health.py'),
    ('agents/AGENT_ARCHITECTURE.md', 'agents/AGENT_ARCHITECTURE.md'),
]

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print(f"Deploying {len(files_to_upload)} files to PythonAnywhere...")
print(f"Token available: {'yes' if token else 'NO — set PYTHONANYWHERE_API_TOKEN'}")

success = 0
failed = 0

for local_rel, remote_rel in files_to_upload:
    local_path = os.path.join(root, local_rel)
    remote_path = f'{project}/{remote_rel}'
    
    if not os.path.exists(local_path):
        print(f"  ⚠️ Skipped {local_rel} (file not found)")
        continue
    
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    r = requests.post(
        f'{base}/files/path{remote_path}',
        headers=headers,
        files={'content': content}
    )
    
    if r.status_code in (200, 201):
        print(f"  ✅ {remote_rel} ({len(content):,} bytes)")
        success += 1
    else:
        print(f"  ❌ {remote_rel}: {r.status_code} {r.text[:200]}")
        failed += 1

print(f"\n{'='*50}")
print(f"Uploaded: {success}/{len(files_to_upload)} succeeded, {failed} failed")

# Reload webapp
if success > 0:
    print("\nReloading webapp...")
    time.sleep(2)
    r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
    if r.status_code == 200:
        print(f"✅ Webapp reloaded successfully")
    else:
        print(f"⚠️ Reload: {r.status_code} {r.text}")
        if r.status_code == 429:
            print("Waiting 90s for rate limit to clear, then retrying...")
            time.sleep(90)
            r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
            print(f"Retry: {r.status_code} {r.text}")
