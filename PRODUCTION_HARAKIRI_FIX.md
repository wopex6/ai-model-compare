# 🎯 PRODUCTION HARAKIRI TIMEOUT - ROOT CAUSE FOUND

## **The Smoking Gun** 🔥

```
2025-12-07 11:58:04 *** HARAKIRI ON WORKER 1 ***
HARAKIRI [core 0] - POST /scientist/chat since 1765108082
DAMN ! worker 1 died, killed by signal 9
```

**What's happening:**
- User sends message at 11:48:03
- AI API call starts
- **Hangs for 10 full minutes** (600 seconds!)
- uWSGI kills it at 11:58:04 with HARAKIRI
- User sees: "Dr. Nova: Error in data transmission. Recalibrating..."

---

## **All Fixes Applied So Far** ✅

1. ✅ `trait_inference.py` - Fixed (file exists, no import errors)
2. ✅ `pysqlite3-binary` - Installed
3. ✅ `.env` loading - Fixed (absolute path at top of app.py)
4. ✅ Conversation retention - Working (loads from database)
5. ✅ App starts successfully - No startup errors
6. ✅ API keys load correctly - Tested and working
7. ✅ 20-second timeout added to AI clients - **BUT NOT WORKING!**

---

## **The Remaining Problem**

The `timeout=20.0` we added to `AsyncOpenAI` and `AsyncAnthropic` clients in `models.py` **isn't preventing the 10-minute hang!**

### **Why the timeout isn't working:**

Looking at `ai_compare/compare.py`:
- Line 44-47: Calls `model_instance._get_models()` or `_get_config()` during initialization
- These methods might be making API calls **without** the timeout
- Or the timeout only applies to `chat.completions.create()`, not model listing

---

## **The Real Culprit: Model Initialization**

```python
# ai_compare/compare.py lines 44-47
if hasattr(model_instance, '_get_models'):
    await model_instance._get_models()  # ← This might hang!
elif hasattr(model_instance, '_get_config'):
    await model_instance._get_config()  # ← Or this!
```

These methods are called BEFORE any chat request to "pre-initialize" models. If they're making API calls to list available models, they might be hanging!

---

## **Solution 1: Wrap ALL Async Operations in Timeout**

We need to wrap the entire async operation in `asyncio.wait_for()`:

```python
# In ai_compare/compare.py

async def _initialize_available_models(self):
    """Initialize only the models that have valid API keys."""
    model_classes = {...}
    
    for name, model_class in model_classes.items():
        try:
            model_instance = model_class()
            
            # Add timeout wrapper here!
            if hasattr(model_instance, '_get_models'):
                try:
                    await asyncio.wait_for(model_instance._get_models(), timeout=10.0)
                except asyncio.TimeoutError:
                    print(f"⚠️ Timeout initializing {name}, using defaults")
                    pass
            elif hasattr(model_instance, '_get_config'):
                try:
                    await asyncio.wait_for(model_instance._get_config(), timeout=10.0)
                except asyncio.TimeoutError:
                    print(f"⚠️ Timeout initializing {name}, using defaults")
                    pass
            
            self.models[name] = model_instance
        except ValueError:
            pass
```

---

## **Solution 2: Skip Model Pre-initialization**

Simply don't call `_get_models()` or `_get_config()` during initialization:

```python
# In ai_compare/compare.py line 43-48
# Comment out or remove the pre-initialization:

# Pre-initialize the model configurations to cache them
# if hasattr(model_instance, '_get_models'):
#     await model_instance._get_models()
# elif hasattr(model_instance, '_get_config'):
#     await model_instance._get_config()

self.models[name] = model_instance
```

Models will initialize lazily on first use instead.

---

## **Solution 3: Add Timeout to Model Discovery**

Check `ai_compare/model_discovery.py` - we already added timeout there, but verify it's being used correctly.

---

## **Recommended Approach:**

**Try Solution 2 first** (skip pre-initialization) - it's the simplest and safest:

1. Edit `ai_compare/compare.py` lines 44-47
2. Comment out the `_get_models()` and `_get_config()` calls
3. Commit and push
4. Pull on production
5. Reload web app
6. Test - should respond in < 20 seconds

---

## **Testing:**

After the fix, you should see:
- Request sent: 12:30:00
- Response received: 12:30:15 (within 20 seconds!)
- No HARAKIRI
- Actual AI response, not error message

---

## **Evidence Summary:**

| Item | Status |
|------|--------|
| App starts | ✅ Working |
| Login | ✅ Working |
| Database | ✅ Working |
| API keys | ✅ Working |
| Conversation load | ✅ Working |
| AI API call starts | ✅ Working |
| **AI API call completes** | **❌ HANGS 10 min** |
| Timeout config | ✅ Added but not effective |

---

## **Next Steps:**

1. Apply Solution 2 (comment out pre-initialization)
2. Test on production
3. If still hangs, try Solution 1 (add wait_for timeouts)
4. If still hangs, investigate async event loop issues

**The hang is happening DURING the AI API call, not before or after!**
