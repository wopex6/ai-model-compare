# AI Life Companion - Complete System Specification

*Last updated: 2025-12-28 22:01:09*


*Last updated: 2025-12-28*  
*Version: 2.0*  
*Status: COMPREHENSIVE*

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Domain Characters](#3-domain-characters)
4. [AI Response System](#4-ai-response-system)
5. [Personality Integration](#5-personality-integration)
6. [Goal Coaching System](#6-goal-coaching-system)
7. [AI Budget & Cost Control](#7-ai-budget--cost-control)
8. [Database Schema](#8-database-schema)
9. [API Endpoints](#9-api-endpoints)
10. [Frontend Architecture](#10-frontend-architecture)
11. [Automated Systems](#11-automated-systems)
12. [Security & Authentication](#12-security--authentication)
13. [Deployment](#13-deployment)
14. [Regeneration Instructions](#14-regeneration-instructions)
15. [Changelog](#15-changelog)

---

## 1. System Overview

### Purpose
AI Life Companion is a multi-character AI coaching system that provides personalized guidance across life domains. It uses personality-aware context interpretation to deliver meaningful, constructive support.

### Core Philosophy
> **"Context is not just data - it's interpretation through the lens of who the user is."**

The same event means different things to different people. This system doesn't just recall context - it **interprets** it intelligently to provide **long-term constructive guidance**.

### Key Features
- **Multi-domain coaching** via specialized AI characters
- **Personality-aware responses** using Big 5 assessment
- **Invisible goal coaching** that adapts to user psychology
- **Cost-controlled AI** with strict budget limits
- **Dual-layer history** for analytics and improvement

---

## 2. Architecture

### Tech Stack
| Component | Technology |
|-----------|------------|
| Backend | Flask (Python 3.9+) |
| Database | SQLite |
| AI Provider | OpenAI GPT-4 |
| Authentication | JWT tokens |
| Frontend | Vanilla JS + HTML templates |
| Hosting | PythonAnywhere |

### Key Files

#### Backend Core
| File | Purpose |
|------|---------|
| `app.py` | Main Flask app, all routes, initialization (~5200 lines) |
| `integrated_database.py` | Database operations, user/message management |
| `domain_character_manager.py` | Character definitions, message routing |
| `domain_character_ai.py` | AI response generation for domain characters |
| `goal_coaching_system.py` | Invisible adaptive goal coaching |

#### Smart Response System (`smart_response/`)
| File | Purpose |
|------|---------|
| `personality_context_integrator.py` | Connects Big5 + profile → AI prompts |
| `trait_inference.py` | Infers personality from conversation patterns |
| `user_context_manager.py` | Extracts facts, goals, language patterns |
| `dual_layer_history.py` | Raw + analytical conversation storage |
| `ai_budget_manager.py` | 100 calls/day limit, cost control |
| `character_traits.py` | 12-dimensional trait-space matching |

#### Frontend
| File | Purpose |
|------|---------|
| `templates/life-companion.html` | Main Life Companion UI |
| `static/domain_characters.js` | Character selection, message routing |
| `static/message_handler.js` | Message display, DOM manipulation |
| `static/auth_helper.js` | JWT authentication for API calls |
| `static/greeting_handler.js` | Automated greeting display |

### Data Flow
```
User Message
    ↓
Authentication (JWT)
    ↓
AI Budget Check (100/day limit)
    ↓
Personality Context Loading
    ↓
Goal Coaching Context Injection
    ↓
Domain Character Routing
    ↓
AI Response Generation
    ↓
Dual-Layer History Storage
    ↓
Response Display
```

---

## 3. Domain Characters

### Coordinator: Aria
- **Role:** Routes messages to appropriate domain specialists
- **Behavior:** Sees bigger picture, delegates to experts
- **ID:** `coordinator`
- **Special:** Can invoke multiple specialists per message

### Domain Specialists

| Character | ID | Expertise |
|-----------|-----|-----------|
| Work Advisor | `domain_work` | Career, productivity, workplace |
| Relationship Guide | `domain_relationships` | Personal relationships, communication |
| Mind Wellness | `domain_mental_health` | Mental health, stress, emotions |
| Body Advisor | `domain_physical_health` | Fitness, nutrition, sleep |
| Finance Guide | `domain_finance` | Money, budgeting, investments |
| Learning Mentor | `domain_learning` | Education, skill development |
| Creative Muse | `domain_creativity` | Art, creative projects, inspiration |

### Character Trait System (12 Dimensions)
Each character exists in a 12-dimensional trait-space:
- **stoicism** (0-1): Emotional detachment
- **optimism** (0-1): Positive outlook
- **directness** (0-1): Communication style
- **supportiveness** (0-1): Empathy level
- **structure** (0-1): Organization preference
- **depth** (0-1): Analysis depth
- **formality** (0-1): Language style
- **verbosity** (0-1): Response length
- **action_oriented** (0-1): Focus on action vs reflection
- **present_focus** (0-1): Here-now vs future planning
- **empathy** (0-1): Emotional attunement
- **intensity** (0-1): Energy level

### Message Routing Logic
1. **Coordinator View:** Message analyzed → routed to 1+ specialists
2. **Direct View:** Message sent directly to selected character
3. **History:** User messages saved to BOTH coordinator AND responding character

---

## 4. AI Response System

### Response Generation Flow
```python
def generate_response(user_id, message, character_id):
    # 1. Check AI budget
    allowed, reason = ai_budget.can_make_ai_call(user_id)
    if not allowed:
        return fallback_response(reason)
    
    # 2. Build context
    context = {
        'personality': get_personality_context(user_id),
        'coaching': get_coaching_context(user_id, message),
        'history': get_recent_history(user_id, character_id),
        'user_profile': get_user_profile(user_id)
    }
    
    # 3. Build system prompt
    system_prompt = build_character_prompt(character_id, context)
    
    # 4. Call AI
    response = openai_call(system_prompt, message)
    
    # 5. Log and save
    ai_budget.log_call(user_id, character_id)
    save_to_history(user_id, character_id, message, response)
    
    return response
```

### Smart Response (Quick Replies)
- Pattern-based responses for common queries
- No AI call required (cost: $0)
- Falls back to AI when patterns don't match

### AI Context Injection
Each AI call includes:
1. **Character personality** - traits, expertise, communication style
2. **User personality** - Big 5 scores, preferences
3. **Active goals** - current coaching context
4. **Conversation history** - recent exchanges
5. **User profile** - interests, background, constraints

---

## 5. Personality Integration

### Data Sources (Priority Order)
1. **Assessment (highest):** Formal Big 5 test in `assessment_history`
2. **Inferred:** Analyzed from conversations in `inferred_personality`
3. **Default:** Neutral 0.5 values if no data

### Big 5 Traits (OCEAN)
| Trait | Description | Range |
|-------|-------------|-------|
| Openness | Creativity, curiosity | 0-1 |
| Conscientiousness | Organization, discipline | 0-1 |
| Extraversion | Social energy | 0-1 |
| Agreeableness | Cooperation, empathy | 0-1 |
| Neuroticism | Emotional sensitivity | 0-1 |

### Adaptive Thresholds
Thresholds adjust based on:
- **Emotional intensity** of message
- **Topic sensitivity** (personal, health, relationships)
- **Goal relevance** (planning, achieving)
- **Data recency** (newer = higher weight)
- **Data confidence** (assessment > inferred > default)

### Integration Flow
```
User message 
    → Analyze conversation state 
    → Get personality context
    → Compute adaptive thresholds 
    → Format for AI prompt
    → AI generates response 
    → Save to history 
    → Run trait inference
```

### Personality Context Format (for AI)
```
USER PERSONALITY CONTEXT:
- Openness: 0.72 (creative, curious)
- Conscientiousness: 0.85 (organized, disciplined)
- Extraversion: 0.45 (balanced introvert/extrovert)
- Agreeableness: 0.68 (cooperative, empathetic)
- Neuroticism: 0.35 (emotionally stable)

ADAPT YOUR RESPONSE:
- User appreciates structured, organized advice
- Can handle direct feedback
- Values practical, actionable guidance
```

---

## 6. Goal Coaching System

### Philosophy
> **"Invisible coaching that feels like helpful conversation, not formal coaching."**

See `GOAL_COACHING_PHILOSOPHY.md` for detailed principles.

### Key Principles
1. **Invisible Strategy:** User experiences natural conversation
2. **Psychology Detection:** Adapt to user's current state
3. **Specific Actions:** Always provide immediate, actionable steps
4. **Engagement Focus:** Keep users moving forward

### User Psychology Detection
```python
def detect_user_state(message):
    signals = {
        'low_energy': ['tired', 'exhausted', 'no motivation'],
        'overwhelmed': ['too much', 'cant handle', 'stressed'],
        'stuck': ['dont know', 'confused', 'lost'],
        'motivated': ['ready', 'excited', 'lets do'],
        'frustrated': ['nothing works', 'gave up', 'pointless']
    }
    # Returns: energy_level, confidence, engagement
```

### Adaptive Response Strategies
| User State | Strategy |
|------------|----------|
| Low Energy | Smallest possible action, reduce overwhelm |
| Overwhelmed | Break down, prioritize one thing |
| Stuck | Offer specific options, remove decision paralysis |
| Motivated | Capitalize on momentum, add stretch goals |
| Frustrated | Validate feelings, find what DID work |

### Database Tables
- `user_goals` - Active goals (invisible to user)
- `goal_strategies` - AI-generated approach
- `goal_milestones` - Progress markers
- `goal_followups` - Scheduled check-ins
- `goal_coaching_sessions` - Conversation context

---

## 7. AI Budget & Cost Control

### Limits
| User Type | Daily Limit | Hourly Limit |
|-----------|-------------|--------------|
| Regular Users | 100 calls/day | 30 calls/hour |
| Administrators | 1000 calls/day | 30 calls/hour |
| System-Wide Cap | 2000 calls/day | - |

### Cost Analysis
- **Per call:** ~$0.002 (GPT-4)
- **User max:** $0.20/day = $6/month
- **System max:** $4/day = $120/month

### Protection Layers
1. **System Cap:** 2000 calls/day system-wide
2. **Per-User Limits:** 100/1000 based on role
3. **Hourly Throttle:** 30 calls/hour
4. **Rate Limiting:** 20 calls/minute
5. **Pattern Detection:** Spike, loop, error detection
6. **Circuit Breaker:** Emergency shutdown

### Notifications
- 80% usage → Warning
- 100% usage → Blocked + notification
- Circuit breaker → Admin alert

### Fallback Response
When budget exceeded:
```
"I've reached my daily limit for personalized responses. 
I can still help with quick questions! Your limit resets at midnight UTC."
```

---

## 8. Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'guest',  -- guest, paid, master, administrator
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### ai_conversations
```sql
CREATE TABLE ai_conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id TEXT UNIQUE,
    character_id TEXT,  -- 'coordinator', 'domain_work', etc.
    title TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### messages
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    sender_type TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON: source, is_automated_greeting, etc.
    reply_to_message_id INTEGER,  -- WhatsApp-style replies
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id)
);
```

### Personality Tables

#### assessment_history
```sql
CREATE TABLE assessment_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    openness REAL, conscientiousness REAL, extraversion REAL,
    agreeableness REAL, neuroticism REAL,
    question_responses TEXT,  -- JSON array of answers
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### inferred_personality
```sql
CREATE TABLE inferred_personality (
    user_id INTEGER PRIMARY KEY,
    openness REAL, conscientiousness REAL, extraversion REAL,
    agreeableness REAL, neuroticism REAL,
    confidence REAL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Goal Coaching Tables

#### user_goals
```sql
CREATE TABLE user_goals (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    goal_title TEXT NOT NULL,
    goal_description TEXT,
    status TEXT DEFAULT 'active',  -- active, paused, completed, abandoned
    priority INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### goal_strategies
```sql
CREATE TABLE goal_strategies (
    id INTEGER PRIMARY KEY,
    goal_id INTEGER NOT NULL,
    strategy_phase TEXT DEFAULT 'discovery',
    current_step INTEGER DEFAULT 1,
    next_action TEXT,
    next_question TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### AI Budget Tables

#### ai_usage_log
```sql
CREATE TABLE ai_usage_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    call_type TEXT,
    purpose TEXT,
    success INTEGER,
    error_message TEXT,
    tokens_used INTEGER,
    cost REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. API Endpoints

### Authentication
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/register` | Create account |
| GET | `/api/user/profile` | Get user profile |

### Life Companion
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/domain-characters/route` | Send message, get responses |
| GET | `/api/domain-characters/history/<character_id>` | Get chat history |
| GET | `/api/domain-characters` | List all characters |

### Profile & Assessment
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/psychological-assessment` | Save Big 5 test results |
| PUT | `/api/user/comprehensive-profile/preferences` | Update goals/interests |
| GET | `/api/user/comprehensive-profile` | Get full profile |

### Admin
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/admin/ai-usage-monitor` | AI usage dashboard |
| GET | `/api/ai-budget/status` | Current budget status |
| POST | `/api/ai-budget/reset-circuit-breaker` | Reset emergency shutdown |

### Greetings
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/greetings/pending` | Get pending greetings |
| POST | `/api/greetings/activity` | Record user activity |

### AI File Attachments
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/ai-attachments/upload` | Upload file with context description |
| GET | `/api/ai-attachments` | Get user's active attachments |
| DELETE | `/api/ai-attachments/<id>` | Remove attachment from AI context |

**Upload Parameters:**
- `file` - The file to upload
- `content_description` - What the file contains (required)
- `ai_instructions` - How AI should use it (optional)
- `character_id` - Associate with specific character (optional)

---

## 10. Frontend Architecture

### Page Structure
```
/                       → Landing page
/login                  → Login form
/register               → Registration form
/chatchat               → Admin multi-character view
/life-companion         → Main Life Companion interface
/profile                → User profile management
/assessment             → Big 5 personality test
```

### Key JavaScript Modules

#### MessageHandler (`message_handler.js`)
- Renders messages with timestamps
- Handles reply-to functionality
- Manages pinned messages and highlights
- Supports dark/light themes

#### DomainCharacters (`domain_characters.js`)
- Character selection UI
- Message routing to backend
- History loading per character
- Session expiry handling

#### AuthHelper (`auth_helper.js`)
- JWT token management
- Authenticated fetch wrapper
- Auto-redirect on 401

#### GreetingHandler (`greeting_handler.js`)
- Polls for pending greetings
- Displays automated messages
- Tracks user activity

### LocalStorage Keys
| Key | Purpose |
|-----|---------|
| `auth_token` | JWT authentication token |
| `showAiAnalysis` | AI analysis checkbox state |
| `theme_preference` | Dark/light mode |

---

## 11. Automated Systems

### Automated Greetings
- **Daily greetings:** Time-based welcome messages
- **Inactivity greetings:** Re-engagement after absence
- **AI context prompts:** Follow-up on previous topics

### Background Tasks
```python
# Scheduled every 6 hours
- Clean up old greetings (>24 hours)
- Process pending follow-ups
- Update inferred personality scores
```

### User Personalization
- **Adaptive parameters:** Response style adjusts over time
- **Interaction signals:** Tracks engagement patterns
- **Theme extraction:** Identifies recurring topics

---

## 12. Security & Authentication

### JWT Authentication
- **Token lifetime:** 7 days
- **Storage:** localStorage (client-side)
- **Refresh:** Re-login required after expiry

### Role-Based Access
| Role | Permissions |
|------|-------------|
| guest | Basic chat (limited) |
| paid | Full chat, all characters |
| master | Extended features |
| administrator | Full admin access, 1000 AI calls/day |

### Protected Routes
- All `/api/*` endpoints require valid JWT
- Admin routes require `administrator` role
- 401 response triggers login redirect

---

## 13. Deployment

### PythonAnywhere Setup
```bash
# Clone repository
git clone https://github.com/wopex6/ai-model-compare.git

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key

# Run migrations
python migrate_all_tables.py

# Configure WSGI
# Point to app.py
```

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key |
| `JWT_SECRET_KEY` | JWT signing key |
| `FLASK_SECRET_KEY` | Flask session key |

### Database Backup
- **Location:** `backups/`
- **Rotation:** 30 backups
- **Interval:** Every 4 hours
- **Admin:** `/admin/backup-manager`

---

## 14. Regeneration Instructions

To regenerate this system from scratch:

### Step 1: Core Setup
```bash
# Create Flask app with JWT authentication
pip install flask flask-cors pyjwt openai
```

### Step 2: Database
```bash
# Run migration script
python migrate_all_tables.py
```

### Step 3: Character System
1. Define characters in `domain_character_manager.py`
2. Implement routing logic
3. Create AI response generation

### Step 4: Personality Integration
1. Create Big 5 assessment UI
2. Implement `personality_context_integrator.py`
3. Add adaptive threshold computation

### Step 5: Goal Coaching
1. Create `goal_coaching_system.py`
2. Implement psychology detection
3. Add coaching context injection

### Step 6: AI Budget
1. Create `ai_budget_manager.py`
2. Wrap all AI calls with budget checks
3. Add notification system

### Step 7: Frontend
1. Create Life Companion template
2. Implement MessageHandler
3. Add DomainCharacters module
4. Wire up GreetingHandler

### Key Design Principles
- User's explicit statements = absolute truth (override inference)
- Personality can change over time - detect and adapt
- Ask clarifying questions when uncertain (confidence < 60%)
- Raw history is immutable; analytical layer can evolve
- Prime goal: Inspire and guide users to act constructively

---

## 15. Changelog

### December 2025

#### Dec 28, 2025
- **Added AI File Attachment feature** - users can upload files with context for AI processing
- Fixed session expiry handling (401 → login redirect)
- Fixed timestamp ordering in chat history
- Restored and expanded AI_REGENERATION_SPEC.md (715 lines)

#### Dec 27, 2025
- Added AI character analysis checkbox persistence
- Fixed backup_log.json git tracking issue

#### Dec 26, 2025
- Implemented Goal Coaching System
- Created GOAL_COACHING_PHILOSOPHY.md
- Updated migrate_all_tables.py for new tables

#### Dec 18, 2025
- Added Personality Context Integrator
- Fixed routed message history
- Implemented Database Backup System

#### Dec 3, 2025
- Activated AI Budget System
- Created AI Usage Monitor dashboard
- Implemented cost control limits

### November 2025

#### Nov 29, 2025
- Created Dual-Layer History System
- Designed Character Spectrum System
- Established System Design Principles

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `GOAL_COACHING_PHILOSOPHY.md` | Coaching system principles |
| `INTELLIGENT_CONTEXT_ARCHITECTURE.md` | Context interpretation design |
| `CHARACTER_SPECTRUM_SYSTEM.md` | Character trait-space system |
| `SYSTEM_DESIGN_PRINCIPLES.md` | Core design principles |
| `AI_BUDGET_ACTIVATED.md` | Budget system details |
| `AI_USAGE_MONITOR_README.md` | Usage dashboard guide |

---

*This document is maintained as the single source of truth for system architecture. Update it when making significant changes.*
