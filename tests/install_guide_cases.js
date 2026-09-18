// Pulls detectInstallGuide() out of the PWA template and runs it against real
// user-agent strings. The install instructions are per-browser, and a browser
// mis-detected here sends the user hunting through a menu that does not exist —
// which for this app means not installing, and WebKit then wiping the offline
// emergency card after seven days. Driven by tests/test_install_guide.py.
const fs = require('fs');
const path = require('path');

const repo = path.resolve(__dirname, '..');
const src = fs.readFileSync(path.join(repo, 'templates', 'dr_health_app.html'), 'utf8');
const start = src.indexOf('    const INSTALL_GUIDES = {');
const endMarker = '    // Static author-written markup, so innerHTML is safe here.';
const end = src.indexOf(endMarker);
if (start < 0 || end < 0) { console.error('could not locate block'); process.exit(1); }
const block = src.slice(start, end);

const cases = [
    ['iPhone Safari', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1', 0, 'Safari'],
    ['iPhone Chrome', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0 Mobile/15E148 Safari/604.1', 0, 'iPhone'],
    ['iPhone Firefox', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/127.0 Mobile/15E148 Safari/605.1.15', 0, 'iPhone'],
    ['iPhone in-app (Instagram)', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 300.0', 0, 'iPhone'],
    ['iPhone webview (no Safari token)', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148', 0, 'iPhone'],
    ['iPad Safari (reports Mac)', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15', 5, 'Safari'],
    ['Android Chrome', 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36', 5, 'Chrome'],
    ['Android Edge', 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36 EdgA/126.0', 5, 'Edge'],
    ['Samsung Internet', 'Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36', 5, 'Samsung Internet'],
    ['Firefox Android', 'Mozilla/5.0 (Android 14; Mobile; rv:127.0) Gecko/127.0 Firefox/127.0', 5, 'Firefox'],
    ['macOS Safari', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15', 0, 'Safari'],
    ['Windows Chrome', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36', 0, 'desktop'],
    ['Windows Edge', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0', 0, 'desktop'],
    ['Linux Firefox', 'Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0', 0, 'this browser'],
];

let failures = 0;
for (const [label, ua, touch, expectedName] of cases) {
    const fakeNavigator = { userAgent: ua, maxTouchPoints: touch };
    const guide = new Function('navigator', block + '\nreturn detectInstallGuide();')(fakeNavigator);
    const ok = guide.name === expectedName;
    if (!ok) failures++;
    console.log((ok ? 'PASS  ' : 'FAIL  ') + label.padEnd(30) +
        ' -> ' + guide.name + (ok ? '' : '  (expected ' + expectedName + ')') +
        '   steps=' + guide.steps.length);
}
// renderInstallSteps() lists every other browser's steps and excludes the
// detected one by label, so duplicate or missing labels would either drop a
// browser from that list or show the detected one twice.
const guides = new Function(block + '\nreturn INSTALL_GUIDES;')();
const labels = Object.keys(guides).map((k) => guides[k].label);
if (labels.some((l) => !l)) {
    console.log('FAIL  every guide needs a label -> ' + JSON.stringify(labels));
    failures++;
} else if (new Set(labels).size !== labels.length) {
    console.log('FAIL  guide labels must be unique -> ' + JSON.stringify(labels));
    failures++;
} else {
    console.log('PASS  ' + labels.length + ' guides, all labelled and unique');
}

console.log(failures ? failures + ' FAILURE(S)' : 'all checks pass (' + cases.length + ' user agents)');
process.exit(failures ? 1 : 0);
