# AI Life Companion - System Changelog

> Comprehensive changelog for AI reference and system recreation
> 
> **Purpose:** Document all significant system changes for future AI understanding and potential system recreation.

---

## January 7, 2026

### Frontend UI Components (Session 2)

#### 1. Explicit Context UI (`static/explicit_context_ui.js`)
- Displays user's stated context (goals, preferences, values)
- Toggle via 🧠 button in chat header
- Groups by type with color-coded display
- Delete individual items
- Updates when switching characters

#### 2. Proactive Clarification UI (`static/proactive_clarification_ui.js`)
- Floating panel for clarifying questions
- Shows when system needs more context
- Click question to pre-fill input
- Dismissible per session

#### 3. AI Budget Notifications (`static/ai_budget_notifications.js`)
- Real-time budget warning notifications
- Auto-checks every 60 seconds
- Types: warning (80%), danger (100%), circuit breaker
- Acknowledge to dismiss permanently

#### 4. Admin Analytics Dashboard (`templates/admin_analytics.html`)
- Route: `/admin/analytics`
- Visual dashboard showing:
  - Total users, messages, AI calls
  - Budget usage meter (safe/warning/danger)
  - Background task status
  - Character effectiveness bars
  - Context type distribution
  - Recent AI calls table
- Auto-refreshes every 30 seconds

#### 5. Documentation Index (`DOCUMENTATION_INDEX.md`)
- Master index of 49+ documentation files
- Organized by category
- Quick reference for AI systems

### Auto-Generated API Documentation
- **File:** `app.py` (lines 6065-6186)
- **Feature:** Dynamic API self-documentation using Flask introspection
- **How it works:**
  - `_get_category_for_route()` - Maps URL prefixes to categories
  - `_get_category_description()` - Human-readable category descriptions
  - `api_documentation()` - Iterates `app.url_map.iter_rules()` to build docs
- **Key points:**
  - Pulls descriptions from function docstrings (first line)
  - Auto-categorizes by URL prefix
  - Never goes out of sync with actual routes
  - Endpoint: `GET /api`

### Frontend UI Data for Explicit Context
- **File:** `app.py` (lines 2058-2124)
- **Endpoint:** `GET /api/user/explicit-context/ui-data`
- **Purpose:** Frontend-friendly format for displaying user's explicit context
- **Returns:** Grouped context with labels, icons, colors, and help text

### Duplicate Function Fix
- Renamed `delete_explicit_context` → `delete_explicit_context_legacy` at line 3538
- Fixed Flask endpoint conflict between `/api/user/explicit-context/<id>` and `/api/explicit-context/<id>`

---

## Recent Major Features (Nov-Dec 2025)

### Smart Response System (`smart_response/` directory)

#### 1. AI Budget Manager (`ai_budget_manager.py`)
- **Hard limit:** 100 AI calls/day
- **Hourly limit:** 30 calls/hour
- **Rate limit:** 20 calls/minute
- **Features:**
  - Circuit breaker for emergencies
  - Pattern detection (spikes, loops, error cascades)
  - Notifications at 80% and 100% usage
  - Complete audit trail in database

#### 2. Character Trait System (`character_traits.py`)
- 12-dimensional trait vectors (0-1 continuous scale)
- **Traits:** stoicism, optimism, directness, supportiveness, structure, depth, formality, verbosity, action_oriented, present_focus, empathy, intensity
- Distance-based character matching using Euclidean distance
- Effectiveness weighting from historical outcomes

#### 3. Explicit Context Handler (`explicit_context_handler.py`)
- Extracts patterns like "I'm feeling X", "My goal is Y", "I prefer Z"
- Stores with CRITICAL priority (overrides all inference)
- Type-specific expiration times (emotional_state: 24h, goals: 30 days, etc.)
- Methods: `extract_context()`, `get_explicit_context()`, `format_for_ai_prompt()`, `expire_old_context()`

#### 4. Dual-Layer History (`dual_layer_history.py`)
- **Primary layer:** Immutable raw conversation data
- **Secondary layer:** Analytical interpretation (intent, emotions, topics, progress)
- Progress tracking for long-term trends
- Versioned for future re-analysis

#### 5. Background Scheduler (`background_scheduler.py`)
- Daily context maintenance (archival, expiration)
- Pattern expansion
- Character expansion (AI-powered, budget-controlled)
- Monthly cleanup

#### 6. Configuration Constants (`config.py`)
- Centralized thresholds and expiration times
- AI budget limits
- Scheduling times
- Replaces all magic numbers

### API Endpoints Summary

#### Authentication (`/api/auth/`)
- POST `/register`, `/login`, `/logout`
- GET `/me`
- POST `/verify-email`, `/resend-verification`, `/forgot-password`, `/reset-password`

#### User Management (`/api/user/`)
- GET/PUT `/profile`
- GET `/conversations`, DELETE `/conversations/<id>`
- GET/POST `/highlights`
- GET `/message-usage`

#### Explicit Context (`/api/user/explicit-context/`)
- GET `/` - List context items
- GET `/summary` - Formatted for AI prompt
- GET `/stats` - Statistics
- GET `/ui-data` - Frontend-friendly format
- DELETE `/<id>` - Remove item

#### Chat (`/chat/`)
- POST `/message`
- GET/POST `/sessions`
- GET/DELETE `/sessions/<id>`
- GET `/export`

#### Domain Characters (`/api/domain-characters/`)
- GET `/` - List all characters
- GET `/<id>` - Character details
- POST `/route` - Route message
- GET `/history/<id>` - Conversation history

#### Personality (`/api/personality/`)
- GET `/profile`, `/history`, `/trends/<trait>`, `/stats`
- POST `/assessment/start`

#### AI Budget (`/api/ai-budget/`)
- GET `/status`, `/notifications`
- POST `/notifications/acknowledge`, `/reset-circuit-breaker`

#### Admin (`/api/admin/`)
- GET `/users`, `/statistics`, `/smart-response-analytics`
- POST `/users/<id>/role`, `/users/<id>/permanent-delete`
- GET `/background-tasks/status`
- POST `/background-tasks/run`
- GET `/ai-errors`, `/ai-usage/summary`, `/patterns/suggestions`, `/backup/status`
- POST `/backup/run`

#### Developer (`/api/developer/`)
- GET `/metrics`, `/ai-calls`, `/user-context`, `/character-effectiveness`, `/debug`, `/health-history`
- POST `/query` (SQL)

---

## Database Tables

### Core Tables
- `users` - User accounts with roles (user, admin, developer)
- `conversations` - Chat sessions
- `messages` - Individual messages

### Smart Response Tables
- `explicit_context` - User-stated context (goals, preferences, values)
- `history_primary` - Raw conversation data (immutable)
- `history_secondary` - Analytical interpretation (evolving)
- `history_progress` - Long-term tracking
- `character_library` - Character trait vectors
- `character_usage_outcomes` - Learning data for effectiveness

### AI Budget Tables
- `ai_usage_log` - All AI calls with cost tracking
- `ai_usage_patterns` - Unusual activity detection
- `ai_budget_notifications` - User alerts

### Personality Tables
- `personality_assessments` - Assessment sessions
- `personality_responses` - Individual question responses
- `personality_profiles` - Computed trait scores

---

## Key Design Principles

1. **Explicit Context Priority** - User's explicit statements = absolute truth
2. **Personality-Aware Interpretation** - Same event means different things to different people
3. **Dual-Layer History** - Separate raw data from interpretation
4. **Cost Control** - Hard limits prevent runaway AI spending
5. **Outcome-Based Learning** - Track what works, improve over time
6. **Character Spectrum** - Characters as points in trait-space, not discrete entities

---

## File Structure

```
ai-model-compare/
├── app.py                          # Main Flask application (~6200 lines)
├── integrated_database.py          # Database operations
├── smart_response/
│   ├── __init__.py
│   ├── ai_budget_manager.py        # Cost control
│   ├── background_scheduler.py     # Scheduled tasks
│   ├── character_traits.py         # 12D character matching
│   ├── config.py                   # Centralized constants
│   ├── context_manager.py          # Context aggregation
│   ├── dual_layer_history.py       # Primary/secondary history
│   ├── explicit_context_handler.py # User-stated context
│   ├── pattern_manager.py          # Response patterns
│   └── personality_profiler.py     # Trait analysis
├── static/
│   ├── css/
│   └── js/
│       ├── components/
│       │   └── ConversationBox.js  # Unified chat UI
│       └── ...
├── templates/
└── *.md                            # Documentation files
```

---

## Deployment

- **Platform:** PythonAnywhere
- **URL:** https://trabcd.pythonanywhere.com
- **Deploy script:** `deploy_anywhere.py`
- **Auto-reload:** Disabled (use manual reload due to slow startup)

---

*This changelog is maintained for AI system understanding and potential recreation.*
