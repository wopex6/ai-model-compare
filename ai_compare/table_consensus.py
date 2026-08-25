"""Document-agnostic consensus merging for OCR'd markdown tables.

Vision OCR of dense tables fails in random, uncorrelated ways: a digit after the
decimal point gets dropped, a column gets skipped, a row goes missing.  Because
the errors are random rather than systematic, running the same extraction several
times and taking a majority vote per cell removes most of them.

Nothing here knows anything about lab reports, test names or units - it operates
purely on markdown table structure, so it works for any tabular document.
"""

import re
from collections import Counter

__all__ = ["parse_markdown_grids", "merge_by_consensus", "grid_to_markdown"]

_SEP_RE = re.compile(r'^[\s|:\-]+$')


def _is_separator(line):
    """True for markdown alignment rows like |---|:--:|."""
    stripped = line.strip()
    return bool(stripped.startswith('|') and '-' in stripped and _SEP_RE.match(stripped))


def _split_row(line):
    """Split a markdown table line into its cells."""
    return [c.strip() for c in line.strip().strip('|').split('|')]


def strip_code_fences(text):
    """Remove markdown code-fence lines, which models often wrap output in."""
    return '\n'.join(ln for ln in (text or '').splitlines()
                     if not ln.strip().startswith('```'))


def parse_markdown_grids(text):
    """Extract markdown tables from ``text``.

    Returns a list of grids, where each grid is a list of rows and each row is a
    list of cell strings.  Separator rows and code fences are discarded.
    """
    grids = []
    current = []
    for line in strip_code_fences(text).splitlines():
        if line.strip().startswith('|'):
            if not _is_separator(line):
                current.append(_split_row(line))
        else:
            if current:
                grids.append(current)
                current = []
    if current:
        grids.append(current)
    return grids


def content_score(text):
    """Count non-empty body cells, as a proxy for how much data a reading holds.

    Used to guarantee that merging never returns less data than the best single
    reading it was given.
    """
    total = 0
    for grid in parse_markdown_grids(text):
        for row in grid[1:]:
            total += sum(1 for c in row if c and c.strip())
    return total


def _norm(cell):
    return re.sub(r'\s+', ' ', (cell or '').strip()).lower()


def _decimal_places(value):
    """Number of digits after the decimal point in the first number found."""
    match = re.search(r'\d+\.(\d+)', value or '')
    return len(match.group(1)) if match else 0


def _pick(values):
    """Majority vote over candidate cell values.

    Ties are broken toward the value carrying more decimal digits, then the
    longer string.  Rationale: OCR drops printed digits far more often than it
    invents them, so when two readings are equally frequent the more precise one
    is the safer choice.
    """
    candidates = [v for v in values if v is not None and v.strip() != '']
    if not candidates:
        return ''
    counts = Counter(candidates)
    top = max(counts.values())
    tied = [v for v, c in counts.items() if c == top]
    if len(tied) == 1:
        return tied[0]
    return sorted(tied, key=lambda v: (_decimal_places(v), len(v)), reverse=True)[0]


def merge_by_consensus(texts, min_row_votes=None):
    """Merge several OCR attempts of the same document into one consensus text.

    ``texts`` is an ordered list of OCR outputs (best-effort first).  Attempts
    whose table shape disagrees with the majority are excluded from voting, then
    each remaining cell is decided by majority vote.

    Rows are kept only if they appear in at least ``min_row_votes`` attempts.
    This defaults to 1 - keeping every row any attempt saw - because discarding
    rows is far more damaging than keeping a doubtful one: when attempts disagree
    about table structure, vote thresholds above 1 can delete most of the real
    data.  Callers who specifically want spurious-row suppression and know the
    attempts are structurally consistent can raise it.
    """
    texts = [t for t in (texts or []) if t and t.strip()]
    if not texts:
        return ''
    if len(texts) == 1:
        return texts[0]

    per_attempt = [parse_markdown_grids(t) for t in texts]
    if not any(per_attempt):
        return texts[0]

    # Merge the Nth table of each attempt with the Nth table of the others.
    table_count = Counter(len(g) for g in per_attempt).most_common(1)[0][0]
    if table_count == 0:
        return texts[0]

    merged_tables = []
    for table_idx in range(table_count):
        grids = [a[table_idx] for a in per_attempt if len(a) > table_idx and a[table_idx]]
        if not grids:
            continue
        merged = _merge_grids(grids, min_row_votes)
        if merged:
            merged_tables.append(merged)

    if not merged_tables:
        return texts[0]

    # Preserve any non-table narrative from the first attempt.
    preamble = [ln for ln in strip_code_fences(texts[0]).splitlines()
                if not ln.strip().startswith('|') and ln.strip()]
    parts = merged_tables[:]
    if preamble:
        parts = ['\n'.join(preamble)] + parts
    return '\n\n'.join(grid_to_markdown(g) if isinstance(g, list) else g for g in parts)


def _merge_grids(grids, min_row_votes=None):
    """Vote cell by cell across several readings of one table."""
    # Attempts that disagree about the number of columns are reading the table
    # structure differently; exclude them rather than let them shift values.
    width = Counter(len(row) for g in grids for row in g).most_common(1)[0][0]
    kept = []
    for g in grids:
        rows = [r for r in g if len(r) == width]
        if len(rows) >= 2:  # need a header plus at least one body row
            kept.append(rows)
    if not kept:
        return None

    if min_row_votes is None:
        min_row_votes = 1

    # Header: vote positionally.
    header = [_pick([k[0][c] for k in kept if len(k[0]) > c]) for c in range(width)]

    # Body: key rows by their first cell so row order differences do not matter.
    row_votes = Counter()
    row_cells = {}
    order = []
    for k in kept:
        for row in k[1:]:
            key = _norm(row[0])
            if not key:
                continue
            if key not in row_cells:
                row_cells[key] = []
                order.append(key)
            row_cells[key].append(row)
            row_votes[key] += 1

    body = []
    for key in order:
        if row_votes[key] < min_row_votes:
            continue
        readings = row_cells[key]
        body.append([_pick([r[c] for r in readings if len(r) > c]) for c in range(width)])

    if not body:
        return None
    return [header] + body


def grid_to_markdown(grid):
    """Render a grid (list of rows of cells) back into a markdown table."""
    if not grid:
        return ''
    width = max(len(r) for r in grid)
    padded = [list(r) + [''] * (width - len(r)) for r in grid]
    lines = ['| ' + ' | '.join(padded[0]) + ' |',
             '|' + '|'.join(['---'] * width) + '|']
    for row in padded[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(lines)
