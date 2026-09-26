"""Tests for ai_compare/engagement.py — open loops, the deterministic picker,
and the /api/engagement/* routes.

Every test monkeypatches engagement.DB_PATH to a tmp file so the real
engagement.db is never touched.
"""
import json
from datetime import datetime, timedelta

import pytest

from ai_compare import engagement


@pytest.fixture()
def db(tmp_path, monkeypatch):
    p = tmp_path / 'engagement.db'
    monkeypatch.setattr(engagement, 'DB_PATH', p)
    return p


# ---------------------------------------------------------------------------
# Detection & seeding
# ---------------------------------------------------------------------------

def test_detect_commitment_and_decision(db):
    found = dict(engagement.detect_candidates(
        "I started running on Tuesdays. I'm thinking about switching jobs."))
    assert 'commitment' in found
    assert 'decision' in found
    assert 'running' in found['commitment']
    assert 'switching jobs' in found['decision']


def test_detect_ignores_plain_text(db):
    assert engagement.detect_candidates("hello, how are you today?") == []
    assert engagement.detect_candidates("") == []
    assert engagement.detect_candidates(None) == []


def test_seed_creates_candidates_not_threads(db):
    ids = engagement.seed_from_message('u1', "I will start meditating daily")
    assert len(ids) == 1
    t = engagement.list_threads('u1')[0]
    assert t['pending_suggestion'] is True
    assert t['kind'] == 'commitment'
    # Pending candidates never prompt — even with no quiet-window history.
    assert engagement.pick_due_prompt('u1') is None


def test_seed_dedupes_against_open_threads(db):
    engagement.seed_from_message('u1', "I will start meditating daily")
    again = engagement.seed_from_message('u1', "I will start meditating daily")
    assert again == []
    assert len(engagement.list_threads('u1')) == 1


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def test_confirm_answer_done(db):
    tid = engagement.create_thread('u1', 'run Tuesday', kind='commitment',
                                   candidate=True)
    t = engagement.confirm_candidate('u1', tid)
    assert t['pending_suggestion'] is False
    assert t['next_due_at'] is not None

    t = engagement.answer_thread('u1', tid, 'done', quick=True)
    assert t['status'] == 'done'
    assert t['answers'][-1]['text'] == 'done'


def test_answer_not_yet_rearms(db):
    tid = engagement.create_thread('u1', 'run Tuesday', kind='commitment')
    t = engagement.answer_thread('u1', tid, 'not yet', quick=True)
    assert t['status'] == 'open'
    assert t['next_due_at'] is not None


def test_snooze_suppresses_picker(db):
    tid = engagement.create_thread('u1', 'run Tuesday', kind='commitment',
                                   cadence_hours=0)
    engagement.snooze_thread('u1', tid, days=3)
    assert engagement.pick_due_prompt('u1') is None
    assert engagement.list_threads('u1')[0]['status'] == 'snoozed'


def test_drop_and_reopen(db):
    tid = engagement.create_thread('u1', 'x', kind='custom')
    engagement.drop_thread('u1', tid)
    assert engagement.list_threads('u1') == []  # dropped threads hidden
    t = engagement.reopen_thread('u1', tid)
    assert t['status'] == 'open'
    assert engagement.list_threads('u1', include_closed=True)


def test_dismiss_candidate_drops(db):
    tid = engagement.create_thread('u1', 'x', kind='custom', candidate=True)
    engagement.dismiss_candidate('u1', tid)
    t = engagement.list_threads('u1', include_closed=True)[0]
    assert t['status'] == 'dropped'


def test_other_users_threads_invisible(db):
    engagement.create_thread('u1', 'mine')
    assert engagement.list_threads('u2') == []
    assert engagement.confirm_candidate('u2',
        engagement.list_threads('u1')[0]['id']) is None


# ---------------------------------------------------------------------------
# Picker — quiet window, decay, self-snooze
# ---------------------------------------------------------------------------

def test_pick_due_prompt_quotes_subject(db):
    engagement.create_thread('u1', 'start running Tuesday', kind='commitment',
                             cadence_hours=0)
    p = engagement.pick_due_prompt('u1')
    assert p is not None
    assert 'start running Tuesday' in p['prompt']['text']
    assert p['prompt']['replies']


def test_quiet_window_blocks_second_prompt(db):
    engagement.create_thread('u1', 'a', kind='commitment', cadence_hours=0)
    engagement.create_thread('u1', 'b', kind='decision', cadence_hours=0)
    first = engagement.pick_due_prompt('u1')
    assert first is not None
    # Second pick inside the quiet window → silence.
    assert engagement.pick_due_prompt('u1') is None


def test_prompt_reschedules_thread(db):
    tid = engagement.create_thread('u1', 'a', kind='commitment',
                                   cadence_hours=0)
    engagement.pick_due_prompt('u1')
    t = engagement.list_threads('u1')[0]
    assert t['prompt_count'] == 1
    # Rescheduled into the future — not due again immediately.
    assert datetime.fromisoformat(t['next_due_at']) > datetime.now()


def test_self_snooze_after_max_prompts(db):
    tid = engagement.create_thread('u1', 'a', kind='commitment',
                                   cadence_hours=0)
    conn = engagement._conn()
    try:
        # Simulate MAX_UNANSWERED prompts already sent.
        conn.execute('UPDATE threads SET prompt_count=? WHERE id=?',
                     (engagement.MAX_UNANSWERED_PROMPTS, tid))
        conn.commit()
    finally:
        conn.close()
    assert engagement.pick_due_prompt('u1') is None
    t = engagement.list_threads('u1')[0]
    assert t['status'] == 'snoozed'


def test_higher_priority_kind_wins(db):
    engagement.create_thread('u1', 'habit thing', kind='habit', cadence_hours=0)
    engagement.create_thread('u1', 'health thing', kind='health', cadence_hours=0)
    p = engagement.pick_due_prompt('u1')
    assert 'health' in p['kind']


def test_suggestions_caps_and_orders(db):
    engagement.create_thread('u1', 'c1', kind='custom', candidate=True)
    engagement.create_thread('u1', 'due1', kind='commitment', cadence_hours=0)
    chips = engagement.suggestions('u1')
    assert len(chips) <= 3
    assert chips[0]['type'] == 'candidate'
    assert any(c['type'] == 'thread' for c in chips)


# ---------------------------------------------------------------------------
# Prompt-context block
# ---------------------------------------------------------------------------

def test_threads_block_for_prompt(db):
    engagement.create_thread('u1', 'start running', kind='commitment')
    block = engagement.threads_block_for_prompt('u1')
    assert 'OPEN LOOPS' in block
    assert 'start running' in block
    assert engagement.threads_block_for_prompt('u-empty') == ''


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

def _client(monkeypatch, tmp_path):
    import app as app_mod
    monkeypatch.setattr(engagement, 'DB_PATH', tmp_path / 'engagement.db')
    app_mod.app.config['TESTING'] = True
    client = app_mod.app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 4242
        sess['username'] = 'engagement-test'
    return client


def test_api_suggestions_and_thread_actions(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    engagement.create_thread('4242', 'run Tuesday', kind='commitment',
                             candidate=True)

    r = client.get('/api/engagement/suggestions')
    assert r.status_code == 200
    chips = r.get_json()['chips']
    assert chips and chips[0]['type'] == 'candidate'
    tid = chips[0]['thread_id']

    r = client.post(f'/api/engagement/threads/{tid}/confirm')
    assert r.status_code == 200
    assert r.get_json()['thread']['pending_suggestion'] is False

    r = client.post(f'/api/engagement/threads/{tid}/answer',
                    json={'answer': 'done', 'quick': True})
    assert r.get_json()['thread']['status'] == 'done'

    r = client.post(f'/api/engagement/threads/{tid}/bogus')
    assert r.status_code == 404


def test_api_threads_lists_open_only(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    engagement.create_thread('4242', 'a')
    tid2 = engagement.create_thread('4242', 'b')
    engagement.drop_thread('4242', tid2)
    r = client.get('/api/engagement/threads')
    subjects = [t['subject'] for t in r.get_json()['threads']]
    assert 'a' in subjects and 'b' not in subjects


def test_api_push_subscription_roundtrip(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    sub = {'endpoint': 'https://push.example.com/x',
           'keys': {'p256dh': 'k', 'auth': 'a'}}
    r = client.post('/api/push-subscription', json={'subscription': sub})
    assert r.status_code == 200
    assert engagement.push_subscriptions_for('4242')
    r = client.delete('/api/push-subscription',
                      json={'endpoint': sub['endpoint']})
    assert r.status_code == 200
    assert engagement.push_subscriptions_for('4242') == []

    r = client.post('/api/push-subscription', json={'endpoint': 'not-https'})
    assert r.status_code == 400


def test_engagement_routes_require_auth(monkeypatch, tmp_path):
    import app as app_mod
    app_mod.app.config['TESTING'] = True
    client = app_mod.app.test_client()
    assert client.get('/api/engagement/suggestions').status_code == 401
    assert client.get('/api/engagement/threads').status_code == 401


def test_companion_page_registered():
    import app as app_mod
    app_mod.app.config['TESTING'] = True
    client = app_mod.app.test_client()
    r = client.get('/companion')
    assert r.status_code == 200
    assert b'Milo' in r.data
