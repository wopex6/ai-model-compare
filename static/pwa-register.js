// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then((registration) => {
                console.log('✅ ServiceWorker registered:', registration.scope);
            })
            .catch((error) => {
                console.log('❌ ServiceWorker registration failed:', error);
            });
    });
}

// Handle PWA install prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show install button if exists
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
        installBtn.style.display = 'block';
        installBtn.addEventListener('click', () => {
            // Hide install button
            installBtn.style.display = 'none';
            // Show prompt
            deferredPrompt.prompt();
            // Wait for user to respond
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('✅ User accepted the install prompt');
                } else {
                    console.log('❌ User dismissed the install prompt');
                }
                deferredPrompt = null;
            });
        });
    }
});

// Handle successful install
window.addEventListener('appinstalled', () => {
    console.log('✅ PWA was installed');
    // Hide install button
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
        installBtn.style.display = 'none';
    }
});

// Check if running as installed PWA
function isPWA() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
}

// Export for use elsewhere
window.PWA = {
    isPWA: isPWA,
    canInstall: () => !!deferredPrompt,
    install: () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
        }
    }
};
