/* Standalone regression checks for static/lab_results.js flag/display logic.
 * Run: node tests/test_lab_results.js   (exits non-zero on failure)
 *
 * Guards the bug where the 'L' inside a unit like 'x10^9/L' was read as a
 * Low flag, and where a stale stored flag letter overrode an in-range value.
 */
'use strict';
const fs = require('fs');
const path = require('path');

global.window = {};
eval(fs.readFileSync(path.join(__dirname, '..', 'static', 'lab_results.js'), 'utf8'));
const L = global.window.LabUtils;

const cases = [
    ['0.5 x10^9/L', 'x10^9/L', '0 - 1.0', ''],
    ['0.5 x10^9/L', '', '0 - 1.0', ''],
    ['0.5 x10^9/L L', 'x10^9/L', '0 - 1.0', ''],
    ['0.1 x10^9/L', '', '0 - 0.5', ''],
    ['0.1 x10^9/L', '', '', ''],
    ['6.4 H mmol/L', 'mmol/L', '4 - 6', 'H'],
    ['6.4 H mmol/L', '', '4 - 6', 'H'],
    ['7.0 mmol/L', 'mmol/L', '4 - 6', 'H'],
    ['0.3', '', '0.5 - 1.0', 'L'],
    ['5.2', '', '<4.5', 'H'],
    ['3.0', '', '<4.5', ''],
];

let failures = 0;
for (const [value, unit, ref, expected] of cases) {
    const got = L.testFlag({ value }, unit, ref);
    if (got !== expected) {
        failures++;
        console.log(`FAIL  ${JSON.stringify(value)} unit=${JSON.stringify(unit)} ref=${JSON.stringify(ref)} -> ${JSON.stringify(got)} (want ${JSON.stringify(expected)})`);
    }
}

// Mixed stored values display consistently within one group.
const groups = L.groupTestResults([
    { test_name: 'Monocytes', value: '0.5 x10^9/L L', reference_range: '0 - 1.0', date: '2026-09-09' },
    { test_name: 'Monocytes', value: '0.5', reference_range: '', date: '2026-07-22' },
], 'recent');
const vals = groups[0].entries.map(e => e.displayVal);
const flags = groups[0].entries.map(e => e.flag);
if (vals.join(',') !== '0.5,0.5' || flags.join(',') !== ',') {
    failures++;
    console.log(`FAIL  displayVals=${JSON.stringify(vals)} flags=${JSON.stringify(flags)} (want ["0.5","0.5"] ["",""])`);
}

// Legacy rows carry unit:null — null is absent data, not an explicit unit.
// The embedded unit must still be found so values strip and never flag.
const nullUnit = L.groupTestResults([
    { test_name: 'Eosinophils', value: '0.1 x10*9/L', unit: null, reference_range: '(0-0.5)', date: '2026-09-09' },
], 'recent');
if (nullUnit[0].unit === 'null' || nullUnit[0].entries[0].displayVal !== '0.1' || nullUnit[0].entries[0].flag !== '') {
    failures++;
    console.log(`FAIL  unit=${JSON.stringify(nullUnit[0].unit)} displayVal=${JSON.stringify(nullUnit[0].entries[0].displayVal)} flag=${JSON.stringify(nullUnit[0].entries[0].flag)}`);
}

// Unit glyph variants: 'x10*9/L' and 'x10^9/L' are the same unit — a row
// written one way must strip under a group unit written the other.
const mixed = L.groupTestResults([
    { test_name: 'Monocytes', value: '0.5 x10^9/L', unit: null, reference_range: '(0-1.0)', date: '2026-09-09' },
    { test_name: 'Monocytes', value: '0.5 x10*9/L', reference_range: '', date: '2026-07-22' },
], 'recent');
const mvals = mixed[0].entries.map(e => e.displayVal);
if (mvals.join(',') !== '0.5,0.5') {
    failures++;
    console.log(`FAIL  */^ variant displayVals=${JSON.stringify(mvals)} (want ["0.5","0.5"])`);
}

// Reference ranges display in one canonical form regardless of report style.
const refCases = [
    ['(10-45)', '10 - 45'],
    ['10-45', '10 - 45'],
    ['10 - 45', '10 - 45'],
    ['(2.0-3.2)', '2.0 - 3.2'],
    ['<4.5', '<4.5'],
    ['(0-1.0)', '0 - 1.0'],
    ['', ''],
];
for (const [raw, want] of refCases) {
    const got = L.formatRefRange(raw);
    if (got !== want) {
        failures++;
        console.log(`FAIL  formatRefRange(${JSON.stringify(raw)}) = ${JSON.stringify(got)} (want ${JSON.stringify(want)})`);
    }
}
// And groupTestResults exposes the normalised form via g.ref/meta.
const refGroup = L.groupTestResults([
    { test_name: 'S Transferrin Saturation', value: '37', reference_range: '(10-45)', date: '2026-09-09' },
], 'recent');
if (refGroup[0].ref !== '10 - 45') {
    failures++;
    console.log(`FAIL  group ref ${JSON.stringify(refGroup[0].ref)} (want "10 - 45")`);
}

// Blank semantics: an unmarked blank unit/ref is absent import data and
// inherits the group default; a user-locked blank stays blank.
const unlocked = L.groupTestResults([
    { test_name: 'Glucose', value: '5.4', unit: '', reference_range: '', date: '2026-09-09' },
    { test_name: 'Glucose', value: '5.0', unit: 'mmol/L', reference_range: '3.6 - 6.0', date: '2026-03-01' },
], 'recent');
if (unlocked[0].entries[0].displayRef !== '3.6 - 6.0' || unlocked[0].unit !== 'mmol/L') {
    failures++;
    console.log(`FAIL  unlocked blank row: displayRef=${JSON.stringify(unlocked[0].entries[0].displayRef)} unit=${JSON.stringify(unlocked[0].unit)} (want '3.6 - 6.0'/'mmol/L')`);
}
const locked = L.groupTestResults([
    { test_name: 'HbA1c', value: '42', unit: '', unit_locked: true, reference_range: '', ref_locked: true, date: '2026-09-09' },
    { test_name: 'HbA1c', value: '40 mmol/mol', reference_range: '20 - 42', date: '2026-03-01' },
], 'recent');
if (locked[0].unit !== '' || locked[0].entries[0].displayRef !== '' || locked[0].entries[1].displayRef !== '20 - 42') {
    failures++;
    console.log(`FAIL  locked blank row: unit=${JSON.stringify(locked[0].unit)} refs=${JSON.stringify(locked[0].entries.map(e => e.displayRef))} (want ''/['','20 - 42'])`);
}
// An unlocked '' unit is absent data — embedded units still resolve.
const blankUnit = L.groupTestResults([
    { test_name: 'Sodium', value: '140 mmol/L', unit: '', reference_range: '135 - 145', date: '2026-09-09' },
], 'recent');
if (blankUnit[0].unit !== 'mmol/L' || blankUnit[0].entries[0].displayVal !== '140') {
    failures++;
    console.log(`FAIL  unlocked '' unit: unit=${JSON.stringify(blankUnit[0].unit)} displayVal=${JSON.stringify(blankUnit[0].entries[0].displayVal)} (want 'mmol/L'/'140')`);
}

console.log(failures ? `${failures} failure(s)` : 'all lab_results checks passed');
process.exit(failures ? 1 : 0);
