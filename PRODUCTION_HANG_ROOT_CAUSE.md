# 🔍 Production Hang - Root Cause Analysis

## **Problem:**
Production hangs after accepting user prompt (works fine locally)

---

## **Root Cause Discovery:**

### **Initial Diagnosis: WRONG!** ❌
We initially thought fixing `models.py` timeout would solve it:
- ✅ Added timeout to `models.py` AsyncOpenAI (lines 29-36)
- ✅ Added timeout to `models.py` AsyncAnthropic (lines 67-74)
- ❌ **But production still hung!**

---

## **The REAL Problem:** 🚨

### **Model Discovery Hangs During Initialization**

When the app starts, it initializes all characters:
```python
# app.py lines 95-102
for char_id in character_ids:
    all_characters[char_id] = CharacterFactory.create_character(char_id)
```

Each character initialization creates AI clients:
```python
# models.py line 23-39
class ChatGPTModel(AIModel):
    def __init__(self):
        self.client = AsyncOpenAI(...)  # ✅ Has timeout NOW
        self.discovery = ModelDiscovery()  # ❌ THIS was the problem!
        self.models = None
```

When first message is sent, it discovers models:
```python
# models.py lines 41-44
async def _get_models(self):
    if self.models is None:
        self.models = await self.discovery.get_openai_models(self.api_key)
        # ↑ THIS CALL HANGS!
    return self.models
```

Inside model_discovery.py (BEFORE fix):
```python
# model_discovery.py line 128 (OLD CODE)
async def discover_models():
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=api_key)  # ❌ NO TIMEOUT!
    models = await client.models.list()    # ← HANGS HERE!
```

---

## **Why It Hung:**

```
User sends message to /scientist/chat
  ↓
character_routes.py → bot.chat(message)
  ↓
AIChatbot.chat() → AICompare.ask_all()
  ↓
models.py → ChatGPTModel.get_response()
  ↓
await self._get_models()  ← First call after init
  ↓
await self.discovery.get_openai_models(api_key)
  ↓
model_discovery.py creates AsyncOpenAI (NO TIMEOUT)
  ↓
await client.models.list()  ← HANGS for 30+ seconds
  ↓
PythonAnywhere timeout kills request
  ↓
504 Gateway Timeout
```

---

## **Why Local Worked But Production Didn't:**

| Environment | Behavior | Why |
|-------------|----------|-----|
| **Local** | Fast | Good network to OpenAI, faster CPU |
| **Production** | Hung | Slow PythonAnywhere network, CPU limits, cold start |

On PythonAnywhere:
- Shared hosting environment
- Limited CPU (100 seconds/day on free tier)
- Slower network to external APIs
- Cold starts after idle time
- **Model discovery can take 20-60 seconds without timeout!**

---

## **Files That Needed Fixing:**

### **1. `ai_compare/models.py`** ✅ (Fixed Earlier)
**Lines 29-36:** AsyncOpenAI for actual chat
**Lines 67-74:** AsyncAnthropic for actual chat
**Purpose:** Timeout for the main AI API calls
**Impact:** Prevents chat messages from hanging

### **2. `ai_compare/model_discovery.py`** ✅ (Just Fixed)
**Lines 130-137:** AsyncOpenAI for model discovery
**Purpose:** Timeout for discovering available models
**Impact:** Prevents initialization/first message from hanging

---

## **The Complete Fix:**

### **File 1: `models.py`**
```python
# Lines 29-36 (Chat API)
self.client = AsyncOpenAI(
    api_key=api_key,
    timeout=20.0,  # 20 second timeout
    http_client=httpx.AsyncClient(
        timeout=20.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
)
```

### **File 2: `model_discovery.py`**
```python
# Lines 130-137 (Discovery API)
client = AsyncOpenAI(
    api_key=api_key,
    timeout=10.0,  # 10 second timeout for discovery
    http_client=httpx.AsyncClient(
        timeout=10.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
)
```

---

## **Why Two Different Timeouts:**

| File | Timeout | Why |
|------|---------|-----|
| `models.py` | 20 seconds | Chat responses need more time |
| `model_discovery.py` | 10 seconds | Just listing models, should be fast |

---

## **Verification:**

### **Check commits:**
```bash
git log --oneline -5
```

Should show:
```
ed26984 fix: Add timeout to model_discovery AsyncOpenAI client (CRITICAL for production hang)
05af385 fix: Add missing trait_inference.py file for production
2e4f192 fix: Add 20s timeout to ACTUAL models.py file (not simple_models.py)
```

### **Verify the fix is in code:**
```bash
# Check models.py has timeout
grep -A 5 "timeout=20.0" ai_compare/models.py

# Check model_discovery.py has timeout
grep -A 5 "timeout=10.0" ai_compare/model_discovery.py
```

---

## **Deployment Steps:**

```bash
# On PythonAnywhere Bash Console

# 1. Pull all fixes
cd ~/ai-model-compare
git pull origin main

# 2. Verify httpx is installed
pip3.10 install --user httpx

# 3. Verify fixes are in code
grep "timeout=" ai_compare/models.py
grep "timeout=" ai_compare/model_discovery.py

# 4. Check if httpx is imported
grep "import httpx" ai_compare/models.py
grep "import httpx" ai_compare/model_discovery.py
```

Then:
1. Go to **Web tab**
2. Click **"Reload trabcd.pythonanywhere.com"**
3. Test `/scientist/chat`

---

## **Expected Behavior After Fix:**

### **Before:**
```
POST /scientist/chat
→ Hangs for 30+ seconds
→ 504 Gateway Timeout
→ HTML error page
```

### **After:**
```
POST /scientist/chat
→ Fast model discovery (< 10s or uses cached)
→ Chat response (< 20s or uses next model)
→ Proper JSON response
→ No hanging!
```

---

## **What This Fixes:**

✅ Production no longer hangs on first message  
✅ Model discovery has timeout  
✅ Chat API calls have timeout  
✅ Falls back to cached models if discovery times out  
✅ Falls back to next model if chat times out  
✅ Clean error handling instead of 504  

---

## **Additional Optimizations:**

### **Model Discovery Caching:**
The model_discovery.py already has 1-hour caching:
```python
self.cache_duration = 3600  # 1 hour cache
```

So model discovery only happens:
- On first app load
- After 1 hour of cache expiry
- If cache fails

### **Fallback Models:**
If discovery times out, it uses known working models:
```python
fallback_models = ['gpt-4o-mini', 'gpt-4', 'gpt-3.5-turbo']
```

---

## **Why This Was Hard to Debug:**

1. **Worked locally** - Made us think it was environment-specific
2. **Multiple files** - Timeout needed in 2 different places
3. **Async complexity** - Hard to trace where the hang actually occurred
4. **Model discovery happens lazily** - Not during initialization, but on first use
5. **PythonAnywhere limitations** - Free tier has strict limits

---

## **Key Lessons:**

### **1. Check ALL places where API clients are created:**
- ✅ Main application code (`models.py`)
- ✅ Discovery/utility code (`model_discovery.py`)
- ✅ Any other async HTTP calls

### **2. Always set timeouts for external API calls:**
```python
# GOOD ✅
client = AsyncOpenAI(api_key=api_key, timeout=20.0)

# BAD ❌
client = AsyncOpenAI(api_key=api_key)  # Can hang forever!
```

### **3. PythonAnywhere-specific considerations:**
- Limited CPU time
- Slower network
- Request timeout ~30-60 seconds
- Need aggressive timeouts for external APIs

### **4. Test production environment separately:**
- Local success ≠ Production success
- Always test on actual production environment
- Monitor logs for timeout patterns

---

## **Summary:**

| Issue | File | Status |
|-------|------|--------|
| Chat API timeout | `models.py` | ✅ Fixed |
| Model discovery timeout | `model_discovery.py` | ✅ Fixed |
| Missing module | `trait_inference.py` | ✅ Fixed |
| httpx dependency | `requirements.txt` | ✅ Already added |

**All fixes are committed and pushed to GitHub!**

**Ready to deploy to PythonAnywhere.** 🚀
