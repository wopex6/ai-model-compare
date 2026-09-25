/* Standalone smoke test: every hub index card routes somewhere real.
 * Run: node tests/test_hub_index.js   (exits non-zero on failure)
 *
 * Renders the index with a minimal DOM stub, clicks each .hub-card through
 * the wired handler, and checks go() lands on a valid section — 'vitals'
 * must open the emergency modal instead.
 */
'use strict';
const fs = require('fs');
const path = require('path');

global.window = {};
global.AuthHelper = { authenticatedFetch: () => Promise.reject(new Error('offline')) };
global.history = { pushState: function () {}, replaceState: function () {}, state: null };
global.document = { getElementById: () => null };

eval(fs.readFileSync(path.join(__dirname, '..', 'static', 'dr_health_hub.js'), 'utf8'));
const Hub = global.window.DrHealthHub;
if (!Hub) { console.error('DrHealthHub missing'); process.exit(1); }

function makeCard(id) {
    const handlers = {};
    return {
        getAttribute: (k) => (k === 'data-section' ? id : null),
        addEventListener: (ev, fn) => { handlers[ev] = fn; },
        click() { if (handlers.click) handlers.click.call(this); }
    };
}

const root = {
    _html: '',
    _cards: [],
    get innerHTML() { return this._html; },
    set innerHTML(v) {
        this._html = String(v);
        // Rebuild the card stubs on each render so listeners attach to the
        // same objects the test clicks.
        this._cards = [...this._html.matchAll(/data-section="([^"]+)"/g)]
            .map(m => makeCard(m[1]));
    },
    querySelector() { return null; },
    querySelectorAll(sel) {
        return sel === '.hub-card' ? this._cards : [];
    }
};

Hub.profile = { personal: { name: 'Test User' }, medications: [{ name: 'X' }] };
let emergencyOpened = 0;
global.window.openEmergency = function () { emergencyOpened++; };

Hub.init(root);

const cards = root.querySelectorAll('.hub-card');
if (cards.length < 10) {
    console.error('FAIL: expected the full tile grid, got', cards.length, 'cards');
    process.exit(1);
}

let failed = 0;
for (const card of cards) {
    const id = card.getAttribute('data-section');
    const kind = Hub.kindOf(id);
    Hub.route = { view: 'index', section: null };
    Hub.navStack = [];
    const before = emergencyOpened;
    card.click();
    if (kind === 'vitals') {
        if (emergencyOpened !== before + 1) {
            console.error('FAIL: vitals card did not open the emergency card');
            failed++;
        }
    } else if (Hub.route.view !== kind || Hub.route.section !== id) {
        console.error('FAIL:', id, 'routed to', JSON.stringify(Hub.route), 'expected kind', kind);
        failed++;
    } else if (!root._html.length) {
        console.error('FAIL:', id, 'rendered an empty section');
        failed++;
    }
}

// The Emergency Card tile entry must exist and be the vitals kind.
const vitals = cards.filter(c => c.getAttribute('data-section') === 'vitals');
if (!vitals.length) {
    console.error('FAIL: no vitals tile on the index');
    failed++;
}

if (failed) { console.error(failed + ' failure(s)'); process.exit(1); }
console.log('OK:', cards.length, 'index cards all route correctly');
