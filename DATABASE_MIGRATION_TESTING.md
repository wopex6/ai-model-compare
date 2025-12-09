# Database Migration Testing Plan
## Phase 5: Test Database Conversation Persistence

**Date:** December 9, 2025  
**Status:** ✅ Implementation Complete, Testing In Progress

---

## 🎯 **What Was Implemented**

### **Phase 1-4 Complete:**
1. ✅ Database schema updated (character_id column)
2. ✅ Database methods added (get/create/save for user+character)
3. ✅ Backend endpoints updated (session, chat, history)
4. ✅ Frontend updated (removed cookies, use authentication)

### **Key Changes:**

#### **Before (Old System):**
```
User visits /scientist
    ↓
Read cookie: session_scientist (browser-specific)
    ↓
Load from JSON file: conversations/UUID.json
    ↓
Send message → Save to JSON file
    ↓
❌ Lost when cookies cleared
❌ Browser-specific, not user-specific
❌ Not queryable for analysis
```

#### **After (Database System):**
```
User authenticates (JWT token)
    ↓
Frontend calls: GET /scientist/session (with auth token)
    ↓
Backend: Get or create session for (user_id, 'scientist')
    ↓
Return session_id from database
    ↓
Load messages from database (ai_conversations + messages tables)
    ↓
Send message → Save to database (linked to user_id + character_id)
    ↓
✅ Persistent across browsers/devices
✅ User-specific, character-specific
✅ Queryable for analysis
```

---

## 🧪 **Testing Checklist**

### **Test 1: Server Startup** ✅

**Goal:** Verify database migration runs without errors

**Steps:**
1. Start server: `python app.py`
2. Look for: "✓ character_id column already exists" or "✅ Migration complete"
3. Check console for any errors

**Expected:**
```
✓ character_id column already exists
=== Initializing All Characters ===
✓ Dynamic routes registered for all 8 characters with Smart Response + Database
```

**Result:** ✅ **PASS** - Server started successfully, migration ran

---

### **Test 2: User Authentication**

**Goal:** Verify user can log in and get auth token

**Steps:**
1. Open browser: http://localhost:5000
2. Click "Login" or navigate to /login
3. Enter credentials:
   - Username: `Wai Tse`
   - Password: `.//`
4. Check for successful login
5. Check browser dev tools → Application → Local Storage
6. Verify `auth_token` is present

**Expected:**
- ✅ Login successful
- ✅ Token stored in local storage
- ✅ Redirected to dashboard or character page

**Result:** _To be tested by user_

---

### **Test 3: Session Creation (Database)**

**Goal:** Verify session created in database for user+character

**Steps:**
1. Log in as "Wai Tse"
2. Visit http://localhost:5000/scientist
3. Open browser dev tools → Console
4. Look for log: "✓ Session loaded: {UUID} for user {user_id}, character scientist"
5. Check browser dev tools → Network tab
6. Find request to: GET /scientist/session
7. Verify response: `{session_id, user_id, character_id: "scientist"}`

**Expected Console Logs:**
```javascript
✓ Session loaded: 550e8400-e29b-41d4-a716-446655440000 for user 1, character scientist
✅ ConversationBox initialized for scientist
```

**Expected Network Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "character_id": "scientist"
}
```

**Database Verification:**
```python
# In Python console:
from integrated_database import IntegratedDatabase
db = IntegratedDatabase()

# Check session exists
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('''
    SELECT session_id, user_id, character_id, created_at
    FROM ai_conversations
    WHERE user_id = 1 AND character_id = 'scientist'
''')
print(cursor.fetchone())
conn.close()
```

**Expected:** Session record with user_id=1, character_id='scientist'

**Result:** _To be tested by user_

---

### **Test 4: Send Message (Database Storage)**

**Goal:** Verify messages saved to database, not JSON files

**Steps:**
1. On /scientist page, type message: "Hello, how are you?"
2. Press Enter or click Send
3. Check Console logs for:
   - "💾 Saved user message to DATABASE for user 1, character scientist"
4. Check Network tab for POST /scientist/chat
5. Verify response includes assistant message
6. Check database for messages

**Expected Console Logs:**
```
✓ Using database session: {UUID} for user 1, character scientist
💾 Saved user message to DATABASE for user 1, character scientist
```

**Database Verification:**
```python
# Check messages
from integrated_database import IntegratedDatabase
db = IntegratedDatabase()
messages = db.get_character_messages(user_id=1, character_id='scientist')
print(f"Found {len(messages)} messages:")
for msg in messages:
    print(f"  {msg['sender_type']}: {msg['content'][:50]}...")
```

**Expected:** 
- At least 2 messages (1 user, 1 assistant)
- Messages linked to conversation_id
- conversation_id linked to user_id=1, character_id='scientist'

**Result:** _To be tested by user_

---

### **Test 5: Load History (Database Retrieval)**

**Goal:** Verify history loads from database on page refresh

**Steps:**
1. After sending messages in Test 4, refresh the page (F5)
2. Check Console logs for:
   - "✓ Session loaded: {UUID} for user 1, character scientist"
   - "Loading history for user 1, character scientist"
   - "✓ Loaded X messages from database"
3. Verify messages appear in chat window
4. Verify messages are in correct order (oldest to newest)

**Expected Console Logs:**
```
✓ Session loaded: {UUID} for user 1, character scientist
Loading history for user 1, character scientist
✓ Loaded 2 messages from database
```

**Expected UI:**
- All previous messages displayed
- User messages on right (or with user styling)
- Assistant messages on left (or with bot styling)
- Timestamps visible

**Result:** _To be tested by user_

---

### **Test 6: Cross-Browser Persistence**

**Goal:** Verify same session loads in different browser

**Steps:**
1. Complete Test 3-5 in Chrome
2. Note the session_id from Console
3. Open Firefox or Edge
4. Log in as "Wai Tse" (same user)
5. Visit http://localhost:5000/scientist
6. Check if same session_id loads
7. Verify all previous messages appear

**Expected:**
- ✅ Same session_id (user_id + character_id determines session)
- ✅ All previous messages load
- ✅ Can continue conversation
- ✅ New messages saved to same database session

**Result:** _To be tested by user_

---

### **Test 7: Multi-Character Isolation**

**Goal:** Verify each character has separate session for same user

**Steps:**
1. Log in as "Wai Tse"
2. Visit /scientist
3. Send message: "Science test message"
4. Note session_id from Console
5. Visit /business_coach
6. Check session_id in Console
7. Verify different session_id
8. Send message: "Business test message"
9. Go back to /scientist
10. Verify only science messages appear

**Expected:**
- /scientist session_id ≠ /business_coach session_id
- Each character has isolated conversation
- Messages don't leak between characters

**Database Verification:**
```python
from integrated_database import IntegratedDatabase
db = IntegratedDatabase()

# Check both sessions exist
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('''
    SELECT character_id, COUNT(*) as message_count
    FROM ai_conversations c
    JOIN messages m ON m.conversation_id = c.id
    WHERE c.user_id = 1
    GROUP BY character_id
''')
print("Sessions per character:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} messages")
conn.close()
```

**Expected:**
```
Sessions per character:
  scientist: 2 messages
  business_coach: 2 messages
```

**Result:** _To be tested by user_

---

### **Test 8: Cookie Removal Verification**

**Goal:** Verify no cookies are used for session storage

**Steps:**
1. Log in and visit /scientist
2. Open Dev Tools → Application → Cookies
3. Check for `session_scientist` cookie
4. Check for any `session_*` cookies
5. Clear all cookies
6. Refresh page
7. Verify session still loads (from database, not cookies)

**Expected:**
- ❌ No `session_scientist` cookie
- ❌ No `session_*` cookies for characters
- ✅ Only `auth_token` in local storage
- ✅ Session loads after clearing cookies (from database)

**Result:** _To be tested by user_

---

### **Test 9: Smart Response Integration**

**Goal:** Verify Smart Response works with database storage

**Steps:**
1. Visit /scientist
2. Send message that triggers Smart Response (simple question)
3. Check Console for Smart Response logs
4. Verify both user message and quick_reply saved to database

**Expected Console Logs:**
```
💾 Saved user message to DATABASE for user 1, character scientist
💾 Saved quick_reply to DATABASE: '...'
```

**Database Verification:**
```python
from integrated_database import IntegratedDatabase
db = IntegratedDatabase()
messages = db.get_character_messages(user_id=1, character_id='scientist')

# Check for metadata
for msg in messages:
    if msg.get('metadata'):
        print(f"{msg['sender_type']}: source={msg['metadata'].get('source')}")
```

**Expected:**
- User message: `source: "user"`
- Assistant message: `source: "smart_response_quick_reply"` or `source: "smart_response"`

**Result:** _To be tested by user_

---

### **Test 10: Analytics Queries**

**Goal:** Verify database enables analysis queries

**Steps:**
Run these SQL queries to test analysis capability:

```python
from integrated_database import IntegratedDatabase
db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()

# Query 1: All conversations for a user
cursor.execute('''
    SELECT character_id, COUNT(*) as message_count, 
           MAX(updated_at) as last_interaction
    FROM ai_conversations c
    LEFT JOIN messages m ON m.conversation_id = c.id
    WHERE c.user_id = 1
    GROUP BY character_id
    ORDER BY last_interaction DESC
''')
print("\nUser's conversations:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} messages, last: {row[2]}")

# Query 2: All messages with scientist
cursor.execute('''
    SELECT m.sender_type, m.content, m.timestamp
    FROM messages m
    JOIN ai_conversations c ON m.conversation_id = c.id
    WHERE c.character_id = 'scientist'
    ORDER BY m.timestamp DESC
    LIMIT 10
''')
print("\nRecent scientist messages:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1][:50]}... ({row[2]})")

# Query 3: Message distribution by character
cursor.execute('''
    SELECT c.character_id, 
           SUM(CASE WHEN m.sender_type = 'user' THEN 1 ELSE 0 END) as user_messages,
           SUM(CASE WHEN m.sender_type = 'assistant' THEN 1 ELSE 0 END) as bot_messages
    FROM ai_conversations c
    LEFT JOIN messages m ON m.conversation_id = c.id
    GROUP BY c.character_id
''')
print("\nMessage distribution:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} user, {row[2]} bot")

conn.close()
```

**Expected:**
- Queries run without errors
- Accurate counts and data
- Can analyze user behavior across characters

**Result:** _To be tested by user_

---

## 🐛 **Debugging Guide**

### **Issue 1: "Authentication required" error**

**Symptoms:**
- Console error: `401 Unauthorized`
- Error: "Authentication required"

**Diagnosis:**
```javascript
// In browser console:
console.log('Auth token:', localStorage.getItem('auth_token'));
```

**Solution:**
1. Check if user is logged in
2. Verify token exists in local storage
3. Re-login if token expired
4. Check AuthHelper.js is included before conversation_box.js

---

### **Issue 2: "Database not configured" error**

**Symptoms:**
- Console error: "Database not configured"
- Session endpoint returns 500

**Diagnosis:**
Check app.py:
```python
# Verify this line exists:
register_character_routes(app, all_characters, process_with_smart_response, integrated_db)
#                                                                          ^^^^^^^^^^^^^^
```

**Solution:**
- Ensure `integrated_db` is passed to `register_character_routes()`
- Restart server if changed

---

### **Issue 3: Messages not saving to database**

**Symptoms:**
- Messages send but don't persist
- History doesn't load after refresh

**Diagnosis:**
```python
# Check if messages table has data:
from integrated_database import IntegratedDatabase
db = IntegratedDatabase()
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM messages')
print(f"Total messages in database: {cursor.fetchone()[0]}")
cursor.execute('SELECT COUNT(*) FROM ai_conversations')
print(f"Total conversations: {cursor.fetchone()[0]}")
conn.close()
```

**Solution:**
- Check console for database error messages
- Verify `integrated_db` parameter passed correctly
- Check user_id is valid (not None)

---

### **Issue 4: History loads from JSON, not database**

**Symptoms:**
- Console log: "⚠️ Fallback: Loaded X messages from JSON"

**Diagnosis:**
This means `integrated_db` is None or not passed correctly.

**Solution:**
1. Check app.py line 2741:
   ```python
   register_character_routes(app, all_characters, process_with_smart_response, integrated_db)
   ```
2. Restart server
3. Clear browser cache

---

## ✅ **Success Criteria**

All tests should pass:

- [x] Server starts without errors
- [ ] User can log in successfully
- [ ] Session created in database (not cookies)
- [ ] Messages saved to database
- [ ] History loads from database
- [ ] Same session across browsers
- [ ] Separate sessions per character
- [ ] No session cookies exist
- [ ] Smart Response works with database
- [ ] Analytics queries work

**When all tests pass:**
✅ Database migration complete  
✅ Ready for production  
✅ Ready to migrate remaining templates  

---

## 📊 **Migration Status**

### **Completed:**
- ✅ Database schema updated
- ✅ Database methods implemented
- ✅ Backend endpoints updated
- ✅ Frontend updated (ConversationBox.js)
- ✅ scientist.html migrated

### **Remaining:**
- [ ] Test all 10 test cases
- [ ] Migrate 7 remaining templates:
  - business_coach.html
  - life_coach.html
  - motivational_coach.html
  - psychologist.html
  - stoic.html
  - wisdom.html
  - zen_master.html

### **Timeline:**
- Phase 1-4: ✅ Complete (Dec 9)
- Phase 5: 🧪 Testing (Dec 9)
- Template Migration: 📋 Pending (2-3 hours)

---

## 🎯 **Next Steps**

1. **Complete Test Cases 2-10** (user testing required)
2. **Verify all tests pass**
3. **Commit test results**
4. **Migrate remaining 7 templates** (use ConversationBox with database)
5. **Final testing across all characters**
6. **Update roadmap document**

---

**Created:** December 9, 2025  
**Status:** Phase 5 In Progress  
**Server:** Running on http://localhost:5000  
**Ready for user testing:** Yes! 🚀
