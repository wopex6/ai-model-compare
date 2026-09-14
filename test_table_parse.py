"""Regression test: markdown lab table -> test_results must preserve
column alignment and decimal precision exactly."""
import re

_UNIT_RE = re.compile(r'\s*(?:mmol/L|umol/L|g/L|ng/mL|IU/L|U/L|pmol/L|mg/dL|mg/L|%|/[a-zA-Z]+)$', re.I)

RAW = """| Test        | 05-Aug-24 | 29-Oct-24 | 28-Dec-24 | 03-Apr-25 | Reference | Unit    |
|-------------|-----------|-----------|-----------|-----------|-----------|---------|
| S CHOL      | 6.7 H     | 4.2       | 6.4 H     | 4.3       | (3.5-5.5) | mmol/L  |
| S TRIG      | 0.8       | 0.5       | 0.8       | 0.6       | (<1.7)    | mmol/L  |
| S HDL-CHOL  | 1.76      | 1.77      | 1.62      | 1.66      | (>1.00)   | mmol/L  |
| S LDL-CHOL  | 4.6 H     | 2.2       | 4.4 H     | 2.4       | (<3.5)    | mmol/L  |
| S CHOL/HDLC | 3.8       | 2.4       | 4.0       | 2.6       | (<4.5)    | mmol/L  |
| S Non HDLC  | 4.9 H     | 2.4       | 4.8 H     | 2.6       | (<3.9)    | mmol/L  |"""

EXPECTED = {
    'S CHOL':      {'05-Aug-24': '6.7 H', '29-Oct-24': '4.2',  '28-Dec-24': '6.4 H', '03-Apr-25': '4.3'},
    'S TRIG':      {'05-Aug-24': '0.8',   '29-Oct-24': '0.5',  '28-Dec-24': '0.8',   '03-Apr-25': '0.6'},
    'S HDL-CHOL':  {'05-Aug-24': '1.76',  '29-Oct-24': '1.77', '28-Dec-24': '1.62',  '03-Apr-25': '1.66'},
    'S LDL-CHOL':  {'05-Aug-24': '4.6 H', '29-Oct-24': '2.2',  '28-Dec-24': '4.4 H', '03-Apr-25': '2.4'},
    'S CHOL/HDLC': {'05-Aug-24': '3.8',   '29-Oct-24': '2.4',  '28-Dec-24': '4.0',   '03-Apr-25': '2.6'},
    'S Non HDLC':  {'05-Aug-24': '4.9 H', '29-Oct-24': '2.4',  '28-Dec-24': '4.8 H', '03-Apr-25': '2.6'},
}


# A unitless ratio row (blank Unit cell) must still be parsed, not dropped.
RAW_UNITLESS = """| Test        | 05-Aug-24 | 03-Apr-25 | Reference | Unit    |
|-------------|-----------|-----------|-----------|---------|
| S CHOL      | 6.7 H     | 4.3       | (3.5-5.5) | mmol/L  |
| S CHOL/HDLC | 3.8       | 2.6       | (<4.5)    |         |"""

EXPECTED_UNITLESS = {
    'S CHOL':      {'05-Aug-24': '6.7 H', '03-Apr-25': '4.3'},
    'S CHOL/HDLC': {'05-Aug-24': '3.8',   '03-Apr-25': '2.6'},
}

# Iron-studies pathology report layout (dates as columns, Reference/Units columns)
RAW_IRON = """| Date | 07-Dec-23 | 05-Aug-24 | 03-Apr-25 | 13-May-25 | Reference | Units |
|------|-----------|-----------|-----------|-----------|-----------|-------|
| Time F-Fast | 0816 F | 0928 F | 0956 F | 1339 | | |
| Lab Id. | 967607283 | 970980440 | 972342598 | 9747100030 | | |
| S IRON | 23 | 22 | 33 H | 33 H | (5-30) | umol/L |
| S TRF | 2.1 | 2.3 | 2.2 | 2.2 | (2.0-3.2) | g/L |
| S TRF SAT | 44 | 38 | 60 H | 60 H | (10-45) | % |
| S FERRITIN | 224 | 229 | 251 | 260 | (30-500) | ng/mL |"""

EXPECTED_IRON = {
    'S IRON':      {'07-Dec-23': '23',    '05-Aug-24': '22',    '03-Apr-25': '33 H', '13-May-25': '33 H'},
    'S TRF':       {'07-Dec-23': '2.1',   '05-Aug-24': '2.3',   '03-Apr-25': '2.2',  '13-May-25': '2.2'},
    'S TRF SAT':   {'07-Dec-23': '44',    '05-Aug-24': '38',    '03-Apr-25': '60 H', '13-May-25': '60 H'},
    'S FERRITIN':  {'07-Dec-23': '224',   '05-Aug-24': '229',   '03-Apr-25': '251',  '13-May-25': '260'},
}

# Same report but transposed (dates as rows, Reference/Units as rows)
RAW_IRON_TRANSPOSED = """| | S IRON | S TRF | S TRF SAT | S FERRITIN |
|---|---|---|---|---|
| 07-Dec-23 | 23 | 2.1 | 44 | 224 |
| 05-Aug-24 | 22 | 2.3 | 38 | 229 |
| 03-Apr-25 | 33 H | 2.2 | 60 H | 251 |
| 13-May-25 | 33 H | 2.2 | 60 H | 260 |
| Reference | (5-30) | (2.0-3.2) | (10-45) | (30-500) |
| Units | umol/L | g/L | % | ng/mL |"""


def _load_parser():
    from ai_compare.medical_advisor_health_context import (
        HealthContextManager, _canonicalize_lab_tables,
    )
    import inspect, textwrap

    src = inspect.getsource(HealthContextManager.analyze_and_store)
    # Pull the nested parser out so we can unit test it without an API call
    lines = src.splitlines()
    start = next(i for i, l in enumerate(lines) if 'def _parse_markdown_tables' in l)
    end = next(i for i, l in enumerate(lines) if 'def _clean_and_parse' in l)
    body = textwrap.dedent('\n'.join(lines[start:end]))
    ns = {'re': re}
    exec(body, ns)
    _parse_markdown_tables = ns['_parse_markdown_tables']
    return lambda raw: _parse_markdown_tables(_canonicalize_lab_tables(raw))


def check(parse, raw, expected, label):
    results = parse(raw)
    got = {}
    for r in results:
        got.setdefault(r['test_name'], {})[r['date']] = r['value']

    failures = []
    for test, dates in expected.items():
        if test not in got:
            failures.append(f"{test}: ROW MISSING ENTIRELY")
            continue
        for date, want in dates.items():
            have = got.get(test, {}).get(date)
            # the parser appends the unit, so compare the numeric/flag prefix
            have_core = _UNIT_RE.sub('', have or '').strip()
            if have_core != want:
                failures.append(f"{test} @ {date}: expected {want!r}, got {have_core!r}")

    total = sum(len(d) for d in expected.values())
    print(f"[{label}] parsed {len(results)} results (expected {total})")
    if failures:
        print(f"[{label}] {len(failures)} FAILURE(S):")
        for f in failures:
            print("  -", f)
        return False
    print(f"[{label}] PASS")
    return True


def main():
    parse = _load_parser()
    ok = check(parse, RAW, EXPECTED, "alignment+decimals")
    ok &= check(parse, RAW_UNITLESS, EXPECTED_UNITLESS, "unitless ratio row")
    ok &= check(parse, RAW_IRON, EXPECTED_IRON, "iron-studies columns")
    ok &= check(parse, RAW_IRON_TRANSPOSED, EXPECTED_IRON, "iron-studies transposed")
    if not ok:
        raise SystemExit(1)
    print("\nALL PASS: rows kept, dates aligned, decimals preserved, transposed tables handled")


if __name__ == '__main__':
    main()
