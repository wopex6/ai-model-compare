# 🚀 PythonAnywhere Deployment Checklist

## ✅ Step-by-Step Deployment

Copy and paste each command in order:

---

### **1. SSH into PythonAnywhere**
```bash
ssh yourusername@ssh.pythonanywhere.com
```
Status: [ ]

---

### **2. Navigate to Project**
```bash
cd ~/ai-model-compare
```
Status: [ ]

---

### **3. Backup Current Version** ⚠️ IMPORTANT
```bash
# Create backup directory
cp -r ~/ai-model-compare ~/ai-model-compare-backup-$(date +%Y%m%d)

# Create git tag for rollback
git tag -a v1.0-before-deploy -m "Backup before 8-char deployment"
```
Status: [ ]

---

### **4. Pull Latest Code**
```bash
# Pull from GitHub
git pull origin main
```
Expected output: `Already up to date` or `Updating...`  
Status: [ ]

---

### **5. Activate Virtual Environment**
```bash
source ~/ai-model-compare/venv/bin/activate
```
Status: [ ]

---

### **6. Update Dependencies**
```bash
pip install -r requirements.txt
```
Status: [ ]

---

### **7. Verify New Files Exist**
```bash
# Check character system files
ls ai_compare/character_factory.py
ls ai_compare/character_configs.py
ls ai_compare/base_enhanced_chatbot.py

# Check new templates
ls templates/zen_master.html
ls templates/business_coach.html
ls templates/life_coach.html
ls templates/scientist.html
```
All should show "file exists"  
Status: [ ]

---

### **8. Test Import** (optional but recommended)
```bash
python3 << EOF
from ai_compare.character_factory import CharacterFactory
print("✅ CharacterFactory imports successfully")
EOF
```
Status: [ ]

---

### **9. Go to PythonAnywhere Web Tab**

Open in browser: https://www.pythonanywhere.com/user/yourusername/webapps/

Status: [ ]

---

### **10. Reload Web App**

Click the big green **"Reload yourusername.pythonanywhere.com"** button

Wait 10-30 seconds for reload to complete

Status: [ ]

---

### **11. Test Deployment**

Visit these URLs and check each:

#### **Dashboard**
```
https://yourusername.pythonanywhere.com/chatchat
```
- [ ] Page loads
- [ ] 8 character cards visible

#### **Legacy Characters**
```
https://yourusername.pythonanywhere.com/super_motivational_coach
https://yourusername.pythonanywhere.com/wisdom_sage
https://yourusername.pythonanywhere.com/stoic_philosopher
https://yourusername.pythonanywhere.com/psychologist
```
- [ ] All load
- [ ] Chat works

#### **New Characters with Custom UIs**
```
https://yourusername.pythonanywhere.com/zen_master
```
- [ ] Loads
- [ ] Meditation timer visible
- [ ] Breathing circle animating
- [ ] Chat works

```
https://yourusername.pythonanywhere.com/business_coach
```
- [ ] Loads
- [ ] KPI cards visible (4 cards)
- [ ] Chat works

```
https://yourusername.pythonanywhere.com/life_coach
```
- [ ] Loads
- [ ] Balance wheel visible
- [ ] Vision board items visible
- [ ] Chat works

```
https://yourusername.pythonanywhere.com/scientist
```
- [ ] Loads
- [ ] Star field visible
- [ ] Scientific method steps visible
- [ ] Chat works

---

### **12. Check Error Logs**

Back in SSH console:
```bash
tail -50 ~/yourusername.pythonanywhere.com.error.log
```

Look for any errors. Common OK messages:
- Loading messages
- Session messages
- Character initialization messages

Status: [ ]

---

## 🎉 **Deployment Complete!**

If all checkboxes above are ✅, your deployment is successful!

---

## ⚠️ **If Something Went Wrong**

### **Rollback Command**:
```bash
cd ~/ai-model-compare
git reset --hard v1.0-before-deploy
# Then reload web app in Web tab
```

### **Check These**:
1. Error log: `tail -100 ~/yourusername.pythonanywhere.com.error.log`
2. Files pulled: `git log -1`
3. Dependencies: `pip list | grep Flask`

---

## 📝 **Deployment Record**

- **Date**: _____________
- **Time**: _____________
- **Deployed by**: _____________
- **Commit Hash**: e0c1ffb
- **Result**: ✅ Success / ❌ Failed / 🔄 Rolled Back

**Notes**:
___________________________________
___________________________________
___________________________________

---

**Next Steps After Successful Deployment**:
1. Test all 8 characters
2. Send test messages
3. Verify mobile responsiveness
4. Monitor for 24 hours
5. Celebrate! 🎊
