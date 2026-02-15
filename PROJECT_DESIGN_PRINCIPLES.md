# Project Design Principles
## Quality Assurance Guidelines for Future Development

**Last Updated:** February 15, 2026  
**Scope:** All current and future development on this project  
**Purpose:** Codify the engineering principles that have guided this project, serving as a QA checklist and onboarding reference for any contributor (human or AI).

> **Related:** `SYSTEM_DESIGN_PRINCIPLES.md` covers domain-specific principles (personality-aware interpretation, proactive coaching, etc.). This document covers **engineering and architecture** principles.

---

## 1. Minimize Redundancy (DRY)

### Principle
> Every piece of knowledge or logic should have a single, authoritative source.

### How We Apply It
- **Shared pipeline:** `ConversationPipeline` runs the same 17-step enrichment for all characters — philosophy and domain — instead of duplicating logic per endpoint.
- **Reusable components:** `ConversationBox` (frontend) eliminated 900+ lines of duplicated chat UI across 8 character templates.
- **Centralized DB helper:** `get_db_conn()` in `app.py` applies WAL mode and busy timeout uniformly, replacing scattered `sqlite3.connect()` calls.
- **Config-driven characters:** All character behavior is defined in `configs.py` data structures, not in per-character code files.

### Checklist
- [ ] Is this logic already implemented elsewhere?
- [ ] Can this be extracted into a shared function, module, or component?
- [ ] If duplicating, is there a strong reason (e.g., intentional isolation)?

---

## 2. Graceful Degradation

### Principle
> The system always provides value, even when subsystems fail or data is incomplete.

### How We Apply It
- **Pipeline resilience:** Every step in `ConversationPipeline.enrich_context()` is wrapped in `try/except` with logging — one failing step never blocks the others.
- **Optional dependencies:** `ConversationPipeline.__init__(**kwargs)` accepts all systems as optional. Missing systems are silently skipped.
- **3-tier personality fallback:** Assessment data → Inferred from history → Neutral defaults.
- **Import guards:** `try: import X; except ImportError: X = None` pattern used throughout (e.g., `base.py` importing `admin_settings`).
- **Self-healing schemas:** `CREATE TABLE IF NOT EXISTS` ensures the app starts cleanly even on a fresh database.

### Checklist
- [ ] What happens if this dependency is unavailable?
- [ ] Does this fail silently with logging, or does it crash?
- [ ] Is there a meaningful fallback for the user?

---

## 3. Configuration-Driven Design (No Hard-Coding)

### Principle
> Behavior should be controlled by data and configuration, not by code branches.

### How We Apply It
- **Centralized thresholds:** `smart_response/config.py` holds all magic numbers — satisfaction scores, time thresholds, budget limits, trait distances, scheduler times.
- **Character configs:** `characters/configs.py` defines trait vectors, style, thresholds, and system prompts as dictionaries. Adding a new character = adding a dict entry, not writing a new class.
- **Knowledge profiles:** `knowledge_config.py` uses `CharacterKnowledgeProfile` dataclasses — fully metadata-driven, no hard-coded authors or fields.
- **Environment variables:** Database paths (`DB_PATH_INTEGRATED`, `DB_PATH_SMART_RESPONSE`), API keys, and deployment settings all externalized to `.env`.
- **Admin-configurable settings:** `admin_settings.py` allows runtime changes to thresholds via database, no redeployment needed.

### Checklist
- [ ] Are there any magic numbers in this code? Move them to `config.py`.
- [ ] Could this behavior change in the future? Make it configurable.
- [ ] Are environment-specific values (paths, keys, URLs) externalized?

---

## 4. Flexible & Extensible Architecture

### Principle
> New features, characters, or integrations should plug in without modifying existing code.

### How We Apply It
- **Abstract base classes:** `BaseCharacter` (ABC) defines the contract; `DomainCharacter` and `CoordinatorCharacter` extend it. New character types inherit, not copy.
- **Plugin-style pipeline:** Adding a new enrichment step to `ConversationPipeline` = adding one method + one call in `enrich_context()`. No existing logic changes.
- **Dynamic character registration:** `register_character_profile()` allows adding characters at runtime.
- **Event bus:** Decoupled event publishing — new listeners can subscribe without modifying publishers.
- **Background scheduler:** New tasks are added as schedule entries, not code rewrites.

### Checklist
- [ ] Can a new feature be added without modifying existing functions?
- [ ] Does this use inheritance/composition rather than conditionals?
- [ ] Is the extension point documented?

---

## 5. Comprehensive Automated Testing

### Principle
> Every feature phase has automated tests. Tests are the source of truth for "does it work?"

### How We Apply It
- **Per-phase test files:** `test_phase2_foundation.py`, `test_phase4_clarification.py`, `test_phase5_character_traits.py`, `test_phase6_context.py`, `test_phase65_collaboration.py`, `test_phase7_effectiveness.py`, `test_phase8_expansion.py` — each phase has dedicated tests.
- **Integration tests:** `test_agents_and_pipeline.py` (48 tests) validates the full pipeline.
- **E2E tests:** `test_e2e_pipeline_smoke.py`, `test_production.py` test against the live site.
- **Browser tests:** Playwright specs (`test_assessment.spec.js`) for UI flows.
- **Local + production split:** Local tests run in <10s; production tests hit the live PA site separately.
- **59+ local tests, 84+ total** across 20 test files.

### Checklist
- [ ] Does this new feature have a test file?
- [ ] Do tests cover: happy path, edge cases, failure/fallback modes?
- [ ] Can tests run locally without external dependencies (API keys, live servers)?
- [ ] Do existing tests still pass after this change?

---

## 6. Separation of Concerns

### Principle
> Each module has one clear responsibility. Modules communicate through well-defined interfaces.

### How We Apply It
- **40+ focused modules** in `smart_response/`: each handles one concern (personality, traits, collaboration, budget, context, clarification, etc.).
- **Frontend separation:** `conversation_box.js` (UI), `domain_characters.js` (character logic), `message_handler.js` (message formatting), `proactive_clarification_ui.js` (clarification UI).
- **Backend layers:** `app.py` (routes/orchestration) → `ConversationPipeline` (enrichment) → individual systems (personality, coaching, etc.) → database layer.
- **Characters vs. intelligence:** Character identity (`configs.py`, `base.py`) is separate from intelligence features (`user_intelligence.py`, `personality_interpreter.py`).

### Checklist
- [ ] Does this module do more than one thing?
- [ ] Could this be split into smaller, focused modules?
- [ ] Are dependencies between modules minimal and well-defined?

---

## 7. Cost Protection & Safety Guardrails

### Principle
> External API calls (especially AI) must have hard limits, monitoring, and emergency shutoffs.

### How We Apply It
- **AI Budget Manager:** Hard daily limits (100/user, 1000/admin, 2000/system), hourly limits, per-minute rate limits.
- **Circuit breaker:** Automatic shutoff on unusual patterns or cap breach. Requires manual reset.
- **Notification system:** Warns at 80% usage, stops at 100%. Stored in database for audit trail.
- **Background task limits:** Separate 10-call/day budget for background AI tasks.
- **Complete audit trail:** Every AI call logged with timestamp, purpose, cost, tokens, success/failure.
- **Maximum cost guarantee:** $6/month ceiling enforced by architecture, not just policy.

### Checklist
- [ ] Does this feature make external API calls? If so, is it wrapped by the budget manager?
- [ ] What happens if this runs away (infinite loop, rapid retries)?
- [ ] Is there a hard upper bound on cost/calls?
- [ ] Are failures logged for audit?

---

## 8. Idempotent & Self-Healing Operations

### Principle
> Operations should be safe to run multiple times. The system should recover from partial failures automatically.

### How We Apply It
- **Schema creation:** `CREATE TABLE IF NOT EXISTS` used across all database initialization — safe on first run, restart, or migration.
- **Upsert patterns:** `INSERT OR REPLACE` for settings and configurations.
- **Environment defaults:** `os.environ.setdefault()` for gRPC verbosity and other settings — safe if already set.
- **Import guards:** `try/except ImportError` with fallback stubs for optional dependencies.
- **Startup diagnostics:** Timing instrumentation prints import durations, making bottlenecks visible on every restart.

### Checklist
- [ ] Is this safe to run twice?
- [ ] Does the database initialization handle pre-existing tables/data?
- [ ] Are there any destructive operations that should be guarded?

---

## 9. Environment-Aware Deployment

### Principle
> Code should adapt to its environment (development, production, PythonAnywhere) without manual changes.

### How We Apply It
- **`.env` loading with absolute path:** `Path(__file__).parent / '.env'` ensures correct loading under WSGI.
- **Production detection:** `RUN_MODE` environment variable switches behavior (auto-docs, debug mode).
- **Database paths:** Externalized to env vars with sensible local defaults.
- **Logging suppression:** Noisy SDK loggers (httpx, openai, anthropic, grpc, absl, google) suppressed at startup.
- **Platform-aware encoding:** Windows console encoding fix (`sys.stdout` UTF-8 reconfiguration).

### Checklist
- [ ] Does this work on both Windows (local) and Linux (PythonAnywhere)?
- [ ] Are all paths relative or environment-configured?
- [ ] Are there any platform-specific assumptions?

---

## 10. Observability & Structured Logging

### Principle
> Every significant action should be logged with enough context to diagnose issues without a debugger.

### How We Apply It
- **Tagged log lines:** `[USER_CONTEXT]`, `[PERSONALITY]`, `[COACHING]`, `[CLARIFICATION]`, `[AI-BUDGET]`, `[ADAPTIVE]`, `[EXPLICIT]`, `[HISTORY_INSIGHTS]` — easy to grep.
- **Startup timing:** `_startup_elapsed()` prints elapsed time at each import stage.
- **Budget logging:** Every AI call check prints user, admin status, calls today, limit.
- **Error context:** Exceptions logged with the operation that failed, not just the error message.
- **Severity levels:** `logger.info` for normal operations, `logger.warning` for recoverable failures, `print` with emoji for user-visible events.

### Checklist
- [ ] Can I diagnose a production issue from logs alone?
- [ ] Are log lines tagged with a searchable prefix?
- [ ] Are errors logged with enough context (user_id, operation, input)?

---

## 11. Security by Default

### Principle
> Authentication, authorization, and data protection are built in, not bolted on.

### How We Apply It
- **JWT authentication:** All user-facing endpoints verify JWT tokens.
- **Role-based access:** `has_admin_access()` guards admin endpoints.
- **API key protection:** Keys stored in `.env`, never hard-coded or committed.
- **Input validation:** User inputs sanitized before database queries.
- **CORS configuration:** `flask_cors` configured for allowed origins.

### Checklist
- [ ] Does this endpoint require authentication?
- [ ] Are there admin-only operations that need role checks?
- [ ] Are secrets externalized to environment variables?
- [ ] Is user input sanitized before use?

---

## 12. Backward Compatibility & Safe Migration

### Principle
> Changes should not break existing functionality. Migrations should be incremental and reversible.

### How We Apply It
- **Database migrations:** New columns and tables added with `IF NOT EXISTS`, never dropping existing schema.
- **Fallback paths:** Database conversation storage falls back to JSON files if database is unavailable.
- **API versioning awareness:** New response fields (e.g., `clarification`) are additive — existing clients ignore them.
- **Feature flags via config:** `_knowledge_enabled = False` can toggle features without removing code.

### Checklist
- [ ] Does this change break any existing API contracts?
- [ ] Is there a fallback for clients that don't understand the new format?
- [ ] Can this migration be rolled back?

---

## 13. Scalable Data Architecture

### Principle
> Data structures should support growth in users, characters, and conversation volume without redesign.

### How We Apply It
- **Dual-layer history:** Raw data (immutable) + analytical layer (can be re-processed with improved algorithms).
- **Indexed queries:** Database indexes on `user_id`, `character_id`, `created_at` for fast lookups.
- **WAL mode:** SQLite Write-Ahead Logging for concurrent read/write performance.
- **Busy timeout:** 5000ms timeout prevents "database is locked" errors under load.
- **Archival system:** `context_archival.py` manages old data lifecycle.
- **Periodic cleanup:** Monthly maintenance via background scheduler.

### Checklist
- [ ] Will this query remain fast with 100K+ rows?
- [ ] Are there appropriate indexes?
- [ ] Is old data archived or cleaned up?
- [ ] Does this handle concurrent access?

---

## 14. Documentation as Code

### Principle
> Documentation should be generated, versioned, and maintained alongside code — not as an afterthought.

### How We Apply It
- **Auto-doc system:** `auto_doc_hook.py` generates documentation from code structure.
- **Roadmap tracking:** `IMPLEMENTATION_ROADMAP.md` and `PRODUCT_ROADMAP.md` kept in-repo and updated with each phase completion.
- **Architecture docs:** `INTELLIGENT_CONTEXT_ARCHITECTURE.md`, `CHARACTER_SPECTRUM_SYSTEM.md`, `CHARACTER_COLLABORATION_DESIGN.md` describe system design.
- **Inline docstrings:** All classes and public methods have docstrings explaining purpose, args, and return values.
- **Phase-specific status docs:** Each major milestone has a status document.

### Checklist
- [ ] Does this new module have a docstring explaining its purpose?
- [ ] Is the roadmap updated to reflect this change?
- [ ] Are architectural decisions documented (not just the code)?

---

## 15. Dependency Injection & Loose Coupling

### Principle
> Systems receive their dependencies explicitly rather than creating or importing them internally.

### How We Apply It
- **Pipeline injection:** `ConversationPipeline(**kwargs)` receives all 15+ subsystems as optional named arguments.
- **Database connection passing:** `get_db_conn()` creates connections; they're passed to constructors, not created inside modules.
- **Factory functions:** `create_personality_integrator()`, `create_effectiveness_learner()` encapsulate construction.
- **Settings injection:** `get_setting(key, default)` with import-guarded fallback.

### Checklist
- [ ] Does this module create its own dependencies, or receive them?
- [ ] Can this module be tested in isolation by passing mock dependencies?
- [ ] Are factory functions used for complex construction?

---

## 16. Progressive Enhancement

### Principle
> Core functionality works immediately. Advanced features activate as more data becomes available.

### How We Apply It
- **New user experience:** Characters respond meaningfully even with zero history, zero personality data, zero preferences.
- **Personality enrichment:** Starts with neutral defaults, improves as the system infers traits from conversation patterns.
- **Coaching adaptation:** Generic at first, increasingly personalized as goals and patterns emerge.
- **Clarification triggers:** Only activates when the system has enough context to know what's missing (confidence < 60%).

### Checklist
- [ ] Does this feature work for a brand-new user with no history?
- [ ] Does it get better over time as data accumulates?
- [ ] Is the "zero data" experience still useful?

---

## Summary Decision Framework

For **every feature, fix, or refactor**, verify:

| # | Principle | Question |
|---|-----------|----------|
| 1 | DRY | Is this logic already implemented elsewhere? |
| 2 | Graceful Degradation | What happens when this fails? |
| 3 | No Hard-Coding | Are values configurable? |
| 4 | Extensibility | Can new features plug in without modifying this? |
| 5 | Testing | Does this have automated tests? |
| 6 | Separation | Does this module do exactly one thing? |
| 7 | Cost Safety | Are external calls bounded and monitored? |
| 8 | Idempotency | Is this safe to run twice? |
| 9 | Environment | Does this work in all deployment targets? |
| 10 | Observability | Can I diagnose issues from logs? |
| 11 | Security | Is auth/authz/sanitization in place? |
| 12 | Compatibility | Does this break existing behavior? |
| 13 | Scalability | Will this handle growth? |
| 14 | Documentation | Is the intent documented? |
| 15 | Loose Coupling | Are dependencies injected, not hard-wired? |
| 16 | Progressive | Does this work with zero data? |

If any answer is unsatisfactory, address it before merging.

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Correct Approach |
|---|---|---|
| Duplicating logic across endpoints | Maintenance burden, inconsistent behavior | Extract to shared pipeline or utility |
| Crashing on missing optional data | Poor UX, cascading failures | try/except with fallback + logging |
| Hard-coded thresholds in business logic | Requires code change + deploy to tune | Centralize in `config.py` or admin settings |
| Testing only happy paths | Bugs hide in edge cases and failures | Test: happy path, edge cases, failure modes |
| Importing heavy dependencies at module level | Slow startup, breaks if dependency missing | Lazy import or import guard |
| Silent failures with no logging | Impossible to diagnose production issues | Always log with context on catch |
| Unbounded external API calls | Cost explosion, rate limit bans | Budget manager + circuit breaker |
| Tight coupling between modules | Can't test or change independently | Dependency injection, clear interfaces |

---

*This document should be consulted for all future development decisions. Update it when new principles emerge or existing ones evolve.*
