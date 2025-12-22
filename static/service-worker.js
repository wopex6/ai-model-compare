// Service Worker for AI Life Companion PWA
const CACHE_NAME = 'life-companion-v1';
const STATIC_CACHE = 'static-v1';

// Files to cache for offline use
const STATIC_FILES = [
    '/',
    '/chatchat',
    '/life-companion',
    '/static/multi_user_styles.css',
    '/static/domain_characters.css',
    '/static/responsive.css',
    '/static/manifest.json'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Install');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[ServiceWorker] Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .catch((err) => {
                console.log('[ServiceWorker] Cache failed:', err);
            })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[ServiceWorker] Activate');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE) {
                        console.log('[ServiceWorker] Removing old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests and API calls
    if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    // Return cached version
                    return cachedResponse;
                }

                // Not in cache, fetch from network
                return fetch(event.request)
                    .then((networkResponse) => {
                        // Don't cache if not a valid response
                        if (!networkResponse || networkResponse.status !== 200) {
                            return networkResponse;
                        }

                        // Clone the response for caching
                        const responseToCache = networkResponse.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return networkResponse;
                    })
                    .catch(() => {
                        // Network failed, return offline page if available
                        if (event.request.mode === 'navigate') {
                            return caches.match('/chatchat');
                        }
                    });
            })
    );
});

// Handle push notifications (future feature)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body || 'New message from Life Companion',
            icon: '/static/icons/icon-192.png',
            badge: '/static/icons/icon-72.png',
            vibrate: [100, 50, 100],
            data: {
                url: data.url || '/life-companion'
            }
        };

        event.waitUntil(
            self.registration.showNotification(data.title || 'Life Companion', options)
        );
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then((clientList) => {
                // If app is already open, focus it
                for (const client of clientList) {
                    if (client.url.includes('/life-companion') && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Otherwise open new window
                if (clients.openWindow) {
                    return clients.openWindow(event.notification.data.url || '/life-companion');
                }
            })
    );
});
