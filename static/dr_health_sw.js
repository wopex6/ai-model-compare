// Service worker for the Dr. Health PWA.
//
// Scope is /dr-health, which is why this file is served from the site root by
// the /dr_health_sw.js route in app.py. A worker can only claim a scope at or
// below its own path, so while it was registered from /static/ its scope was
// /static/ — a directory no page lives in — and it never controlled the app.
//
// Two rules:
//   1. Only the paths in SHELL_ASSETS are ever cached. Everything else goes
//      straight to the network, untouched. This is an allow-list rather than a
//      list of exclusions, so any endpoint added later is uncached by default —
//      the safe direction to fail in for a health app.
//   2. Cached assets are revalidated in the background every time they are
//      used, so a stale copy survives at most one launch. Bumping CACHE_NAME
//      forces it sooner, but forgetting to no longer strands users.
const CACHE_NAME = 'dr-health-shell-v79';
const APP_SHELL = '/dr-health';
const SHELL_ASSETS = [
    APP_SHELL,
    '/static/dr_health_manifest.json',
    '/static/lab_results.js',
    '/static/health_review.js',
    '/static/health_dictation.js',
    '/static/auth_helper.js',
    '/static/message_handler.js',
    '/static/conversation_box.js',
    '/static/dr_health_hub.js',
    '/static/icons/dr_health_icon_192.png',
    '/static/icons/dr_health_icon_512.png'
];
const CACHEABLE = new Set(SHELL_ASSETS);

// Shown only when the app is opened offline and the shell was never cached —
// normally the cached shell loads instead, which can still display the
// emergency card held on this phone.
const OFFLINE_PAGE = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dr. Health — offline</title>
<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:linear-gradient(135deg,#E53935,#EF5350);font-family:'Segoe UI',system-ui,sans-serif;padding:24px}
div{background:#fff;border-radius:18px;padding:32px 24px;max-width:360px;text-align:center;color:#333}
h1{font-size:1.2rem;margin:0 0 8px;color:#c62828}p{font-size:0.9rem;line-height:1.5;color:#666;margin:0}</style>
</head><body><div><h1>No connection</h1>
<p>Dr. Health could not be opened offline because it has not finished saving
itself to this phone yet. Connect to the internet and open it once, and it will
work offline from then on.</p></div></body></html>`;

function offlineResponse() {
    return new Response(OFFLINE_PAGE, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
}

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) =>
            // Individually, not addAll: one missing asset must not abandon the
            // whole install and leave the app with no offline copy at all.
            Promise.all(SHELL_ASSETS.map((url) =>
                fetch(new Request(url, { cache: 'reload' })).then((response) => {
                    if (response && response.status === 200) {
                        return cache.put(url, response);
                    }
                }).catch(() => {})
            ))
        ).catch((err) => console.log('SW install cache failed:', err))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const request = event.request;
    if (request.method !== 'GET') return;

    let url;
    try {
        url = new URL(request.url);
    } catch (e) {
        return;
    }
    if (url.origin !== self.location.origin) return;

    // Opening the app: network first, so a deployed template change is seen
    // immediately and the page is never served stale while online. The stored
    // shell is the fallback, which is what makes an offline open work.
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).then((response) => {
                if (response && response.status === 200) {
                    const copy = response.clone();
                    event.waitUntil(
                        caches.open(CACHE_NAME).then((cache) => cache.put(APP_SHELL, copy))
                    );
                }
                return response;
            }).catch(() =>
                caches.match(APP_SHELL).then((cached) => cached || offlineResponse())
            )
        );
        return;
    }

    // Anything not on the allow-list — every API, chat, session and history
    // call — is left alone and always hits the network.
    if (!CACHEABLE.has(url.pathname)) return;

    // Shell assets: answer from the stored copy at once, then refresh it in the
    // background for the next launch.
    event.respondWith(
        caches.match(request).then((cached) => {
            const fromNetwork = fetch(request).then((response) => {
                if (response && response.status === 200) {
                    const copy = response.clone();
                    return caches.open(CACHE_NAME)
                        .then((cache) => cache.put(request, copy))
                        .then(() => response);
                }
                return response;
            });
            if (cached) {
                event.waitUntil(fromNetwork.catch(() => {}));
                return cached;
            }
            return fromNetwork;
        })
    );
});
