if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/dr_health_sw.js')
                .then((r) => console.log('Dr Health SW registered:', r.scope))
                .catch((e) => console.log('Dr Health SW registration failed:', e));
        }