# Database Conversation Storage - Migration Plan
## Move from JSON Files to Database with User + Character Linking

**Date:** December 9, 2025  
**Priority:** HIGH - Required for user-specific history and future analysis

---

## 🎯 **User Requirements**

1. ✅ Fix "USER'S EXPLICIT STATEMENTS" (DONE)
2. ❌ Conversations should be stored in **DATABASE** (not cookies/JSON files)
3. ❌ Unique for each **user + character** combination
4. ❌ Retrieved from database when loading
5. ❌ Used for future analysis (context, goals, preferences)

---

## 📊 **Current System Analysis**

### **What's Wrong:**

| Component | Current State | Problem |
|-----------|--------------|---------|
| **Storage** | JSON files via `ConversationManager` | Not database |
| **Session Tracking** | Browser cookies (`session_scientist`) | Browser-specific, not user-specific |
| **User Linking** | None | Sessions not linked to user_id |
| **Character Linking** | None | Sessions not linked to character_id |
| **Database Tables** | Exist but unused | `ai_conversations` & `messages` tables exist |
| **Authentication** | Backend only | Frontend doesn't know user_id |

### **Current Flow:**

```
User visits /scientist
    ↓
ConversationBox reads cookie: session_scientist
    ↓
If exists: Load from JSON file (conversations/UUID.json)
    ↓
Send message → Save to JSON file
    ↓
Problem: No user_id, no character_id, browser-specific
```

---

## ✅ **Target System Architecture**

### **Database Schema:**

```sql
-- UPDATED ai_conversations table (add character_id)
CREATE TABLE ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    character_id TEXT NOT NULL,              -- NEW!
    session_id TEXT UNIQUE NOT NULL,
    title TEXT,
    conversation_data TEXT,                  -- JSON (deprecated, use messages table)
    personality_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE(user_id, character_id)           -- NEW! One active session per user+character
);

-- messages table (already exists, perfect structure)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    sender_type TEXT NOT NULL CHECK (sender_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata TEXT,                           -- JSON: {source, confidence, etc.}
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
);
```

### **New Flow:**

```
User authenticates (login)
    ↓
Frontend knows user_id from auth token
    ↓
User visits /scientist
    ↓
ConversationBox calls: GET /scientist/session (with auth token)
    ↓
Backend: Get or create session for (user_id, character_id)
    ↓
Return session_id to frontend
    ↓
Load messages from database (messages table)
    ↓
Display conversation history
    ↓
Send message → Save to database (linked to user_id + character_id)
```

---

## 📋 **Implementation Steps**

### **Step 1: Update Database Schema** ✅

**File:** `integrated_database.py`

**Add:**
1. Migration to add `character_id` column to `ai_conversations`
2. Add unique constraint on `(user_id, character_id)`
3. Create indexes for faster queries

**Code:**
```python
def migrate_add_character_id(self):
    """Add character_id column to ai_conversations table"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(ai_conversations)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'character_id' not in columns:
            # Add column
            cursor.execute('ALTER TABLE ai_conversations ADD COLUMN character_id TEXT')
            
            # Create index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversations_user_character 
                ON ai_conversations(user_id, character_id)
            ''')
            
            conn.commit()
            print("✓ Added character_id column to ai_conversations")
        
    finally:
        conn.close()
```

---

### **Step 2: Add Database Methods** ✅

**File:** `integrated_database.py`

**New Methods:**

```python
def get_or_create_character_session(self, user_id: int, character_id: str) -> str:
    """Get existing session or create new one for user+character"""
    conn = self.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check for existing session
        cursor.execute('''
            SELECT session_id FROM ai_conversations
            WHERE user_id = ? AND character_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (user_id, character_id))
        
        result = cursor.fetchone()
        
        if result:
            session_id = result[0]
            print(f"✓ Found existing session: {session_id} for user {user_id}, character {character_id}")
            return session_id
        
        # Create new session
        session_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO ai_conversations (user_id, character_id, session_id, title)
            VALUES (?, ?, ?, ?)
        ''', (user_id, character_id, session_id, f"{character_id} conversation"))
        
        conn.commit()
        print(f"✓ Created new session: {session_id} for user {user_id}, character {character_id}")
        return session_id
        
    finally:
        conn.close()

def save_character_message(self, user_id: int, character_id: str, role: str, content: str, metadata: dict = None) -> bool:
    """Save message to database for user+character"""
    session_id = self.get_or_create_character_session(user_id, character_id)
    return self.add_message(session_id, user_id, role, content, metadata)

def get_character_messages(self, user_id: int, character_id: str, limit: int = None) -> List[Dict]:
    """Get conversation history for user+character"""
    session_id = self.get_or_create_character_session(user_id, character_id)
    messages = self.get_conversation_messages(session_id, user_id)
    
    if limit:
        messages = messages[-limit:]
    
    return messages
```

---

### **Step 3: Update character_routes.py** ✅

**File:** `ai_compare/character_routes.py`

**Changes:**

1. Add `/session` endpoint to get/create session for user+character
2. Update `/chat` endpoint to use database
3. Update `/history` endpoint to use database
4. Remove ConversationManager dependency

**New Endpoints:**

```python
@app.route('/<character_id>/session', methods=['GET'])
def get_character_session(character_id):
    """Get or create session for authenticated user + character"""
    
    # Get user from auth token
    user_data = authenticate_token()
    if not user_data:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = user_data['user_id']
    
    # Get or create session in database
    session_id = integrated_db.get_or_create_character_session(user_id, character_id)
    
    return jsonify({
        'session_id': session_id,
        'user_id': user_id,
        'character_id': character_id
    })

@app.route('/<character_id>/chat', methods=['POST'])
def character_chat(character_id):
    """Updated to use database instead of ConversationManager"""
    
    # Get user from auth
    user_data = authenticate_token()
    if not user_data:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = user_data['user_id']
    message = request.json.get('message')
    
    # Get or create session
    session_id = integrated_db.get_or_create_character_session(user_id, character_id)
    
    # Save user message to database
    integrated_db.save_character_message(user_id, character_id, 'user', message, {'source': 'user'})
    
    # Process with Smart Response...
    # (existing logic)
    
    # Save assistant response to database
    integrated_db.save_character_message(user_id, character_id, 'assistant', response, {'source': 'smart_response'})
    
    return jsonify({'response': response, 'session_id': session_id})

@app.route('/<character_id>/history', methods=['GET'])
def character_history(character_id):
    """Get conversation history from database"""
    
    # Get user from auth
    user_data = authenticate_token()
    if not user_data:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = user_data['user_id']
    
    # Get messages from database
    messages = integrated_db.get_character_messages(user_id, character_id)
    
    return jsonify({
        'messages': messages,
        'character_id': character_id
    })
```

---

### **Step 4: Update ConversationBox.js** ✅

**File:** `static/conversation_box.js`

**Changes:**

1. Remove cookie-based session management
2. Add authentication token handling
3. Call `/session` endpoint to get user session
4. Pass auth token with all requests

**New Flow:**

```javascript
const ConversationBox = {
    characterId: null,
    sessionId: null,
    userId: null,  // NEW
    config: {},
    
    async init(characterId, config) {
        this.characterId = characterId;
        this.config = {
            ...defaultConfig,
            ...config
        };
        
        // Get authenticated session from backend
        await this._getAuthenticatedSession();
        
        // Setup event listeners
        this._setupEventListeners();
        
        // Load history from database
        await this.loadHistory();
    },
    
    async _getAuthenticatedSession() {
        try {
            // Call backend to get session for this user+character
            const response = await AuthHelper.authenticatedFetch(`/${this.characterId}/session`, {
                method: 'GET'
            });
            
            const data = await response.json();
            this.sessionId = data.session_id;
            this.userId = data.user_id;
            
            console.log(`✓ Session loaded: ${this.sessionId} for user ${this.userId}, character ${this.characterId}`);
            
        } catch (error) {
            console.error('Error getting session:', error);
            // Fallback: User not authenticated
            this.sessionId = null;
            this.userId = null;
        }
    },
    
    async loadHistory() {
        if (!this.sessionId) {
            console.log('No session, skipping history load');
            return;
        }
        
        try {
            // Call backend to get messages from database
            const response = await AuthHelper.authenticatedFetch(`/${this.characterId}/history`, {
                method: 'GET'
            });
            
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                // Display messages
                MessageHandler.messagesContainer.innerHTML = '';
                
                data.messages.forEach(msg => {
                    MessageHandler.addMessage({
                        content: msg.content,
                        role: msg.sender_type,  // 'user' or 'assistant'
                        timestamp: msg.timestamp,
                        source: msg.metadata?.source,
                        shouldScroll: false
                    });
                });
                
                MessageHandler.messagesContainer.scrollTop = MessageHandler.messagesContainer.scrollHeight;
            }
            
        } catch (error) {
            console.error('Error loading history:', error);
        }
    },
    
    async sendMessage(messageText = null) {
        // ... existing code ...
        
        // Send to backend (already using AuthHelper)
        const response = await AuthHelper.authenticatedFetch(this.config.chatEndpoint, {
            method: 'POST',
            body: JSON.stringify({
                message: message
                // No need to send session_id - backend gets it from user_id + character_id
            })
        });
        
        // ... rest of existing code ...
    }
};
```

---

### **Step 5: Remove Cookie Dependencies** ✅

**Files to Update:**
- `conversation_box.js` - Remove `_getCookie`, `_setCookie`, `_updateSessionId`
- `character_routes.py` - Remove ConversationManager usage
- `app.py` - Deprecate ConversationManager

**Result:**
- No more browser-specific sessions
- All sessions linked to user_id + character_id
- Persistent across browsers/devices
- Ready for analysis (context, goals, preferences)

---

## 🎯 **Benefits**

### **Before (Current System):**
❌ Sessions in JSON files  
❌ Browser-specific (cookies)  
❌ Not linked to users  
❌ Not linked to characters  
❌ Can't analyze across users  
❌ Lost when cookies cleared  

### **After (Database System):**
✅ Sessions in database  
✅ User-specific (auth token)  
✅ Linked to user_id  
✅ Linked to character_id  
✅ Ready for analysis  
✅ Persistent across browsers/devices  
✅ Can query: "Show all scientist conversations"  
✅ Can analyze: "What goals does user X have?"  
✅ Can track: "User journey across characters"  

---

## 📊 **Database Queries Enabled**

After migration, you can run analytics like:

```sql
-- All conversations for a specific user
SELECT * FROM ai_conversations WHERE user_id = 1;

-- All messages with scientist
SELECT m.* FROM messages m
JOIN ai_conversations c ON m.conversation_id = c.id
WHERE c.character_id = 'scientist';

-- User's conversation history across all characters
SELECT c.character_id, COUNT(m.id) as message_count
FROM ai_conversations c
JOIN messages m ON m.conversation_id = c.id
WHERE c.user_id = 1
GROUP BY c.character_id;

-- Extract goals from conversations (for future AI analysis)
SELECT content FROM messages
WHERE sender_type = 'user'
AND content LIKE '%goal%'
OR metadata LIKE '%goal%';

-- User preferences analysis
SELECT c.character_id, m.content, m.metadata
FROM messages m
JOIN ai_conversations c ON m.conversation_id = c.id
WHERE c.user_id = 1
AND m.metadata LIKE '%preference%';
```

---

## ⚠️ **Migration Considerations**

### **Existing JSON File Data:**

Option 1: Leave as-is (historical data)
- Old sessions remain in JSON files
- New sessions use database
- Clean separation

Option 2: Migrate to database
- Create script to import JSON → database
- Link to default user or anonymous user
- Requires mapping session → user_id + character_id

**Recommendation:** Option 1 (clean separation, less risk)

---

### **Backward Compatibility:**

**ConversationManager:**
- Keep for now (don't delete)
- Mark as deprecated
- Used only for old sessions

**Cookies:**
- Remove `session_*` cookies after migration
- Keep auth tokens

---

## 🧪 **Testing Plan**

### **Test 1: New User Registration**
1. Register new user
2. Visit /scientist
3. Send message
4. Check database: `SELECT * FROM ai_conversations WHERE user_id = X`
5. Verify: Session created with character_id = 'scientist'
6. Check database: `SELECT * FROM messages WHERE conversation_id = Y`
7. Verify: Message saved with sender_type = 'user'

### **Test 2: Cross-Browser Persistence**
1. User logs in on Chrome
2. Send message to scientist
3. Log out, log in on Firefox
4. Visit /scientist
5. Verify: History loads correctly
6. **Expected:** Same conversation, same session_id

### **Test 3: Multi-Character Sessions**
1. User visits /scientist → Send message
2. User visits /business_coach → Send message
3. Check database: `SELECT * FROM ai_conversations WHERE user_id = X`
4. **Expected:** 2 sessions, different character_ids
5. Refresh /scientist
6. **Expected:** Only scientist history loads

### **Test 4: Message Analysis**
1. User has conversations with 3 characters
2. Run query: `SELECT character_id, COUNT(*) FROM messages JOIN ai_conversations ...`
3. **Expected:** Accurate counts per character
4. Extract goals: `SELECT content WHERE content LIKE '%goal%'`
5. **Expected:** All goal-related messages across all characters

---

## 🚀 **Implementation Priority**

**Phase 1: Database Setup** (30 min)
- [ ] Update schema (add character_id column)
- [ ] Add database methods
- [ ] Test database methods

**Phase 2: Backend Integration** (45 min)
- [ ] Update character_routes.py
- [ ] Add `/session` endpoint
- [ ] Update `/chat` to use database
- [ ] Update `/history` to use database
- [ ] Test backend endpoints

**Phase 3: Frontend Integration** (45 min)
- [ ] Update ConversationBox.js
- [ ] Remove cookie methods
- [ ] Add session initialization
- [ ] Test with scientist.html

**Phase 4: Testing** (30 min)
- [ ] Test new user registration
- [ ] Test cross-browser persistence
- [ ] Test multi-character sessions
- [ ] Test message retrieval

**Phase 5: Migrate Templates** (2 hours)
- [ ] Migrate remaining 6 characters
- [ ] All use same database system
- [ ] Test each character

**Total Time:** ~5 hours

---

## ✅ **Success Criteria**

1. ✅ All conversations stored in database (not JSON files)
2. ✅ Each session linked to user_id + character_id
3. ✅ Messages retrieved from database on page load
4. ✅ Persistent across browsers/devices
5. ✅ Can query conversations for analysis
6. ✅ No cookie-based session management
7. ✅ Authentication required for all chat operations

---

## 📝 **Summary**

**Current Issue:**
- Conversations in JSON files, browser-specific, not linked to users/characters

**Solution:**
- Migrate to database storage with user_id + character_id linking
- Use authentication tokens instead of cookies
- Enable future analysis (context, goals, preferences)

**Implementation:**
- Update database schema
- Add database methods
- Update backend (character_routes.py)
- Update frontend (conversation_box.js)
- Test thoroughly
- Migrate all templates

**Timeline:** ~5 hours  
**Priority:** HIGH - Required for personalization and analysis

---

**Ready to proceed with implementation?**
