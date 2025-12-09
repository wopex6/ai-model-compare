# Template CSS Class Audit
## Checking for MessageHandler Compatibility

---

## **Issue Found: stoic_marcus.html**
**Status:** ✅ **FIXED**

**Problem:** Used `.user-message` and `.assistant-message` classes, but MessageHandler creates `.message.user` and `.message.bot`

**Solution Applied:**
```css
/* Added CSS rules for MessageHandler's structure */
.message.user {
    background: linear-gradient(135deg, #edf2f7, #cbd5e0);
    margin-left: auto;
    text-align: right;
}

.message.bot {
    background: white;
    border-left: 4px solid #718096;
}
```

---

## **Other Templates - Status Check**

### **✅ business_coach.html - NO ISSUES**
**Message Classes Used:** `.message`, `.bot`, `.user`
**Container ID:** `chatMessages`
**Status:** Compatible with MessageHandler

**Evidence:**
```html
<div class="message bot">
    <div class="message-bubble">
```

**MessageHandler Config:**
```javascript
MessageHandler.init('business_coach', {
    messageClass: 'message',
    bubbleClass: 'message-bubble'
});
```

---

### **✅ life_coach.html - NO ISSUES**
**Message Classes Used:** `.message-life`, `.user`, `.bot`
**Container ID:** `chatMessages`
**Status:** Compatible (custom classes specified)

**Evidence:**
```css
.message-life.user {
    text-align: right;
}

.message-life.bot .message-bubble-life {
    background: white;
}
```

**MessageHandler Config:**
```javascript
MessageHandler.init('life_coach', {
    messageClass: 'message-life',
    bubbleClass: 'message-bubble-life'
});
```

---

### **✅ motivational_coach.html - NO ISSUES**
**Message Classes Used:** `.message`, `.user`, `.coach`
**Container ID:** `chatMessages`
**Status:** Compatible

**CSS:**
```css
.message {
    margin-bottom: 20px;
    display: flex;
}

.message.user {
    flex-direction: row-reverse;
}
```

**MessageHandler Config:**
```javascript
MessageHandler.init('super_motivational_coach', {
    messageClass: 'message',
    bubbleClass: 'message-content'
});
```

---

### **✅ psychologist.html - NO ISSUES**
**Message Classes Used:** `.message`, `.bot`, `.user`
**Container ID:** `chatMessages`
**Status:** Compatible

**Evidence:**
```html
<div class="message bot">
    <div class="message-bubble">
```

**MessageHandler Config:**
```javascript
MessageHandler.init('psychologist', {
    messageClass: 'message',
    bubbleClass: 'message-bubble'
});
```

---

### **⏳ wisdom_sage.html - NOT YET MIGRATED**
**Status:** Pending migration
**Expected:** Similar to other templates, should use `.message.user` / `.message.bot`

---

### **⏳ zen_master.html - NOT YET MIGRATED**
**Status:** Pending migration
**Expected:** Similar to other templates, should use `.message.user` / `.message.bot`

---

## **MessageHandler Defaults**

From `static/message_handler.js` (Line 37):
```javascript
this.messagesContainer = document.getElementById('chatMessages') 
                      || document.getElementById('chat-messages');
```

**Default Container IDs Supported:**
- `chatMessages` (primary)
- `chat-messages` (fallback)

**Default CSS Classes:**
```javascript
messageClass: theme.messageClass || 'message',
bubbleClass: theme.bubbleClass || 'message-bubble',
```

**Message Structure Created:**
```html
<div class="message user">  <!-- or .message.bot -->
    <div class="message-bubble">
        <strong>You:</strong> message content
        <span class="timestamp">12:34</span>
    </div>
</div>
```

---

## **Conclusion**

### **Templates With Issues:**
1. ~~stoic_marcus.html~~ ✅ **FIXED**

### **Templates Verified OK:**
1. ✅ business_coach.html
2. ✅ life_coach.html  
3. ✅ motivational_coach.html
4. ✅ psychologist.html
5. ✅ scientist.html (baseline)

### **Templates Not Yet Migrated:**
6. ⏳ wisdom_sage.html
7. ⏳ zen_master.html

---

## **Recommendation**

**No further CSS fixes needed for migrated templates.** All use compatible class structures.

**When migrating wisdom_sage and zen_master:**
- Ensure they use `.message.user` and `.message.bot` in CSS
- Or specify custom `messageClass` in MessageHandler.init()
- Verify container ID is `chatMessages` or `chat-messages`

---

**Document Created:** Dec 9, 2025, 9:10 PM  
**Audit Status:** Complete for 5/7 migrated templates
