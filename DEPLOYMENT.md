# PythonAnywhere Deployment Guide

## Initial Setup

### 1. Upload Project to PythonAnywhere

```bash
git clone https://github.com/yourusername/ai-model-compare.git
cd ai-model-compare
```

### 2. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Note**: `llama-cpp-python` is commented out in requirements.txt due to size constraints.

### 3. Create .env File with API Keys and Secrets

```bash
nano .env
```

Add the following (replace with your actual keys):
```
OPENAI_API_KEY=your_openai_api_key_here
GROK_API_KEY=your_grok_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Generate random secrets with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET=your_random_jwt_secret_here
SECRET_KEY=your_random_flask_secret_here

# Production Settings - Disable auto-docs to prevent timeouts
DISABLE_AUTO_DOCS=true
```

Save with `Ctrl+X`, `Y`, `Enter`.

### 4. Initialize Database

```bash
python3 -c "from integrated_database import IntegratedDatabase; IntegratedDatabase()"
python3 add_user_roles.py
```

### 5. Configure Web App

Go to **Web** tab → **Add a new web app**:
- Choose **Manual configuration**
- Select **Python 3.10**

**Set paths:**
- Source code: `/home/yourusername/ai-model-compare`
- Working directory: `/home/yourusername/ai-model-compare`
- Virtualenv: `/home/yourusername/ai-model-compare/venv`

**Configure WSGI** (click WSGI configuration file link):
```python
import sys
import os

project_home = '/home/yourusername/ai-model-compare'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['FLASK_ENV'] = 'production'

from app import app as application
```

**Add Static Files:**
- URL: `/static/`
- Directory: `/home/yourusername/ai-model-compare/static`

### 6. Reload Web App

Click the green **"Reload yourusername.pythonanywhere.com"** button.

Wait 15-20 seconds for initialization, then visit:
`https://yourusername.pythonanywhere.com/multi-user`

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
