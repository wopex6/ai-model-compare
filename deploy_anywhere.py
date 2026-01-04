#!/usr/bin/env python3
"""
Manual Deployment Script for PythonAnywhere
Run this locally when you're ready to deploy to production.

Usage:
    python deploy_anywhere.py

Prerequisites:
    1. Install paramiko: pip install paramiko
    2. Set environment variables or edit config below:
       - PYTHONANYWHERE_USERNAME (default: trabcd)
       - PYTHONANYWHERE_API_TOKEN (get from pythonanywhere.com/account)
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

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
    """Push local changes to GitHub"""
    print("\n📤 Pushing to GitHub...")
    
    # Check for uncommitted changes
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if result.stdout.strip():
        print("⚠️  You have uncommitted changes:")
        print(result.stdout)
        response = input("Commit and push anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return False
        
        # Add and commit
        subprocess.run(['git', 'add', '-A'])
        message = input("Commit message: ") or "Deploy to production"
        subprocess.run(['git', 'commit', '-m', message])
    
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
    """Main deployment flow"""
    show_deployment_summary()
    
    if not check_api_token():
        sys.exit(1)
    
    response = input("\nProceed with deployment? (y/n): ")
    if response.lower() != 'y':
        print("Deployment cancelled.")
        sys.exit(0)
    
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


if __name__ == '__main__':
    main()
