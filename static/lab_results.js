/*
 * Shared lab-result helpers used by both the health-profile website and the
 * Dr. Health PWA. Functions are exposed under the same global names the two
 * templates used to define locally, plus window.LabUtils.groupTestResults for
 * the group/sort/flag pipeline they both render.
 */
(function () {
    'use strict';

    function parseReferenceRange(ref) {
        const nums = String(ref || '').match(/\d+(?:\.\d+)?/g) || [];
        if (nums.length >= 2) {
            const [a, b] = nums.map(parseFloat);
            return [Math.min(a, b), Math.max(a, b)];
        }
        return [null, null];
    }

    function testStatus(num, lower, upper) {
        if (lower === null || upper === null) return 'normal';
        if (num > upper) return 'high';
        if (num < lower) return 'low';
        return 'normal';
    }

    function statusColor(status) {
        return { high: '#e6a000', low: '#1565c0', normal: '#43a047' }[status] || '#999';
    }

    function computeTestFlag(num, ref) {
        if (isNaN(num)) return '';
        const [lower, upper] = parseReferenceRange(ref);
        if (lower === null || upper === null) return '';
        const s = testStatus(num, lower, upper);
        return s === 'high' ? 'H' : s === 'low' ? 'L' : '';
    }

    function buildSparkline(values, referenceRange = '') {
        const nums = values.map(v => parseFloat(v)).filter(v => !isNaN(v));
        if (nums.length < 2) return '';
        const [lower, upper] = parseReferenceRange(referenceRange);
        const statuses = nums.map(v => testStatus(v, lower, upper));
        const min = Math.min(...nums), max = Math.max(...nums);
        const range = max - min || 1;
        const w = 60, h = 18;
        const step = w / (nums.length - 1);
        const points = nums.map((v, i) => [i * step, h - ((v - min) / range) * h]);
        let svg = `<svg width="${w}" height="${h}" class="sparkline">`;
        for (let i = 0; i < points.length - 1; i++) {
            const color = statusColor(statuses[i + 1]);
            const [x1, y1] = points[i];
            const [x2, y2] = points[i + 1];
            svg += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>`;
            if (statuses[i + 1] === 'high') {
                const y1b = Math.min(h - 1, y1 + 1.8);
                const y2b = Math.min(h - 1, y2 + 1.8);
                svg += `<line x1="${x1.toFixed(1)}" y1="${y1b.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2b.toFixed(1)}" stroke="#fff176" stroke-width="1.5" stroke-linecap="round"/>`;
            }
        }
        for (let i = 0; i < points.length; i++) {
            const [x, y] = points[i];
            if (statuses[i] === 'high') svg += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" fill="#000"/>`;
            if (statuses[i] === 'low') svg += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" fill="#c62828"/>`;
        }
        svg += `</svg>`;
        return svg;
    }

    function extractTestUnit(value) {
        const m = String(value || '').match(/^-?\d+(?:\.\d+)?(?:\s+(?:H|L|High|Low))?\s*(.*)$/i);
        if (!m) return '';
        return m[1].replace(/(?:\s+|^)(H|L|High|Low)$/i, '').trim();
    }

    function stripTestUnit(value, unit) {
        if (!unit) return String(value || '');
        // Allow optional whitespace between every character so 'x10^9/L' and
        // 'x 10^9/L' are both removed, instead of leaving some rows with a unit.
        const esc = unit.replace(/\s+/g, '').split('')
            .map(c => c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
            .join('\\s*');
        const re = new RegExp('\\s*' + esc + '(?=\\s+(?:H|L|High|Low)\\b|\\s*$)', 'i');
        return String(value || '').replace(re, '').trim();
    }

    function extractTestFlag(value) {
        // A flag is a standalone H/L/High/Low token at the start or end of the
        // value — never the 'L' inside a unit like 'x10^9/L' or 'mg/L'.
        const t = String(value || '').trim();
        const m = t.match(/^(H|L|High|Low)\s+/i) || t.match(/\s(H|L|High|Low)\s*$/i);
        return m ? m[1].toUpperCase().charAt(0) : '';
    }

    function testFlag(entry, unit, ref) {
        // Fall back to the value's own embedded unit so '6.4 H mmol/L' still
        // strips to '6.4 H' when the group has no unit of its own.
        const stripped = stripTestUnit(entry.value, unit || extractTestUnit(entry.value));
        const displayVal = stripped.replace(/^(?:H|L|High|Low)\s+/i, '').replace(/\s+(?:H|L|High|Low)$/i, '').trim();
        const num = parseFloat(displayVal);
        const [lower, upper] = parseReferenceRange(ref);
        if (!isNaN(num) && lower !== null && upper !== null) {
            // When the number and the range both parse, arithmetic is
            // authoritative — a stale stored 'L' must not flag an in-range
            // value.
            const s = testStatus(num, lower, upper);
            return s === 'high' ? 'H' : s === 'low' ? 'L' : '';
        }
        let flag = '';
        if (!isNaN(num)) {
            // Single-boundary ranges like <4.5 or >2.0 have no
            // two-number range for computeTestFlag to work with
            const m = String(ref).match(/([<>≤≥])\s*(\d+(?:\.\d+)?)/);
            if (m) {
                const bound = parseFloat(m[2]);
                if ((m[1] === '<' || m[1] === '≤') && num >= bound) flag = 'H';
                if ((m[1] === '>' || m[1] === '≥') && num <= bound) flag = 'L';
                if (!flag) return '';
            }
        }
        return flag || extractTestFlag(stripped);
    }

    function normalizeTestType(testName) {
        if (!testName) return 'Unknown Test';
        // Parenthetical qualifiers are kept: '(NGSP)' vs '(IFCC)' or
        // '(fasting)' vs none are different measurements with different
        // units/ranges, and must not share a group or its reference range.
        return testName
            .replace(/historical/ig, '')
            .replace(/\s+/g, ' ')
            .replace(/\s+\(/g, '(')
            .trim() || testName.trim();
    }

    function parseMedicalDate(dateStr, addedAtStr = '') {
        const text = (dateStr || '').trim();
        if (text) {
            const patterns = [
                /^(\d{4})-(\d{2})-(\d{2})$/,
                /^(\d{4})-(\d{2})$/,
                /^(\d{4})$/,
                /^(\d{2})\/(\d{2})\/(\d{4})$/,
                /^(\d{2})-([A-Za-z]{3})-(\d{2,4})$/,
                /^(\d{2})\s+([A-Za-z]{3,9})\s+(\d{4})$/
            ];

            for (let i = 0; i < patterns.length; i++) {
                const m = text.match(patterns[i]);
                if (!m) continue;

                if (i === 0) return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
                if (i === 1) return new Date(Number(m[1]), Number(m[2]) - 1, 1);
                if (i === 2) return new Date(Number(m[1]), 0, 1);
                if (i === 3) return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));

                if (i === 4 || i === 5) {
                    const day = Number(m[1]);
                    const monthRaw = m[2].slice(0, 3).toLowerCase();
                    const monthMap = { jan:0, feb:1, mar:2, apr:3, may:4, jun:5, jul:6, aug:7, sep:8, oct:9, nov:10, dec:11 };
                    const month = monthMap[monthRaw];
                    if (month === undefined) continue;

                    let year = Number(m[3]);
                    if (year < 100) year += year >= 70 ? 1900 : 2000;
                    return new Date(year, month, day);
                }
            }

            const nativeDate = new Date(text);
            if (!Number.isNaN(nativeDate.getTime())) return nativeDate;
        }

        if (addedAtStr) {
            const addedDate = new Date(addedAtStr);
            if (!Number.isNaN(addedDate.getTime())) return addedDate;
        }

        return new Date(0);
    }

    function normalizeDateInput(text) {
        const t = (text || '').trim();
        if (!t) return null;
        let m;
        if ((m = t.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/))) return `${m[1]}-${String(m[2]).padStart(2,'0')}-${String(m[3]).padStart(2,'0')}`;
        if ((m = t.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/))) return `${m[3]}-${String(m[2]).padStart(2,'0')}-${String(m[1]).padStart(2,'0')}`;
        if ((m = t.match(/^(\d{4})-(\d{1,2})$/))) return `${m[1]}-${String(m[2]).padStart(2,'0')}-01`;
        if ((m = t.match(/^(\d{4})$/))) return `${m[1]}-01-01`;
        const d = new Date(t);
        if (!Number.isNaN(d.getTime())) return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
        return null;
    }

    /* Group raw test_results rows into display groups, computing everything
     * both pages need: unit, reference range, display name, meta line,
     * sparkline, per-row display value + flag, and the newest abnormal date.
     *
     * items:      array of test_result rows ({test_name, value, reference_range, date, ...})
     * sortMode:   'abnormal' (groups with an out-of-range reading first, ranked
     *             by newest abnormal date) or 'recent' (newest result first)
     * includeFn:  optional predicate; rows it rejects are skipped. idx always
     *             refers to the row's position in the original items array.
     *
     * Returns sorted [{displayName, unit, ref, meta, spark, lastAbnormal,
     *                  entries: [{item, idx, displayVal, flag}]}]
     */
    function groupTestResults(items, sortMode, includeFn) {
        const groups = {};
        items.forEach((item, idx) => {
            if (includeFn && !includeFn(item)) return;
            const key = normalizeTestType(item.test_name).toLowerCase();
            if (!groups[key]) groups[key] = { displayName: normalizeTestType(item.test_name), entries: [] };
            groups[key].entries.push({ item, idx });
        });

        Object.values(groups).forEach(g => {
            g.entries.sort((a, b) => parseMedicalDate(b.item.date, b.item.added_at) - parseMedicalDate(a.item.date, a.item.added_at));
            // An explicitly stored unit — even a blank one — wins: 'no unit'
            // is a deliberate choice (ratios like S CHOL/HDLC), and must not
            // be overridden by a unit left over in an older row's value text.
            const explicitUnit = g.entries.map(e => e.item.unit).find(u => u !== undefined);
            g.unit = explicitUnit !== undefined ? String(explicitUnit).trim()
                : (g.entries.map(e => extractTestUnit(e.item.value)).find(u => u) || '');
            g.ref = g.entries.map(e => e.item.reference_range || '').find(r => r.trim()) || '';
            const escUnit = g.unit ? g.unit.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') : '';
            if (g.unit) g.displayName = g.displayName.replace(new RegExp('(?:^|\\s)' + escUnit + '(?:\\s|$)', 'ig'), ' ').replace(/\s+/g, ' ').trim();
            const metaUnit = g.unit && !g.ref.toLowerCase().includes(g.unit.toLowerCase()) ? g.unit : '';
            g.meta = [g.ref, metaUnit].filter(Boolean).join(' ');
            g.spark = buildSparkline(g.entries.slice().reverse().map(e => e.item.value), g.ref);
            g.lastAbnormal = g.entries.reduce((latest, e) => {
                // Fall back to the value's own embedded unit so rows like
                // '0.5 x10^9/L' and '0.5' display consistently in one group.
                const rowUnit = g.unit || extractTestUnit(e.item.value);
                e.displayVal = stripTestUnit(e.item.value, rowUnit)
                    .replace(/^(?:H|L|High|Low)\s+/i, '').replace(/\s+(?:H|L|High|Low)$/i, '').trim();
                e.flag = testFlag(e.item, g.unit, g.ref);
                if (!e.flag) return latest;
                const d = parseMedicalDate(e.item.date, e.item.added_at);
                return d > latest ? d : latest;
            }, new Date(0));
        });

        const byRecent = (a, b) => {
            const da = a.entries.length ? parseMedicalDate(a.entries[0].item.date, a.entries[0].item.added_at) : new Date(0);
            const db = b.entries.length ? parseMedicalDate(b.entries[0].item.date, b.entries[0].item.added_at) : new Date(0);
            if (db.getTime() !== da.getTime()) return db - da;
            return a.displayName.localeCompare(b.displayName);
        };

        return Object.values(groups).sort((a, b) => {
            if (sortMode === 'abnormal') {
                const aa = a.lastAbnormal.getTime() > 0, ab = b.lastAbnormal.getTime() > 0;
                if (aa && ab && b.lastAbnormal.getTime() !== a.lastAbnormal.getTime()) return b.lastAbnormal - a.lastAbnormal;
                if (aa !== ab) return aa ? -1 : 1;
            }
            return byRecent(a, b);
        });
    }

    window.LabUtils = {
        parseReferenceRange, testStatus, statusColor, computeTestFlag,
        buildSparkline, extractTestUnit, stripTestUnit, extractTestFlag,
        testFlag, normalizeTestType, parseMedicalDate, normalizeDateInput,
        groupTestResults
    };

    // Flat globals matching the names the templates already call.
    window.parseReferenceRange = parseReferenceRange;
    window.testStatus = testStatus;
    window.statusColor = statusColor;
    window.computeTestFlag = computeTestFlag;
    window.buildSparkline = buildSparkline;
    window.extractTestUnit = extractTestUnit;
    window.stripTestUnit = stripTestUnit;
    window.extractTestFlag = extractTestFlag;
    window.testFlag = testFlag;
    window.normalizeTestType = normalizeTestType;
    window.parseMedicalDate = parseMedicalDate;
    window.normalizeDateInput = normalizeDateInput;
})();
