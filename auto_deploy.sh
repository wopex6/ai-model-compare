#!/bin/bash
# Auto-deploy script for PythonAnywhere
# Add this to PythonAnywhere Scheduled Tasks

cd ~/ai-model-compare

# Pull latest changes
git pull origin main

# Check if requirements changed
if git diff HEAD@{1} HEAD --name-only | grep -q requirements.txt; then
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Reload web app by touching WSGI file
touch /var/www/$(whoami)_pythonanywhere_com_wsgi.py

echo "$(date): Auto-deploy complete" >> ~/deploy.log
