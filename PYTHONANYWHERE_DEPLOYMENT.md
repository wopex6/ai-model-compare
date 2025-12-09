# PythonAnywhere Deployment Guide
## Complete step-by-step guide for deploying AI Model Compare to PythonAnywhere

---

## **Pre-Deployment Checklist**

### **What You'll Need:**
- [ ] PythonAnywhere account (Free or Paid)
- [ ] OpenAI API key
- [ ] GitHub repository access
- [ ] Databases ready to migrate (optional)

### **PythonAnywhere Account Tiers:**

| Tier | Price | CPU | Storage | Outbound API | Custom Domain |
|------|-------|-----|---------|--------------|---------------|
| **Beginner** | Free | Limited | 512MB | Whitelist only | No |
| **Hacker** | $5/month | 1 CPU-second | 1GB | Yes | No |
| **Web Developer** | $12/month | 2 CPU-seconds | 10GB | Yes | Yes |

**Recommended:** Start with **Free tier** for testing, upgrade to **Hacker ($5)** or **Web Developer ($12)** for production.

---

## **Step-by-Step Deployment**

### **Step 1: Create PythonAnywhere Account**

1. Go to https://www.pythonanywhere.com
2. Click "Pricing & signup"
3. Choose a plan (Free to start)
4. Create your account
5. Verify email

---

### **Step 2: Open Bash Console**

1. In PythonAnywhere dashboard, click "Consoles"
2. Click "Bash" to open a new console
3. You'll see a command line interface

---

### **Step 3: Clone Your Repository**

```bash
# Clone from GitHub
git clone https://github.com/wopex6/ai-model-compare.git
cd ai-model-compare

# Verify files
ls -la
```

---

### **Step 4: Create Virtual Environment**

```bash
# Create virtual environment with Python 3.10 (PythonAnywhere supports 3.10)
mkvirtualenv --python=/usr/bin/python3.10 aimodelcompare

# Activate it (usually auto-activated after creation)
workon aimodelcompare

# Upgrade pip
pip install --upgrade pip
```

---

### **Step 5: Install Dependencies**

```bash
# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list
```

**If installation fails due to memory limits:**
```bash
# Install packages one by one
pip install flask
pip install openai
pip install python-dotenv
pip install pyjwt
# ... etc
```

---

### **Step 6: Create Environment File**

```bash
# Create .env file
nano .env
```

**Add the following content:**
```ini
# CRITICAL: Add your actual OpenAI API key
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Generate a secret key (use the command below to generate)
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET=your-generated-jwt-secret-here

# PythonAnywhere specific settings
FLASK_ENV=production
FLASK_DEBUG=0

# Database paths (relative to app directory)
DATABASE_PATH=./databases/production_integrated_users.db
SMART_RESPONSE_DB=./databases/production_smart_response.db

# Disable auto-documentation (IMPORTANT for PythonAnywhere)
DISABLE_AUTO_DOCS=true

# Logging
LOG_LEVEL=INFO

# AI Budget (conservative for free tier)
MAX_AI_CALLS_PER_DAY=50
ADMIN_AI_CALLS_PER_DAY=100
SYSTEM_AI_CALL_CAP=150
```

**Generate SECRET_KEY in the console:**
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_hex(32))"
# Copy these values to your .env file
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

---

### **Step 7: Create Necessary Directories**

```bash
# Create directories for data
mkdir -p databases
mkdir -p logs
mkdir -p conversations
mkdir -p user_profiles

# Set permissions
chmod 755 databases logs conversations user_profiles
```

---

### **Step 8: Migrate Databases (Optional)**

#### **Option A: Start Fresh (Recommended for first deployment)**

Databases will be created automatically when the app runs. Users will register new accounts.

#### **Option B: Migrate Existing Databases**

**From your local machine:**

1. **Download your local databases:**
```powershell
# On your local Windows machine
# The databases are in your project folder
cd "c:\Users\trabc\CascadeProjects\ai-model-compare - Claude"

# Compress databases for upload
tar -czf databases_backup.tar.gz integrated_users.db smart_response.db
```

2. **Upload to PythonAnywhere:**

**Method 1: Via Files tab (Easier)**
- Go to PythonAnywhere "Files" tab
- Navigate to: `/home/yourusername/ai-model-compare/`
- Click "Upload a file"
- Upload `databases_backup.tar.gz`

**Method 2: Via Bash console (if you have the file URL)**
```bash
cd ~/ai-model-compare
wget https://your-file-url/databases_backup.tar.gz
tar -xzf databases_backup.tar.gz
mv integrated_users.db databases/production_integrated_users.db
mv smart_response.db databases/production_smart_response.db
```

3. **Verify databases:**
```bash
cd ~/ai-model-compare
sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) FROM users;"
sqlite3 databases/production_smart_response.db "SELECT COUNT(*) FROM user_profiles;"
```

#### **Option C: Export/Import Specific Data**

If you only want to migrate certain users:

```bash
# On local machine: Export users
sqlite3 integrated_users.db ".mode csv" ".output users_export.csv" "SELECT * FROM users;"

# Upload users_export.csv to PythonAnywhere
# On PythonAnywhere: Import users
sqlite3 databases/production_integrated_users.db
.mode csv
.import users_export.csv users
.quit
```

---

### **Step 9: Create WSGI Configuration File**

1. **Go to "Web" tab** in PythonAnywhere
2. Click "Add a new web app"
3. Choose "Manual configuration" (NOT Flask)
4. Choose **Python 3.10**
5. Click through to create the app

6. **Edit WSGI configuration file:**
   - In the Web tab, find "Code" section
   - Click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)

7. **Replace entire contents with:**

```python
# +++++++++++ FLASK +++++++++++
# Flask WSGI configuration for AI Model Compare on PythonAnywhere

import sys
import os
from dotenv import load_dotenv

# Add your project directory to the sys.path
project_home = '/home/yourusername/ai-model-compare'  # CHANGE 'yourusername' to your actual username!
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Load environment variables from .env file
load_dotenv(os.path.join(project_home, '.env'))

# Set working directory
os.chdir(project_home)

# Import Flask app
from app import app as application

# IMPORTANT: PythonAnywhere needs the application object
# Don't change the name 'application'
```

**CRITICAL: Replace `yourusername` with your actual PythonAnywhere username!**

---

### **Step 10: Configure Virtual Environment**

In the **Web tab**, find the "Virtualenv" section:

1. Click "Enter path to a virtualenv"
2. Enter: `/home/yourusername/.virtualenvs/aimodelcompare`
   - Replace `yourusername` with your actual username
3. Click the checkmark to save

---

### **Step 11: Configure Static Files**

In the **Web tab**, find the "Static files" section:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/ai-model-compare/static` |

1. Click "Enter URL" and enter `/static/`
2. Click "Enter path" and enter `/home/yourusername/ai-model-compare/static`
3. Replace `yourusername` with your actual username

---

### **Step 12: Reload Web App**

1. In the **Web tab**, scroll to top
2. Click the big green **"Reload"** button
3. Wait for reload to complete (green checkmark)

---

### **Step 13: Test Your Deployment**

1. **Find your app URL** at top of Web tab:
   - Free tier: `http://yourusername.pythonanywhere.com`
   - Paid tier: Can use custom domain

2. **Visit your app:**
   ```
   http://yourusername.pythonanywhere.com
   ```

3. **Test checklist:**
   - [ ] Homepage loads
   - [ ] Register new account
   - [ ] Login works
   - [ ] Click on "Scientist" character
   - [ ] Send a message
   - [ ] Get AI response
   - [ ] Refresh page - history persists
   - [ ] Test other characters

---

### **Step 14: Check Logs for Errors**

If something doesn't work:

1. **Go to Web tab**
2. **Click on "Log files"** section
3. **Check Error log:**
   - `/var/log/yourusername.pythonanywhere.com.error.log`
4. **Check Server log:**
   - `/var/log/yourusername.pythonanywhere.com.server.log`

**Common issues and fixes below in Troubleshooting section.**

---

## **PythonAnywhere Limitations & Workarounds**

### **1. Outbound API Restrictions (Free Tier)**

**Problem:** Free accounts can only make API calls to whitelisted sites.

**OpenAI is whitelisted ✅** - Your app will work on free tier!

**Workaround for other APIs:**
- Upgrade to Hacker ($5/month) for unrestricted API access

---

### **2. CPU Time Limits**

**Problem:** Free tier gets limited CPU seconds per day.

**Impact:** AI API calls might timeout if too slow.

**Workarounds:**
- Set shorter timeouts in code
- Upgrade to paid tier for more CPU
- Use Smart Response (60% quick replies = less AI load)

---

### **3. File Upload Limits**

**Problem:** Free tier has 512MB storage, paid tiers have more.

**Impact:** Database files can grow large.

**Workarounds:**
```bash
# Monitor database size
du -sh databases/*.db

# Vacuum to compress (run monthly)
sqlite3 databases/production_integrated_users.db "VACUUM;"
sqlite3 databases/production_smart_response.db "VACUUM;"
```

---

### **4. No Background Tasks**

**Problem:** Can't run scheduled tasks (cron jobs) on free tier.

**Impact:** No automatic backups.

**Workarounds:**
- Manual backups (download databases weekly)
- Upgrade to paid tier for scheduled tasks
- Use external backup service

---

### **5. Session Timeout**

**Problem:** Long AI responses might timeout.

**Impact:** Very long conversations might fail.

**Workarounds:**
- Already handled in code (120s timeout)
- Keep responses concise
- Smart Response helps (quick replies don't timeout)

---

## **Database Backup Strategy for PythonAnywhere**

### **Manual Backup (Weekly Recommended)**

**Via Files Tab:**
1. Go to "Files" tab
2. Navigate to `/home/yourusername/ai-model-compare/databases/`
3. Right-click on `production_integrated_users.db`
4. Select "Download"
5. Repeat for `production_smart_response.db`
6. Save to your local computer with date in filename:
   - `integrated_users_backup_2025-12-09.db`
   - `smart_response_backup_2025-12-09.db`

**Via Bash Console:**
```bash
cd ~/ai-model-compare/databases

# Create backup with timestamp
DATE=$(date +%Y%m%d)
sqlite3 production_integrated_users.db ".backup 'backup_users_$DATE.db'"
sqlite3 production_smart_response.db ".backup 'backup_smart_$DATE.db'"

# Compress for download
tar -czf backup_$DATE.tar.gz backup_*_$DATE.db
rm backup_*_$DATE.db

# Download via Files tab or use zip command
```

---

### **Automatic Backup (Paid Tier Only)**

If you upgrade to paid tier with scheduled tasks:

```bash
# Create backup script
nano ~/backup_databases.sh
```

**Script content:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
cd /home/yourusername/ai-model-compare/databases

sqlite3 production_integrated_users.db ".backup '/home/yourusername/backups/users_$DATE.db'"
sqlite3 production_smart_response.db ".backup '/home/yourusername/backups/smart_$DATE.db'"

# Keep only last 7 days
find /home/yourusername/backups -name "users_*.db" -mtime +7 -delete
find /home/yourusername/backups -name "smart_*.db" -mtime +7 -delete
```

**Make executable:**
```bash
chmod +x ~/backup_databases.sh
```

**Schedule daily (in PythonAnywhere Tasks tab):**
```
Schedule: Daily at 03:00
Command: /home/yourusername/backup_databases.sh
```

---

## **Updating Your App**

### **Pull Latest Code from GitHub:**

```bash
# Open Bash console
cd ~/ai-model-compare

# Pull updates
git pull origin main

# Reinstall dependencies if requirements.txt changed
workon aimodelcompare
pip install -r requirements.txt

# Reload web app
# Go to Web tab and click "Reload" button
```

---

### **Update Environment Variables:**

```bash
cd ~/ai-model-compare
nano .env
# Make your changes
# Save with Ctrl+X, Y, Enter

# Reload web app in Web tab
```

---

## **Monitoring Your App**

### **Check Error Logs:**

**Via Web Tab:**
1. Go to "Web" tab
2. Scroll to "Log files"
3. Click on error log link
4. View recent errors

**Via Bash Console:**
```bash
# View last 50 lines of error log
tail -50 /var/log/yourusername.pythonanywhere.com.error.log

# Follow log in real-time (Ctrl+C to stop)
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

---

### **Check Application Logs:**

```bash
cd ~/ai-model-compare
tail -50 logs/app.log
```

---

### **Monitor Database Size:**

```bash
cd ~/ai-model-compare
du -sh databases/*.db
du -sh conversations/
du -sh user_profiles/

# Total usage
du -sh .
```

---

## **Troubleshooting**

### **Issue: "ImportError: No module named flask"**

**Solution:**
```bash
workon aimodelcompare
pip install flask
# Reload web app
```

---

### **Issue: "No such file or directory: .env"**

**Solution:**
```bash
cd ~/ai-model-compare
nano .env
# Add your environment variables
# Save and reload
```

---

### **Issue: "Database is locked"**

**Solution:**
```bash
# Check if old process is running
ps aux | grep python

# Kill old processes (replace PID)
kill -9 <PID>

# Reload web app
```

---

### **Issue: "OpenAI API error / Invalid API key"**

**Solution:**
```bash
cd ~/ai-model-compare
nano .env
# Verify OPENAI_API_KEY is correct (starts with sk-)
# No spaces, no quotes around the key
# Save and reload
```

---

### **Issue: "500 Internal Server Error"**

**Solution:**
```bash
# Check error log
tail -50 /var/log/yourusername.pythonanywhere.com.error.log

# Common causes:
# 1. Missing .env file
# 2. Wrong virtual environment path
# 3. Missing dependencies
# 4. Wrong WSGI configuration
```

---

### **Issue: "Static files not loading (CSS/JS)"**

**Solution:**
1. Go to Web tab
2. Check "Static files" section
3. Verify path: `/home/yourusername/ai-model-compare/static`
4. Test URL: `http://yourusername.pythonanywhere.com/static/conversation_box.js`

---

### **Issue: "Database tables don't exist"**

**Solution:**
```bash
cd ~/ai-model-compare
workon aimodelcompare

# Test database creation
python3 -c "from app import integrated_db; print('Database initialized')"

# Verify tables exist
sqlite3 databases/production_integrated_users.db ".tables"
```

---

## **Performance Optimization for PythonAnywhere**

### **1. Enable Smart Response (Already Enabled)**

Smart Response reduces AI API calls by 60%, which helps with:
- ✅ Faster responses
- ✅ Less CPU usage
- ✅ Lower costs
- ✅ Fewer timeouts

**It's already enabled by default** in `ConversationBox.js` (`includeContext: true`)

---

### **2. Optimize Database Queries**

```bash
# Monthly database maintenance
cd ~/ai-model-compare
sqlite3 databases/production_integrated_users.db
VACUUM;
ANALYZE;
.quit

sqlite3 databases/production_smart_response.db
VACUUM;
ANALYZE;
.quit
```

---

### **3. Monitor AI Usage**

```bash
# Check AI usage logs
cd ~/ai-model-compare
sqlite3 databases/production_smart_response.db "SELECT COUNT(*), SUM(cost) FROM ai_usage_log WHERE DATE(timestamp) = DATE('now');"
```

---

### **4. Clear Old Conversations (If Storage Fills Up)**

```bash
# Check storage
du -sh conversations/

# Delete conversations older than 90 days
find conversations/ -name "*.json" -mtime +90 -delete

# Or move to archive
mkdir ~/conversation_archive
find conversations/ -name "*.json" -mtime +90 -exec mv {} ~/conversation_archive/ \;
```

---

## **Migrating from PythonAnywhere to Railway Later**

### **Export Your Data:**

```bash
# On PythonAnywhere Bash console
cd ~/ai-model-compare/databases

# Create full backup
tar -czf migration_backup.tar.gz *.db

# Download via Files tab
# The file will be at: /home/yourusername/ai-model-compare/databases/migration_backup.tar.gz
```

### **Import to Railway:**

1. Deploy app to Railway (follow Railway instructions)
2. Use Railway CLI or connect via SSH
3. Upload `migration_backup.tar.gz`
4. Extract to databases folder
5. Restart app

**Data Migration is Simple:** Both use SQLite, so databases are portable! ✅

---

## **Cost Comparison**

| Scenario | PythonAnywhere | Railway | VPS |
|----------|---------------|---------|-----|
| **Testing/Learning** | FREE ✅ | FREE ✅ | $12/month |
| **10 users** | $5/month | $5/month | $12/month |
| **100 users** | $12/month | $10-20/month | $24/month |
| **+ AI costs** | +$40-60 | +$40-60 | +$40-60 |

**Start with PythonAnywhere free tier**, then:
- Stay on PythonAnywhere if it works well
- Migrate to Railway if you need more performance
- Migrate to VPS if you need full control

---

## **Success Checklist**

After deployment, verify:

- [ ] App loads at `http://yourusername.pythonanywhere.com`
- [ ] Can register new user
- [ ] Can login
- [ ] All 8 characters accessible
- [ ] Can send messages and get AI responses
- [ ] Messages persist after refresh
- [ ] Smart Response working ([SR] badges visible)
- [ ] Database growing (check file size)
- [ ] No errors in logs
- [ ] Backed up databases locally

---

## **Quick Commands Reference**

```bash
# Open bash console and activate environment
workon aimodelcompare
cd ~/ai-model-compare

# Pull latest code
git pull

# Update dependencies
pip install -r requirements.txt

# Check logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Database backup
sqlite3 databases/production_integrated_users.db ".backup 'backup.db'"

# Check database size
du -sh databases/

# Reload app (then go to Web tab and click Reload button)
```

---

## **Support Resources**

- **PythonAnywhere Help:** https://help.pythonanywhere.com
- **PythonAnywhere Forums:** https://www.pythonanywhere.com/forums/
- **Flask on PythonAnywhere:** https://help.pythonanywhere.com/pages/Flask/
- **Your App Documentation:** See other .md files in project

---

**Ready to deploy!** Follow the steps above and you'll have your app running on PythonAnywhere in about 20-30 minutes.

Remember: You can always migrate to Railway or VPS later - the databases are portable!
