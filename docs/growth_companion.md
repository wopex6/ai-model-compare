# Growth Companion — living design doc

This is the working spec for the Growth Companion (`/grow`, engine in
`smart_response/growth_engine.py`). It is **living**: revise it as we learn;
the anti-pattern registry especially is never "done". Decisions are dated
where they were made.

North star (decided): **niche-outcomes** — success is transformation depth
per user (completed actions, unstuck habits, embodied learning), not market
defensibility or engagement metrics. Big Tech will not optimise for a small
high-touch niche; the accumulated personal model is an operational switching
cost, not a structural moat. The real risk is that nobody's life measurably
improves — so metrics are action-completion, never retention.

---

## The three realities

- **User's perceived reality** — what they believe/feel about themselves and
  their situation right now.
- **The app's reality** — the private, evidence-grounded model
  (`growth_reflections` etc.). Honest, always maintained; never softened
  because the user wasn't ready.
- **The coaching frontier** — the delta between them. The companion works
  *at* it: meet the user inside their perceived reality, expand gradually.

## Delivery calibration — knowing ≠ telling

| Strategy | When | Form |
|---|---|---|
| `hold` | sensitive / closed type / wrong state | kept in model; resurfaces on trigger conditions |
| `seed` | not ready for the conclusion | observation without the conclusion |
| `lead` | partially open / opportune | questions, their own past words |
| `propose` | open type, right moment | "I've noticed X — ring true?" confirm/correct/delete |
| `show` | user pulls it (Mirror surface) | pull, not push |

Rules:

- **Well-being overrides readiness** — safety-relevant findings are never
  shelved indefinitely; `hold` carries trigger conditions, not silence.
- **Transparency boundary** — stored *facts* are always user-inspectable and
  correctable; *interpretations* are what's calibrated. The internal model is
  inspectable on request (admin inspector exists for dev/test).
- Every delivery decision is logged with its reason; strategies serve the
  user's well-being goals only — never engagement or retention.

## Top-down vs bottom-up

Top-down (milestones, plans, strategies, goal-driven): efficient when the
methodology is proven *and* the situation well-defined. Bottom-up (research,
coordination, adaptation, cooperation, trial-and-error, flexibility):
required when novel or ill-defined. The engine itself is bottom-up — it
learns from feedback loops, not a fixed rule tree.

Each commitment records `mode` and why. A bottom-up approach that repeatedly
works *for this user* graduates into their personal playbook; a top-down
routine repeatedly failing demotes back to bottom-up. Plan failure is a
signal to switch mode, not to insist.

Current mapping: habits → `top_down` (defined cadence); engagement threads →
`adaptive` (self-adjusting); stated goals/intentions → `bottom_up`.

## Progression models

**Internal (self-understanding)** — awareness, not a skill:
noticed → acknowledged → explored → integrated. No "mastery".

**External (knowledge/skill)** — 8 stages:
heard → understood → felt → accepted → applied → proficient → mastery →
transfer. Stage 3 requires *embodied* evidence (reported in-the-moment
experience or observed behaviour) — agreeing words don't count. Transitions
store their trigger text — auditable, user-correctable.

Boundary nuance: trainable internal capabilities (emotion regulation,
self-noticing) ride the external track; split by nature, not topic label.

## Channels & feedback timing

Chat is the highest-effort channel; every channel is judged on
effort-to-engage AND whether a signal returns.

**Ask in the moment, not later** (memory is short, attention shorter):

- Inline one-tap reactions on cards — never delayed recall questions.
- Prime before watching; ask feelings, not facts.
- Embed external video in-app; the watch layer (transcript → planned moments
  → IFrame-API prompts) makes borrowed content interactive.
- Catch on return — minutes/hours after, not days.

Tracks stay separate: in-app micro-content (primary) / curated external links
(sparse events) / public generic marketing content (never personalized).

Avatars: current pipeline quality insufficient — voice-only reflections
(TTS client-side); better avatar is a deferred research track.

## Cold start & lifecycle

Hybrid onboarding: one seed question ("what are you working on lately?") →
tap-to-refine topic cards → generic starter set; psych test offered later as
an optional card, never a gate. Consent is staged (notifications at first
scheduling, health opt-in at relevance). First loop closes within session
1–2: one tiny calibrated action.

Re-engagement: one honest win-back referencing their open thread, then
silence — never a drip campaign.

## Data boundaries

- Health ↔ Growth: opt-in per domain, revocable anytime; health specifics
  never in glanceable feed copy; mirror facts domain-tagged for audit.
- Internal model: server-side only; included in export AND delete-my-data.
- Coaching never issues medical guidance — Dr. Health owns that.
- Language: UI English-fixed; content follows user's language via the model.
- Small circle (deferred): opt-in accountability-partner view of
  commitments/wins only — never reflections or health.

## Anti-pattern registry — living

| Failure mode | Countermeasure |
|---|---|
| Notification fatigue / nagging | rate limits, digest batching, snooze/dismiss/stop |
| Generic advice | evidence citations on everything |
| Hallucinated memory | verified/unverified provenance |
| Sycophancy | internal model stays honest regardless of delivery |
| Premature truth / illusion collapse | hold/seed/lead/propose + receptivity |
| Indirect-coaching → manipulation | delivery decisions logged; well-being only |
| Waited forever | hold has trigger conditions |
| Top-down on bottom-up problem | mode recorded; failure demotes |
| Bottom-up wandering on solved problem | proven patterns graduate to playbook |
| Attention leak to external platforms | embed in-app; links are primed events |
| Delayed-feedback noise | in-moment capture; feelings not facts |
| Engagement without feedback loop | every channel returns a signal |
| Personalized content leaking public | tracks strictly separate |
| Content quality risk | curation first; quality bar before generation |
| Interruption fatigue | 2–4 watch moments max, mutable |
| Hallucinated watch-moments | timestamps validated against transcript |
| Free-API dependence | tiered analysis; degrade to metadata |
| Demand-creation → clickbait | teasers quote the real question; relevance only |
| Analysis cost explosion | tier escalation only on miss; per-video cache |
| Pool staleness | keyed to active topics; expire unused |
| Cold-start emptiness | designed day-one; value in first session |
| Ranking drift | explicit feed policy; session length never a signal |
| Health-data leakage into engagement | opt-in per domain; auditable tags |
| Re-engagement → drip marketing | one win-back then silence |
| Cost ceiling as product ceiling | per-user/day model-call budget |
| Calibration theatre | persona-scenario eval harness in CI |
| Guilt-tripping on misses | neutral reschedule/drop |
| Engagement bait | success = completed actions |
| Privacy creepiness | facts inspectable; interpretations on request |
| Dependency | route toward real-world action; crisis_detector upstream |
| Stale advice | re-derived state, signature invalidation |
| Runaway autonomy | proposals first; provenance on every write |
| Mirror as verdict | evidence-linked; user's word is last |

## Evaluation

Persona-scenario fixtures assert the deterministic decision layer (delivery
strategy, stage behaviour, feed order) — never regex on generated prose.
Golden-prompt regression for LLM phrasing; optional nightly LLM-as-judge;
scripted user simulator deferred.

Metrics: completed actions / active user / week; return-catch response rate;
mirror confirm/correct ratio (high correct rate = calibration failure);
plan-completion by mode. Never: session length, DAU, notification opens.

## Decisions log

- Niche-outcomes north star (not venture defensibility).
- Health→growth: opt-in per domain, anytime revocable.
- Language: UI English; content follows user language via model.
- Small circle: designed, deferred until core loop proves out.
- Admin inspector is the dev/test window into the private model.
- Phase 0 build: engine + state endpoint + inspector; reads pure-Python.
- Phase 1 build: `/grow` — card feed + coordinator chat + correctable facts.
- Phase 2 build: learning topics — `derive_topics()` populates
  `growth_topics` from observed sources only (topics_discussed, explicit
  goals/preferences/self-descriptions, engagement subjects; never invented).
  Stage advances deterministically on evidence: multi-day mentions → 2,
  engaged card signal → 3, linked thread/habit → 4, completed linked
  commitment → 5, repeated completions → 6 (7–8 not auto-reachable yet).
  Stages never regress; every move stores its trigger text. Feed surfaces
  one topic card at a time, stage-labelled, throttled to once per topic per
  `TOPIC_RESURFACE_DAYS`; `not_for_me` dismisses it permanently. Topic
  kinds split internal (4-stage: noticed→acknowledged→explored→integrated)
  vs external (8-stage) by keyword; refinement is deliberate future work.
- Phase 3 build: receptivity + delivery ladder. `learn_receptivity()`
  recomputes `growth_receptivity` from the whole feedback history —
  global `openness` (Laplace-smoothed around 0.5) plus per-subject
  scores keyed by item_type or `topic:`/`refl:` ref. `surfaced`/`snoozed`
  never count; `corrected` counts as engagement, not rejection.
  `delivery_strategy()` maps sensitivity × openness onto
  hold/seed/propose deterministically (high-sensitivity is NEVER
  card-proposed — pull only); resolved reflections leave the rotation.
  A subject scoring below `TOPIC_SUBJECT_SUPPRESS` stops surfacing without
  being dismissed. At most one `propose` card per feed, throttled per
  reflection; its confirm/correct/snooze replies land on
  `status`/`delivery_log` — the mirror confirm/correct ratio metric now
  has data. Receptivity tunes the companion's prompts only — habits,
  check-ins and threads (the user's own commitments) are never dampened.
