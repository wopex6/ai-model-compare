#!/usr/bin/env python3
"""
Deploy to PythonAnywhere via Files API from Windsurf
Usage: python deploy_from_windsurf.py
"""
import os
import requests
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()

# PythonAnywhere config
token = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
username = 'trabcd'
headers = {'Authorization': f'Token {token}'}
base = f'https://www.pythonanywhere.com/api/v0/user/{username}'
project = f'/home/{username}/ai-model-compare'

# Files to upload (same as _pa_upload_and_reload.py)
files_to_upload = [
    ('ai_compare/chatbot.py', 'ai_compare/chatbot.py'),
    ('smart_response/characters/ai_integration.py', 'smart_response/characters/ai_integration.py'),
    ('static/conversation_box.js', 'static/conversation_box.js'),
    ('static/multi_user_app.js', 'static/multi_user_app.js'),
    ('static/domain_characters.js', 'static/domain_characters.js'),
    ('static/multi_user_styles.css', 'static/multi_user_styles.css'),
    ('static/domain_characters.css', 'static/domain_characters.css'),
]

def upload_file(local_path, remote_path):
    """Upload a single file to PythonAnywhere"""
    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        r = requests.post(
            f'{base}/files/path{remote_path}',
            headers=headers,
            files={'content': content}
        )
        
        if r.status_code in (200, 201):
            print(f"✅ Uploaded {remote_path} ({len(content)} bytes)")
            return True
        else:
            print(f"❌ Failed {remote_path}: {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error uploading {remote_path}: {e}")
        return False

def reload_webapp():
    """Reload the webapp"""
    try:
        r = requests.post(f'{base}/webapps/{username}.pythonanywhere.com/reload/', headers=headers)
        if r.status_code == 200:
            print("✅ Webapp reloaded successfully")
            return True
        else:
            print(f"⚠️ Reload returned {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Error reloading: {e}")
        return False

def main():
    """Deploy all files"""
    print("🚀 Deploying to PythonAnywhere...")
    
    # Get workspace root
    workspace_root = Path(__file__).parent
    success_count = 0
    
    for local_rel, remote_rel in files_to_upload:
        local_path = workspace_root / local_rel
        if not local_path.exists():
            print(f"⚠️ File not found: {local_path}")
            continue
        
        if upload_file(str(local_path), f'{project}/{remote_rel}'):
            success_count += 1
    
    print(f"\n📊 Uploaded {success_count}/{len(files_to_upload)} files")
    
    # Try to reload
    print("\n🔄 Reloading webapp...")
    reload_webapp()
    
    print("\n✨ Done! Check https://trabcd.pythonanywhere.com/")

if __name__ == '__main__':
    main()
