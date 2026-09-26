"""Derive a report table's layout from its contents rather than its wording.

Reports arrive in layouts nobody has seen before: columns may be dates, or
Actual/Predicted/%Predicted, or a reference range with no heading at all.
Matching English column headings ('Pred', '%Chng') only ever works for the
reports whose vocabulary someone already thought of, so this module reads the
*cells*:

- a column whose cells parse as dates is a date column, whatever it is called;
- a column of 'a - b' or '< x' is a reference range, even unlabelled;
- a column that equals 100 x one column divided by another is a percentage of a
  baseline -- which is what '%Pred' means, found by arithmetic instead of by
  vocabulary, so '% of expected' or a Chinese heading works identically.

Column headings are still read, but only as a tie-break and to *name* what was
found; they never decide it on their own. Whatever the report calls a column is
what the extracted row is labelled with, so nothing here needs editing when a
new report kind turns up.

`describe()` also returns a signature for the layout. A layout seen before is
recognised by signature and reused; an unfamiliar one is described from scratch
and recorded. That is the "old format is fine, new format gets analysed" stage.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from statistics import median
from typing import Dict, List, Optional, Tuple

# --- shapes a cell can have -------------------------------------------------

_DATE_CELL_RE = re.compile(
    r'^[\(\[]?\s*(?:'
    r'\d{1,2}[-/. ][A-Za-z]{3,9}[-/. ]\d{2,4}'
    r'|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}'
    r'|\d{4}[-/.]\d{1,2}[-/.]\d{1,2}'
    r'|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{2,4}'
    r')\s*[\)\]]?$'
)
_DATE_IN_TEXT_RE = re.compile(
    r'(\d{1,2}[-/. ][A-Za-z]{3,9}[-/. ]\d{2,4}'
    r'|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}'
    r'|\d{4}[-/.]\d{1,2}[-/.]\d{1,2})'
)
_RANGE_CELL_RE = re.compile(
    r'^[\(\[]?\s*(?:'
    r'[<>\u2264\u2265]=?\s*-?\d+(?:\.\d+)?'
    r'|-?\d+(?:\.\d+)?\s*(?:-|\u2013|\u2014|to)\s*-?\d+(?:\.\d+)?'
    r')\s*[a-zA-Z\u00b5\u03bc/%^0-9.]*\s*[\)\]]?$',
    re.I,
)
_FLAG_CELL_RE = re.compile(
    r'^[\(\[]?\s*(?:H|L|N|A|HH|LL|\*|\+|\u2191|\u2193'
    r'|abn(?:ormal)?|high|low|normal)\s*[\)\]]?$',
    re.I,
)
_UNIT_CELL_RE = re.compile(
    r'^[\(\[]?\s*(?:'
    r'x?10[\^*]?\d+\s*/\s*[A-Za-z]+'
    r'|[A-Za-z\u00b5\u03bc%\u00b0]{1,12}(?:/[A-Za-z0-9\u00b5\u03bc^*.]{1,12}){0,3}'
    r')\s*[\)\]]?$'
)
_NUM_RE = re.compile(r'-?\d+(?:\.\d+)?')
# A measurement is a number, optionally behind a comparator and followed by a
# flag and a unit -- not prose that happens to contain a digit. 'repeat in 6
# months' must not make its column look like a column of results.
_MEASUREMENT_RE = re.compile(
    r'^[\(\[]?\s*[<>\u2264\u2265~=]?\s*-?\d+(?:[.,]\d+)*'
    r'(?:\s*[A-Za-z\u00b5\u03bc%\u00b0^*/0-9.+-]{1,14}){0,2}\s*[\)\]]?$'
)
_SEPARATOR_RE = re.compile(r'^:?-{2,}:?$')


def looks_like_date(cell: str) -> bool:
    return bool(_DATE_CELL_RE.match((cell or '').strip()))


def looks_like_range(cell: str) -> bool:
    return bool(_RANGE_CELL_RE.match((cell or '').strip()))


def looks_like_flag(cell: str) -> bool:
    return bool(_FLAG_CELL_RE.match((cell or '').strip()))


def looks_like_unit(cell: str) -> bool:
    """A unit is a short symbol, not a word and not a number.

    'Serum' or 'Fasting' would otherwise pass as a unit and turn a specimen
    column into a unit column, so a unit must either carry a symbol that only
    units carry (/, %, ^, degree) or be very short.
    """
    text = (cell or '').strip().strip('()[]')
    if not text or len(text) > 16 or ' ' in text:
        return False
    if not _UNIT_CELL_RE.match(text):
        return False
    if re.search(r'[/%^\u00b0]', text) or re.match(r'x?10[\^*]', text, re.I):
        return True
    # Bare SI letters (L, g, U) — not English words. 'None' on a radiology
    # Severity column used to pass because it is four letters, and then every
    # finding was skipped because the table had no measurement column.
    return bool(re.match(r'^[A-Za-z]{1,2}$', text))


def looks_like_measurement(cell: str) -> bool:
    return bool(_MEASUREMENT_RE.match((cell or '').strip()))


def number_in(cell: str) -> Optional[float]:
    """The first number in a cell, ignoring flags, units and thousands commas."""
    text = re.sub(r'(?<=\d),(?=\d{3}\b)', '', str(cell or ''))
    match = _NUM_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def is_separator_row(cells: List[str]) -> bool:
    return bool(cells) and all(
        _SEPARATOR_RE.match((c or '').strip()) or not (c or '').strip() for c in cells
    )


# --- heading hints ----------------------------------------------------------
# Only ever a tie-break. Every role these suggest is also reachable from the
# cells alone, so a report in another language or vocabulary still parses.

_HINTS: Tuple[Tuple[str, str], ...] = (
    (r'%\s*(?:of\s*)?(?:pred|predict|expect|target|norm|ref)', 'percent_of'),
    (r'%\s*ch?a?n?g', 'percent_change'),
    (r'\bchange\b.*%|%.*\bchange\b', 'percent_change'),
    (r'\b(refer|reference|range|normal range)\b', 'range'),
    (r'\bunits?\b', 'unit'),
    (r'\b(pred|predicted|expected|target|baseline)\b', 'baseline'),
    (r'\b(actual|result|value|measured|observed|reading)\b', 'measured'),
    (r'\b(flag|abnormal)\b|\bh\s*/\s*l\b', 'flag'),
    (r'\b(date|collected|taken|latest|previous)\b', 'date'),
    (r'\b(comment|note|remark|method|interpretation)\b', 'text'),
)


def heading_hint(label: str) -> str:
    text = re.sub(r'\s+', ' ', (label or '')).strip().lower()
    if not text:
        return ''
    for pattern, role in _HINTS:
        if re.search(pattern, text):
            return role
    return ''


# --- column profiling -------------------------------------------------------

def _evidence(cells: List[str]) -> Dict:
    filled = [c for c in cells if (c or '').strip()]
    n = len(filled)
    if not n:
        return {'filled': 0, 'date': 0.0, 'range': 0.0, 'unit': 0.0,
                'flag': 0.0, 'numeric': 0.0, 'percent': 0.0, 'distinct': 0}
    return {
        'filled': n,
        'date': round(sum(1 for c in filled if looks_like_date(c)) / n, 3),
        'range': round(sum(1 for c in filled if looks_like_range(c)) / n, 3),
        'unit': round(sum(1 for c in filled if looks_like_unit(c)) / n, 3),
        'flag': round(sum(1 for c in filled if looks_like_flag(c)) / n, 3),
        'numeric': round(sum(1 for c in filled if looks_like_measurement(c)) / n, 3),
        'percent': round(sum(1 for c in filled if '%' in c) / n, 3),
        'distinct': len({c.strip().lower() for c in filled}),
    }


def _role_from_evidence(ev: Dict, hint: str) -> Tuple[str, str]:
    """Decide a column's role from its cells, and say what decided it.

    Returns (role, basis). The basis travels all the way into the extraction
    record so a reading that rested on a column heading rather than on the data
    can be told apart from one the numbers confirmed.
    """
    if not ev['filled']:
        return (hint or 'empty'), ('heading' if hint else 'empty')
    if ev['date'] >= 0.6:
        return 'date', 'cells'
    if ev['range'] >= 0.5:
        return 'range', 'cells'
    if ev['flag'] >= 0.6:
        return 'flag', 'cells'
    if ev['unit'] >= 0.6 and ev['numeric'] < 0.4:
        return 'unit', 'cells'
    if ev['numeric'] >= 0.5:
        # A bare number could be a measurement, a baseline or a percentage of
        # one. Arithmetic decides in detect_relations; until then it is just a
        # number.
        return 'number', 'cells'
    if hint in ('unit', 'range', 'flag', 'text'):
        return hint, 'heading'
    return 'text', 'cells'


def _carry_qualifiers(header_rows: List[List[str]], width: int) -> List[str]:
    """Sparse rows above the heading row label groups of columns.

    Spirometry writes 'Pre-Bronch' once over three columns; a chemistry panel
    may write a specimen or a fasting state the same way. The label is carried
    forward over the columns it introduces -- structural, so it needs no
    knowledge of what the label says.
    """
    qualifiers = [''] * width
    current = ''
    for col in range(width):
        for row in header_rows:
            if col < len(row) and (row[col] or '').strip():
                current = row[col].strip()
                break
        qualifiers[col] = current
    return qualifiers


def _fit(expected: List[Optional[float]], actual: List[Optional[float]],
         tolerance: float) -> Optional[float]:
    """Median relative error between a column and a candidate formula for it.

    The median lets one OCR misread through without losing the relationship,
    but a relationship that only holds for half the rows is a coincidence, so
    most rows must agree as well.
    """
    pairs = [(e, a) for e, a in zip(expected, actual) if e is not None and a is not None]
    if len(pairs) < 2:
        return None
    errors = []
    for want, got in pairs:
        scale = max(abs(want), abs(got), 1.0)
        errors.append(abs(want - got) / scale)
    agree = sum(1 for e in errors if e <= 3 * tolerance) / len(errors)
    if agree < 0.6:
        return None
    return round(median(errors), 4)


def _percent_marked(col: Dict) -> bool:
    """A per-cent sign in the heading, or in most of the cells."""
    if '%' in (col.get('label') or ''):
        return True
    return (col.get('evidence') or {}).get('percent', 0) >= 0.5


def _off_scale(values: Dict[int, List[Optional[float]]], target: int,
               others: List[int]) -> bool:
    """True when the target column's magnitudes sit well away from the others'."""
    def magnitude(idx: int) -> Optional[float]:
        nums = [abs(v) for v in values.get(idx, []) if v not in (None, 0)]
        return median(nums) if nums else None

    here = magnitude(target)
    there = [m for m in (magnitude(i) for i in others) if m]
    if here is None or not there:
        return False
    return all(here / m > 8 or m / here > 8 for m in there)


def detect_relations(columns: List[Dict], data_rows: List[List[str]],
                     tolerance: float = 0.05) -> List[Dict]:
    """Find numeric columns that are arithmetic functions of other columns.

    '% of predicted' is the ratio of two other columns; '% change' is the change
    between two others. Finding them by arithmetic means the report can call them
    anything -- and it also catches a column mislabelled by OCR.
    """
    numeric = [c['index'] for c in columns if c['role'] == 'number']
    # Both relationships need three distinct columns: the derived one and the
    # two it is derived from.
    if len(numeric) < 3:
        return []

    def col_values(idx: int) -> List[Optional[float]]:
        out = []
        for row in data_rows:
            out.append(number_in(row[idx]) if idx < len(row) else None)
        return out

    values = {idx: col_values(idx) for idx in numeric}
    by_index = {c['index']: c for c in columns}
    candidates: List[Dict] = []

    for target in numeric:
        got = values[target]
        for a in numeric:
            if a == target:
                continue
            for b in numeric:
                if b in (target, a):
                    continue
                ratio = [
                    (100.0 * x / y) if (x is not None and y not in (None, 0)) else None
                    for x, y in zip(values[a], values[b])
                ]
                fit = _fit(ratio, got, tolerance)
                if fit is not None and fit <= tolerance:
                    candidates.append({'kind': 'percent_of', 'column': target,
                                       'measured': a, 'baseline': b, 'fit': fit})
                change = [
                    (100.0 * (y - x) / x) if (x not in (None, 0) and y is not None) else None
                    for x, y in zip(values[a], values[b])
                ]
                fit = _fit(change, got, tolerance)
                if fit is not None and fit <= tolerance:
                    candidates.append({'kind': 'percent_change', 'column': target,
                                       'from': a, 'to': b, 'fit': fit})

    # c = 100a/b rearranges to b = 100a/c, so a ratio triple fits three ways and
    # arithmetic alone cannot say which column is the derived one. The per-cent
    # sign settles it -- notation rather than vocabulary, so it reads the same in
    # any language. Failing that, the derived column is the one on a different
    # scale from the other two, because a percentage of a like quantity lands
    # near 100 while the quantities themselves do not.
    def preference(rel: Dict) -> Tuple[int, int, float]:
        target = by_index.get(rel['column'], {})
        others = [rel.get('measured'), rel.get('baseline'),
                  rel.get('from'), rel.get('to')]
        return (1 if _percent_marked(target) else 0,
                1 if _off_scale(values, rel['column'], [o for o in others if o is not None]) else 0,
                -rel['fit'])

    accepted: List[Dict] = []
    accepted_targets: set = set()
    accepted_parts: set = set()
    for rel in sorted(candidates, key=preference, reverse=True):
        parts = {rel[k] for k in ('measured', 'baseline', 'from', 'to') if k in rel}
        if rel['column'] in accepted_targets or rel['column'] in accepted_parts:
            continue
        if parts & accepted_targets:
            continue
        accepted.append(rel)
        accepted_targets.add(rel['column'])
        accepted_parts |= parts
    return sorted(accepted, key=lambda r: r['column'])


def _apply_relations(columns: List[Dict], relations: List[Dict]) -> None:
    by_index = {c['index']: c for c in columns}
    for rel in relations:
        target = by_index.get(rel['column'])
        if target is None:
            continue
        target['role'] = rel['kind']
        target['basis'] = 'arithmetic'
        target['derived_from'] = rel
        if rel['kind'] == 'percent_of':
            baseline = by_index.get(rel['baseline'])
            measured = by_index.get(rel['measured'])
            if baseline is not None and baseline['role'] == 'number':
                baseline['role'] = 'baseline'
                baseline['basis'] = 'arithmetic'
            if measured is not None and measured['role'] == 'number':
                measured['role'] = 'measured'
                measured['basis'] = 'arithmetic'

    # Arithmetic needs at least two rows to distinguish a real relationship
    # from a coincidence, so a one-row report reaches this point with every
    # number unclassified. Only now is the column heading allowed to decide.
    for col in columns:
        if col['role'] != 'number':
            continue
        if col['hint'] in ('baseline', 'percent_of', 'percent_change', 'measured'):
            col['role'] = col['hint']
            col['basis'] = 'heading'
        else:
            # Nothing said otherwise: a number in its own column, under its own
            # heading, is a measurement.
            col['role'] = 'measured'
            col['basis'] = 'default'


def _signature(columns: List[Dict]) -> str:
    """Stable id for a layout.

    Date headings are replaced by a placeholder so the same laboratory's report
    next month is recognised as the same format instead of looking brand new.
    """
    parts = []
    for col in columns:
        label = re.sub(r'\s+', ' ', col['label'] or '').strip().lower()
        if looks_like_date(label) or _DATE_IN_TEXT_RE.search(label):
            label = '<date>'
        qualifier = re.sub(r'\s+', ' ', col['qualifier'] or '').strip().lower()
        if looks_like_date(qualifier) or _DATE_IN_TEXT_RE.search(qualifier):
            qualifier = '<date>'
        parts.append('{}/{}:{}'.format(qualifier, label, col['role']))
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()[:16]


def _shape_of(col: Dict) -> str:
    """What the cells look like, before a role is decided.

    Confirmed user roles are stored against this, not against the automatic
    role: two readings that disagree on Pred vs %Pred still share a structure
    so the user's correction applies to both.
    """
    ev = col.get('evidence') or {}
    # Role is not consulted: a user correction must not change the structure
    # hash, or the confirmed reading would miss the next scan of the same grid.
    if ev.get('date', 0) >= 0.6:
        return 'date'
    if ev.get('range', 0) >= 0.5:
        return 'range'
    if ev.get('flag', 0) >= 0.6:
        return 'flag'
    if ev.get('unit', 0) >= 0.6 and ev.get('numeric', 0) < 0.4:
        return 'unit'
    if ev.get('numeric', 0) >= 0.5:
        return 'number'
    if col.get('role') == 'name':
        return 'name'
    return 'text'


def structure_of(description: Dict) -> str:
    parts = []
    for col in description.get('columns') or []:
        label = re.sub(r'\s+', ' ', col.get('label') or '').strip().lower()
        if looks_like_date(label) or _DATE_IN_TEXT_RE.search(label):
            label = '<date>'
        qualifier = re.sub(r'\s+', ' ', col.get('qualifier') or '').strip().lower()
        if looks_like_date(qualifier) or _DATE_IN_TEXT_RE.search(qualifier):
            qualifier = '<date>'
        parts.append('{}/{}:{}'.format(qualifier, label, _shape_of(col)))
    return hashlib.sha256('|'.join(parts).encode('utf-8')).hexdigest()[:16]


def _layout_from_roles(columns: List[Dict]) -> str:
    roles = {c['role'] for c in columns}
    if 'dated' in roles:
        return 'dated'
    if 'percent_of' in roles or 'percent_change' in roles or 'baseline' in roles:
        return 'derived'
    if 'measured' in roles:
        return 'measured'
    if 'stated' in roles:
        return 'stated'
    return 'unknown'


def describe(rows: List[List[str]], sep_idx: int, section: str = '',
             skip_name: Optional[re.Pattern] = None) -> Dict:
    """Describe a table's layout: one entry per column, plus a signature.

    `rows` is the whole pipe-table including heading rows; `sep_idx` is the
    index of the '---' row. `section` is any heading that introduced the table.
    `skip_name` matches rows that are metadata rather than results -- a report
    that prints its reference ranges on their own 'Reference' row would
    otherwise make a column of results look like a column of ranges.
    """
    header_rows = rows[:sep_idx]
    if not header_rows:
        return {'columns': [], 'relations': [], 'layout': 'unknown',
                'signature': '', 'structure': '', 'row_count': 0,
                'section': section, 'labels': [], 'qualifiers': []}
    labels = header_rows[-1]
    data_rows = [r for r in rows[sep_idx + 1:] if r and any((c or '').strip() for c in r)]
    if skip_name is not None:
        data_rows = [r for r in data_rows if not skip_name.search((r[0] or '').strip())]
    width = max([len(labels)] + [len(r) for r in data_rows])
    labels = list(labels) + [''] * (width - len(labels))
    qualifiers = _carry_qualifiers(header_rows[:-1], width)

    columns: List[Dict] = []
    for idx in range(width):
        cells = [row[idx] if idx < len(row) else '' for row in data_rows]
        ev = _evidence(cells)
        hint = heading_hint(labels[idx])
        if idx == 0:
            role, basis = 'name', 'position'
        else:
            role, basis = _role_from_evidence(ev, hint)
        col = {'index': idx, 'label': labels[idx].strip(), 'qualifier': qualifiers[idx],
               'role': role, 'basis': basis, 'hint': hint, 'evidence': ev}
        # A numeric column headed by a date holds that date's readings -- the
        # ordinary multi-date laboratory table.
        if role in ('number', 'date'):
            head_date = _DATE_IN_TEXT_RE.search(labels[idx])
            if head_date:
                col['role'] = 'dated'
                col['basis'] = 'heading date'
                col['date'] = head_date.group(1)
            elif role == 'date':
                col['role'] = 'dated'
                col['date'] = ''
        columns.append(col)

    relations = detect_relations(columns, data_rows)
    _apply_relations(columns, relations)

    roles = {c['role'] for c in columns}
    if 'dated' in roles:
        layout = 'dated'
    elif 'percent_of' in roles or 'percent_change' in roles or 'baseline' in roles:
        layout = 'derived'
    elif 'measured' in roles:
        layout = 'measured'
    else:
        layout = 'unknown'

    # A table of findings, visit facts or discharge fields has no numeric
    # measurement column. The payload is still a named value — whatever the
    # report printed in the first non-name column (or the one whose heading
    # already says 'value' / 'result'). Without this those rows were skipped
    # as 'no value in any measured column' and never reached the editor.
    if layout == 'unknown':
        candidates = [c for c in columns if c['index'] > 0 and c['role'] in ('text', 'empty')]
        # A heading that already says value/result is the payload. A Notes
        # column is commentary — it must not win over Finding or Category.
        preferred = [c for c in candidates if c.get('hint') == 'measured']
        if not preferred:
            preferred = [c for c in candidates if c.get('hint') != 'text']
        pick = preferred or candidates
        if pick:
            pick[0]['role'] = 'stated'
            pick[0]['basis'] = 'heading' if pick[0].get('hint') else 'default'
            layout = 'stated'

    described = {
        'columns': columns,
        'relations': relations,
        'layout': layout,
        'signature': _signature(columns),
        'row_count': len(data_rows),
        'section': section,
        'labels': labels,
        'qualifiers': qualifiers,
    }
    described['structure'] = structure_of(described)
    return described


# --- learned-format registry ------------------------------------------------

def roles_of(description: Dict) -> List[str]:
    return ['{}/{}={}'.format(c['qualifier'], c['label'], c['role'])
            for c in description.get('columns') or []]


def remember(store: Dict, description: Dict, now: Optional[datetime] = None) -> str:
    """Record this layout against the profile. Returns 'known' or 'new'.

    'known' means the same layout has been parsed before, so the roles derived
    now agree with a reading the user has already seen and had a chance to
    correct. 'new' means this is the first time and the reading deserves a
    closer look -- the extraction record says which.
    """
    signature = description.get('signature')
    if not signature:
        return 'unknown'
    registry = store.setdefault('report_formats', {})
    stamp = (now or datetime.now()).isoformat()
    roles = roles_of(description)
    entry = registry.get(signature)
    if entry:
        entry['seen_count'] = int(entry.get('seen_count') or 0) + 1
        entry['last_seen'] = stamp
        if not entry.get('structure'):
            entry['structure'] = description.get('structure') or structure_of(description)
        if description.get('from_user') or entry.get('confirmed'):
            # A confirmed (or just-overlaid) reading is the one to keep.
            # Automatic disagreement against it is not a new fact.
            if description.get('from_user'):
                entry['column_roles'] = column_roles_of(description)
                entry['roles'] = roles
            return 'known'
        if entry.get('roles') != roles:
            # Two readings of the same layout disagreed. Keep both: silently
            # overwriting would hide the fact that one of them is wrong.
            entry.setdefault('role_changes', []).append(
                {'at': stamp, 'from': entry.get('roles'), 'to': roles})
            entry['roles'] = roles
        return 'known'
    registry[signature] = {
        'signature': signature,
        'structure': description.get('structure') or structure_of(description),
        'layout': description.get('layout'),
        'section': description.get('section') or '',
        'roles': roles,
        'column_roles': column_roles_of(description),
        'seen_count': 1,
        'first_seen': stamp,
        'last_seen': stamp,
        'confirmed': False,
    }
    return 'new'


ALLOWED_ROLES = (
    'name', 'measured', 'dated', 'stated', 'baseline', 'percent_of',
    'percent_change', 'range', 'unit', 'flag', 'text', 'empty',
)


def column_roles_of(description: Dict) -> List[Dict]:
    return [{'index': c['index'], 'label': c.get('label') or '',
             'qualifier': c.get('qualifier') or '', 'role': c['role']}
            for c in description.get('columns') or []]


def find_by_structure(store: Dict, structure: str) -> Optional[Dict]:
    if not structure:
        return None
    matches = [e for e in (store.get('report_formats') or {}).values()
               if e.get('structure') == structure]
    if not matches:
        return None
    confirmed = [e for e in matches if e.get('confirmed')]
    pool = confirmed or matches
    return max(pool, key=lambda e: e.get('last_seen') or '')


def apply_column_roles(description: Dict, column_roles: List[Dict],
                       basis: str = 'user') -> bool:
    """Overlay a user's reading of the columns. Returns True if anything changed.

    The automatic signature is left alone: it is how we recognise the same
    grid next time. The user's roles live in column_roles and are what extract
    uses after this call.
    """
    by_index = {c['index']: c for c in description.get('columns') or []}
    changed = False
    for spec in column_roles or []:
        try:
            idx = int(spec.get('index'))
        except (TypeError, ValueError):
            continue
        role = str(spec.get('role') or '').strip()
        if role not in ALLOWED_ROLES or idx not in by_index:
            continue
        col = by_index[idx]
        if col['role'] != role:
            col['role'] = role
            col['basis'] = basis
            changed = True
        elif col.get('basis') != basis and basis == 'user':
            col['basis'] = basis
            changed = True
    if changed:
        description['layout'] = _layout_from_roles(description['columns'])
        description['from_user'] = True
    return changed


def apply_remembered(description: Dict, store: Dict) -> bool:
    """If the user has confirmed this structure, read it their way."""
    structure = description.get('structure') or structure_of(description)
    entry = find_by_structure(store, structure)
    if not entry or not entry.get('confirmed'):
        return False
    roles = entry.get('column_roles') or []
    if not roles:
        return False
    return apply_column_roles(description, roles, basis='user')


def confirm(store: Dict, description: Dict, column_roles: Optional[List[Dict]] = None,
            now: Optional[datetime] = None) -> Dict:
    """The user has accepted or corrected this layout. Reuse it next time."""
    if column_roles:
        apply_column_roles(description, column_roles, basis='user')
    remember(store, description, now=now)
    structure = description.get('structure') or structure_of(description)
    entry = find_by_structure(store, structure)
    if entry is None:
        signature = description.get('signature') or _signature(description.get('columns') or [])
        entry = (store.get('report_formats') or {}).get(signature)
    if entry is None:
        return {}
    entry['confirmed'] = True
    entry['column_roles'] = column_roles_of(description)
    entry['roles'] = roles_of(description)
    entry['confirmed_at'] = (now or datetime.now()).isoformat()
    return entry


def record_report_date(store: Dict, structure: str, date: str,
                       now: Optional[datetime] = None) -> None:
    """A date the user (or a sibling page) supplied for an undated layout."""
    if not structure or not date:
        return
    entry = find_by_structure(store, structure)
    if entry is None:
        return
    entry['last_report_date'] = date
    entry['last_report_date_at'] = (now or datetime.now()).isoformat()


def sibling_date(store: Dict, structure: str, now: Optional[datetime] = None,
                 within_hours: float = 2) -> str:
    """Date from another page of the same layout, uploaded recently.

    Several photos of one report lose the date that was only on page 1. The
    structure is the hook: a table matching one seen minutes earlier is almost
    certainly the same report.
    """
    entry = find_by_structure(store, structure)
    if not entry:
        return ''
    stamped = entry.get('last_report_date_at') or ''
    date = entry.get('last_report_date') or ''
    if not stamped or not date:
        return ''
    try:
        then = datetime.fromisoformat(stamped)
    except ValueError:
        return ''
    if abs(((now or datetime.now()) - then).total_seconds()) > within_hours * 3600:
        return ''
    return date


def learn_from_edit(store: Dict, before: Dict, after: Dict,
                    now: Optional[datetime] = None) -> Optional[str]:
    """Infer a layout fact from a row the user edited. Returns what was learned.

    Only edits that are hard to misread count. A single free-text tweak does
    not rewrite the format.
    """
    structure = (after or {}).get('format_structure') or (before or {}).get('format_structure')
    if not structure:
        return None
    entry = find_by_structure(store, structure)
    if entry is None:
        return None
    # They dated an undated filing: this layout has no date column.
    before_source = (before or {}).get('date_source')
    new_date = str((after or {}).get('date') or '').strip()
    old_date = str((before or {}).get('date') or '').strip()
    if before_source == 'filed' and new_date and new_date != old_date:
        record_report_date(store, structure, new_date, now=now)
        entry.setdefault('learned', []).append(
            {'at': (now or datetime.now()).isoformat(), 'kind': 'report_date',
             'date': new_date})
        return 'report_date'
    return None


def learn_from_delete(store: Dict, removed: Dict, remaining: List[Dict],
                      now: Optional[datetime] = None) -> Optional[str]:
    """If the user deleted every row that came from one column, that column
    is not a measurement for this layout."""
    structure = (removed or {}).get('format_structure')
    role = (removed or {}).get('source_role')
    if not structure or role not in ('measured', 'stated', 'dated',
                                     'percent_of', 'percent_change', 'baseline'):
        return None
    entry = find_by_structure(store, structure)
    if entry is None:
        return None
    left = [r for r in remaining
            if r.get('format_structure') == structure and r.get('source_role') == role]
    if left:
        return None
    # Demote that role on this structure. Name/range/unit stay put.
    roles = list(entry.get('column_roles') or [])
    changed = False
    for col in roles:
        if col.get('role') == role and col.get('index') != 0:
            col['role'] = 'text'
            changed = True
    if not changed:
        return None
    entry['column_roles'] = roles
    entry['confirmed'] = True
    entry.setdefault('learned', []).append(
        {'at': (now or datetime.now()).isoformat(), 'kind': 'dropped_column',
         'role': role})
    return 'dropped_column'


# --- extraction -------------------------------------------------------------

def _unit_for_row(description: Dict, row: List[str], name: str) -> str:
    for col in description['columns']:
        if col['role'] == 'unit' and col['index'] < len(row):
            cell = (row[col['index']] or '').strip().strip('()[]')
            if cell:
                return cell
    match = re.search(r'\(([^)]+)\)\s*$', name)
    if match and looks_like_unit(match.group(1)):
        return match.group(1)
    return ''


def _cell(row: List[str], idx: Optional[int]) -> str:
    if idx is None or idx >= len(row):
        return ''
    return (row[idx] or '').strip()


def _extra_key(col: Dict) -> str:
    key = ' '.join(x for x in (col['qualifier'], col['label']) if x).strip()
    return key or 'column {}'.format(col['index'])


def _partner(columns: List[Dict], measured: Dict, role: str) -> Optional[Dict]:
    """The column of `role` that belongs to this measurement.

    Arithmetic already says which measurement a percentage was computed from,
    so that wins. Failing that, a column in the same qualifier group is taken,
    then one anywhere in the table -- spirometry prints a single Predicted
    column and reuses it for both the pre- and post-bronchodilator readings.
    """
    candidates = [c for c in columns if c['role'] == role]
    if not candidates:
        return None
    for col in candidates:
        rel = col.get('derived_from') or {}
        if rel.get('measured') == measured['index'] or rel.get('to') == measured['index']:
            return col
    if role == 'baseline':
        for col in candidates:
            rel = next((c.get('derived_from') or {} for c in columns
                        if (c.get('derived_from') or {}).get('baseline') == col['index']
                        and (c.get('derived_from') or {}).get('measured') == measured['index']),
                       {})
            if rel:
                return col
    same_group = [c for c in candidates if c['qualifier'] == measured['qualifier']]
    if same_group:
        return same_group[0]
    # A percentage printed under another group heading belongs to that group's
    # own measurement, not to this one.
    if role != 'baseline' and any(c['qualifier'] for c in candidates):
        return None
    return candidates[0]


def extract(description: Dict, data_rows: List[List[str]],
            skip_name: Optional[re.Pattern] = None) -> Tuple[List[Dict], List[Dict]]:
    """Turn described rows into result records, plus a note of what was skipped.

    Every extra column the report carries is kept in `fields`, keyed by the
    report's own heading. Nothing is discarded because the schema has no place
    for it, and nothing needs adding to the schema when a new report kind turns
    up -- the editor renders whatever `fields` holds.
    """
    columns = description['columns']
    by_role: Dict[str, List[Dict]] = {}
    for col in columns:
        by_role.setdefault(col['role'], []).append(col)

    range_col = by_role['range'][0]['index'] if by_role.get('range') else None
    flag_col = by_role['flag'][0]['index'] if by_role.get('flag') else None
    measured_columns = (by_role.get('measured', []) + by_role.get('dated', [])
                        + by_role.get('stated', []))
    # When each measurement column sits under its own group heading, that
    # heading alone distinguishes the readings ('Pre-Bronch' / 'Post-Bronch').
    # Otherwise the column's own heading has to be part of the name.
    # Dated columns are told apart by the date they carry, so they never add to
    # the name; only undated measurement columns need a distinguishing suffix.
    undated = by_role.get('measured', [])
    group_labels = [c['qualifier'] for c in undated]
    qualifier_tells_apart = (len(undated) <= 1 or
                             len(set(group_labels)) == len(group_labels))
    results: List[Dict] = []
    skipped: List[Dict] = []

    for row_no, row in enumerate(data_rows):
        name = _cell(row, 0)
        if not name:
            skipped.append({'row': row_no, 'reason': 'no test name', 'cells': row})
            continue
        name = re.sub(r'^[*+\u2022]\s*', '', name).strip()
        if skip_name is not None and skip_name.search(name):
            skipped.append({'row': row_no, 'reason': 'heading or metadata row',
                            'name': name})
            continue
        unit = _unit_for_row(description, row, name)
        row_range = _cell(row, range_col).strip('()[]')
        flag = _cell(row, flag_col)

        emitted_before = len(results)
        for col in measured_columns:
            value = _cell(row, col['index'])
            if not value:
                continue
            qualifier = col['qualifier']
            if col['role'] == 'dated' or qualifier_tells_apart:
                suffix = qualifier
            else:
                suffix = ' '.join(b for b in (qualifier, col['label']) if b)
            test_name = name + (' ({})'.format(suffix) if suffix else '')

            reference = row_range
            notes: List[str] = []
            # Whatever else the report printed for this measurement is kept
            # under the report's own heading, so nothing is lost merely because
            # the profile has no field for it. Columns belonging to another
            # group describe another measurement and are left out.
            fields: Dict[str, str] = {}
            for other in columns:
                if other['role'] in ('name', 'measured', 'dated', 'stated',
                                     'unit', 'range', 'flag'):
                    continue
                if other['qualifier'] and qualifier and other['qualifier'] != qualifier:
                    continue
                cell = _cell(row, other['index'])
                if cell:
                    fields[_extra_key(other)] = cell

            baseline = _partner(columns, col, 'baseline')
            if baseline is not None:
                baseline_value = _cell(row, baseline['index'])
                if baseline_value:
                    reference = ' '.join(
                        x for x in (baseline['label'] or 'baseline', baseline_value, unit)
                        if x).strip()
                    fields.pop(_extra_key(baseline), None)

            percent = _partner(columns, col, 'percent_of')
            if percent is not None:
                cell = _cell(row, percent['index'])
                if cell:
                    against = (baseline['label'] if baseline is not None else '') or 'baseline'
                    notes.append('{}% of {}'.format(cell.rstrip('%'), against))
                    fields.pop(_extra_key(percent), None)

            change = _partner(columns, col, 'percent_change')
            if change is not None:
                cell = _cell(row, change['index'])
                if cell:
                    number = cell.rstrip('%')
                    signed = number if number.startswith('-') else '+' + number
                    notes.append('{} {}%'.format(change['label'] or 'change', signed))
                    fields.pop(_extra_key(change), None)

            # A stated finding is already complete as printed. Do not glue a
            # unit or flag onto 'Clear' or 'Pneumonia' — those columns belong
            # in fields under the report's own headings.
            if col['role'] != 'stated':
                if flag and flag.lower() not in value.lower():
                    value = (value + ' ' + flag).strip()
                if unit and not re.search(re.escape(unit), value, re.I):
                    value = (value + ' ' + unit).strip()

            record = {
                'test_name': test_name,
                'value': value,
                'reference_range': reference,
                'date': col.get('date', '') if col['role'] == 'dated' else '',
                'notes': ' \u00b7 '.join(notes),
            }
            if unit and col['role'] != 'stated':
                record['unit'] = unit
            if qualifier:
                record['qualifier'] = qualifier
            if description.get('section'):
                record['section'] = description['section']
            if fields:
                record['fields'] = fields
            record['source_role'] = col['role']
            record['format_structure'] = description.get('structure') or ''
            record['format_signature'] = description.get('signature') or ''
            results.append(record)
        if len(results) == emitted_before:
            skipped.append({'row': row_no, 'reason': 'no value in any measured column',
                            'name': name})

    return results, skipped


def parse_tables(tables: List[Dict], store: Optional[Dict] = None,
                 now: Optional[datetime] = None,
                 overlays: Optional[List[Dict]] = None
                 ) -> Tuple[List[Dict], List[Dict]]:
    """Describe, overlay a confirmed or supplied reading, extract, remember.

    `tables` is a list of {'rows': pipe-grid, 'sep_idx': int, 'section': str}.
    Returns (extractions, analyses). Each analysis carries familiarity
    ('new' / 'known') and whether a confirmed layout was applied.
    """
    store = store if store is not None else {}
    extractions: List[Dict] = []
    analyses: List[Dict] = []
    for index, table in enumerate(tables or []):
        rows = table.get('rows') or []
        sep_idx = table.get('sep_idx', 1)
        section = table.get('section') or ''
        skip_name = table.get('skip_name')
        description = describe(rows, sep_idx, section=section, skip_name=skip_name)
        if not description.get('columns'):
            continue
        overlay = _overlay_for(index, description, overlays)
        applied = False
        if overlay:
            applied = apply_column_roles(description, overlay, basis='user')
        elif store:
            applied = apply_remembered(description, store)
        sibling = sibling_date(store, description.get('structure') or '', now=now)
        rows_out, skipped = extract(description, rows[sep_idx + 1:], skip_name=skip_name)
        if sibling:
            for row in rows_out:
                if not row.get('date'):
                    row['date'] = sibling
                    row['date_source'] = 'sibling'
        familiarity = remember(store, description, now=now)
        dated = next((r.get('date') for r in rows_out if r.get('date')), '')
        if dated:
            record_report_date(store, description.get('structure') or '', dated, now=now)
        analysis = dict(description)
        analysis['familiarity'] = familiarity
        analysis['applied_confirmed'] = applied
        analyses.append(analysis)
        extractions.append({'rows': rows_out, 'skipped': skipped, 'analysis': analysis})
    return extractions, analyses


def _overlay_for(index: int, description: Dict,
                 overlays: Optional[List[Dict]]) -> Optional[List[Dict]]:
    for spec in overlays or []:
        roles = spec.get('column_roles')
        if not roles:
            continue
        if spec.get('structure') and spec['structure'] == description.get('structure'):
            return roles
        if spec.get('signature') and spec['signature'] == description.get('signature'):
            return roles
        if spec.get('index') == index:
            return roles
    return None
