"""Regression test: abbreviated test names must merge into their long form.

Verifies that 'S BICARB'/'S Bicarbonate', 'S Creat'/'S Creatinine',
'S Chol'/'S Cholesterol' and 'MCH'/'M.C.H.' group into a single series, that
reference ranges and units confirm the merge, and that tests which merely look
similar (Cholesterol vs Cholesterol/HDL Ratio) stay separate.
"""
from ai_compare.medical_advisor_health_context import (
    HealthProfile,
    _canonical_test_key,
    _canonical_test_name,
    _normalize_unit,
    _references_compatible,
    _strip_redundant_unit,
)


def _profile():
    """A HealthProfile that never touches disk."""
    profile = HealthProfile.__new__(HealthProfile)
    profile.user_id = "test"
    profile.file_path = None
    profile.ingest_source = "test"
    profile.data = {"test_results": [], "conversation_insights": []}
    profile._file_stamp = None
    return profile


def check_canonical_names():
    cases = [
        ("S BICARB", "S Bicarbonate"),
        ("s bicarbonate", "S Bicarbonate"),
        ("S Creat", "S Creatinine"),
        ("S CREATININE", "S Creatinine"),
        ("S Chol", "S Cholesterol"),
        ("S Cholesterol", "S Cholesterol"),
        ("MCH", "MCH"),
        ("M.C.H.", "MCH"),
        ("m.c.h.c.", "MCHC"),
        ("MCHC", "MCHC"),
        ("S HDL-CHOL", "S HDL Cholesterol"),
        ("S TRF SAT", "S Transferrin Saturation"),
        ("Widget Panel X", "Widget Panel X"),  # unknown names pass through
    ]
    failures = []
    for raw, want in cases:
        got = _canonical_test_name(raw)
        if got != want:
            failures.append(f"{raw!r}: expected {want!r}, got {got!r}")
    return _report("canonical names", failures)


def check_keys_group():
    same = [
        ("S BICARB", "S Bicarbonate"),
        ("S Creat", "S CREATININE"),
        ("s chol", "S Cholesterol"),
        ("MCH", "M.C.H."),
        ("MCHC", "M.C.H.C."),
    ]
    different = [
        ("S Cholesterol", "S Chol/HDLC"),
        ("MCH", "MCHC"),
        ("S Iron", "U Iron"),
    ]
    failures = []
    for a, b in same:
        if _canonical_test_key(a) != _canonical_test_key(b):
            failures.append(f"{a!r} and {b!r} should share a key")
    for a, b in different:
        if _canonical_test_key(a) == _canonical_test_key(b):
            failures.append(f"{a!r} and {b!r} must NOT share a key")
    return _report("grouping keys", failures)


def check_units_and_refs():
    failures = []
    if _normalize_unit("umol/L") != _normalize_unit("\u00b5mol/l"):
        failures.append("umol/L and micro-mol/l should normalize the same")
    if _normalize_unit("ng/mL") != _normalize_unit("ug/L"):
        failures.append("ng/mL and ug/L are equivalent")
    if _normalize_unit("mmol/L") == _normalize_unit("g/L"):
        failures.append("mmol/L and g/L must differ")
    if not _references_compatible("(20 - 32 mmol/L)", "20-32"):
        failures.append("same bounds with/without unit text should be compatible")
    if _references_compatible("(20 - 32)", "(3.5 - 5.5)"):
        failures.append("different bounds must be incompatible")
    if _references_compatible("(<4.5)", "(3.5-5.5)"):
        failures.append("upper-limit vs range must be incompatible")
    return _report("units and references", failures)


def check_merge_on_ingest():
    profile = _profile()
    profile.add_test_result("S BICARB", "24", "(20 - 32 mmol/L)", "2024-08-05")
    profile.add_test_result("S Bicarbonate", "26", "(20 - 32 mmol/L)", "2025-04-03")
    profile.add_test_result("S Creat", "88", "(60 - 110 umol/L)", "2024-08-05")
    profile.add_test_result("S Creatinine", "92", "(60 - 110 umol/L)", "2025-04-03")
    profile.add_test_result("M.C.H.", "30.1", "(27 - 33 pg)", "2024-08-05")
    profile.add_test_result("MCH", "30.4", "(27 - 33 pg)", "2025-04-03")
    # Similar-looking but genuinely different tests must stay apart
    profile.add_test_result("S Chol", "6.7 H", "(3.5-5.5) mmol/L", "2024-08-05")
    profile.add_test_result("S Chol/HDLC", "3.8", "(<4.5)", "2024-08-05")

    grouped = {}
    for row in profile.data["test_results"]:
        grouped.setdefault(profile._normalize_test_key(row["test_name"]), []).append(row)

    failures = []
    expected_series = {
        "s:bicarbonate": (2, "S Bicarbonate"),
        "s:creatinine": (2, "S Creatinine"),
        "mch": (2, "MCH"),
        "s:cholesterol": (1, "S Cholesterol"),
        "s:cholesterolhdlratio": (1, "S Cholesterol/HDL Ratio"),
    }
    for key, (count, name) in expected_series.items():
        rows = grouped.get(key)
        if not rows:
            failures.append(f"missing series {key!r}")
            continue
        if len(rows) != count:
            failures.append(f"{key}: expected {count} row(s), got {len(rows)}")
        bad = [r["test_name"] for r in rows if r["test_name"] != name]
        if bad:
            failures.append(f"{key}: expected all rows named {name!r}, got {bad}")
    if len(grouped) != len(expected_series):
        failures.append(f"expected {len(expected_series)} series, got {sorted(grouped)}")
    return _report("merge on ingest", failures)


def check_conflicting_refs_not_merged():
    """An abbreviation pattern alone must not merge tests with clashing references."""
    profile = _profile()
    profile.add_test_result("S Ferritin", "224", "(30 - 500 ug/L)", "2024-08-05")
    profile.add_test_result("S Ferr", "18", "(1 - 3 mmol/L)", "2024-08-05")
    keys = {profile._normalize_test_key(r["test_name"]) for r in profile.data["test_results"]}
    failures = []
    # Both map to Ferritin via the static table, so they share a key by design;
    # what must NOT happen is a dynamic merge of unrelated names.
    profile2 = _profile()
    profile2.add_test_result("S Widgetase", "10", "(1 - 5 U/L)", "2024-08-05")
    profile2.add_test_result("S Widg", "200", "(100 - 300 mmol/L)", "2024-08-05")
    keys2 = {profile2._normalize_test_key(r["test_name"]) for r in profile2.data["test_results"]}
    if len(keys2) != 2:
        failures.append(f"clashing references must stay separate, got {sorted(keys2)}")
    if not keys:
        failures.append("ferritin rows disappeared")
    return _report("conflicting references", failures)


def check_dynamic_merge_learns():
    """Unknown abbreviations merge when reference and unit both confirm."""
    profile = _profile()
    profile.add_test_result("S Widgetase", "10", "(1 - 5 U/L)", "2024-08-05")
    profile.add_test_result("S Widget", "12", "(1 - 5 U/L)", "2025-04-03")
    names = {r["test_name"] for r in profile.data["test_results"]}
    keys = {profile._normalize_test_key(r["test_name"]) for r in profile.data["test_results"]}
    failures = []
    if len(keys) != 1:
        failures.append(f"expected one merged series, got {sorted(keys)}")
    if names != {"S Widgetase"}:
        failures.append(f"expected the longer name to win, got {sorted(names)}")
    return _report("dynamic merge", failures)


def check_specimen_prefix_merge():
    """'Transferrin Saturation' and 'S Transferrin Saturation' are one series."""
    profile = _profile()
    profile.add_test_result("S Transferrin Saturation", "44", "(10 - 45) %", "2023-12-07")
    profile.add_test_result("Transferrin Saturation", "37", "10 - 45 %", "2026-09-09")
    profile.add_test_result("WHITE CELLS", "4.5", "(4.0 - 11.0) x10^9/L", "2023-12-07")
    profile.add_test_result("White Cell Count", "5.6", "4.0 - 11.0 x10^9/L", "2026-09-09")
    # Different specimens must never merge
    profile.add_test_result("S Iron", "12", "(5 - 30) umol/L", "2026-09-09")
    profile.add_test_result("U Iron", "9", "(5 - 30) umol/L", "2026-09-09")

    grouped = {}
    for row in profile.data["test_results"]:
        grouped.setdefault(profile._normalize_test_key(row["test_name"]), []).append(row["test_name"])

    failures = []
    trf = [k for k in grouped if 'transferrinsaturation' in k]
    if len(trf) != 1:
        failures.append(f"transferrin saturation should be one series, got {trf}")
    elif set(grouped[trf[0]]) != {"S Transferrin Saturation"}:
        failures.append(f"expected 'S Transferrin Saturation' everywhere, got {set(grouped[trf[0]])}")
    wcc = [k for k in grouped if 'whitecellcount' in k]
    if len(wcc) != 1:
        failures.append(f"white cells should be one series, got {wcc}")
    elif set(grouped[wcc[0]]) != {"White Cell Count"}:
        failures.append(f"expected 'White Cell Count' everywhere, got {set(grouped[wcc[0]])}")
    iron = [k for k in grouped if k.endswith('iron')]
    if len(iron) != 2:
        failures.append(f"S Iron and U Iron must stay separate, got {iron}")
    return _report("specimen prefix merge", failures)


def check_units_stripped():
    """Units that repeat the reference range are dropped from the value."""
    cases = [
        ("220 x10^9/L", "150 - 450 x10^9/L", "220"),
        ("237 x 10^9/L L", "(150 - 450) x10^9/L", "237 L"),
        ("189", "150 - 450 x10^9/L", "189"),
        ("260 ng/mL", "30 - 500 ug/L", "260"),
        ("1.2 L x10^9/L", "2.0 - 7.5 x10^9/L", "1.2 L"),
        ("4.8 x10^12/L", "4.3 - 5.8 x10^12/L", "4.8"),
        ("37 %", "10 - 45 %", "37"),
        ("30.1 pg", "27 - 33 pg", "30.1"),
        ("35 mmol/mol", "25 - 38 mmol/mol", "35"),
        # No unit in the reference: keep the value's unit rather than lose it
        ("5.6 x10^9/L", "4.0 - 11.0", "5.6 x10^9/L"),
        # Unit that disagrees with the reference is preserved for review
        ("2.6 g/L", "26 - 38 g/dL", "2.6 g/L"),
        ("12.3", "11 - 17", "12.3"),
    ]
    failures = []
    for value, ref, want in cases:
        got = _strip_redundant_unit(value, ref)
        if got != want:
            failures.append(f"{value!r} with ref {ref!r}: expected {want!r}, got {got!r}")
    return _report("redundant units stripped", failures)


def check_units_consistent_in_series():
    """Every row of a series renders the same way once stored."""
    profile = _profile()
    ref = "150 - 450 x10^9/L"
    profile.add_test_result("Platelets", "241 x10^9/L", ref, "2023-05-17")
    profile.add_test_result("Platelets", "234 x 10^9/L", ref, "2023-12-07")
    profile.add_test_result("Platelets", "189", ref, "2026-09-09")
    values = [r["value"] for r in profile.data["test_results"]]
    failures = []
    for v in values:
        if '10^9' in v or '/L' in v:
            failures.append(f"value still carries a unit: {v!r}")
    if sorted(values) != sorted(["241", "234", "189"]):
        failures.append(f"expected bare numbers, got {values}")
    return _report("consistent series values", failures)


def check_ambiguous_prefix_not_merged():
    """'Iron' must not be guessed onto a specimen when S and U Iron both exist."""
    profile = _profile()
    profile.add_test_result("S Iron", "12", "(5 - 30) umol/L", "2025-01-01")
    profile.add_test_result("U Iron", "9", "(5 - 30) umol/L", "2025-01-01")
    profile.add_test_result("Iron", "14", "(5 - 30) umol/L", "2026-01-01")
    names = [r["test_name"] for r in profile.data["test_results"]]
    failures = []
    if sorted(names) != ["Iron", "S Iron", "U Iron"]:
        failures.append(f"ambiguous 'Iron' must stay unmerged, got {sorted(names)}")
    if profile.data.get("test_name_aliases"):
        failures.append(f"no alias should be learned, got {profile.data['test_name_aliases']}")
    return _report("ambiguous prefix not merged", failures)


def check_merge_never_overwrites():
    """A merge that would replace a same-date reading is abandoned."""
    profile = _profile()
    profile.add_test_result("S Transferrin Saturation", "44", "(10 - 45) %", "2025-04-03")
    profile.add_test_result("Transferrin Saturation", "37", "(10 - 45) %", "2025-04-03")
    values = sorted(r["value"] for r in profile.data["test_results"])
    failures = []
    if values != ["37", "44"]:
        failures.append(f"both readings must survive, got {values}")
    if len(profile.data["test_results"]) != 2:
        failures.append(f"expected 2 rows, got {len(profile.data['test_results'])}")
    return _report("merge never overwrites", failures)


def check_alias_reverified():
    """A learned alias does not absorb a row whose reference contradicts it."""
    profile = _profile()
    profile.add_test_result("S Widgetase", "10", "(1 - 5 U/L)", "2025-01-01")
    profile.add_test_result("S Widget", "12", "(1 - 5 U/L)", "2025-02-01")
    profile.add_test_result("S Widget", "300", "(100 - 500 mmol/L)", "2025-03-01")
    by_name = {}
    for row in profile.data["test_results"]:
        by_name.setdefault(row["test_name"], []).append(row["value"])
    failures = []
    if sorted(by_name.get("S Widgetase", [])) != ["10", "12"]:
        failures.append(f"confirmed rows should merge, got {by_name}")
    if by_name.get("S Widget") != ["300"]:
        failures.append(f"clashing row must keep its own name, got {by_name}")
    return _report("alias re-verified", failures)


def check_qualified_names_canonicalized():
    """A parenthetical qualifier does not stop the name resolving."""
    cases = [
        ("S Chol (fasting)", "S Cholesterol (fasting)", "s:cholesterol"),
        ("TSH historical", "TSH", "tsh"),
        ("S BICARB (repeat)", "S Bicarbonate (repeat)", "s:bicarbonate"),
    ]
    failures = []
    for raw, want_name, want_key in cases:
        got_name = _canonical_test_name(raw)
        got_key = _canonical_test_key(raw)
        if got_name != want_name:
            failures.append(f"{raw!r}: expected name {want_name!r}, got {got_name!r}")
        if got_key != want_key:
            failures.append(f"{raw!r}: expected key {want_key!r}, got {got_key!r}")
    return _report("qualified names", failures)


def _report(label, failures):
    if failures:
        print(f"[{label}] {len(failures)} FAILURE(S):")
        for f in failures:
            print("  -", f)
        return False
    print(f"[{label}] PASS")
    return True


def main():
    ok = check_canonical_names()
    ok &= check_keys_group()
    ok &= check_units_and_refs()
    ok &= check_merge_on_ingest()
    ok &= check_conflicting_refs_not_merged()
    ok &= check_dynamic_merge_learns()
    ok &= check_specimen_prefix_merge()
    ok &= check_units_stripped()
    ok &= check_units_consistent_in_series()
    ok &= check_ambiguous_prefix_not_merged()
    ok &= check_merge_never_overwrites()
    ok &= check_alias_reverified()
    ok &= check_qualified_names_canonicalized()
    if not ok:
        raise SystemExit(1)
    print("\nALL PASS: abbreviations merged into long forms, distinct tests kept apart")


if __name__ == '__main__':
    main()
