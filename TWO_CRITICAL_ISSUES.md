# 🚨 Two Critical Issues - Analysis & Fixes

## **Issue 1: Production Still Hanging** ⏱️

### **Status:**
We've fixed:
- ✅ `models.py` - Added 20s timeout for chat API
- ✅ `model_discovery.py` - Added 10s timeout for discovery API
- ✅ `trait_inference.py` - Added missing file

**BUT production still hangs!**

### **Possible Causes:**

#### **A. httpx Not Installed on Production** ⚠️
Even though we fixed the code, if `httpx` isn't installed, the timeouts won't work!

**Check:**
```bash
# On PythonAnywhere
python3.10 -c "import httpx; print(httpx.__version__)"
```

**Fix:**
```bash
pip3.10 install --user httpx
```

#### **B. Code Not Pulled on Production** ⚠️
Production might still have the old code without timeouts.

**Check:**
```bash
# On PythonAnywhere
cd ~/ai-model-compare
git log -1 --oneline
# Should show: ed26984 fix: Add timeout to model_discovery...
```

**Fix:**
```bash
git pull origin main
```

#### **C. App Not Reloaded** ⚠️
Even if code is pulled, Flask app needs reload to use new code.

**Fix:**
- Go to PythonAnywhere Web tab
- Click "Reload trabcd.pythonanywhere.com"

#### **D. Google Gemini Hanging** 🔍
Google's `genai` library doesn't support timeouts the same way!

**Check `models.py` line 106:**
```python
genai.configure(api_key=api_key)  # No timeout possible!
```

**If using Gemini, it might be the culprit!**

#### **E. Database Locks** 🔒
SQLite can have locking issues with multiple concurrent requests.

**Check error logs:**
```bash
tail -50 /var/log/trabcd.pythonanywhere.com.error.log
```

Look for: "database is locked"

#### **F. PythonAnywhere Worker Limits** 🚫
Free tier has very limited concurrent requests.

**Symptoms:**
- Works for first request
- Hangs on simultaneous requests
- Works after waiting

---

## **Issue 2: Local Conversation Not Retained** 💾

### **Problem:**
Conversations don't persist between sessions (server restarts).

### **Root Cause:**

```python
# app.py line 195
message_history = message_histories.get(history_key, [])
```

`message_histories` is an **in-memory dictionary** that's cleared on restart!

```python
# app.py line 157 (top of file)
message_histories = {}  # ← Lost on server restart!
```

### **Why It Happens:**

1. **Server starts** → `message_histories = {}` (empty)
2. **User chats** → Adds to `message_histories` (in RAM)
3. **Also saves to database** (dual-layer history system) ✅
4. **Server restarts** → `message_histories = {}` (empty again!)
5. **User returns** → Loads from `message_histories` → **Empty!** ❌

Even though conversations are saved to the database, they're never loaded back into memory!

### **The Fix:**

We need to load conversation history from database when user starts chatting:

```python
# In process_with_smart_response function (around line 195)

# Get message history for this user/character
history_key = f"{user_id}_{character_name}" if user_id else None

# Check in-memory cache first
message_history = message_histories.get(history_key, []) if history_key else []

# If empty and user is authenticated, load from database
if not message_history and user_id and history_key and history_system:
    try:
        # Load last 20 messages from dual-layer history
        db_history = history_system.get_conversation_history(
            user_id, character_name, limit=20
        )
        
        # Convert to message_history format
        message_history = []
        for msg in db_history:
            message_history.append({
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['timestamp']
            })
        
        # Cache in memory for this session
        message_histories[history_key] = message_history
        
        print(f"📚 Loaded {len(message_history)} messages from database for {character_name}")
    except Exception as e:
        print(f"⚠️ Failed to load history from database: {e}")
        message_history = []
```

---

## **Diagnostic Steps:**

### **For Production Hang:**

Run this diagnostic script on PythonAnywhere:
```bash
cd ~/ai-model-compare
python3.10 diagnose_production_hang.py
```

This will check:
1. ✅ httpx installed?
2. ✅ Timeout code present in models.py?
3. ✅ Timeout code present in model_discovery.py?
4. ✅ API keys configured?
5. ✅ Can create AsyncOpenAI with timeout?
6. ✅ Can discover models?
7. ✅ Can chat?
8. ✅ Database accessible?

### **For Conversation Retention:**

Check if history is actually being saved:
```python
# On PythonAnywhere Python console
from smart_response.dual_layer_history import DualLayerHistorySystem
history = DualLayerHistorySystem()

# Check if conversations exist
user_id = 1  # Replace with actual user ID
conversations = history.get_conversation_history(user_id, "scientist", limit=20)
print(f"Found {len(conversations)} messages")
```

---

## **Quick Fixes to Deploy:**

### **Fix 1: Ensure Production Has Latest Code**
```bash
# On PythonAnywhere
cd ~/ai-model-compare
git pull origin main
pip3.10 install --user httpx
python3.10 diagnose_production_hang.py
# Then reload web app
```

### **Fix 2: Add Conversation History Loading**
```python
# Will create fix in app.py to load from database
```

---

## **Priority:**

### **🔴 URGENT - Production Hang:**
1. Run diagnostic script on production
2. Check if httpx is installed
3. Check if latest code is pulled
4. Check if app is reloaded
5. Check error logs for specific error

### **🟡 IMPORTANT - Conversation Retention:**
1. Implement database loading in process_with_smart_response
2. Test locally
3. Deploy to production

---

## **Files to Check/Fix:**

| Issue | File | Action |
|-------|------|--------|
| Production hang | PythonAnywhere server | Run diagnostics |
| Production hang | Check httpx install | `pip3.10 install --user httpx` |
| Production hang | Check error logs | `tail -50 /var/log/...` |
| Conversation | `app.py` | Add DB loading logic |
| Both | Test thoroughly | Local → Production |

---

## **Next Steps:**

1. **Run diagnostic on production** - See exact cause
2. **Fix conversation loading** - Implement DB loading
3. **Test locally** - Verify both issues fixed
4. **Deploy to production** - One final deployment
5. **Monitor** - Check logs for any remaining issues

Let's start with the diagnostic to identify the exact cause of the hang!
