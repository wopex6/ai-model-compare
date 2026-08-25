"""Regression test: markdown lab table -> test_results must preserve
column alignment and decimal precision exactly."""
import re

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


def _load_parser():
    from ai_compare.medical_advisor_health_context import HealthContextManager
    import inspect, textwrap

    src = inspect.getsource(HealthContextManager.analyze_and_store)
    # Pull the nested parser out so we can unit test it without an API call
    lines = src.splitlines()
    start = next(i for i, l in enumerate(lines) if 'def _parse_markdown_tables' in l)
    end = next(i for i, l in enumerate(lines) if 'def _clean_and_parse' in l)
    body = textwrap.dedent('\n'.join(lines[start:end]))
    ns = {'re': re}
    exec(body, ns)
    return ns['_parse_markdown_tables']


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
            have_core = (have or '').replace('mmol/L', '').strip()
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
    if not ok:
        raise SystemExit(1)
    print("\nALL PASS: rows kept, dates aligned, decimals preserved")


if __name__ == '__main__':
    main()
