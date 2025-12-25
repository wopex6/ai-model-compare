# User Personalization System

## Overview

Every user is unique with different:
- **Character/personality preferences**
- **Interests and background**
- **Goals and aspirations**
- **Communication styles**
- **Habits and routines**
- **Temporary emotions, desires, and needs**

This system provides **default parameters as starting points** that **adapt per-user over time** based on their interactions.

---

## Architecture

### Database Tables

| Table | Purpose |
|-------|---------|
| `user_personalization` | Stores per-user parameter overrides |
| `user_parameter_history` | Tracks all parameter changes (for debugging/learning) |
| `user_interaction_signals` | Records behavior signals for adaptive learning |

### Key Classes

- **`UserPersonalization`** (`smart_response/user_personalization.py`) - Main manager
- Integrated with **`CharacterManager`** for personalized routing thresholds

---

## Parameter Categories

### 1. Routing Thresholds
Control which domain characters respond to user messages.

```python
"routing": {
    "coordinator_threshold": 0.1,
    "domain_mental_health_threshold": 0.25,
    "domain_finance_threshold": 0.25,
    "domain_relationships_threshold": 0.25,
    "domain_career_threshold": 0.25,
    "domain_creativity_threshold": 0.25,
    "domain_learning_threshold": 0.25,
    "domain_physical_health_threshold": 0.25,
}
```

**Lower threshold** = Character responds more often
**Higher threshold** = Character responds less often

### 2. Communication Style
How the AI communicates with the user.

```python
"communication": {
    "preferred_tone": "warm",        # warm, professional, casual, direct
    "emoji_preference": "moderate",  # none, minimal, moderate, frequent
    "response_length": "medium",     # brief, medium, detailed
    "formality_level": 0.5,          # 0.0 (casual) to 1.0 (formal)
    "encouragement_level": 0.7,      # How much positive reinforcement
    "directness_level": 0.5,         # 0.0 (gentle hints) to 1.0 (very direct)
}
```

### 3. Engagement Preferences
How proactively the system engages the user.

```python
"engagement": {
    "proactive_prompts_enabled": True,
    "prompt_frequency_hours": 24,      # How often to send prompts
    "inactivity_check_minutes": 5,     # When to send inactivity messages
    "follow_up_enabled": True,         # Follow up on previous suggestions
    "theme_based_prompts": True,       # Use extracted themes for prompts
}
```

### 4. Content Preferences
What topics to focus on or avoid.

```python
"content": {
    "preferred_topics": [],      # Auto-populated from theme extraction
    "avoided_topics": [],        # Topics user doesn't want to discuss
    "goal_focus_areas": [],      # User's stated goals
    "sensitivity_topics": [],    # Topics requiring extra care
}
```

### 5. Timing Preferences
When the user is active and prefers to interact.

```python
"timing": {
    "active_hours_start": 8,         # 8 AM
    "active_hours_end": 22,          # 10 PM
    "timezone_offset": 0,            # UTC offset in hours
    "preferred_check_in_time": None, # Specific time for daily check-in
}
```

### 6. Adaptation Settings
How quickly the system learns and adapts.

```python
"adaptation": {
    "learning_rate": 0.1,            # How quickly to adjust parameters
    "feedback_weight": 0.3,          # How much feedback affects adjustments
    "recency_weight": 0.7,           # Weight for recent vs old interactions
    "min_interactions_to_adapt": 5,  # Minimum interactions before adapting
}
```

---

## API Endpoints

### Get User Parameters
```http
GET /api/user/personalization
Authorization: Bearer <token>
```

Returns all parameters (defaults merged with user customizations).

### Update Parameters
```http
PUT /api/user/personalization
Authorization: Bearer <token>
Content-Type: application/json

{
  "parameters": {
    "communication": {
      "preferred_tone": "professional"
    }
  },
  "reason": "User preference"
}
```

### Set Single Parameter
```http
PUT /api/user/personalization/parameter
Authorization: Bearer <token>
Content-Type: application/json

{
  "path": "routing.domain_mental_health_threshold",
  "value": 0.15,
  "reason": "User prefers mental health advice"
}
```

### View Change History
```http
GET /api/user/personalization/history?path=routing.domain_mental_health_threshold&limit=20
Authorization: Bearer <token>
```

### Record Interaction Signal
```http
POST /api/user/personalization/signal
Authorization: Bearer <token>
Content-Type: application/json

{
  "signal_type": "preferred_character",
  "signal_value": "domain_mental_health",
  "context": "User explicitly asked for mental health advice"
}
```

**Signal Types:**
- `positive_response` - User responded positively
- `negative_response` - User responded negatively
- `topic_interest` - User showed interest in a topic
- `topic_avoid` - User avoided/disliked a topic
- `preferred_character` - User preferred a specific character
- `response_length_feedback` - User indicated length preference
- `prompt_dismissed` - User dismissed a proactive prompt
- `prompt_engaged` - User engaged with a proactive prompt
- `timing_preference` - User activity at specific times

### Trigger Adaptive Learning
```http
POST /api/user/personalization/adapt
Authorization: Bearer <token>
```

Processes unprocessed signals and updates parameters accordingly.

### Reset to Defaults
```http
POST /api/user/personalization/reset
Authorization: Bearer <token>
Content-Type: application/json

{
  "category": "routing"  // Optional: reset only one category
}
```

### Export Full Profile
```http
GET /api/user/personalization/export
Authorization: Bearer <token>
```

---

## Adaptive Learning Flow

```
User Interaction
       ↓
Record Signal (automatic)
       ↓
Accumulate 5+ Signals
       ↓
Process Signals → Adapt Parameters
       ↓
Apply to Future Routing/Responses
```

### Auto-Recorded Signals

The system automatically records signals when:
1. **Character responds** → `preferred_character` signal
2. **User gives feedback** → `preferred_character` or `topic_avoid` signal
3. **User engages with prompt** → `prompt_engaged` signal
4. **User dismisses prompt** → `prompt_dismissed` signal

---

## Integration with Character Routing

Characters now check personalized thresholds:

```python
# In manager.py
user_id = context.get('user_id')
threshold = character.get_threshold_for_user(user_id)
if character.should_respond(concern_level, user_id):
    # Character responds
```

This means:
- **New users** get default thresholds
- **Returning users** get personalized thresholds based on their history
- **Thresholds adapt** as users provide feedback

---

## Adding New Parameters

When adding new parameters to the system:

1. **Add to `DEFAULT_USER_PARAMETERS`** in `user_personalization.py`
2. **Document the parameter** in this file
3. **Use `get_parameter()`** to read with fallback to defaults
4. **The system will automatically** merge new defaults with existing user data

---

## Testing

```javascript
// Get your personalization
fetch('/api/user/personalization', {
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('authToken')}
}).then(r => r.json()).then(console.log)

// Set a parameter
fetch('/api/user/personalization/parameter', {
  method: 'PUT',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('authToken'),
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    path: 'communication.preferred_tone',
    value: 'professional',
    reason: 'Testing'
  })
}).then(r => r.json()).then(console.log)
```

---

## Future Enhancements

- [ ] UI for users to view/edit their preferences
- [ ] AI-based parameter recommendations
- [ ] A/B testing of parameter combinations
- [ ] Export/import personalization profiles
- [ ] Time-based parameter variations (e.g., different style for morning vs evening)
