"""End-to-end OCR accuracy check against a real stored lab report.

Runs the production extraction pipeline on an image file and scores the result
against a known-correct transcription.  This calls the OpenAI API, so it costs
money and is not part of the offline test suite - run it deliberately:

    python test_ocr_live.py health_uploaded_documents/23/<file>.jpg

The expected values below were verified by eye against the printed report.
"""

import sys
from ai_compare.table_consensus import parse_markdown_grids

# Verified against the source document: 4 date columns, no more.
EXPECTED = {
    'S CHOL':      {'05-Aug-24': '6.7 H', '29-Oct-24': '4.2',  '28-Dec-24': '6.4 H', '03-Apr-25': '4.3'},
    'S TRIG':      {'05-Aug-24': '0.8',   '29-Oct-24': '0.5',  '28-Dec-24': '0.8',   '03-Apr-25': '0.6'},
    'S HDL-CHOL':  {'05-Aug-24': '1.76',  '29-Oct-24': '1.77', '28-Dec-24': '1.62',  '03-Apr-25': '1.66'},
    'S LDL-CHOL':  {'05-Aug-24': '4.6 H', '29-Oct-24': '2.2',  '28-Dec-24': '4.4 H', '03-Apr-25': '2.4'},
    'S CHOL/HDLC': {'05-Aug-24': '3.8',   '29-Oct-24': '2.4',  '28-Dec-24': '4.0',   '03-Apr-25': '2.6'},
    'S Non HDLC':  {'05-Aug-24': '4.9 H', '29-Oct-24': '2.4',  '28-Dec-24': '4.8 H', '03-Apr-25': '2.6'},
}
EXPECTED_DATE_COLUMNS = 4


def _norm_name(s):
    return ' '.join((s or '').replace('*', '').replace('+', '').split()).upper()


def _norm_date(s):
    return (s or '').strip().replace('/', '-').upper()


def _norm_value(s):
    return ' '.join((s or '').replace('mmol/L', '').split()).upper()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    path = sys.argv[1]

    from app import _extract_text_from_file_bytes
    import os
    with open(path, 'rb') as fh:
        data = fh.read()
    ext = os.path.splitext(path)[1].lower()

    print(f"Running extraction on {path} ...\n")
    text = _extract_text_from_file_bytes(data, ext)
    print("--- extracted text ---")
    print(text)
    print("--- end ---\n")

    # Flatten to {(TEST, DATE): VALUE}
    got = {}
    date_cols = set()
    for grid in parse_markdown_grids(text):
        header = grid[0]
        for row in grid[1:]:
            name = _norm_name(row[0])
            for i, cell in enumerate(row[1:], start=1):
                if i >= len(header):
                    continue
                col = _norm_date(header[i])
                if any(ch.isdigit() for ch in col) and '-' in col:
                    date_cols.add(col)
                    got[(name, col)] = _norm_value(cell)

    total = sum(len(v) for v in EXPECTED.values())
    correct, problems = 0, []
    for test, dates in EXPECTED.items():
        for date, want in dates.items():
            actual = got.get((_norm_name(test), _norm_date(date)))
            if actual is None:
                problems.append(f"MISSING  {test} @ {date} (expected {want})")
            elif actual != _norm_value(want):
                problems.append(f"WRONG    {test} @ {date}: want {want!r}, got {actual!r}")
            else:
                correct += 1

    extra_cols = len(date_cols) - EXPECTED_DATE_COLUMNS
    print(f"date columns found: {len(date_cols)} (expected {EXPECTED_DATE_COLUMNS})"
          + (f"  <-- {extra_cols:+d} INVENTED/LOST" if extra_cols else "  OK"))
    print(f"values correct: {correct}/{total} ({100 * correct // total}%)\n")
    for p in problems:
        print(" ", p)
    if problems or extra_cols:
        raise SystemExit(1)
    print("PERFECT - every value matches the printed report")


if __name__ == '__main__':
    main()
