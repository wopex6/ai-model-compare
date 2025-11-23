# 🚨 Security Fix - API Key Exposure

## Problem
API keys were hardcoded in:
- `test_gpt_direct.py`
- `gpt.py`

These files were committed to git and pushed to GitHub.

## Immediate Actions Required

### 1. Regenerate ALL API Keys ⚠️ DO THIS FIRST

**OpenAI:**
1. Go to: https://platform.openai.com/api-keys
2. Delete exposed key: `sk-proj-OMlp...`
3. Create new API key
4. Save it securely (password manager)

**Anthropic (if you have one):**
1. Go to: https://console.anthropic.com/settings/keys
2. Revoke old keys
3. Create new key

**Google AI (if you have one):**
1. Go to: https://makersuite.google.com/app/apikey
2. Revoke old keys
3. Create new key

### 2. Remove Files from Git History

Run these commands to remove the files with exposed keys:

```bash
cd "c:\Users\trabc\CascadeProjects\ai-model-compare - Claude"

# Remove files from git completely
git rm --cached test_gpt_direct.py
git rm --cached gpt.py

# Commit the removal
git commit -m "Remove files with exposed API keys"

# Push to GitHub
git push origin main
```

### 3. Add Files to .gitignore

Create/update .gitignore:

```bash
# Add these lines
test_gpt_direct.py
gpt.py
```

### 4. Update Code to Use Environment Variables

Instead of hardcoded keys, use environment variables:

**In your .env file** (which is already gitignored):
```env
OPENAI_API_KEY=your-new-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
```

**In your Python code:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Good - reads from environment
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Bad - hardcoded (NEVER DO THIS)
# client = OpenAI(api_key="sk-proj-...")
```

### 5. Clean Git History (Optional but Recommended)

To completely remove keys from git history:

```bash
# This is advanced - only if you're comfortable with git
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch test_gpt_direct.py gpt.py" \
  --prune-empty --tag-name-filter cat -- --all

# Force push to overwrite history
git push origin --force --all
```

**⚠️ WARNING**: This rewrites git history. Only do this if:
- You're the only one working on the repo
- Or everyone on the team is aware and will re-clone

## Order of Operations

1. ✅ **FIRST**: Regenerate all API keys (keys are already compromised)
2. ✅ Remove exposed files from repo
3. ✅ Update .gitignore
4. ✅ Update code to use environment variables
5. ✅ **THEN**: Deploy to PythonAnywhere with new keys

## Why This Order?

- Keys are already exposed in GitHub (public)
- Must regenerate BEFORE deploying
- No point deploying with compromised keys
- Clean repo BEFORE adding new keys

## After Security Fix

Once you've:
1. ✅ Regenerated all keys
2. ✅ Removed exposed files from git
3. ✅ Updated code to use .env

Then proceed with deployment using the new keys.
