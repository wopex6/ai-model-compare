# Smart Response Character Tuning Guide
## Managing Quick Reply Aggressiveness Per Character

---

## **The Problem: Template Repetition**

**Issue Reported:**
- Life Coach and Zen Master were giving the same prepared answer repeatedly
- Example: "cool", "awesome", "great" all triggered same 3 acknowledgment templates

**Root Cause:**
1. **Over-broad pattern matching** - Too many words map to same category
   - `r'\b(cool|kool|coo|sweet|nice|great|awesome|perfect)\b'` → ALL = 'acknowledgment'
2. **Limited template variety** - Only 3 reply variations per category
3. **High confidence triggers** - 85-95% confidence = quick reply
4. **Character philosophy mismatch** - Some characters need personalization, not templates

---

## **The Solution: Character-Specific Thresholds**

Instead of one-size-fits-all, characters can have custom confidence thresholds:

```python
CHARACTER_SAFETY_RULES = {
    'life_coach': {
        'confidence_threshold': 0.97  # Very high - prefers AI
    },
    'zen_master': {
        'confidence_threshold': 0.97  # Very high - prefers AI
    },
    # Others use default 0.90
}
```

**Default threshold:** 0.90 (90% confidence)
**High threshold:** 0.97 (97% confidence - very rare!)

---

## **Character Analysis**

### **High Threshold Characters (0.97) - Prefer Full AI**

#### **1. Life Coach**
**Why:** Life transformation requires personalization
- Generic: "Wonderful! How does that feel in your body?" (template)
- Personalized: "That's great! Based on your career goals we discussed, this alignment with your values is significant progress. How do you want to build on this?" (contextual)

**Philosophy:** Coaching is about deep, personal work. Templates feel robotic.

**Quick replies ONLY for:**
- ✅ Greetings ("Hi" → "Hey there! Ready to create the life you want?")
- ✅ Farewells ("Bye" → "Take care! Remember to celebrate your wins!")
- ❌ Acknowledgments (use AI for personalization)

---

#### **2. Zen Master (Master Kai)**
**Why:** Zen teachings require mindful presence
- Generic: "Ah. The student hears the bell ring." (template)
- Personalized: "Ah, yes. Like the river you mentioned earlier - it flows without forcing. Your awareness of this pattern shows you're already finding the stillness within the movement." (present & contextual)

**Philosophy:** Each moment is unique. Generic responses miss the essence of "being present."

**Quick replies ONLY for:**
- ✅ Greetings ("Hi" → "*bows* Welcome, seeker. What question brings you to this moment?")
- ✅ Farewells ("Bye" → "Go gently. The path continues whether we walk it or not.")
- ❌ Acknowledgments (Zen requires mindful, unique responses)

---

### **Default Threshold Characters (0.90) - Balanced**

#### **3. Motivational Coach (Coach Max)**
**Why:** Quick motivation is effective
- "You got this! 💪 Keep crushing it!"
- "Awesome! 💪 What's next on your action list?"

**Philosophy:** High energy, rapid-fire motivation works well in templates.

**Quick replies work for:**
- ✅ Greetings, acknowledgments, thanks, farewells
- ⚠️ Complex goals/progress discussions use AI

---

#### **4. Business Coach**
**Why:** Quick strategic insights acceptable
- "Perfect! Now let's turn that insight into action. 📈"
- "Excellent! That's strategic thinking right there. 🎯"

**Philosophy:** Business guidance can be brief and actionable.

**Quick replies work for:**
- ✅ Greetings, acknowledgments
- ⚠️ Strategy development uses AI

---

#### **5. Stoic Marcus**
**Why:** Brief Stoic principles work well
- "Good. Understanding is the foundation of wisdom."
- "Indeed. Continue to contemplate these truths."

**Philosophy:** Stoic brevity is a feature, not a bug.

**Quick replies work for:**
- ✅ Greetings, acknowledgments, simple agreement
- ⚠️ Virtue/ethics discussions use AI (separate rules)

---

#### **6. Psychologist (Dr. Elena)**
**Why:** Safety rules handle critical topics separately
- Normal conversations: Templates OK
- Crisis topics: Always use AI (separate safety rules)

**Philosophy:** Balanced approach with safety override.

**Quick replies work for:**
- ✅ Greetings, acknowledgments
- ❌ Any critical keywords trigger full AI
- ❌ Mental health topics always use AI

---

#### **7. Scientist (Dr. Ada)**
**Why:** Quick facts/encouragement acceptable
- "Excellent! You're thinking like a scientist! 🔬"
- "Perfect! That's the scientific method at work. 📊"

**Philosophy:** Brief scientific encouragement is fine.

**Quick replies work for:**
- ✅ Greetings, acknowledgments
- ⚠️ Complex explanations use AI

---

#### **8. Wisdom Sage (Sage Wei)**
**Why:** Could go either way - currently default

**Consideration for future:** Might benefit from higher threshold (0.95-0.97) like Zen Master, since wisdom requires context and depth.

**Current:** Uses default 0.90

---

## **How the Threshold System Works**

### **Confidence Score Calculation:**

1. **Pattern Detection** (0-1 confidence)
   - "Hi" matches greeting pattern → 0.95 confidence
   - "cool" matches acknowledgment pattern → 0.85 confidence

2. **Context Adjustment** (±0.2)
   - Recent conversation context adds/subtracts confidence
   - "cool" after long AI explanation → +0.05 = 0.90

3. **Threshold Check:**
   ```python
   if adjusted_confidence >= character_threshold:
       use_quick_reply()
   else:
       use_full_ai()
   ```

### **Examples:**

**Life Coach (threshold 0.97):**
- "Hi" → 0.95 confidence → **Below 0.97** → Full AI ✅
- Actually, "Hi" is so obvious it gets 0.97+ → Quick reply ✅
- "cool" → 0.85 confidence → **Below 0.97** → Full AI ✅
- "Thanks so much!" → 0.92 confidence → **Below 0.97** → Full AI ✅

**Motivational Coach (threshold 0.90):**
- "Hi" → 0.95 confidence → **Above 0.90** → Quick reply ✅
- "cool" → 0.85 confidence → **Below 0.90** → Full AI ✅
- "Thanks!" → 0.95 confidence → **Above 0.90** → Quick reply ✅

---

## **Decision Framework**

### **When to Use High Threshold (0.95-0.97):**

✅ Character requires **depth and personalization**
✅ Generic templates feel **robotic or shallow**
✅ Philosophy emphasizes **unique, present responses**
✅ Work is **transformational** (not transactional)

**Examples:** Life Coach, Zen Master, possibly Wisdom Sage

### **When to Use Default Threshold (0.90):**

✅ Quick responses are **part of character's energy**
✅ Templates **don't hurt the philosophy**
✅ Character is **action-oriented** or **fact-based**
✅ Brevity is a **feature** (Stoicism, motivation)

**Examples:** Coach Max, Business Coach, Stoic Marcus, Scientist

### **When to Use Low Threshold (0.80-0.85):**

⚠️ **Not recommended** - Too many templates reduce quality
❌ Would trigger even for borderline/complex messages

---

## **Template Variety Analysis**

### **Current Templates Per Category:**

| Category | Templates | Enough? |
|----------|-----------|---------|
| Greeting | 3 | ✅ |
| Thanks | 3 | ✅ |
| Acknowledgment | 3 | ⚠️ (repetitive) |
| Agreement | 3 | ⚠️ (repetitive) |
| Farewell | 3 | ✅ |

**Problem Categories:**
- **Acknowledgment** - Used too often ("cool", "great", "awesome")
- **Agreement** - Similar issue ("yes", "yep", "totally")

**Solutions:**
1. ✅ **Raise threshold** (implemented for life_coach, zen_master)
2. 🔮 **Add more templates** (future - 5-7 per category)
3. 🔮 **Narrow patterns** (future - be more selective)

---

## **Future Improvements**

### **1. More Template Variety (Optional)**
Add 2-4 more templates per category to reduce cycling:
```python
'acknowledgment': [
    "Wonderful! How does that feel in your body? 💫",
    "Great awareness! That's the first step to transformation. ✨",
    "Perfect! You're really tuning into what matters most. 🌟",
    "Excellent! You're connecting with something important here. 💫",  # NEW
    "Beautiful insight! That kind of self-awareness is powerful. ✨",   # NEW
],
```

### **2. Contextual Template Selection (Optional)**
Instead of random selection, choose based on conversation context:
```python
if previous_message_was_emotional:
    return emotional_acknowledgment
elif previous_message_was_insight:
    return insight_acknowledgment
```

### **3. Pattern Refinement (Risky - Low Priority)**
Make patterns more selective (but risk missing valid small talk):
```python
# Current: Too broad
r'\b(cool|kool|coo|sweet|nice|great|awesome|perfect)\b'

# Refined: More conservative (might miss casual speech)
r'^(cool|great|awesome)$'  # Only if it's the ONLY word
```

---

## **Implementation Status**

### **✅ Completed:**
1. Life Coach threshold → 0.97
2. Zen Master threshold → 0.97
3. Character-specific threshold system implemented
4. Documentation (this file)

### **⏳ Optional Future:**
1. Add more template variations (5-7 per category)
2. Contextual template selection
3. Pattern refinement (risky)
4. Consider raising threshold for Wisdom Sage

### **📋 Testing Checklist:**

**For High Threshold Characters (Life Coach, Zen Master):**
- [ ] "Hi" → Quick greeting (obvious small talk)
- [ ] "Thanks" → Quick thanks (obvious)
- [ ] "cool" → **Full AI personalized** (not template!)
- [ ] "awesome" → **Full AI personalized** (different response!)
- [ ] "great" → **Full AI personalized** (different response!)
- [ ] No template repetition

**For Default Characters (Coach Max, Business Coach, etc.):**
- [ ] "Hi" → Quick greeting
- [ ] "Thanks" → Quick thanks
- [ ] "cool" → **Full AI** (below 0.90 threshold)
- [ ] "awesome" → **Full AI**
- [ ] Some quick replies, but less repetition

---

## **Configuration Reference**

### **File:** `smart_response/handler.py`

```python
CHARACTER_SAFETY_RULES = {
    'psychologist': {
        'critical_keywords': [...],  # Always use AI
        'sensitive_topics': [...]     # Always use AI
    },
    'life_coach': {
        'critical_keywords': [...],
        'prefer_full_ai': True,
        'confidence_threshold': 0.97  # High threshold
    },
    'zen_master': {
        'prefer_full_ai': True,
        'confidence_threshold': 0.97  # High threshold
    },
    'marcus': {
        'prefer_ai_keywords': [...]   # Certain topics use AI
    },
    # All others use default 0.90
}
```

### **Threshold Logic:**

```python
def process_message(self, user_id, message, character):
    # 1. Detect small talk
    detection = self.detector.detect(message, context)
    
    # 2. Get character threshold
    character_threshold = self._get_character_threshold(character)
    
    # 3. Compare
    if character_threshold is not None:
        should_use_quick = confidence >= character_threshold
    else:
        should_use_quick = learner.should_use_quick_reply(...)
    
    # 4. Decide
    if should_use_quick:
        return quick_reply
    else:
        return full_AI
```

---

## **Summary**

**Problem:** Generic quick replies felt robotic for transformational characters
**Solution:** Character-specific confidence thresholds
**Result:** 
- ✅ Life Coach & Zen Master now use full AI (personalized) for 97% of messages
- ✅ Other characters maintain balanced quick reply usage
- ✅ No more template repetition issues

**Philosophy:** Match response style to character's core purpose
- **Transformation** → Personalization (high threshold)
- **Motivation/Facts** → Templates OK (default threshold)

---

**Document Created:** Dec 9, 2025, 9:45 PM  
**Status:** Implemented for life_coach and zen_master  
**Next:** Monitor user feedback, consider wisdom_sage adjustment
