# Update Database on PythonAnywhere
## Quick guide to update your production database

---

## **⚠️ IMPORTANT: Backup First!**

Before updating, **always backup** your current production database:

### **Step 1: Backup Current Production Database**

**In PythonAnywhere Bash Console:**
```bash
cd ~/ai-model-compare/databases

# Create backup with timestamp
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 production_integrated_users.db ".backup 'backup_users_$DATE.db'"
sqlite3 production_smart_response.db ".backup 'backup_smart_$DATE.db'"

# List backups to confirm
ls -lh backup_*.db
```

**Or download via Files tab:**
1. Go to PythonAnywhere "Files" tab
2. Navigate to `/home/yourusername/ai-model-compare/databases/`
3. Right-click on `production_integrated_users.db` → Download
4. Right-click on `production_smart_response.db` → Download
5. Save with date: `backup_users_2025-12-09.db`

---

## **Option A: Upload Entire Database** (Simplest)

If you want to replace the entire database with your local version:

### **Step 1: Prepare Local Database**

**On your Windows machine:**
```powershell
cd "c:\Users\trabc\CascadeProjects\ai-model-compare - Claude"

# Your local databases should be:
# - integrated_users.db
# - smart_response.db

# Verify they exist and are recent
Get-ChildItem *.db | Select-Object Name, Length, LastWriteTime
```

### **Step 2: Upload to PythonAnywhere**

**Method 1: Via Files Tab (Easier)**
1. Go to PythonAnywhere "Files" tab
2. Navigate to: `/home/yourusername/ai-model-compare/databases/`
3. Click "Upload a file"
4. Upload `integrated_users.db`
5. After upload, **rename** it to `production_integrated_users.db`
6. Repeat for `smart_response.db` → rename to `production_smart_response.db`
7. Confirm overwrite if asked

**Method 2: Via SCP (If you have it)**
```bash
# From your local machine
scp integrated_users.db yourusername@ssh.pythonanywhere.com:~/ai-model-compare/databases/production_integrated_users.db
scp smart_response.db yourusername@ssh.pythonanywhere.com:~/ai-model-compare/databases/production_smart_response.db
```

### **Step 3: Reload Web App**

1. Go to PythonAnywhere "Web" tab
2. Click the big green **"Reload"** button
3. Wait for reload to complete

### **Step 4: Test**

1. Visit your app: `http://yourusername.pythonanywhere.com`
2. Login with an account
3. Check that data is correct
4. Send a test message
5. Verify everything works

---

## **Option B: Merge Specific Data** (Selective)

If you want to add specific users or data without replacing everything:

### **Step 1: Export Data from Local Database**

**On your Windows machine:**
```powershell
# Export users table
sqlite3 integrated_users.db ".mode csv" ".output users_export.csv" "SELECT * FROM users;"

# Export specific table (example: recent messages)
sqlite3 integrated_users.db ".mode csv" ".output messages_export.csv" "SELECT * FROM user_messages WHERE created_at > '2025-12-01';"
```

### **Step 2: Upload CSV to PythonAnywhere**

1. Go to PythonAnywhere "Files" tab
2. Navigate to: `/home/yourusername/ai-model-compare/`
3. Upload `users_export.csv`

### **Step 3: Import Data**

**In PythonAnywhere Bash Console:**
```bash
cd ~/ai-model-compare

# Import users (careful - check for duplicates)
sqlite3 databases/production_integrated_users.db <<EOF
.mode csv
.import users_export.csv users_temp
-- Merge avoiding duplicates
INSERT OR IGNORE INTO users SELECT * FROM users_temp;
DROP TABLE users_temp;
EOF

# Reload web app
```

---

## **Option C: Schema Updates Only** (If tables changed)

If you added new tables or columns:

### **Step 1: Get Schema from Local Database**

**On your Windows machine:**
```powershell
# Export schema
sqlite3 integrated_users.db ".schema" > schema.sql

# Or specific table
sqlite3 integrated_users.db ".schema user_sessions" > sessions_schema.sql
```

### **Step 2: Upload and Apply**

**Upload schema.sql to PythonAnywhere, then in Bash Console:**
```bash
cd ~/ai-model-compare

# Check current schema
sqlite3 databases/production_integrated_users.db ".schema users"

# Apply schema changes (example: add column)
sqlite3 databases/production_integrated_users.db <<EOF
ALTER TABLE users ADD COLUMN new_field TEXT;
EOF

# Or run full schema file (careful!)
# sqlite3 databases/production_integrated_users.db < schema.sql
```

---

## **Quick Update Script**

For regular updates, create this script:

**On PythonAnywhere, create `update_db.sh`:**
```bash
#!/bin/bash
cd ~/ai-model-compare/databases

# Backup first
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 production_integrated_users.db ".backup 'backup_users_$DATE.db'"
sqlite3 production_smart_response.db ".backup 'backup_smart_$DATE.db'"

echo "✅ Backup created: backup_*_$DATE.db"
echo ""
echo "Now upload your new databases to:"
echo "  /home/$(whoami)/ai-model-compare/databases/"
echo ""
echo "Files to upload:"
echo "  1. integrated_users.db → production_integrated_users.db"
echo "  2. smart_response.db → production_smart_response.db"
echo ""
echo "After upload, reload web app in Web tab"
```

**Make executable:**
```bash
chmod +x ~/ai-model-compare/update_db.sh
```

**Run before each update:**
```bash
~/ai-model-compare/update_db.sh
```

---

## **Verify Database After Update**

**Check record counts:**
```bash
cd ~/ai-model-compare

# Check users
sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) as users FROM users;"

# Check sessions
sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) as sessions FROM user_sessions;"

# Check messages
sqlite3 databases/production_integrated_users.db "SELECT COUNT(*) as messages FROM user_messages;"

# Check database size
du -sh databases/*.db
```

**Check recent data:**
```bash
# Most recent users
sqlite3 databases/production_integrated_users.db "SELECT id, username, created_at FROM users ORDER BY created_at DESC LIMIT 5;"

# Recent messages
sqlite3 databases/production_integrated_users.db "SELECT user_id, character_id, created_at FROM user_messages ORDER BY created_at DESC LIMIT 5;"
```

---

## **Rollback if Something Goes Wrong**

If the update causes issues:

**Restore from backup:**
```bash
cd ~/ai-model-compare/databases

# Find your backup
ls -lh backup_*.db

# Restore (replace DATE with your backup timestamp)
cp backup_users_YYYYMMDD_HHMMSS.db production_integrated_users.db
cp backup_smart_YYYYMMDD_HHMMSS.db production_smart_response.db

# Reload web app
```

---

## **Common Update Scenarios**

### **Scenario 1: New Users Added Locally**

Upload entire database OR export/import just the users table:
```bash
# Export locally
sqlite3 integrated_users.db ".mode csv" ".output new_users.csv" "SELECT * FROM users WHERE created_at > '2025-12-09';"

# Upload and import on PythonAnywhere
sqlite3 databases/production_integrated_users.db ".mode csv" ".import new_users.csv users"
```

### **Scenario 2: Fixed Smart Response Configuration**

The Smart Response configurations are in the code (Python files), not the database.

**Just update code:**
```bash
cd ~/ai-model-compare
git pull origin main
# Reload web app
```

### **Scenario 3: Database Schema Changed**

If you added new tables or modified structure:

**Export schema:**
```powershell
# Local
sqlite3 integrated_users.db ".schema" > full_schema.sql
```

**Apply on PythonAnywhere:**
```bash
# Review differences first
sqlite3 databases/production_integrated_users.db ".schema" > current_schema.sql
diff current_schema.sql full_schema.sql

# Apply changes manually (safer than running full schema)
```

### **Scenario 4: Testing New Features**

If testing requires fresh data:

**Create test database:**
```bash
cd ~/ai-model-compare/databases

# Backup production
cp production_integrated_users.db production_integrated_users.db.backup

# Copy fresh database for testing
cp ~/uploaded_test.db production_integrated_users.db

# Test features
# If good, keep it
# If bad, restore backup
```

---

## **Best Practices**

1. **Always backup before updating** ✅
2. **Test locally first** ✅
3. **Update during low-traffic hours** ✅
4. **Keep backups for at least 7 days** ✅
5. **Document what changed** ✅
6. **Test immediately after update** ✅
7. **Monitor error logs after update** ✅

---

## **Checklist for Database Update**

- [ ] Backup current production database (download or copy)
- [ ] Verify local database is ready
- [ ] Upload new database to PythonAnywhere
- [ ] Rename to production_integrated_users.db
- [ ] Reload web app
- [ ] Test login
- [ ] Test sending messages
- [ ] Check error logs
- [ ] Verify data is correct
- [ ] Monitor for 1 hour

---

## **Quick Commands Reference**

```bash
# Backup
cd ~/ai-model-compare/databases
sqlite3 production_integrated_users.db ".backup 'backup_$(date +%Y%m%d).db'"

# Check size
du -sh *.db

# Count records
sqlite3 production_integrated_users.db "SELECT COUNT(*) FROM users;"

# View schema
sqlite3 production_integrated_users.db ".schema users"

# Test database integrity
sqlite3 production_integrated_users.db "PRAGMA integrity_check;"

# View recent activity
sqlite3 production_integrated_users.db "SELECT * FROM users ORDER BY id DESC LIMIT 5;"
```

---

## **Need Help?**

If you run into issues:
1. Check error log: `/var/log/yourusername.pythonanywhere.com.error.log`
2. Restore from backup
3. Check database integrity: `PRAGMA integrity_check;`
4. Verify file permissions: `ls -la databases/`

---

**Ready to update? Follow Option A for the simplest approach!** 🚀
