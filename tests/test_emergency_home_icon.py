"""Home-screen Emergency icon: dedicated page, generated PNG, SW allow-list."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from ai_compare.emergency_icon import emergency_icon_png, ALLOWED_SIZES


def test_emergency_icon_png_is_valid_png():
    data = emergency_icon_png(192)
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    assert b'IEND' in data
    assert len(data) > 200


def test_emergency_page_and_icons_are_public():
    client = app_module.app.test_client()
    page = client.get('/dr-health/emergency')
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert 'emergency_card.js' in html
    assert 'emergency_manifest.json' in html
    assert 'id="install-now"' in html
    assert 'Add to home screen' in html
    assert 'iPhone has no install button' in html
    assert 'Add to Home Screen' in html
    assert 'Android — Firefox' not in html
    assert "register('/dr_health_sw.js'" in html
    assert "register('/static/emergency_sw.js'" not in html
    assert 'id="emergency-refresh"' in html
    assert 'id="emergency-close"' in html
    assert 'id="emergency-pair-form"' in html
    assert 'emergency-card/pair' in open(
        os.path.join(os.path.dirname(__file__), '..', 'static', 'emergency_card.js'),
        encoding='utf-8').read()
    assert 'autoRefresh' in html
    assert 'cameFromDrHealth' in html
    assert 'window.close()' in html
    assert 'href="/dr-health"' not in html
    assert 'href="/dr-health/"' not in html

    redir = client.get('/emergency', follow_redirects=False)
    assert redir.status_code == 302
    assert redir.headers['Location'].endswith('/dr-health/emergency')

    for size in ALLOWED_SIZES:
        resp = client.get(f'/dr-health/emergency-icon-{size}.png')
        assert resp.status_code == 200, size
        assert resp.headers['Content-Type'] == 'image/png'
        assert resp.data[:8] == b'\x89PNG\r\n\x1a\n'

    missing = client.get('/dr-health/emergency-icon-16.png')
    assert missing.status_code == 404


def test_logged_in_emergency_modal_has_back():
    html = open(os.path.join(os.path.dirname(__file__), '..',
                             'templates', 'dr_health_app.html'),
                encoding='utf-8').read()
    assert 'id="emergency-back"' in html
    assert "pushState({ emergency: true }" in html
    assert "addEventListener('popstate'" in html
    assert 'id="emergency-close"' not in html
    assert 'leaveEmergencyToHub' in html
    assert 'skipPush: true' in html
    assert "kind: 'emergency'" in html
    assert "JSON.stringify({username: u})" in html
    assert "JSON.stringify({username: u, password: p})" not in html
    assert "modal: 'review'" in html
    assert "modal: 'data'" in html
    assert 'id="emergency-show-pair"' in html


def test_emergency_manifest_is_its_own_app():
    raw = open(os.path.join(os.path.dirname(__file__), '..',
                            'static', 'emergency_manifest.json'),
               encoding='utf-8').read()
    manifest = json.loads(raw)
    assert manifest['id'] == '/dr-health/emergency'
    assert manifest['start_url'] == '/dr-health/emergency'
    assert manifest['display'] == 'standalone'
    assert any('emergency-icon' in i.get('src', '') for i in manifest['icons'])


def test_main_manifest_has_emergency_shortcut():
    raw = open(os.path.join(os.path.dirname(__file__), '..',
                            'static', 'dr_health_manifest.json'),
               encoding='utf-8').read()
    manifest = json.loads(raw)
    urls = [s.get('url') for s in manifest.get('shortcuts') or []]
    assert '/dr-health/emergency' in urls


def test_service_worker_caches_emergency_shell_separately():
    sw = open(os.path.join(os.path.dirname(__file__), '..',
                           'static', 'dr_health_sw.js'),
              encoding='utf-8').read()
    assert "EMERGENCY_SHELL = '/dr-health/emergency'" in sw
    assert '/static/emergency_card.js' in sw
    assert "pathname === EMERGENCY_SHELL" in sw
    # Version-agnostic: the cache name bumps every static change, so assert the
    # pattern, not the number (pinning it broke on every legitimate bump).
    assert re.search(r"CACHE_NAME = 'dr-health-shell-v\d+'", sw)
    # The previous bug: every navigate was stored as the main app shell, so
    # opening Emergency offline would have overwritten /dr-health.
    assert 'cache.put(APP_SHELL, copy)' not in sw
    assert 'cache.put(dest, copy)' in sw


def test_emergency_card_js_escapes_and_lists_dose():
    import shutil
    import subprocess
    if shutil.which('node') is None:
        return
    script = r"""
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync('static/emergency_card.js', 'utf8');
const ctx = { window: {}, localStorage: { getItem: () => null, setItem: () => {} } };
ctx.window = ctx;
vm.runInNewContext(code, ctx);
const html = ctx.EmergencyCard.html({
    name: '<script>x</script>',
    medications: [{ name: 'Metformin', dose: '500mg', frequency: 'twice daily' }]
});
if (html.indexOf('<script>x</script>') !== -1) { console.error('UNESCAPED'); process.exit(1); }
if (html.indexOf('&lt;script&gt;') === -1) { console.error('NO ESCAPE'); process.exit(1); }
if (html.indexOf('Metformin') === -1 || html.indexOf('500mg') === -1 ||
    html.indexOf('twice daily') === -1) { console.error('MEDS'); process.exit(1); }
if (html.indexOf('Personal Details') === -1 || html.indexOf('Conditions') === -1) {
    console.error('SOURCE NOTE'); process.exit(1);
}
console.log('PASS');
"""
    result = subprocess.run(
        ['node', '-e', script],
        cwd=os.path.join(os.path.dirname(__file__), '..'),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS' in result.stdout


def test_hub_back_goes_one_level():
    hub = open(os.path.join(os.path.dirname(__file__), '..',
                            'static', 'dr_health_hub.js'),
               encoding='utf-8').read()
    assert 'backOneLevel' in hub
    assert 'self.backOneLevel()' in hub
    assert 'navStack' in hub
    assert 'pushReturn' in hub
    assert "prev.kind === 'emergency'" in hub
    assert 'skipPush' in hub
    assert 'hubNav' in hub
    assert "back.addEventListener('click', () => self.go('index'))" not in hub
    assert 'data-cancel="1"' not in hub
    assert 'hub-dob-cancel' in hub
    assert 'GP visit brief' in hub
    assert 'Explain this result' in hub
    assert '/api/health-profile/visit-brief' in hub
    assert '/api/health-profile/explain-test' in hub


def test_hub_form_actually_builds_and_reads_back_unknown_fields():
    """Run the real functions, not a text search. A row carrying columns the
    schema never declared must produce a box for each one, and reading the form
    back must put 'fields.<heading>' into the nested bag rather than creating a
    top-level key named after a column."""
    import shutil
    import subprocess
    if shutil.which('node') is None:
        return
    script = r"""
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync('static/dr_health_hub.js', 'utf8');
const ctx = { window: {}, document: { getElementById: () => null },
              localStorage: { getItem: () => null, setItem: () => {} } };
ctx.window = ctx;
vm.runInNewContext(code, ctx);
const hub = ctx.DrHealthHub;
function fail(m) { console.error(m); process.exit(1); }

const row = {
    test_name: 'FEV1 (L) (Pre-Bronch)', value: '0.96 L',
    reference_range: 'Pred 1.62 L', date: '2026-09-20', unit: 'L',
    qualifier: 'Pre-Bronch', section: 'SPIROMETRY',
    fields: { 'Pre-Bronch %Pred': '59', 'Method': 'spirometry' },
    // Bookkeeping the app maintains — visible, but never a text box.
    status: 'active', last_confirmed_at: '2026-09-20T10:00:00',
    history: [{ at: 'x' }], ref_locked: false, date_source: 'filed',
    added_at: '2026-09-20T10:00:00', source: 'document_extracted'
};
const extras = hub.extraFields('test_results', row);
const keys = extras.map((f) => f.key);

// Each report column gets its own box, keyed by the report's own heading.
if (keys.indexOf('fields.Pre-Bronch %Pred') === -1) fail('MISSING NESTED %Pred: ' + keys);
if (keys.indexOf('fields.Method') === -1) fail('MISSING NESTED Method: ' + keys);
// Undeclared scalars too.
if (keys.indexOf('qualifier') === -1 || keys.indexOf('section') === -1) fail('MISSING SCALAR: ' + keys);
// Never the bookkeeping, and never a declared field twice.
['status', 'last_confirmed_at', 'history', 'ref_locked', 'date_source',
 'added_at', 'source', 'test_name', 'value', 'date', 'fields'].forEach((k) => {
    if (keys.indexOf(k) !== -1) fail('OFFERED A BOX FOR ' + k);
});

// The nested heading carries a space and a per-cent sign; the element id must
// be sanitised while data-key keeps the real heading.
const inputHtml = hub.inputHtml(extras[keys.indexOf('fields.Pre-Bronch %Pred')], '59');
if (inputHtml.indexOf('data-key="fields.Pre-Bronch %Pred"') === -1) fail('DATA-KEY LOST: ' + inputHtml);
if (/id="[^"]*[ %]/.test(inputHtml)) fail('UNSAFE ID: ' + inputHtml);

// Reading the form back must rebuild the nested bag.
const inputs = [
    { key: 'value', type: 'text', value: '0.97 L' },
    { key: 'fields.Pre-Bronch %Pred', type: 'text', value: '60' },
    { key: 'fields.Method', type: 'text', value: 'spirometry' }
];
const formEl = { querySelectorAll: () => inputs.map((i) => ({
    value: i.value,
    getAttribute: (a) => (a === 'data-key' ? i.key : i.type)
})) };
const out = hub.readForm(formEl);
if (out.value !== '0.97 L') fail('VALUE: ' + JSON.stringify(out));
if (!out.fields || out.fields['Pre-Bronch %Pred'] !== '60') fail('NESTED NOT REBUILT: ' + JSON.stringify(out));
if (out.fields.Method !== 'spirometry') fail('NESTED METHOD: ' + JSON.stringify(out));
if ('fields.Method' in out) fail('FLAT KEY LEAKED: ' + JSON.stringify(out));
console.log('PASS');
"""
    result = subprocess.run(
        ['node', '-e', script],
        cwd=os.path.join(os.path.dirname(__file__), '..'),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS' in result.stdout


def test_editing_form_renders_fields_the_schema_does_not_declare():
    """A report kind nobody anticipated stores its extra columns under the
    report's own headings. If the form only rendered declared fields those
    would be read-only curiosities, so the form has to build boxes for
    whatever the record carries — and must not offer a box for lifecycle
    bookkeeping, which is the app's to maintain."""
    hub = open(os.path.join(os.path.dirname(__file__), '..',
                            'static', 'dr_health_hub.js'),
               encoding='utf-8').read()
    assert 'extraFields(' in hub
    assert 'this.extraFields(id, item)' in hub
    assert "'fields.' + k" in hub
    assert 'MANAGED_KEYS' in hub
    for managed in ('last_confirmed_at', 'history', 'ref_locked', 'date_source'):
        assert managed in hub
    # 'fields.<heading>' must land back in the nested bag, not create a
    # top-level key named after a column.
    assert 'out[parent][child] = value' in hub


def test_document_analysis_is_downloadable_as_a_file():
    """The whole reading of one document — transcribed text, extracted rows,
    skipped rows and the role given to each column — has to be inspectable
    outside the app; no screen has room for it."""
    app_py = open(os.path.join(os.path.dirname(__file__), '..', 'app.py'),
                  encoding='utf-8').read()
    assert "request.args.get('download')" in app_py
    assert 'attachment; filename=' in app_py
    # Patient data must not be cached by a proxy or the service worker.
    assert "response.headers['Cache-Control'] = 'no-store'" in app_py
    html = open(os.path.join(os.path.dirname(__file__), '..',
                             'templates', 'dr_health_app.html'),
                encoding='utf-8').read()
    assert 'downloadStoredAnalysis' in html
    assert 'document-result?download=1' in html
    sw = open(os.path.join(os.path.dirname(__file__), '..',
                           'static', 'dr_health_sw.js'), encoding='utf-8').read()
    assert 'document-result' not in sw, 'analysis files must never be precached'


def test_emergency_card_links_do_not_pop_their_own_history_entry():
    """Tapping Personal Details / Medications / Conditions on the card must
    stay on that section. history.back() is asynchronous, so popping the
    card's entry delivered a popstate after the hub had drilled in, and the
    popstate handler read it as "back one level" — the section closed again
    in the same tap."""
    html = open(os.path.join(os.path.dirname(__file__), '..',
                             'templates', 'dr_health_app.html'),
                encoding='utf-8').read()
    assert 'data-hub-go="personal"' in html
    assert 'data-hub-go="medications"' in html
    assert 'data-hub-go="conditions"' in html
    assert 'closeEmergency({ keepHistoryEntry: true })' in html
    assert 'opts.keepHistoryEntry' in html
    # The unwinding branch still exists for the plain Back button.
    assert 'history.back();' in html
    body = html.split('function leaveEmergencyToHub')[1].split('function openEmergency')[0]
    assert 'history.back()' not in body


def test_chat_has_attach_review_and_digest_hooks():
    html = open(os.path.join(os.path.dirname(__file__), '..',
                             'templates', 'dr_health_app.html'),
                encoding='utf-8').read()
    assert 'id="chat-review-prompt"' in html
    assert 'id="chat-photo-btn"' in html
    assert 'id="chat-file-btn"' in html
    assert 'personaliseQuickTopics' in html
    assert 'maybeShowDigestInChat' in html
    assert '/api/health-profile/upload' in html

