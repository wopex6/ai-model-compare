"""
Data freshness: item lifecycle, change history and the confirmation queue.

Stored health data decays. A dose changes, a symptom resolves, a supplement is
stopped — and nothing in the record says so, because until now the only way to
remove something was to delete it, which destroys exactly the history worth
keeping.

This module adds the missing layer, in three parts:

* Lifecycle - every item carries status / started_on / ended_on /
              last_confirmed_at, so "no longer true" is a state rather than a
              deletion and the past stays queryable.
* History   - field-level changes are appended to the item instead of silently
              overwriting it, so '5mg -> 10mg on 12 Mar' survives.
* Queue     - a small, priority-ordered batch of things to confirm, rate limited
              so the user is asked about a few items occasionally rather than
              everything at once. Intervals adapt to the answers: what never
              changes is asked about less often, what does change more often.

Diet and lifestyle are tracked per subsection rather than per entry. Their
entries are bare strings with no identity, and asking "is 'rice' still
accurate?" forty times over is precisely the overwhelm this is meant to avoid.

Pure standard library, no model calls: the queue is deterministic and free.
"""
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional

from .health_insights import (
    SOURCE_AI,
    SOURCE_USER,
    TRUSTED_SOURCES,
    iso,
    normalize_source,
    parse_date,
    stable_id,
)

# --------------------------------------------------------------- lifecycle ---

STATUS_ACTIVE = 'active'
STATUS_PAUSED = 'paused'
STATUS_STOPPED = 'stopped'
STATUS_RESOLVED = 'resolved'
STATUS_INVESTIGATING = 'investigating'

# Statuses that mean "still true today". Anything else is history.
ACTIVE_STATUSES = (STATUS_ACTIVE, STATUS_INVESTIGATING, STATUS_PAUSED)
ENDED_STATUSES = (STATUS_STOPPED, STATUS_RESOLVED, 'completed', 'cancelled',
                  'dismissed', 'expired')

# Categories whose items have a lifecycle, mapped to the field holding the
# item's display name and the date field that marks when it began.
LIFECYCLE_CATEGORIES = {
    'medications': ('name', 'prescribed_date'),
    'supplements': ('name', 'prescribed_date'),
    'conditions': ('name', 'diagnosed_date'),
    'symptoms': ('description', 'onset'),
}

# How a category ends by default. A condition resolves; a drug is stopped.
END_STATUS = {
    'conditions': STATUS_RESOLVED,
    'symptoms': STATUS_RESOLVED,
    'medications': STATUS_STOPPED,
    'supplements': STATUS_STOPPED,
}

# Keep history bounded — this lives inside the profile JSON.
MAX_HISTORY = 25

# Fields the confirmation prompt lets the user correct inline. Anything beyond
# these belongs in the full editor. Mirrored by EDIT_FIELDS in
# static/health_review.js, which renders the inputs.
EDITABLE_FIELDS = {
    'medications': ('dose', 'frequency'),
    'supplements': ('dose', 'frequency'),
    'conditions': ('details',),
    'symptoms': ('severity', 'frequency'),
}


def is_active(item: Dict) -> bool:
    """True when an item still describes the present."""
    if not isinstance(item, dict):
        return False
    status = str(item.get('status') or '').strip().lower()
    if not status:
        return True  # Unset means active; backfill will stamp it.
    return status not in ENDED_STATUSES


def item_label(category: str, item: Dict) -> str:
    name_key = LIFECYCLE_CATEGORIES.get(category, ('name', ''))[0]
    return str(item.get(name_key) or item.get('name') or '').strip()


def item_detail(category: str, item: Dict) -> str:
    """One-line description used in the confirmation question."""
    if category in ('medications', 'supplements'):
        parts = [item.get('dose'), item.get('frequency')]
    elif category == 'conditions':
        parts = [item.get('status'), item.get('details')]
    else:
        parts = [item.get('severity'), item.get('frequency')]
    return ', '.join(str(p).strip() for p in parts if str(p or '').strip())


def backfill_lifecycle(data: Dict) -> int:
    """Stamp lifecycle fields on pre-existing items, exactly once.

    `last_confirmed_at` is deliberately left unset rather than backdated to
    now: these items have never actually been confirmed, and pretending
    otherwise would hide every stale record in the profile from the queue.
    Guarded by `lifecycle_backfilled`. Returns the number of items touched.
    """
    if data.get('lifecycle_backfilled'):
        return 0

    touched = 0
    for category, (_name_key, start_key) in LIFECYCLE_CATEGORIES.items():
        for item in data.get(category) or []:
            if not isinstance(item, dict):
                continue
            before = dict(item)
            item.setdefault('status', STATUS_ACTIVE)
            if not item.get('started_on'):
                started = parse_date(item.get(start_key)) or parse_date(item.get('added_at'))
                if started:
                    item['started_on'] = iso(started)
            item.setdefault('ended_on', '')
            item.setdefault('history', [])
            if before != item:
                touched += 1

    data['lifecycle_backfilled'] = datetime.now().isoformat(timespec='seconds')
    return touched


def record_change(item: Dict, field: str, new_value, source: str = SOURCE_USER,
                  at: Optional[datetime] = None) -> bool:
    """Set a field, appending the old value to the item's history.

    Returns True when something actually changed. No-ops when the value is
    unchanged, so this is safe to call on every ingest.
    """
    if not isinstance(item, dict):
        return False
    old = item.get(field)
    if str(old or '').strip() == str(new_value or '').strip():
        return False

    item[field] = new_value
    # Only log a real change; filling a blank is not a change worth surfacing.
    if str(old or '').strip():
        history = item.setdefault('history', [])
        history.append({
            'at': (at or datetime.now()).isoformat(timespec='seconds'),
            'field': field,
            'from': old,
            'to': new_value,
            'source': normalize_source(source),
        })
        del history[:-MAX_HISTORY]
    return True


# ------------------------------------------------------------- test audit ---
# A bounded, append-only log of test-result changes. Unlike the per-item
# `history` above, this is profile-level: adds, edits, deletions and import
# merges all land here so the audit view can answer "what changed lately?"
# without walking every row.

TEST_AUDIT_MAX = 500
DEFAULT_AUDIT_DAYS = 30


def audit_days(data: Dict) -> int:
    """How many days of test-data changes the audit view shows (default 30)."""
    try:
        days = int((data.get('audit_settings') or {}).get('days') or DEFAULT_AUDIT_DAYS)
    except (TypeError, ValueError):
        days = DEFAULT_AUDIT_DAYS
    return min(3650, max(1, days))


def audit_test_change(data: Dict, action: str, test_name: str = '',
                      detail: Optional[Dict] = None,
                      source: str = SOURCE_USER,
                      at: Optional[datetime] = None) -> Dict:
    """Append one test-data event to the audit log.

    `action` is 'added' | 'updated' | 'deleted' | 'merged'. `detail` carries
    the specifics — value/date for adds and deletes, a changes list for
    updates, a removed count for merges. Timestamps are tz-aware UTC so the
    browser renders the user's local time (naive strings were read as local
    and displayed eight hours off).
    """
    entry = {
        'at': (at or datetime.now(timezone.utc)).isoformat(timespec='seconds'),
        'action': action,
        'test': str(test_name or ''),
        'source': normalize_source(source),
    }
    if detail:
        entry['detail'] = detail
    log = data.setdefault('test_audit', [])
    log.append(entry)
    del log[:-TEST_AUDIT_MAX]
    return entry


def confirm_item(item: Dict, at: Optional[datetime] = None) -> None:
    """Record that the user has just vouched for this item as-is."""
    item['last_confirmed_at'] = (at or datetime.now()).isoformat(timespec='seconds')
    item['verified_by_user'] = True
    item.pop('snoozed_until', None)


def end_item(item: Dict, category: str = '', status: str = '',
             on: Optional[date] = None, at: Optional[datetime] = None) -> None:
    """Retire an item without deleting it."""
    item['status'] = status or END_STATUS.get(category, STATUS_STOPPED)
    item['ended_on'] = iso(on or date.today())
    item['verified_by_user'] = True
    item['last_confirmed_at'] = (at or datetime.now()).isoformat(timespec='seconds')
    item.pop('snoozed_until', None)


def merge_incoming(item: Dict, updates: Dict, source: str,
                   category: str = '') -> Dict:
    """Reconcile freshly ingested fields against a stored item.

    Three outcomes per field, because "newer" does not mean "righter":

    * the stored field is empty          -> fill it
    * it differs, from a trusted source  -> apply it and log the change
    * it differs, from AI inference      -> propose it, change nothing

    That last case matters: a value the AI merely inferred from conversation
    must never silently overwrite something the user or a lab report stated.

    Returns {'updated': bool, 'proposals': [...]} .
    """
    source = normalize_source(source)
    trusted = source in TRUSTED_SOURCES
    updated = False
    proposals: List[Dict] = []

    for field, value in (updates or {}).items():
        if not str(value or '').strip():
            continue
        current = str(item.get(field) or '').strip()
        if not current:
            item[field] = value
            updated = True
        elif current == str(value).strip():
            continue
        elif trusted:
            updated = record_change(item, field, value, source) or updated
        else:
            proposals.append({
                'field': field,
                'from': item.get(field),
                'to': value,
                'source': source,
                'category': category,
                'label': item_label(category, item),
                'at': datetime.now().isoformat(timespec='seconds'),
            })
    return {'updated': updated, 'proposals': proposals}


# ------------------------------------------------------ freshness horizons ---

# How long a category stays believable before it is worth re-checking, in days.
# Doses change often; a diagnosis rarely stops being true.
BASE_HORIZON_DAYS = {
    'medications': 90,
    'supplements': 120,
    'symptoms': 60,
    'conditions': 365,
    'diet': 180,
    'lifestyle': 180,
}

# Relative importance when several things are stale at once. A wrong medication
# list is dangerous; a stale food preference is not.
CATEGORY_WEIGHT = {
    'medications': 1.0,
    'conditions': 0.85,
    'symptoms': 0.8,
    'supplements': 0.7,
    'diet': 0.45,
    'lifestyle': 0.45,
}

# Diet and lifestyle are confirmed a subsection at a time.
GROUP_TARGETS = (
    ('diet', 'restrictions', 'Dietary restrictions'),
    ('diet', 'daily_foods', 'Usual daily foods'),
    ('diet', 'preferences', 'Food preferences'),
    ('lifestyle', 'exercise', 'Exercise routine'),
    ('lifestyle', 'habits', 'Habits'),
    ('lifestyle', 'stress_factors', 'Stress factors'),
)

# Ask about at most this many things at once, however much is stale.
MAX_BATCH = 3
DEFAULT_COOLDOWN_DAYS = 3
MAX_COOLDOWN_DAYS = 45
DEFAULT_SNOOZE_DAYS = 14

# Bounds on how far the adaptive interval may drift from the base horizon.
MIN_FACTOR = 0.5
MAX_FACTOR = 4.0
FACTOR_ON_UNCHANGED = 1.35   # confirmed as-is -> ask less often
FACTOR_ON_CHANGED = 0.6      # it had changed  -> ask more often

# Ceiling on how much being overdue can raise a score. Without it, age alone
# decides the order: a decade-old food preference would out-rank a medication
# that is merely months overdue, because nothing bounds the ratio. Past this
# point everything is simply "very overdue" and clinical weight should decide.
MAX_OVERDUE = 4.0


def review_prefs(data: Dict) -> Dict:
    """Per-user nudge state, created on first access."""
    prefs = data.setdefault('review_prefs', {})
    prefs.setdefault('category_factor', {})
    prefs.setdefault('cooldown_days', DEFAULT_COOLDOWN_DAYS)
    prefs.setdefault('consecutive_dismissals', 0)
    prefs.setdefault('last_nudge_at', '')
    prefs.setdefault('paused_until', '')
    prefs.setdefault('answered_count', 0)
    return prefs


def horizon_days(data: Dict, category: str) -> int:
    """The adaptive confirmation interval for a category."""
    base = BASE_HORIZON_DAYS.get(category, 180)
    factor = review_prefs(data)['category_factor'].get(category, 1.0)
    try:
        factor = min(MAX_FACTOR, max(MIN_FACTOR, float(factor)))
    except (TypeError, ValueError):
        factor = 1.0
    return max(7, int(round(base * factor)))


def _nudge_factor(prefs: Dict, category: str, multiplier: float) -> None:
    factors = prefs.setdefault('category_factor', {})
    current = factors.get(category, 1.0)
    try:
        current = float(current)
    except (TypeError, ValueError):
        current = 1.0
    factors[category] = round(min(MAX_FACTOR, max(MIN_FACTOR, current * multiplier)), 3)


def _freshness_entry(data: Dict, key: str) -> Dict:
    return data.setdefault('freshness', {}).setdefault(key, {})


def _age_days(item: Dict, today: date, start_key: str = '') -> Optional[int]:
    """Days since the item was last vouched for, or since it first appeared."""
    anchor = parse_date(item.get('last_confirmed_at'))
    if anchor is None and start_key:
        anchor = parse_date(item.get(start_key))
    if anchor is None:
        anchor = parse_date(item.get('started_on')) or parse_date(item.get('added_at'))
    if anchor is None:
        return None
    return (today - anchor).days


def _snoozed(item: Dict, today: date) -> bool:
    until = parse_date(item.get('snoozed_until'))
    return until is not None and until > today


def _priority(score: float) -> str:
    if score >= 2.0:
        return 'high'
    if score >= 1.25:
        return 'medium'
    return 'low'


def _candidate(category, label, detail, age, horizon, weight,
               unverified, **extra) -> Optional[Dict]:
    """Score one potential question. Returns None when it is not yet due."""
    if age is None:
        # Never dated at all — worth confirming, but not urgently.
        overdue = 1.05
    else:
        overdue = age / float(horizon or 1)
    if overdue < 1.0:
        return None

    score = min(overdue, MAX_OVERDUE) * weight
    if unverified:
        # AI guesses that were never confirmed are the least trustworthy
        # things in the profile, so they earn their way up the queue.
        score *= 1.3

    entry = {
        'id': stable_id('review', category, label, extra.get('group_key', ''),
                        extra.get('index')),
        'category': category,
        'label': label,
        'detail': detail,
        'days_since': age,
        'horizon_days': horizon,
        'score': round(score, 3),
        'priority': _priority(score),
        'unverified': bool(unverified),
    }
    entry.update(extra)
    return entry


def build_review_queue(data: Dict, today: Optional[date] = None,
                       limit: int = MAX_BATCH) -> List[Dict]:
    """The next few things worth asking about, most urgent first.

    Only overdue items appear, capped at `limit`, so the caller can render the
    whole result without deciding what to hide.
    """
    today = today or date.today()
    out: List[Dict] = []

    for category, (_name_key, start_key) in LIFECYCLE_CATEGORIES.items():
        horizon = horizon_days(data, category)
        weight = CATEGORY_WEIGHT.get(category, 0.5)
        for index, item in enumerate(data.get(category) or []):
            if not isinstance(item, dict) or not is_active(item):
                continue
            if _snoozed(item, today):
                continue
            label = item_label(category, item)
            if not label:
                continue
            unverified = (normalize_source(item.get('source')) == SOURCE_AI
                          and not item.get('verified_by_user'))
            candidate = _candidate(
                category, label, item_detail(category, item),
                _age_days(item, today, start_key), horizon, weight, unverified,
                kind='item', index=index,
                question=_question(category, label, item_detail(category, item)),
                actions=['confirm', 'changed', 'stopped', 'snooze'],
                # Current values so the inline editor opens pre-filled rather
                # than blank, which would invite accidental data loss.
                values={f: item.get(f, '') for f in EDITABLE_FIELDS.get(category, ())},
            )
            if candidate:
                out.append(candidate)

    for category, sub_key, title in GROUP_TARGETS:
        values = ((data.get(category) or {}).get(sub_key)) or []
        if not isinstance(values, list) or not values:
            continue
        group_key = category + '.' + sub_key
        meta = (data.get('freshness') or {}).get(group_key) or {}
        if _snoozed(meta, today):
            continue
        horizon = horizon_days(data, category)
        age = _age_days(meta, today) if meta.get('last_confirmed_at') else None
        if age is None:
            age = _age_days({'added_at': data.get('created_at')}, today)
        preview = ', '.join(str(v) for v in values[:4] if str(v or '').strip())
        if len(values) > 4:
            preview += ' +' + str(len(values) - 4) + ' more'
        candidate = _candidate(
            category, title, preview, age, horizon,
            CATEGORY_WEIGHT.get(category, 0.45), False,
            kind='group', group_key=group_key,
            question='Is this still accurate? ' + title.lower(),
            actions=['confirm', 'changed', 'snooze'],
        )
        if candidate:
            out.append(candidate)

    out.sort(key=lambda c: (-c['score'], c['label'].lower()))
    return out[:max(0, int(limit or 0))]


def _question(category: str, label: str, detail: str) -> str:
    suffix = (' (' + detail + ')') if detail else ''
    if category == 'medications':
        return 'Are you still taking ' + label + suffix + '?'
    if category == 'supplements':
        return 'Are you still taking ' + label + suffix + '?'
    if category == 'symptoms':
        return 'Do you still have ' + label + suffix + '?'
    if category == 'conditions':
        return 'Is ' + label + ' still ongoing' + suffix + '?'
    return 'Is ' + label + ' still accurate?'


def nudge_due(data: Dict, today: Optional[date] = None) -> bool:
    """Whether it is polite to ask right now.

    Three brakes: a global cooldown that lengthens each time the user waves the
    prompt away, an explicit pause, and having something actually overdue.
    """
    today = today or date.today()
    prefs = review_prefs(data)

    paused = parse_date(prefs.get('paused_until'))
    if paused and paused > today:
        return False

    last = parse_date(prefs.get('last_nudge_at'))
    if last is not None:
        try:
            cooldown = int(prefs.get('cooldown_days') or DEFAULT_COOLDOWN_DAYS)
        except (TypeError, ValueError):
            cooldown = DEFAULT_COOLDOWN_DAYS
        if (today - last).days < cooldown:
            return False

    return bool(build_review_queue(data, today, limit=1))


def mark_nudged(data: Dict, at: Optional[datetime] = None) -> None:
    review_prefs(data)['last_nudge_at'] = (at or datetime.now()).isoformat(timespec='seconds')


def freshness_summary(data: Dict, today: Optional[date] = None) -> Dict:
    """Counts for a passive indicator, ignoring the batch cap and cooldown."""
    today = today or date.today()
    queue = build_review_queue(data, today, limit=999)
    return {
        'due': len(queue),
        'high': len([q for q in queue if q['priority'] == 'high']),
        'nudge_due': nudge_due(data, today),
        'next': queue[0] if queue else None,
    }


# ------------------------------------------------------------- applying it ---

VALID_ACTIONS = ('confirm', 'changed', 'stopped', 'snooze', 'dismiss', 'pause',
                 'accept', 'reject')


def _apply_proposal(data: Dict, action: str, index: Optional[int]) -> Dict:
    """Accept or discard a parked AI-inferred field change.

    Proposals sit in `pending_changes` because an AI guess must not overwrite
    what the user or a lab report stated. Accepting applies the change as a
    user edit; rejecting just drops it. Either way the slot is consumed.
    """
    pending = data.get('pending_changes') or []
    if not isinstance(index, int) or isinstance(index, bool) \
            or index < 0 or index >= len(pending):
        return {'ok': False, 'error': 'Suggestion no longer exists', 'item': None}
    proposal = pending.pop(index)
    if action == 'reject':
        return {'ok': True, 'error': '', 'item': proposal}

    category = str(proposal.get('category') or '')
    if category not in LIFECYCLE_CATEGORIES:
        return {'ok': True, 'error': '', 'item': proposal}
    label = str(proposal.get('label') or '').strip().lower()
    for item in data.get(category) or []:
        if item_label(category, item).strip().lower() == label:
            record_change(item, proposal.get('field'), proposal.get('to'),
                          SOURCE_USER)
            confirm_item(item)
            return {'ok': True, 'error': '', 'item': item}
    # The item the proposal referred to is gone; dropping it is the only
    # honest outcome.
    return {'ok': True, 'error': '', 'item': proposal}


def apply_review_action(data: Dict, action: str, category: str = '',
                        index: Optional[int] = None, group_key: str = '',
                        changes: Optional[Dict] = None, days: int = 0,
                        proposal_index: Optional[int] = None,
                        today: Optional[date] = None) -> Dict:
    """Apply one answer from the confirmation queue.

    Returns {'ok': bool, 'error': str, 'item': dict|None}. The caller saves.
    """
    today = today or date.today()
    action = str(action or '').strip().lower()
    prefs = review_prefs(data)

    if action not in VALID_ACTIONS:
        return {'ok': False, 'error': 'Unknown action', 'item': None}

    # Whole-nudge actions, not tied to any one item.
    if action == 'dismiss':
        prefs['consecutive_dismissals'] = int(prefs.get('consecutive_dismissals') or 0) + 1
        # Back off geometrically: someone who keeps waving this away should
        # stop seeing it, without having to find a setting to turn it off.
        cooldown = DEFAULT_COOLDOWN_DAYS * (2 ** prefs['consecutive_dismissals'])
        prefs['cooldown_days'] = min(MAX_COOLDOWN_DAYS, cooldown)
        mark_nudged(data)
        return {'ok': True, 'error': '', 'item': None}

    if action == 'pause':
        span = max(1, min(365, int(days or 30)))
        prefs['paused_until'] = iso(today + timedelta(days=span))
        return {'ok': True, 'error': '', 'item': None}

    # Any real answer is engagement: reset the back-off.
    prefs['consecutive_dismissals'] = 0
    prefs['cooldown_days'] = DEFAULT_COOLDOWN_DAYS
    prefs['answered_count'] = int(prefs.get('answered_count') or 0) + 1
    mark_nudged(data)

    if action in ('accept', 'reject'):
        return _apply_proposal(data, action, proposal_index)

    if group_key:
        meta = _freshness_entry(data, group_key)
        if action == 'snooze':
            meta['snoozed_until'] = iso(today + timedelta(days=max(1, days or DEFAULT_SNOOZE_DAYS)))
            return {'ok': True, 'error': '', 'item': meta}
        meta['last_confirmed_at'] = datetime.now().isoformat(timespec='seconds')
        meta.pop('snoozed_until', None)
        section = group_key.split('.')[0]
        _nudge_factor(prefs, section,
                      FACTOR_ON_UNCHANGED if action == 'confirm' else FACTOR_ON_CHANGED)
        return {'ok': True, 'error': '', 'item': meta}

    if category not in LIFECYCLE_CATEGORIES:
        return {'ok': False, 'error': 'Unknown category', 'item': None}
    items = data.get(category) or []
    if not isinstance(index, int) or index < 0 or index >= len(items):
        return {'ok': False, 'error': 'Item no longer exists', 'item': None}
    item = items[index]
    if not isinstance(item, dict):
        return {'ok': False, 'error': 'Item no longer exists', 'item': None}

    if action == 'snooze':
        item['snoozed_until'] = iso(today + timedelta(days=max(1, days or DEFAULT_SNOOZE_DAYS)))
    elif action == 'confirm':
        confirm_item(item)
        _nudge_factor(prefs, category, FACTOR_ON_UNCHANGED)
    elif action == 'changed':
        for field, value in (changes or {}).items():
            record_change(item, field, value, SOURCE_USER)
        confirm_item(item)
        _nudge_factor(prefs, category, FACTOR_ON_CHANGED)
    elif action == 'stopped':
        end_item(item, category=category, on=today)
        _nudge_factor(prefs, category, FACTOR_ON_CHANGED)

    return {'ok': True, 'error': '', 'item': item}
