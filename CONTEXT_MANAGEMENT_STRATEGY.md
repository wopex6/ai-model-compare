# 🎯 Smart Context Management Strategy

## **The Challenge**

Context management is indeed complicated. You need to balance:
- **Usefulness** - Only include relevant information
- **Timing** - Know when to load/update/clear
- **Dynamic** - Adapt as conversations evolve

## **Core Principle: Context Layers**

Instead of one giant context blob, use **layers** with different priorities:

```
┌─────────────────────────────────────┐
│  LAYER 1: IMMEDIATE (Last 2-3 msgs) │  ← Always include
├─────────────────────────────────────┤
│  LAYER 2: SESSION (Current topic)   │  ← Include if relevant
├─────────────────────────────────────┤
│  LAYER 3: RECENT (Last 7 days)      │  ← Include selectively
├─────────────────────────────────────┤
│  LAYER 4: HISTORICAL (30+ days)     │  ← Include rarely
└─────────────────────────────────────┘
```

---

## **Strategy 1: Usefulness - Relevance Scoring**

### **Problem:**
Including all context = noisy, expensive, confusing AI

### **Solution: Dynamic Relevance Scoring**

```python
class ContextRelevanceScorer:
    """
    Scores context items by relevance to current message
    Only passes high-scoring items to AI
    """
    
    def score_context_item(self, item: Dict, current_message: str, 
                           time_factor: float) -> float:
        """
        Score = Recency × Importance × Similarity × Usage
        Range: 0.0 to 1.0
        """
        score = 0.0
        
        # 1. RECENCY (40% weight)
        # Recent context more valuable
        recency_score = time_factor  # 1.0 = today, 0.5 = 7 days, 0.1 = 30 days
        score += recency_score * 0.4
        
        # 2. IMPORTANCE (30% weight)
        # Topics mentioned frequently are important
        importance = item.get('importance_score', 0.5)
        score += importance * 0.3
        
        # 3. SIMILARITY (20% weight)
        # Keywords overlap with current message
        similarity = self._calculate_similarity(
            current_message, 
            item.get('content', '')
        )
        score += similarity * 0.2
        
        # 4. USAGE (10% weight)
        # Context that led to successful interactions
        usage_success = item.get('usage_success_rate', 0.5)
        score += usage_success * 0.1
        
        return min(1.0, score)
    
    def _calculate_similarity(self, msg1: str, msg2: str) -> float:
        """Simple keyword overlap similarity"""
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'you'}
        words1 -= stop_words
        words2 -= stop_words
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        
        return overlap / total if total > 0 else 0.0
    
    def get_relevant_context(self, all_context: List[Dict], 
                            current_message: str, 
                            max_items: int = 5) -> List[Dict]:
        """
        Returns only the most relevant context items
        """
        import datetime
        
        # Score all items
        scored_items = []
        for item in all_context:
            # Calculate time factor
            item_time = datetime.datetime.fromisoformat(item['timestamp'])
            days_ago = (datetime.datetime.now() - item_time).days
            time_factor = max(0.1, 1.0 - (days_ago / 30))  # Decay over 30 days
            
            # Score item
            score = self.score_context_item(item, current_message, time_factor)
            
            # Only include if score > threshold
            if score > 0.3:  # Threshold
                scored_items.append((score, item))
        
        # Sort by score, take top N
        scored_items.sort(reverse=True, key=lambda x: x[0])
        relevant_items = [item for score, item in scored_items[:max_items]]
        
        return relevant_items
```

### **Usage:**

```python
# Before passing to AI:
scorer = ContextRelevanceScorer()

# Get all potential context
all_context = get_all_context(user_id, character)

# Filter to most relevant
relevant_context = scorer.get_relevant_context(
    all_context, 
    current_message, 
    max_items=5  # Only top 5 most relevant items
)

# Pass only relevant context to AI
ai_response = chat_with_context(message, relevant_context)
```

**Benefits:**
- ✅ Only useful context passed to AI
- ✅ Reduces token usage (cheaper!)
- ✅ Less noise = better AI responses
- ✅ Automatically adapts to conversation

---

## **Strategy 2: Timing - Smart Load/Update/Clear**

### **Problem:**
When to load? When to update? When to clear?

### **Solution: State-Based Context Lifecycle**

```python
class ContextLifecycleManager:
    """
    Manages WHEN to load, update, and clear context
    """
    
    # Context states
    FRESH = "fresh"           # Just loaded, <1 min old
    STALE = "stale"           # >5 min old, needs refresh
    EXPIRED = "expired"       # >1 hour old, needs reload
    ARCHIVED = "archived"     # >7 days old, historical only
    
    def __init__(self):
        self.context_cache = {}  # {user_character: {context, loaded_at, state}}
        self.update_thresholds = {
            'message_count': 5,      # Update every 5 messages
            'time_minutes': 15,      # Or every 15 minutes
            'topic_shift_detected': True  # Or on topic shift
        }
    
    def should_load_context(self, user_id: int, character: str, 
                           current_time: datetime) -> bool:
        """Decide if context needs loading"""
        
        cache_key = f"{user_id}_{character}"
        
        # No cache? Load it
        if cache_key not in self.context_cache:
            print("🔄 Loading context: Not in cache")
            return True
        
        cached = self.context_cache[cache_key]
        loaded_at = cached['loaded_at']
        age_minutes = (current_time - loaded_at).total_seconds() / 60
        
        # Check state
        if age_minutes < 1:
            print("✓ Context FRESH - Using cache")
            return False
        elif age_minutes < 5:
            print("✓ Context valid - Using cache")
            return False
        elif age_minutes < 60:
            print("⚠️  Context STALE - Refreshing")
            return True
        else:
            print("🔄 Context EXPIRED - Reloading")
            return True
    
    def should_update_context(self, user_id: int, character: str, 
                             exchange_count: int, 
                             last_update: datetime,
                             topic_shift: bool = False) -> Tuple[bool, str]:
        """Decide if context needs updating"""
        
        reasons = []
        
        # Reason 1: Message count threshold
        if exchange_count % self.update_thresholds['message_count'] == 0:
            reasons.append("message_threshold")
        
        # Reason 2: Time threshold
        minutes_since = (datetime.now() - last_update).total_seconds() / 60
        if minutes_since > self.update_thresholds['time_minutes']:
            reasons.append("time_threshold")
        
        # Reason 3: Topic shift detected
        if topic_shift:
            reasons.append("topic_shift")
        
        # Reason 4: Session boundary (user returned after absence)
        if minutes_since > 60:
            reasons.append("session_boundary")
        
        should_update = len(reasons) > 0
        reason_str = ", ".join(reasons) if reasons else "none"
        
        return should_update, reason_str
    
    def should_clear_context(self, context_age_days: int, 
                            last_message_days: int) -> Tuple[bool, str]:
        """Decide if context should be cleared"""
        
        # Clear if:
        # 1. No activity in 30+ days
        if last_message_days > 30:
            return True, "inactive_30_days"
        
        # 2. Context very old (90+ days) and not accessed
        if context_age_days > 90:
            return True, "context_expired_90_days"
        
        # 3. User explicitly requested (not shown here)
        
        return False, "active"
    
    def get_context_with_lifecycle(self, user_id: int, character: str) -> Dict:
        """
        Get context with intelligent loading/caching
        """
        current_time = datetime.now()
        cache_key = f"{user_id}_{character}"
        
        # Check if we should load
        if self.should_load_context(user_id, character, current_time):
            # Load from database
            context = self._load_from_database(user_id, character)
            
            # Cache it
            self.context_cache[cache_key] = {
                'context': context,
                'loaded_at': current_time,
                'state': self.FRESH
            }
            
            return context
        else:
            # Use cached
            return self.context_cache[cache_key]['context']
```

### **Usage Example:**

```python
lifecycle_manager = ContextLifecycleManager()

# In your chat endpoint:
def process_message(user_id, character, message, exchange_count):
    # 1. LOAD (with caching)
    context = lifecycle_manager.get_context_with_lifecycle(user_id, character)
    
    # 2. USE
    response = generate_response(message, context)
    
    # 3. UPDATE (conditionally)
    topic_shift = detect_topic_shift(message, context)
    should_update, reason = lifecycle_manager.should_update_context(
        user_id, character, exchange_count, context['last_update'], topic_shift
    )
    
    if should_update:
        print(f"💾 Updating context: {reason}")
        update_context(user_id, character, message, response)
    
    # 4. CLEAR (occasionally)
    should_clear, reason = lifecycle_manager.should_clear_context(
        context['age_days'], context['last_message_days']
    )
    
    if should_clear:
        print(f"🗑️  Clearing context: {reason}")
        clear_context(user_id, character)
    
    return response
```

**Benefits:**
- ✅ Smart caching (reduces DB queries)
- ✅ Automatic refresh when needed
- ✅ Clear rules for updates
- ✅ Auto-cleanup of old context

---

## **Strategy 3: Dynamic - Adaptive Context**

### **Problem:**
Conversations evolve. Yesterday's context may be irrelevant today.

### **Solution: Adaptive Context Windows**

```python
class AdaptiveContextManager:
    """
    Dynamically adjusts context based on conversation flow
    """
    
    def get_adaptive_context(self, user_id: int, character: str, 
                            current_message: str) -> Dict:
        """
        Returns context that adapts to conversation state
        """
        
        # Detect conversation mode
        mode = self._detect_conversation_mode(current_message)
        
        if mode == "NEW_TOPIC":
            # New topic → focus on general context, less history
            return self._get_minimal_context(user_id, character)
        
        elif mode == "CONTINUING":
            # Continuing → focus on recent context
            return self._get_recent_context(user_id, character, window=5)
        
        elif mode == "CALLBACK":
            # Referencing old topic → bring back relevant history
            return self._get_callback_context(user_id, character, current_message)
        
        elif mode == "EMOTIONAL":
            # Emotional message → include emotional history
            return self._get_emotional_context(user_id, character)
        
        else:  # DEFAULT
            return self._get_balanced_context(user_id, character)
    
    def _detect_conversation_mode(self, message: str) -> str:
        """Detect what kind of conversation this is"""
        msg_lower = message.lower()
        
        # Callback indicators
        callback_words = ['remember', 'you said', 'earlier', 'before', 'last time']
        if any(word in msg_lower for word in callback_words):
            return "CALLBACK"
        
        # Emotional indicators
        emotional_words = ['feel', 'feeling', 'emotion', 'upset', 'happy', 'sad', 
                          'anxious', 'worried', 'excited', 'angry', 'frustrated']
        if any(word in msg_lower for word in emotional_words):
            return "EMOTIONAL"
        
        # New topic indicators
        new_topic_words = ['new', 'different', 'change topic', 'another thing', 
                          'by the way', 'also', 'unrelated']
        if any(word in msg_lower for word in new_topic_words):
            return "NEW_TOPIC"
        
        # Default: continuing conversation
        return "CONTINUING"
    
    def _get_minimal_context(self, user_id: int, character: str) -> Dict:
        """Minimal context for new topics"""
        return {
            'mode': 'minimal',
            'summary': get_high_level_summary(user_id, character),
            'user_preferences': get_user_preferences(user_id),
            'recent_messages': []  # Empty - fresh start
        }
    
    def _get_recent_context(self, user_id: int, character: str, 
                           window: int = 5) -> Dict:
        """Recent context for continuing conversations"""
        return {
            'mode': 'recent',
            'recent_messages': get_last_n_messages(user_id, character, window),
            'current_topic': get_current_topic(user_id, character),
            'ongoing_threads': get_active_threads(user_id, character)
        }
    
    def _get_callback_context(self, user_id: int, character: str, 
                             message: str) -> Dict:
        """Search for relevant historical context"""
        # Extract what user is referring to
        keywords = extract_keywords(message)
        
        # Search historical messages
        relevant_history = search_context_by_keywords(
            user_id, character, keywords, max_results=3
        )
        
        return {
            'mode': 'callback',
            'relevant_history': relevant_history,
            'summary': get_high_level_summary(user_id, character)
        }
    
    def _get_emotional_context(self, user_id: int, character: str) -> Dict:
        """Context focused on emotional history"""
        return {
            'mode': 'emotional',
            'emotional_history': get_emotional_messages(user_id, character),
            'current_emotional_state': get_emotional_state(user_id, character),
            'recent_messages': get_last_n_messages(user_id, character, 3)
        }
    
    def _get_balanced_context(self, user_id: int, character: str) -> Dict:
        """Balanced context for normal conversation"""
        return {
            'mode': 'balanced',
            'summary': get_summary(user_id, character),
            'recent_topics': get_recent_topics(user_id, character, limit=3),
            'recent_messages': get_last_n_messages(user_id, character, 5),
            'ongoing_threads': get_active_threads(user_id, character)
        }
```

### **Example Adaptation:**

```
Conversation Start:
User: "Hi!"
Mode: NEW_TOPIC → Minimal context (just user preferences)

User: "I want to improve my fitness"
Mode: NEW_TOPIC → Create new context for fitness

User: "What should I do first?"
Mode: CONTINUING → Include recent context (fitness topic)

User: "I feel overwhelmed though"
Mode: EMOTIONAL → Add emotional context layer

User: "Remember what you said about goals?"
Mode: CALLBACK → Search historical context for "goals"
```

**Benefits:**
- ✅ Context adapts to conversation flow
- ✅ Doesn't overload AI with irrelevant info
- ✅ Handles topic shifts gracefully
- ✅ Retrieves old context when needed

---

## **Complete Implementation: All 3 Strategies Combined**

```python
class SmartContextManager:
    """
    Combines all three strategies for production-ready context management
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.scorer = ContextRelevanceScorer()
        self.lifecycle = ContextLifecycleManager()
        self.adaptive = AdaptiveContextManager()
    
    def get_smart_context(self, user_id: int, character: str, 
                         current_message: str) -> Dict:
        """
        One method to rule them all!
        Gets the perfect context for this exact moment.
        """
        
        # STEP 1: TIMING - Check if we need to load
        if not self.lifecycle.should_load_context(user_id, character, datetime.now()):
            print("✓ Using cached context")
            cached = self.lifecycle.context_cache.get(f"{user_id}_{character}")
            if cached:
                return cached['context']
        
        # STEP 2: DYNAMIC - Get adaptive context based on conversation mode
        print("🔄 Loading adaptive context...")
        raw_context = self.adaptive.get_adaptive_context(
            user_id, character, current_message
        )
        
        # STEP 3: USEFULNESS - Score and filter to most relevant
        print("🎯 Scoring context relevance...")
        if 'recent_messages' in raw_context:
            relevant_messages = self.scorer.get_relevant_context(
                raw_context['recent_messages'], 
                current_message, 
                max_items=5
            )
            raw_context['recent_messages'] = relevant_messages
        
        # Format for AI
        formatted_context = self._format_for_ai(raw_context)
        
        print(f"✅ Smart context ready: {len(formatted_context)} chars, "
              f"{raw_context.get('mode', 'balanced')} mode")
        
        return formatted_context
    
    def _format_for_ai(self, context: Dict) -> str:
        """Format context for AI consumption"""
        lines = ["[Context]"]
        
        if context.get('summary'):
            lines.append(f"Summary: {context['summary']}")
        
        if context.get('current_topic'):
            lines.append(f"Current topic: {context['current_topic']}")
        
        if context.get('recent_messages'):
            lines.append("Recent:")
            for msg in context['recent_messages'][-3:]:  # Last 3
                role = msg.get('role', 'user')
                content = msg.get('content', '')[:100]  # Truncate
                lines.append(f"  {role}: {content}")
        
        if context.get('emotional_state'):
            lines.append(f"User mood: {context['emotional_state']}")
        
        return "\n".join(lines)
```

### **Usage in Production:**

```python
# In your chat endpoint:
smart_context_mgr = SmartContextManager(db)

def chat_with_smart_context(user_id, character, message):
    # Get perfect context for this moment
    context = smart_context_mgr.get_smart_context(user_id, character, message)
    
    # Pass to AI
    response = ai_chat(message, context)
    
    # Update context (automatic timing checks inside)
    smart_context_mgr.lifecycle.update_if_needed(user_id, character, message, response)
    
    return response
```

**Console Output:**
```
🔄 Loading adaptive context...
   Detected mode: CONTINUING
🎯 Scoring context relevance...
   5 items scored, 3 above threshold
✅ Smart context ready: 245 chars, continuing mode
```

---

## **Recommended Configuration**

### **For Most Applications:**

```python
CONTEXT_CONFIG = {
    # USEFULNESS
    'relevance_threshold': 0.3,      # Minimum score to include
    'max_context_items': 5,          # Max items to pass to AI
    'max_context_chars': 500,        # Character limit for context
    
    # TIMING
    'cache_duration_minutes': 5,     # How long to cache
    'update_frequency_messages': 5,  # Update every N messages
    'clear_after_days': 30,          # Clear inactive context
    
    # DYNAMIC
    'enable_adaptive_mode': True,    # Use adaptive context
    'emotional_detection': True,     # Track emotions
    'callback_search_enabled': True, # Search historical context
}
```

### **For High-Volume Applications:**

```python
CONTEXT_CONFIG_HIGH_VOLUME = {
    'relevance_threshold': 0.5,      # Higher threshold (more selective)
    'max_context_items': 3,          # Fewer items (cheaper)
    'cache_duration_minutes': 10,    # Longer cache (fewer DB calls)
    'update_frequency_messages': 10, # Less frequent updates
}
```

### **For Deep Conversations:**

```python
CONTEXT_CONFIG_DEEP = {
    'relevance_threshold': 0.2,      # Lower threshold (more context)
    'max_context_items': 10,         # More items (richer context)
    'max_context_chars': 1000,       # More detail
    'callback_search_enabled': True, # Important for deep talks
}
```

---

## **Summary: Managing Context Complexity**

| Challenge | Solution | Benefit |
|-----------|----------|---------|
| **Usefulness** | Relevance scoring | Only relevant context → better AI |
| **Timing** | Lifecycle management | Smart caching → fewer DB calls |
| **Dynamic** | Adaptive windows | Context adapts → natural flow |

**Result:**
- Context stays **useful** (scored by relevance)
- Context stays **timely** (smart loading/caching)
- Context stays **dynamic** (adapts to conversation)

All automated. No manual management needed. 🚀
