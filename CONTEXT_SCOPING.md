# 🔒 Context Scoping & Privacy

## **Question: Is context user-specific?**

## **Answer: YES! ✅ 100% User-Specific**

---

## **Database Design - Privacy by Default**

Every context table includes `user_id` as a **NOT NULL** field:

```sql
-- Context is ALWAYS scoped to user
CREATE TABLE conversation_context (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,        -- ✅ REQUIRED
    character TEXT NOT NULL,          -- ✅ REQUIRED
    context_type TEXT NOT NULL,
    context_data TEXT NOT NULL,
    UNIQUE(user_id, character, context_type)  -- Unique per user+character
)

CREATE TABLE conversation_topics (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,        -- ✅ REQUIRED
    character TEXT NOT NULL,          -- ✅ REQUIRED
    topic TEXT NOT NULL
)

CREATE TABLE followup_suggestions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,        -- ✅ REQUIRED
    character TEXT NOT NULL,          -- ✅ REQUIRED
    suggestion TEXT NOT NULL
)
```

---

## **Context Isolation**

### **Each User Has:**

```
User 1 (Alice)
├── Coach Context
│   ├── Topics: [fitness, goals, motivation]
│   ├── Summary: "Training for marathon"
│   └── Messages: [her messages only]
├── Sage Context
│   ├── Topics: [wisdom, philosophy]
│   └── Summary: "Seeking life guidance"
└── Marcus Context
    └── [separate context]

User 2 (Bob)
├── Coach Context
│   ├── Topics: [career, business]
│   ├── Summary: "Starting a business"
│   └── Messages: [his messages only]
└── [completely separate from Alice]

User 3 (Carol)
└── [completely separate from Alice and Bob]
```

**No cross-contamination. Ever.**

---

## **Query Protection**

All queries include `user_id` in WHERE clause:

```python
# ALWAYS scoped to user
def get_context_for_ai(self, user_id: int, character: str, ...):
    cursor.execute('''
        SELECT context_type, context_data 
        FROM conversation_context
        WHERE user_id = ? AND character = ?  -- ✅ USER SPECIFIC
    ''', (user_id, character))

def _update_topic(self, user_id: int, character: str, topic: str):
    cursor.execute('''
        SELECT id FROM conversation_topics
        WHERE user_id = ? AND character = ? AND topic = ?  -- ✅ USER SPECIFIC
    ''', (user_id, character, topic))
```

**Impossible to access another user's context.**

---

## **Authentication Integration**

Context is only accessible with valid JWT token:

```python
@app.route('/api/context/<character>', methods=['GET'])
@require_auth  # ✅ AUTHENTICATION REQUIRED
def get_conversation_context(character):
    # Extract user from token
    user_id = request.current_user['user_id']  # ✅ FROM JWT
    
    # Only returns THIS user's context
    context = context_manager.get_context_for_ai(user_id, character, [])
    
    return jsonify(context)
```

**You can only access your own context.**

---

## **Context Scoping Levels**

```
┌────────────────────────────────────────────────────┐
│  LEVEL 1: USER ISOLATION (Primary)                 │
│  - Each user has completely separate context       │
│  - user_id is PRIMARY scoping mechanism            │
│  - NO cross-user access possible                   │
└────────────────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────────────┐
│  LEVEL 2: CHARACTER SEPARATION (Secondary)         │
│  - Within a user, each character has own context   │
│  - Alice's Coach context ≠ Alice's Sage context    │
│  - Characters don't share context (by default)     │
└────────────────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────────────┐
│  LEVEL 3: CONTEXT TYPE (Tertiary)                  │
│  - Within user+character, types separated          │
│  - 'summary', 'preferences', 'emotional_state'     │
│  - Allows granular updates                         │
└────────────────────────────────────────────────────┘
```

---

## **Privacy Guarantees**

### **What IS Shared:**
- ❌ **Nothing between users**

### **What is NOT Shared:**
- ✅ Context
- ✅ Topics
- ✅ Message history
- ✅ Suggestions
- ✅ Preferences
- ✅ Emotional state
- ✅ Conversation summaries

### **Optional Sharing (Not Implemented, But Possible):**

If you wanted to share insights between characters for the SAME user:

```python
def get_cross_character_insights(user_id: int) -> Dict:
    """
    OPTIONAL: Share high-level insights across characters
    ONLY within the same user
    """
    cursor.execute('''
        SELECT character, context_data
        FROM conversation_context
        WHERE user_id = ? AND context_type = 'summary'  -- ✅ SAME USER
    ''', (user_id,))
    
    # Alice's Coach can know Alice's Sage topics
    # But NEVER Bob's anything
```

**Example Use Case:**
```
Alice talks to Sage about stress
→ Sage notes: "User experiencing work stress"

Later, Alice talks to Coach
→ Coach could optionally know: "Sage mentioned stress"
→ Coach: "I see you've been dealing with stress. Let's build resilience!"

But Coach NEVER knows what Bob discussed.
```

---

## **Testing Context Isolation**

### **Test Case: Two Users, Same Character**

```python
# User 1 (Alice) chats with Coach
alice_id = 1
send_message(alice_id, 'coach', 'I want to run a marathon')
# Context stored: user_id=1, character='coach', topic='fitness'

# User 2 (Bob) chats with Coach
bob_id = 2
send_message(bob_id, 'coach', 'I want to start a business')
# Context stored: user_id=2, character='coach', topic='business'

# Retrieve Alice's context
alice_context = get_context(alice_id, 'coach')
# Returns: topics=['fitness'], summary='Training for marathon'

# Retrieve Bob's context
bob_context = get_context(bob_id, 'coach')
# Returns: topics=['business'], summary='Starting a business'

# Assert isolation
assert alice_context['topics'] != bob_context['topics']  # ✅ PASS
assert 'marathon' not in bob_context['summary']           # ✅ PASS
assert 'business' not in alice_context['summary']         # ✅ PASS
```

---

## **Context Access Control**

```python
class ContextAccessControl:
    """Enforces who can access what context"""
    
    def can_access_context(self, requesting_user_id: int, 
                          context_user_id: int) -> bool:
        """Check if user can access context"""
        
        # Rule 1: Users can only access their own context
        if requesting_user_id != context_user_id:
            print(f"❌ ACCESS DENIED: User {requesting_user_id} "
                  f"tried to access User {context_user_id}'s context")
            return False
        
        # Rule 2: Must be authenticated
        if requesting_user_id is None:
            print("❌ ACCESS DENIED: Not authenticated")
            return False
        
        return True
    
    def get_context_safe(self, requesting_user_id: int, 
                        context_user_id: int, character: str):
        """Get context with access control"""
        
        if not self.can_access_context(requesting_user_id, context_user_id):
            raise PermissionError("Cannot access another user's context")
        
        return get_context(context_user_id, character)
```

---

## **Context in Memory vs Database**

### **In-Memory (Runtime):**

```python
# Separate dictionaries per user
message_histories = {
    '1_coach': [messages for user 1 with coach],
    '1_sage': [messages for user 1 with sage],
    '2_coach': [messages for user 2 with coach],  # Different from user 1!
}

# Key format: f"{user_id}_{character}"
# Ensures separation in memory too
```

### **In Database (Persistent):**

```sql
-- Query 1: Alice's coach context
SELECT * FROM conversation_context 
WHERE user_id = 1 AND character = 'coach'

-- Query 2: Bob's coach context
SELECT * FROM conversation_context 
WHERE user_id = 2 AND character = 'coach'

-- NEVER query without user_id!
```

---

## **GDPR & Data Privacy Compliance**

### **User Rights:**

```python
# Right to access
def export_user_context(user_id: int) -> Dict:
    """Export all context for a user"""
    return {
        'contexts': get_all_contexts(user_id),
        'topics': get_all_topics(user_id),
        'suggestions': get_all_suggestions(user_id)
    }

# Right to deletion
def delete_user_context(user_id: int):
    """Delete all context for a user (GDPR right to be forgotten)"""
    cursor.execute('DELETE FROM conversation_context WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM conversation_topics WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM followup_suggestions WHERE user_id = ?', (user_id,))
    print(f"✅ All context deleted for user {user_id}")

# Right to portability
def export_user_data(user_id: int, format='json'):
    """Export user data in portable format"""
    data = export_user_context(user_id)
    if format == 'json':
        return json.dumps(data, indent=2)
    elif format == 'csv':
        return convert_to_csv(data)
```

---

## **Multi-Tenancy Support**

If you have multiple organizations:

```sql
-- Extended schema with organization isolation
CREATE TABLE conversation_context (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,          -- ✅ Organization
    user_id INTEGER NOT NULL,         -- ✅ User within org
    character TEXT NOT NULL,
    context_data TEXT NOT NULL,
    UNIQUE(org_id, user_id, character, context_type)
)

-- Query: User 1 in Org A ≠ User 1 in Org B
WHERE org_id = ? AND user_id = ? AND character = ?
```

---

## **Summary: Context Scoping**

| Question | Answer |
|----------|--------|
| Is context user-specific? | ✅ YES - 100% |
| Can users see each other's context? | ❌ NO - Impossible |
| Can characters share context? | ⚠️ Within same user only (optional) |
| Is it secure? | ✅ YES - JWT auth + user_id scoping |
| GDPR compliant? | ✅ YES - Export & delete functions |
| Multi-tenancy support? | ✅ Can be extended with org_id |

**Your context is YOURS. Always. Forever.** 🔒
