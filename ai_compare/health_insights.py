"""
Health insights, reminders and provenance.

Three layers, deliberately separated by cost and risk:

* Provenance  - every stored item is labelled user_entered / document_extracted /
                ai_inferred / clinician_report so the AI (and the user) can tell
                facts from interpretations.
* Tier 1       - deterministic observations and reminders computed in pure Python.
                 No model calls, so they are free, instant and never hallucinate.
* Tier 2       - AI-worded suggestions and questions for the doctor. Hash-gated and
                 cached, capped per day, and validated against stored facts.

Deliberately dependency-light: only the standard library at import time. The model
helper is imported lazily so this module stays importable in tests.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, date, timezone
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------- provenance ---

SOURCE_USER = 'user_entered'
SOURCE_DOCUMENT = 'document_extracted'
SOURCE_AI = 'ai_inferred'
SOURCE_CLINICIAN = 'clinician_report'

# Items that predate provenance tracking. Their true origin is unrecoverable —
# they may have been typed by the user or guessed by the AI — so they are held
# as untrusted until the user confirms them. Never use this as an ingest source
# for new data.
SOURCE_UNKNOWN = 'unknown'

VALID_SOURCES = (SOURCE_USER, SOURCE_DOCUMENT, SOURCE_AI, SOURCE_CLINICIAN,
                 SOURCE_UNKNOWN)

# Sources whose facts Tier 2 advice is allowed to cite.
TRUSTED_SOURCES = (SOURCE_USER, SOURCE_DOCUMENT, SOURCE_CLINICIAN)

SOURCE_LABELS = {
    SOURCE_USER: 'You entered this',
    SOURCE_DOCUMENT: 'From your uploaded report',
    SOURCE_AI: 'AI interpretation',
    SOURCE_CLINICIAN: 'From your clinician',
    SOURCE_UNKNOWN: 'Recorded before sources were tracked',
}

# Older profiles used a free-form `source` string. Map those onto the vocabulary
# above so the migration is idempotent.
LEGACY_SOURCE_MAP = {
    'ai': SOURCE_AI,
    'ai_inferred': SOURCE_AI,
    'assistant': SOURCE_AI,
    'conversation': SOURCE_AI,
    'chat': SOURCE_AI,
    'user': SOURCE_USER,
    'user_entered': SOURCE_USER,
    'manual': SOURCE_USER,
    'self': SOURCE_USER,
    'upload': SOURCE_DOCUMENT,
    'uploaded': SOURCE_DOCUMENT,
    'document': SOURCE_DOCUMENT,
    'document_extracted': SOURCE_DOCUMENT,
    'ocr': SOURCE_DOCUMENT,
    'report': SOURCE_DOCUMENT,
    'lab': SOURCE_CLINICIAN,
    'clinician': SOURCE_CLINICIAN,
    'clinician_report': SOURCE_CLINICIAN,
    'doctor': SOURCE_CLINICIAN,
    'provider': SOURCE_CLINICIAN,
}

# Categories that hold lists of provenance-bearing items.
PROVENANCE_CATEGORIES = (
    'conditions', 'symptoms', 'medications', 'supplements', 'test_results',
    'action_plans', 'follow_ups', 'questions_for_doctor', 'provider_notes',
    'conversation_insights', 'diary',
)

# A user typing something in is self-evidently "verified by the user".
SELF_VERIFYING_SOURCES = (SOURCE_USER,)

DISCLAIMER = (
    'This is general information generated from your own records, not medical '
    'advice or a diagnosis. Always confirm with a qualified clinician.'
)

PROMPT_VERSION = 'advice-v1'


def normalize_source(value, default: str = SOURCE_USER) -> str:
    """Map any legacy/free-form source string onto the canonical vocabulary."""
    text = str(value or '').strip().lower()
    if not text:
        return default
    if text in VALID_SOURCES:
        return text
    return LEGACY_SOURCE_MAP.get(text, default)


def backfill_legacy_provenance(data: Dict) -> int:
    """Label pre-provenance items as `unknown` exactly once, before any save.

    Without this, the first save of an existing profile would stamp every
    unlabelled item with the ingest default (`user_entered`), which is treated as
    self-verifying. That would silently promote years of AI-extracted guesses to
    confirmed facts, and the real origin would be unrecoverable. Marking them
    `unknown` keeps them visible and uncitable until the user confirms them.

    Runs once per profile, guarded by `provenance_backfilled`. Returns the number
    of items labelled.
    """
    if data.get('provenance_backfilled'):
        return 0

    labelled = 0
    for category in PROVENANCE_CATEGORIES:
        items = data.get(category)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            # Only touch items with no usable source at all. Anything already
            # carrying a recognisable source keeps it.
            if str(item.get('source') or '').strip():
                continue
            item['source'] = SOURCE_UNKNOWN
            item.setdefault('verified_by_user', False)
            labelled += 1

    data['provenance_backfilled'] = datetime.now().isoformat(timespec='seconds')
    return labelled


def apply_provenance_defaults(data: Dict, default_source: str = SOURCE_USER) -> int:
    """Stamp `source`, `verified_by_user` and `confidence` on every stored item.

    Idempotent: items that already carry a canonical source are left alone, so
    this is safe to call on every save. Returns the number of items changed.
    """
    default_source = normalize_source(default_source, SOURCE_USER)
    changed = 0
    for category in PROVENANCE_CATEGORIES:
        items = data.get(category)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            before = (item.get('source'), item.get('verified_by_user'))
            source = normalize_source(item.get('source'), default_source)
            item['source'] = source
            if 'verified_by_user' not in item:
                item['verified_by_user'] = source in SELF_VERIFYING_SOURCES
            if item.get('confidence') is None:
                item.pop('confidence', None)
            if before != (item['source'], item['verified_by_user']):
                changed += 1
    return changed


def provenance_counts(data: Dict) -> Dict[str, int]:
    """Count stored items by source, plus how many AI items are unverified."""
    counts = {s: 0 for s in VALID_SOURCES}
    counts['unverified_ai'] = 0
    for category in PROVENANCE_CATEGORIES:
        for item in data.get(category) or []:
            if not isinstance(item, dict):
                continue
            source = normalize_source(item.get('source'))
            counts[source] = counts.get(source, 0) + 1
            if source == SOURCE_AI and not item.get('verified_by_user'):
                counts['unverified_ai'] += 1
    return counts


# ------------------------------------------------------------ parsing helpers ---

_MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def parse_date(text) -> Optional[date]:
    """Parse the date formats that turn up in reports and user input."""
    if isinstance(text, datetime):
        return text.date()
    if isinstance(text, date):
        return text
    raw = str(text or '').strip()
    if not raw:
        return None
    raw = raw.split('T')[0].strip()

    m = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', raw)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    m = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', raw)
    if m:
        # Day-first: this app is used in Hong Kong / AU where DD/MM/YYYY wins.
        return _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    m = re.match(r'^(\d{1,2})\s+([A-Za-z]{3,})\.?\s+(\d{4})$', raw)
    if m:
        month = _MONTHS.get(m.group(2)[:3].lower())
        if month:
            return _safe_date(int(m.group(3)), month, int(m.group(1)))

    m = re.match(r'^([A-Za-z]{3,})\.?\s+(\d{1,2}),?\s+(\d{4})$', raw)
    if m:
        month = _MONTHS.get(m.group(1)[:3].lower())
        if month:
            return _safe_date(int(m.group(3)), month, int(m.group(2)))

    return None


def _safe_date(year: int, month: int, day: int) -> Optional[date]:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def iso(d: Optional[date]) -> str:
    return d.isoformat() if d else ''


def extract_numeric(value) -> Optional[float]:
    """Pull the first number out of a lab value string like '6.4 H mmol/L'."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or '')
    m = re.search(r'-?\d+(?:\.\d+)?', text.replace(',', ''))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def parse_reference_range(text) -> Tuple[Optional[float], Optional[float]]:
    """Return (low, high) from a reference range string. Either may be None."""
    raw = str(text or '').strip()
    if not raw:
        return (None, None)
    cleaned = raw.replace('\u2013', '-').replace('\u2014', '-').replace(',', '')

    m = re.search(r'(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)', cleaned)
    if m:
        low, high = float(m.group(1)), float(m.group(2))
        return (low, high) if low <= high else (high, low)

    m = re.search(r'[<\u2264]\s*(-?\d+(?:\.\d+)?)', cleaned)
    if m:
        return (None, float(m.group(1)))

    m = re.search(r'[>\u2265]\s*(-?\d+(?:\.\d+)?)', cleaned)
    if m:
        return (float(m.group(1)), None)

    return (None, None)


def range_position(value, reference_range) -> Optional[str]:
    """Classify a value against its reference range: low / normal / high."""
    flag = _explicit_flag(value)
    if flag:
        return flag
    number = extract_numeric(value)
    if number is None:
        return None
    low, high = parse_reference_range(reference_range)
    if low is None and high is None:
        return None
    if high is not None and number > high:
        return 'high'
    if low is not None and number < low:
        return 'low'
    return 'normal'


def _explicit_flag(value) -> Optional[str]:
    """Honour the H / L markers labs print next to the number."""
    text = str(value or '')
    if re.search(r'(?:^|[\s(])H(?:$|[\s)*])', text):
        return 'high'
    if re.search(r'(?:^|[\s(])L(?:$|[\s)*])', text):
        return 'low'
    return None


def severity_of_excursion(value, reference_range) -> Optional[float]:
    """How far outside the range a value sits, as a ratio of the bound."""
    number = extract_numeric(value)
    if number is None:
        return None
    low, high = parse_reference_range(reference_range)
    if high is not None and high > 0 and number > high:
        return number / high
    if low is not None and low > 0 and 0 < number < low:
        return low / number
    return None


def normalize_test_key(name) -> str:
    text = str(name or '').lower()
    text = re.sub(r'^[\*\+\s]+', '', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def stable_id(*parts) -> str:
    joined = '|'.join(str(p or '') for p in parts)
    return hashlib.md5(joined.encode('utf-8')).hexdigest()[:16]


# ----------------------------------------------------------------- reminders ---

# "recheck in 3 months", "repeat bloods in 6 weeks", "review in 2 weeks"
_RETEST_RE = re.compile(
    r'(?:re-?check|re-?test|repeat|review|follow[\s-]?up|recheck)\b[^.\n]{0,40}?'
    r'\bin\s+(\d{1,2})\s*(day|week|month|year)s?',
    re.IGNORECASE,
)

_UNIT_DAYS = {'day': 1, 'week': 7, 'month': 30, 'year': 365}

# 'stopped' and 'expired' come from the lifecycle layer (health_freshness).
# They belong here too: a drug the user has stopped must not keep generating
# "Take X" reminders, and it must not count towards polypharmacy.
DONE_STATUSES = ('completed', 'done', 'resolved', 'cancelled', 'dismissed',
                 'stopped', 'expired')


def _is_done(item: Dict) -> bool:
    return str(item.get('status') or '').strip().lower() in DONE_STATUSES


def _due_status(due: Optional[date], today: date) -> Tuple[str, Optional[int]]:
    if due is None:
        return ('no_date', None)
    delta = (due - today).days
    if delta < 0:
        return ('overdue', delta)
    if delta == 0:
        return ('due_today', 0)
    return ('upcoming', delta)


def _reminder(kind, title, detail, due, today, priority='medium',
              category='', index=None, recurrence=''):
    status, days = _due_status(due, today)
    if recurrence:
        status = 'recurring'
    return {
        'id': stable_id(kind, title, iso(due), category, index),
        'kind': kind,
        'title': title,
        'detail': detail,
        'due_date': iso(due),
        'status': status,
        'days_until': days,
        'priority': priority,
        'source_category': category,
        'source_index': index,
        'recurrence': recurrence,
    }


_REMINDER_ORDER = {'overdue': 0, 'due_today': 1, 'upcoming': 2, 'recurring': 3, 'no_date': 4}
_PRIORITY_ORDER = {'high': 0, 'medium': 1, 'low': 2}


def build_reminders(data: Dict, today: Optional[date] = None,
                    horizon_days: int = 120) -> List[Dict]:
    """Derive reminders from stored data. Pure Python: no model calls.

    Sources: follow-ups with due dates, "recheck in N months" phrasing inside
    test notes and provider notes, ongoing medications/supplements, and a gentle
    diary nudge.
    """
    today = today or date.today()
    out: List[Dict] = []

    # 1. Explicit follow-ups.
    for idx, item in enumerate(data.get('follow_ups') or []):
        if not isinstance(item, dict) or _is_done(item):
            continue
        title = str(item.get('title') or '').strip()
        if not title:
            continue
        due = parse_date(item.get('due_date'))
        if due and (due - today).days > horizon_days:
            continue
        steps = item.get('steps') or []
        detail = '; '.join(str(s) for s in steps if s) if isinstance(steps, list) else str(steps)
        out.append(_reminder(
            'follow_up', title, detail, due, today,
            priority=str(item.get('priority') or 'medium').lower(),
            category='follow_ups', index=idx,
        ))

    # 2. "Recheck in N months" buried in test notes / provider notes.
    out.extend(_retest_reminders(data, today, horizon_days))

    # 3. Ongoing medications and supplements -> recurring reminders.
    for category, kind in (('medications', 'medication'), ('supplements', 'supplement')):
        for idx, item in enumerate(data.get(category) or []):
            if not isinstance(item, dict) or _is_done(item):
                continue
            name = str(item.get('name') or '').strip()
            if not name:
                continue
            frequency = str(item.get('frequency') or '').strip()
            dose = str(item.get('dose') or '').strip()
            if not frequency:
                continue
            detail = ' '.join(p for p in (dose, frequency) if p)
            out.append(_reminder(
                kind, 'Take ' + name, detail, None, today,
                priority='medium', category=category, index=idx,
                recurrence=frequency,
            ))

    # 4. Diary nudge when nothing has been written for a while.
    nudge = _diary_nudge(data, today)
    if nudge:
        out.append(nudge)

    out.sort(key=lambda r: (
        _REMINDER_ORDER.get(r['status'], 9),
        r['days_until'] if r['days_until'] is not None else 999,
        _PRIORITY_ORDER.get(r['priority'], 1),
        r['title'].lower(),
    ))
    return out


def _retest_reminders(data: Dict, today: date, horizon_days: int) -> List[Dict]:
    """Turn 'recheck in 3 months' phrasing into dated reminders."""
    found: List[Dict] = []
    seen = set()
    scan = (
        ('test_results', 'notes', 'test_name'),
        ('provider_notes', 'note', 'provider'),
        ('action_plans', 'title', 'title'),
    )
    for category, text_key, label_key in scan:
        for idx, item in enumerate(data.get(category) or []):
            if not isinstance(item, dict) or _is_done(item):
                continue
            text = str(item.get(text_key) or '')
            m = _RETEST_RE.search(text)
            if not m:
                continue
            amount = int(m.group(1))
            unit = m.group(2).lower()
            anchor = parse_date(item.get('date')) or parse_date(item.get('added_at')) or today
            due = anchor + timedelta(days=amount * _UNIT_DAYS.get(unit, 30))
            if (due - today).days > horizon_days:
                continue
            label = str(item.get(label_key) or 'your results').strip() or 'your results'
            title = 'Recheck ' + label
            key = (title, iso(due))
            if key in seen:
                continue
            seen.add(key)
            found.append(_reminder(
                'retest', title,
                m.group(0).strip() + ' (from ' + category.replace('_', ' ') + ')',
                due, today, priority='high', category=category, index=idx,
            ))
    return found


def _diary_nudge(data: Dict, today: date, quiet_days: int = 5) -> Optional[Dict]:
    entries = data.get('diary') or []
    if not entries:
        return None
    latest = None
    for item in entries:
        if not isinstance(item, dict):
            continue
        d = parse_date(item.get('date')) or parse_date(item.get('added_at'))
        if d and (latest is None or d > latest):
            latest = d
    if latest is None:
        return None
    gap = (today - latest).days
    if gap < quiet_days:
        return None
    return _reminder(
        'diary', 'Add a diary entry',
        'Your last entry was ' + str(gap) + ' days ago on ' + iso(latest) + '.',
        today, today, priority='low', category='diary',
    )


def reminders_to_ics(reminders: List[Dict], calendar_name: str = 'Dr. Health') -> str:
    """Export dated reminders as an iCalendar file.

    Web push is unreliable on iOS home-screen PWAs, so a calendar export gives
    the user a delivery channel that works on every platform.
    """
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Dr. Health//Reminders//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:' + _ics_escape(calendar_name),
    ]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for r in reminders:
        due = parse_date(r.get('due_date'))
        if not due:
            continue
        lines.extend([
            'BEGIN:VEVENT',
            'UID:' + r['id'] + '@dr-health',
            'DTSTAMP:' + stamp,
            'DTSTART;VALUE=DATE:' + due.strftime('%Y%m%d'),
            'DTEND;VALUE=DATE:' + (due + timedelta(days=1)).strftime('%Y%m%d'),
            'SUMMARY:' + _ics_escape(r.get('title') or 'Health reminder'),
            'DESCRIPTION:' + _ics_escape(r.get('detail') or ''),
            'BEGIN:VALARM',
            'TRIGGER:-P1D',
            'ACTION:DISPLAY',
            'DESCRIPTION:' + _ics_escape(r.get('title') or 'Health reminder'),
            'END:VALARM',
            'END:VEVENT',
        ])
    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines) + '\r\n'


def _ics_escape(text: str) -> str:
    return (str(text or '')
            .replace('\\', '\\\\').replace(';', '\\;')
            .replace(',', '\\,').replace('\n', '\\n'))


# ------------------------------------------------- tier 1: observations (free) ---

SEVERITY_URGENT = 'urgent'
SEVERITY_WATCH = 'watch'
SEVERITY_INFO = 'info'

_SEVERITY_ORDER = {SEVERITY_URGENT: 0, SEVERITY_WATCH: 1, SEVERITY_INFO: 2}

# Widely-ordered panels. Used only to point out gaps, never to recommend a test.
COMMON_PANELS = (
    ('Vitamin D', ('vitamin d', '25 oh', '25 hydroxy')),
    ('HbA1c', ('hba1c', 'glycated haemoglobin', 'glycated hemoglobin')),
    ('LDL cholesterol', ('ldl',)),
    ('Creatinine (kidney)', ('creatinine',)),
    ('ALT (liver)', ('alt', 'sgpt')),
    ('Haemoglobin', ('haemoglobin', 'hemoglobin', 'hgb')),
    ('TSH (thyroid)', ('tsh',)),
)

NEGATIVE_MOODS = ('sad', 'angry', 'anxious', 'tired')

POLYPHARMACY_THRESHOLD = 5
STALE_TEST_DAYS = 365
CRITICAL_EXCURSION_RATIO = 2.0


def _observation(oid, severity, title, detail, evidence=None, action=''):
    return {
        'id': oid,
        'tier': 1,
        'severity': severity,
        'title': title,
        'detail': detail,
        'action': action,
        'evidence': evidence or [],
        'source': 'computed',
    }


def _dated_tests(data: Dict) -> Dict[str, List[Dict]]:
    """Group test results by normalized name, each list sorted oldest first."""
    groups: Dict[str, List[Dict]] = {}
    for idx, item in enumerate(data.get('test_results') or []):
        if not isinstance(item, dict):
            continue
        name = str(item.get('test_name') or '').strip()
        if not name:
            continue
        key = normalize_test_key(name)
        if not key:
            continue
        entry = dict(item)
        entry['_index'] = idx
        entry['_date'] = parse_date(item.get('date')) or parse_date(item.get('added_at'))
        entry['_number'] = extract_numeric(item.get('value'))
        groups.setdefault(key, []).append(entry)
    for key in groups:
        groups[key].sort(key=lambda e: (e['_date'] or date.min, e['_index']))
    return groups


def build_observations(data: Dict, today: Optional[date] = None) -> List[Dict]:
    """Tier 1 facts computed from stored data. No model calls, no interpretation.

    Every observation carries the evidence it was derived from so the UI can show
    the user exactly which stored values produced it.
    """
    today = today or date.today()
    groups = _dated_tests(data)
    out: List[Dict] = []

    out.extend(_out_of_range_observations(groups))
    out.extend(_trend_observations(groups))
    out.extend(_stale_test_observations(groups, today))
    out.extend(_missing_panel_observations(groups))
    out.extend(_polypharmacy_observations(data))
    out.extend(_unverified_observations(data))
    out.extend(_mood_observations(data, today))

    out.sort(key=lambda o: (_SEVERITY_ORDER.get(o['severity'], 9), o['title'].lower()))
    return out


def _evidence(entry: Dict) -> Dict:
    return {
        'category': 'test_results',
        'index': entry.get('_index'),
        'test_name': entry.get('test_name', ''),
        'value': entry.get('value', ''),
        'reference_range': entry.get('reference_range', ''),
        'date': iso(entry.get('_date')),
    }


def _out_of_range_observations(groups: Dict[str, List[Dict]]) -> List[Dict]:
    out = []
    for key, entries in groups.items():
        latest = entries[-1]
        position = range_position(latest.get('value'), latest.get('reference_range'))
        if position not in ('high', 'low'):
            continue
        ratio = severity_of_excursion(latest.get('value'), latest.get('reference_range'))
        critical = ratio is not None and ratio >= CRITICAL_EXCURSION_RATIO
        name = latest.get('test_name', key)
        detail = (
            'Your most recent ' + str(name) + ' was ' + str(latest.get('value', '')) +
            (' against a reference range of ' + str(latest.get('reference_range'))
             if latest.get('reference_range') else '') +
            ' on ' + (iso(latest.get('_date')) or 'an unrecorded date') + '.'
        )
        out.append(_observation(
            stable_id('range', key, iso(latest.get('_date'))),
            SEVERITY_URGENT if critical else SEVERITY_WATCH,
            str(name) + ' is ' + position,
            detail,
            evidence=[_evidence(latest)],
            action=('This is well outside the reference range. Please contact a '
                    'clinician about this result.') if critical
                   else 'Worth raising at your next appointment.',
        ))
    return out


def _trend_observations(groups: Dict[str, List[Dict]]) -> List[Dict]:
    out = []
    for key, entries in groups.items():
        points = [e for e in entries if e['_date'] and e['_number'] is not None]
        if len(points) < 3:
            continue
        first, last = points[0], points[-1]
        if first['_number'] == 0:
            continue
        change = last['_number'] - first['_number']
        if abs(change) < 1e-9:
            continue
        percent = (change / abs(first['_number'])) * 100.0
        if abs(percent) < 10.0:
            continue
        direction = 'risen' if change > 0 else 'fallen'
        name = last.get('test_name', key)
        out.append(_observation(
            stable_id('trend', key, iso(first['_date']), iso(last['_date'])),
            SEVERITY_WATCH if abs(percent) >= 25.0 else SEVERITY_INFO,
            str(name) + ' has ' + direction + ' over ' + str(len(points)) + ' results',
            str(name) + ' went from ' + _fmt(first['_number']) + ' on ' + iso(first['_date']) +
            ' to ' + _fmt(last['_number']) + ' on ' + iso(last['_date']) +
            ' (' + ('+' if percent > 0 else '') + _fmt(percent) + '%).',
            evidence=[_evidence(p) for p in points],
            action='A trend is more informative than a single value. Show this to your doctor.',
        ))
    return out


def _fmt(number: float) -> str:
    text = ('%.2f' % float(number)).rstrip('0').rstrip('.')
    return text if text else '0'


def _stale_test_observations(groups: Dict[str, List[Dict]], today: date) -> List[Dict]:
    dated = [e for entries in groups.values() for e in entries if e['_date']]
    if not dated:
        return []
    newest = max(e['_date'] for e in dated)
    age = (today - newest).days
    if age <= STALE_TEST_DAYS:
        return []
    return [_observation(
        stable_id('stale', iso(newest)),
        SEVERITY_INFO,
        'Your test results are over a year old',
        'The most recent result on file is from ' + iso(newest) + ', ' + str(age) + ' days ago.',
        action='Upload newer results so trends stay meaningful.',
    )]


def _missing_panel_observations(groups: Dict[str, List[Dict]]) -> List[Dict]:
    if not groups:
        return []
    keys = ' | '.join(groups.keys())
    missing = [label for label, needles in COMMON_PANELS
               if not any(n in keys for n in needles)]
    if not missing:
        return []
    return [_observation(
        stable_id('missing', *missing),
        SEVERITY_INFO,
        'Some common measurements are not on file',
        'No stored result for: ' + ', '.join(missing) + '.',
        action=('This only means the value is missing from your records here. It is '
                'not a recommendation to get tested.'),
    )]


def _polypharmacy_observations(data: Dict) -> List[Dict]:
    # Count only what is still being taken; a long history of stopped drugs
    # is not polypharmacy.
    meds = [m for m in (data.get('medications') or [])
            if isinstance(m, dict) and m.get('name') and not _is_done(m)]
    sups = [s for s in (data.get('supplements') or [])
            if isinstance(s, dict) and s.get('name') and not _is_done(s)]
    total = len(meds) + len(sups)
    if total < POLYPHARMACY_THRESHOLD:
        return []
    return [_observation(
        stable_id('polypharmacy', total),
        SEVERITY_WATCH,
        'You are taking ' + str(total) + ' medications and supplements',
        str(len(meds)) + ' medication(s) and ' + str(len(sups)) + ' supplement(s) are on file.',
        action='Ask a pharmacist or doctor to review the whole list together.',
    )]


def _unverified_observations(data: Dict) -> List[Dict]:
    counts = provenance_counts(data)
    out = []

    unverified = counts.get('unverified_ai', 0)
    if unverified >= 3:
        out.append(_observation(
            stable_id('unverified', unverified),
            SEVERITY_INFO,
            str(unverified) + ' entries came from AI and are unconfirmed',
            'These were inferred by the AI from your documents or conversations and you '
            'have not confirmed them yet.',
            action='Open each item and confirm or correct it so future advice is built on facts.',
        ))

    # Legacy items predate source tracking, so they are held as untrusted too.
    legacy = counts.get(SOURCE_UNKNOWN, 0)
    if legacy >= 3:
        out.append(_observation(
            stable_id('legacy_provenance', legacy),
            SEVERITY_INFO,
            str(legacy) + ' older entries have no recorded source',
            'These were saved before Dr. Health tracked where each fact came from, so '
            'it is not known whether you entered them or the AI inferred them.',
            action='Confirm the ones you know are correct so advice can rely on them.',
        ))

    return out


def _mood_observations(data: Dict, today: date, window_days: int = 14) -> List[Dict]:
    entries = data.get('diary') or []
    if not entries:
        return []
    cutoff = today - timedelta(days=window_days)
    recent, negative = 0, 0
    for item in entries:
        if not isinstance(item, dict):
            continue
        d = parse_date(item.get('date')) or parse_date(item.get('added_at'))
        if not d or d < cutoff:
            continue
        recent += 1
        if str(item.get('mood') or '').strip().lower() in NEGATIVE_MOODS:
            negative += 1
    if recent < 3 or negative * 2 < recent:
        return []
    return [_observation(
        stable_id('mood', today.isoformat(), negative, recent),
        SEVERITY_WATCH,
        'Most recent diary entries record a low mood',
        str(negative) + ' of your last ' + str(recent) + ' entries in the past ' +
        str(window_days) + ' days recorded a difficult mood.',
        action='If this keeps up, it is worth telling someone you trust or your doctor.',
    )]


def red_flags(observations: List[Dict]) -> List[Dict]:
    """The subset that should be shown prominently rather than buried in a list."""
    return [o for o in observations if o.get('severity') == SEVERITY_URGENT]


# ------------------------------------------------------ settings & usage caps ---

DEFAULT_ADVICE_SETTINGS = {
    'ai_enabled': True,
    'reminders_enabled': True,
    'notifications_enabled': False,
    'digest_frequency': 'weekly',   # weekly | monthly | off
    'locale': 'en',                 # en | zh-HK
}

DIGEST_PERIOD_DAYS = {'weekly': 7, 'monthly': 30}


def advice_settings(data: Dict) -> Dict:
    """Merge stored preferences over the defaults."""
    stored = data.get('advice_settings')
    merged = dict(DEFAULT_ADVICE_SETTINGS)
    if isinstance(stored, dict):
        for key in DEFAULT_ADVICE_SETTINGS:
            if key in stored and stored[key] is not None:
                merged[key] = stored[key]
    return merged


def daily_cap() -> int:
    try:
        return max(0, int(os.getenv('HEALTH_ADVICE_DAILY_CAP', '5')))
    except ValueError:
        return 5


def _usage(data: Dict, today: date) -> Dict:
    usage = data.get('ai_advice_usage')
    if not isinstance(usage, dict) or usage.get('date') != today.isoformat():
        usage = {'date': today.isoformat(), 'count': 0}
        data['ai_advice_usage'] = usage
    return usage


def remaining_generations(data: Dict, today: Optional[date] = None) -> int:
    today = today or date.today()
    return max(0, daily_cap() - int(_usage(data, today).get('count', 0)))


# --------------------------------------------- tier 2: AI advice (hash-gated) ---

# Only fields that can change the advice go into the signature. Cosmetic edits
# (titles, tags, personal details) deliberately do not trigger a regeneration.
def advice_signature(data: Dict) -> str:
    def norm_list(category, keys):
        rows = []
        for item in data.get(category) or []:
            if not isinstance(item, dict):
                continue
            rows.append([str(item.get(k) or '').strip().lower() for k in keys])
        rows.sort()
        return rows

    payload = {
        'v': PROMPT_VERSION,
        'conditions': norm_list('conditions', ('name', 'status')),
        'medications': norm_list('medications', ('name', 'dose')),
        'supplements': norm_list('supplements', ('name', 'dose')),
        'symptoms': norm_list('symptoms', ('description', 'severity')),
        'tests': norm_list('test_results', ('test_name', 'value', 'date')),
        'follow_ups': norm_list('follow_ups', ('title', 'due_date', 'status')),
        'personal': [
            str((data.get('personal') or {}).get('age') or ''),
            str((data.get('personal') or {}).get('gender') or ''),
        ],
        'locale': advice_settings(data).get('locale', 'en'),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def cached_advice(data: Dict) -> Optional[Dict]:
    """Return the stored advice when it still matches the current facts."""
    cached = data.get('ai_advice')
    if not isinstance(cached, dict):
        return None
    if cached.get('signature') != advice_signature(data):
        return None
    return cached


ADVICE_SYSTEM_PROMPT = """You help a patient understand their own health records.

You will be given VERIFIED FACTS (entered by the patient or extracted from their
lab reports) and separately UNVERIFIED AI GUESSES. Rules you must follow:

- Base everything on the VERIFIED FACTS. You may mention an unverified item only
  to ask the patient to confirm it. Never treat an unverified guess as true.
- Never invent a test name, a number, a date or a diagnosis. Every value you cite
  must appear verbatim in the facts you were given.
- Do NOT diagnose. Do NOT give dosages. Do NOT tell the patient to start, stop or
  change any medication.
- Frame suggestions as things to discuss with a clinician.
- Be brief and concrete. Plain language, no jargon, no bullet symbols in strings.

Return ONLY valid JSON, no markdown fences, in exactly this shape:

{
  "suggestions": [
    {"title": "short heading",
     "detail": "2 sentences max, plain language",
     "cites": ["exact test name or medication name from the facts"],
     "confidence": "high|medium|low"}
  ],
  "questions_for_doctor": [
    {"question": "a question the patient can read out at their appointment",
     "context": "one sentence on why, referencing their own data",
     "priority": "high|medium|low"}
  ]
}

Return at most 5 suggestions and at most 5 questions. Omit a key if you have
nothing for it."""


def _facts_for_prompt(data: Dict) -> Tuple[str, str, set]:
    """Split stored data into verified facts, unverified guesses, and citable names."""
    verified, unverified = [], []
    citable = set()

    def add(item, line, name):
        source = normalize_source(item.get('source'))
        trusted = item.get('verified_by_user') or source in TRUSTED_SOURCES
        (verified if trusted else unverified).append(line)
        if trusted and name:
            citable.add(normalize_test_key(name))

    personal = data.get('personal') or {}
    if personal.get('age'):
        verified.append('Age: ' + str(personal['age']))
    if personal.get('gender'):
        verified.append('Gender: ' + str(personal['gender']))

    for item in data.get('conditions') or []:
        if isinstance(item, dict) and item.get('name'):
            add(item, 'Condition: ' + str(item['name']) +
                ' (status ' + str(item.get('status') or 'unknown') + ')', item['name'])

    for category, label in (('medications', 'Medication'), ('supplements', 'Supplement')):
        for item in data.get(category) or []:
            if isinstance(item, dict) and item.get('name'):
                bits = [str(item['name'])]
                if item.get('dose'):
                    bits.append(str(item['dose']))
                if item.get('purpose'):
                    bits.append('for ' + str(item['purpose']))
                add(item, label + ': ' + ' '.join(bits), item['name'])

    for item in data.get('symptoms') or []:
        if isinstance(item, dict) and item.get('description'):
            add(item, 'Symptom: ' + str(item['description']) +
                ' (' + str(item.get('severity') or 'unspecified') + ')', item['description'])

    # Latest 40 dated results keep the prompt small without losing recent trends.
    tests = []
    for item in data.get('test_results') or []:
        if not isinstance(item, dict) or not item.get('test_name'):
            continue
        tests.append((parse_date(item.get('date')) or date.min, item))
    tests.sort(key=lambda pair: pair[0])
    for _, item in tests[-40:]:
        line = ('Test: ' + str(item['test_name']) + ' = ' + str(item.get('value') or '') +
                (' (ref ' + str(item['reference_range']) + ')' if item.get('reference_range') else '') +
                (' on ' + str(item['date']) if item.get('date') else ''))
        add(item, line, item['test_name'])

    for item in data.get('follow_ups') or []:
        if isinstance(item, dict) and item.get('title') and not _is_done(item):
            add(item, 'Open follow-up: ' + str(item['title']) +
                (' due ' + str(item['due_date']) if item.get('due_date') else ''), item['title'])

    return ('\n'.join(verified), '\n'.join(unverified), citable)


def _strip_fences(text: str) -> str:
    cleaned = str(text or '').strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
    start, end = cleaned.find('{'), cleaned.rfind('}')
    if start != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    return cleaned


def validate_advice(parsed: Dict, citable: set) -> Dict:
    """Drop anything that cites a fact we do not actually hold.

    This is the guard against the model inventing a lab value or a medication.
    """
    suggestions = []
    for raw in (parsed.get('suggestions') or [])[:5]:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get('title') or '').strip()
        detail = str(raw.get('detail') or '').strip()
        if not title or not detail:
            continue
        cites = raw.get('cites') or []
        if not isinstance(cites, list):
            cites = [cites]
        clean_cites = [str(c).strip() for c in cites if str(c).strip()]
        # Every citation must map to something we stored.
        if clean_cites and not all(normalize_test_key(c) in citable for c in clean_cites):
            continue
        suggestions.append({
            'id': stable_id('suggestion', title, detail),
            'tier': 2,
            'title': title,
            'detail': detail,
            'cites': clean_cites,
            'confidence': str(raw.get('confidence') or 'medium').lower(),
            'source': SOURCE_AI,
        })

    questions = []
    for raw in (parsed.get('questions_for_doctor') or [])[:5]:
        if not isinstance(raw, dict):
            continue
        question = str(raw.get('question') or '').strip()
        if not question:
            continue
        questions.append({
            'id': stable_id('question', question),
            'question': question,
            'context': str(raw.get('context') or '').strip(),
            'priority': str(raw.get('priority') or 'medium').lower(),
            'source': SOURCE_AI,
        })

    return {'suggestions': suggestions, 'questions_for_doctor': questions}


def empty_advice(reason: str = '') -> Dict:
    return {
        'signature': '',
        'generated_at': '',
        'model': '',
        'prompt_version': PROMPT_VERSION,
        'suggestions': [],
        'questions_for_doctor': [],
        'disclaimer': DISCLAIMER,
        'reason': reason,
    }


def conversation_context(messages: List[Dict], limit: int = 40,
                         max_chars: int = 4000) -> Tuple[str, str]:
    """Render the recent chat for the advice prompt, plus a change marker.

    The marker lets callers tell when the conversation has moved on even
    though the profile facts have not — that is what makes the cached advice
    stale when new personal information was only ever discussed in chat.
    """
    msgs = [m for m in (messages or [])
            if isinstance(m, dict)
            and str(m.get('sender_type') or '') in ('user', 'assistant')
            and str(m.get('content') or '').strip()]
    tail = msgs[-limit:]
    last = tail[-1] if tail else {}
    marker = hashlib.sha256(
        (str(len(msgs)) + '|' + str(last.get('id') or last.get('timestamp') or ''))
        .encode('utf-8')).hexdigest()[:16]
    lines = []
    for m in tail:
        who = 'Patient' if m.get('sender_type') == 'user' else 'Dr. Health'
        text = ' '.join(str(m.get('content') or '').split())[:240]
        lines.append(who + ': ' + text)
    while lines and len('\n'.join(lines)) > max_chars:
        lines.pop(0)
    return '\n'.join(lines), marker


def generate_advice(data: Dict, force: bool = False, today: Optional[date] = None,
                    chat=None, conversation: str = '',
                    conversation_marker: str = '') -> Dict:
    """Return Tier 2 advice, generating it only when it is actually needed.

    Gating order: opt-out, then cache hash, then daily cap. `chat` is injectable
    so tests never reach a network.
    """
    today = today or date.today()
    settings = advice_settings(data)

    if not settings.get('ai_enabled'):
        return empty_advice('AI advice is turned off in your settings.')

    if not force:
        cached = cached_advice(data)
        # Advice also depends on what was discussed in chat, so a marker
        # mismatch means the conversation moved on even though the stored
        # facts did not.
        if cached and str(cached.get('conversation_marker') or '') == \
                str(conversation_marker or ''):
            result = dict(cached)
            result['cached'] = True
            return result

    verified, unverified, citable = _facts_for_prompt(data)
    if not verified.strip():
        return empty_advice('Add some health information first.')

    usage = _usage(data, today)
    if int(usage.get('count', 0)) >= daily_cap():
        stale = data.get('ai_advice')
        if isinstance(stale, dict):
            result = dict(stale)
            result['cached'] = True
            result['reason'] = 'Daily AI limit reached; showing your last advice.'
            return result
        return empty_advice('Daily AI limit reached. Try again tomorrow.')

    if chat is None:
        from ai_compare.medical_advisor_health_context import _health_ai_chat as chat

    locale_note = ('Write in Traditional Chinese (Hong Kong).'
                   if str(settings.get('locale')) == 'zh-HK' else 'Write in English.')
    user_prompt = (
        'VERIFIED FACTS:\n' + verified +
        ('\n\nUNVERIFIED AI GUESSES (confirm before relying on these):\n' + unverified
         if unverified.strip() else '') +
        ('\n\nRECENT CONVERSATION (things the patient mentioned in chat — '
         'reconcile these with the facts above):\n' + conversation
         if str(conversation or '').strip() else '') +
        '\n\n' + locale_note
    )

    model = os.getenv('HEALTH_ADVICE_MODEL', '') or None
    try:
        raw = chat(
            [{'role': 'system', 'content': ADVICE_SYSTEM_PROMPT},
             {'role': 'user', 'content': user_prompt}],
            max_tokens=1200,
            temperature=0.2,
            model=model,
        )
        parsed = json.loads(_strip_fences(raw))
    except Exception as e:
        return empty_advice('Could not generate advice right now: ' + str(e)[:120])

    if not isinstance(parsed, dict):
        return empty_advice('The AI returned an unexpected format.')

    validated = validate_advice(parsed, citable)
    usage['count'] = int(usage.get('count', 0)) + 1

    advice = {
        'signature': advice_signature(data),
        'generated_at': datetime.now().isoformat(),
        'model': model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        'prompt_version': PROMPT_VERSION,
        'conversation_marker': str(conversation_marker or ''),
        'locale': settings.get('locale', 'en'),
        'suggestions': validated['suggestions'],
        'questions_for_doctor': validated['questions_for_doctor'],
        'disclaimer': DISCLAIMER,
        'reason': '',
        'cached': False,
    }
    data['ai_advice'] = advice
    return advice


# --------------------------------------------------------------- weekly digest ---

def digest_due(data: Dict, today: Optional[date] = None) -> bool:
    today = today or date.today()
    frequency = str(advice_settings(data).get('digest_frequency') or 'weekly')
    if frequency == 'off':
        return False
    period = DIGEST_PERIOD_DAYS.get(frequency, 7)
    last = parse_date((data.get('digest') or {}).get('generated_at'))
    if not last:
        return True
    return (today - last).days >= period


def build_digest(data: Dict, today: Optional[date] = None) -> Dict:
    """A periodic review: what changed, what needs attention, what is coming up.

    Entirely deterministic. Any AI wording it shows is the already-cached advice,
    so producing a digest never costs a model call.
    """
    today = today or date.today()
    frequency = str(advice_settings(data).get('digest_frequency') or 'weekly')
    period = DIGEST_PERIOD_DAYS.get(frequency, 7)
    start = today - timedelta(days=period)

    added: Dict[str, int] = {}
    for category in PROVENANCE_CATEGORIES:
        count = 0
        for item in data.get(category) or []:
            if not isinstance(item, dict):
                continue
            stamp = parse_date(item.get('added_at')) or parse_date(item.get('date'))
            if stamp and stamp >= start:
                count += 1
        if count:
            added[category] = count

    observations = build_observations(data, today)
    reminders = build_reminders(data, today)
    due_soon = [r for r in reminders
                if r['status'] in ('overdue', 'due_today')
                or (r['days_until'] is not None and r['days_until'] <= period)]

    cached = cached_advice(data) or {}

    return {
        'period': frequency,
        'period_start': start.isoformat(),
        'period_end': today.isoformat(),
        'generated_at': today.isoformat(),
        'added': added,
        'added_total': sum(added.values()),
        'red_flags': red_flags(observations),
        'observations': observations,
        'reminders_due': due_soon,
        'suggestions': cached.get('suggestions', []),
        'questions_for_doctor': cached.get('questions_for_doctor', []),
        'provenance': provenance_counts(data),
        'disclaimer': DISCLAIMER,
    }


def build_overview(data: Dict, today: Optional[date] = None) -> Dict:
    """Everything the UI needs for the badge and the advice screen, cache-only."""
    today = today or date.today()
    settings = advice_settings(data)
    observations = build_observations(data, today)
    reminders = build_reminders(data, today) if settings.get('reminders_enabled') else []
    cached = cached_advice(data)
    signature = advice_signature(data)
    stored = data.get('ai_advice') if isinstance(data.get('ai_advice'), dict) else None

    return {
        'settings': settings,
        'observations': observations,
        'red_flags': red_flags(observations),
        'reminders': reminders,
        'reminder_counts': {
            'overdue': len([r for r in reminders if r['status'] == 'overdue']),
            'due_today': len([r for r in reminders if r['status'] == 'due_today']),
            'total': len(reminders),
        },
        'advice': cached or empty_advice(
            'Tap refresh to generate advice from your latest records.'
            if stored is None else 'Your records changed since this advice was written.'
        ),
        'advice_stale': cached is None and stored is not None,
        'advice_signature': signature,
        'provenance': provenance_counts(data),
        'digest_due': digest_due(data, today),
        'remaining_generations': remaining_generations(data, today),
        'disclaimer': DISCLAIMER,
    }
