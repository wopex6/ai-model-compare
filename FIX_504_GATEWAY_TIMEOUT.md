# 🔴 Fix 504 Gateway Timeout on PythonAnywhere

## **Error Encountered:**
```
POST https://trabcd.pythonanywhere.com/scientist/chat 504 (Gateway Time-out)
SyntaxError: Unexpected token '<', "<html>..." is not valid JSON
```

---

## **Root Cause Analysis:**

### **What's Happening:**
1. ✅ User sends chat message to `/scientist/chat`
2. ⏱️ Server makes AI API call (OpenAI/Anthropic)
3. ❌ AI API takes >30 seconds (PythonAnywhere timeout)
4. ❌ Web worker times out, returns HTML error page
5. ❌ Frontend expects JSON, tries to parse HTML → Error

### **Why This Happens:**
- **No timeout set** on AI API calls
- **PythonAnywhere limits:** 30-60s request timeout
- **Network issues:** Slow connection to AI providers
- **AI provider delays:** Model overload or network issues

---

## **Solutions:**

### **1. Add Timeout to AI Clients** 🔴 **CRITICAL FIX**

#### **File: `ai_compare/simple_models.py`**

**ChatGPT Client (Line 30-31):**
```python
# BEFORE (No timeout)
from openai import OpenAI
self.client = OpenAI(api_key=api_key)

# AFTER (With 20s timeout)
from openai import OpenAI
import httpx
self.client = OpenAI(
    api_key=api_key,
    timeout=20.0,  # 20 second timeout
    http_client=httpx.Client(
        timeout=20.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
)
```

**Claude Client (Line 62-63):**
```python
# BEFORE (No timeout)
import anthropic
self.client = anthropic.AsyncAnthropic(api_key=api_key)

# AFTER (With 20s timeout)
import anthropic
import httpx
self.client = anthropic.AsyncAnthropic(
    api_key=api_key,
    timeout=20.0,  # 20 second timeout
    http_client=httpx.AsyncClient(
        timeout=20.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
)
```

---

### **2. Add Better Error Handling**

#### **Update Chat Response Functions:**

**Add to `ai_compare/simple_models.py` - Line 35-55:**
```python
async def get_response(self, prompt: str) -> str:
    """Try models in order until one works"""
    last_error = None
    
    for model in self.models:
        try:
            # Add timeout wrapper for extra safety
            async with asyncio.timeout(25):  # 25s overall timeout
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=20.0  # Per-request timeout
                )
                return response.choices[0].message.content
        except asyncio.TimeoutError:
            last_error = Exception(f"Timeout calling {model} (>25s)")
            print(f"⏱️ Timeout calling {model}")
            continue
        except Exception as e:
            last_error = e
            print(f"❌ Error with {model}: {e}")
            continue
    
    raise last_error if last_error else Exception("All OpenAI models failed")
```

---

### **3. Add Timeout Warning on Frontend**

#### **Update `templates/scientist.html` (or auth_helper.js):**

**Add timeout handling:**
```javascript
async sendMessage(message) {
    try {
        // Set a frontend timeout (30s max)
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), 30000)
        );
        
        const fetchPromise = AuthHelper.authenticatedFetch('/scientist/chat', {
            method: 'POST',
            body: JSON.stringify({ 
                message: message, 
                include_context: true 
            })
        });
        
        // Race between fetch and timeout
        const response = await Promise.race([fetchPromise, timeoutPromise]);
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('Chat error:', error);
        
        // User-friendly error messages
        if (error.message === 'Request timeout') {
            return {
                error: '⏱️ Request timed out. The AI service is taking too long. Please try again.',
                retry: true
            };
        } else if (error.message.includes('504') || error.message.includes('Gateway')) {
            return {
                error: '⏱️ Server timeout. The AI is overloaded. Please wait 30 seconds and try again.',
                retry: true
            };
        }
        
        return {
            error: '❌ An error occurred. Please try again.',
            details: error.message
        };
    }
}
```

---

### **4. Database Optimization for PythonAnywhere**

#### **SQLite Under Load:**

PythonAnywhere uses SQLite which can lock under concurrent requests.

**Add to `integrated_database.py`:**
```python
def __init__(self, db_path='integrated_users.db'):
    self.db_path = db_path
    
    # PythonAnywhere optimization
    conn = sqlite3.connect(db_path, timeout=30.0)  # 30s wait for lock
    conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
    conn.execute('PRAGMA busy_timeout=30000')  # 30s busy timeout
    conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
    conn.close()
```

---

### **5. PythonAnywhere-Specific Configuration**

#### **Create `.pythonanywhere-config.py`:**
```python
"""
PythonAnywhere-specific settings
"""

# Request timeout (lower than PA's limit)
REQUEST_TIMEOUT = 25  # seconds (PA has ~30s limit)

# AI API timeouts
AI_API_TIMEOUT = 20  # seconds
AI_API_MAX_RETRIES = 1  # Don't retry on timeout

# Database settings
DB_TIMEOUT = 30  # seconds
DB_BUSY_TIMEOUT = 30000  # milliseconds

# Worker settings
MAX_CONCURRENT_REQUESTS = 2  # Low due to PA limits

# Enable production mode
PRODUCTION = True
DEBUG = False
```

---

## **Implementation Steps:**

### **Step 1: Add httpx dependency**
```bash
pip install httpx
```

**Update `requirements.txt`:**
```
httpx>=0.25.0
```

### **Step 2: Update AI clients**
```bash
# Edit ai_compare/simple_models.py
# Add timeout parameters to OpenAI and Anthropic clients
```

### **Step 3: Update error handling**
```bash
# Add async timeout wrapper
# Add better error messages
```

### **Step 4: Update frontend**
```bash
# Add timeout handling in auth_helper.js or scientist.html
# Add retry logic
# Add user-friendly error messages
```

### **Step 5: Test locally**
```bash
python app.py
# Test with slow network simulation
```

### **Step 6: Deploy to PythonAnywhere**
```bash
# Update code on PA
pip install --user httpx
# Reload web app
```

---

## **Quick Fix (Immediate):**

If you need an immediate fix without code changes:

### **On PythonAnywhere Web Tab:**
1. **Increase worker timeout** (if available on your tier)
2. **Reload web app**
3. **Check error logs** for specific timeout issues

### **Temporary Workaround:**
- **Use shorter prompts** - Reduce AI processing time
- **Retry failed requests** - Most will succeed on 2nd try
- **Clear browser cache** - Old service workers can cause issues

---

## **Monitoring:**

### **Add logging to track timeouts:**
```python
import time

start_time = time.time()
try:
    response = await ai_client.get_response(prompt)
    elapsed = time.time() - start_time
    print(f"✅ AI response in {elapsed:.2f}s")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ AI timeout after {elapsed:.2f}s: {e}")
```

---

## **Expected Results After Fix:**

✅ **No more 504 errors** - Requests fail gracefully before timeout  
✅ **Better error messages** - Users know what happened  
✅ **Retry logic** - Automatic recovery from transient failures  
✅ **Faster responses** - Timeout forces faster model selection  
✅ **Production-ready** - Handles PythonAnywhere constraints  

---

##  **Priority Actions:**

1. **🔴 HIGH:** Add timeouts to AI clients (Step 2)
2. **🟡 MEDIUM:** Add frontend timeout handling (Step 4)
3. **🟢 LOW:** Optimize database (Step 4)

**Start with Step 2 - that's the root cause!**
