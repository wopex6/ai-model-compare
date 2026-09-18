"""Home-screen Emergency icon: dedicated page, generated PNG, SW allow-list."""
import json
import os
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
    assert 'Add to Home screen' in html
    assert 'Android — Firefox' in html
    assert 'iPhone or iPad' in html
    assert 'Android' in html
    assert "register('/dr_health_sw.js'" in html
    assert "register('/static/emergency_sw.js'" not in html

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
    assert 'dr-health-shell-v85' in sw
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

