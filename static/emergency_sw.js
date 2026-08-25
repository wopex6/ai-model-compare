// Service worker for the Emergency Info PWA.
// Caches the app shell so the card loads instantly, even with no network.
const CACHE_NAME = 'emergency-info-v2';
const SHELL_ASSETS = [
    '/emergency',
    '/static/emergency_manifest.json',
    '/static/auth_helper.js',
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

    // Never cache API calls — always go to network.
    if (url.pathname.startsWith('/api/')) {
        return;
    }

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
