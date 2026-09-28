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


def test_moving_a_field_value_to_a_slot_teaches_the_column_role():
    """User re-types a wrong column's value into the right box: the layout
    learns that column was really the unit."""
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False,
                 'column_roles': [
                     {'index': 0, 'label': 'Name', 'qualifier': '', 'role': 'name'},
                     {'index': 1, 'label': 'Reading', 'qualifier': '', 'role': 'measured'},
                     {'index': 2, 'label': 'O2', 'qualifier': '', 'role': 'text'},
                 ]}
    }}
    before = {'format_structure': 'struct1', 'fields': {'O2': 'mmHg'}}
    after = {'format_structure': 'struct1', 'unit': 'mmHg', 'fields': {}}
    learned = rf.learn_from_edit(store, before, after)
    assert learned and 'O2' in learned
    roles = {c['index']: c['role'] for c in store['report_formats']['sig1']['column_roles']}
    assert roles[2] == 'unit'
    assert store['report_formats']['sig1']['confirmed'] is True


def test_clearing_a_field_demotes_its_column_to_text():
    """Emptying a bogus column's value means it was never data."""
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False,
                 'column_roles': [
                     {'index': 0, 'label': 'Name', 'qualifier': '', 'role': 'name'},
                     {'index': 1, 'label': 'Spurious', 'qualifier': '', 'role': 'stated'},
                 ]}
    }}
    before = {'format_structure': 'struct1', 'fields': {'Spurious': 'junk'}}
    after = {'format_structure': 'struct1', 'fields': {}}
    learned = rf.learn_from_edit(store, before, after)
    assert learned and 'Spurious' in learned
    roles = {c['index']: c['role'] for c in store['report_formats']['sig1']['column_roles']}
    assert roles[1] == 'text'


def test_untouched_fields_teach_nothing():
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False,
                 'column_roles': [
                     {'index': 0, 'label': 'Name', 'qualifier': '', 'role': 'name'},
                     {'index': 1, 'label': 'Extra', 'qualifier': '', 'role': 'text'},
                 ]}
    }}
    row = {'format_structure': 'struct1', 'fields': {'Extra': 'abc'}}
    assert rf.learn_from_edit(store, row, dict(row)) is None
    roles = {c['index']: c['role'] for c in store['report_formats']['sig1']['column_roles']}
    assert roles == {0: 'name', 1: 'text'}


def test_learned_role_is_applied_on_the_next_scan():
    """End to end: a user moves a fields value into a canonical slot, and the
    next scan of the same grid reads that column with its new role."""
    rows, sep = _table('''
        | Analyte | Got | Note |
        | --- | --- | --- |
        | Alpha | 0.96 | Run A |
        | Beta | 1.47 | Run B |
    ''')
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    results, _ = rf.extract(description, rows[sep + 1:])
    assert 'Note' in (results[0].get('fields') or {})
    # The user's edit: the value sat under 'Note' but belongs to 'unit'.
    before = dict(results[0])
    after = dict(results[0])
    after['fields'] = {}
    after['unit'] = before['fields']['Note']
    assert rf.learn_from_edit(store, before, after)
    # Rescan the identical grid: the learned role applies before extract.
    again = rf.describe(rows, sep)
    assert rf.apply_remembered(again, store) is True
    results2, _ = rf.extract(again, rows[sep + 1:])
    assert 'Note' not in (results2[0].get('fields') or {})
    assert results2[0]['unit'] == 'Run A' or 'Run A' in results2[0]['value']


def test_renamed_qualified_row_teaches_the_layouts_name_style():
    """'Alpha (Before)' retyped as 'Alpha Before' teaches this layout to join
    the qualifier bare — the rescan names every row that way."""
    rows, sep = _table('''
        | | Before | | | After | | |
        | | Got | Norm | Ratio % | Got | Ratio % | Shift % |
        | --- | --- | --- | --- | --- | --- | --- |
        | Alpha | 0.96 | 1.62 | 59 | 1.30 | 80 | 35.4 |
        | Beta | 1.47 | 2.03 | 72 | 1.37 | 67 | -6.8 |
    ''')
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    results, _ = rf.extract(description, rows[sep + 1:])
    before_row = next(r for r in results if r['test_name'] == 'Alpha (Before)')
    after = dict(before_row)
    after['test_name'] = 'Alpha Before'
    learned = rf.learn_from_edit(store, before_row, after)
    assert learned
    assert store['report_formats']
    entry = next(iter(store['report_formats'].values()))
    # 'Alpha' + bare ' Before' decomposes into the richer name pattern —
    # name cell then qualifier with a bare join.
    assert entry.get('name_pattern') or entry.get('name_style') == 'bare'
    # Rescan the identical grid: names come out bare for every row.
    again = rf.describe(rows, sep)
    assert rf.apply_remembered(again, store) is True
    results2, _ = rf.extract(again, rows[sep + 1:])
    names2 = [r['test_name'] for r in results2]
    assert 'Alpha Before' in names2 and 'Alpha After' in names2
    assert 'Alpha (Before)' not in names2


def test_unrelated_renames_teach_no_name_style():
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False}
    }}
    before = {'format_structure': 'struct1', 'test_name': 'Alpha (Before)'}
    after = {'format_structure': 'struct1', 'test_name': 'Lung capacity'}
    assert rf.learn_from_edit(store, before, after) is None
    assert 'name_style' not in store['report_formats']['sig1']


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


# --- several photos of one report -------------------------------------------
# parse_report_pages lives in medical_advisor_health_context (it owns the
# metadata regexes); the merge rules below are what make pages one document.

def _pages_module():
    import importlib
    mod = importlib.import_module(
        'ai_compare.medical_advisor_health_context')
    return mod


def test_undated_continuation_page_inherits_the_document_date():
    """Page 2 of a report often repeats nothing but the table itself. When the
    batch shows exactly one report date, undated rows inherit it and say so."""
    m = _pages_module()
    page1 = '''Patient: Ken T
Collection Date: 12-May-2026

| Test | 12-May-26 | Reference |
| --- | --- | --- |
| S CHOL | 6.7 | 3.0 - 5.5 |
'''
    page2 = '''
| Measure | Got | Norm | Ratio % |
| --- | --- | --- | --- |
| Alpha | 0.96 | 1.62 | 59 |
| Beta | 1.47 | 2.03 | 72 |
'''
    rows, analysis = m.parse_report_pages(
        [{'name': 'page1.jpg', 'text': page1},
         {'name': 'page2.jpg', 'text': page2}], store={})
    alpha = next(r for r in rows if r['test_name'] == 'Alpha')
    assert alpha['date'] == '12-May-2026'
    assert alpha['date_source'] == 'document'
    assert alpha['source_page'] == 2
    assert alpha['source_file'] == 'page2.jpg'
    # Page 1's own rows keep their real column date, untouched.
    chol = next(r for r in rows if r['test_name'] == 'S CHOL')
    assert chol['date'] == '12-May-26'
    assert 'date_source' not in chol


def test_overlapping_photos_drop_duplicate_rows_and_say_so():
    """An overlap screenshot re-shows the bottom rows of page 1. Identical
    name+value+date is one reading seen twice; the drop is recorded."""
    m = _pages_module()
    page1 = '''Collection Date: 12-May-2026

| Test | 12-May-26 | Reference |
| --- | --- | --- |
| S CHOL | 6.7 | 3.0 - 5.5 |
| S TRIG | 1.9 | < 1.7 |
'''
    page2 = '''
| Test | 12-May-26 | Reference |
| --- | --- | --- |
| S TRIG | 1.9 | < 1.7 |
| S HDL | 1.2 | > 1.0 |
'''
    rows, analysis = m.parse_report_pages(
        [{'name': 'p1.jpg', 'text': page1},
         {'name': 'p2.jpg', 'text': page2}], store={})
    trigs = [r for r in rows if r['test_name'] == 'S TRIG']
    assert len(trigs) == 1
    assert trigs[0]['source_page'] == 1
    assert len(analysis['duplicates_dropped']) == 1
    assert analysis['duplicates_dropped'][0]['test_name'] == 'S TRIG'
    assert analysis['duplicates_dropped'][0]['dropped_page'] == 2
    assert analysis['duplicates_dropped'][0]['kept_page'] == 1


def test_two_reports_in_one_batch_keep_their_own_dates():
    """Pages that are actually different reports each have their own metadata
    date, so each page's undated rows take their own page's date — never the
    other report's."""
    m = _pages_module()
    page_a = '''Reported: 01-Jun-2026

| Test | Result |
| --- | --- |
| Alpha | 1.2 |
'''
    page_b = '''Reported: 15-Jun-2026

| Test | Result |
| --- | --- |
| Beta | 3.4 |
'''
    rows, _ = m.parse_report_pages(
        [{'name': 'a.jpg', 'text': page_a},
         {'name': 'b.jpg', 'text': page_b}], store={})
    alpha = next(r for r in rows if r['test_name'] == 'Alpha')
    beta = next(r for r in rows if r['test_name'] == 'Beta')
    assert alpha['date'] == '01-Jun-2026'
    assert beta['date'] == '15-Jun-2026'


def test_ambiguous_batch_dates_leave_rows_undated():
    """Two different metadata dates and a page with none: guessing is worse
    than admitting the date is unknown — the row stays undated for filing."""
    m = _pages_module()
    page_a = '''Reported: 01-Jun-2026

| Test | Result |
| --- | --- |
| Alpha | 1.2 |
'''
    page_b = '''Reported: 15-Jun-2026

| Test | Result |
| --- | --- |
| Beta | 3.4 |
'''
    page_c = '''
| Test | Result |
| --- | --- |
| Gamma | 5.6 |
'''
    rows, analysis = m.parse_report_pages(
        [{'name': 'a.jpg', 'text': page_a},
         {'name': 'b.jpg', 'text': page_b},
         {'name': 'c.jpg', 'text': page_c}], store={})
    gamma = next(r for r in rows if r['test_name'] == 'Gamma')
    assert not gamma['date']
    assert gamma.get('date_source') != 'document'


def test_a_birth_date_is_never_a_document_date():
    """'Date of Birth' is the patient's date, not the report's — propagating
    it onto result rows would misdate every measurement."""
    m = _pages_module()
    page = '''Patient: Ken T
Date of Birth: 03-Mar-1968

| Test | Result |
| --- | --- |
| Alpha | 1.2 |
'''
    rows, analysis = m.parse_report_pages(
        [{'name': 'a.jpg', 'text': page}], store={})
    alpha = next(r for r in rows if r['test_name'] == 'Alpha')
    assert alpha['date'] != '03-Mar-1968'


def test_pages_naming_different_patients_are_flagged():
    m = _pages_module()
    page_a = 'Patient: Ken T\n\n| Test | Result |\n| --- | --- |\n| Alpha | 1.2 |\n'
    page_b = 'Patient: Someone Else\n\n| Test | Result |\n| --- | --- |\n| Beta | 3.4 |\n'
    _, analysis = m.parse_report_pages(
        [{'name': 'a.jpg', 'text': page_a},
         {'name': 'b.jpg', 'text': page_b}], store={})
    assert analysis.get('patient_conflict') == ['someone else', 'wai t']


def test_single_page_batch_matches_single_text_parse():
    """A one-page batch must produce the same rows as the single-text parse —
    page plumbing must not change what a single document reads."""
    m = _pages_module()
    text = '''
| Test | 05-Aug-24 | Reference | Units |
| --- | --- | --- | --- |
| S CHOL | 6.7 H | 3.0 - 5.5 | mmol/L |
'''
    single, _ = m.parse_report_tables(text, store={})
    batched, analysis = m.parse_report_pages(
        [{'name': 'p.jpg', 'text': text}], store={})
    assert [ (r['test_name'], r['value'], r['date']) for r in batched
            ] == [ (r['test_name'], r['value'], r['date']) for r in single ]
    assert batched[0]['source_page'] == 1


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


# --- positional integrity ----------------------------------------------------
# A report is a 2-D grid: a cell means what its position means. When the
# transcription drops a cell, the rest of the row slides left — the check
# below is what stops a shifted reading from being filed as data.

def test_a_row_with_a_dropped_cell_is_skipped_not_shifted():
    """The middle row is short: its measured cell is gone and the range/unit
    cells slid into earlier positions. The unit text sitting in the measured
    position contradicts the column's shape — the row must not produce a
    value, or 'mmol/L' would be filed as a result."""
    description, results, skipped = _read('''
        | Analyte | | | |
        | --- | --- | --- | --- |
        | Potassium | 5.9 | 3.5 - 5.5 | mmol/L |
        | Sodium | mmol/L | 135 - 145 |
        | Chloride | 102 | 98 - 107 | mmol/L |
    ''')
    names = [r['test_name'] for r in results]
    assert 'Sodium' not in names
    assert 'Potassium' in names and 'Chloride' in names
    assert any('misaligned' in s['reason'] for s in skipped)


def test_a_row_with_a_date_in_the_value_position_is_skipped():
    description, results, skipped = _read('''
        | Analyte | | | |
        | --- | --- | --- | --- |
        | Potassium | 5.9 | 3.5 - 5.5 | mmol/L |
        | Sodium | 05-Aug-2024 | 135 - 145 | mmol/L |
    ''')
    assert [r['test_name'] for r in results] == ['Potassium']
    assert any('misaligned' in s['reason'] for s in skipped)


def test_a_short_row_is_still_extracted_but_flagged():
    """A short row is usually just trimmed trailing empties, so it still
    extracts — but each record it emits carries `misaligned` so the review
    can badge it for a position check."""
    description, results, skipped = _read('''
        | Analyte | | | |
        | --- | --- | --- | --- |
        | Potassium | 5.9 | 3.5 - 5.5 | mmol/L |
        | Sodium | 139 | 135 - 145 |
    ''')
    sodium = next(r for r in results if r['test_name'] == 'Sodium')
    assert sodium['value'] == '139'
    assert sodium.get('misaligned') is True
    potassium = next(r for r in results if r['test_name'] == 'Potassium')
    assert not potassium.get('misaligned')


# --- rejection teaches -------------------------------------------------------

def _store_with_confirmed_roles():
    """A remembered layout with confirmed roles for a 4-column lab grid."""
    rows, sep = _table('''
        | Analyte | | | |
        | --- | --- | --- | --- |
        | Potassium | 5.9 | 3.5 - 5.5 | mmol/L |
        | Sodium | 139 | 135 - 145 | mmol/L |
    ''')
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    rf.confirm(store, description)
    return store, description['structure']


def test_rejecting_every_row_of_a_column_demotes_it():
    """User declined all three rows a measured column produced — the layout
    learns that position is not data."""
    store, structure = _store_with_confirmed_roles()
    rejected = [
        {'format_structure': structure, 'source_column': 1, 'test_name': 'A'},
        {'format_structure': structure, 'source_column': 1, 'test_name': 'B'},
    ]
    kept = [
        {'format_structure': structure, 'source_column': 3, 'test_name': 'A'},
        {'format_structure': structure, 'source_column': 3, 'test_name': 'B'},
    ]
    what = rf.learn_from_reject(store, rejected, kept)
    assert 'rejected column 1' in (what or '')
    roles = {c['index']: c['role']
             for c in rf.find_by_structure(store, structure)['column_roles']}
    assert roles[1] == 'text'
    assert roles[3] != 'text'  # its rows were kept — untouched


def test_partial_rejection_changes_no_roles():
    """User kept some rows of a column and declined others — that is picking
    rows, not a misread column, so nothing demotes."""
    store, structure = _store_with_confirmed_roles()
    rejected = [{'format_structure': structure, 'source_column': 1}]
    kept = [{'format_structure': structure, 'source_column': 1}]
    what = rf.learn_from_reject(store, rejected, kept)
    assert what is None
    roles = {c['index']: c['role']
             for c in rf.find_by_structure(store, structure)['column_roles']}
    assert roles[1] != 'text'


def test_rejected_name_column_is_never_demoted():
    store, structure = _store_with_confirmed_roles()
    rejected = [{'format_structure': structure, 'source_column': 0}]
    what = rf.learn_from_reject(store, rejected, [])
    roles = {c['index']: c['role']
             for c in rf.find_by_structure(store, structure)['column_roles']}
    assert roles[0] == 'name'


def test_mass_rejection_with_manual_reentry_demotes_nothing():
    """Real case: a garbled spirometry scan produced 19 wrong rows; the user
    rejected them all and retyped ten manual rows with the same test stems.
    Declining every row of a column usually means 'not data' — but re-entered
    rows mean the values were wrong, so no column is demoted."""
    store, structure = _store_with_confirmed_roles()
    rejected = [
        {'format_structure': structure, 'source_column': 1,
         'test_name': 'Potassium (mmol/L) (Pre-Bronch Actual)',
         'name_base': 'Potassium (mmol/L)'},
        {'format_structure': structure, 'source_column': 1,
         'test_name': 'Sodium (mmol/L) (Pre-Bronch Actual)',
         'name_base': 'Sodium (mmol/L)'},
    ]
    kept = [
        {'test_name': 'Potassium', 'value': '5.9', '_manual': True},
        {'test_name': 'Sodium', 'value': '139', '_manual': True},
    ]
    what = rf.learn_from_reject(store, rejected, kept)
    assert not (what or '').startswith('rejected column')
    roles = {c['index']: c['role']
             for c in rf.find_by_structure(store, structure)['column_roles']}
    assert roles[1] != 'text'


# --- renaming a field maps back by value and position ------------------------

def test_renamed_field_heading_maps_back_by_value():
    """The user prefers a different name than the report printed. The rename
    is matched to its column by the value that carried over, so the next scan
    of this layout emits the user's heading — not the report's."""
    rows, sep = _table('''
        | Analyte | Got | Note |
        | --- | --- | --- |
        | Alpha | 0.96 | Run A |
        | Beta | 1.47 | Run B |
    ''')
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    results, _ = rf.extract(description, rows[sep + 1:])
    assert 'Note' in (results[0].get('fields') or {})
    before = dict(results[0])
    after = dict(results[0])
    after['fields'] = {'Batch': 'Run A'}
    learned = rf.learn_from_edit(store, before, after)
    assert learned and 'renamed' in learned
    entry = next(iter(store['report_formats'].values()))
    spec = next(c for c in entry['column_roles'] if c['label'] == 'Note')
    assert spec.get('alias') == 'Batch'
    # The role stays 'text' — it was renamed, not deleted.
    assert spec['role'] == 'text'
    # Rescan the identical grid: the field arrives under the user's heading.
    again = rf.describe(rows, sep)
    assert rf.apply_remembered(again, store) is True
    results2, _ = rf.extract(again, rows[sep + 1:])
    fields2 = results2[0].get('fields') or {}
    assert fields2.get('Batch') == 'Run A'
    assert 'Note' not in fields2


def test_renamed_field_with_retyped_value_maps_by_position():
    """One heading out, one heading in — a rename even when the value was
    retyped along with the name."""
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False,
                 'column_roles': [
                     {'index': 0, 'label': 'Name', 'qualifier': '', 'role': 'name'},
                     {'index': 1, 'label': 'Odd', 'qualifier': '', 'role': 'text'},
                 ]}
    }}
    before = {'format_structure': 'struct1', 'fields': {'Odd': 'Run A'}}
    after = {'format_structure': 'struct1', 'fields': {'Batch': 'Run A2'}}
    learned = rf.learn_from_edit(store, before, after)
    assert learned and 'renamed' in learned
    spec = store['report_formats']['sig1']['column_roles'][1]
    assert spec.get('alias') == 'Batch'
    assert spec['role'] == 'text'  # renamed, not demoted


# --- learned name composition ------------------------------------------------

def test_retyped_name_teaches_the_layouts_name_pattern():
    """'FEV1 (L) Pre-Bronch Actual' typed over the extracted 'FEV1 (Pre-Bronch)'
    teaches the whole composition — name cell + unit in parens + qualifier +
    label, joined bare — and the sibling FVC row is named the same way."""
    rows, sep = _table('''
        | | | Pre-Bronch | |
        | Analyte | Units | Actual | Norm |
        | --- | --- | --- | --- |
        | FEV1 | L | 0.96 | 1.62 |
        | FVC | mL | 1.47 | 2.03 |
        | PEF | L/s | 4.10 | 5.00 |
    ''')
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    results, _ = rf.extract(description, rows[sep + 1:])
    before_row = next(r for r in results
                      if r['test_name'] == 'FEV1 (Pre-Bronch Actual)')
    assert before_row['name_base'] == 'FEV1'
    assert before_row['unit'] == 'L'
    after = dict(before_row)
    after['test_name'] = 'FEV1 (L) Pre-Bronch Actual'
    learned = rf.learn_from_edit(store, before_row, after)
    assert learned and 'name_pattern' in learned
    entry = next(iter(store['report_formats'].values()))
    pattern = entry.get('name_pattern')
    assert [p['part'] for p in pattern] == ['name', 'unit', 'qualifier', 'label']
    # Rescan the identical grid: every sibling row is named the learned way.
    again = rf.describe(rows, sep)
    assert rf.apply_remembered(again, store) is True
    results2, _ = rf.extract(again, rows[sep + 1:])
    names2 = [r['test_name'] for r in results2]
    assert 'FEV1 (L) Pre-Bronch Actual' in names2
    assert 'FVC (mL) Pre-Bronch Actual' in names2
    assert 'FEV1 (Pre-Bronch Actual)' not in names2


def test_an_unexplained_rename_teaches_no_name_pattern():
    """A typed name that cannot be rebuilt from the layout's parts is not
    learned — a half-understood pattern would misname every sibling."""
    store = {'report_formats': {
        'sig1': {'signature': 'sig1', 'structure': 'struct1', 'confirmed': False,
                 'column_roles': [
                     {'index': 0, 'label': 'Name', 'qualifier': '', 'role': 'name'},
                     {'index': 1, 'label': 'Got', 'qualifier': '', 'role': 'measured'},
                 ]}
    }}
    before = {'format_structure': 'struct1', 'test_name': 'FEV1 (Pre)',
              'name_base': 'FEV1', 'qualifier': 'Pre', 'unit': 'L',
              'source_column': 1}
    after = {'format_structure': 'struct1', 'test_name': 'FEV1 something else'}
    assert rf.learn_from_edit(store, before, after) is None
    assert 'name_pattern' not in store['report_formats']['sig1']


# --- shared layout knowledge -------------------------------------------------

def test_confirmed_layout_seeds_another_profiles_store():
    """Profile A confirms a layout; profile B scanning the same grid inherits
    the corrected column roles — the whole point of the shared store."""
    store_a, structure = _store_with_confirmed_roles()
    entry = next(iter(store_a['report_formats'].values()))
    entry['last_report_date'] = '2026-09-27'
    entry['last_report_date_at'] = '2026-09-27T10:00:00'

    shared = {}
    assert rf.promote_to_shared(store_a, shared) is True
    assert structure in [e['structure'] for e in shared.values()]
    # report dates never cross profiles
    assert 'last_report_date' not in next(iter(shared.values()))

    store_b = {}
    seeded = rf.seed_from_shared(store_b, shared)
    assert seeded == 1
    b_entry = next(iter(store_b['report_formats'].values()))
    assert b_entry['confirmed'] is True
    assert b_entry['structure'] == structure
    assert 'last_report_date' not in b_entry
    # Seeding twice is a no-op — the profile owns its copy now
    assert rf.seed_from_shared(store_b, shared) == 0


def test_promote_to_shared_is_idempotent_and_prefers_newer():
    store, structure = _store_with_confirmed_roles()
    entry = next(iter(store['report_formats'].values()))
    entry['confirmed_at'] = '2026-09-28T03:00:00'
    shared = {}
    assert rf.promote_to_shared(store, shared) is True
    assert rf.promote_to_shared(store, shared) is False  # same confirmed_at

    # An older profile confirmation must not overwrite the newer shared one
    store_old, _ = _store_with_confirmed_roles()
    old_entry = next(iter(store_old['report_formats'].values()))
    old_entry['structure'] = structure
    old_entry['confirmed_at'] = '2026-09-01T00:00:00'
    assert rf.promote_to_shared(store_old, shared) is False
    assert shared[next(iter(shared))]['confirmed_at'] == '2026-09-28T03:00:00'


def test_unconfirmed_layouts_never_seed_or_promote():
    rows, sep = _table("""
        | Analyte | | | |
        | --- | --- | --- | --- |
        | Potassium | 5.9 | 3.5 - 5.5 | mmol/L |
    """)
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)  # seen, not confirmed
    shared = {}
    assert rf.promote_to_shared(store, shared) is False
    other = {'x': {'structure': description['structure'], 'confirmed': False}}
    assert rf.seed_from_shared(store, other) == 0


# --- compact emission: "one row per test, columns into fields" ---------------

def _spiro_table():
    return _table('''
        |  | Pre-Bronch Pred | Pre-Bronch Actual | Pre-Bronch %Pred | Post-Bronch Actual | Post-Bronch %Pred | Post-Bronch %Chng | Reference Range | Units |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- |
        | FEV1 (L) | 1.62 | 0.96 | 59 | 1.30 | 80 | 36.2 | > 1.0 | L |
        | FVC (L) | 2.03 | 1.47 | 73 | 1.37 | 68 | -6.8 | > 1.5 | L |
        | FEF25-75% (L/s) | 1.52 | 1.13 | 75 | 3.19 | 210 | 181.9 | > 0.5 | L/s |
    ''')


def _confirmed_spiro_store():
    rows, sep = _spiro_table()
    description = rf.describe(rows, sep)
    store = {}
    rf.remember(store, description)
    rf.confirm(store, description)
    # As on the confirmed production layout: the Units column is 'unit',
    # not 'flag' — describe reads pure L/L/… cells as flag letters.
    entry = next(iter(store['report_formats'].values()))
    for c in entry['column_roles']:
        if c.get('label') == 'Units':
            c['role'] = 'unit'
    return store, description['structure']


def test_rejecting_composed_rows_for_manual_compact_rows_learns_emission():
    """Sau Tse's case: the scan emitted 'FEV1 (L) (Pre-Bronch Actual)' rows,
    the user declined them all and typed 'FEV1' with Pred/%Pred/Post fields.
    The layout must learn emission='compact' and the user's headings."""
    store, structure = _confirmed_spiro_store()
    rejected = [
        {'format_structure': structure,
         'test_name': 'FEV1 (L) (Pre-Bronch Actual)', 'name_base': 'FEV1 (L)'},
        {'format_structure': structure,
         'test_name': 'FVC (L) (Pre-Bronch Actual)', 'name_base': 'FVC (L)'},
    ]
    kept = [
        {'test_name': 'FEV1', 'value': '0.96', '_manual': True,
         'fields': {'Pred': '1.62', 'Pre-Bronch %Pred': '59',
                    'Post-Bronch Actual': '1.30',
                    'Post-Bronch %Pred': '80', '%Chng': '36.2'}},
        {'test_name': 'FVC', 'value': '1.47', '_manual': True},
    ]
    what = rf.learn_compact_emission(store, rejected, kept)
    assert 'compact emission' in (what or '')
    entry = rf.find_by_structure(store, structure)
    assert entry['emission'] == 'compact'
    aliases = {c['index']: c.get('alias')
               for c in entry['column_roles'] if c.get('alias')}
    assert aliases == {1: 'Pred', 3: 'Pre-Bronch %Pred',
                       4: 'Post-Bronch Actual', 5: 'Post-Bronch %Pred',
                       6: '%Chng'}


def test_compact_emission_extracts_one_row_per_test_with_user_headings():
    """Rescanning the same grid after the lesson emits Sau Tse's saved shape:
    'FEV1' value from Pre-Bronch Actual, everything else in fields."""
    store, structure = _confirmed_spiro_store()
    entry = rf.find_by_structure(store, structure)
    entry['emission'] = 'compact'
    for c in entry['column_roles']:
        c['alias'] = {1: 'Pred', 3: 'Pre-Bronch %Pred',
                      4: 'Post-Bronch Actual', 5: 'Post-Bronch %Pred',
                      6: '%Chng'}.get(c['index'])

    rows, sep = _spiro_table()
    description = rf.describe(rows, sep)
    assert rf.apply_remembered(description, store) is True
    assert description.get('emission') == 'compact'
    results, skipped = rf.extract(description, rows[sep + 1:])
    fev1 = next(r for r in results if r['test_name'] == 'FEV1')
    assert fev1['value'] == '0.96'
    assert fev1['unit'] == 'L'
    assert fev1['fields'] == {'Pred': '1.62', 'Pre-Bronch %Pred': '59',
                             'Post-Bronch Actual': '1.30',
                             'Post-Bronch %Pred': '80', '%Chng': '36.2'}
    fvc = next(r for r in results if r['test_name'] == 'FVC')
    assert fvc['fields']['%Chng'] == '-6.8'
    assert len(results) == 3  # one per grid row, not one per measured column


# --- user-confirmed layout beats a fresh reading of the same report ---------

def test_apply_remembered_falls_back_to_column_vocabulary():
    """A rescan that relabels a column produces a different structure hash —
    the confirmed layout must still apply when the vocabulary matches and
    the grid is the same width. The user's reading wins over the fresh one."""
    store, structure = _confirmed_spiro_store()
    entry = rf.find_by_structure(store, structure)
    entry['emission'] = 'compact'

    rows, sep = _spiro_table()
    rows[sep - 1][6] = 'Post-Bronch Change'  # relabelled → new structure
    description = rf.describe(rows, sep)
    assert description['structure'] != structure
    assert rf.find_by_structure(store, description['structure']) is None
    assert rf.apply_remembered(description, store) is True
    assert description.get('emission') == 'compact'
    roles = {c['index']: c['role'] for c in description['columns']}
    assert roles[4] == 'measured' and roles[6] == 'percent_change'


def test_vocabulary_match_needs_width_and_confirmed():
    """A different-width grid or an unconfirmed layout gets no overlay —
    the fallback is the user's confirmed reading, not any similar table."""
    store, structure = _confirmed_spiro_store()
    rows, sep = _table('''
        | Test | Pred | Actual | %Pred | %Chng | Reference Range | Units |
        | --- | --- | --- | --- | --- | --- | --- |
        | FEV1 | 1.62 | 0.96 | 59 | 36.2 | > 1.0 | L |
    ''')
    description = rf.describe(rows, sep)  # 7 columns, confirmed wants 9
    assert rf.apply_remembered(description, store) is False

    fresh = rf.describe(*_table('''
        | Analyte | Result | Flag | Reference | Units |
        | --- | --- | --- | --- | --- |
        | Sodium | 141 |  | 135-145 | mmol/L |
    '''))
    assert rf.find_by_vocabulary(store, fresh['labels']) is None

    unconfirmed = {}
    rows, sep = _spiro_table()
    d2 = rf.describe(rows, sep)
    rf.remember(unconfirmed, d2)  # seen but never confirmed
    assert rf.apply_remembered(d2, unconfirmed) is False


def test_note_row_labels_records_kept_names():
    store, structure = _confirmed_spiro_store()
    rf.note_row_labels(store, structure, [
        {'test_name': 'FEV1'}, {'name_base': 'FVC'}, {'test_name': 'fev1'}])
    entry = rf.find_by_structure(store, structure)
    assert entry['row_labels'] == ['FEV1', 'FVC']  # deduped, order kept


def test_expected_headers_flatten_qualifier_and_label():
    store, structure = _confirmed_spiro_store()
    headers = rf.expected_headers(rf.find_by_structure(store, structure))
    assert headers[0] == 'Test'
    assert headers[1] == 'Pre-Bronch Pred'
    assert headers[8] == 'Units'
    assert len(headers) == 9


def test_vocabulary_matches_bare_labels_against_flattened_ones():
    """ST's rescan printed bare column names ('Pred', 'Actual') while the
    confirmed layout stored flattened ones ('Pre-Bronch Pred'). The last word
    carries the meaning — 'Pre-Bronch Pred' must still answer to 'pred'."""
    store, structure = _confirmed_spiro_store()
    rescan_headings = ['Test', 'Pred', 'Actual', '%Pred', '%Chng',
                       'Reference Range', 'Units']
    entry = rf.find_by_vocabulary(store, rescan_headings)
    assert entry is not None and entry['structure'] == structure
