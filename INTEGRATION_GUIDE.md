# 🔌 Smart Response Integration Guide

## 📋 Step-by-Step Local Integration

### **Step 1: Add Smart Response to app.py Initialization**

Add this near the top of `app.py` where other imports are:

```python
# Add after existing imports
from smart_response.handler import SmartResponseHandler
import sqlite3

# Add after app initialization
# Initialize Smart Response System
smart_response_conn = sqlite3.connect('integrated_users.db', check_same_thread=False)
smart_handler = SmartResponseHandler(smart_response_conn)

# Track previous interactions for learning
previous_interactions = {}
```

---

### **Step 2: Update One Character Route (Test with Coach)**

**Before:**
```python
@app.route('/coach/chat', methods=['POST'])
def coach_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        include_context = data.get('include_context', True)
        
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(motivational_bot.chat(message, include_context))
        loop.close()
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**After (with Smart Response):**
```python
@app.route('/coach/chat', methods=['POST'])
@require_auth  # Make sure auth is required
def coach_chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        include_context = data.get('include_context', True)
        user_id = request.current_user.get('user_id')
        
        if not message.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # ✨ SMART RESPONSE CHECK ✨
        from datetime import datetime
        
        # Track previous interaction for learning
        prev_key = f"{user_id}_coach"
        if prev_key in previous_interactions:
            prev = previous_interactions[prev_key]
            time_diff = (datetime.now() - prev['timestamp']).total_seconds()
            smart_handler.track_response(
                user_id=user_id,
                message=prev['message'],
                response_type=prev['response_type'],
                character='coach',
                user_followup=message,
                time_to_followup=time_diff
            )
        
        # Check if this is small talk
        response_type, response_data = smart_handler.process_message(
            user_id, message, 'coach'
        )
        
        if response_type == 'quick_reply':
            # Use quick reply (instant, no API cost!)
            result = {
                'response': response_data['text'],
                'type': 'quick_reply',
                'confidence': response_data['confidence']
            }
            
            # Store for learning
            previous_interactions[prev_key] = {
                'message': message,
                'response_type': 'quick_reply',
                'timestamp': datetime.now()
            }
            
            return jsonify(result)
        
        # Otherwise, use full AI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(motivational_bot.chat(message, include_context))
        loop.close()
        
        # Store for learning
        previous_interactions[prev_key] = {
            'message': message,
            'response_type': 'full_ai',
            'timestamp': datetime.now()
        }
        
        # Add metadata
        if isinstance(response, dict):
            response['type'] = 'full_ai'
            response['smart_response_confidence'] = response_data['confidence']
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

### **Step 3: Test Locally**

Start your Flask app:
```bash
python app.py
```

Test these messages to Coach:
1. `"hi"` → Should get quick reply ⚡
2. `"thanks"` → Should get quick reply ⚡
3. `"I'm struggling with motivation"` → Should get full AI 🤖
4. `"ok"` → Should get quick reply ⚡

**Check console for:**
```
Quick Reply: "Hey there, champion! 🔥 Ready to crush your goals today?"
Full AI: [Complex response about motivation]
```

---

### **Step 4: Add Stats Endpoint (Optional)**

See how the learning is working:

```python
@app.route('/api/smart-response/stats')
@require_auth
def smart_response_stats():
    """Get user's smart response learning stats"""
    try:
        user_id = request.current_user.get('user_id')
        stats = smart_handler.get_user_stats(user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

Test it:
```bash
curl http://localhost:5000/api/smart-response/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### **Step 5: Roll Out to Other Characters**

Once Coach works, apply the same pattern to:
- `/sage/chat`
- `/marcus/chat`
- `/psychologist/chat`
- `/zen_master/chat`
- `/business_coach/chat`
- `/life_coach/chat`
- `/scientist/chat`

Just change:
- `'coach'` → character name
- `motivational_bot` → appropriate bot instance

---

## 🎯 Quick Testing Checklist

After integration, test these scenarios:

### Test 1: Greetings
```
Message: "hi"
Expected: Quick reply in <100ms
Example: "Hey there, champion! 🔥 Ready to crush your goals today!"
```

### Test 2: Thanks
```
Message: "thanks for your help"
Expected: Quick reply
Example: "You got this! 💪 Keep crushing it!"
```

### Test 3: Complex Question
```
Message: "I'm feeling anxious about my career goals"
Expected: Full AI response
Should take 2-5 seconds
```

### Test 4: Acknowledgment
```
Message: "ok"
Expected: Quick reply
Example: "Awesome! 💪 What's next on your action list?"
```

### Test 5: Learning Over Time
```
1. Send: "thanks"
2. Send: "that's helpful" (within 3 seconds)
   → System learns you're satisfied with quick replies
3. Next time "thanks" might have lower threshold
```

---

## 🐛 Troubleshooting

### Quick replies not showing

**Check:**
```python
# Is user authenticated?
user_id = request.current_user.get('user_id')
print(f"User ID: {user_id}")

# Is smart handler initialized?
print(f"Handler: {smart_handler}")

# What's the detection result?
response_type, response_data = smart_handler.process_message(user_id, message, 'coach')
print(f"Type: {response_type}, Confidence: {response_data['confidence']}")
```

### Database errors

```python
# Check if tables exist
import sqlite3
conn = sqlite3.connect('integrated_users.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%learning%'")
print(cursor.fetchall())
```

### Still using full AI too much

```python
# Check user profile
stats = smart_handler.get_user_stats(user_id)
print(f"Threshold: {stats['threshold']}")
print(f"Quick reply rate: {stats['quick_reply_rate']}")
```

---

## 📊 Monitor Performance

Add logging to see savings:

```python
import logging

# In your chat route
if response_type == 'quick_reply':
    logging.info(f"💰 SAVED COST - User {user_id} - '{message}' - Quick reply used")
else:
    logging.info(f"💸 API CALL - User {user_id} - '{message}' - Full AI needed")
```

Watch your console:
```
💰 SAVED COST - User 1 - 'hi' - Quick reply used
💰 SAVED COST - User 1 - 'thanks' - Quick reply used
💸 API CALL - User 1 - 'how do I improve productivity?' - Full AI needed
💰 SAVED COST - User 1 - 'ok' - Quick reply used
```

---

## 🚀 Deploy to Production

After local testing works:

```bash
# Commit changes
git add app.py smart_response_integration.py
git commit -m "Integrate Smart Response System into Coach chat"
git push origin main

# Auto-deploys via GitHub Actions!
# Wait 60 seconds, then reload PythonAnywhere
```

On PythonAnywhere, also run:
```bash
pip install spacy
python -m spacy download en_core_web_sm
python migrate_smart_response_tables.py
```

---

## ✅ Success Criteria

You'll know it's working when:

1. ⚡ **Instant responses** for "hi", "thanks", "ok", "bye"
2. 💰 **Lower API costs** (check OpenAI/Anthropic usage)
3. 📈 **Stats show learning** (`quick_reply_rate` increases over time)
4. 🎭 **Character voice maintained** (replies sound like Coach)
5. 🛡️ **Safety works** (complex/emotional topics still use AI)

---

**Ready to start? Let me know and I can help modify `app.py` for you!** 🚀
