"""Helper script to pull code and reload on PythonAnywhere"""
import os, time, requests
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'

# Kill old consoles
r = requests.get(f'{base}/consoles/', headers=headers)
consoles = r.json()
print(f"Active consoles: {len(consoles)}")
for c in consoles:
    requests.delete(f'{base}/consoles/{c["id"]}/', headers=headers)
print("Cleaned up old consoles")

time.sleep(2)

# Create new console and pull
r = requests.post(f'{base}/consoles/', headers=headers, 
                  json={'executable': 'bash', 'working_directory': f'/home/{username}/ai-model-compare'})
console_id = r.json().get('id')
print(f"Created console: {console_id}")

time.sleep(3)

# Send git pull command
r = requests.post(f'{base}/consoles/{console_id}/send_input/', headers=headers,
                  json={'input': 'cd /home/trabcd/ai-model-compare && git pull origin main\n'})
print(f"Sent pull command: {r.status_code}")

time.sleep(15)

# Get output
r = requests.get(f'{base}/consoles/{console_id}/get_latest_output/', headers=headers)
output = r.json().get('output', '')
print(f"Output:\n{output[-600:]}")

# Clean up console
requests.delete(f'{base}/consoles/{console_id}/', headers=headers)

# Reload webapp
time.sleep(2)
r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
print(f"\nReload: {r.status_code} {r.text}")

if r.status_code != 200:
    print("Reload returned non-200, waiting 60s and retrying...")
    time.sleep(60)
    r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
    print(f"Retry reload: {r.status_code} {r.text}")
