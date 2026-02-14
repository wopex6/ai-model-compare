# AI Agent Team Architecture

## Overview

A team of autonomous AI agents that manage, test, and evolve the system without requiring real users. The agents communicate via an Event Bus and are coordinated by an Orchestrator.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR                           │
│  Coordinates all agents, manages schedules & priorities  │
│  Plans: quick-test | light | default | intensive         │
└──────────┬──────────┬──────────┬──────────┬─────────────┘
           │          │          │          │
    ┌──────▼──┐ ┌─────▼────┐ ┌──▼──────┐ ┌▼───────────┐
    │ Simulated│ │  Health   │ │Character│ │  Event     │
    │  Users   │ │  Monitor  │ │Expansion│ │   Bus      │
    │ (5 agents│ │           │ │ System  │ │ (pub/sub)  │
    └──────────┘ └──────────┘ └─────────┘ └────────────┘
           │          │          │          │
           └──────────┴──────────┴──────────┘
                       │
              ┌────────▼────────┐
              │   Production    │
              │     System      │
              │ (PythonAnywhere)│
              └─────────────────┘
```

## Implemented Agents

### 1. Simulated User Agents (`agents/simulated_users.py`)
**Purpose:** Act like real users to generate conversation data through the full API pipeline.

**5 Personas:**
| Agent | Style | Topics | Msgs/Convo |
|-------|-------|--------|------------|
| Alex | Analytical | Career, financial, skill dev | 4-8 |
| Maya | Emotional | Grief, relationships, health | 5-10 |
| Jordan | Brief | Existential, creative, skill dev | 3-6 |
| Priya | Verbose | Existential, career, creative | 4-7 |
| Marcus | Guarded | Career, emotional, grief, health | 3-6 |

**Rate limit:** 20 msgs/agent/day (guest tier) = 100 msgs/day total

**Usage:**
```bash
# Single round, all agents
python agents/simulated_users.py --production

# 3 rounds with 2 agents
python agents/simulated_users.py --production --agents 2 --rounds 3

# Run for 30 minutes
python agents/simulated_users.py --production --duration 30
```

### 2. System Health Agent (`agents/system_health.py`)
**Purpose:** Monitor system health across multiple dimensions.

**Checks performed:**
- API responsiveness (latency, status codes)
- Chat endpoint functionality (optional, costs 1 AI call)
- Database integrity (table counts, size, recent activity)
- Character effectiveness trends (satisfaction scores, weak situations)
- AI budget consumption

**Usage:**
```bash
# Quick health check against production
python agents/system_health.py --production

# Include chat endpoint test
python agents/system_health.py --production --chat-test

# JSON output for automation
python agents/system_health.py --production --json
```

### 3. Agent Orchestrator (`agents/orchestrator.py`)
**Purpose:** Coordinate all agents on configurable schedules.

**Run Plans:**
| Plan | Agents | Convos/Cycle | Health Interval | Delay | Duration |
|------|--------|-------------|-----------------|-------|----------|
| quick-test | 2 | 1 | every cycle | 0 | single |
| light | 2 | 1 | every 5 cycles | 120s | 30 min |
| default | 3 | 1 | every cycle | 60s | 30 min |
| intensive | 5 | 1 | every 3 cycles | 30s | 60 min |
| health-only | 0 | 0 | every cycle | 300s | 60 min |

**Usage:**
```bash
# Quick test (1 cycle, 2 agents)
python agents/orchestrator.py --production --plan quick-test

# Default 30-min run
python agents/orchestrator.py --production --plan default

# Intensive 1-hour run
python agents/orchestrator.py --production --plan intensive --duration 60

# List all plans
python agents/orchestrator.py --list-plans
```

### 4. Event Bus (`agents/event_bus.py`)
**Purpose:** Decouple modules via publish/subscribe messaging.

**Standard Topics:**
- `conversation.completed` → triggers effectiveness learning
- `character.gap_detected` → triggers character expansion
- `user.inactive` → triggers re-engagement
- `health.critical` → triggers alerts
- `agent.rate_limited` → orchestrator switches agents

## Implemented Agents (continued)

### 5. Conversation Quality Scorer (`agents/quality_scorer.py`)
**Purpose:** Automatically grade conversations on multiple quality dimensions.

**Dimensions scored (0-1 scale):**
- Coherence (did the AI stay on topic?)
- Helpfulness (did it address the user's actual concern?)
- Engagement (did the conversation show depth?)
- Resolution (did the conversation reach a natural conclusion?)
- Consistency (did the AI stay in character?)

**Usage:**
```bash
python agents/quality_scorer.py --db smart_response.db --days 7
```

### 6. Quota Monitor (`agents/quota_monitor.py`)
**Purpose:** Monitor AI provider quotas, alert when credits run low.

Checks OpenAI, Anthropic, Google, and Grok provider health. Publishes `health.critical` events when quota errors are detected.

### 7. Alert Notifier (`agents/alert_notifier.py`)
**Purpose:** Send email/console alerts on critical Event Bus events.

**Features:**
- Subscribes to `health.critical`, `agent.error`, `quota.exceeded` events
- Email alerts via SMTP (using `email_service.py`)
- Cooldown to prevent alert spam (default 15 min per event type)
- Alert history for dashboard display
- CLI test mode

**Config:** `ADMIN_ALERT_EMAIL`, `EMAIL_SENDER`, `EMAIL_PASSWORD`, `SMTP_SERVER`, `SMTP_PORT`

### 8. Self-Improvement Agent (`agents/self_improvement.py`)
**Purpose:** Analyze quality scores and effectiveness data to auto-tune character configurations.

**Tunable parameters:**
- Character trait vectors (12-dimensional, max ±0.05 per cycle)
- System prompt addons (append learned guidelines)
- Style config (tone, response_length, emoji_usage)

**Safety:** All changes logged with before/after snapshots, minimum sample size required, dry-run mode for review.

**Usage:**
```bash
python agents/self_improvement.py --db smart_response.db --dry-run
python agents/self_improvement.py --db smart_response.db --apply
```

### 9. A/B Testing Agent (`agents/ab_testing.py`)
**Purpose:** Run controlled experiments on character configurations.

**Experiment types:**
- `prompt_variation` — Test different system prompt wordings
- `trait_adjustment` — Test different trait vector values
- `response_length` — Test concise vs detailed responses
- `collaboration_mode` — Test visible vs silent collaboration

**Pre-built experiments:** Empathy Boost, Response Length, Actionable Advice, Clarifying Questions

**Usage:**
```bash
python agents/ab_testing.py --create    # Create standard experiments
python agents/ab_testing.py --list      # List experiments
python agents/ab_testing.py --run ID    # Start an experiment
```

### 10. Admin Agent Dashboard (`templates/admin_agent_dashboard.html`)
**Purpose:** Real-time monitoring dashboard for all agent activity.

**Panels:** Provider health, budget usage ring, quality score bars, event bus stream, alert feed, sim user table, provider errors (24h).

**URL:** `/admin/agent-dashboard`

## Proposed Future Agents

### Documentation Agent (planned)
- Keeps README and architecture docs current
- Prunes stale .md files
- Generates API documentation from code
- Maintains changelog

## Architecture Enhancements Roadmap

### Phase 1: Foundation (DONE)
- [x] Simulated User Agents (5 personas, full API integration)
- [x] System Health Agent (API, DB, effectiveness, budget checks)
- [x] Agent Orchestrator (5 run plans)
- [x] Event Bus (pub/sub with wildcards, history, persistence)

### Phase 2: Integration (DONE)
- [x] Wire Event Bus into app.py endpoints (message.sent, health.critical, quota alerts)
- [x] Upgrade simulated users to 'paid' role for unlimited messaging
- [x] Email alerts on health.critical / quota exceeded events (AlertNotifier)
- [x] Admin Agent Dashboard (real-time monitoring UI)

### Phase 3: Intelligence (DONE)
- [x] Conversation Quality Scorer (6-dimension scoring)
- [x] Quota Monitor (provider health + budget tracking)
- [x] Self-Improvement Agent (auto-tune traits + prompts based on quality data)
- [x] A/B Testing Agent (controlled experiments on prompt/config variations)

### Phase 4: Scale
- [ ] Move from SQLite to PostgreSQL for concurrent agent access
- [ ] Add Redis for Event Bus persistence and pub/sub
- [ ] Containerize agents for independent scaling
- [ ] Documentation Agent for automated docs maintenance

## Key Design Decisions

1. **Agents use the real API** — not direct DB access. This exercises the full pipeline and catches integration bugs.
2. **Rate limits are respected** — agents don't bypass limits, ensuring realistic testing conditions.
3. **Event Bus is optional** — modules can adopt it incrementally; no big-bang migration needed.
4. **Plans are configurable** — from 1-minute quick tests to hour-long intensive runs.
5. **All agents are stateless between runs** — they can be started/stopped without data loss.
