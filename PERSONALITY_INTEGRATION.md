# Personality Integration System

**Created:** December 18, 2025  
**Status:** Fully Implemented and Active

## Overview

This document describes the personality integration system that connects user profile data, personality assessments, and inferred traits to the AI conversation system with dynamic adaptive thresholds.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐   Priority: 1 (highest)                │
│  │ assessment_history  │   Source: Formal Big5 assessment       │
│  │ (Big 5 Test)        │   Confidence: Up to 90%                │
│  └─────────────────────┘   Decay: 90-day half-life              │
│                                                                  │
│  ┌─────────────────────┐   Priority: 2                          │
│  │ inferred_personality│   Source: Conversation pattern analysis│
│  │ (Auto-inferred)     │   Confidence: Up to 70%                │
│  └─────────────────────┘   Decay: 30-day half-life              │
│                                                                  │
│  ┌─────────────────────┐   Priority: 3 (fallback)               │
│  │ Default traits      │   Source: Neutral defaults (0.5)       │
│  │                     │   Confidence: 30%                       │
│  └─────────────────────┘                                        │
│                                                                  │
│  ┌─────────────────────┐   Additional context                   │
│  │ user_profiles       │   Goals, interests, preferences        │
│  │ user_context        │   Extracted facts from conversations   │
│  └─────────────────────┘                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              PersonalityContextIntegrator                        │
│              smart_response/personality_context_integrator.py    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Collects data from all sources                              │
│  2. Resolves conflicts (priority-based)                         │
│  3. Computes adaptive thresholds                                │
│  4. Formats context for AI prompts                              │
│  5. Detects significant changes                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE THRESHOLDS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  personality_influence (0.1 - 0.9)                              │
│  ├── Base: 0.6 (assessment) or 0.4 (inferred)                   │
│  ├── × confidence_factor (data source reliability)              │
│  ├── × recency_factor (newer data = higher weight)              │
│  └── + emotional_boost (sensitive topics increase this)         │
│                                                                  │
│  goal_emphasis (0.1 - 0.9)                                      │
│  ├── Base: 0.7 (has goals) or 0.3 (no goals)                    │
│  └── + goal_relevance_boost (goal-related messages)             │
│                                                                  │
│  emotional_sensitivity (0.1 - 0.9)                              │
│  ├── Base: 0.3 + (neuroticism × 0.4)                            │
│  └── + emotional_intensity_boost (emotional messages)           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI PROMPT OUTPUT                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  USER CONTEXT:                                                   │
│  - User personality: curious, creative, emotionally stable      │
│  - User goals: improve work-life balance, learn meditation      │
│  - Preferred style: direct                                      │
│  - Interests: technology, psychology                            │
│  - Note: User may be emotionally sensitive (if applicable)      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Confidence Level System

### How Confidence Is Calculated

```python
# Assessment-based confidence (highest reliability)
base_confidence = 0.9
age_factor = 0.5 ** (age_days / 90)  # Half-life: 90 days
final_confidence = base_confidence * age_factor

# Example: 45-day-old assessment
# 0.9 * 0.5^(45/90) = 0.9 * 0.707 = 0.64 (64% confidence)

# Inferred-based confidence (lower reliability)
base_confidence = stored_confidence * 0.7  # Max 70%
age_factor = 0.5 ** (age_days / 30)  # Half-life: 30 days (faster decay)
final_confidence = base_confidence * age_factor
```

### Confidence Triggers

| Event | Action |
|-------|--------|
| New assessment saved | Confidence jumps to ~90% |
| Profile updated | Cache invalidated, recalculated |
| Inferred traits updated | Confidence recalculated |
| Time passes | Confidence decays automatically |

---

## Continuous Trait Refinement

### How It Works

1. **Every conversation message** is analyzed by `TraitInferenceEngine`
2. Pattern matching detects Big5 trait indicators in text
3. Traits are updated in `inferred_personality` table
4. `PersonalityContextIntegrator` cache is invalidated
5. Next conversation uses updated traits

### Trait Detection Patterns (Examples)

```python
# Openness indicators
'high': ['creative', 'curious', 'imaginative', 'innovative', 'explore']
'low': ['routine', 'traditional', 'practical', 'familiar']

# Conscientiousness indicators  
'high': ['organized', 'plan', 'schedule', 'prepare', 'goal']
'low': ['spontaneous', 'flexible', 'laid-back', 'improvise']

# Extraversion indicators
'high': ['party', 'social', 'excited', 'energetic', 'outgoing']
'low': ['quiet', 'alone', 'reserved', 'solitary', 'reflective']

# Agreeableness indicators
'high': ['help', 'support', 'care', 'kind', 'empathy']
'low': ['compete', 'challenge', 'critical', 'disagree']

# Neuroticism indicators
'high': ['stressed', 'anxious', 'worried', 'overwhelmed', 'nervous']
'low': ['calm', 'stable', 'confident', 'resilient', 'secure']
```

### Update Frequency

- **TraitInferenceEngine** runs `run_inference_if_needed()` which checks:
  - Minimum message threshold reached
  - Minimum time since last inference
  - Prevents excessive recalculation

---

## Auto-Update on Data Changes

### Cache Invalidation Points

| Location | Trigger | File |
|----------|---------|------|
| `save_psychological_assessment()` | Assessment saved | app.py:2770-2773 |
| `update_profile()` | Profile updated | app.py:1140-1142 |
| `update_comprehensive_preferences()` | Preferences changed | app.py:1202-1204 |
| Domain characters route | Traits inferred | app.py:3095-3097 |

### Code Example

```python
# After saving assessment
if personality_integrator:
    personality_integrator.invalidate_cache(user_id)
    print(f"[PERSONALITY] Cache invalidated for user {user_id} after assessment")
```

---

## Dynamic Threshold Adaptation

### Message Analysis

The system analyzes each message to determine conversation state:

```python
def get_conversation_state_from_message(message):
    # Emotional intensity detection
    emotional_words = ['stressed', 'anxious', 'happy', 'frustrated', ...]
    emotional_intensity = count_matches / threshold
    
    # Topic sensitivity detection
    sensitive_patterns = ['personal', 'relationship', 'health', 'career', ...]
    topic_sensitivity = count_matches / threshold
    
    # Goal relevance detection
    goal_patterns = ['goal', 'want to', 'working on', 'improve', ...]
    goal_relevance = count_matches / threshold
    
    return {
        'emotional_intensity': 0.0 - 1.0,
        'topic_sensitivity': 0.0 - 1.0,
        'goal_relevance': 0.0 - 1.0
    }
```

### Threshold Adjustment Examples

```
Message: "I'm feeling really stressed about my career lately"
├── emotional_intensity: 0.50 (stressed, feeling)
├── topic_sensitivity: 0.60 (career, personal concern)
└── goal_relevance: 0.15 (not directly goal-related)

Threshold adjustments:
├── personality_influence: base + 0.12 (sensitivity boost)
├── emotional_sensitivity: base + 0.125 (emotional boost)  
└── goal_emphasis: base + 0.045 (minimal boost)

Result: AI response emphasizes emotional support, uses personality
        traits to calibrate response tone
```

---

## Files Modified/Created

### New Files

| File | Purpose |
|------|---------|
| `smart_response/personality_context_integrator.py` | Main integration module (~450 lines) |
| `PERSONALITY_INTEGRATION.md` | This documentation |

### Modified Files

| File | Changes |
|------|---------|
| `app.py` | Added import, initialization, integration into routes, cache invalidation |

### Integration Points in app.py

```python
# Line 154: Import
from smart_response.personality_context_integrator import create_personality_integrator

# Line 164: Initialize
personality_integrator = create_personality_integrator(smart_response_conn, integrated_db)

# Lines 2928-2956: Domain characters integration
# - Analyzes message for conversation state
# - Gets personality context with adaptive thresholds
# - Formats for AI prompt
# - Detects changes

# Lines 3088-3099: Continuous trait refinement
# - Runs trait inference
# - Invalidates cache if traits updated

# Lines 1140-1142, 1202-1204, 2770-2773: Cache invalidation
# - Profile update, preferences update, assessment save
```

---

## Data Flow Summary

```
User sends message
        │
        ▼
┌───────────────────────────────────────┐
│ 1. Analyze message for conversation   │
│    state (emotional, sensitive, goal) │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 2. Get personality context            │
│    - Check cache (5 min TTL)          │
│    - Load traits (assessment/inferred)│
│    - Load profile (goals, interests)  │
│    - Compute adaptive thresholds      │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 3. Format for AI prompt               │
│    - Include notable traits           │
│    - Include goals (if relevant)      │
│    - Add sensitivity notes            │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 4. AI generates response using        │
│    personality-aware context          │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 5. After response: run trait inference│
│    - Analyze conversation patterns    │
│    - Update inferred_personality      │
│    - Invalidate cache if changed      │
└───────────────────────────────────────┘
        │
        ▼
    Next message uses updated context
```

---

## Configuration Options

### PersonalityContextIntegrator Settings

```python
# Cache TTL (how long before re-fetching data)
self._cache_ttl_minutes = 5

# Significant change threshold (triggers change notification)
self._significant_change_threshold = 0.15  # 15% change

# Trait interpretation thresholds
HIGH_THRESHOLD = 0.65  # Above this = "high" trait
LOW_THRESHOLD = 0.35   # Below this = "low" trait
# Between = neutral (not mentioned)
```

### Threshold Bounds

```python
AdaptiveThreshold:
    min_value = 0.1  # Never goes below 10%
    max_value = 0.9  # Never exceeds 90%
```

---

## Testing the Integration

### Verify Personality Context is Being Used

Look for these log messages in console:

```
[PERSONALITY] Added personality context (source: assessment, confidence: 85%)
[PERSONALITY] Added personality context (source: inferred, confidence: 45%)
[PERSONALITY] Change detected: openness increased; new goals: meditation
```

### Verify Trait Inference is Running

```
[TRAIT_INFERENCE] ✓ Updated traits for user 123 (confidence: 62%)
```

### Verify Cache Invalidation

```
[PERSONALITY] Cache invalidated for user 123 after assessment
```

---

## Message Routing History Fix (Dec 18, 2025)

### Problem
When users sent messages through Aria (coordinator) that were routed to domain characters, the original question wasn't appearing in the domain character's chat history.

### Solution
1. **app.py lines 3056-3060**: Save user message to domain character history when routing
```python
if target_character == 'coordinator' and char_id != 'coordinator':
    integrated_db.save_character_message(user_id, char_id, 'user', message)
```

2. **Migration script**: `migrate_routed_messages.py` - Fixes existing data by copying routed messages from coordinator to domain characters

### Result
Questions now appear in both:
- Coordinator view (with `[Character Name]` response attribution)
- Domain character view (direct question + response)

---

## Future Enhancements (Optional)

1. **Emotion trend tracking** - Track emotional patterns over time
2. **Style mirroring refinement** - Learn user's specific communication patterns
3. **Goal progress tracking** - Connect personality to goal achievement
4. **Character-specific adaptation** - Different characters weight traits differently

---

## Related Documentation

- `INTELLIGENT_CONTEXT_ARCHITECTURE.md` - Overall context system design
- `CHARACTER_SPECTRUM_SYSTEM.md` - Character trait system
- `SYSTEM_DESIGN_PRINCIPLES.md` - Design principles
