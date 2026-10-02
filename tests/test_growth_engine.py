"""Tests for smart_response/growth_engine.py — Phase 0 machinery.

Covers:
- growth_state() assembles facts from existing modules (habits,
  explicit_context, companion profile, engagement threads)
- derive_reflections() produces evidence-linked, sensitivity-tagged
  candidate insights, all status='hold'
- derivation is idempotent (claim_key dedup; re-runs update, not duplicate)
- commitments view tags top_down / adaptive / bottom_up modes
- admin-gating on the inspector endpoints

Run: python -m pytest tests/test_growth_engine.py -v
"""
import json
import sqlite3
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from smart_response.habit_tracker import HabitTracker
from smart_response.life_companion_profile import (
    LifeCompanionProfiler, CompanionProfile, DomainStatus,
)
from smart_response.growth_engine import GrowthEngine


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Engine + collaborators on a throwaway DB; engagement pointed at tmp."""
    db = sqlite3.connect(str(tmp_path / 'growth.db'))
    # explicit_context schema mirrors ExplicitContextHandler._init_tables —
    # the handler itself pulls in the personality interpreter, too heavy for
    # a unit fixture.
    db.execute('''CREATE TABLE explicit_context (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        character TEXT NOT NULL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        context_type TEXT NOT NULL, context_key TEXT NOT NULL,
        context_value TEXT NOT NULL, original_statement TEXT NOT NULL,
        priority TEXT NOT NULL, confidence FLOAT DEFAULT 1.0,
        active BOOLEAN DEFAULT 1, expires_at TIMESTAMP, extracted_via TEXT)''')
    db.commit()
    from ai_compare import engagement
    monkeypatch.setattr(engagement, 'DB_PATH', tmp_path / 'engagement.db')
    habits = HabitTracker(db)
    profiler = LifeCompanionProfiler(db)
    engine = GrowthEngine(db, habits, profiler)
    return SimpleNamespace(db=db, habits=habits, profiler=profiler,
                           engine=engine)


def _insert_explicit(db, user_id, ctype, value, statement, days_ago=0,
                     active=1):
    ts = (datetime.now() - timedelta(days=days_ago)).isoformat()
    db.execute('''INSERT INTO explicit_context
        (user_id, character, timestamp, context_type, context_key,
         context_value, original_statement, priority, active)
        VALUES (?, 'general', ?, ?, ?, ?, ?, 'NORMAL', ?)''',
        (user_id, ts, ctype, 'k', value, statement, active))
    db.commit()


def _insert_checkins(db, user_id, scores):
    for i, s in enumerate(scores):
        db.execute('''INSERT INTO daily_checkins
            (user_id, check_date, mood, mood_score)
            VALUES (?, ?, 'low', ?)''',
            (user_id, (datetime.now() - timedelta(days=i)).date().isoformat(), s))
    db.commit()


# --- unified state ---------------------------------------------------------

def test_growth_state_assembles_facts(env):
    env.habits.create_habit(7, 'Walk', category='health')
    _insert_explicit(env.db, 7, 'goal', 'run a 5k', 'I want to run a 5k')
    state = env.engine.growth_state(7)
    assert [c['label'] for c in state['commitments']
            if c['source'] == 'explicit'] == ['run a 5k']
    assert any(c['source'] == 'habit' and c['mode'] == 'top_down'
               for c in state['commitments'])
    assert any(c['mode'] == 'bottom_up' for c in state['commitments'])
    assert state['habits']['active_habits'][0]['name'] == 'Walk'
    assert state['explicit'][0]['value'] == 'run a 5k'


# --- reflection derivation -------------------------------------------------

def test_stale_goal_reflection(env):
    _insert_explicit(env.db, 7, 'goal', 'learn piano',
                     'I want to learn piano', days_ago=30)
    res = env.engine.derive_reflections(7)
    assert res['created'] == 1
    refs = env.engine._reflections(7)
    r = refs[0]
    assert 'learn piano' in r['claim']
    assert r['status'] == 'hold'          # calibrated away until delivery logic
    assert r['sensitivity'] == 'medium'
    assert r['evidence'][0]['source'] == 'explicit_context'
    assert r['trigger']


def test_fresh_goal_not_stale(env):
    _insert_explicit(env.db, 7, 'goal', 'learn piano',
                     'I want to learn piano', days_ago=5)
    res = env.engine.derive_reflections(7)
    assert res['created'] == 0


def test_habit_low_completion_reflection(env):
    env.habits.create_habit(7, 'Meditate', category='mindfulness')
    env.engine.derive_reflections(7)
    keys = [r['claim_key'] for r in env.engine._reflections(7)]
    assert any(k.startswith('habit_low:') for k in keys)


def test_stated_vs_observed_divergence(env):
    env.habits.create_habit(7, 'Gym', category='health')
    _insert_explicit(env.db, 7, 'value', 'health matters',
                     'My health matters to me')
    env.engine.derive_reflections(7)
    div = [r for r in env.engine._reflections(7)
           if r['claim_key'].startswith('divergence:')]
    assert div and div[0]['sensitivity'] == 'high'
    assert len(div[0]['evidence']) == 2


def test_mood_declining_reflection(env):
    _insert_checkins(env.db, 7, [1, 2, 1, 2])
    env.engine.derive_reflections(7)
    mood = [r for r in env.engine._reflections(7)
            if r['claim_key'] == 'mood_declining']
    assert mood and mood[0]['sensitivity'] == 'high'


def test_guarded_trust_reflection(env):
    p = CompanionProfile(user_id=7)
    p.trust_level = 0.1
    p.total_interactions = 25
    env.profiler._save_profile(7, p)
    env.engine.derive_reflections(7)
    assert any(r['claim_key'] == 'guarded_trust'
               for r in env.engine._reflections(7))


def test_domain_struggle_reflection(env):
    p = CompanionProfile(user_id=7)
    p.life_domains['work'] = DomainStatus(
        domain='work', sentiment='negative', mention_count=5,
        trajectory='declining')
    env.profiler._save_profile(7, p)
    env.engine.derive_reflections(7)
    assert any(r['claim_key'] == 'domain_struggle:work'
               for r in env.engine._reflections(7))


def test_derive_idempotent(env):
    _insert_explicit(env.db, 7, 'goal', 'learn piano',
                     'I want to learn piano', days_ago=30)
    first = env.engine.derive_reflections(7)
    second = env.engine.derive_reflections(7)
    assert first['created'] == 1
    assert second['created'] == 0 and second['updated'] >= 1
    assert len(env.engine._reflections(7)) == 1


# --- inspector payload -----------------------------------------------------

def test_inspector_includes_private_model(env):
    _insert_explicit(env.db, 7, 'goal', 'x', 'stated x', days_ago=40)
    env.engine.derive_reflections(7)
    payload = env.engine.inspector_payload(7)
    assert payload['reflections']
    assert payload['receptivity']['source'] == 'default'
    assert 'commitments' in payload and 'topics' in payload


def test_feedback_recording(env):
    env.engine.record_feedback(7, 'reflection', 'stale_goal:1', 'dismissed',
                               'not relevant')
    fb = env.engine._feedback(7)
    assert fb[0]['signal'] == 'dismissed'


# --- admin gating (app routes) ----------------------------------------------

def test_inspector_endpoints_require_admin(env, monkeypatch):
    import app as app_mod
    app_mod.app.config['TESTING'] = True
    client = app_mod.app.test_client()

    with client.session_transaction() as sess:
        sess['user_id'] = 99
        sess['username'] = 'plain-user'
    monkeypatch.setattr(app_mod.integrated_db, 'get_user_role',
                        lambda uid: 'user')
    r = client.get('/api/growth/insights/1')
    assert r.status_code == 403
    r = client.post('/api/growth/insights/1/derive')
    assert r.status_code == 403

    # Inject the fixture engine — app.py's own init may have aborted on a
    # locked integrated_users.db, which is unrelated to what this tests.
    monkeypatch.setattr(app_mod, 'growth_engine', env.engine)
    monkeypatch.setattr(app_mod.integrated_db, 'get_user_role',
                        lambda uid: 'administrator')
    r = client.get('/api/growth/insights/7')
    assert r.status_code == 200
    body = r.get_json()
    assert body['success'] is True
    assert 'reflections' in body['state']


def test_growth_state_requires_auth():
    import app as app_mod
    app_mod.app.config['TESTING'] = True
    client = app_mod.app.test_client()
    r = client.get('/api/growth/state')
    assert r.status_code == 401


# --- feed ------------------------------------------------------------------

def test_feed_starter_first_for_new_user(env):
    cards = env.engine.build_feed(999)
    assert cards[0]['type'] == 'starter'


def test_feed_no_starter_for_established_user(env):
    env.habits.create_habit(7, 'Walk', category='health')
    p = CompanionProfile(user_id=7)
    p.total_interactions = 20
    env.profiler._save_profile(7, p)
    cards = env.engine.build_feed(7)
    assert cards[0]['type'] != 'starter'


def test_feed_orders_loops_first(env):
    import sqlite3 as _sq
    from ai_compare import engagement
    env.habits.create_habit(7, 'Walk', category='health')   # due today
    tid = engagement.create_thread('7', 'call accountant', kind='commitment')
    # make the thread due now
    conn = _sq.connect(str(engagement.DB_PATH))  # monkeypatched to tmp by env
    conn.execute("UPDATE threads SET next_due_at=? WHERE id=?",
                 ((datetime.now() - timedelta(hours=1)).isoformat(), tid))
    conn.commit(); conn.close()
    cards = env.engine.build_feed(7)
    types = [c['type'] for c in cards]
    assert types.index('thread') < types.index('habits_due')
    assert 'checkin' in types


def test_feed_win_card(env):
    h = env.habits.create_habit(7, 'Run', category='health')
    env.db.execute('UPDATE habits SET current_streak=?, best_streak=? WHERE id=?',
                   (9, 9, h.id))
    env.db.commit()
    _insert_checkins(env.db, 7, [4])  # has today's check-in → no checkin card
    cards = env.engine.build_feed(7)
    assert any(c['type'] == 'win' and '9-day' in c['title'] for c in cards)


def test_feed_includes_candidate_chip(env):
    from ai_compare import engagement
    engagement.create_thread('7', 'meditation habit', kind='habit',
                             candidate=True)
    cards = env.engine.build_feed(7)
    assert any(c['type'] == 'candidate' and c['thread_id'] for c in cards)


# --- new endpoints ---------------------------------------------------------

def test_feedback_endpoint(env, monkeypatch):
    import app as app_mod
    app_mod.app.config['TESTING'] = True
    monkeypatch.setattr(app_mod, 'growth_engine', env.engine)
    client = app_mod.app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 7
    r = client.post('/api/growth/feedback',
                    json={'item_type': 'card', 'item_ref': 'win:Run',
                          'signal': 'landed'})
    assert r.status_code == 200
    fb = env.engine._feedback(7)
    assert fb[0]['signal'] == 'landed' and fb[0]['item_ref'] == 'win:Run'


def test_fact_correct_endpoint(env, monkeypatch):
    import app as app_mod
    from smart_response.explicit_context_handler import ExplicitContextHandler
    monkeypatch.setattr(ExplicitContextHandler, '__init__',
                        lambda self, conn: setattr(self, 'db', conn))
    handler = ExplicitContextHandler.__new__(ExplicitContextHandler)
    handler.db = env.db
    app_mod.app.config['TESTING'] = True
    monkeypatch.setattr(app_mod, 'growth_engine', env.engine)
    monkeypatch.setattr(app_mod, 'explicit_context_handler', handler)
    client = app_mod.app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 7
    _insert_explicit(env.db, 7, 'goal', 'learn piano', 'I want to learn piano')
    cid = env.db.execute('SELECT id FROM explicit_context LIMIT 1').fetchone()[0]
    r = client.post(f'/api/growth/facts/{cid}/correct', json={})
    assert r.status_code == 200
    active = env.db.execute('SELECT active FROM explicit_context WHERE id=?',
                            (cid,)).fetchone()[0]
    assert active == 0
    assert env.engine._feedback(7)[0]['signal'] == 'corrected'


def test_feed_endpoint_auth(env, monkeypatch):
    import app as app_mod
    app_mod.app.config['TESTING'] = True
    monkeypatch.setattr(app_mod, 'growth_engine', env.engine)
    client = app_mod.app.test_client()
    assert client.get('/api/growth/feed').status_code == 401
    with client.session_transaction() as sess:
        sess['user_id'] = 7
    r = client.get('/api/growth/feed')
    assert r.status_code == 200 and 'cards' in r.get_json()
