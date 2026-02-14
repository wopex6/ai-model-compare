"""Deploy to PythonAnywhere - alternative approach using scheduled task"""
import os, time, requests
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'

# Step 1: Check current consoles and clean up
print("Step 1: Cleaning up consoles...")
r = requests.get(f'{base}/consoles/', headers=headers)
consoles = r.json()
print(f"  Found {len(consoles)} consoles")
for c in consoles:
    cid = c['id']
    requests.delete(f'{base}/consoles/{cid}/', headers=headers)
print("  Cleaned up")
time.sleep(5)

# Step 2: Create a fresh Bash console
print("Step 2: Creating fresh console...")
r = requests.post(f'{base}/consoles/', headers=headers,
                  json={'executable': '/bin/bash',
                        'arguments': '',
                        'working_directory': f'/home/{username}'})
print(f"  Status: {r.status_code}")
cdata = r.json()
console_id = cdata.get('id')
print(f"  Console ID: {console_id}")

# Wait for console to be ready (needs longer on free tier)
print("  Waiting 30s for console to initialize...")
time.sleep(30)

# Step 3: Send commands
print("Step 3: Pulling code...")
cmd = (
    'cd /home/trabcd/ai-model-compare && '
    'git pull origin main 2>&1 && '
    'echo "GIT_PULL_DONE" && '
    'touch /var/www/trabcd_pythonanywhere_com_wsgi.py 2>&1 && '
    'echo "WSGI_TOUCHED"\n'
)
r = requests.post(f'{base}/consoles/{console_id}/send_input/', headers=headers,
                  json={'input': cmd})
print(f"  Send status: {r.status_code}")

# Wait for commands to finish
time.sleep(20)

# Step 4: Get output
print("Step 4: Getting output...")
r = requests.get(f'{base}/consoles/{console_id}/get_latest_output/', headers=headers)
output = r.json().get('output', '')
print(f"  Output (last 800 chars):\n{output[-800:]}")

# Check success markers
if 'GIT_PULL_DONE' in output:
    print("\n✅ Git pull completed")
else:
    print("\n⚠️ Git pull status unclear")

if 'WSGI_TOUCHED' in output:
    print("✅ WSGI file touched (app will reload)")
else:
    print("⚠️ WSGI touch status unclear")

# Cleanup
requests.delete(f'{base}/consoles/{console_id}/', headers=headers)
print("\nDone. App should reload within 30 seconds.")
