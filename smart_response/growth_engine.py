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
    # Feed — deterministic card assembly (facts only, never reflections)
    # ------------------------------------------------------------------
    def build_feed(self, user_id: int) -> List[Dict]:
        """Cards for the /grow feed, ordered by the ranking policy in
        docs/growth_companion.md: open loops (engagement chips) first, then
        due habits, then check-in, then wins, then a starter prompt when
        there is nothing else. Every card carries an id so feedback signals
        can reference it."""
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

        # 5. Starter card — first for a brand-new user (the seed question is
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
        self.db.commit()

    def inspector_payload(self, user_id: int) -> Dict:
        """Everything the app privately models about a user — admin view."""
        state = self.growth_state(user_id)
        state['reflections'] = self._reflections(user_id)
        state['receptivity'] = self._receptivity(user_id)
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
