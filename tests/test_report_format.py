"""A report's layout must be derived from its contents, not from its wording.

Every test here uses headings the code has never been told about -- or no
headings at all -- because the point of ai_compare/report_format.py is that a
report kind nobody anticipated parses without anyone editing the parser.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_compare import report_format as rf


def _table(text):
    """Turn a markdown pipe table into (rows, separator index)."""
    rows = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line.startswith('|'):
            continue
        rows.append([c.strip() for c in line.split('|')[1:-1]])
    sep = next(i for i, r in enumerate(rows) if rf.is_separator_row(r))
    return rows, sep


import re

# The caller decides which row labels are metadata; this mirrors the pattern
# ai_compare/medical_advisor_health_context.py passes in.
META = re.compile(r'^(Date|Time|Lab|Reference|Unit|Units|Name of|Patient|Page|Report)', re.I)


def _read(text, section=''):
    rows, sep = _table(text)
    description = rf.describe(rows, sep, section=section, skip_name=META)
    results, skipped = rf.extract(description, rows[sep + 1:], skip_name=META)
    return description, results, skipped


def _roles(description):
    return [c['role'] for c in description['columns']]


# --- roles come from the cells ----------------------------------------------

def test_reference_and_unit_columns_need_no_headings():
    """The old parser found the reference and unit columns by matching the words
    'reference' and 'unit' in the heading. Here both headings are blank."""
    description, results, _ = _read('''
        | Analyte | | | |
        | --- | --- | --- | --- |
        | Potassium | 5.9 | 3.5 - 5.5 | mmol/L |
        | Sodium | 139 | 135 - 145 | mmol/L |
    ''')
    assert _roles(description) == ['name', 'measured', 'range', 'unit']
    potassium = next(r for r in results if r['test_name'] == 'Potassium')
    assert potassium['value'] == '5.9 mmol/L'
    assert potassium['reference_range'] == '3.5 - 5.5'
    assert potassium['unit'] == 'mmol/L'


def test_a_word_column_is_not_mistaken_for_a_unit():
    """'Serum' is a specimen, not a unit. Short bare words only read as units
    when they are short enough or carry unit notation."""
    description, _, _ = _read('''
        | Test | Specimen | Result | Units |
        | --- | --- | --- | --- |
        | Glucose | Plasma | 5.4 | mmol/L |
        | Calcium | Serum | 2.31 | mmol/L |
    ''')
    roles = dict((c['label'], c['role']) for c in description['columns'])
    assert roles['Specimen'] == 'text'
    assert roles['Units'] == 'unit'
    assert roles['Result'] == 'measured'


def test_flag_column_is_found_from_its_cells():
    description, results, _ = _read('''
        | Test | 05-Aug-24 | | Reference |
        | --- | --- | --- | --- |
        | Cholesterol | 6.7 | H | 3.0 - 5.5 |
    ''')
    assert 'flag' in _roles(description)
    assert results[0]['value'] == '6.7 H'
    assert results[0]['date'] == '05-Aug-24'


def test_dated_columns_still_give_one_row_per_date():
    """The ordinary multi-date laboratory table must not change."""
    _, results, _ = _read('''
        | Test | 05-Aug-24 | 29-Oct-24 | 28-Dec-24 | Reference | Units |
        | --- | --- | --- | --- | --- | --- |
        | S CHOL | 6.7 H | 4.2 | 6.4 H | (3.0-5.5) | mmol/L |
    ''')
    assert [r['date'] for r in results] == ['05-Aug-24', '29-Oct-24', '28-Dec-24']
    # The date belongs in the date field, never in the name.
    assert {r['test_name'] for r in results} == {'S CHOL'}
    assert [r['value'] for r in results] == ['6.7 H mmol/L', '4.2 mmol/L', '6.4 H mmol/L']


# --- roles come from arithmetic ---------------------------------------------

def test_percentage_of_a_baseline_is_found_by_arithmetic_not_by_wording():
    """No heading here says 'predicted' or 'reference' in any form the code
    knows. The third column is 100 x the first divided by the second, which is
    the only reason it reads as a derived percentage."""
    description, results, _ = _read('''
        | Measure | Got | Norm | Ratio % |
        | --- | --- | --- | --- |
        | Alpha | 0.96 | 1.62 | 59 |
        | Beta | 1.47 | 2.03 | 72 |
        | Gamma | 4.10 | 5.00 | 82 |
    ''')
    assert _roles(description) == ['name', 'measured', 'baseline', 'percent_of']
    assert [c['basis'] for c in description['columns'][1:]] == ['arithmetic'] * 3
    alpha = results[0]
    assert alpha['value'] == '0.96'
    # The baseline is labelled with the report's own word for it.
    assert alpha['reference_range'] == 'Norm 1.62'
    assert alpha['notes'] == '59% of Norm'
    assert '0.96' not in [r['value'] for r in results][1:]


def test_a_baseline_is_never_stored_as_a_measurement():
    _, results, _ = _read('''
        | Measure | Got | Norm | Ratio % |
        | --- | --- | --- | --- |
        | Alpha | 0.96 | 1.62 | 59 |
        | Beta | 1.47 | 2.03 | 72 |
    ''')
    values = [r['value'] for r in results]
    assert values == ['0.96', '1.47']
    assert '1.62' not in values and '59' not in values


def test_group_headings_split_one_row_into_separate_measurements():
    """A sparse heading row spanning several columns marks phases or specimens
    of the same measurement. Each becomes its own result, named with the
    report's own wording, and none of them invents a date."""
    _, results, _ = _read('''
        | | Before | | | After | | |
        | | Got | Norm | Ratio % | Got | Ratio % | Shift % |
        | --- | --- | --- | --- | --- | --- | --- |
        | Alpha | 0.96 | 1.62 | 59 | 1.30 | 80 | 35.4 |
        | Beta | 1.47 | 2.03 | 72 | 1.37 | 67 | -6.8 |
    ''')
    names = [r['test_name'] for r in results]
    assert 'Alpha (Before)' in names and 'Alpha (After)' in names
    after = next(r for r in results if r['test_name'] == 'Alpha (After)')
    assert after['value'] == '1.30'
    assert '80% of Norm' in after['notes']
    assert '+35.4%' in after['notes']
    # A single baseline column serves both phases.
    assert after['reference_range'] == 'Norm 1.62'
    assert all(not r['date'] for r in results)


def test_one_row_falls_back_to_the_heading_and_says_so():
    """Arithmetic needs two rows to tell a relationship from a coincidence, so a
    single-row table has to lean on the heading -- and the record must admit
    that, because the reading is weaker."""
    description, results, _ = _read('''
        | | Actual | Pred | %Pred |
        | --- | --- | --- | --- |
        | DLCO (ml/min/mmHg) | 13.37 | 16.93 | 79 |
    ''')
    assert _roles(description) == ['name', 'measured', 'baseline', 'percent_of']
    assert [c['basis'] for c in description['columns'][1:]] == ['heading'] * 3
    assert results[0]['test_name'] == 'DLCO (ml/min/mmHg)'
    assert results[0]['value'] == '13.37 ml/min/mmHg'


def test_unrecognised_columns_are_kept_under_the_reports_own_headings():
    """Nothing is dropped because the profile has no field for it."""
    _, results, _ = _read('''
        | Test | Result | Method | Comment |
        | --- | --- | --- | --- |
        | Vitamin D | 58 nmol/L | LC-MS/MS | repeat in 6 months |
    ''')
    assert results[0]['fields'] == {'Method': 'LC-MS/MS',
                                    'Comment': 'repeat in 6 months'}


def test_skipped_rows_say_why():
    _, results, skipped = _read('''
        | Test | Result |
        | --- | --- |
        | Reference | 3.5 - 5.5 |
        | Potassium | 5.9 |
        | Sodium | |
    ''')
    assert [r['test_name'] for r in results] == ['Potassium']
    reasons = {s.get('name'): s['reason'] for s in skipped}
    assert reasons['Reference'] == 'heading or metadata row'
    assert reasons['Sodium'] == 'no value in any measured column'


def test_section_heading_between_tables_is_recorded():
    description, results, _ = _read('''
        | Test | Result |
        | --- | --- |
        | DLCO | 13.37 |
    ''', section='DIFFUSION')
    assert description['section'] == 'DIFFUSION'
    assert results[0]['section'] == 'DIFFUSION'


# --- recognising a layout that has been seen before -------------------------

def test_same_layout_next_month_is_recognised_despite_new_dates():
    """A signature that changed whenever the dates changed would call every
    report new. Date headings collapse to a placeholder so the same laboratory's
    next report is recognised."""
    august, _ = _table('''
        | Test | 05-Aug-24 | Reference | Units |
        | --- | --- | --- | --- |
        | S CHOL | 6.7 | 3.0 - 5.5 | mmol/L |
    ''')
    october, _ = _table('''
        | Test | 29-Oct-24 | Reference | Units |
        | --- | --- | --- | --- |
        | S CHOL | 4.2 | 3.0 - 5.5 | mmol/L |
    ''')
    first = rf.describe(august, 1)
    second = rf.describe(october, 1)
    assert first['signature'] == second['signature']

    store = {}
    assert rf.remember(store, first) == 'new'
    assert rf.remember(store, second) == 'known'
    entry = store['report_formats'][first['signature']]
    assert entry['seen_count'] == 2
    assert entry['confirmed'] is False


def test_a_different_layout_is_not_taken_for_a_known_one():
    lab, lab_sep = _table('''
        | Test | 05-Aug-24 | Reference |
        | --- | --- | --- |
        | S CHOL | 6.7 | 3.0 - 5.5 |
    ''')
    lung, lung_sep = _table('''
        | Measure | Got | Norm | Ratio % |
        | --- | --- | --- | --- |
        | Alpha | 0.96 | 1.62 | 59 |
        | Beta | 1.47 | 2.03 | 72 |
    ''')
    store = {}
    rf.remember(store, rf.describe(lab, lab_sep))
    assert rf.remember(store, rf.describe(lung, lung_sep)) == 'new'
    assert len(store['report_formats']) == 2


def test_two_readings_of_one_layout_that_disagree_are_both_kept():
    """Overwriting silently would hide the fact that one reading is wrong."""
    rows, sep = _table('''
        | Test | Result |
        | --- | --- |
        | S CHOL | 6.7 |
    ''')
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    changed = dict(description)
    changed['columns'] = [dict(c) for c in description['columns']]
    changed['columns'][1]['role'] = 'baseline'
    assert rf.remember(store, changed) == 'known'
    entry = store['report_formats'][description['signature']]
    assert entry['role_changes']
    assert entry['role_changes'][0]['from'] != entry['role_changes'][0]['to']


# --- the five sample reports (FBC, biochem, radiology, clinic, discharge) --

FBC = '''
| Test | Result | Units | Reference Range |
| --- | --- | --- | --- |
| Haemoglobin | 142 | g/L | 130-175 |
| Haematocrit | 0.42 | ratio | 0.38-0.50 |
| RBC Count | 4.8 | x10^12/L | 4.2-5.8 |
| WBC Count | 6.1 | x10^9/L | 4.0-11.0 |
| Platelets | 250 | x10^9/L | 150-400 |
'''

BIOCHEM = '''
| Test | Result | Units | Reference Range |
| --- | --- | --- | --- |
| Total Cholesterol | 5.8 | mmol/L | <5.5 |
| LDL Cholesterol | 3.7 | mmol/L | <3.0 |
| HDL Cholesterol | 1.2 | mmol/L | >1.0 |
| Triglycerides | 1.9 | mmol/L | <1.7 |
| ALT | 32 | U/L | <40 |
| AST | 28 | U/L | <40 |
| Ferritin | 180 | ug/L | 30-300 |
| Transferrin Saturation | 35 | % | 20-45 |
'''

RADIOLOGY = '''
| Region | Finding | Severity | Notes |
| --- | --- | --- | --- |
| Lungs | Clear | None | No consolidation |
| Heart | Normal size | None | Normal silhouette |
| Mediastinum | Normal contours | None | No widening |
| Pleura | No effusion | None | Symmetric |
| Bones | No acute abnormality | None | Ribs intact |
'''

CLINIC = '''
| Category | Value | Notes |
| --- | --- | --- |
| Reason for Visit | Dyslipidaemia review | Routine follow-up |
| BP | 130/80 mmHg | Sitting |
| BMI | 28 kg/m2 | Overweight range |
| Symptoms | None | Asymptomatic |
| Assessment | Dyslipidaemia | Primary |
| Plan | Start statin | Review in 3 months |
'''

DISCHARGE = '''
| Field | Value | Notes |
| --- | --- | --- |
| Admission Diagnosis | Pneumonia | Right lower lobe |
| Discharge Diagnosis | Resolved pneumonia | Completed antibiotics |
| Length of Stay | 4 days | Uncomplicated |
| Key Investigation | Chest X-ray | Consolidation resolved |
| Medication on Discharge | Amoxicillin-clavulanate | 5-day course |
| Follow-up | GP in 1 week | Routine |
'''


def test_full_blood_count_uses_cells_not_heading_words():
    description, results, skipped = _read(FBC, section='Full Blood Count')
    assert description['layout'] == 'measured'
    assert _roles(description) == ['name', 'measured', 'unit', 'range']
    assert not skipped
    hb = next(r for r in results if r['test_name'] == 'Haemoglobin')
    assert hb['value'] == '142 g/L' and hb['reference_range'] == '130-175'
    assert hb['unit'] == 'g/L' and hb['section'] == 'Full Blood Count'
    plt = next(r for r in results if r['test_name'] == 'Platelets')
    assert plt['value'] == '250 x10^9/L' and plt['reference_range'] == '150-400'


def test_biochemistry_reads_inequality_reference_ranges():
    _, results, skipped = _read(BIOCHEM, section='Biochemistry Panel')
    assert not skipped
    chol = next(r for r in results if r['test_name'] == 'Total Cholesterol')
    assert chol['value'] == '5.8 mmol/L' and chol['reference_range'] == '<5.5'
    hdl = next(r for r in results if r['test_name'] == 'HDL Cholesterol')
    assert hdl['reference_range'] == '>1.0'
    sat = next(r for r in results if r['test_name'] == 'Transferrin Saturation')
    assert sat['value'] == '35 %' and sat['reference_range'] == '20-45'


def test_radiology_findings_are_not_dropped_as_unmeasured():
    """A structured findings table has no numeric result column. The finding
    is still a named value; severity and notes stay under the report's own
    headings so the editor can show them."""
    description, results, skipped = _read(RADIOLOGY, section='Radiology Structured Findings')
    assert description['layout'] == 'stated'
    assert _roles(description) == ['name', 'stated', 'text', 'text']
    assert not skipped
    lungs = next(r for r in results if r['test_name'] == 'Lungs')
    assert lungs['value'] == 'Clear'
    assert lungs['fields'] == {'Severity': 'None', 'Notes': 'No consolidation'}
    assert 'None' not in lungs['value']


def test_clinic_visit_keeps_every_row_including_prose():
    _, results, skipped = _read(CLINIC, section='Clinic Visit Summary')
    assert not skipped
    names = {r['test_name'] for r in results}
    assert names == {'Reason for Visit', 'BP', 'BMI', 'Symptoms',
                     'Assessment', 'Plan'}
    bp = next(r for r in results if r['test_name'] == 'BP')
    assert bp['value'] == '130/80 mmHg'
    assert bp['fields']['Notes'] == 'Sitting'
    plan = next(r for r in results if r['test_name'] == 'Plan')
    assert plan['value'] == 'Start statin'
    assert plan['fields']['Notes'] == 'Review in 3 months'


def test_discharge_summary_stores_fields_the_schema_does_not_declare():
    _, results, skipped = _read(DISCHARGE, section='Hospital Discharge Summary')
    assert not skipped
    med = next(r for r in results if r['test_name'] == 'Medication on Discharge')
    assert med['value'] == 'Amoxicillin-clavulanate'
    assert med['fields']['Notes'] == '5-day course'
    stay = next(r for r in results if r['test_name'] == 'Length of Stay')
    assert stay['value'] == '4 days'


def test_chinese_headings_and_one_ocr_typo_still_find_the_ratio():
    """The ratio is in the numbers, not in the words. Headings the code has
    never seen, plus one mistyped percentage, must not flip which column is
    the measurement."""
    description, results, skipped = _read('''
        | 项目 | 测得 | 预计 | 占比% |
        | --- | --- | --- | --- |
        | Alpha | 0.96 | 1.62 | 59 |
        | Beta | 1.47 | 2.03 | 72 |
        | Gamma | 4.10 | 5.00 | 99 |
    ''')
    assert not skipped
    assert _roles(description) == ['name', 'measured', 'baseline', 'percent_of']
    assert [c['basis'] for c in description['columns'][1:]] == ['arithmetic'] * 3
    alpha = next(r for r in results if r['test_name'] == 'Alpha')
    assert alpha['value'] == '0.96'
    assert '1.62' in alpha['reference_range']
    assert '59%' in alpha['notes']
    values = [r['value'] for r in results]
    assert '1.62' not in values and '59' not in values
    # The mistyped 99 is still that row's percentage, not a measurement.
    gamma = next(r for r in results if r['test_name'] == 'Gamma')
    assert gamma['value'] == '4.10'
    assert '99%' in gamma['notes']


# --- cell shape helpers -----------------------------------------------------

def test_cell_shape_helpers():
    assert rf.looks_like_date('05-Aug-24') and rf.looks_like_date('2024-08-05')
    assert not rf.looks_like_date('Pred') and not rf.looks_like_date('59')
    assert rf.looks_like_range('3.5 - 5.5') and rf.looks_like_range('< 2.0')
    assert not rf.looks_like_range('5.9')
    assert rf.looks_like_unit('mmol/L') and rf.looks_like_unit('L')
    assert rf.looks_like_unit('10^9/L') and not rf.looks_like_unit('Serum')
    assert not rf.looks_like_unit('None'), 'a severity of None is not a unit'
    assert rf.looks_like_flag('H') and not rf.looks_like_flag('HbA1c')
    assert rf.number_in('6.7 H mmol/L') == 6.7
    assert rf.number_in('1,234') == 1234.0
    assert rf.number_in('no numbers here') is None


# --- learning from a confirmed reading --------------------------------------

def test_structure_survives_a_role_disagreement():
    """Pred vs %Pred disagree on role but share a grid. Confirmed roles key
    off the cells, not the automatic signature."""
    rows, sep = _table('''
        | Measure | Got | Norm | Ratio % |
        | --- | --- | --- | --- |
        | Alpha | 0.96 | 1.62 | 59 |
        | Beta | 1.47 | 2.03 | 72 |
    ''')
    first = rf.describe(rows, sep)
    changed = dict(first)
    changed['columns'] = [dict(c) for c in first['columns']]
    changed['columns'][2]['role'] = 'dated'
    assert first['structure'] == rf.structure_of(changed)
    assert first['signature'] != rf._signature(changed['columns'])


def test_confirmed_roles_are_applied_on_the_next_scan():
    rows, sep = _table('''
        | Test | Result | Other |
        | --- | --- | --- |
        | Finding | Clear | None |
        | Category | Chest | —
    ''')
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    # User says the second column is stated and the third is text.
    rf.confirm(store, description, [
        {'index': 1, 'role': 'stated'},
        {'index': 2, 'role': 'text'},
    ])
    again = rf.describe(rows, sep)
    assert rf.apply_remembered(again, store) is True
    assert [c['role'] for c in again['columns']] == ['name', 'stated', 'text']
    assert all(c['basis'] == 'user' for c in again['columns'][1:])
    results, skipped = rf.extract(again, rows[sep + 1:])
    assert not skipped
    assert [r['test_name'] for r in results] == ['Finding', 'Category']
    assert results[0]['source_role'] == 'stated'
    assert results[0]['format_structure'] == description['structure']


def test_dating_a_filed_row_records_the_report_date():
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False}
    }}
    before = {'format_structure': 'struct1', 'date': '2026-09-26',
              'date_source': 'filed'}
    after = {'format_structure': 'struct1', 'date': '2024-08-05'}
    assert rf.learn_from_edit(store, before, after) == 'report_date'
    assert store['report_formats']['sig1']['last_report_date'] == '2024-08-05'


def test_deleting_every_row_from_a_column_drops_that_role():
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False,
                 'column_roles': [
                     {'index': 0, 'role': 'name'},
                     {'index': 1, 'role': 'measured'},
                     {'index': 2, 'role': 'stated'},
                 ]}
    }}
    removed = {'format_structure': 'struct1', 'source_role': 'stated',
               'test_name': 'Finding'}
    remaining = [{'format_structure': 'struct1', 'source_role': 'measured'}]
    assert rf.learn_from_delete(store, removed, remaining) == 'dropped_column'
    roles = [c['role'] for c in store['report_formats']['sig1']['column_roles']]
    assert roles == ['name', 'measured', 'text']
    assert store['report_formats']['sig1']['confirmed'] is True


def test_sibling_date_fills_an_undated_page_of_the_same_layout():
    from datetime import datetime
    rows, sep = _table('''
        | Test | Result |
        | --- | --- |
        | S CHOL | 6.7 |
    ''')
    description = rf.describe(rows, sep)
    store = {}
    now = datetime(2026, 9, 26, 13, 0, 0)
    rf.remember(store, description, now=now)
    rf.record_report_date(store, description['structure'], '2024-08-05', now=now)
    later = datetime(2026, 9, 26, 13, 20, 0)
    assert rf.sibling_date(store, description['structure'], now=later) == '2024-08-05'
    too_late = datetime(2026, 9, 26, 16, 0, 0)
    assert rf.sibling_date(store, description['structure'], now=too_late) == ''
