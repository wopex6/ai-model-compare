"""Engagement threads — the app's open loops with the user.

One entity underneath every "we were talking about X" moment: a commitment the
user made, a decision left pending, a health follow-up, a habit check-in.
Seeded deterministically from chat (never auto-opened — the user confirms a
candidate first), picked deterministically (never more than one prompt per
quiet window), and damped by what the user actually responds to.

Design rules (deliberate — see AGENTS.md):

- Deterministic triggers, optional AI wording. The picker only decides WHEN
  and WHAT thread; it never invents a subject. If nothing is due, it says
  nothing — silence is acceptable, generic is not.
- Every prompt names its source: "you told me X on Tuesday". No reason, no
  nag — that is the difference between relevant and creepy.
- Unanswered threads decay politely: the interval doubles, then the thread
  snoozes itself rather than nagging forever.
- Per-kind responsiveness is learned from the events log — a user who always
  answers health prompts but ignores habit ones gets more of the former,
  fewer of the latter. Simple counts, not a model.
"""

import json
import re
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / 'engagement.db'

# Rough pull strength of each kind, per the product discussion: things the
# user started beat things the system suggests.
KIND_PRIORITY = {
    'health': 5,
    'commitment': 4,
    'decision': 3,
    'habit': 2,
    'custom': 2,
}

# Base cadence between prompts on a thread, hours. Commitments ask soon after
# they were made; decisions can wait days.
KIND_CADENCE_HOURS = {
    'health': 72,
    'commitment': 24,
    'decision': 96,
    'habit': 24,
    'custom': 48,
}

MIN_USER_GAP_HOURS = 18       # never more than one prompt inside this window
MAX_UNANSWERED_PROMPTS = 3    # then the thread snoozes itself for a week
SELF_SNOOZE_DAYS = 7


def _conn(db_path=None):
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS threads (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        subject TEXT NOT NULL,
        detail TEXT DEFAULT '',
        owner TEXT DEFAULT 'companion',
        status TEXT DEFAULT 'open',
        pending_suggestion INTEGER DEFAULT 0,
        source TEXT DEFAULT 'user',
        created_at TEXT NOT NULL,
        last_prompted_at TEXT,
        prompt_count INTEGER DEFAULT 0,
        next_due_at TEXT,
        snooze_until TEXT,
        last_outcome TEXT,
        answers TEXT DEFAULT '[]'
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        thread_id TEXT,
        kind TEXT NOT NULL,
        detail TEXT DEFAULT '',
        at TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS push_subscriptions (
        user_id TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        keys_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (user_id, endpoint)
    )''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_threads_user ON threads(user_id, status)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id, at)')
    return conn


def _now():
    return datetime.now()


def _iso(dt=None):
    return (dt or _now()).isoformat()


def _log(user_id, kind, thread_id=None, detail='', conn=None):
    own = conn is None
    conn = conn or _conn()
    conn.execute(
        'INSERT INTO events (user_id, thread_id, kind, detail, at) VALUES (?,?,?,?,?)',
        (str(user_id), thread_id, kind, detail[:500], _iso()))
    if own:
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------

def create_thread(user_id, subject, kind='custom', detail='', owner='companion',
                  source='user', candidate=False, cadence_hours=None,
                  db_path=None):
    """Create a thread. candidate=True parks it as a 'Track this?' suggestion —
    it does not prompt until the user confirms it."""
    if kind not in KIND_PRIORITY:
        kind = 'custom'
    conn = _conn(db_path)
    try:
        tid = uuid.uuid4().hex[:16]
        cadence = cadence_hours if cadence_hours is not None else KIND_CADENCE_HOURS[kind]
        conn.execute('''INSERT INTO threads
            (id, user_id, kind, subject, detail, owner, status,
             pending_suggestion, source, created_at, next_due_at)
            VALUES (?,?,?,?,?,?, 'open', ?,?,?,?)''',
            (tid, str(user_id), kind, subject[:200], detail[:500], owner,
             1 if candidate else 0, source, _iso(),
             None if candidate else _iso(_now() + timedelta(hours=cadence))))
        _log(user_id, 'suggested' if candidate else 'created', tid,
             subject[:200], conn=conn)
        conn.commit()
        return tid
    finally:
        conn.close()


def _row_to_dict(row):
    d = dict(row)
    try:
        d['answers'] = json.loads(d.get('answers') or '[]')
    except (ValueError, TypeError):
        d['answers'] = []
    d['pending_suggestion'] = bool(d.get('pending_suggestion'))
    return d


def list_threads(user_id, include_closed=False, db_path=None):
    conn = _conn(db_path)
    try:
        q = 'SELECT * FROM threads WHERE user_id=?'
        args = [str(user_id)]
        if not include_closed:
            q += " AND status NOT IN ('done','dropped')"
        q += ' ORDER BY created_at DESC'
        return [_row_to_dict(r) for r in conn.execute(q, args)]
    finally:
        conn.close()


def _get(conn, user_id, thread_id):
    row = conn.execute(
        'SELECT * FROM threads WHERE id=? AND user_id=?',
        (thread_id, str(user_id))).fetchone()
    return _row_to_dict(row) if row else None


def _reschedule(thread, answered, conn, now=None):
    """Next prompt time from the base cadence, stretched by non-response."""
    now = now or _now()
    cadence = KIND_CADENCE_HOURS.get(thread['kind'], 48)
    unanswered = int(thread.get('prompt_count') or 0)
    # Each unanswered prompt doubles the wait; an answered one resets it.
    factor = 1 if answered else min(2 ** max(unanswered - 1, 0), 8)
    due = now + timedelta(hours=cadence * factor)
    conn.execute('UPDATE threads SET next_due_at=? WHERE id=?',
                 (_iso(due), thread['id']))
    thread['next_due_at'] = _iso(due)


def confirm_candidate(user_id, thread_id, db_path=None):
    """User accepted a 'Track this?' suggestion — it can now prompt."""
    conn = _conn(db_path)
    try:
        t = _get(conn, user_id, thread_id)
        if not t:
            return None
        cadence = KIND_CADENCE_HOURS.get(t['kind'], 48)
        conn.execute('''UPDATE threads SET pending_suggestion=0,
                        next_due_at=?, last_outcome='confirmed' WHERE id=?''',
                     (_iso(_now() + timedelta(hours=cadence)), thread_id))
        _log(user_id, 'confirmed', thread_id, conn=conn)
        conn.commit()
        return _get(conn, user_id, thread_id)
    finally:
        conn.close()


def dismiss_candidate(user_id, thread_id, db_path=None):
    """User declined a suggestion — drop it and learn the no."""
    return _set_status(user_id, thread_id, 'dropped', 'dismissed', db_path)


def answer_thread(user_id, thread_id, answer, quick=False, db_path=None):
    """Record the user's answer and close or re-arm the thread.

    Quick answers ('done','yes','no','not yet') are structured data — 'done'
    closes the thread, 'not yet' re-arms it. Free text re-arms; the user can
    close explicitly with the done action.
    """
    conn = _conn(db_path)
    try:
        t = _get(conn, user_id, thread_id)
        if not t:
            return None
        answers = list(t.get('answers') or [])
        answers.append({'at': _iso(), 'text': str(answer)[:500],
                        'quick': bool(quick)})
        answered = True
        new_status = 'open'
        if quick and str(answer).strip().lower() in ('done', 'yes'):
            new_status = 'done'
        conn.execute('''UPDATE threads SET answers=?, status=?,
                        last_outcome='answered', prompt_count=0 WHERE id=?''',
                     (json.dumps(answers), new_status, thread_id))
        _log(user_id, 'answered', thread_id, str(answer)[:200], conn=conn)
        if new_status == 'open':
            _reschedule(t, answered=True, conn=conn)
        conn.commit()
        return _get(conn, user_id, thread_id)
    finally:
        conn.close()


def _set_status(user_id, thread_id, status, event, db_path=None):
    conn = _conn(db_path)
    try:
        t = _get(conn, user_id, thread_id)
        if not t:
            return None
        conn.execute('UPDATE threads SET status=? WHERE id=?',
                     (status, thread_id))
        _log(user_id, event, thread_id, conn=conn)
        conn.commit()
        return _get(conn, user_id, thread_id)
    finally:
        conn.close()


def snooze_thread(user_id, thread_id, days=3, db_path=None):
    conn = _conn(db_path)
    try:
        t = _get(conn, user_id, thread_id)
        if not t:
            return None
        conn.execute('UPDATE threads SET status=?, snooze_until=? WHERE id=?',
                     ('snoozed', _iso(_now() + timedelta(days=days)), thread_id))
        _log(user_id, 'snoozed', thread_id, conn=conn)
        conn.commit()
        return _get(conn, user_id, thread_id)
    finally:
        conn.close()


def drop_thread(user_id, thread_id, db_path=None):
    return _set_status(user_id, thread_id, 'dropped', 'dropped', db_path)


def reopen_thread(user_id, thread_id, db_path=None):
    conn = _conn(db_path)
    try:
        t = _get(conn, user_id, thread_id)
        if not t:
            return None
        conn.execute('''UPDATE threads SET status='open', snooze_until=NULL,
                        prompt_count=0 WHERE id=?''', (thread_id,))
        _log(user_id, 'reopened', thread_id, conn=conn)
        _reschedule(t, answered=True, conn=conn)
        conn.commit()
        return _get(conn, user_id, thread_id)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Picker — decides whether anything is worth saying right now
# ---------------------------------------------------------------------------

def _responsiveness(conn, user_id, kind):
    """(answered or tapped) / prompted for this kind — smoothed. Returns a
    0.5–1.5 weight; new kinds start neutral."""
    row = conn.execute('''SELECT
        SUM(CASE WHEN e.kind='prompted' THEN 1 ELSE 0 END) AS prompted,
        SUM(CASE WHEN e.kind IN ('answered','confirmed','tapped') THEN 1 ELSE 0 END)
            AS engaged
        FROM events e JOIN threads t ON t.id = e.thread_id
        WHERE e.user_id=? AND t.kind=?''', (str(user_id), kind)).fetchone()
    prompted = row['prompted'] or 0
    engaged = row['engaged'] or 0
    if prompted < 3:
        return 1.0
    rate = (engaged + 1) / (prompted + 2)
    return 0.5 + rate  # 0.5 (never engages) .. 1.5 (always)


def _prompt_text(thread):
    """Deterministic wording — the subject is always quoted verbatim."""
    subject = thread['subject']
    when = (thread.get('created_at') or '')[:10]
    if thread['kind'] == 'decision':
        text = f'You were deciding about: {subject}'
        question = 'Did you land anywhere?'
        replies = ['Decided', 'Still thinking', 'Dropped it']
    elif thread['kind'] == 'commitment':
        text = f'You said: {subject}'
        question = 'How is it going?'
        replies = ['Done', 'Going well', 'Slipped', 'Not yet']
    elif thread['kind'] == 'health':
        text = f'Health follow-up: {subject}'
        question = 'Any update?'
        replies = ['Done', 'Still open', 'Not needed']
    elif thread['kind'] == 'habit':
        text = subject
        question = 'Done today?'
        replies = ['Done', 'Not yet', 'Skip']
    else:
        text = f'You mentioned: {subject}'
        question = 'Still on your mind?'
        replies = ['Done', 'Yes', 'Not anymore']
    return {'text': text, 'question': question, 'replies': replies,
            'since': when}


def pick_due_prompt(user_id, now=None, db_path=None):
    """The one prompt worth sending right now, or None.

    Rules: only open, non-candidate, due, un-snoozed threads; one per quiet
    window per user; auto-snooze a thread that has been ignored
    MAX_UNANSWERED_PROMPTS times.
    """
    now = now or _now()
    conn = _conn(db_path)
    try:
        # Per-user quiet window: any prompt sent recently suppresses the rest.
        last = conn.execute(
            "SELECT MAX(at) AS t FROM events WHERE user_id=? AND kind='prompted'",
            (str(user_id),)).fetchone()
        if last and last['t']:
            try:
                last_at = datetime.fromisoformat(last['t'])
                if (now - last_at).total_seconds() < MIN_USER_GAP_HOURS * 3600:
                    return None
            except ValueError:
                pass

        rows = conn.execute('''SELECT * FROM threads
            WHERE user_id=? AND status='open' AND pending_suggestion=0
            AND next_due_at IS NOT NULL AND next_due_at <= ?
            ORDER BY next_due_at''',
            (str(user_id), _iso(now))).fetchall()
        best = None
        for row in rows:
            t = _row_to_dict(row)
            if t.get('snooze_until'):
                try:
                    if datetime.fromisoformat(t['snooze_until']) > now:
                        continue
                except ValueError:
                    pass
            if int(t.get('prompt_count') or 0) >= MAX_UNANSWERED_PROMPTS:
                # Politely park it rather than ask a fourth time.
                conn.execute(
                    'UPDATE threads SET status=?, snooze_until=? WHERE id=?',
                    ('snoozed', _iso(now + timedelta(days=SELF_SNOOZE_DAYS)),
                     t['id']))
                _log(user_id, 'self_snoozed', t['id'], conn=conn)
                continue
            score = (KIND_PRIORITY.get(t['kind'], 1)
                     * _responsiveness(conn, user_id, t['kind']))
            t['_score'] = score
            if best is None or score > best['_score']:
                best = t
        if not best:
            conn.commit()
            return None

        conn.execute('''UPDATE threads SET last_prompted_at=?,
                        prompt_count=prompt_count+1, last_outcome='prompted'
                        WHERE id=?''', (_iso(now), best['id']))
        _log(user_id, 'prompted', best['id'], conn=conn)
        _reschedule(best, answered=False, conn=conn, now=now)
        conn.commit()
        out = dict(best)
        out['prompt'] = _prompt_text(best)
        return out
    finally:
        conn.close()


def pending_candidates(user_id, db_path=None):
    """'Track this?' chips — threads waiting for the user's yes/no."""
    conn = _conn(db_path)
    try:
        rows = conn.execute('''SELECT * FROM threads
            WHERE user_id=? AND pending_suggestion=1 AND status='open'
            ORDER BY created_at DESC LIMIT 5''', (str(user_id),)).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Deterministic seeding from chat text — candidates only, never auto-open.
# ---------------------------------------------------------------------------

_COMMITMENT_RE = re.compile(
    r"\b(i (?:started|begin|began|decided to|am going to|will|plan to|"
    r"promised myself|committed to)\b[^.!?]{3,80})",
    re.IGNORECASE)
_DECISION_RE = re.compile(
    r"\b(i(?:'m| am) (?:thinking about|considering|deciding|not sure (?:if|whether)|"
    r"weighing up|torn between)\b[^.!?]{3,80})",
    re.IGNORECASE)


def detect_candidates(text):
    """Cheap phrase detectors → [(kind, subject)]. Cheap is the point: a false
    positive only costs a 'Track this?' chip the user can dismiss; an LLM call
    per message costs money on every message."""
    found = []
    text = (text or '').strip()
    if not text or len(text) > 4000:
        return found
    for m in _COMMITMENT_RE.finditer(text):
        found.append(('commitment', m.group(1).strip()))
    for m in _DECISION_RE.finditer(text):
        found.append(('decision', m.group(1).strip()))
    # One of each per message is enough.
    seen = set()
    out = []
    for kind, subject in found:
        if kind not in seen:
            seen.add(kind)
            out.append((kind, subject))
    return out


def seed_from_message(user_id, message, db_path=None):
    """Create candidate threads from a user message. Dedupes against open
    threads so the same phrase doesn't spawn a second suggestion."""
    created = []
    if not message:
        return created
    existing = {t['subject'].lower() for t in list_threads(user_id, db_path=db_path)}
    for kind, subject in detect_candidates(message):
        if subject.lower() in existing:
            continue
        tid = create_thread(user_id, subject, kind=kind, source='chat_detect',
                            candidate=True, db_path=db_path)
        created.append(tid)
        existing.add(subject.lower())
    return created


# ---------------------------------------------------------------------------
# Suggestions — ambient chips for the dashboard, ranked and capped.
# ---------------------------------------------------------------------------

def suggestions(user_id, extras=None, db_path=None):
    """Chips for the home screen: pending 'Track this?' candidates first
    (they need a yes/no), then due threads. extras lets app.py append
    providers (decisions, health) without this module importing them."""
    chips = []
    for t in pending_candidates(user_id, db_path=db_path):
        chips.append({'type': 'candidate', 'thread_id': t['id'],
                      'title': 'Track this?',
                      'text': t['subject'],
                      'kind': t['kind']})
    now = _now()
    for t in list_threads(user_id, db_path=db_path):
        if t['status'] != 'open' or t['pending_suggestion']:
            continue
        due = t.get('next_due_at')
        if due:
            try:
                if datetime.fromisoformat(due) > now:
                    continue
            except ValueError:
                pass
        p = _prompt_text(t)
        chips.append({'type': 'thread', 'thread_id': t['id'],
                      'title': p['question'],
                      'text': p['text'], 'kind': t['kind'],
                      'replies': p['replies']})
    for chip in (extras or [])[:3]:
        chips.append(chip)
    return chips[:3]


# ---------------------------------------------------------------------------
# Push subscriptions (main app — the health store is a separate scope)
# ---------------------------------------------------------------------------

def add_push_subscription(user_id, subscription, db_path=None):
    ep = (subscription or {}).get('endpoint')
    keys = (subscription or {}).get('keys')
    if not ep or not keys:
        return False
    conn = _conn(db_path)
    try:
        conn.execute('''INSERT OR REPLACE INTO push_subscriptions
            (user_id, endpoint, keys_json, created_at) VALUES (?,?,?,?)''',
            (str(user_id), ep, json.dumps(keys), _iso()))
        conn.commit()
        return True
    finally:
        conn.close()


def remove_push_subscription(user_id, endpoint, db_path=None):
    conn = _conn(db_path)
    try:
        conn.execute('DELETE FROM push_subscriptions WHERE user_id=? AND endpoint=?',
                     (str(user_id), endpoint or ''))
        conn.commit()
    finally:
        conn.close()


def all_push_subscriptions(db_path=None):
    conn = _conn(db_path)
    try:
        rows = conn.execute('SELECT * FROM push_subscriptions').fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def push_subscriptions_for(user_id, db_path=None):
    conn = _conn(db_path)
    try:
        rows = conn.execute(
            'SELECT * FROM push_subscriptions WHERE user_id=?',
            (str(user_id),)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def threads_block_for_prompt(user_id, limit=5, db_path=None):
    """A short context block for the companion: its open loops with the user."""
    threads = [t for t in list_threads(user_id, db_path=db_path)
               if t['status'] == 'open' and not t['pending_suggestion']]
    if not threads:
        return ''
    lines = ['OPEN LOOPS with this user (things they said or decided — '
             'follow up naturally when relevant, never all at once):']
    for t in threads[:limit]:
        age = ''
        try:
            days = (_now() - datetime.fromisoformat(t['created_at'])).days
            age = f' ({days}d ago)' if days else ' (today)'
        except ValueError:
            pass
        lines.append(f"- [{t['kind']}]{age} {t['subject']}")
        for a in (t.get('answers') or [])[-2:]:
            lines.append(f"    user answered: {a.get('text', '')[:120]}")
    return '\n'.join(lines)
