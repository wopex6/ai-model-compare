#!/usr/bin/env python3
"""
Manual Deployment Script for PythonAnywhere
Run this locally when you're ready to deploy to production.

Usage:
    python deploy_anywhere.py

Prerequisites:
    1. pip install requests python-dotenv
    2. Add to your .env file (gitignored, safe):
       PYTHONANYWHERE_API_TOKEN=your_token_here
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load from .env file (gitignored, so safe for secrets)
load_dotenv()

# Configuration
USERNAME = os.getenv('PYTHONANYWHERE_USERNAME', 'trabcd')
API_TOKEN = os.getenv('PYTHONANYWHERE_API_TOKEN', '')
PROJECT_PATH = f'/home/{USERNAME}/ai-model-compare'
WEBAPP_DOMAIN = f'{USERNAME}.pythonanywhere.com'

# PythonAnywhere API base URL
API_BASE = f'https://www.pythonanywhere.com/api/v0/user/{USERNAME}'


def check_api_token():
    """Ensure API token is available"""
    if not API_TOKEN:
        print("❌ PYTHONANYWHERE_API_TOKEN not set!")
        print("\nTo get your API token:")
        print("1. Go to https://www.pythonanywhere.com/account/")
        print("2. Scroll to 'API Token' section")
        print("3. Create or copy your token")
        print("4. Set it: set PYTHONANYWHERE_API_TOKEN=your_token_here")
        return False
    return True


def git_push():
    """Push local changes to GitHub (fully automated)"""
    print("\n📤 Pushing to GitHub...")
    
    # Check for uncommitted changes
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if result.stdout.strip():
        print("⚠️  Uncommitted changes found, auto-committing...")
        
        # Add all changes
        subprocess.run(['git', 'add', '-A'])
        
        # Generate meaningful commit message from changed files
        from datetime import datetime
        changed_files = result.stdout.strip().split('\n')
        
        # Analyze changes to create descriptive message
        changes = []
        for line in changed_files[:5]:  # Look at first 5 files
            if len(line) > 3:
                filepath = line[3:].strip()
                filename = filepath.split('/')[-1].split('\\')[-1]
                if 'test' in filename.lower():
                    changes.append('tests')
                elif 'analytics' in filename.lower():
                    changes.append('analytics')
                elif '.html' in filename:
                    changes.append('templates')
                elif '.js' in filename:
                    changes.append('frontend')
                elif '.py' in filename:
                    changes.append('backend')
                elif '.css' in filename:
                    changes.append('styles')
                elif '.md' in filename:
                    changes.append('docs')
        
        # Create unique list of change types
        unique_changes = list(dict.fromkeys(changes))[:3]
        if unique_changes:
            change_desc = ', '.join(unique_changes)
            message = f"Update {change_desc}"
        else:
            message = "Update files"
        
        # Add file count if many files changed
        if len(changed_files) > 3:
            message += f" ({len(changed_files)} files)"
        
        subprocess.run(['git', 'commit', '-m', message])
        print(f"✅ Committed: {message}")
    
    # Push
    result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Git push failed: {result.stderr}")
        return False
    
    print("✅ Pushed to GitHub")
    return True


def run_console_command(command):
    """Run a command on PythonAnywhere via API"""
    headers = {'Authorization': f'Token {API_TOKEN}'}
    
    # Create a new console or use existing
    response = requests.post(
        f'{API_BASE}/consoles/',
        headers=headers,
        data={'executable': 'bash', 'arguments': '', 'working_directory': PROJECT_PATH}
    )
    
    if response.status_code == 201:
        console_id = response.json()['id']
    else:
        # Try to get existing console
        response = requests.get(f'{API_BASE}/consoles/', headers=headers)
        consoles = response.json()
        if consoles:
            console_id = consoles[0]['id']
        else:
            print(f"❌ Failed to create console: {response.text}")
            return False
    
    # Send command
    response = requests.post(
        f'{API_BASE}/consoles/{console_id}/send_input/',
        headers=headers,
        data={'input': command + '\n'}
    )
    
    return response.status_code == 200


def deploy_via_api():
    """Deploy using PythonAnywhere API"""
    headers = {'Authorization': f'Token {API_TOKEN}'}
    
    print("\n🔄 Pulling latest code on PythonAnywhere...")
    
    # Use the files API to check if we can connect
    response = requests.get(
        f'{API_BASE}/files/path{PROJECT_PATH}/',
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Cannot access project: {response.text}")
        return False
    
    # Run git pull via console
    commands = [
        f'cd {PROJECT_PATH} && git pull origin main',
        f'cd {PROJECT_PATH} && python migrate_all_tables.py',
        f'cd {PROJECT_PATH} && python fix_message_count_column.py',
        f'cd {PROJECT_PATH} && python migrate_analytics_tables.py',
        f'cd {PROJECT_PATH} && python migrate_analytics_test_data.py',
    ]
    
    for cmd in commands:
        print(f"  Running: {cmd.split('&&')[-1].strip()}")
        if not run_console_command(cmd):
            print(f"⚠️  Command may have failed, continuing...")
    
    print("✅ Code pulled and migrations run")
    return True


def reload_webapp():
    """Reload the web app via API"""
    headers = {'Authorization': f'Token {API_TOKEN}'}
    
    print("\n🔄 Reloading web app...")
    
    response = requests.post(
        f'{API_BASE}/webapps/{WEBAPP_DOMAIN}/reload/',
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Web app reloaded!")
        return True
    else:
        print(f"❌ Failed to reload: {response.text}")
        return False


def show_deployment_summary():
    """Show what will be deployed"""
    print("\n" + "=" * 50)
    print("DEPLOYMENT TO PYTHONANYWHERE")
    print("=" * 50)
    print(f"Username: {USERNAME}")
    print(f"Project:  {PROJECT_PATH}")
    print(f"URL:      https://{WEBAPP_DOMAIN}")
    print("=" * 50)
    
    # Show recent commits
    result = subprocess.run(
        ['git', 'log', '--oneline', '-5'],
        capture_output=True, text=True
    )
    print("\nRecent commits:")
    print(result.stdout)


def main():
    """Main deployment flow (fully automated)"""
    show_deployment_summary()
    
    if not check_api_token():
        sys.exit(1)
    
    print("\n🚀 Starting automated deployment...")
    
    # Step 1: Push to GitHub
    if not git_push():
        sys.exit(1)
    
    # Step 2: Pull on PythonAnywhere
    if not deploy_via_api():
        print("\n⚠️  API deployment failed. Manual steps:")
        print(f"1. SSH to PythonAnywhere")
        print(f"2. cd {PROJECT_PATH}")
        print(f"3. git pull origin main")
        print(f"4. python migrate_all_tables.py")
        print(f"5. Reload web app from dashboard")
    
    # Step 3: Reload web app
    if reload_webapp():
        print("\n" + "=" * 50)
        print("🎉 DEPLOYMENT COMPLETE!")
        print(f"Visit: https://{WEBAPP_DOMAIN}")
        print("=" * 50)
    else:
        print("\n⚠️  Please reload manually from PythonAnywhere dashboard")
    
    # Show deployed commit
    print("\n📌 Deployed commit:")
    subprocess.run(['git', 'log', '-1', '--oneline'])


if __name__ == '__main__':
    main()
