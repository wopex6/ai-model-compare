# PythonAnywhere Deployment Checklist
## Quick step-by-step guide - print this and check off as you go!

---

## **Before You Start**
- [ ] Have PythonAnywhere account created
- [ ] Have OpenAI API key ready
- [ ] Know your PythonAnywhere username

---

## **STEP 1: Setup (5 minutes)**

- [ ] Go to https://www.pythonanywhere.com and login
- [ ] Click "Consoles" → "Bash"
- [ ] Clone repository:
  ```bash
  git clone https://github.com/wopex6/ai-model-compare.git
  cd ai-model-compare
  ```

---

## **STEP 2: Virtual Environment (3 minutes)**

- [ ] Create virtual environment:
  ```bash
  mkvirtualenv --python=/usr/bin/python3.10 aimodelcompare
  ```
- [ ] Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
  ⏳ This takes 2-3 minutes

---

## **STEP 3: Environment Variables (2 minutes)**

- [ ] Generate secrets:
  ```bash
  python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
  python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_hex(32))"
  ```
  📝 Copy these values!

- [ ] Create .env file:
  ```bash
  nano .env
  ```

- [ ] Paste this template and fill in your keys:
  ```ini
  OPENAI_API_KEY=sk-your-actual-key-here
  SECRET_KEY=paste-generated-secret-here
  JWT_SECRET=paste-generated-secret-here
  FLASK_ENV=production
  FLASK_DEBUG=0
  DATABASE_PATH=./databases/production_integrated_users.db
  SMART_RESPONSE_DB=./databases/production_smart_response.db
  DISABLE_AUTO_DOCS=true
  LOG_LEVEL=INFO
  MAX_AI_CALLS_PER_DAY=50
  ```

- [ ] Save: `Ctrl+X` → `Y` → `Enter`

---

## **STEP 4: Create Directories (30 seconds)**

- [ ] Create data directories:
  ```bash
  mkdir -p databases logs conversations user_profiles
  ```

---

## **STEP 5: Web App Configuration (5 minutes)**

- [ ] Go to "Web" tab in PythonAnywhere
- [ ] Click "Add a new web app"
- [ ] Choose "Manual configuration" (NOT Flask!)
- [ ] Choose "Python 3.10"
- [ ] Click through to finish

---

## **STEP 6: WSGI Configuration (3 minutes)**

- [ ] In Web tab, find "Code" section
- [ ] Click on WSGI configuration file link
- [ ] **DELETE all existing content**
- [ ] Open `pythonanywhere_wsgi.py` from your project
- [ ] **COPY all content** from that file
- [ ] **PASTE into WSGI config**
- [ ] **CHANGE 'yourusername' to your actual username** (3 places in the file)
- [ ] Save (Ctrl+S or File → Save)

---

## **STEP 7: Virtual Environment Path (1 minute)**

- [ ] In Web tab, find "Virtualenv" section
- [ ] Enter: `/home/yourusername/.virtualenvs/aimodelcompare`
- [ ] Replace `yourusername` with yours
- [ ] Click checkmark to save

---

## **STEP 8: Static Files (1 minute)**

- [ ] In Web tab, find "Static files" section
- [ ] Click "Enter URL" → type: `/static/`
- [ ] Click "Enter path" → type: `/home/yourusername/ai-model-compare/static`
- [ ] Replace `yourusername` with yours

---

## **STEP 9: Reload and Test (2 minutes)**

- [ ] Scroll to top of Web tab
- [ ] Click big green **"Reload"** button
- [ ] Wait for reload (green checkmark appears)
- [ ] Copy your URL: `http://yourusername.pythonanywhere.com`
- [ ] Visit in browser

---

## **STEP 10: Verify Everything Works**

- [ ] Homepage loads ✅
- [ ] Click "Register" → Create account ✅
- [ ] Login with new account ✅
- [ ] Click "Scientist" character ✅
- [ ] Type "Hi" → Send ✅
- [ ] Get AI response ✅
- [ ] Refresh page → History persists ✅
- [ ] Test another character ✅

---

## **If Something Doesn't Work:**

### **Check Error Logs:**
- [ ] Go to Web tab
- [ ] Scroll to "Log files"
- [ ] Click error log link
- [ ] Look for error messages

### **Common Issues:**

**"500 Internal Server Error"**
- [ ] Check WSGI file has correct username
- [ ] Check .env file exists: `ls -la ~/ai-model-compare/.env`
- [ ] Check virtual environment path is correct

**"Module not found"**
- [ ] Activate environment: `workon aimodelcompare`
- [ ] Reinstall: `pip install -r requirements.txt`
- [ ] Reload web app

**"Invalid API key"**
- [ ] Check .env file: `nano ~/ai-model-compare/.env`
- [ ] Verify OPENAI_API_KEY starts with `sk-`
- [ ] No spaces or quotes around the key
- [ ] Reload web app

**"Static files not loading"**
- [ ] Check static files path in Web tab
- [ ] Should be: `/home/yourusername/ai-model-compare/static`
- [ ] Test URL: `http://yourusername.pythonanywhere.com/static/conversation_box.js`

---

## **Database Migration (Optional)**

### **If Starting Fresh:**
- [ ] Nothing to do! Databases create automatically ✅

### **If Migrating Existing Data:**

**On your local machine:**
- [ ] Copy databases:
  ```powershell
  cd "c:\Users\trabc\CascadeProjects\ai-model-compare - Claude"
  copy integrated_users.db databases_backup\
  copy smart_response.db databases_backup\
  ```

**On PythonAnywhere:**
- [ ] Go to "Files" tab
- [ ] Navigate to `/home/yourusername/ai-model-compare/databases/`
- [ ] Upload your database files:
  - Upload as `production_integrated_users.db`
  - Upload as `production_smart_response.db`
- [ ] Go to Web tab → Reload

**Verify migration:**
- [ ] Bash console:
  ```bash
  cd ~/ai-model-compare
  sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) FROM users;"
  ```
- [ ] Should show your user count ✅

---

## **Backup Plan (Do This Weekly!)**

- [ ] Go to "Files" tab
- [ ] Navigate to `/home/yourusername/ai-model-compare/databases/`
- [ ] Right-click `production_integrated_users.db` → Download
- [ ] Right-click `production_smart_response.db` → Download
- [ ] Save to your computer with date: `backup_2025-12-09.db`

---

## **Update Code Later**

When you push updates to GitHub:
- [ ] Bash console:
  ```bash
  cd ~/ai-model-compare
  git pull origin main
  workon aimodelcompare
  pip install -r requirements.txt
  ```
- [ ] Web tab → Reload

---

## **Monitoring Checklist (Daily for First Week)**

- [ ] Check error log for issues
- [ ] Test app still works
- [ ] Check database size: `du -sh ~/ai-model-compare/databases/`
- [ ] Monitor AI usage (check OpenAI dashboard)

---

## **Success Criteria**

✅ App loads at your URL
✅ Users can register/login
✅ All 8 characters work
✅ Chat messages send and receive
✅ History persists after refresh
✅ Smart Response working ([SR] badges)
✅ No errors in logs
✅ Database backed up locally

---

## **Migration to Railway Later (When Needed)**

When you want to migrate:
- [ ] Download databases from PythonAnywhere
- [ ] Deploy to Railway (3-minute setup)
- [ ] Upload databases to Railway
- [ ] Update DNS if using custom domain
- [ ] Test everything works
- [ ] Cancel PythonAnywhere (or keep as backup)

**Databases are portable!** SQLite files work everywhere ✅

---

## **Quick Reference**

**Your username:** `________________` (write it here!)
**Your URL:** `http://________________.pythonanywhere.com`
**Deployed on:** `________________` (date)

**Common commands:**
```bash
# Activate environment
workon aimodelcompare

# Go to project
cd ~/ai-model-compare

# Update code
git pull

# View logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Check database
sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) FROM users;"
```

---

**Estimated total time: 20-30 minutes** ⏱️

**Good luck with your deployment!** 🚀

See `PYTHONANYWHERE_DEPLOYMENT.md` for detailed troubleshooting.
