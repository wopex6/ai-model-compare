# Production Database Update Guide - Phase 3.1

## 🎯 Overview

This guide helps you safely update your production database to support Phase 3.1 personality features.

---

## ⚠️ BEFORE YOU START

### **Requirements:**
- ✅ Python 3.7+
- ✅ Access to production database (`integrated_users.db`)
- ✅ 5-10 minutes of downtime (recommended)
- ✅ Backup access (just in case)

### **What Will Change:**
1. **Users Table** - Adds `user_role` column (master/administrator/paid/guest)
2. **Personality Tables** - Creates `personality_interpretations` table
3. **Message Usage** - Creates `message_usage` table for tracking
4. **History Secondary** - Adds personality interpretation columns

---

## 🚀 Step-by-Step Instructions

### **Step 1: Backup Current Database** ✅

The migration script automatically creates a backup, but it's good to have your own:

```bash
# Manual backup (optional but recommended)
cp integrated_users.db integrated_users.db.backup_manual
```

---

### **Step 2: Run Migration Script** 🔧

```bash
python migrate_production_phase_3_1.py
```

**What happens:**
1. 📦 Creates automatic backup with timestamp
2. 🔍 Checks what changes are needed
3. ⚠️ Asks for your confirmation
4. 🔧 Applies changes safely
5. ✅ Shows results and statistics

**Example output:**
```
🚀 Phase 3.1 Production Database Migration
======================================================================

📋 Step 1: Creating Backup
----------------------------------------------------------------------
📦 Creating backup: integrated_users.db.backup_20251204_124500
✅ Backup created successfully

🔍 Step 2: Checking Database Schema
----------------------------------------------------------------------
✅ 'user_role' column exists in users table
✅ 'personality_interpretations' table exists
✅ 'message_usage' table exists
✅ Personality columns exist in history_secondary table

✅ Database is already up to date - no migration needed
```

**If changes needed, you'll see:**
```
⚠️  4 change(s) needed:
   1. Add 'user_role' column to users table
   2. Create 'personality_interpretations' table
   3. Create 'message_usage' table
   4. Add personality columns to history_secondary table

❓ Apply these changes? (yes/no):
```

Type `yes` to proceed.

---

### **Step 3: Promote Users to Master Role** ⭐

After migration, promote specific users to Master role:

```bash
python add_master_role.py
```

**What you'll see:**
```
🔧 Adding Master Role to User System
============================================================

📋 Current User Roles:
------------------------------------------------------------
👤 JohnDoe            - guest          (ID: 1)
👤 JaneDoe            - guest          (ID: 2)
👑 Wai Tse            - administrator  (ID: 23)

============================================================
ℹ️  Master Role Features:
   ✅ All Paid User privileges (unlimited messages)
   ✅ Access to Phase 3.1 Personality Insights Dashboard
   ✅ View personality interpretations and analytics
   ✅ Enhanced personality assessment tools

❌ Does NOT include:
   ❌ Admin panel access
   ❌ User management
   ❌ System administration
============================================================

Enter username to promote to Master (or 'skip' to skip):
```

**Recommendations:**
- **Promote paid users** who should have personality access
- **Keep admins as admins** (they already have personality access)
- **Don't promote everyone** - Master is a premium feature

---

### **Step 4: Verify Migration** ✅

```bash
python test_phase_3_1.py
```

**Expected output:**
```
✅ All Phase 3.1 features are ready
✅ Database schema is correct
✅ Master role system is active
✅ 2 Master user(s) configured
```

---

### **Step 5: Restart Application** 🚀

```bash
python app.py
```

Test the features:
1. ✅ Login as Master/Admin user
2. ✅ Look for "🧠 Personality Insights ⭐" button
3. ✅ Click and verify dashboard loads
4. ✅ Test personality features

---

## 🔍 Troubleshooting

### **"Database not found" Error**
**Problem:** Script can't find `integrated_users.db`

**Solution:**
```bash
# Check current directory
pwd  # or "cd" on Windows

# Navigate to correct directory
cd /path/to/ai-model-compare - Claude

# Verify database exists
ls integrated_users.db  # or "dir integrated_users.db" on Windows
```

---

### **Migration Failed Mid-Way**
**Problem:** Error during migration

**Solution:**
```bash
# Restore from backup
cp integrated_users.db.backup_20251204_124500 integrated_users.db

# Check what went wrong
# Read error message carefully
# Fix issue, then retry
```

---

### **Can't See Personality Insights Button**
**Problem:** Button not visible after login

**Checklist:**
1. ✅ Did migration complete successfully?
2. ✅ Is user Master or Administrator role?
3. ✅ Did you hard refresh browser? (`Ctrl+Shift+R`)
4. ✅ Check console for errors (F12)

**Solution:**
```bash
# Verify user role
python add_master_role.py
# Check the list - user should be Master or Administrator

# If not, promote them
# Enter username when prompted
```

---

### **Dashboard Shows Errors**
**Problem:** Dashboard loads but shows error messages

**Common Causes:**
1. Missing tables → Re-run migration
2. No personality data → Expected for new users
3. JavaScript errors → Check browser console

**Solution:**
```bash
# Check database integrity
python test_phase_3_1.py

# If issues found, restore and re-migrate
cp integrated_users.db.backup_20251204_124500 integrated_users.db
python migrate_production_phase_3_1.py
```

---

## 📊 What Each Role Can Do

| Feature | Guest | Paid | Master | Admin |
|---------|-------|------|--------|-------|
| Chat with AI | ✅ (20/day) | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| Psychology traits | ✅ | ✅ | ✅ | ✅ |
| **Personality Insights Dashboard** | ❌ | ❌ | **✅** | **✅** |
| **Personality Interpretations** | ❌ | ❌ | **✅** | **✅** |
| **Inline Interpretation Display** | ❌ | ❌ | **✅** | **✅** |
| Admin Panel | ❌ | ❌ | ❌ | ✅ |
| User Management | ❌ | ❌ | ❌ | ✅ |

---

## 🔄 Rollback Instructions

If something goes wrong and you need to rollback:

### **Option 1: Automatic Backup**
```bash
# Find the backup
ls integrated_users.db.backup_*

# Restore (replace TIMESTAMP with actual timestamp)
cp integrated_users.db.backup_20251204_124500 integrated_users.db

# Restart app
python app.py
```

### **Option 2: Manual Backup**
```bash
# Restore your manual backup
cp integrated_users.db.backup_manual integrated_users.db

# Restart app
python app.py
```

**Note:** Rollback will:
- ❌ Remove Phase 3.1 features
- ❌ Lose any personality interpretations created after migration
- ✅ Keep user accounts and messages intact
- ✅ Keep psychology trait data intact

---

## 📝 Post-Migration Checklist

After successful migration:

- [ ] ✅ Migration script completed without errors
- [ ] ✅ At least one Master or Admin user exists
- [ ] ✅ Test login works
- [ ] ✅ Personality Insights button appears
- [ ] ✅ Dashboard loads without errors
- [ ] ✅ Backup file saved in safe location
- [ ] ✅ Application restarted and running
- [ ] ✅ Users notified of new features

---

## 🆘 Need Help?

### **Before Asking:**
1. Check console logs (browser F12)
2. Check server logs (terminal where app.py runs)
3. Run `python test_phase_3_1.py`
4. Check this guide's troubleshooting section

### **Provide This Info:**
- Error message (full text)
- Output from `python test_phase_3_1.py`
- Browser console errors (if frontend issue)
- Python version: `python --version`
- Database exists: `ls integrated_users.db`

---

## ✅ Success Indicators

You'll know everything worked when:

1. **Migration Script Says:**
   ```
   ✅ MIGRATION COMPLETE!
   ```

2. **Test Script Says:**
   ```
   ✅ All Phase 3.1 features are ready
   ```

3. **In Browser:**
   - 🧠 Personality Insights button visible (Master/Admin)
   - Dashboard loads with statistics
   - No console errors

4. **Database Shows:**
   - Master/Admin users can see personality data
   - Regular users don't see the button (correct!)

---

## 🎉 You're Done!

Your production database is now updated with Phase 3.1 features!

**Next:**
- 📢 Announce new features to Master/Admin users
- 📊 Monitor personality interpretation usage
- 🎯 Consider promoting valued users to Master role
- 📈 Track engagement with new features

**Keep your backup for at least 7 days!**
