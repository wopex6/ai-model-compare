// Service worker for the Dr. Health PWA.
// Caches the app shell for fast/offline load; all API/data requests always go to network.
const CACHE_NAME = 'dr-health-shell-v22';
const SHELL_ASSETS = [
    '/dr-health',
    '/static/dr_health_manifest.json',
    '/static/auth_helper.js',
    '/static/message_handler.js',
    '/static/conversation_box.js',
    '/static/icons/dr_health_icon_192.png',
    '/static/icons/dr_health_icon_512.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS)).catch(() => {})
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
    const url = new URL(event.request.url);

    // Never cache API calls or chat/auth endpoints — always go to network.
    if (url.pathname.startsWith('/api/') || url.pathname.includes('/chat') ||
        url.pathname.includes('/session') || url.pathname.includes('/history') ||
        url.pathname.includes('/daily-insight')) {
        return;
    }

    // App shell: cache-first, fall back to network.
    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request).then((response) => {
                if (response && response.status === 200 && event.request.method === 'GET') {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
                }
                return response;
            }).catch(() => cached);
        })
    );
});
