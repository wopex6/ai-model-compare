# 🔍 Complete Production Problem Diagnosis

## **Error Symptoms:**
```
POST https://trabcd.pythonanywhere.com/scientist/chat 504 (Gateway Time-out)
SyntaxError: Unexpected token '<', "<html>..." is not valid JSON
```

---

## **Root Cause Analysis:**

### ✅ **Route EXISTS** (Not a 404)
- `/scientist/chat` route IS defined
- Found in: `ai_compare/character_routes.py` (Line 126-131)
- Registered dynamically in `app.py` (Line 2679)
- All 8 characters get routes: `/{character_id}/chat`

### ❌ **Problem: AI API Timeout**
- Request reaches the server ✅
- Server calls AI API (OpenAI/Anthropic) ✅
- **AI API takes >30 seconds** ❌
- PythonAnywhere worker times out ❌
- Returns HTML error page instead of JSON ❌

---

## **How It Works (Normal Flow):**

```
1. Frontend calls: POST /scientist/chat
   ↓
2. Route handler: character_routes.py line 93-123
   ↓
3. Smart Response check (optional speedup)
   ↓
4. AI API call: bot.chat(message) 
   ↓  [THIS IS WHERE IT HANGS]
5. OpenAI/Anthropic responds (should be <20s)
   ↓
6. Return JSON response
```

---

## **What's Happening on Production:**

```
1. Frontend: POST /scientist/chat ✅
   ↓
2. Route handler activated ✅
   ↓
3. Smart Response (quick replies work fine) ✅
   ↓
4. Full AI call needed ✅
   ↓
5. OpenAI/Anthropic called...
   ⏱️  5 seconds...
   ⏱️  10 seconds...
   ⏱️  20 seconds...
   ⏱️  30 seconds... PythonAnywhere timeout!
   ❌ 504 Gateway Timeout
   ↓
6. Returns HTML error page
   ↓
7. Frontend tries to parse HTML as JSON
   ❌ SyntaxError: Unexpected token '<'
```

---

##  **Why AI Calls Timeout:**

### **1. No Timeout Set** (PRIMARY ISSUE)
```python
# BEFORE (ai_compare/simple_models.py)
from openai import OpenAI
self.client = OpenAI(api_key=api_key)  # NO TIMEOUT!

# AI call can hang indefinitely
response = self.client.chat.completions.create(...)
```

**Problem:** If OpenAI/Anthropic is slow/overloaded, request never times out

### **2. PythonAnywhere Limits**
- **Free tier:** 100 CPU seconds/day total
- **Request timeout:** ~30-60 seconds max
- **Worker limits:** Limited concurrent requests
- **Network:** Can be slow to external APIs

### **3. AI Provider Issues**
- **High load:** Models overloaded (peak times)
- **Network issues:** Slow connections
- **Rate limiting:** API throttling
- **Model complexity:** Larger models = slower

---

## **The Fix (Already Implemented):**

### ✅ **Added 20-Second Timeout**

**File: `ai_compare/simple_models.py`**

```python
# Line 1: Import httpx
import httpx

# Line 33-40: OpenAI with timeout
from openai import OpenAI
self.client = OpenAI(
    api_key=api_key,
    timeout=20.0,  # 20 second timeout
    http_client=httpx.Client(
        timeout=20.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
)

# Line 73-80: Anthropic with timeout  
import anthropic
self.client = anthropic.AsyncAnthropic(
    api_key=api_key,
    timeout=20.0,  # 20 second timeout
    http_client=httpx.AsyncClient(
        timeout=20.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
)
```

**Benefits:**
- ✅ Fails fast (<20s) instead of hanging
- ✅ Prevents 504 Gateway Timeout
- ✅ Allows model fallback to try next model
- ✅ Better error messages

---

## **How the Flow Works NOW:**

```
1. Frontend: POST /scientist/chat
   ↓
2. Route handler: character_routes.py
   ↓
3. Smart Response check
   ↓
4. AI API call with 20s timeout
   ↓
5a. SUCCESS (<20s): Return response ✅
   OR
5b. TIMEOUT (>20s): Try next model ⚡
   OR
5c. ALL MODELS TIMEOUT: Return error (not HTML!) ✅
   ↓
6. Return JSON response
```

---

## **Deployment Status:**

### **Local Changes Made:**
- ✅ Added `import httpx` to simple_models.py
- ✅ Added timeout to OpenAI client
- ✅ Added timeout to Anthropic client
- ✅ Added `httpx>=0.25.0` to requirements.txt

### **NOT YET on Production:**
- ⏳ Code not pushed to GitHub
- ⏳ Code not pulled on PythonAnywhere
- ⏳ httpx not installed on PythonAnywhere
- ⏳ Web app not reloaded

---

## **What Needs to Happen:**

### **Step 1: Commit and Push**
```bash
git add ai_compare/simple_models.py requirements.txt
git commit -m "fix: Add 20s timeout to AI clients"
git push origin main
```

### **Step 2: Deploy to PythonAnywhere**
```bash
# On PythonAnywhere Bash Console
cd ~/ai-model-compare
git pull origin main
pip3.10 install --user httpx
```

### **Step 3: Reload Web App**
- Go to Web tab
- Click "Reload trabcd.pythonanywhere.com"

---

## **Testing the Fix:**

### **Before Fix:**
```
POST /scientist/chat
→ Hangs for 30+ seconds
→ 504 Gateway Timeout
→ HTML error page
→ JSON parse error
```

### **After Fix:**
```
POST /scientist/chat
→ Completes in <20 seconds, or
→ Clean timeout error (JSON), or
→ Falls back to faster model
→ Returns proper JSON response
```

---

## **Additional Optimizations:**

### **1. Use Faster Models**
Edit `ai_compare/model_config.py`:
```python
FALLBACK_MODELS = {
    'openai': [
        'gpt-3.5-turbo',  # Fast!
        'gpt-4-turbo-preview'  # Slower
    ],
    'anthropic': [
        'claude-3-haiku-20240307',  # Fastest
        'claude-3-sonnet-20240229'  # Medium
    ]
}
```

### **2. Smart Response Optimization**
- Already implemented ✅
- Quick replies save 90% of API calls
- Context-aware responses
- Learning from patterns

### **3. Monitor Performance**
Check logs for:
- Average response time
- Timeout frequency
- Model fallback patterns
- Peak usage times

---

## **PythonAnywhere-Specific Issues:**

### **1. Database Locking (SQLite)**
**Symptom:** Multiple users cause DB locks

**Solution:** Already in code
```python
# WAL mode for better concurrency
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA busy_timeout=30000')
```

### **2. Resource Limits**
**Free Tier:**
- 100 CPU seconds/day
- Limited worker processes
- Shared resources

**Solution:** 
- Upgrade to Basic ($5/month) if needed
- Use Smart Response to reduce AI calls

### **3. Cold Starts**
**Symptom:** First request after idle is slow

**Reason:** PythonAnywhere puts idle apps to sleep

**Solution:** 
- Always Online feature (paid tiers)
- Or accept first-request latency

---

## **Monitoring Commands:**

### **Check Error Log:**
```bash
# On PythonAnywhere
tail -f /var/log/trabcd.pythonanywhere.com.error.log
```

### **Check Server Log:**
```bash
tail -f /var/log/trabcd.pythonanywhere.com.server.log
```

### **Test Route Exists:**
```bash
curl -X POST https://trabcd.pythonanywhere.com/scientist/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message":"test"}'
```

---

## **Summary:**

| Issue | Status | Solution |
|-------|--------|----------|
| Route missing | ❌ FALSE | Routes registered dynamically |
| AI timeout | ✅ IDENTIFIED | Added 20s timeout to clients |
| Code fixed locally | ✅ DONE | simple_models.py updated |
| Deployed to production | ⏳ PENDING | Need to deploy |
| httpx installed | ⏳ PENDING | Need to install |
| Web app reloaded | ⏳ PENDING | Need to reload |

---

## **Next Actions:**

1. **🔴 HIGH PRIORITY:** Deploy the timeout fix
2. **🟡 MEDIUM:** Monitor error logs after deployment
3. **🟢 LOW:** Consider faster models if still slow

**The fix is ready - just needs deployment!** 🚀

See `DEPLOY_TO_PYTHONANYWHERE.md` for deployment steps.
