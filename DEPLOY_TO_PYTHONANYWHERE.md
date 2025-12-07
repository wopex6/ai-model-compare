# 🚀 Deploy 504 Timeout Fix to PythonAnywhere

## **What Was Fixed:**

✅ **Added 20-second timeout** to OpenAI and Anthropic API clients  
✅ **Added httpx dependency** for timeout management  
✅ **Prevents 504 Gateway Timeout errors**  

---

## **Deployment Steps:**

### **Step 1: Commit Changes Locally**

```bash
git add ai_compare/simple_models.py
git add requirements.txt
git add FIX_504_GATEWAY_TIMEOUT.md
git add DEPLOY_TO_PYTHONANYWHERE.md

git commit -m "fix: Add 20s timeout to AI clients to prevent 504 errors

- Added httpx library for timeout management
- Set 20s timeout for OpenAI client
- Set 20s timeout for Anthropic client
- Prevents Gateway Timeout on PythonAnywhere
- Closes #504-timeout-issue"

git push origin main
```

---

### **Step 2: Update Code on PythonAnywhere**

**Open PythonAnywhere Bash Console:**

```bash
# Navigate to your project
cd ~/ai-model-compare

# Pull latest changes
git pull origin main

# Verify files updated
git log -1 --stat
```

---

### **Step 3: Install httpx Dependency**

**In the same Bash Console:**

```bash
# Install httpx for the user
pip3.10 install --user httpx

# Or if using requirements.txt
pip3.10 install --user -r requirements.txt

# Verify installation
python3.10 -c "import httpx; print(f'httpx version: {httpx.__version__}')"
```

---

### **Step 4: Reload Web App**

**Two ways to reload:**

#### **Option A: Via Web Tab (Recommended)**
1. Go to **Web** tab in PythonAnywhere dashboard
2. Find your web app (trabcd.pythonanywhere.com)
3. Click **"Reload trabcd.pythonanywhere.com"** button (green button)
4. Wait for "✓ Reloaded" message

#### **Option B: Via Bash Console**
```bash
# Reload web app from command line
touch /var/www/trabcd_pythonanywhere_com_wsgi.py
```

---

### **Step 5: Test the Fix**

**Test in browser:**
1. Go to: `https://trabcd.pythonanywhere.com/scientist`
2. Send a chat message
3. Wait for response (should be < 20 seconds)
4. Check browser console (F12) for errors

**Expected results:**
- ✅ No 504 errors
- ✅ Response within 20 seconds, or
- ✅ Clean timeout error message (not HTML)

---

## **Monitoring:**

### **Check Error Logs:**

**On PythonAnywhere:**
1. Go to **Web** tab
2. Scroll to **Log files** section
3. Click **Error log** link
4. Look for timeout-related errors

**Check for:**
- ❌ `TimeoutError` - AI API timeout (expected, will retry)
- ❌ `504 Gateway Time-out` - Should be GONE now
- ✅ `✓ AI response in X.XXs` - Success

---

## **Troubleshooting:**

### **If 504 Errors Still Occur:**

#### **1. Check httpx Installation**
```bash
python3.10 -c "import httpx; print('OK')"
```

If error, reinstall:
```bash
pip3.10 install --user --upgrade httpx
```

#### **2. Verify Code Update**
```bash
# Check if timeout is in the code
grep -n "timeout=20.0" ~/ai-model-compare/ai_compare/simple_models.py
```

Should show:
```
35:            timeout=20.0,  # 20 second timeout
37:                timeout=20.0,
75:            timeout=20.0,  # 20 second timeout
77:                timeout=20.0,
```

#### **3. Reduce Timeout Further (if needed)**
Edit `ai_compare/simple_models.py`:
```python
# Change from 20 to 15 seconds
timeout=15.0,  # 15 second timeout
```

Then reload web app.

#### **4. Check AI Provider Status**
- OpenAI Status: https://status.openai.com/
- Anthropic Status: https://status.anthropic.com/

If AI providers are down, timeouts are expected.

---

## **Alternative Solutions:**

### **If Timeouts Still Occur:**

#### **Option 1: Use Faster Models**
Edit `ai_compare/model_config.py` to prioritize faster models:
```python
'openai': ['gpt-3.5-turbo', 'gpt-4-turbo-preview'],  # 3.5 is faster
'anthropic': ['claude-3-haiku-20240307', 'claude-3-sonnet-20240229'],  # Haiku is fastest
```

#### **Option 2: Implement Queueing**
For production systems with high load:
- Use Celery or Redis Queue
- Process long requests asynchronously
- Return job ID immediately, poll for results

#### **Option 3: Upgrade PythonAnywhere Tier**
- **Free tier:** 100 seconds CPU/day, limited workers
- **Basic ($5/month):** More workers, better timeout limits
- **Hacker ($12/month):** Even more resources

---

## **Production Checklist:**

- [x] ✅ Added timeouts to AI clients
- [x] ✅ Added httpx to requirements.txt
- [x] ✅ Code committed to git
- [ ] ⏳ Code pushed to GitHub/origin
- [ ] ⏳ Code pulled on PythonAnywhere
- [ ] ⏳ httpx installed on PythonAnywhere
- [ ] ⏳ Web app reloaded
- [ ] ⏳ Tested in production
- [ ] ⏳ Monitoring error logs

---

## **Quick Commands Reference:**

```bash
# Update code
cd ~/ai-model-compare && git pull origin main

# Install dependencies
pip3.10 install --user httpx

# Reload web app
touch /var/www/trabcd_pythonanywhere_com_wsgi.py

# Check logs
tail -f /var/log/trabcd.pythonanywhere.com.error.log

# Test httpx
python3.10 -c "import httpx; print('OK')"
```

---

## **Need More Help?**

### **Common Issues:**

**Q: Still getting 504 errors**
A: Check error logs, verify httpx installed, try reducing timeout to 15s

**Q: Import error for httpx**
A: Run `pip3.10 install --user httpx` in Bash console

**Q: Code changes not taking effect**
A: Make sure you reloaded the web app (green button on Web tab)

**Q: AI responses too slow even with timeout**
A: Switch to faster models (gpt-3.5-turbo, claude-3-haiku)

---

## **Success Criteria:**

✅ **No 504 Gateway Timeout errors**  
✅ **Responses within 20 seconds**  
✅ **Graceful timeout errors if AI is slow**  
✅ **Clean error messages (JSON, not HTML)**  

**Deploy and test! The fix should resolve the 504 errors.** 🎉
