# Database Schema Migration Guide
## Update PythonAnywhere database structure to match local

---

## **What This Does**

This migrates the **database structure/schema** from your local database to PythonAnywhere:
- ✅ Adds missing tables
- ✅ Adds missing columns to existing tables
- ✅ Preserves all existing data
- ✅ Creates automatic backup
- ✅ Safe rollback if needed

**Does NOT overwrite your data** - only updates the structure!

---

## **Quick Steps**

### **Step 1: Export Schema from Local Database**

On your Windows machine:

```powershell
python export_schema.py
```

This creates:
- `database_schema.sql` - Full schema for reference
- `database_schema.json` - Schema info for migration

---

### **Step 2: Upload Schema to PythonAnywhere**

1. Go to PythonAnywhere **Files** tab
2. Navigate to: `/home/yourusername/ai-model-compare/`
3. Upload `database_schema.json`
4. Upload `apply_schema_migration.py` (if not already there)

---

### **Step 3: Apply Migration on PythonAnywhere**

In PythonAnywhere **Bash console**:

```bash
cd ~/ai-model-compare
python apply_schema_migration.py
```

The script will:
1. ✅ Create automatic backup
2. ✅ Check current schema
3. ✅ Add missing columns
4. ✅ Report missing tables (if any)
5. ✅ Optimize database
6. ✅ Show summary

---

### **Step 4: Reload Web App**

1. Go to **Web** tab
2. Click green **"Reload"** button
3. Test your application

---

## **What Gets Updated**

### **Common Schema Changes:**

#### **Smart Response Tables:**
- `interaction_history` - User interaction logs
- `user_learning_profiles` - Learning preferences
- Columns: `character`, `confidence`, `metadata`

#### **AI Budget Tables:**
- `ai_usage_log` - AI call tracking
- `ai_usage_patterns` - Pattern detection
- `ai_budget_notifications` - User alerts

#### **Dual-Layer History:**
- `history_primary` - Raw conversations
- `history_secondary` - Analysis/interpretation
- `history_progress` - Long-term tracking

#### **New Columns Added Recently:**
- `user_sessions.character_id` - Character tracking
- Various `metadata` columns - JSON data storage

---

## **Example Output**

```
======================================================================
  Schema Migration for PythonAnywhere
======================================================================

📋 Target schema: 30 tables

📦 Creating backup: databases/production_integrated_users.db.backup_20251209_223045
✅ Backup created (0.65 MB)

🔍 Analyzing current schema...
📋 Current schema: 28 tables

🔨 Checking for missing tables...
   ⚠️  Missing table: pattern_suggestions
   ⚠️  Missing table: pattern_statistics

🔨 Checking for missing columns...
   ✅ All columns present in existing tables

⚠️  WARNING: 2 tables are missing!
   These tables should be created by running the application.
   
   Run your Flask app once to auto-create missing tables.

🔧 Optimizing database...

======================================================================
  Migration Summary
======================================================================

✅ No column changes needed - schema is up to date!

📦 Backup saved at: databases/production_integrated_users.db.backup_20251209_223045

✅ Schema migration complete!

📋 Next steps:
   1. Test your application
   2. If everything works, keep the backup for 7 days
   3. If something broke, restore from backup
```

---

## **Safety Features**

### **Automatic Backup**
Before any changes, the script creates:
```
databases/production_integrated_users.db.backup_YYYYMMDD_HHMMSS
```

### **Rollback If Needed**

If something goes wrong:

```bash
cd ~/ai-model-compare/databases

# List backups
ls -lh *.backup_*

# Restore from backup
cp production_integrated_users.db.backup_20251209_223045 production_integrated_users.db

# Reload web app
```

---

## **What Gets Changed vs. What Doesn't**

### **✅ Changes Applied:**
- Missing tables created (if schema includes them)
- Missing columns added to existing tables
- Indexes updated
- Database optimized

### **❌ Does NOT Change:**
- Existing data in tables
- Existing columns
- Primary keys
- Foreign key relationships
- Your user data, messages, or conversations

---

## **Common Scenarios**

### **Scenario 1: Added New Smart Response Features**

**Local changes:**
- Added `character_preferences` column to `user_learning_profiles`
- Added `confidence_threshold` column to character config

**Migration:**
```bash
# Export local schema
python export_schema.py

# Upload to PythonAnywhere
# Run migration
python apply_schema_migration.py
```

**Result:**
```
✅ Added column: user_learning_profiles.character_preferences
✅ Added column: character_config.confidence_threshold
```

---

### **Scenario 2: Added New AI Budget Tables**

**Local changes:**
- Added `ai_budget_notifications` table
- Added `ai_usage_patterns` table

**Migration will note:**
```
⚠️  Missing table: ai_budget_notifications
⚠️  Missing table: ai_usage_patterns

Run your Flask app once to auto-create missing tables.
```

**Solution:**
Just run your web app - Flask will auto-create missing tables on startup.

---

### **Scenario 3: Updated Dual-Layer History**

**Local changes:**
- Added `version` column to `history_secondary`
- Added `analysis_model` column

**Migration:**
```
✅ Added column: history_secondary.version
✅ Added column: history_secondary.analysis_model
```

---

## **Troubleshooting**

### **Issue: "database_schema.json not found"**

**Solution:**
```bash
# Make sure file is in project directory
ls ~/ai-model-compare/database_schema.json

# If missing, upload it via Files tab
```

---

### **Issue: "Database is locked"**

**Solution:**
```bash
# Stop web app temporarily
# In Web tab, disable web app
# Run migration
python apply_schema_migration.py
# Re-enable web app
```

---

### **Issue: Migration added columns but app doesn't work**

**Solution:**
```bash
# Check error log
tail -50 /var/log/yourusername.pythonanywhere.com.error.log

# Reload web app
# Sometimes Flask needs restart to see schema changes
```

---

### **Issue: Want to undo migration**

**Solution:**
```bash
cd ~/ai-model-compare/databases

# Find your backup
ls -lh *.backup_*

# Restore it (replace with your backup filename)
cp production_integrated_users.db.backup_20251209_223045 production_integrated_users.db

# Reload web app
```

---

## **Verification**

After migration, verify schema:

```bash
cd ~/ai-model-compare

# Check tables
python -c "import sqlite3; conn = sqlite3.connect('databases/production_integrated_users.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name'); print('\n'.join([t[0] for t in cursor.fetchall()]))"

# Check specific table columns
python -c "import sqlite3; conn = sqlite3.connect('databases/production_integrated_users.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(user_learning_profiles)'); print('\n'.join([f'{c[1]}: {c[2]}' for c in cursor.fetchall()]))"
```

---

## **Files Involved**

| File | Purpose | Location |
|------|---------|----------|
| `export_schema.py` | Export schema from local | Local machine |
| `database_schema.sql` | Full schema (reference) | Generated locally |
| `database_schema.json` | Schema for migration | Upload to PythonAnywhere |
| `apply_schema_migration.py` | Apply migration | PythonAnywhere |

---

## **Best Practices**

1. **Always export schema after code changes**
   - After adding new features
   - After updating models
   - Before deploying to production

2. **Test migration locally first**
   ```powershell
   # On local machine
   python apply_schema_migration.py
   ```

3. **Keep backups for 7 days**
   - Automatic backups are timestamped
   - Delete old backups manually after 7 days

4. **Document schema changes**
   - Note what changed in commit messages
   - Update documentation

5. **Migrate during low-traffic times**
   - Migration is fast (seconds) but safe to do anytime
   - Backup + restore takes ~30 seconds

---

## **Quick Command Reference**

```bash
# Export schema (local)
python export_schema.py

# Upload to PythonAnywhere
# Via Files tab: upload database_schema.json

# Apply migration (PythonAnywhere)
cd ~/ai-model-compare
python apply_schema_migration.py

# Verify
python -c "import sqlite3; conn = sqlite3.connect('databases/production_integrated_users.db'); print('Tables:', conn.execute('SELECT COUNT(*) FROM sqlite_master WHERE type=\"table\"').fetchone()[0])"

# Rollback if needed
cp databases/production_integrated_users.db.backup_TIMESTAMP databases/production_integrated_users.db

# Check backups
ls -lh ~/ai-model-compare/databases/*.backup_*
```

---

## **Summary**

✅ **Safe** - Automatic backup before changes
✅ **Fast** - Takes seconds to run
✅ **Non-destructive** - Only adds, never removes
✅ **Reversible** - Easy rollback from backup
✅ **Automatic** - Detects and applies only needed changes
✅ **Tested** - Dry-run mode available

**Use this whenever you:**
- Add new features with database changes
- Update models/schemas locally
- Want PythonAnywhere to match local structure

---

**Ready to migrate? Run `python export_schema.py` to start!** 🚀
