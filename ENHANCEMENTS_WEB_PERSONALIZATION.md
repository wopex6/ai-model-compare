# Web Platform Personalization Enhancements
## Session Log — March 2026

---

## Overview

This document captures all personalization, reliability, and UX enhancements made to the web platform. It is updated continuously as each feature is implemented and tested.

---

## Completed Enhancements

### 1. Network Reliability — Retry Logic & Session Reuse
**Files:** `ai_compare/models.py`  
**Status:** ✅ Implemented & Tested

**Problem fixed:**
- `MetaModel` and `GrokModel` created a new `aiohttp.ClientSession` on every single API call — a resource leak that slowed responses and could exhaust file descriptors under load.
- No retry logic existed for transient network failures (rate limits, server errors).

**What was done:**
- Added `_retry_with_backoff(coro_func, max_attempts=3, base_delay=1.0)` — exponential backoff with jitter, retries on HTTP 408/429/500/502/503/504.
- `MetaModel` and `GrokModel` now reuse a single `aiohttp.ClientSession` per instance via `_get_session()`.
- Added `close()` method to both for clean teardown.
- `ClaudeModel.get_response()` now accepts a `max_tokens` parameter (default 4000) so response length can be controlled per-call.

**Impact:** Transient failures now auto-recover instead of crashing. Resource usage drops significantly under concurrent load.

---

### 2. Verbosity Personalisation — Full Pipeline Wiring
**Files:** `ai_compare/chatbot.py`, `ai_compare/character_routes.py`  
**Status:** ✅ Implemented & Tested

**Problem fixed:**
- `user_personalization.py` already stored `communication.response_length` (brief/medium/detailed) per user, and `user_intelligence.py` already detected verbosity patterns — but neither was wired into the actual prompt builder. The entire system was built but dead.

**What was done in `chatbot.py`:**
- `chat()` and `_build_enhanced_prompt()` now accept a `user_id` parameter.
- If `user_id` is provided, pulls `communication.response_length` from `UserPersonalization` and injects a concrete `VERBOSITY:` instruction into the prompt (e.g. "Use 1-3 sentences max" vs "Go deep with examples").
- Context window expanded from **3 to 8** recent exchanges for better conversation continuity.

**What was done in `character_routes.py`:**
- `user_id` is now threaded into both `bot.chat()` call paths (smart_response and direct fallback).
- Verbosity signal detection: when a user's message contains phrases like "keep it short", "be brief", "elaborate", or "in detail", a `response_length_feedback` signal is recorded to `UserPersonalization`. Over time, `process_signals_and_adapt()` applies these signals to permanently update the user's `communication.response_length` preference.

---

### 3. Automatic Signal Processing — Preferences Actually Applied
**Files:** `ai_compare/character_routes.py`  
**Status:** ✅ Implemented & Tested

**Problem fixed:**
- `process_signals_and_adapt()` existed and was designed to update user preferences based on accumulated signals, but was **never called** anywhere. Signals were recorded but never applied.

**What was done:**
- After every successful chat response (inside a safe `try/except`), `process_signals_and_adapt(user_id)` is called.
- This processes accumulated `response_length_feedback` signals and adjusts `communication.response_length` to the most common preference.
- The call is positioned after the response is returned to the client — it never delays the user's reply.

---

### 4. Emotional Context in Prompts
**Files:** `ai_compare/chatbot.py`  
**Status:** ✅ Implemented & Tested

**Problem fixed:**
- `user_intelligence.py` had a full `analyze_emotional_journey()` method (sentiment trajectory, resolution indicators) that was **never used** to adapt AI responses.

**What was done:**
- `_build_enhanced_prompt()` now calls `analyze_emotional_journey(user_id, recent_messages=10)` when `user_id` is available.
- Only activates when `confidence >= 0.3` — no noise on cold start or new users.
- Injects an `EMOTIONAL CONTEXT:` instruction into the prompt:
  - `trajectory = 'declining'` → empathy-first, validate before advice
  - `trajectory = 'improving'` → direct and action-focused
  - `had_resolution = False` → check whether previous concerns were addressed
- All exceptions silently caught — never breaks a response if intelligence system is unavailable.

---

### 5. Advanced Comparison Metrics — Wired into /ask Endpoint
**Files:** `app.py`, `advanced_comparison_metrics.py`  
**Status:** ✅ Implemented & Tested

**Problem fixed:**
- `advanced_comparison_metrics.py` was a standalone module with no integration into the live comparison endpoint.

**What was done:**
- The `/ask` endpoint accepts an optional `include_metrics: true` param (default on).
- After model responses are received, `AdvancedResponseEvaluator.evaluate_responses()` is called.
- The JSON response now includes:
  - `comparison_metrics` — per-model scores: `semantic_similarity`, `token_efficiency`, `coherence_score`, `clarity_score`, `helpfulness_score`
  - `rankings` — best model per metric dimension
- Metrics failure is fully non-fatal: wrapped in `try/except`, core comparison always succeeds.

---

### 6. UI — Length Feedback Buttons
**Files:** `static/conversation_box.js`  
**Status:** ✅ Implemented & Tested

**What was done:**
- Added **"Too long"** (amber) and **"Too short"** (teal) buttons alongside the existing "Tell me more" / "Not what I meant" response actions.
- Clicking "Too long" sends a brief-preference message that also records a `response_length_feedback: brief` signal.
- Clicking "Too short" sends a detail-request message with `detail_requested: true` flag.
- Both buttons have distinct colour-coded CSS so users can visually distinguish length vs direction feedback.

---

### 7. Response Need Classifier — The "Exceptional" Feature
**File:** `smart_response/response_need_classifier.py`  
**Status:** ✅ Implemented & Tested

**What it does:**
Detects WHAT TYPE of response a user actually needs from their message, before the AI responds. This directly implements the original requirement: *"some need direction, some need action plan, some need immediate results, some need questions for inspiration, some need small steps advice, some need sympathy and listening."*

**8 need types detected:**

| Type | Trigger example | AI behaviour |
|---|---|---|
| `sympathy` | "I'm so overwhelmed and lost" | Listen first, reflect emotions, do NOT advise immediately |
| `direction` | "Should I stay or go? I can't decide" | Give a clear recommendation with reason |
| `action_plan` | "Give me a step-by-step plan to launch" | Numbered steps, first action doable TODAY |
| `immediate_result` | "Quick — what is X?" | Lead with the answer in sentence 1 |
| `small_steps` | "I'm paralysed. Break it down for me" | ONE tiny action, acknowledge overwhelm first |
| `inspiration` | "I feel stuck and uninspired" | Ask 1–2 powerful opening questions, reframe |
| `information` | "What is machine learning?" | Clear explanation at appropriate depth |
| `validation` | "Am I on the right track?" | Confirm what IS right, then gently correct if needed |

**Architecture:**
- Pure regex heuristics — zero API calls, zero latency, works offline
- `confidence` score (0–1) gates injection: only fires at ≥ 0.2
- `get_instruction()` returns a ready-to-inject `RESPONSE MODE — X:` block
- Module-level singleton via `get_need_classifier()`
- Never raises — always returns a valid classification

---

### 8. base_chatbot.py — Full Parity with chatbot.py
**File:** `ai_compare/base_chatbot.py`  
**Status:** ✅ Implemented & Tested

**Problem fixed:**
`base_chatbot.py` is the shared base class for all AI characters. It had **none** of the improvements made to `chatbot.py` — all characters using `BaseChatbot` were missing verbosity, emotional context, need classification, and had a 3-exchange context window.

**What was done:**
- `chat()`, `_core_process()`, `_build_enhanced_prompt()` all accept `user_id`
- `user_id` threaded through the full call chain: `chat → _core_process → _build_enhanced_prompt`
- Context window: 3 → **8 exchanges**
- All three adaptive instructions injected: verbosity + emotional context + need classification
- `CRITICAL RESPONSE RULES` block added (was missing from base)

---

### 9. Proactive Clarifier — "Immediate Attention" Feature
**File:** `smart_response/proactive_clarifier.py`  
**Wired in:** `ai_compare/character_routes.py`  
**Status:** ✅ Implemented & Tested

**What it does:**
Before sending to the AI, checks whether the message is clear enough to respond to well. If not, asks ONE targeted question. If a crisis signal is detected, responds with immediate empathy.

**Triggers (in priority order):**
1. **Crisis keywords** (e.g., "want to kill myself", "can't go on") → immediate empathy + "Are you safe?" — always fires regardless of confidence
2. **Vague messages** (< 4 words, confidence < 0.3) → targeted clarifying question for the detected need type
3. **Competing needs** (two strong signals, low confidence) → question to disambiguate
4. **Very low confidence** (< 0.21) → generic fallback question

**Why this saves money AND improves quality:**
- A vague message sent to AI wastes one API call and gets a generic response
- One clarifying question gets a specific follow-up that the AI can answer precisely
- Critical situations are handled safely before any AI call

**Pipeline position:** Fires BEFORE `ai_function` is called — no wasted API calls.

**Response format** (added to standard response JSON):
```json
{ "type": "clarification", "urgency": "normal|critical", "detected_need": "direction", "response": "..." }
```

---

### 10. Character Suggester — "Exceptional" Feature
**File:** `smart_response/character_suggester.py`  
**Wired in:** `ai_compare/character_routes.py`  
**Status:** ✅ Implemented & Tested

**What it does:**
After each AI response, checks whether the current character is the best match for the user's detected need. If a better-suited character exists and the user is on a specialist character, appends a gentle suggestion to the response.

**Need → Character mapping (top picks):**

| Need | Best character | Why |
|---|---|---|
| sympathy | The Psychologist | specialises in emotional support |
| direction | The Life Coach | confident decision guidance |
| action_plan | The Life Coach | concrete step-by-step planning |
| inspiration | The Sage | opens new perspectives with questions |
| small_steps | The Life Coach | breaks overwhelm into micro-steps |
| information | The Sage | clear, well-structured explanations |
| validation | The Life Coach | honest, constructive feedback |

**Design rules:**
- Never suggests switching away from general-purpose characters (Coach/Sage/Psychologist) — they handle everything well
- Only fires when need confidence ≥ 0.5
- Never forces — suggestion is metadata in the response, frontend shows it as a soft nudge
- Never raises, never blocks response

**Response metadata added:**
```json
{ "detected_need": "sympathy", "character_suggestion": { "character_id": "psychologist", "character_name": "The Psychologist", "reason": "specialises in emotional support", "message": "..." } }
```

---

### 11. Personalization Profile API Endpoint
**File:** `app.py`  
**Endpoint:** `GET /api/user/personalization-profile`  
**Status:** ✅ Implemented & Tested

**What it returns:**
- `response_length` — current verbosity preference (brief/medium/detailed)
- `parameters` — full user personalization parameters
- `emotional_journey` — recent sentiment trajectory and resolution status
- `communication_style` — detected formality, verbosity, message patterns

**Use cases:**
- Frontend profile/settings page showing "How the AI sees you"
- Debugging why the AI is responding a certain way
- User can see their learned preferences and understand the system

---

### 12. UI — Clarification Card + Character Suggestion Bar
**File:** `static/conversation_box.js`  
**Status:** ✅ Implemented & Tested

**Clarification Card:**
- When backend returns `type: 'clarification'`, the response is rendered as a distinct indigo-bordered card instead of a normal chat bubble
- Label reads "Just to clarify" (normal) or "Important" (critical/crisis situations)
- Critical cards use red accent styling to signal urgency
- Response action buttons are NOT shown for clarification responses (no "Tell me more" etc.)

**Character Suggestion Bar:**
- When backend returns `character_suggestion` with a suggestion, a soft amber nudge bar appears below the response
- Shows "💡 Based on what you've shared, [Character Name] (reason) might be especially helpful here. You can switch any time."
- Character name is a clickable link that calls `_handleCharacterSwitch()` — navigates to character page or fires `onCharacterSwitch` callback
- Only shown for normal AI responses, never for clarifications

**New `conversation_box.js` config option:**
```js
onCharacterSwitch: (characterId) => { /* handle switch */ }
```
If not provided, defaults to `window.location.href = '/{characterId}'`.

---

### 13. Explicit Context Auto-Extraction — "Absolute Truth" Feature
**Files:** `smart_response/explicit_context_handler.py` (pre-existing), wired into `ai_compare/character_routes.py` + `ai_compare/chatbot.py` + `ai_compare/base_chatbot.py`  
**Status:** ✅ Implemented & Tested

**The problem it fixes:**
Per the system design principle: *"User's explicit statements = absolute truth (CRITICAL priority). Trust user honesty — assume good faith. Explicit context overrides ALL inference."*

Previously, statements like "I'm feeling anxious", "My goal is to get a promotion", "I prefer direct answers" were parsed by the AI in context but **never stored**. They were lost after every response. The AI had no memory of what the user explicitly told it.

**What was wired:**

*Extraction (character_routes.py → on every user message):*
- `ExplicitContextHandler.extract_explicit_context(user_id, character_id, message)` called immediately after the message is saved to the database
- Detects 7 pattern types: `emotional_state`, `goal`, `preference`, `need`, `self_description`, `intention`, `value`
- Stored in the `explicit_context` table with `CRITICAL` priority
- Context merging: new emotional states/goals deactivate previous ones (no accumulation of stale data)
- Runs BEFORE the AI call — extraction happens before ProactiveClarifier check

*Injection (chatbot.py + base_chatbot.py prompt builder):*
- `format_for_ai_prompt(user_id, character_id)` retrieves all active CRITICAL-priority explicit context
- Injected at the **TOP** of the prompt, before any other instruction blocks
- This means when a user said "I want a promotion" two weeks ago, it shows up at the top of every prompt:
  ```
  WHAT THIS USER HAS EXPLICITLY TOLD YOU:
  - Goal: I want a promotion this year
  - Feeling: anxious about my performance review
  ```

**Pattern examples:**
```
"I'm feeling anxious"        → emotional_state.current = "anxious"
"My goal is a promotion"     → goal.main = "promotion"
"I prefer direct answers"    → preference.response_style = "direct"
"I need more structure"      → need.current = "structure"
"I'm an introvert"           → self_description.personality = "introvert"
"I plan to quit next month"  → intention.next_action = "quit"
"Honesty is important to me" → value.core = "honesty"
```

---

### 14. Long-term Progress Context — "TRANSFORMATION" Feature
**File:** `smart_response/progress_context_builder.py`  
**Wired into:** `ai_compare/chatbot.py`, `ai_compare/base_chatbot.py`  
**API:** `GET /api/user/progress-summary`  
**Status:** ✅ Implemented & Tested

**What it does:**
Builds a compact `LONG-TERM CONTEXT` block from the dual-layer history secondary layer (analytical interpretations of past conversations). Injected into the AI prompt so the AI can reference patterns across sessions — e.g. *"You've been working toward a goal across multiple sessions"* or *"You have recurring concerns around this topic."*

**Surfaced signals (from secondary history):**
- Recurring topics (appear 2+ times across sessions)
- Recurring concerns (appear 2+ times)
- Dominant emotional tone across recent sessions
- Goal-tracking signals (multiple sessions mentioning goals)
- Obstacle-tracking signals (multiple sessions with obstacles)

**Constraints:**
- Max 8 lines in the prompt block (no prompt bloat)
- Only fires when ≥ 2 occurrences of a theme (signal over noise)
- New users with no history get an empty string — no noise
- All errors return empty string — never blocks a response

**Prompt injection example:**
```
LONG-TERM CONTEXT (from previous conversations):
- Topics this user often discusses: career, promotion
- Recurring concerns: performance review
- Emotional trend in recent sessions: anxious
- User has been working toward a goal across multiple sessions.
(Use this context naturally — reference it when relevant, not mechanically.)
```

---

## Automated Test Suite
**File:** `tests/test_web_enhancements.py`  
**Command:** `pytest tests/test_web_enhancements.py -v`

| Test Group | Tests | Status |
|---|---|---|
| Models — Retry & Session | 8 | ✅ All pass |
| Chatbot — Verbosity & Context | 5 | ✅ All pass |
| Character Routes — Verbosity Wiring | 3 | ✅ All pass |
| UI — Feedback Buttons | 6 | ✅ All pass |
| Verbosity System (standalone) | 4 | ✅ All pass |
| Advanced Metrics | 3 | ✅ All pass |
| Signal Processing — Wired | 3 | ✅ All pass |
| Emotional Context — Wired | 6 | ✅ All pass |
| /ask Endpoint — Comparison Metrics | 5 | ✅ All pass |
| Documentation Coverage | 7 | ✅ All pass |
| ResponseNeedClassifier — 8 need types | 14 | ✅ All pass |
| base_chatbot.py — Full Parity | 8 | ✅ All pass |
| ProactiveClarifier | 9 | ✅ All pass |
| CharacterSuggester | 10 | ✅ All pass |
| Routes — Clarifier + Suggester Wired | 6 | ✅ All pass |
| Personalization Profile Endpoint | 6 | ✅ All pass |
| UI — Clarification Card + Suggestion Bar | 10 | ✅ All pass |
| Explicit Context Extraction Wiring | 15 | ✅ All pass |
| ProgressContextBuilder + Wiring | 9 | ✅ All pass |
| Dual-Layer History Storage Wiring | 8 | ✅ All pass |
| Character Effectiveness Tracking | 10 | ✅ All pass |
| CharacterSuggester Effectiveness Weighting | 8 | ✅ All pass |
| Personalization Status Indicator | 14 | ✅ All pass |
| GoalCheckInBuilder | 10 | ✅ All pass |
| SessionEngagementTracker | 11 | ✅ All pass |
| FrustrationDetector | 12 | ✅ All pass |
| MilestoneDetector | 11 | ✅ All pass |
| ToneCalibrator | 12 | ✅ All pass |
| **TOTAL** | **233** | ✅ **100%** |

---

### 15. Dual-Layer History Storage — Critical Gap Closed
**Wired in:** `ai_compare/character_routes.py`  
**Status:** ✅ Implemented & Tested

**The gap:**  
`DualLayerHistorySystem` existed but was never called from the character chat route. This meant the secondary (analytical) layer was empty, making `ProgressContextBuilder` return empty strings for all users in production.

**What was wired:**
After every AI response (after the response dict is built and before returning), calls:
1. `store_interaction(user_id, character_id, message, ai_text, response_type)` — stores the raw exchange in the primary layer
2. `analyze_and_store_secondary(primary_id, user_id, character_id)` — auto-analyzes topics, intents, concerns, opportunities and stores them in the secondary layer

**Result:**  
Each conversation turn now automatically populates the analytical history that feeds both `ProgressContextBuilder` and long-term trend analysis. After 2+ conversations discussing the same topics, the AI will receive context about recurring patterns.

---

## Complete Message Pipeline — All Features

```
USER sends message
       │
       ▼
character_routes.py — PRE-PROCESSING
  ├─ [1] Save user message to database
  ├─ [2] ExplicitContextHandler.extract_explicit_context()
  │       → stores "I'm feeling X / My goal is Y" in explicit_context table
  ├─ [3] Detect verbosity phrases → record response_length_feedback signal
  ├─ [4] ProactiveClarifier.decide()
  │       → CRISIS: return immediate empathy card (no AI call)
  │       → VAGUE / LOW CONFIDENCE: return clarification question (no AI call)
  │       → CLEAR: continue to AI
  └─ [5] Calls bot.chat(message, user_id=user_id)
       │
       ▼
chatbot.py _build_enhanced_prompt(user_id=...)
  ├─ [6]  explicit_context_block  ← ExplicitContextHandler.format_for_ai_prompt()
  │         "WHAT THIS USER HAS EXPLICITLY TOLD YOU: Goal: promotion, Feeling: anxious"
  ├─ [7]  progress_context_block  ← ProgressContextBuilder.build_progress_context()
  │         "LONG-TERM CONTEXT: recurring topics, concerns, emotional trend"
  ├─ [8]  verbosity_instruction   ← UserPersonalization.get_parameter(response_length)
  ├─ [9]  emotional_instruction   ← UserIntelligence.analyze_emotional_journey()
  └─ [10] need_instruction        ← ResponseNeedClassifier.get_instruction()
            "User needs: action_plan → provide structured steps"
       │
       ▼
AI Model (OpenAI / Claude / Gemini / Grok / Meta)
  │   (adapts to explicit context, history, verbosity, emotion, need type)
  ▼
Response received
       │
       ▼
character_routes.py — POST-PROCESSING
  ├─ [11] CharacterSuggester.suggest()
  │         → append character_suggestion to response metadata
  │         → append detected_need to response metadata
  ├─ [12] DualLayerHistorySystem.store_interaction() + analyze_and_store_secondary()
  │         → populates analytical history for future ProgressContextBuilder calls
  ├─ [13] UserPersonalization.process_signals_and_adapt()
  │         → update stored verbosity preference from accumulated signals
  └─ [14] return jsonify(response)
               {response, session_id, detected_need?, character_suggestion?}
       │
       ▼
conversation_box.js — RENDERING
  ├─ [15a] type === 'clarification' → _addClarificationCard() (styled question card)
  ├─ [15b] normal response → MessageHandler.addMessage()
  │          + _addResponseActions() (Tell me more / Not what I meant / Too long / Too short)
  └─ [15c] character_suggestion present → _addCharacterSuggestion() (amber nudge bar)
```

**New API endpoints added:**
- `GET /api/user/personalization-profile` — verbosity prefs, emotional journey, communication style
- `GET /api/user/progress-summary` — long-term topic/concern trends from dual-layer history
- `GET /ask` (enhanced) — now returns `comparison_metrics` and `rankings` per model response

---

### 16. Character Effectiveness Tracking — Feedback Loop Closed
**Endpoint:** `POST /api/user/character-switch`  
**Frontend:** `static/conversation_box.js` — `_handleCharacterSwitch()` upgraded  
**Status:** Implemented & Tested

**What it does:**  
When a user clicks the character suggestion link in the amber nudge bar, a fire-and-forget signal is sent to the backend recording which character was switched to, which need type triggered the suggestion, and which character was left. This builds up effectiveness data via `UserIntelligence.record_engagement()` with `signal_type='character_switch'`.

**Why it matters:**  
The `CharacterSuggester` currently uses static priority mappings. With enough `character_switch` signals, the effectiveness of each need→character pairing can be quantified from real user behaviour rather than assumptions.

**Signal structure:**
```json
{ "from_character": "marcus", "to_character": "psychologist", "detected_need": "sympathy", "suggestion_used": true }
```

---

### 17. Pre-Processing Parity — Both Paths
**Wired in:** `ai_compare/character_routes.py`  
**Status:** ✅ Implemented

Moved explicit context extraction, verbosity signal recording, and proactive clarification checks to run **unconditionally** — before the `if smart_response_processor:` fork. Previously these only ran on the smart-response path; the direct AI fallback path received none of the personalization pre-processing.

---

### 18. Explicit Context Expiry
**Wired in:** `ai_compare/character_routes.py` post-processing  
**Module:** `smart_response/explicit_context_handler.py` — `expire_old_context()`  
**Status:** ✅ Implemented

`expire_old_context()` now runs after every response, enforcing type-specific TTLs:
- `emotional_state` → expires after 24 hours
- `intention` → 48 hours
- `goal` → 168 hours (1 week)
- `preference` → 720 hours (30 days)
- `value` → 8,760 hours (1 year)

Prevents stale context (e.g., "I'm anxious" from 3 months ago) from polluting current prompts.

---

### 19. CharacterSuggester Live Effectiveness Weighting
**Module:** `smart_response/character_suggester.py` — `get_effectiveness_scores()` + `_suggest_safe()` upgrade  
**Status:** ✅ Implemented & Tested

Added `get_effectiveness_scores(primary_need)` that queries `character_switch` engagement signals from `user_engagement_signals` to build a live frequency distribution. When ≥ 3 signals exist for a need type, this data **re-ranks** the static candidate list — characters users have actually switched to for this need move to the front.

Fallback: static ordering when no live data available (new deployments, new need types).

---

### 20. Personalization Status Indicator
**Frontend:** `static/conversation_box.js` — `_loadPersonalizationStatus()` + `_renderPersonalizationStatus()`  
**Endpoint:** `GET /api/user/personalization-profile` (extended)  
**Status:** ✅ Implemented & Tested

Up to 4 small chips rendered below the chat input on page load, showing the user what the AI currently knows about them:

| Chip | Colour | Shows |
|---|---|---|
| ⚡ concise / 📄 detailed | Amber | Verbosity preference |
| 😔 anxious | Red | Latest active emotional state |
| 🎯 get promoted | Green | Active goal from explicit context |
| ✦ action_plan | Blue | Most recent detected need type |

Chips are silent when empty (new users). They update on each page load by calling `/api/user/personalization-profile`. The endpoint was extended to return `verbosity.response_length`, `emotional_state`, `active_goal`, and `current_need`.

---

### 21. Proactive Goal Check-In
**Module:** `smart_response/goal_checkin_builder.py` — `GoalCheckInBuilder`  
**Wired into:** `ai_compare/chatbot.py`, `ai_compare/base_chatbot.py`  
**Status:** ✅ Implemented & Tested

When all conditions are true, injects a `GOAL CHECK-IN` hint block into the AI prompt:
- User has an active `goal` or `intention` in explicit context
- The item was set ≥ 7 days ago
- The user hasn't mentioned it in the last 5 days of messages
- The user has ≥ 3 sessions (not brand-new)

The hint text reads:
```
GOAL CHECK-IN:
This user set a goal 15 days ago: "get promoted"
They haven't mentioned it recently. If the conversation allows it naturally,
gently ask how it's going or acknowledge their progress.
(Don't force it — only reference if genuinely relevant to what they're saying now.)
```

The AI decides whether to use it — it is never forced. This creates organic follow-through on user goals across sessions without being intrusive.

---

### 22. Session Engagement Tracker
**Module:** `smart_response/session_engagement_tracker.py` — `SessionEngagementTracker`  
**Wired into:** `ai_compare/chatbot.py`, `ai_compare/base_chatbot.py`  
**Status:** ✅ Implemented & Tested

Two complementary behaviours per request:

**RE-ENGAGEMENT block** — when the user hasn't been seen for ≥ 7 days, injects:
```
RE-ENGAGEMENT NOTE:
This user is returning after a 10-day absence.
  - Last discussed: help me think through my career
Consider briefly acknowledging their return and checking in on any ongoing goals...
```

**Auto verbosity signal** — measures average word count over the last 10 messages:
- avg < 12 words → records `brief` signal into `UserPersonalization`
- avg > 60 words → records `detailed` signal
- Between these thresholds → no signal (balanced)

This closes the gap where users who habitually write very short messages never explicitly say "be brief" — the system infers it from behaviour.

---

### 23. Frustration Detector
**Module:** `smart_response/frustration_detector.py` — `FrustrationDetector`  
**Wired into:** `ai_compare/chatbot.py`, `ai_compare/base_chatbot.py`  
**Status:** ✅ Implemented & Tested

Detects two frustration signals per request:

1. **Correction phrases** — explicit correction language in the current message (e.g., "no that's wrong", "you don't understand me", "not what I asked", "still not", "try again")
2. **Repeated topic** — ≥3 of the last 4 user messages have Jaccard similarity ≥ 0.40 with the current message, indicating the AI hasn't resolved their need

When fired, injects a `FRUSTRATION DETECTED` block:
```
FRUSTRATION DETECTED:
The user is explicitly correcting your previous response — they feel misunderstood.
Do NOT repeat the same type of answer. Instead:
  1. Briefly acknowledge that you may have missed what they needed.
  2. Ask ONE specific clarifying question to make sure you understand.
  3. Try a completely different angle if you re-answer.
```

Silent for all normal messages (no block injected).

---

### 24. Milestone Detector
**Module:** `smart_response/milestone_detector.py` — `MilestoneDetector`  
**Wired into:** `ai_compare/chatbot.py`, `ai_compare/base_chatbot.py`  
**Status:** Implemented & Tested

Fires when the current message contains an achievement phrase ("I got", "I finally", "I landed", "I passed", "we launched", etc.) AND key words from an active stored goal appear in the message.

On detection:
1. Injects `MILESTONE ACHIEVED` block so the AI celebrates naturally
2. Marks the achieved goal as `active=0` in `explicit_context` (won't appear in future prompts or check-in hints)

Example trigger: user has goal `get promoted`, sends `"I finally got promoted today!"` → block fires, goal deactivated.

Silent for normal messages — no false positives without both conditions.

---

### 25. Adaptive Tone Calibration
**Module:** `smart_response/tone_calibrator.py` — `ToneCalibrator`  
**Wired into:** `ai_compare/chatbot.py`, `ai_compare/base_chatbot.py`  
**Status:** ✅ Implemented & Tested

Measures the ratio of casual vs formal markers across the last 10 user messages and injects a tone instruction:

| Detection | Ratio | Instruction |
|---|---|---|
| Casual | ≥ 0.65 casual share | "Match their energy — be conversational, warm, direct" |
| Formal | ≤ 0.25 casual share | "Match their register — be precise, structured, professional" |
| Neutral | between | '' (no instruction injected) |

**Casual signals:** slang (lol, btw, ngl, gonna, idk), contractions (i'm, can't, didn't), emoji — checked with word-boundary matching to avoid false positives (e.g. "ugh" inside "through").

**Formal signals:** vocabulary like "furthermore", "pursuant", "aforementioned", "accordingly", multi-word phrases like "with respect to", "could you please".

Returns '' when insufficient data (< 4 messages) or no strong signal.

---

### 26. Format Preference Detector
**Module:** `smart_response/format_preference_detector.py` — `FormatPreferenceDetector`  
**Wired into:** `smart_response/personalization_pipeline.py` → both chatbots  
**Status:** ✅ Implemented & Tested

Detects user preference for answer formatting from the current message and injects a compact format instruction:

| Format | Trigger examples | Instruction injected |
|---|---|---|
| Bullets | "give me a list", "key points", "what are the" | "Use clear, concise bullets. No long paragraphs." |
| Steps | "step by step", "walk me through", "how do I" | "Present your answer as an ordered step-by-step sequence." |
| Prose | "just explain", "summarize", "tldr", "in plain english" | "Skip lists — explain in plain, flowing sentences." |

Requires a clear winner (no ties); returns '' on neutral messages or ambiguous overlap. No DB query — analysis runs on the current message only.

---

### 27. Cross-Character Explicit Context Carryover
**Module:** `smart_response/explicit_context_handler.py` — `get_cross_character_context()`  
**Status:** ✅ Implemented & Tested

Previously, CRITICAL/HIGH explicit context (goals, preferences) stored while talking to one AI character was invisible when switching to another character. Fixed by:

- `get_cross_character_context(user_id, character_id)` retrieves active CRITICAL/HIGH context from **all other characters** for the same user.
- `format_for_ai_prompt()` merges cross-character context, deduplicating by value so nothing is repeated.

Result: A goal set with the Coach carries over seamlessly when the user switches to the Psychologist or Sage.

---

### 28. PersonalizationPipeline — Shared Module (Zero Redundancy)
**Module:** `smart_response/personalization_pipeline.py` — `build_personalization()`  
**Wired into:** `ai_compare/chatbot.py`, `ai_compare/base_chatbot.py`  
**Status:** ✅ Implemented & Tested

Previously every personalization module was copy-pasted as ~100 lines of independent `try/except` blocks in both `chatbot.py` AND `base_chatbot.py` — a direct violation of DRY with high maintenance risk.

**What was done:**
- Created `PersonalizationResult` dataclass with 11 named fields (all string, all `''` by default).
- `build_personalization(user_message, user_id, character_id, db_path)` runs all 11 modules in one call:
  1. `UserPersonalization` → `verbosity_instruction`
  2. `ExplicitContextHandler` → `explicit_context_block`
  3. `build_progress_context` → `progress_context_block`
  4. `GoalCheckInBuilder` → `goal_checkin_block`
  5. `SessionEngagementTracker` → `engagement_block`
  6. `FrustrationDetector` → `frustration_block`
  7. `MilestoneDetector` → `milestone_block`
  8. `FormatPreferenceDetector` → `format_instruction`
  9. `ToneCalibrator` → `tone_instruction`
  10. `get_need_classifier` → `need_instruction`
  11. `user_intelligence` → `emotional_instruction`
- Every module is isolated in its own `try/except` — one failure never blocks another.
- Both `chatbot.py` and `base_chatbot.py` now replace their ~100-line blocks with a single `build_personalization()` call.

**Answers user question:** Yes — all personalization features apply equally to both the domain/character chatbot path (`chatbot.py`) and the AI-compare fallback path (`base_chatbot.py`). They share 100% of the logic through this single pipeline.

---

---

### 29. `/api/user/conversation-summary` Endpoint
**File:** `app.py`  
**Status:** ✅ Implemented & Tested

Returns a concise high-level summary of a user's conversation activity across all AI characters:

| Field | Source | Description |
|---|---|---|
| `total_messages` | `character_messages` | Total user messages across all characters |
| `characters_used` | `character_messages` | `{character_id: count}` map |
| `most_active_character` | `character_messages` | Character with highest message count |
| `first_interaction` | `character_messages` | ISO timestamp of earliest user message |
| `last_interaction` | `character_messages` | ISO timestamp of most recent user message |
| `active_goals` | `explicit_context` | Up to 5 active CRITICAL/HIGH goals |
| `recent_topics` | `history_secondary` | Up to 5 recent topics from analytical history layer |
| `emotional_state` | `explicit_context` | Most recent stored emotional state string |

- Requires `@require_auth`  
- Each sub-query is individually wrapped in `try/except` — one missing table never breaks the whole response  
- Returns `{'success': True, 'summary': {...}}`

---

## Test Count

**278 / 278 tests passing** (`tests/test_web_enhancements.py`)

New test classes added this session:
- `TestPersonalizationPipeline` (11 tests) — pipeline import, return types, error isolation, format/steps/neutral detection, both chatbots wired, all 11 modules present
- `TestConversationSummaryEndpoint` (11 tests) — route defined, auth required, all response fields present, correct DB tables queried, ≥4 `except Exception` blocks, `success` key returned

---

## Known Remaining Items

| Item | Priority | Notes |
|---|---|---|
| Session cleanup for MetaModel/GrokModel | Low | `close()` added but needs app teardown hook |
| Pattern expander AI calls | Low | `pattern_expander.py` exists but unused — wait until budget allows |
