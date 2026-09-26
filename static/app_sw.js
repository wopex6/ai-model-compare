// Service worker for the AI Life Companion PWA — the whole ai-model-compare app.
//
// Served from the site root by the /app_sw.js route in app.py so it can claim
// scope '/'. The previous worker was registered from /static/, which capped
// its scope at /static/ — a directory no page lives in — so it controlled
// nothing at all. Scope '/' also covers /dr-health, but the more specific
// /dr-health worker wins for those pages; this one never sees them.
//
// Two rules, same as the Dr. Health worker:
//   1. Only the paths in SHELL_ASSETS are ever cached. Everything else —
//      every /api, chat, session and history call — goes straight to the
//      network, untouched. An allow-list means endpoints added later are
//      uncached by default: the safe direction to fail in for an app whose
//      responses carry account and health data. The worker this replaces
//      cached ANY 200 GET — including /chat/session payloads — which is why
//      it had to go, not just move.
//   2. Cached assets are revalidated in the background every time they are
//      used, so a stale copy survives at most one launch. Bumping CACHE_NAME
//      forces it sooner.
const CACHE_NAME = 'life-companion-shell-v4';
const APP_SHELL = '/chatchat';
const SHELL_ASSETS = [
    APP_SHELL,
    '/life-companion',
    // Character pages: rendered server-side but identical for every user —
    // login is client-side, so the cached shell is safe to show offline.
    '/zen_master',
    '/business_coach',
    '/life_coach',
    '/scientist',
    '/psychologist',
    '/super_motivational_coach',
    '/wisdom_sage',
    '/stoic_philosopher',
    '/gentle_companion',
    '/medical_advisor',
    '/companion',
    '/static/manifest.json',
    '/static/multi_user_styles.css',
    '/static/responsive.css',
    '/static/themes.css',
    '/static/domain_characters.css',
    '/static/avatar_styles.css',
    '/static/pwa-register.js',
    '/static/multi_user_app.js',
    '/static/auth_helper.js',
    '/static/message_handler.js',
    '/static/conversation_box.js',
    '/static/domain_characters.js',
    '/static/explicit_context_ui.js',
    '/static/file_upload_handler.js',
    '/static/personality_interpretation_display.js',
    '/static/proactive_clarification_ui.js',
    '/static/avatar_engine.js',
    '/static/avatar_widget.js',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];
// Templates request some of these with ?v= cache-busters; match on pathname
// so the query never defeats the allow-list.
const CACHEABLE = new Set(SHELL_ASSETS);

const OFFLINE_PAGE = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Life Companion — offline</title>
<style>body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:linear-gradient(135deg,#667eea,#764ba2);font-family:'Segoe UI',system-ui,sans-serif;padding:24px}
div{background:#fff;border-radius:18px;padding:32px 24px;max-width:360px;text-align:center;color:#333}
h1{font-size:1.2rem;margin:0 0 8px;color:#5a67d8}p{font-size:0.9rem;line-height:1.5;color:#666;margin:0}</style>
</head><body><div><h1>No connection</h1>
<p>AI Life Companion needs the internet to chat. Some pages you have opened
before may still load — otherwise reconnect and try again.</p></div></body></html>`;

function offlineResponse() {
    return new Response(OFFLINE_PAGE, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
}

function cached(pathname) {
    return caches.open(CACHE_NAME).then(cache => cache.match(pathname));
}

// Serve the cached copy immediately and refresh it in the background — a
// stale asset self-heals on the next launch instead of needing a version bump.
function staleWhileRevalidate(request, pathname) {
    return caches.open(CACHE_NAME).then(cache =>
        cache.match(pathname).then(hit => {
            const refresh = fetch(request).then(response => {
                if (response && response.ok) cache.put(pathname, response.clone());
                return response;
            }).catch(() => null);
            return hit || refresh.then(response => response || offlineResponse());
        })
    );
}

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(SHELL_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(names => Promise.all(names
                .filter(name => name !== CACHE_NAME)
                .map(name => caches.delete(name))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const request = event.request;
    if (request.method !== 'GET') return;
    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;

    if (CACHEABLE.has(url.pathname)) {
        event.respondWith(staleWhileRevalidate(request, url.pathname));
        return;
    }

    // Navigations to uncached pages: network first, then the app shell so an
    // installed app still opens offline, then the offline notice.
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(() =>
                cached(APP_SHELL).then(hit => hit || offlineResponse()))
        );
    }
    // Everything else — every API, session, history and auth call — passes
    // through to the network untouched.
});

// Push notifications: the Life Companion reminder channel. Shows whatever the
// server sends; tapping focuses the app.
self.addEventListener('push', event => {
    if (!event.data) return;
    let data = {};
    try { data = event.data.json(); } catch (e) { data = { body: event.data.text() }; }
    const options = {
        body: data.body || 'New message from Life Companion',
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-72.png',
        data: { url: data.url || '/chatchat' }
    };
    event.waitUntil(
        self.registration.showNotification(data.title || 'Life Companion', options)
    );
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || '/chatchat';
    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clients => {
                for (const client of clients) {
                    if (client.url.startsWith(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                return self.clients.openWindow(url);
            })
    );
});
