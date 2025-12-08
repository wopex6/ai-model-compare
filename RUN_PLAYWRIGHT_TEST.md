# 🎭 Run Playwright Test for Conversation History

## **Quick Start:**

```powershell
# Make sure Flask is running in another terminal
python app.py

# Run the Playwright test
python playwright_history_check.py
```

The test will:
1. ✅ Open a real Chrome browser (visible, not headless)
2. ✅ Navigate to scientist page
3. ✅ Send 2 messages
4. ✅ Leave the page
5. ✅ Return to the page
6. ✅ Check if messages are still there
7. ✅ Take a screenshot
8. ✅ Stay open 10 seconds for you to inspect

---

## **What to Look For:**

### **If Test PASSES:**
```
✅ SUCCESS! History persisted!
✅ BROWSER TEST PASSED - History works in real browser!
```

### **If Test FAILS:**
```
❌ FAILURE! History NOT persisted!
Expected: 5 messages
Got: 1 messages
```

**Then check:**
1. Browser console - any red errors?
2. Network tab - was `/scientist/history?session_id=...` called?
3. Application tab → Cookies - is `session_scientist` there?
4. Screenshot: `history_check_screenshot.png`

---

## **Manual Debug Checklist:**

If Playwright test fails, open browser DevTools (F12) and check:

### **1. Console Tab:**
Look for these messages:
```javascript
✅ GOOD:
Loading history for session: scientist_20251208_...
Loaded 4 messages from history

❌ BAD:
Error loading conversation history: ...
```

### **2. Network Tab:**
Filter by "history" - should see:
```
GET /scientist/history?session_id=scientist_20251208_...
Status: 200
Response: {"messages": [...]}
```

### **3. Application Tab → Cookies:**
Should see:
```
Name: session_scientist
Value: scientist_20251208_...
Path: /
```

### **4. Application Tab → Local Storage:**
Check if anything is interfering

---

## **Common Issues:**

### **Issue 1: No session cookie created**

**Symptom:** Cookie `session_scientist` doesn't exist

**Cause:** `setCookie()` not being called

**Check in console:**
```javascript
document.cookie
// Should contain: session_scientist=...
```

**Debug:** Add this to browser console:
```javascript
console.log('All cookies:', document.cookie);
```

---

### **Issue 2: History endpoint not called**

**Symptom:** Network tab shows no request to `/scientist/history`

**Cause:** `loadConversationHistory()` not running

**Check:** Is it being called in `window.addEventListener('load')`?

---

### **Issue 3: History endpoint returns empty**

**Symptom:** Request returns `{"messages": []}`

**Cause:** Backend not finding session file

**Check:** Does file exist in `conversations/` folder?

---

### **Issue 4: Messages not displayed**

**Symptom:** History loaded but messages don't appear

**Cause:** `addMessage()` function issue or DOM manipulation

**Debug in console:**
```javascript
// Check if messages are in DOM
document.querySelectorAll('.message').length
// Should match message count

// Check message content
Array.from(document.querySelectorAll('.message')).map(m => m.innerText)
```

---

## **Expected Browser Console Output:**

```javascript
// On page load:
Loading history for session: scientist_20251208_150623
Loaded 4 messages from history

// When sending message:
New session created: scientist_20251208_150623  // Or uses existing

// On return visit:
Loading history for session: scientist_20251208_150623
Loaded 6 messages from history  // Includes new messages
```

---

## **Screenshot Analysis:**

After test runs, check `history_check_screenshot.png`:

**Look for:**
- Are messages visible in the chat area?
- How many messages do you see?
- Is there a welcome message or actual conversation?

---

## **If You Want to Debug Manually:**

1. Open http://localhost:5000/scientist
2. Open DevTools (F12)
3. Go to Console tab
4. Paste this debug script:

```javascript
// Check session management
console.log('characterId:', characterId);
console.log('sessionId:', sessionId);
console.log('All cookies:', document.cookie);

// Check functions exist
console.log('getCookie exists:', typeof getCookie);
console.log('setCookie exists:', typeof setCookie);
console.log('loadConversationHistory exists:', typeof loadConversationHistory);

// Try to get session cookie
const cookieValue = getCookie(`session_${characterId}`);
console.log('Session cookie value:', cookieValue);

// Try to load history
loadConversationHistory().then(() => {
    console.log('History load complete');
    console.log('Message count:', messageCount);
    console.log('DOM messages:', document.querySelectorAll('.message').length);
});
```

---

## **Next Steps:**

1. **Run Playwright test** - `python playwright_history_check.py`
2. **If it fails** - Use the debug checklist above
3. **Check screenshot** - `history_check_screenshot.png`
4. **Report back** - What did you find?

---

## **Quick Fix If Cookie Issue:**

If cookies aren't being set, try adding `SameSite` attribute:

```javascript
function setCookie(name, value, days = 365) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
    //                                                                              ^^^^^^^^ ADD THIS
}
```

---

**Ready to test?** Run `python playwright_history_check.py` now! 🎭
