# 🚀 Deploy Phase 3.1 to Production

## **What Needs Deploying:**
1. ✅ Updated JavaScript cache version (`chatchat.html`)
2. ✅ Personality Insights Dashboard (`personality_dashboard.html`)
3. ✅ Inline interpretation display (`personality_interpretation_display.js`)
4. ✅ API endpoints for personality features
5. ✅ Database migration scripts

---

## **Quick Deploy Steps:**

### **Option 1: Git Push & Pull (Recommended)**

#### **On Local Machine:**
```bash
# 1. Check what changed
git status

# 2. Add all Phase 3.1 files
git add templates/chatchat.html
git add templates/personality_dashboard.html
git add static/personality_interpretation_display.js
git add app.py
git add integrated_database.py
git add migrate_production_phase_3_1.py
git add add_master_role.py
git add verify_production_ready.py
git add PRODUCTION_UPDATE_GUIDE.md

# 3. Commit
git commit -m "Phase 3.1: Personality Insights Dashboard + cache fix"

# 4. Push to GitHub
git push origin main
```

#### **On Production Server (PythonAnywhere):**
```bash
# 1. SSH into server
ssh yourusername@ssh.pythonanywhere.com

# 2. Navigate to project
cd ~/ai-model-compare

# 3. Pull latest changes
git pull origin main

# 4. Run database migration (if needed)
python3 migrate_production_phase_3_1.py
# Type "yes" when prompted

# 5. Promote users to Master role
python3 add_master_role.py
# Enter username when prompted

# 6. Reload web app
# Go to PythonAnywhere Web tab → Click "Reload" button
```

---

### **Option 2: Manual File Upload (If no Git)**

#### **Files to Upload:**

**Critical Files:**
1. `templates/chatchat.html` (cache version updated)
2. `templates/personality_dashboard.html` (new dashboard)
3. `static/personality_interpretation_display.js` (new feature)
4. `app.py` (personality API endpoints)
5. `integrated_database.py` (has_personality_access method)

**Migration Scripts:**
6. `migrate_production_phase_3_1.py`
7. `add_master_role.py`
8. `verify_production_ready.py`

#### **Upload Process:**
1. Go to PythonAnywhere → Files tab
2. Navigate to your project folder
3. Upload each file (overwrites existing)
4. Run migration scripts via Bash console
5. Reload web app

---

## **After Deployment:**

### **1. Verify Deployment:**
```bash
# In production Bash console
cd ~/ai-model-compare
python3 verify_production_ready.py
```

**Expected output:**
```
✅ PRODUCTION READY!
```

### **2. Test in Browser:**

**Clear browser cache:**
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Or open in **Incognito/Private mode**

**Login and check:**
1. Go to your production URL
2. Login as administrator
3. Look for **🧠 Personality Insights ⭐** button
4. Click button → Should load dashboard

**Check console (F12):**
```
multi_user_app.js?v=20251204_1310  ← New version!
✅ User has personality access! Role: administrator
✅ Personality Insights button made visible
```

---

## **Troubleshooting:**

### **Still shows old version (v=20251120_2240)?**

**On PythonAnywhere:**
1. Go to Web tab
2. Click **"Reload"** button (force reload)
3. Wait 10 seconds
4. Hard refresh browser (`Ctrl+Shift+R`)

**If still old:**
```bash
# SSH into server
cd ~/ai-model-compare

# Check file content
grep "v=2025" templates/chatchat.html

# Should show: v=20251204_1310
# If not, file didn't upload - try again
```

### **Button still not showing?**

**Check user role:**
```bash
# In production Bash console
python3 add_master_role.py

# Look at the list - is your user Master or Administrator?
# If not, enter username to promote
```

**Check browser console:**
```javascript
// In browser console (F12)
localStorage.getItem('currentUser')
// Should show: {"id":23,"username":"Wai Tse","role":"administrator"}

// If role is missing, logout and login again
```

---

## **Quick Commands Cheat Sheet:**

### **On Local Machine:**
```bash
git add .
git commit -m "Phase 3.1: Personality Insights"
git push origin main
```

### **On Production Server:**
```bash
cd ~/ai-model-compare
git pull origin main
python3 migrate_production_phase_3_1.py  # Type "yes"
python3 add_master_role.py  # Enter username
# Then reload web app in PythonAnywhere Web tab
```

### **Test:**
```bash
python3 verify_production_ready.py
```

---

## **Rollback (If Needed):**

### **Option 1: Git Rollback**
```bash
# On production server
cd ~/ai-model-compare
git log --oneline -5  # Find previous commit
git reset --hard <previous-commit-hash>
# Reload web app
```

### **Option 2: Database Rollback**
```bash
# Restore from backup
cp integrated_users.db.backup_20251204_131231 integrated_users.db
```

---

## **Success Indicators:**

✅ Console shows: `multi_user_app.js?v=20251204_1310`  
✅ Login console shows: `User data saved with role: administrator`  
✅ Dashboard button visible: `🧠 Personality Insights ⭐`  
✅ Dashboard loads without errors  
✅ No 401 authentication errors

---

## **Timeline:**

**Estimated deployment time:** 5-10 minutes
- 2 min: Git push/pull
- 2 min: Database migration
- 1 min: Promote users
- 2 min: Reload and test

---

## **Need Help?**

**Check these first:**
1. `python3 verify_production_ready.py` output
2. Browser console (F12) for JavaScript errors
3. PythonAnywhere error logs
4. Verify file uploaded correctly

**Common issues:**
- Old cache → Hard refresh browser
- Web app not reloaded → Click Reload in Web tab
- User not Master/Admin → Run add_master_role.py
- Database not migrated → Run migrate_production_phase_3_1.py
