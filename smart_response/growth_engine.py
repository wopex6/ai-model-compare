"""Growth Engine — unified read of a user's growth state + the private
insight model ("the app's reality").

Phase 0 scope (see docs/growth_companion.md):

  - Composes existing machinery into one read path: explicit_context goals
    and values, habit_tracker summaries, life_companion_profile, engagement
    threads (ai_compare/engagement.py).
  - Maintains four growth tables: growth_reflections, growth_topics,
    growth_receptivity, growth_feedback.
  - derive_reflections() produces *candidate* insights deterministically —
    every claim carries evidence references, a sensitivity tag, a delivery
    status (default 'hold') and the trigger condition that would make it
    timely. Reflections are the app's private model: they are NEVER shown
    to the user directly; delivery is calibrated later (hold/seed/lead/
    propose/show).

All reads are pure Python. No model calls. All writes carry provenance.
"""

import json
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# ---------------------------------------------------------------------------
# Reflection rules
# ---------------------------------------------------------------------------

STALE_GOAL_DAYS = 21          # stated goal/intention untouched this long → stale
LOW_COMPLETION_RATE = 0.3     # weekly habit completion below this → "missing"
STRONG_STREAK_DAYS = 14       # streak at/above this → consistency observation
LOW_MOOD_AVG = 2.5            # 1-5 scale; avg of recent check-ins below → concern
MIN_MOOD_CHECKINS = 3
GUARDED_TRUST_MAX = 0.3       # profile trust_level below this → guarded
MIN_INTERACTIONS_GUARDED = 10
DOMAIN_STRUGGLE_MIN_MENTIONS = 3

# Map explicit stated values/self-descriptions onto habit categories so a
# stated value can be checked against observed behaviour in the same domain.
VALUE_CATEGORY_KEYWORDS = {
    'health':     ('health', 'fitness', 'exercise', 'gym', 'diet', 'sleep'),
    'learning':   ('learn', 'study', 'read', 'course', 'skill'),
    'mindfulness': ('meditat', 'mindful', 'calm', 'stress', 'mental'),
    'social':     ('family', 'friend', 'relationship', 'partner', 'social'),
    'productivity': ('work', 'productive', 'career', 'project', 'focus'),
    'creativity': ('creat', 'write', 'art', 'music', 'paint'),
}

# ---------------------------------------------------------------------------
# Learning topics (Phase 2) — the 8-stage external track and the 4-stage
# internal track. Stages only move forward, only on evidence, and every move
# records its trigger text.
# ---------------------------------------------------------------------------

INTERNAL_TOPIC_KEYWORDS = (
    'emotion', 'feeling', 'feel ', 'stress', 'anxiet', 'mood', 'self',
    'confidence', 'relationship', 'fear', 'grief', 'loneli', 'motivation',
    'self-doubt', 'anger', 'shame', 'identity', 'purpose', 'meaning',
)

EXTERNAL_STAGE_LABELS = {
    1: 'heard', 2: 'understood', 3: 'felt', 4: 'accepted',
    5: 'applied', 6: 'proficient', 7: 'mastery', 8: 'transfer',
}
INTERNAL_STAGE_LABELS = {
    1: 'noticed', 2: 'acknowledged', 3: 'explored', 4: 'integrated',
}
MAX_INTERNAL_STAGE = 4

TOPIC_RESURFACE_DAYS = 3    # don't resurface a topic card more often than this

# Stage-aware card copy. Short, honest, never fake-deep.
TOPIC_STAGE_COPY = {
    'external': {
        1: 'This came up for you. Still on your radar?',
        2: 'You have looked at this a few times now — what part of it matters most right now?',
        3: 'Next time this comes up, just notice how it lands before deciding what to do.',
        4: 'One small thing you could actually try with this?',
        5: 'This is becoming practice, not just an idea — what changed?',
        6: 'You have real reps on this now. What would you tell someone earlier in it?',
        7: 'This looks close to second nature — where does it still slip?',
        8: 'You have taken this into another part of life — what carried over?',
    },
    'internal': {
        1: 'This has come up a few times.',
        2: 'How has this been showing up lately?',
        3: 'What is underneath it, do you think?',
        4: 'You have been working with this — what have you learned about yourself?',
    },
}

# Feedback signals that count as embodied engagement with a topic card
TOPIC_ENGAGED_SIGNALS = ('acted', 'tell_me_more', 'positive', 'done', 'landed')

# ---------------------------------------------------------------------------
# Receptivity (Phase 3) — learned from the feedback loop, per user and per
# subject. Receptivity tunes the COMPANION'S prompts (topic/propose cards);
# it never silences the user's own commitments (habits, check-ins, threads).
# 'surfaced' rows are engine bookkeeping, not user signals — never counted.
# ---------------------------------------------------------------------------

POSITIVE_SIGNALS = TOPIC_ENGAGED_SIGNALS + (
    'confirm', 'confirmed', 'accepted', 'answered', 'corrected', 'correct')
NEGATIVE_SIGNALS = ('dismissed', 'not_for_me', 'rejected')
NEUTRAL_SIGNALS = ('surfaced', 'snoozed')   # bookkeeping / deferral

PROPOSE_RESURFACE_DAYS = 2   # at most one propose card per reflection this often
TOPIC_SUBJECT_SUPPRESS = 0.2  # per-topic score below this → stop surfacing it

# Openness a reflection's sensitivity needs before it may be proposed.
PROPOSE_OPENNESS = {'low': 0.4, 'medium': 0.65, 'high': 1.1}  # high: never propose


class GrowthEngine:
    """Unified growth-state read + private reflection model.

    Usage::

        engine = GrowthEngine(conn, habit_tracker, life_companion_profiler)
        state = engine.growth_state(user_id)          # user-visible facts
        result = engine.derive_reflections(user_id)    # candidate insights
        payload = engine.inspector_payload(user_id)    # admin/dev view
    """

    def __init__(self, db_connection=None, habit_tracker=None, profiler=None):
        self.db = db_connection
        self._habits = habit_tracker
        self._profiler = profiler
        self._tables_ok = False
        self._ensure_tables()

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    def _ensure_tables(self):
        """Create growth tables; retried lazily — a locked DB at init must not
        permanently wedge the engine (init runs inside app's big try block
        where a lock failure is survivable)."""
        if not self.db or self._tables_ok:
            return
        try:
            cur = self.db.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS growth_reflections (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id          INTEGER NOT NULL,
                    claim_key        TEXT NOT NULL,
                    claim            TEXT NOT NULL,
                    sensitivity      TEXT DEFAULT 'medium',
                    status           TEXT DEFAULT 'hold',
                    evidence_json    TEXT DEFAULT '[]',
                    trigger_text     TEXT DEFAULT '',
                    delivery_log     TEXT DEFAULT '[]',
                    source           TEXT DEFAULT 'engine',
                    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, claim_key)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS growth_topics (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id          INTEGER NOT NULL,
                    topic            TEXT NOT NULL,
                    kind             TEXT DEFAULT 'external',
                    stage            INTEGER DEFAULT 1,
                    stage_trigger    TEXT DEFAULT '',
                    source           TEXT DEFAULT 'user',
                    dismissed        INTEGER DEFAULT 0,
                    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, topic)
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS growth_receptivity (
                    user_id          INTEGER PRIMARY KEY,
                    openness         REAL DEFAULT 0.5,
                    sensitivity_json TEXT DEFAULT '{}',
                    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS growth_feedback (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id          INTEGER NOT NULL,
                    item_type        TEXT NOT NULL,
                    item_ref         TEXT DEFAULT '',
                    signal           TEXT NOT NULL,
                    detail           TEXT DEFAULT '',
                    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db.commit()
            self._tables_ok = True
        except Exception as e:
            print(f"[GrowthEngine] table init error: {e}")

    # ------------------------------------------------------------------
    # Unified read
    # ------------------------------------------------------------------
    def _explicit_items(self, user_id: int) -> List[Dict]:
        """Active explicit_context rows across all characters.

        The handler API is per-character; growth state needs the aggregate,
        so this reads the shared table directly (read-only).
        """
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT id, timestamp, context_type, context_key, context_value,
                       original_statement, priority, confidence, character
                FROM explicit_context
                WHERE user_id = ? AND active = 1
                ORDER BY timestamp DESC
            ''', (user_id,))
            rows = cur.fetchall()
        except Exception as e:
            print(f"[GrowthEngine] explicit read error: {e}")
            return []
        return [
            {'id': r[0], 'timestamp': r[1], 'type': r[2], 'key': r[3],
             'value': r[4], 'statement': r[5], 'priority': r[6],
             'confidence': r[7], 'character': r[8]}
            for r in rows
        ]

    def _habit_summary(self, user_id: int) -> Dict:
        if not self._habits:
            return {}
        try:
            s = self._habits.get_summary(user_id)
            return {
                'active_habits': [
                    {'id': h.id, 'name': h.name, 'category': h.category,
                     'streak': h.current_streak, 'best_streak': h.best_streak,
                     'total_completions': h.total_completions,
                     'last_completed': h.last_completed}
                    for h in s.active_habits
                ],
                'due_today': [h.name for h in s.due_today],
                'current_streaks': s.current_streaks,
                'weekly_completion_rate': s.weekly_completion_rate,
                'mood_trend': s.mood_trend,
                'recent_checkins': [
                    {'date': c.date, 'mood': c.mood, 'energy': c.energy,
                     'mood_score': c.mood_score}
                    for c in s.recent_checkins
                ],
            }
        except Exception as e:
            print(f"[GrowthEngine] habit summary error: {e}")
            return {}

    def _profile(self, user_id: int) -> Dict:
        if not self._profiler:
            return {}
        try:
            p = self._profiler.get_profile(user_id)
            return {
                'trust_level': p.trust_level,
                'avg_message_depth': p.avg_message_depth,
                'total_interactions': p.total_interactions,
                'first_interaction': p.first_interaction,
                'last_interaction': p.last_interaction,
                'detected_values': p.detected_values,
                'life_domains': {
                    d: {'sentiment': s.sentiment, 'confidence': s.confidence,
                        'mention_count': s.mention_count,
                        'trajectory': s.trajectory}
                    for d, s in p.life_domains.items()
                },
                'topics_discussed': p.topics_discussed,
            }
        except Exception as e:
            print(f"[GrowthEngine] profile error: {e}")
            return {}

    def _engagement_threads(self, user_id: int) -> List[Dict]:
        """Open engagement threads — the existing commitment loop."""
        try:
            from ai_compare import engagement
            return engagement.list_threads(str(user_id))
        except Exception as e:
            print(f"[GrowthEngine] engagement threads error: {e}")
            return []

    def commitments(self, user_id: int) -> List[Dict]:
        """Unified commitment view with a mode tag per item.

        mode: 'top_down'  — proven structure (a habit with a defined cadence)
              'adaptive'  — engagement thread (self-adjusting cadence)
              'bottom_up' — stated goal/intention without structure yet
        """
        items = []
        for h in (self._habit_summary(user_id).get('active_habits') or []):
            items.append({
                'source': 'habit', 'ref': h['id'], 'label': h['name'],
                'status': 'active', 'mode': 'top_down',
                'detail': f"streak {h['streak']}, best {h['best_streak']}",
            })
        for t in self._engagement_threads(user_id):
            items.append({
                'source': 'engagement', 'ref': t.get('id'), 'label': t.get('subject', ''),
                'status': t.get('status', 'open'), 'mode': 'adaptive',
                'detail': t.get('kind', ''),
            })
        for c in self._explicit_items(user_id):
            if c['type'] in ('goal', 'intention', 'plan'):
                items.append({
                    'source': 'explicit', 'ref': c['id'], 'label': c['value'],
                    'status': 'open', 'mode': 'bottom_up',
                    'detail': c['statement'],
                })
        return items

    def growth_state(self, user_id: int) -> Dict:
        """The user-visible unified state — facts only, no reflections."""
        self._ensure_tables()
        topics = []
        try:
            cur = self.db.cursor()
            cur.execute('''
                SELECT topic, kind, stage, stage_trigger, source
                FROM growth_topics WHERE user_id = ? AND dismissed = 0
                ORDER BY stage DESC, updated_at DESC
            ''', (user_id,))
            topics = [
                {'topic': r[0], 'kind': r[1], 'stage': r[2],
                 'stage_trigger': r[3], 'source': r[4]}
                for r in cur.fetchall()
            ]
        except Exception as e:
            print(f"[GrowthEngine] topics read error: {e}")
        return {
            'user_id': user_id,
            'explicit': self._explicit_items(user_id),
            'habits': self._habit_summary(user_id),
            'profile': self._profile(user_id),
            'commitments': self.commitments(user_id),
            'topics': topics,
        }

    # ------------------------------------------------------------------
    # Reflection derivation — deterministic candidate insights
    # ------------------------------------------------------------------
    def _upsert_reflection(self, user_id: int, c: Dict, now: str) -> str:
        """Insert or refresh a candidate reflection. Returns 'created' or
        'updated'. An existing row keeps its status and delivery_log —
        re-derivation updates the claim/evidence, never re-hides a delivered
        or dismissed reflection."""
        cur = self.db.cursor()
        cur.execute('''
            SELECT id, status FROM growth_reflections
            WHERE user_id = ? AND claim_key = ?
        ''', (user_id, c['claim_key']))
        row = cur.fetchone()
        evidence = json.dumps(c.get('evidence', []))
        if row:
            cur.execute('''
                UPDATE growth_reflections
                SET claim = ?, sensitivity = ?, evidence_json = ?,
                    trigger_text = ?, updated_at = ?
                WHERE id = ?
            ''', (c['claim'], c['sensitivity'], evidence,
                  c.get('trigger', ''), now, row[0]))
            return 'updated'
        cur.execute('''
            INSERT INTO growth_reflections
                (user_id, claim_key, claim, sensitivity, status,
                 evidence_json, trigger_text, source)
            VALUES (?, ?, ?, ?, 'hold', ?, ?, 'engine')
        ''', (user_id, c['claim_key'], c['claim'], c['sensitivity'],
              evidence, c.get('trigger', '')))
        return 'created'

    def derive_reflections(self, user_id: int, now: Optional[datetime] = None) -> Dict:
        """Run every deterministic rule over the user's data and upsert the
        candidate reflections they produce. Idempotent — claim_key dedups."""
        self._ensure_tables()
        now = now or datetime.now()
        now_s = now.isoformat()
        candidates: List[Dict] = []

        explicit = self._explicit_items(user_id)
        habits = self._habit_summary(user_id)
        profile = self._profile(user_id)

        # Rule 1 — stale stated goals/intentions
        cutoff = (now - timedelta(days=STALE_GOAL_DAYS)).isoformat()
        for c in explicit:
            if c['type'] in ('goal', 'intention', 'plan') \
                    and (c['timestamp'] or '') < cutoff:
                candidates.append({
                    'claim_key': f"stale_goal:{c['id']}",
                    'claim': (f"Goal stated but not revisited: "
                              f"“{c['value']}” (said {(c['timestamp'] or '')[:10]})"),
                    'sensitivity': 'medium',
                    'trigger': 'when the user next raises a related topic',
                    'evidence': [{'source': 'explicit_context', 'ref': c['id'],
                                  'note': c['statement']}],
                })

        # Rule 2 — habit consistency, both directions
        rate = habits.get('weekly_completion_rate')
        for h in habits.get('active_habits') or []:
            ev = [{'source': 'habits', 'ref': h['id'],
                   'note': f"weekly rate {rate}, streak {h['streak']}"}]
            if rate is not None and rate < LOW_COMPLETION_RATE:
                candidates.append({
                    'claim_key': f"habit_low:{h['id']}",
                    'claim': f"“{h['name']}” is being missed often this week.",
                    'sensitivity': 'low',
                    'trigger': 'next check-in on this habit',
                    'evidence': ev,
                })
            if h['streak'] >= STRONG_STREAK_DAYS:
                candidates.append({
                    'claim_key': f"habit_streak:{h['id']}",
                    'claim': f"“{h['name']}” has a {h['streak']}-day streak.",
                    'sensitivity': 'low',
                    'trigger': 'natural moment to acknowledge consistency',
                    'evidence': ev,
                })

        # Rule 3 — stated-vs-observed divergence
        habit_categories = {(h['category'] or '').lower() for h in
                            (habits.get('active_habits') or [])}
        stated = [c for c in explicit if c['type'] in
                  ('value', 'self_description', 'preference')]
        for c in stated:
            text = f"{c['key']} {c['value']} {c['statement']}".lower()
            for cat, keywords in VALUE_CATEGORY_KEYWORDS.items():
                if cat not in habit_categories or \
                        not any(k in text for k in keywords):
                    continue
                if rate is not None and rate < LOW_COMPLETION_RATE:
                    candidates.append({
                        'claim_key': f"divergence:{c['id']}:{cat}",
                        'claim': (f"Stated “{c['value']}” but observed "
                                  f"{cat} habits are slipping "
                                  f"({(rate or 0) * 100:.0f}% this week)."),
                        'sensitivity': 'high',
                        'trigger': 'hold until the user names the gap '
                                   'themselves or asks about the domain',
                        'evidence': [
                            {'source': 'explicit_context', 'ref': c['id'],
                             'note': c['statement']},
                            {'source': 'habits', 'ref': cat,
                             'note': f"weekly rate {rate}"},
                        ],
                    })

        # Rule 4 — mood trend declining
        checkins = habits.get('recent_checkins') or []
        scores = [c['mood_score'] for c in checkins
                  if isinstance(c.get('mood_score'), (int, float))]
        if habits.get('mood_trend') == 'declining' or (
                len(scores) >= MIN_MOOD_CHECKINS
                and sum(scores) / len(scores) < LOW_MOOD_AVG):
            candidates.append({
                'claim_key': 'mood_declining',
                'claim': 'Recent check-ins suggest mood has been trending down.',
                'sensitivity': 'high',
                'trigger': 'next natural opening; never lead with this',
                'evidence': [{'source': 'daily_checkins',
                              'ref': 'recent',
                              'note': f"scores {scores[-7:]}"}],
            })

        # Rule 5 — guarded despite history
        if (profile.get('trust_level') is not None
                and profile['trust_level'] < GUARDED_TRUST_MAX
                and (profile.get('total_interactions') or 0)
                    >= MIN_INTERACTIONS_GUARDED):
            candidates.append({
                'claim_key': 'guarded_trust',
                'claim': ('Shares at surface level despite many '
                          'interactions — likely a reserved style, not '
                          'disengagement.'),
                'sensitivity': 'medium',
                'trigger': 'prefer indirect strategies (seed/lead); do not '
                           'press for disclosure',
                'evidence': [{'source': 'companion_profile', 'ref': 'trust',
                              'note': f"trust {profile['trust_level']}, "
                                      f"{profile['total_interactions']} msgs"}],
            })

        # Rule 6 — recurring negative life domain
        for domain, d in (profile.get('life_domains') or {}).items():
            if d.get('mention_count', 0) >= DOMAIN_STRUGGLE_MIN_MENTIONS \
                    and (d.get('sentiment') == 'negative'
                         or d.get('trajectory') == 'declining'):
                candidates.append({
                    'claim_key': f"domain_struggle:{domain}",
                    'claim': (f"“{domain}” recurs with "
                              f"{d.get('sentiment')} sentiment "
                              f"({d.get('mention_count')} mentions, "
                              f"trajectory {d.get('trajectory')})."),
                    'sensitivity': 'medium',
                    'trigger': 'when the user raises this domain again',
                    'evidence': [{'source': 'companion_profile',
                                  'ref': domain,
                                  'note': json.dumps(d)}],
                })

        created = updated = 0
        for c in candidates:
            if self._upsert_reflection(user_id, c, now_s) == 'created':
                created += 1
            else:
                updated += 1
        self.db.commit()
        return {'created': created, 'updated': updated,
                'candidates': len(candidates)}

    # ------------------------------------------------------------------
    # Learning topics — derivation + deterministic stage tracking
    # ------------------------------------------------------------------
    def _topic_candidates(self, user_id: int) -> Dict[str, Dict]:
        """Topic strings from existing machinery, never invented.

        Returns {normalized_topic: {'sources': set, 'days': set, 'raw': str}}.
        """
        out: Dict[str, Dict] = {}

        def add(text: str, source: str, day: str):
            text = (text or '').strip()
            if not text or len(text) < 3 or len(text) > 120:
                return
            key = text.lower()
            slot = out.setdefault(key, {'sources': set(), 'days': set(),
                                        'raw': text})
            slot['sources'].add(source)
            if day:
                slot['days'].add(day[:10])

        profile = self._profile(user_id)
        for t in profile.get('topics_discussed') or []:
            add(t, 'topics_discussed', '')

        for c in self._explicit_items(user_id):
            if c['type'] in ('goal', 'preference', 'self_description'):
                add(c['value'], f"explicit:{c['type']}", c['timestamp'])

        for t in self._engagement_threads(user_id):
            add(t.get('subject', ''), 'engagement', '')

        return out

    def _topic_linkage(self, user_id: int, topic: str) -> Dict:
        """Commitments linked to a topic by shared words, plus completion
        evidence (done threads, habit completions)."""
        tokens = {w for w in re.findall(r"[a-z']+", topic.lower())
                  if len(w) > 3}
        linked = done = 0
        # Commitments = engagement threads + habits only. explicit_context
        # goals are how a topic *arises*, not structure around it — counting
        # the source goal as its own commitment would jump every topic
        # straight to 'accepted'.
        try:
            from ai_compare import engagement
            threads = engagement.list_threads(str(user_id), include_closed=True)
        except Exception:
            threads = []
        for t in threads:
            words = set(re.findall(r"[a-z']+", (t.get('subject') or '').lower()))
            if tokens & words:
                linked += 1
                if t.get('status') == 'done':
                    done += 1
        for h in (self._habit_summary(user_id).get('active_habits') or []):
            words = set(re.findall(r"[a-z']+", (h['name'] or '').lower()))
            if tokens & words:
                linked += 1
                if (h.get('total_completions') or 0) >= 3:
                    done += 1
        return {'linked': linked, 'done': done}

    def _topic_feedback_signals(self, user_id: int) -> Dict[str, Dict]:
        """Per-topic feedback: engaged signals, last surfaced date."""
        cur = self.db.cursor()
        try:
            # Cards signal as item_type='card', item_ref='topic:<name>'; the
            # API may also post item_type='topic' with the bare name.
            cur.execute('''
                SELECT item_ref, signal, created_at FROM growth_feedback
                WHERE user_id = ?
                  AND (item_type = 'topic' OR item_ref LIKE 'topic:%')
            ''', (user_id,))
            rows = cur.fetchall()
        except Exception:
            return {}
        out: Dict[str, Dict] = {}
        for ref, signal, at in rows:
            key = ref[len('topic:'):] if ref.startswith('topic:') else ref
            slot = out.setdefault(key, {'engaged': False, 'surfaced': ''})
            if signal in TOPIC_ENGAGED_SIGNALS:
                slot['engaged'] = True
            if signal == 'surfaced' and (at or '') > slot['surfaced']:
                slot['surfaced'] = at
        return out

    def _eval_stage(self, kind: str, ev: Dict) -> tuple:
        """Evidence -> (stage, trigger). Stages only what evidence supports."""
        mentions = len(ev['days'])
        sources = len(ev['sources'])
        if kind == 'internal':
            if ev['engaged'] and mentions >= 4:
                return 4, 'engaged with the card and the topic keeps recurring'
            if ev['engaged']:
                return 3, 'user engaged with the topic card'
            if mentions >= 2:
                return 2, 'came up on more than one day'
            return 1, 'first seen'
        # external
        if ev['done'] >= 2:
            return 6, 'linked commitments completed more than once'
        if ev['done'] >= 1:
            return 5, 'a linked commitment was completed'
        if ev['linked'] >= 1:
            return 4, 'a commitment now exists for this topic'
        if ev['engaged']:
            return 3, 'user engaged with the topic card'
        if mentions >= 2 or sources >= 2:
            return 2, 'raised more than once / across sources'
        return 1, 'first seen'

    def derive_topics(self, user_id: int, now: Optional[datetime] = None) -> Dict:
        """Populate/refresh growth_topics from observed data. Idempotent:
        upsert by (user, topic); stage never regresses; every move records
        the trigger that earned it."""
        self._ensure_tables()
        now_s = (now or datetime.now()).isoformat()
        candidates = self._topic_candidates(user_id)
        signals = self._topic_feedback_signals(user_id)
        cur = self.db.cursor()
        created = advanced = 0
        for topic, ev in candidates.items():
            kind = ('internal' if any(k in topic
                                      for k in INTERNAL_TOPIC_KEYWORDS)
                    else 'external')
            fb = signals.get(topic, {})
            link = self._topic_linkage(user_id, topic)
            stage, trigger = self._eval_stage(
                kind, {**ev, 'engaged': fb.get('engaged', False), **link})
            cur.execute('''
                SELECT id, stage FROM growth_topics
                WHERE user_id = ? AND topic = ?
            ''', (user_id, topic))
            row = cur.fetchone()
            if row:
                if stage > row[1]:
                    cur.execute('''
                        UPDATE growth_topics SET stage = ?, stage_trigger = ?,
                            updated_at = ? WHERE id = ?
                    ''', (stage, trigger, now_s, row[0]))
                    advanced += 1
            else:
                cur.execute('''
                    INSERT INTO growth_topics
                        (user_id, topic, kind, stage, stage_trigger, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, topic, kind, stage, trigger,
                      ','.join(sorted(ev['sources']))))
                created += 1
        self.db.commit()
        return {'created': created, 'advanced': advanced,
                'total': len(candidates)}

    def _topic_card(self, user_id: int,
                    receptivity: Optional[Dict] = None) -> Optional[Dict]:
        """One topic card: the furthest-along topic not surfaced recently
        and not suppressed by its own feedback score. Facts only — stage
        label + stage-appropriate prompt."""
        self._ensure_tables()
        cutoff = (datetime.now()
                  - timedelta(days=TOPIC_RESURFACE_DAYS)).isoformat()
        surfaced = {r: s['surfaced']
                    for r, s in self._topic_feedback_signals(user_id).items()}
        scores = (receptivity or {}).get('sensitivity') or {}
        cur = self.db.cursor()
        cur.execute('''
            SELECT topic, kind, stage FROM growth_topics
            WHERE user_id = ? AND dismissed = 0
            ORDER BY stage DESC, updated_at DESC
        ''', (user_id,))
        for topic, kind, stage in cur.fetchall():
            if stage > MAX_INTERNAL_STAGE and kind == 'internal':
                stage = MAX_INTERNAL_STAGE
            if stage > 5:
                continue  # past 'applied' — don't keep prompting
            if (surfaced.get(topic) or '') > cutoff:
                continue  # surfaced recently — throttle
            if scores.get(f'topic:{topic}', {}).get('score', 1.0) \
                    < TOPIC_SUBJECT_SUPPRESS:
                continue  # user keeps rejecting this topic — stop asking
            labels = (INTERNAL_STAGE_LABELS if kind == 'internal'
                      else EXTERNAL_STAGE_LABELS)
            copy = TOPIC_STAGE_COPY[kind].get(
                stage, TOPIC_STAGE_COPY[kind][1])
            return {
                'id': f'topic:{topic}', 'type': 'topic',
                'title': topic, 'stage': stage,
                'stage_label': labels.get(stage, ''),
                'text': copy,
            }
        return None

    # ------------------------------------------------------------------
    # Receptivity — learned openness, per user and per subject
    # ------------------------------------------------------------------
    def learn_receptivity(self, user_id: int) -> Dict:
        """Recompute receptivity from the whole growth_feedback history.

        openness   — global 0..1 willingness to engage with prompts.
                     Laplace-smoothed around 0.5 so a handful of signals
                     can't swing it to an extreme.
        sensitivity — per-subject scores (item_type, or 'topic:<name>' /
                     'refl:<id>' for per-item learning). Below
                     TOPIC_SUBJECT_SUPPRESS the subject stops surfacing.

        'corrected' counts as positive participation — correcting the
        mirror is engagement, not rejection. 'surfaced'/'snoozed' are
        bookkeeping/deferral and never move the score.
        """
        self._ensure_tables()
        cur = self.db.cursor()
        try:
            cur.execute('''
                SELECT item_type, item_ref, signal, created_at
                FROM growth_feedback WHERE user_id = ?
            ''', (user_id,))
            rows = cur.fetchall()
        except Exception as e:
            print(f"[GrowthEngine] receptivity read error: {e}")
            rows = []

        subjects: Dict[str, Dict] = {}
        pos = neg = 0
        for item_type, ref, signal, at in rows:
            if signal in NEUTRAL_SIGNALS:
                continue
            if ref.startswith(('topic:', 'refl:')):
                subject = ref
            else:
                subject = item_type or 'card'
            s = subjects.setdefault(
                subject, {'positive': 0, 'negative': 0, 'last': ''})
            if signal in POSITIVE_SIGNALS:
                s['positive'] += 1
                pos += 1
            elif signal in NEGATIVE_SIGNALS:
                s['negative'] += 1
                neg += 1
            else:
                continue
            if (at or '') > s['last']:
                s['last'] = at or ''

        def score(p: int, n: int, smooth: int) -> float:
            return max(0.05, min(0.95,
                                 0.5 + 0.5 * (p - n) / (p + n + smooth)))

        for s in subjects.values():
            s['score'] = round(score(s['positive'], s['negative'], 4), 3)
        openness = round(score(pos, neg, 6), 3)

        cur.execute('''
            INSERT INTO growth_receptivity (user_id, openness,
                                            sensitivity_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                openness = excluded.openness,
                sensitivity_json = excluded.sensitivity_json,
                updated_at = excluded.updated_at
        ''', (user_id, openness, json.dumps(subjects),
              datetime.now().isoformat()))
        self.db.commit()
        return {'openness': openness, 'sensitivity': subjects,
                'source': 'learned'}

    # ------------------------------------------------------------------
    # Delivery calibration — hold/seed/lead/propose/show
    # ------------------------------------------------------------------
    def delivery_strategy(self, reflection: Dict,
                          receptivity: Dict) -> tuple:
        """(strategy, reason) for a reflection under learned receptivity.

        Push strategies only — 'show' is the pull path and is never chosen
        here. A resolved reflection (confirmed/corrected/dismissed) stays
        out of the push rotation regardless of openness.
        """
        status = reflection.get('status') or 'hold'
        if status in ('confirmed', 'corrected', 'dismissed'):
            return 'done', f'status is {status}'
        o = (receptivity or {}).get('openness', 0.5)
        sens = reflection.get('sensitivity') or 'medium'
        need = PROPOSE_OPENNESS.get(sens, 0.65)
        if o >= need:
            return 'propose', f'openness {o} >= {need} for {sens} sensitivity'
        if sens == 'high':
            return 'hold', (f'high sensitivity needs openness >= 0.85 '
                            f'to lead, never to propose (openness {o})')
        if o >= 0.4:
            return 'seed', (f'openness {o} below propose threshold {need}; '
                            'observation only, no conclusion')
        return 'hold', f'openness {o} too low for {sens} sensitivity'

    def _propose_card(self, user_id: int,
                      receptivity: Dict) -> Optional[Dict]:
        """At most one 'propose' card: the gentlest reflection whose
        strategy clears the ladder and which wasn't surfaced recently."""
        self._ensure_tables()
        cutoff = (datetime.now()
                  - timedelta(days=PROPOSE_RESURFACE_DAYS)).isoformat()
        cur = self.db.cursor()
        try:
            cur.execute('''
                SELECT item_ref, created_at FROM growth_feedback
                WHERE user_id = ? AND signal = 'surfaced'
                  AND item_ref LIKE 'refl:%'
            ''', (user_id,))
            surfaced = {r[0]: r[1] for r in cur.fetchall()}
        except Exception:
            surfaced = {}
        rank = {'low': 0, 'medium': 1, 'high': 2}
        for ref in sorted(self._reflections(user_id),
                          key=lambda r: (rank.get(r['sensitivity'], 1),
                                         r['updated_at'])):
            strategy, _ = self.delivery_strategy(ref, receptivity)
            if strategy != 'propose':
                continue
            ref_id = f"refl:{ref['id']}"
            if (surfaced.get(ref_id) or '') > cutoff:
                continue
            return {
                'id': ref_id, 'type': 'propose',
                'title': 'Something I noticed',
                'text': f"{ref['claim']} — does that ring true?",
                'kind': 'observation',
            }
        return None

    # ------------------------------------------------------------------
    # Feed — deterministic card assembly (facts only, never reflections)
    # ------------------------------------------------------------------
    def build_feed(self, user_id: int) -> List[Dict]:
        """Cards for the /grow feed, ordered by the ranking policy in
        docs/growth_companion.md: open loops (engagement chips) first, then
        due habits, then check-in, then wins, then learning topics, then —
        last and most delicate — at most one calibrated 'propose' card
        carrying a reflection the user is ready to hear. Reflections only
        ever reach the feed through that ladder; nothing raw is shown.
        Every card carries an id so feedback signals can reference it."""
        uid = str(user_id)
        cards: List[Dict] = []

        # 1. Open loops — engagement candidates ('Track this?') then due threads
        try:
            from ai_compare import engagement
            for chip in engagement.suggestions(uid):
                cards.append({
                    'id': f"eng:{chip.get('thread_id')}",
                    'type': chip.get('type', 'thread'),
                    'title': chip.get('title', ''),
                    'text': chip.get('text', ''),
                    'kind': chip.get('kind', ''),
                    'thread_id': chip.get('thread_id'),
                    'replies': chip.get('replies') or [],
                    'url': chip.get('url'),
                })
        except Exception as e:
            print(f"[GrowthEngine] feed engagement error: {e}")

        habits = self._habit_summary(user_id)

        # 2. Due-today habits — one card, one Done button each
        due = [h for h in (habits.get('active_habits') or [])
               if h['name'] in (habits.get('due_today') or [])]
        if due:
            cards.append({
                'id': 'habits:due_today', 'type': 'habits_due',
                'title': 'Due today', 'text': '',
                'habits': [{'id': h['id'], 'name': h['name']} for h in due],
            })

        # 3. Mood check-in if none today
        recent = habits.get('recent_checkins') or []
        today = datetime.now().date().isoformat()
        if not any(c.get('date') == today for c in recent):
            cards.append({
                'id': 'checkin:today', 'type': 'checkin',
                'title': 'How are you today?',
                'text': 'One word is enough.',
                'replies': ['Great', 'Good', 'Okay', 'Low', 'Bad'],
            })

        # 4. Win card — strongest active streak
        streaks = habits.get('current_streaks') or {}
        if streaks:
            name, streak = max(streaks.items(), key=lambda kv: kv[1])
            if streak >= 7:
                cards.append({
                    'id': f"win:{name}", 'type': 'win',
                    'title': f'{streak}-day streak',
                    'text': f'"{name}" — that is consistency, not luck.',
                })

        # Receptivity learning runs here (cheap, deterministic) — the
        # feedback loop tunes both topic surfacing and the propose ladder.
        try:
            receptivity = self.learn_receptivity(user_id)
        except Exception as e:
            print(f"[GrowthEngine] receptivity error: {e}")
            receptivity = {}

        # 5. Topic card — the learning topic furthest along that hasn't been
        # surfaced recently or suppressed by its own feedback score.
        try:
            self.derive_topics(user_id)
            topic_card = self._topic_card(user_id, receptivity)
            if topic_card:
                cards.append(topic_card)
                self.record_feedback(user_id, 'topic',
                                     topic_card['id'][len('topic:'):],
                                     'surfaced')
        except Exception as e:
            print(f"[GrowthEngine] feed topic error: {e}")

        # 6. Propose card — the one place a reflection may reach the user:
        # only when the ladder says 'propose', throttled, and always with
        # confirm/correct/not-now replies (the calibration loop).
        try:
            propose = self._propose_card(user_id, receptivity)
            if propose:
                cards.append(propose)
                self.record_feedback(user_id, 'refl', propose['id'],
                                     'surfaced')
        except Exception as e:
            print(f"[GrowthEngine] feed propose error: {e}")

        # 6. Starter card — first for a brand-new user (the seed question is
        # the designed cold start), or the fallback when nothing else exists.
        explicit = self._explicit_items(user_id)
        profile = self._profile(user_id)
        is_new = (not explicit and not (habits.get('active_habits'))
                  and not (profile.get('total_interactions') or 0))
        starter = {
            'id': 'starter', 'type': 'starter',
            'title': 'Start here',
            'text': 'Tell me one thing you are working on or thinking '
                    'about lately — that is all it takes to begin.',
        }
        if is_new:
            cards.insert(0, starter)
        elif not cards:
            cards.append(starter)
        return cards

    # ------------------------------------------------------------------
    # Inspector payload — the admin/dev window into the private model
    # ------------------------------------------------------------------
    def _reflections(self, user_id: int) -> List[Dict]:
        self._ensure_tables()
        cur = self.db.cursor()
        cur.execute('''
            SELECT id, claim_key, claim, sensitivity, status, evidence_json,
                   trigger_text, delivery_log, source, created_at, updated_at
            FROM growth_reflections WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        out = []
        for r in cur.fetchall():
            out.append({
                'id': r[0], 'claim_key': r[1], 'claim': r[2],
                'sensitivity': r[3], 'status': r[4],
                'evidence': json.loads(r[5] or '[]'),
                'trigger': r[6], 'delivery_log': json.loads(r[7] or '[]'),
                'source': r[8], 'created_at': r[9], 'updated_at': r[10],
            })
        return out

    def _receptivity(self, user_id: int) -> Dict:
        self._ensure_tables()
        cur = self.db.cursor()
        cur.execute('SELECT openness, sensitivity_json, updated_at '
                    'FROM growth_receptivity WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        if not row:
            return {'openness': 0.5, 'sensitivity': {}, 'source': 'default'}
        return {'openness': row[0], 'sensitivity': json.loads(row[1] or '{}'),
                'updated_at': row[2], 'source': 'learned'}

    def _feedback(self, user_id: int, limit: int = 50) -> List[Dict]:
        self._ensure_tables()
        cur = self.db.cursor()
        cur.execute('''
            SELECT item_type, item_ref, signal, detail, created_at
            FROM growth_feedback WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        ''', (user_id, limit))
        return [
            {'item_type': r[0], 'item_ref': r[1], 'signal': r[2],
             'detail': r[3], 'at': r[4]}
            for r in cur.fetchall()
        ]

    def record_feedback(self, user_id: int, item_type: str, item_ref: str,
                        signal: str, detail: str = ''):
        self._ensure_tables()
        cur = self.db.cursor()
        cur.execute('''
            INSERT INTO growth_feedback (user_id, item_type, item_ref, signal, detail)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, item_type, item_ref, signal, detail))
        # Topic cards arrive as item_type='card', item_ref='topic:<name>' —
        # normalise so both spellings hit the same handling.
        topic = ''
        if item_type == 'topic':
            topic = item_ref
        elif item_ref.startswith('topic:'):
            topic = item_ref[len('topic:'):]
        if topic:
            if signal in ('dismissed', 'not_for_me'):
                cur.execute('''
                    UPDATE growth_topics SET dismissed = 1, updated_at = ?
                    WHERE user_id = ? AND topic = ?
                ''', (datetime.now().isoformat(), user_id, topic))
            elif signal in TOPIC_ENGAGED_SIGNALS:
                # Embodied engagement advances the stage immediately — the
                # signal is the evidence, not a later batch pass.
                cur.execute('''
                    SELECT id, stage FROM growth_topics
                    WHERE user_id = ? AND topic = ?
                ''', (user_id, topic))
                row = cur.fetchone()
                if row and row[1] < 3:
                    cur.execute('''
                        UPDATE growth_topics SET stage = 3,
                            stage_trigger = ?, updated_at = ?
                        WHERE id = ?
                    ''', ('user engaged with the topic card',
                          datetime.now().isoformat(), row[0]))
        elif item_ref.startswith('refl:'):
            # A propose-card response. The user's word is last: confirm,
            # correct and dismiss all land on the reflection's status, and
            # every response is appended to its delivery_log.
            try:
                ref_id = int(item_ref[len('refl:'):])
            except ValueError:
                ref_id = 0
            if ref_id and signal != 'surfaced':
                new_status = {
                    'confirm': 'confirmed', 'confirmed': 'confirmed',
                    'correct': 'corrected', 'corrected': 'corrected',
                    'dismissed': 'dismissed', 'not_for_me': 'dismissed',
                }.get(signal)
                cur.execute('''
                    SELECT status, delivery_log FROM growth_reflections
                    WHERE id = ? AND user_id = ?
                ''', (ref_id, user_id))
                row = cur.fetchone()
                if row:
                    log = json.loads(row[1] or '[]')
                    log.append({'signal': signal,
                                'at': datetime.now().isoformat()})
                    if new_status and row[0] != new_status:
                        cur.execute('''
                            UPDATE growth_reflections SET status = ?,
                                delivery_log = ?, updated_at = ?
                            WHERE id = ?
                        ''', (new_status, json.dumps(log),
                              datetime.now().isoformat(), ref_id))
                    else:
                        cur.execute('''
                            UPDATE growth_reflections SET delivery_log = ?,
                                updated_at = ? WHERE id = ?
                        ''', (json.dumps(log),
                              datetime.now().isoformat(), ref_id))
        self.db.commit()

    def inspector_payload(self, user_id: int) -> Dict:
        """Everything the app privately models about a user — admin view."""
        state = self.growth_state(user_id)
        try:
            receptivity = self.learn_receptivity(user_id)
        except Exception:
            receptivity = self._receptivity(user_id)
        reflections = self._reflections(user_id)
        for r in reflections:
            strategy, reason = self.delivery_strategy(r, receptivity)
            r['strategy'] = strategy
            r['strategy_reason'] = reason
        state['reflections'] = reflections
        state['receptivity'] = receptivity
        state['feedback'] = self._feedback(user_id)
        return state


# ---------------------------------------------------------------------------
# Singleton accessor (same pattern as get_habit_tracker etc.)
# ---------------------------------------------------------------------------
_instance: Optional[GrowthEngine] = None


def get_growth_engine(db_connection=None, habit_tracker=None,
                      profiler=None) -> GrowthEngine:
    global _instance
    if _instance is None:
        _instance = GrowthEngine(db_connection, habit_tracker, profiler)
    return _instance
