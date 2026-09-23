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

console.log(failures ? `${failures} failure(s)` : 'all lab_results checks passed');
process.exit(failures ? 1 : 0);
