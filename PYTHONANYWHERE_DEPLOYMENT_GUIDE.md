# PythonAnywhere Deployment Guide 🚀

## ✅ **Pre-Deployment Checklist**

- [x] **Git Backup Complete** - All changes pushed to GitHub (commit: e0c1ffb)
- [ ] SSH into PythonAnywhere
- [ ] Pull latest changes
- [ ] Update dependencies
- [ ] Reload web app

---

## 📋 **What's New in This Version**

### **Major Features**:
1. ✅ **8 AI Characters** (up from 4)
   - Coach Max (Motivational)
   - Sage Wei (Wisdom)
   - Marcus Aurelius (Stoic)
   - Dr. Elena (Psychologist)
   - Master Kai (Zen Master) 🆕
   - Coach Ryan (Business Coach) 🆕
   - Coach Jordan (Life Coach) 🆕
   - Dr. Nova (Scientist) 🆕

2. ✅ **4 Custom UIs** with unique designs:
   - `zen_master.html` - Meditation timer & breathing exercises
   - `business_coach.html` - KPI dashboard
   - `life_coach.html` - Life balance wheel & vision board
   - `scientist.html` - Scientific method lab interface

3. ✅ **Unified Character Architecture**:
   - Configuration-driven character system
   - Factory pattern for character creation
   - Dynamic route registration
   - Base enhanced chatbot class

### **New Files**:
```
ai_compare/
├── base_enhanced_chatbot.py        (New)
├── character_configs.py            (New)
├── character_factory.py            (New)
├── character_routes.py             (New)
├── knowledge_config.py             (New)
├── knowledge_enhanced_chatbot.py   (New)
├── knowledge_system.py             (New)
├── knowledge_discovery.py          (New)
├── knowledge_tracker.py            (New)
└── knowledge_vector_store.py       (New)

templates/
├── zen_master.html                 (New)
├── business_coach.html             (New)
├── life_coach.html                 (New)
├── scientist.html                  (New)
├── character_universal.html        (New)
└── chatchat.html                   (Renamed from multi_user.html)
```

---

## 🔧 **Deployment Steps**

### **Step 1: SSH into PythonAnywhere**

```bash
ssh yourusername@ssh.pythonanywhere.com
```

### **Step 2: Navigate to Your Project**

```bash
cd ~/ai-model-compare
```

### **Step 3: Backup Current Version** ⚠️

```bash
# Create a backup of the current working version
cp -r ~/ai-model-compare ~/ai-model-compare-backup-$(date +%Y%m%d)

# Or create a git tag for the old version
git tag -a v1.0-pre-8chars -m "Version before 8-character system"
git push origin v1.0-pre-8chars
```

### **Step 4: Pull Latest Changes**

```bash
# Stash any local changes if needed
git stash

# Pull the latest version
git pull origin main

# If you stashed changes
git stash pop  # Only if needed
```

### **Step 5: Update Dependencies**

```bash
# Activate virtual environment
source ~/ai-model-compare/venv/bin/activate

# Update requirements
pip install -r requirements.txt

# Check if ChromaDB dependencies are installed (optional for knowledge system)
pip install chromadb sentence-transformers  # Optional
```

### **Step 6: Verify File Structure**

```bash
# Check that new files exist
ls ai_compare/character_*.py
ls templates/zen_master.html templates/business_coach.html templates/life_coach.html templates/scientist.html

# Check app.py was updated
grep "CharacterFactory" app.py
```

### **Step 7: Update WSGI Configuration**

Go to **PythonAnywhere Web Tab** → **Code section** → **WSGI configuration file**

Ensure it looks like this:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/ai-model-compare'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables if needed
os.environ['FLASK_ENV'] = 'production'

# Import flask app
from app import app as application
```

### **Step 8: Reload Web App**

In **PythonAnywhere Web Tab**:
1. Click the big green **"Reload yourusername.pythonanywhere.com"** button
2. Wait for reload to complete (~10-30 seconds)

### **Step 9: Verify Deployment**

Visit your site and test:

#### **Test URLs**:
```
https://yourusername.pythonanywhere.com/chatchat
https://yourusername.pythonanywhere.com/zen_master
https://yourusername.pythonanywhere.com/business_coach
https://yourusername.pythonanywhere.com/life_coach
https://yourusername.pythonanywhere.com/scientist
https://yourusername.pythonanywhere.com/psychologist
https://yourusername.pythonanywhere.com/super_motivational_coach
https://yourusername.pythonanywhere.com/wisdom_sage
https://yourusername.pythonanywhere.com/stoic_philosopher
```

#### **Verification Checklist**:
- [ ] Dashboard (`/chatchat`) loads and shows all 8 characters
- [ ] Each character link works and displays correctly
- [ ] Custom UIs load (zen_master, business_coach, life_coach, scientist)
- [ ] Chat functionality works for all characters
- [ ] Daily insights display
- [ ] Quick topics work
- [ ] No 500 errors in error logs

---

## 🔍 **Troubleshooting**

### **Issue: Import Errors**

```bash
# Check Python path in WSGI
grep sys.path /var/www/yourusername_pythonanywhere_com_wsgi.py

# Verify all files were pulled
ls -la ai_compare/character_*.py
```

### **Issue: 500 Internal Server Error**

```bash
# Check error logs
tail -50 ~/yourusername.pythonanywhere.com.error.log

# Common causes:
# 1. Missing dependencies
pip list | grep -i chroma  # Check if ChromaDB installed (optional)

# 2. Import errors
python3 -c "from ai_compare.character_factory import CharacterFactory; print('OK')"

# 3. Syntax errors
python3 -c "import app; print('OK')"
```

### **Issue: ChromaDB Not Working**

ChromaDB is **optional** for the knowledge system. If it causes issues:

```python
# In base_enhanced_chatbot.py, the code already handles this:
# CHROMA_AVAILABLE is checked before using ChromaDB
```

If you want to install it:
```bash
pip install chromadb==0.4.18 sentence-transformers==2.2.2
```

### **Issue: Old Routes Not Working**

The old `/multi_user` route is now `/chatchat`. Update any bookmarks or links.

```python
# In app.py, you can add a redirect if needed:
@app.route('/multi_user')
def redirect_multi_user():
    return redirect('/chatchat')
```

---

## 🎯 **Quick Deployment Script**

Create this script on PythonAnywhere to automate deployment:

```bash
#!/bin/bash
# File: ~/deploy.sh

echo "🚀 Deploying AI Model Compare..."

cd ~/ai-model-compare

echo "📦 Pulling latest changes..."
git pull origin main

echo "🔧 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet

echo "✅ Deployment complete!"
echo "👉 Don't forget to reload your web app in the Web tab!"
echo "🌐 Visit: https://yourusername.pythonanywhere.com/chatchat"
```

Make it executable:
```bash
chmod +x ~/deploy.sh
```

Run it:
```bash
~/deploy.sh
```

---

## 📊 **Post-Deployment Testing**

### **Manual Test Sequence**:

1. **Dashboard Test**
   ```
   Visit: /chatchat
   Verify: All 8 character cards visible
   ```

2. **Legacy Characters** (should still work)
   ```
   /super_motivational_coach - Coach Max
   /wisdom_sage - Sage Wei  
   /stoic_philosopher - Marcus
   /psychologist - Dr. Elena
   ```

3. **New Characters** (with custom UIs)
   ```
   /zen_master - Master Kai (meditation timer visible?)
   /business_coach - Coach Ryan (KPI cards visible?)
   /life_coach - Coach Jordan (balance wheel visible?)
   /scientist - Dr. Nova (star field visible?)
   ```

4. **Chat Functionality**
   - Send a message to each character
   - Verify responses come back
   - Check daily insights load

5. **Quick Topics**
   - Click quick topic buttons
   - Verify they populate the chat input

### **Automated Test** (optional):

Create `test_deployment.py`:

```python
import requests

BASE_URL = "https://yourusername.pythonanywhere.com"

characters = [
    "zen_master",
    "business_coach", 
    "life_coach",
    "scientist",
    "psychologist",
    "super_motivational_coach",
    "wisdom_sage",
    "stoic_philosopher"
]

print("🧪 Testing deployment...")

for char in characters:
    url = f"{BASE_URL}/{char}"
    try:
        response = requests.get(url)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {char}: {response.status_code}")
    except Exception as e:
        print(f"❌ {char}: ERROR - {e}")

print("\n✅ Deployment test complete!")
```

---

## 🔐 **Environment Variables** (if needed)

If you use any API keys or secrets:

```bash
# In PythonAnywhere bash console:
echo 'export OPENAI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

Or in **WSGI config**:
```python
os.environ['OPENAI_API_KEY'] = 'your-key'
```

---

## 🗂️ **Database Considerations**

### **SQLite** (current):
- Already works on PythonAnywhere
- Located in project directory
- No changes needed

### **PostgreSQL** (if you upgrade):
```bash
# PythonAnywhere doesn't support PostgreSQL on free tier
# Use MySQL if needed
```

---

## 📈 **Performance Optimization**

### **For PythonAnywhere**:

1. **Reduce conversation history**:
   ```python
   # In base_enhanced_chatbot.py
   MAX_HISTORY = 10  # Reduce if needed
   ```

2. **Disable ChromaDB** if causing memory issues:
   ```python
   # It's already optional - just don't install it
   ```

3. **Use caching** for daily insights:
   ```python
   # Add caching decorator to get_daily_insight()
   from functools import lru_cache
   
   @lru_cache(maxsize=10)
   def get_daily_insight(self):
       ...
   ```

---

## 🆘 **Rollback Procedure**

If something goes wrong:

### **Quick Rollback**:
```bash
cd ~/ai-model-compare
git log --oneline -5  # Find previous commit
git reset --hard COMMIT_HASH  # Replace with actual hash
# Then reload web app
```

### **Full Rollback**:
```bash
cd ~
rm -rf ai-model-compare
cp -r ai-model-compare-backup-YYYYMMDD ai-model-compare
# Then reload web app
```

---

## ✅ **Success Criteria**

Your deployment is successful when:

- [ ] All 8 characters visible on dashboard
- [ ] All character pages load without errors
- [ ] Custom UIs display correctly (meditation timer, KPI cards, etc.)
- [ ] Chat works for all characters
- [ ] Daily insights load
- [ ] No errors in PythonAnywhere error logs
- [ ] Response times are reasonable (<3 seconds)

---

## 📞 **Support**

If issues persist:

1. **Check PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
2. **Review Error Logs**: `~/yourusername.pythonanywhere.com.error.log`
3. **Test Locally First**: Ensure it works on `localhost:5000`
4. **Check File Permissions**: `ls -la ~/ai-model-compare`

---

## 📝 **Deployment Log Template**

Keep a log of your deployment:

```
Date: [DATE]
Version: v2.0 - 8 Character System
Deployed by: [NAME]
Commit Hash: e0c1ffb

Pre-deployment backup: ✅
Git pull: ✅
Dependencies updated: ✅
WSGI config checked: ✅
Web app reloaded: ✅

Test Results:
- Dashboard: ✅/❌
- Zen Master: ✅/❌
- Business Coach: ✅/❌
- Life Coach: ✅/❌
- Scientist: ✅/❌
- Legacy characters: ✅/❌
- Chat functionality: ✅/❌

Issues encountered: [NONE/LIST]
Resolution: [N/A/DESCRIBE]

Deployment status: ✅ SUCCESS / ❌ ROLLED BACK
```

---

## 🎉 **Post-Deployment**

After successful deployment:

1. **Update documentation** with production URLs
2. **Notify users** about new features
3. **Monitor error logs** for first 24 hours
4. **Test from different devices** (mobile, desktop)
5. **Celebrate!** 🎊

---

**Last Updated**: November 23, 2025  
**Version**: 2.0 - 8 Character System  
**Commit**: e0c1ffb  
**Status**: Ready to Deploy 🚀
