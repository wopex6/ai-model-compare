*Last updated: 2025-12-25 19:17:41*

# AI System Regeneration Specification

**Purpose:** This document enables another AI system to understand and regenerate the Life Companion system from scratch.

---

## 1. System Overview

**Life Companion** is a multi-domain AI advisory system that provides personalized guidance across all areas of life through specialized AI characters.

### Core Concept
- One coordinator (Aria) routes messages to domain-specific advisors
- 7 domain characters with distinct personalities and expertise
- Personality-aware responses based on user assessments and inferred traits
- Continuous learning from conversation patterns

### Technology Stack
- **Backend:** Python/Flask
- **Database:** SQLite (integrated_users.db)
- **AI Providers:** OpenAI, Anthropic, Google, Grok (with fallback)
- **Frontend:** HTML/CSS/JavaScript (vanilla + modern UI)

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Dashboard   │  │Life Companion│  │  Profile    │             │
│  │             │  │(domain_chars)│  │ Assessment  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND (app.py)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Auth System │  │ AI Router   │  │ API Endpoints│             │
│  │ (JWT)       │  │             │  │              │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SMART RESPONSE SYSTEM                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │UserContextMgr   │  │PersonalityIntegr│  │ TraitInference  │ │
│  │(facts,goals)    │  │(Big5→prompts)   │  │(conversation→   │ │
│  │                 │  │                 │  │ traits)         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │DualLayerHistory │  │ AIBudgetManager │  │ CharacterTraits │ │
│  │(raw+analytical) │  │(100 calls/day)  │  │(12D trait-space)│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN CHARACTER SYSTEM                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Aria (Coordinator) - Routes to specialists                 ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ Work Advisor      │ Relationship Guide │ Mind Wellness     ││
│  │ Body Advisor      │ Finance Guide      │ Learning Mentor   ││
│  │ Creative Muse     │                    │                   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DATABASE                                 │
│  integrated_users.db                                            │
│  ├── users, user_profiles (authentication, personal info)      │
│  ├── ai_conversations, messages (per-character sessions)       │
│  ├── assessment_history (Big 5 personality tests)              │
│  ├── inferred_personality (traits from conversations)          │
│  ├── history_primary/secondary (dual-layer analytics)          │
│  └── ai_usage_log, ai_budget_notifications (cost control)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Files

### Backend Core
| File | Purpose |
|------|---------|
| `app.py` | Main Flask app, all routes, initialization |
| `integrated_database.py` | Database operations, user/message management |
| `domain_character_manager.py` | Character definitions, message routing |
| `domain_character_ai.py` | AI response generation for domain characters |

### Smart Response System (`smart_response/`)
| File | Purpose |
|------|---------|
| `personality_context_integrator.py` | Connects Big5 + profile → AI prompts |
| `trait_inference.py` | Infers personality from conversation patterns |
| `user_context_manager.py` | Extracts facts, goals, language patterns |
| `dual_layer_history.py` | Raw + analytical conversation storage |
| `ai_budget_manager.py` | 100 calls/day limit, cost control |
| `character_traits.py` | 12-dimensional trait-space matching |

### Frontend
| File | Purpose |
|------|---------|
| `templates/life-companion.html` | Main Life Companion UI |
| `static/domain_characters.js` | Character selection, message routing |
| `static/message_handler.js` | Message display, DOM manipulation |
| `static/auth_helper.js` | JWT authentication for API calls |

---

## 4. Domain Characters

### Coordinator: Aria
- **Role:** Routes messages to appropriate domain specialists
- **Behavior:** Sees bigger picture, delegates to experts
- **ID:** `coordinator`

### Domain Specialists

| Character | Domain | Expertise |
|-----------|--------|-----------|
| Work Advisor | `domain_work` | Career, productivity, workplace |
| Relationship Guide | `domain_relationships` | Personal relationships, communication |
| Mind Wellness | `domain_mental_health` | Mental health, stress, emotions |
| Body Advisor | `domain_physical_health` | Fitness, nutrition, sleep |
| Finance Guide | `domain_finance` | Money, budgeting, investments |
| Learning Mentor | `domain_learning` | Education, skill development |
| Creative Muse | `domain_creativity` | Art, creative projects, inspiration |

---

## 5. Personality Integration System

### Data Sources (Priority Order)
1. **Assessment (highest):** Formal Big 5 test in `assessment_history`
2. **Inferred:** Analyzed from conversations in `inferred_personality`
3. **Default:** Neutral 0.5 values if no data

### Big 5 Traits
- **Openness:** Creativity, curiosity (0-1)
- **Conscientiousness:** Organization, discipline (0-1)
- **Extraversion:** Social energy (0-1)
- **Agreeableness:** Cooperation, empathy (0-1)
- **Neuroticism:** Emotional sensitivity (0-1)

### Adaptive Thresholds
Thresholds adjust based on:
- **Emotional intensity** of message
- **Topic sensitivity** (personal, health, relationships)
- **Goal relevance** (planning, achieving)
- **Data recency** (newer = higher weight)
- **Data confidence** (assessment > inferred > default)

### Integration Flow
```
User message → Analyze conversation state → Get personality context
     → Compute adaptive thresholds → Format for AI prompt
     → AI generates response → Save to history → Run trait inference
```

---

## 6. Message Routing

### Coordinator to Domain
1. User sends message to Aria (coordinator)
2. Message analyzed for domain relevance
3. Routed to 1+ domain characters
4. User message saved to BOTH coordinator AND domain character histories
5. Responses saved with `[Character Name]` attribution in coordinator view

### Direct to Domain
1. User clicks specific domain character
2. Message sent directly to that character
3. Saved only to that character's history

---

## 7. Database Schema (Key Tables)

### users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    role TEXT DEFAULT 'guest',  -- guest, paid, master, administrator
    created_at DATETIME
);
```

### ai_conversations
```sql
CREATE TABLE ai_conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    session_id TEXT UNIQUE,
    character_id TEXT,  -- 'coordinator', 'domain_work', etc.
    title TEXT,
    created_at DATETIME,
    updated_at DATETIME
);
```

### messages
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER,
    sender_type TEXT,  -- 'user' or 'assistant'
    content TEXT,
    metadata TEXT,
    timestamp DATETIME
);
```

### assessment_history
```sql
CREATE TABLE assessment_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    openness REAL, conscientiousness REAL, extraversion REAL,
    agreeableness REAL, neuroticism REAL,
    completed_at DATETIME
);
```

### inferred_personality
```sql
CREATE TABLE inferred_personality (
    user_id INTEGER PRIMARY KEY,
    openness REAL, conscientiousness REAL, extraversion REAL,
    agreeableness REAL, neuroticism REAL,
    confidence REAL,
    last_updated DATETIME
);
```

---

## 8. API Endpoints (Key)

### Authentication
- `POST /api/auth/login` - Login, returns JWT
- `POST /api/auth/register` - Create account
- `GET /api/user/profile` - Get user profile

### Life Companion
- `POST /api/domain-characters/route` - Send message, get responses
- `GET /api/domain-characters/history/<character_id>` - Get chat history
- `GET /api/domain-characters` - List all characters

### Profile & Assessment
- `POST /api/psychological-assessment` - Save Big 5 test results
- `PUT /api/user/comprehensive-profile/preferences` - Update goals/interests

---

## 9. Cost Control (AI Budget)

- **Daily limit:** 100 AI calls for users, 1000 for admins
- **Notifications:** At 80% and 100% usage
- **Circuit breaker:** Auto-shutdown on unusual patterns
- **Logging:** All calls tracked in `ai_usage_log`

---

## 10. Recent Changes (Dec 18, 2025)

### Personality Context Integrator
- **File:** `smart_response/personality_context_integrator.py`
- Connects Big 5 assessment + profile → AI prompts
- Adaptive thresholds based on conversation state
- Auto-invalidates cache when data changes

### Routed Message History Fix
- User messages routed from coordinator now saved to domain character histories
- Migration script: `migrate_routed_messages.py`
- Ensures questions appear in domain character view

### Database Backup System
- **File:** `database_backup.py`
- Auto-discovers all .db files
- 30 backup rotation, 4-hour intervals
- Admin dashboard: `/admin/backup-manager`

---

## 11. Regeneration Instructions

To regenerate this system:

1. **Create Flask app** with JWT authentication
2. **Set up SQLite database** with schema above
3. **Implement domain characters** with routing logic
4. **Add personality integration** with Big 5 + adaptive thresholds
5. **Implement dual-layer history** for analytics
6. **Add AI budget manager** for cost control
7. **Create frontend** with character selection and chat UI
8. **Wire everything together** in app.py

### Key Design Principles
- User's explicit statements = absolute truth (override inference)
- Personality can change over time - detect and adapt
- Ask clarifying questions when uncertain (confidence < 60%)
- Raw history is immutable; analytical layer can evolve
- Prime goal: Inspire and guide users to act constructively

---

## 12. Related Documentation

- `PERSONALITY_INTEGRATION.md` - Detailed personality system docs
- `INTELLIGENT_CONTEXT_ARCHITECTURE.md` - Context system design
- `CHARACTER_SPECTRUM_SYSTEM.md` - Character trait-space system
- `SYSTEM_DESIGN_PRINCIPLES.md` - Core design principles
- `ARCHITECTURE_OVERVIEW.md` - System architecture
