"""Tests for document-agnostic OCR consensus merging.

The reference table below is used purely as a TEST FIXTURE - a known-correct
transcription to measure against.  It is not used by, or available to, the
production code path.
"""

from ai_compare.table_consensus import merge_by_consensus, parse_markdown_grids

TRUTH = """| Test | 05-Aug-24 | 29-Oct-24 | 28-Dec-24 | 03-Apr-25 | Reference | Unit |
|---|---|---|---|---|---|---|
| S CHOL | 6.7 H | 4.2 | 6.4 H | 4.3 | (3.5-5.5) | mmol/L |
| S TRIG | 0.8 | 0.5 | 0.8 | 0.6 | (<1.7) | mmol/L |
| S HDL-CHOL | 1.76 | 1.77 | 1.62 | 1.66 | (>1.00) | mmol/L |
| S LDL-CHOL | 4.6 H | 2.2 | 4.4 H | 2.4 | (<3.5) | mmol/L |
| S CHOL/HDLC | 3.8 | 2.4 | 4.0 | 2.6 | (<4.5) |  |
| S Non HDLC | 4.9 H | 2.4 | 4.8 H | 2.6 | (<3.9) | mmol/L |"""


def _cells(text):
    """Flatten a markdown table into {(row_name, col_header): value}."""
    out = {}
    for grid in parse_markdown_grids(text):
        header = grid[0]
        for row in grid[1:]:
            for i, val in enumerate(row[1:], start=1):
                if i < len(header):
                    out[(row[0].strip(), header[i].strip())] = val.strip()
    return out


def _diff(got, want):
    gc, wc = _cells(got), _cells(want)
    problems = []
    for key, expected in wc.items():
        actual = gc.get(key)
        if actual is None:
            problems.append(f"MISSING {key[0]} @ {key[1]}")
        elif actual != expected:
            problems.append(f"{key[0]} @ {key[1]}: want {expected!r}, got {actual!r}")
    return problems


def test_single_attempt_passes_through():
    assert not _diff(merge_by_consensus([TRUTH]), TRUTH)
    print("PASS single attempt is returned unchanged")


def test_majority_beats_truncated_decimals():
    """Two good readings should outvote one that truncated decimals."""
    truncated = TRUTH.replace('| 1.76 | 1.77 | 1.62 | 1.66 |',
                              '| 1.7 | 1.4 | 1.6 | 1.6 |')
    merged = merge_by_consensus([truncated, TRUTH, TRUTH])
    problems = _diff(merged, TRUTH)
    assert not problems, problems
    print("PASS truncated decimals outvoted by majority")


def test_tie_prefers_more_precision():
    """With one good and one truncated reading, keep the more precise digits."""
    truncated = TRUTH.replace('| 1.76 |', '| 1.7 |')
    merged = merge_by_consensus([truncated, TRUTH])
    assert _cells(merged)[('S HDL-CHOL', '05-Aug-24')] == '1.76'
    print("PASS tie broken toward the more precise reading")


def test_dropped_row_recovered():
    """A row missing from one attempt survives if other attempts saw it."""
    without = '\n'.join(l for l in TRUTH.splitlines() if 'S CHOL/HDLC' not in l)
    merged = merge_by_consensus([without, TRUTH, TRUTH])
    assert ('S CHOL/HDLC', '03-Apr-25') in _cells(merged), "unitless row was lost"
    print("PASS row dropped by one attempt recovered from the others")


def test_hallucinated_row_suppressed_when_requested():
    """Opt-in vote threshold drops a row only one attempt invented."""
    extra = TRUTH + "\n| Request No 12345 | 1.0 | 1.0 | 1.0 | 1.0 | | |"
    merged = merge_by_consensus([extra, TRUTH, TRUTH], min_row_votes=2)
    names = {k[0].lower() for k in _cells(merged)}
    assert not any('request' in n for n in names), "spurious row survived"
    print("PASS opt-in vote threshold suppresses a single-attempt row")


def test_default_never_drops_rows():
    """REGRESSION: a vote threshold once deleted 21 of 24 real rows.

    When attempts disagree about table structure, row keys stop lining up and
    genuine rows look like one-offs.  The default must keep them.
    """
    metadata_table = ("| Date Time | Lab ID | Latest Results |\n"
                      "|---|---|---|\n"
                      "| 05Aug24 09:24 | 0921F | 1.6 |")
    merged = merge_by_consensus([TRUTH, metadata_table, TRUTH])
    problems = _diff(merged, TRUTH)
    assert not problems, f"real rows lost: {problems[:5]}"
    print("PASS default keeps every real row when attempts disagree on structure")


def test_code_fences_stripped():
    """REGRESSION: a ```markdown wrapper leaked into the extracted text."""
    fenced = "```markdown\n" + TRUTH + "\n```"
    merged = merge_by_consensus([fenced, TRUTH])
    assert '```' not in merged, "code fence leaked into output"
    assert not _diff(merged, TRUTH)
    print("PASS code fences stripped")


def test_content_score_detects_collapse():
    """A collapsed reading must score below a complete one, so callers can reject it."""
    from ai_compare.table_consensus import content_score
    collapsed = ("| Date Time | Lab ID | Latest Results |\n"
                 "|---|---|---|\n"
                 "| 05Aug24 09:24 | 0921F | 1.6 |")
    assert content_score(collapsed) < content_score(TRUTH)
    print("PASS content score ranks a collapsed reading below a complete one")


def test_column_shift_outvoted():
    """A reading that drops a column (shifting values left) is excluded."""
    shifted = TRUTH.replace('| S CHOL | 6.7 H | 4.2 | 6.4 H | 4.3 |',
                            '| S CHOL | 6.7 H | 6.4 H | 4.3 |')
    merged = merge_by_consensus([shifted, TRUTH, TRUTH])
    problems = _diff(merged, TRUTH)
    assert not problems, problems
    print("PASS column-shifted reading rejected")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print()
    if failed:
        print(f"{failed}/{len(tests)} FAILED")
        raise SystemExit(1)
    print(f"ALL {len(tests)} CONSENSUS TESTS PASSED")


if __name__ == '__main__':
    main()
