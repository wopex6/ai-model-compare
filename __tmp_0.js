window.doLogin = function() {
                    const errEl = document.getElementById('login-error');
                    if (errEl) { errEl.textContent = 'Loading login scripts, please wait...'; errEl.style.color = '#333'; }
                };
                window.addEventListener('error', (e) => {
                    const errEl = document.getElementById('login-error');
                    if (errEl) { errEl.textContent = 'JS error: ' + e.message + ' (line ' + e.lineno + ')'; errEl.style.color = '#c62828'; }
                });