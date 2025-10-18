# PythonAnywhere Deployment Guide

## Initial Setup

1. **Upload project**:
   ```bash
   git clone https://github.com/yourusername/ai-model-compare.git
   cd ai-model-compare
   ```

2. **Create virtual environment**:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup database**:
   ```bash
   python3 add_user_roles.py
   ```

4. **Configure WSGI** (in Web tab):
   ```python
   import sys
   import os
   
   project_home = '/home/yourusername/ai-model-compare'
   if project_home not in sys.path:
       sys.path = [project_home] + sys.path
   
   os.environ['FLASK_ENV'] = 'production'
   
   from app import app as application
   ```

5. **Add .env file**:
   ```bash
   nano .env
   # Add your API keys
   ```

6. **Reload** web app from Web tab

## Updating Deployment

```bash
cd ~/ai-model-compare
git pull
source venv/bin/activate
pip install -r requirements.txt
# Click Reload button in Web tab
```

## URLs

- Main app: https://yourusername.pythonanywhere.com
- Multi-user: https://yourusername.pythonanywhere.com/multi-user

## Troubleshooting

- Check error logs in Web tab
- Verify all paths in WSGI config
- Ensure venv is activated
- Check file permissions: `chmod 644 integrated_users.db`
