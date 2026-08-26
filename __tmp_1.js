// ---------- Register service worker ----------
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/dr_health_sw.js').then(reg => {
            if (navigator.serviceWorker.controller) {
                reg.addEventListener('updatefound', () => {
                    const newWorker = reg.installing;
                    if (newWorker) {
                        newWorker.addEventListener('statechange', () => {
                            if (newWorker.state === 'activated') {
                                window.location.reload();
                            }
                        });
                    }
                });
            }
        }).catch(() => {});
    }
    let currentProfile = null;

    // ---------- Navigation ----------
    function showScreen(id) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.target === id));
        document.getElementById('topbar-title').textContent = id === 'chat-screen' ? 'Dr. Health' : 'Health Profile';
        if (id === 'profile-screen') loadHealthProfile();
    }
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => showScreen(btn.dataset.target));
    });

    // ---------- Auth gating ----------
    function checkAuth() {
        const loginScreen = document.getElementById('login-screen');
        if (AuthHelper.isAuthenticated()) {
            loginScreen.classList.add('hidden');
            return true;
        } else {
            loginScreen.classList.remove('hidden');
            return false;
        }
    }

    const CREDENTIALS_KEY = 'drHealth.credentials.v1';
    function getStoredCredentials() {
        try { return JSON.parse(localStorage.getItem(CREDENTIALS_KEY)); }
        catch (e) { return null; }
    }
    function clearStoredCredentials() {
        localStorage.removeItem(CREDENTIALS_KEY);
    }

    async function doLogin(username, password) {
        const u = (username !== undefined) ? username : document.getElementById('login-username').value.trim();
        const p = (password !== undefined) ? password : document.getElementById('login-password').value;
        const errEl = document.getElementById('login-error');
        const btn = document.getElementById('login-btn');
        errEl.textContent = 'Logging in...';
        errEl.style.color = '#333';
        if (btn) { btn.disabled = true; btn.textContent = 'Logging in...'; }
        if (typeof u !== 'string' || typeof p !== 'string') {
            errEl.textContent = 'Stored credentials are invalid. Please enter them again.';
            clearStoredCredentials();
            if (btn) { btn.disabled = false; btn.textContent = 'Log on'; }
            return;
        }
        if (!u || !p) { errEl.textContent = 'Enter username and password.'; if (btn) { btn.disabled = false; btn.textContent = 'Log on'; } return; }
        try {
            const resp = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p })
            });
            const data = await resp.json();
            if (!resp.ok || !data.success) {
                errEl.textContent = data.error || 'Login failed.';
                clearStoredCredentials();
                if (btn) { btn.disabled = false; btn.textContent = 'Log on'; }
                return;
            }
            AuthHelper.setAuthToken(data.token);
            localStorage.setItem(CREDENTIALS_KEY, JSON.stringify({username: u, password: p}));
            document.getElementById('login-screen').classList.add('hidden');
            initApp();
        } catch (e) {
            errEl.textContent = 'Login error: ' + (e && e.message ? e.message : String(e));
            errEl.style.color = '#c62828';
            if (btn) { btn.disabled = false; btn.textContent = 'Log on'; }
        }
    }
    window.doLogin = doLogin;

    document.getElementById('login-btn').addEventListener('click', (ev) => {
        ev.preventDefault();
        doLogin();
    });

    document.getElementById('logout-btn').addEventListener('click', () => {
        AuthHelper.clearAuthToken();
        clearStoredCredentials();
        location.reload();
    });

    // ---------- Thinking / Chat UI ----------
    function showThinking() {
        if (document.getElementById('thinking-bubble')) return;
        const chatMessages = document.getElementById('chatMessages');
        const wrapper = document.createElement('div');
        wrapper.className = 'message bot-message';
        wrapper.id = 'thinking-bubble';
        wrapper.innerHTML = `<div class="message-bubble thinking-bubble">
            <div class="typing-dots"><span></span><span></span><span></span></div>
            <span style="font-size:0.8rem;margin-left:4px;">Dr. Health is thinking...</span>
        </div>`;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        const inputArea = document.getElementById('sendBtn').closest('.chat-input-area');
        if (inputArea) inputArea.classList.add('sending');
    }
    function hideThinking() {
        const t = document.getElementById('thinking-bubble');
        if (t) t.remove();
        const inputArea = document.getElementById('sendBtn').closest('.chat-input-area');
        if (inputArea) inputArea.classList.remove('sending');
    }

    // ---------- Chat ----------
    let appInitialized = false;
    function initApp() {
        if (appInitialized) return;
        appInitialized = true;

        MessageHandler.init('medical_advisor', {
            userColor: '#c62828',
            botColor: '#E53935',
            characterDisplayName: 'Dr. Health',
            messageClass: 'message',
            bubbleClass: 'message-bubble'
        });

        ConversationBox.init('medical_advisor', {
            inputElementId: 'userInput',
            sendButtonId: 'sendBtn',
            errorMessage: 'I apologize, but I encountered a temporary issue. Please try again.',
            onMessageSent: () => showThinking(),
            onResponseReceived: () => hideThinking(),
            onError: () => hideThinking(),
            localCache: true,
            localStorageKey: 'drHealth.conversation.medical.v1',
            offlineMessage: "You are currently offline. Your message has been saved on this phone. Please connect to the internet so Dr. Health can respond.",
            onHistoryLoaded: (messages) => {
                if (!messages || messages.length === 0) {
                    MessageHandler.addMessage({
                        content: "Hello! I'm Dr. Health. Ask me about symptoms, wellness, nutrition, or anything health-related. Remember: I provide general information only — for personal medical advice, consult your healthcare provider.",
                        role: 'bot',
                        shouldScroll: false
                    });
                }
            }
        });

        document.querySelectorAll('#quick-topics-bar .qt').forEach(el => {
            el.addEventListener('click', () => ConversationBox.sendQuickMessage(el.dataset.msg));
        });

        loadHealthProfile();
        showScreen('chat-screen');
    }

        function normalizeTestType(testName) {
            if (!testName) return 'Unknown Test';
            return testName
                .replace(/\(.*?\)/g, '')
                .replace(/historical/ig, '')
                .replace(/\s+/g, ' ')
                .trim() || testName.trim();
        }
        function parseReferenceRange(ref) {
            const nums = String(ref || '').match(/\d+(?:\.\d+)?/g) || [];
            if (nums.length >= 2) {
                const [a, b] = nums.map(parseFloat);
                return [Math.min(a, b), Math.max(a, b)];
            }
            return [null, null];
        }
        function testStatus(num, lower, upper) {
            if (lower === null || upper === null) return 'normal';
            if (num > upper) return 'high';
            if (num < lower) return 'low';
            return 'normal';
        }
        function statusColor(status) {
            return { high: '#e6a000', low: '#1565c0', normal: '#43a047' }[status] || '#999';
        }
        function computeTestFlag(num, ref) {
            if (isNaN(num)) return '';
            const [lower, upper] = parseReferenceRange(ref);
            if (lower === null || upper === null) return '';
            const s = testStatus(num, lower, upper);
            return s === 'high' ? 'H' : s === 'low' ? 'L' : '';
        }
        function buildSparkline(values, referenceRange = '') {
            const nums = values.map(v => parseFloat(v)).filter(v => !isNaN(v));
            if (nums.length < 2) return '';
            const [lower, upper] = parseReferenceRange(referenceRange);
            const statuses = nums.map(v => testStatus(v, lower, upper));
            const min = Math.min(...nums), max = Math.max(...nums);
            const range = max - min || 1;
            const w = 60, h = 18;
            const step = w / (nums.length - 1);
            const points = nums.map((v, i) => [i * step, h - ((v - min) / range) * h]);
            let svg = `<svg width="${w}" height="${h}" class="sparkline">`;
            for (let i = 0; i < points.length - 1; i++) {
                const color = statusColor(statuses[i + 1]);
                const [x1, y1] = points[i];
                const [x2, y2] = points[i + 1];
                svg += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>`;
                if (statuses[i + 1] === 'high') {
                    const y1b = Math.min(h - 1, y1 + 1.8);
                    const y2b = Math.min(h - 1, y2 + 1.8);
                    svg += `<line x1="${x1.toFixed(1)}" y1="${y1b.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2b.toFixed(1)}" stroke="#fff176" stroke-width="1.5" stroke-linecap="round"/>`;
                }
            }
            for (let i = 0; i < points.length; i++) {
                const [x, y] = points[i];
                if (statuses[i] === 'high') svg += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" fill="#000"/>`;
                if (statuses[i] === 'low') svg += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" fill="#c62828"/>`;
            }
            svg += `</svg>`;
            return svg;
        }
        function extractTestUnit(value) {
            const m = String(value || '').match(/^-?\d+(?:\.\d+)?(?:\s+(?:H|L|High|Low))?\s*(.*)$/i);
            if (!m) return '';
            return m[1].replace(/(?:\s+|^)(H|L|High|Low)$/i, '').trim();
        }
        function stripTestUnit(value, unit) {
            if (!unit) return String(value || '');
            const esc = unit.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const re = new RegExp('\\s*' + esc + '(?=\\s+(?:H|L|High|Low)\\b|\\s*$)', 'i');
            return String(value || '').replace(re, '').trim();
        }
        function extractTestFlag(value) {
            const m = String(value || '').match(/\b(H|L)\b/i);
            return m ? m[1].toUpperCase() : '';
        }
        function normalizeDateInput(text) {
            const t = (text || '').trim();
            if (!t) return null;
            let m;
            if ((m = t.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/))) return `${m[1]}-${String(m[2]).padStart(2,'0')}-${String(m[3]).padStart(2,'0')}`;
            if ((m = t.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/))) return `${m[3]}-${String(m[2]).padStart(2,'0')}-${String(m[1]).padStart(2,'0')}`;
            if ((m = t.match(/^(\d{4})-(\d{1,2})$/))) return `${m[1]}-${String(m[2]).padStart(2,'0')}-01`;
            if ((m = t.match(/^(\d{4})$/))) return `${m[1]}-01-01`;
            const d = new Date(t);
            if (!Number.isNaN(d.getTime())) return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
            return null;
        }

    // ---------- Health profile ----------
    async function loadHealthProfile() {
        const el = document.getElementById('profile-summary');
        el.innerHTML = '<em style="color:#999;"><i class="fas fa-spinner fa-spin"></i> Loading...</em>';
        try {
            const resp = await AuthHelper.authenticatedFetch('/api/health-profile');
            if (!resp.ok) { el.innerHTML = '<em style="color:#999;">No profile yet. Chat or add info to start building yours.</em>'; return; }
            const d = await resp.json();
            if (!d.success || !d.profile) { el.innerHTML = '<em style="color:#999;">No profile yet.</em>'; return; }
            const p = d.profile;
            currentProfile = p;
            let html = '';
            if (p.name) html += `<div style="margin-bottom:8px;"><strong>${p.name}</strong></div>`;
            if (p.conditions && p.conditions.length) {
                html += '<strong style="color:#c62828;">Conditions:</strong><ul>';
                p.conditions.forEach(c => { if (c.status === 'active' || c.status === 'investigating') html += `<li>${c.name}</li>`; });
                html += '</ul>';
            }
            if (p.test_results && p.test_results.length) {
                const testGroups = {};
                p.test_results.forEach((t, idx) => {
                    t._sourceIndex = idx;
                    const key = normalizeTestType(t.test_name).toLowerCase();
                    if (!testGroups[key]) testGroups[key] = { displayName: normalizeTestType(t.test_name), entries: [] };
                    testGroups[key].entries.push(t);
                });
                const sortedGroups = Object.values(testGroups).map(g => {
                    g.entries.sort((a, b) => (new Date(b.date || '1970-01-01') - new Date(a.date || '1970-01-01')));
                    return g;
                }).sort((a, b) => {
                    const da = a.entries.length ? new Date(a.entries[0].date || '1970-01-01') : new Date(0);
                    const db = b.entries.length ? new Date(b.entries[0].date || '1970-01-01') : new Date(0);
                    if (db.getTime() !== da.getTime()) return db - da;
                    return a.displayName.localeCompare(b.displayName);
                });

                html += '<strong style="color:#1565C0;">Test Results:</strong>';
                sortedGroups.forEach(group => {
                    const unit = group.entries.map(e => extractTestUnit(e.value)).find(u => u) || '';
                    const ref = group.entries.map(e => e.reference_range || '').find(r => r.trim()) || '';
                    const escUnit = unit ? unit.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') : '';
                    const displayName = unit ? group.displayName.replace(new RegExp('(?:^|\\s)' + escUnit + '(?:\\s|$)', 'ig'), ' ').replace(/\s+/g, ' ').trim() : group.displayName;
                    const metaUnit = unit && !ref.toLowerCase().includes(unit.toLowerCase()) ? unit : '';
                    const meta = [ref, metaUnit].filter(Boolean).join(' ');
                    const spark = buildSparkline(group.entries.slice().reverse().map(e => e.value), ref);
                    html += `<div class="pwa-test-group">`;
                    html += `<div style="font-weight:600; color:#1565C0; display:flex; align-items:center; gap:6px; flex-wrap:wrap; margin-bottom:4px;"><i class="fas fa-vial"></i> <span>${displayName}</span> <span style="color:#666; font-weight:400;">${meta}</span> ${spark}</div>`;
                    html += `<table><thead><tr><th>Date</th><th>Value</th></tr></thead><tbody>`;
                    group.entries.forEach(t => {
                        const stripped = stripTestUnit(t.value, unit);
                        const displayVal = stripped.replace(/^(?:H|L|High|Low)\s+/i, '').replace(/\s+(?:H|L|High|Low)$/i, '').trim();
                        const num = parseFloat(displayVal);
                        let flag = computeTestFlag(num, ref) || extractTestFlag(stripped);
                        const flagHtml = flag ? `<span style="font-size:0.7rem; color:${flag === 'H' ? '#c62828' : '#1565c0'}; font-weight:600; margin-left:4px;">${flag}</span>` : '<span style="font-size:0.7rem; color:#999; margin-left:4px;">—</span>';
                        html += `<tr><td style="white-space:nowrap; color:#555;"><span class="pwa-tt-editable" contenteditable="false" data-idx="${t._sourceIndex}" data-field="date" ontouchstart="startEditHold(this, event)" ontouchend="cancelEditHold()" ontouchmove="cancelEditHold()" oncontextmenu="return false" onblur="saveTestResult(this)">${t.date || ''}</span></td>`;
                        html += `<td style="font-weight:500;"><span class="pwa-tt-editable" contenteditable="false" data-idx="${t._sourceIndex}" data-field="value" data-unit="${unit.replace(/"/g, '&quot;')}" ontouchstart="startEditHold(this, event)" ontouchend="cancelEditHold()" ontouchmove="cancelEditHold()" oncontextmenu="return false" onblur="saveTestResult(this)">${displayVal}</span> ${flagHtml}</td></tr>`;
                    });
                    html += `</tbody></table></div>`;
                });
            }
            if (p.action_plans && p.action_plans.length) {
                const active = p.action_plans.filter(a => a.status === 'active');
                if (active.length) {
                    html += '<strong style="color:#2E7D32;">Active Plans:</strong><ul>';
                    active.forEach(a => html += `<li>${a.title}</li>`);
                    html += '</ul>';
                }
            }
            if (p.follow_ups && p.follow_ups.length) {
                const active = p.follow_ups.filter(f => f.status === 'active');
                if (active.length) {
                    html += '<strong style="color:#1565C0;">Active Follow-ups:</strong><ul>';
                    active.slice(-5).forEach(f => html += `<li>${f.title}${f.due_date ? ' (due ' + f.due_date + ')' : ''}</li>`);
                    html += '</ul>';
                }
            }
            if (p.questions_for_doctor && p.questions_for_doctor.length) {
                const open = p.questions_for_doctor.filter(q => !q.answered);
                if (open.length) {
                    html += '<strong style="color:#6A1B9A;">Questions for Doctor:</strong><ul>';
                    open.slice(-5).forEach(q => html += `<li>${q.question}</li>`);
                    html += '</ul>';
                }
            }
            if (p.supplements && p.supplements.length) {
                html += `<strong style="color:#6A1B9A;">Supplements:</strong> ${p.supplements.map(s => s.name).join(', ')}`;
            }
            const vitals = { ...(p.vitals || {}), ...loadVitals() };
            if (vitals.name || vitals.age || vitals.blood || vitals.conditions || vitals.medications || vitals.allergies || vitals.doctors || vitals.ecName || vitals.ecPhone) {
                html += '<strong style="color:#c62828;"><i class="fas fa-kit-medical"></i> Emergency / Vitals:</strong><ul>';
                if (vitals.name) html += `<li><strong>${vitals.name}</strong>${vitals.age ? ' (' + vitals.age + ')' : ''}${vitals.blood ? ' • Blood: ' + vitals.blood : ''}</li>`;
                if (vitals.conditions) html += `<li>Conditions: ${vitals.conditions}</li>`;
                if (vitals.medications) html += `<li>Medications: ${vitals.medications}</li>`;
                if (vitals.allergies) html += `<li>Allergies: ${vitals.allergies}</li>`;
                if (vitals.doctors) html += `<li>Doctors: ${vitals.doctors}</li>`;
                if (vitals.ecName || vitals.ecPhone) html += `<li>Emergency contact: ${[vitals.ecName, vitals.ecRel, vitals.ecPhone].filter(Boolean).join(' — ')}</li>`;
                html += '</ul>';
            }
            el.innerHTML = html || '<em style="color:#999;">No data yet. Chat or add info to build your profile.</em>';
        } catch (e) {
            el.innerHTML = '<em style="color:#999;">Sign in to see your health profile.</em>';
        }
    }

        let editHoldTimer = null;
        let lastTouchX = 0, lastTouchY = 0;
        let editScrollTop = 0;
        let activeEditEl = null;
        function editTestCell(el) {
            el.contentEditable = 'true';
            el.focus({preventScroll: true});
            activeEditEl = el;
            const range = document.caretRangeFromPoint ? document.caretRangeFromPoint(lastTouchX, lastTouchY) : null;
            if (range) {
                const sel = window.getSelection();
                if (sel) { sel.removeAllRanges(); sel.addRange(range); }
            }
            const outside = (e) => { if (activeEditEl && !activeEditEl.contains(e.target)) activeEditEl.blur(); };
            el._outsideListener = outside;
            document.addEventListener('touchstart', outside, {passive: true});
            el.addEventListener('blur', () => {
                document.removeEventListener('touchstart', outside);
                activeEditEl = null;
            }, {once: true});
            requestAnimationFrame(() => {
                const pc = document.getElementById('profile-screen-content');
                if (pc) pc.scrollTop = editScrollTop;
            });
        }
        function startEditHold(el, e) {
            if (editHoldTimer) clearTimeout(editHoldTimer);
            if (e && e.touches && e.touches[0]) { lastTouchX = e.touches[0].clientX; lastTouchY = e.touches[0].clientY; }
            const pc = document.getElementById('profile-screen-content');
            editScrollTop = pc ? pc.scrollTop : 0;
            editHoldTimer = setTimeout(() => {
                editHoldTimer = null;
                editTestCell(el);
            }, 1200);
        }
        function cancelEditHold() {
            if (editHoldTimer) {
                clearTimeout(editHoldTimer);
                editHoldTimer = null;
            }
        }

        async function saveTestResult(el) {
            const idx = parseInt(el.dataset.idx, 10);
            const field = el.dataset.field;
            if (isNaN(idx) || !field || !currentProfile || !currentProfile.test_results) return;
            const orig = currentProfile.test_results[idx];
            if (!orig) return;
            let raw = el.textContent.trim();
            if (field === 'date') {
                const nd = normalizeDateInput(raw);
                if (nd) { raw = nd; el.textContent = raw; }
            }
            let updates = { [field]: raw };
            if (field === 'value') {
                const unit = (el.dataset.unit || '').trim();
                const flagMatch = raw.match(/(?:^|\s)(H|L|High|Low)(?:\s|$)/i);
                const typedFlag = flagMatch ? flagMatch[1][0].toUpperCase() : '';
                const numMatch = raw.match(/-?\d+(?:\.\d+)?/);
                const num = numMatch ? parseFloat(numMatch[0]) : NaN;
                const numText = numMatch ? numMatch[0] : raw;
                const ref = orig.reference_range || '';
                let computedFlag = '';
                if (!isNaN(num) && ref) {
                    const [lower, upper] = parseReferenceRange(ref);
                    if (lower !== null && upper !== null) {
                        if (num > upper) computedFlag = 'H';
                        else if (num < lower) computedFlag = 'L';
                    }
                }
                const flag = computedFlag || typedFlag;
                const value = (numText + (flag ? ' ' + flag : '') + (unit ? ' ' + unit : '')).trim();
                updates = { value: value };
            }
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/item', {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ category: 'test_results', index: idx, updates: updates })
                });
                if (resp.ok) {
                    const pc = document.getElementById('profile-screen-content');
                    const y = pc ? pc.scrollTop : 0;
                    await loadHealthProfile();
                    if (pc) pc.scrollTop = y;
                } else {
                    const err = await resp.json().catch(() => ({}));
                    console.error('PWA saveTestResult failed', resp.status, err);
                }
            } catch (e) { console.error(e); }
        }

    document.getElementById('analyze-btn').addEventListener('click', async () => {
        const text = document.getElementById('profile-text').value.trim();
        const status = document.getElementById('profile-status');
        if (!text) { status.textContent = 'Enter some text first.'; return; }
        status.textContent = 'Analyzing...';
        try {
            const resp = await AuthHelper.authenticatedFetch('/api/health-profile/analyze', {
                method: 'POST',
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            if (resp.ok && data.success !== false && data.pending_review) {
                status.textContent = 'Review the extracted data before saving.';
                openReviewModal(data.pending_review);
            } else {
                status.textContent = data.error || 'Nothing to review or analysis failed.';
            }
        } catch (e) {
            status.textContent = 'Network error.';
        }
    });

    document.getElementById('upload-btn').addEventListener('click', async () => {
        const fileInput = document.getElementById('profile-file');
        const status = document.getElementById('profile-status');
        if (!fileInput.files || !fileInput.files.length) { status.textContent = 'Choose one or more files first.'; return; }
        const files = Array.from(fileInput.files);
        let ok = 0, failed = 0, lastError = '', lastPending = null, lastMeta = null;
        const retain = document.getElementById('retain-photo')?.checked ?? true;
        for (let i = 0; i < files.length; i++) {
            status.textContent = `Uploading & analyzing file ${i + 1} of ${files.length}...`;
            const formData = new FormData();
            formData.append('file', files[i]);
            formData.append('retain', String(retain));
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();
                if (resp.ok && data.success !== false && data.pending_review) {
                    ok++;
                    lastPending = data.pending_review;
                    lastMeta = {
                        source_file: data.source_file,
                        extracted_text: data.extracted_text,
                        extracted_text_preview: data.extracted_text_preview,
                        stored_document: data.stored_document
                    };
                } else {
                    failed++;
                    lastError = data.error || 'Upload failed.';
                }
            } catch (e) {
                failed++;
                lastError = 'Network error.';
            }
        }
        if (lastPending) {
            status.textContent = `✓ ${ok} file(s) ready for review.`;
            openReviewModal(lastPending, lastMeta);
            playNotificationSound();
        } else {
            status.textContent = (failed === 0 ? 'No structured data found.' : `Failed: ${lastError}`);
        }
        fileInput.value = '';
    });

    // ---------- Review & Data Manager ----------
    let currentPending = null;
    let currentMeta = {};
    let dmCurrentProfile = null;

    function playNotificationSound() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            const ctx = new AudioContext();
            if (ctx.state === 'suspended') ctx.resume();
            const osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.value = 1200;
            const gain = ctx.createGain();
            gain.gain.value = 0.15;
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.25);
        } catch (e) { console.error('sound', e); }
    }

    function escapeHtml(s) {
        return (s || '').toString().replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function closeReviewModal() {
        document.getElementById('review-modal').classList.remove('active');
        currentPending = null;
        currentMeta = {};
    }

    function openReviewModal(extracted, meta = {}) {
        currentPending = extracted;
        currentMeta = meta || {};
        const container = document.getElementById('review-content');
        container.innerHTML = '';

        // Show upload/source meta for verification before any extracted data
        if (currentMeta && (currentMeta.source_file || currentMeta.extracted_text)) {
            const metaSection = document.createElement('div');
            metaSection.className = 'review-section';
            const metaTitle = document.createElement('h4');
            metaTitle.textContent = 'Uploaded source';
            metaSection.appendChild(metaTitle);
            if (meta.source_file) {
                const fileP = document.createElement('p');
                fileP.style.fontSize = '0.85rem';
                fileP.textContent = 'File: ' + meta.source_file;
                metaSection.appendChild(fileP);
            }
            if (currentMeta.extracted_text) {
                const preview = document.createElement('div');
                preview.className = 'review-item-json';
                const ta = document.createElement('textarea');
                ta.id = 'review-raw-text';
                ta.rows = 6;
                ta.value = currentMeta.extracted_text;
                preview.appendChild(ta);
                metaSection.appendChild(preview);

                const reBtn = document.createElement('button');
                reBtn.className = 'btn-secondary';
                reBtn.textContent = 'Re-analyze edited text';
                reBtn.style.marginTop = '8px';
                reBtn.addEventListener('click', reanalyzeFromReview);
                metaSection.appendChild(reBtn);
            }
            container.appendChild(metaSection);
        }

        let hasData = !!(currentMeta && (currentMeta.source_file || currentMeta.extracted_text));

        for (const [key, val] of Object.entries(currentPending || {})) {
            if (val === null || val === undefined) continue;
            if (Array.isArray(val) && val.length === 0) continue;
            if (typeof val === 'object' && !Array.isArray(val) && Object.keys(val).length === 0) continue;
            hasData = true;

            const section = document.createElement('div');
            section.className = 'review-section';
            const title = document.createElement('h4');
            title.textContent = key.replace(/_/g, ' ');
            section.appendChild(title);

            if (Array.isArray(val)) {
                const list = document.createElement('div');
                let items = val;
                if (key === 'clinical_notes') {
                    items = val.map(item => (typeof item === 'string' ? { date: '', note: item } : item));
                }
                items.forEach((item, idx) => {
                    const row = document.createElement('div');
                    row.className = 'review-item';

                    const cb = document.createElement('input');
                    cb.type = 'checkbox';
                    cb.checked = true;
                    cb.dataset.category = key;
                    cb.dataset.index = idx;
                    row.appendChild(cb);

                    if (key === 'test_results') {
                        const fields = document.createElement('div');
                        fields.className = 'review-item-fields';
                        ['test_name', 'value', 'reference_range', 'date', 'notes'].forEach(field => {
                            const label = document.createElement('label');
                            label.textContent = field;
                            const input = document.createElement(field === 'notes' ? 'textarea' : 'input');
                            input.value = (item && item[field] !== undefined ? item[field] : '');
                            input.dataset.field = field;
                            fields.appendChild(label);
                            fields.appendChild(input);
                        });
                        row.appendChild(fields);
                    } else if (typeof item === 'object' && item !== null) {
                        const fields = document.createElement('div');
                        fields.className = 'review-item-fields';
                        Object.entries(item).forEach(([field, v]) => {
                            const label = document.createElement('label');
                            label.textContent = field;
                            const isLong = typeof v === 'string' && (v.length > 60 || /note|comment|text/i.test(field));
                            const input = document.createElement(isLong ? 'textarea' : 'input');
                            if (!isLong) input.type = 'text';
                            input.value = v !== undefined && v !== null ? String(v) : '';
                            input.dataset.field = field;
                            if (isLong) input.rows = 3;
                            fields.appendChild(label);
                            fields.appendChild(input);
                        });
                        row.appendChild(fields);
                    } else {
                        const wrap = document.createElement('div');
                        wrap.className = 'review-item-json';
                        const ta = document.createElement('textarea');
                        ta.rows = 3;
                        ta.value = String(item);
                        wrap.appendChild(ta);
                        row.appendChild(wrap);
                    }

                    list.appendChild(row);
                });
                section.appendChild(list);

                const addBtn = document.createElement('button');
                addBtn.className = 'btn-secondary';
                addBtn.style.marginTop = '8px';
                addBtn.innerHTML = `<i class="fas fa-plus"></i> Add ${key.replace(/_/g, ' ')} row`;
                addBtn.addEventListener('click', () => addReviewRow(list, key));
                section.appendChild(addBtn);
            } else if (typeof val === 'object') {
                const wrap = document.createElement('div');
                wrap.className = 'review-item-json';
                const cb = document.createElement('input');
                cb.type = 'checkbox';
                cb.checked = true;
                cb.dataset.category = key;
                cb.dataset.isObject = 'true';
                wrap.appendChild(cb);
                const fields = document.createElement('div');
                fields.className = 'review-item-fields';
                Object.entries(val).forEach(([field, v]) => {
                    const label = document.createElement('label');
                    label.textContent = field;
                    const isLong = typeof v === 'string' && (v.length > 60 || /note|comment|text/i.test(field));
                    const input = document.createElement(isLong ? 'textarea' : 'input');
                    if (!isLong) input.type = 'text';
                    input.value = v !== undefined && v !== null ? String(v) : '';
                    input.dataset.field = field;
                    if (isLong) input.rows = 3;
                    fields.appendChild(label);
                    fields.appendChild(input);
                });
                wrap.appendChild(fields);
                section.appendChild(wrap);
            } else {
                const wrap = document.createElement('label');
                wrap.innerHTML = `<input type="checkbox" checked data-category="${escapeHtml(key)}"> <span id="review-simple-${escapeHtml(key)}"></span>`;
                const span = wrap.querySelector('span');
                span.textContent = String(val);
                section.appendChild(wrap);
            }

            container.appendChild(section);
        }

        if (!hasData) container.innerHTML = '<p>No structured data was found.</p>';
        document.getElementById('review-modal').classList.add('active');
    }

    function addReviewRow(list, key) {
        const newRow = document.createElement('div');
        newRow.className = 'review-item';

        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.dataset.category = key;
        newRow.appendChild(cb);

        const fields = document.createElement('div');
        fields.className = 'review-item-fields';

        if (key === 'clinical_notes') {
            ['date', 'note'].forEach(field => {
                const label = document.createElement('label');
                label.textContent = field;
                const input = document.createElement(field === 'note' ? 'textarea' : 'input');
                if (field !== 'note') input.type = 'text';
                input.value = '';
                input.dataset.field = field;
                if (field === 'note') input.rows = 3;
                fields.appendChild(label);
                fields.appendChild(input);
            });
        } else {
            const source = list.querySelector('.review-item .review-item-fields');
            if (source) {
                source.querySelectorAll('input, textarea').forEach(src => {
                    const label = document.createElement('label');
                    label.textContent = src.dataset.field;
                    const input = document.createElement(src.tagName === 'TEXTAREA' ? 'textarea' : 'input');
                    if (src.tagName !== 'TEXTAREA') input.type = src.type || 'text';
                    input.value = '';
                    input.dataset.field = src.dataset.field;
                    if (src.rows) input.rows = src.rows;
                    fields.appendChild(label);
                    fields.appendChild(input);
                });
            }
        }

        newRow.appendChild(fields);
        list.appendChild(newRow);
    }

    function setReviewAll(checked) {
        document.querySelectorAll('#review-content input[type="checkbox"]').forEach(cb => cb.checked = checked);
    }

    async function saveReview() {
        const status = document.getElementById('review-status');
        const extracted = {};

        // Arrays
        const rows = Array.from(document.querySelectorAll('#review-content .review-item'));
        for (const row of rows) {
            const cb = row.querySelector('input[type="checkbox"]');
            if (!cb || !cb.checked) continue;
            const cat = cb.dataset.category;
            if (!Array.isArray(extracted[cat])) extracted[cat] = [];

            if (cat === 'test_results') {
                const item = {};
                row.querySelectorAll('.review-item-fields input, .review-item-fields textarea').forEach(el => {
                    item[el.dataset.field] = el.value;
                });
                extracted[cat].push(item);
            } else {
                const item = {};
                const fields = row.querySelector('.review-item-fields');
                if (fields) {
                    fields.querySelectorAll('input, textarea').forEach(el => {
                        item[el.dataset.field] = el.value;
                    });
                    extracted[cat].push(item);
                } else {
                    const ta = row.querySelector('textarea');
                    if (ta) {
                        const raw = ta.value.trim();
                        if ((raw.startsWith('{') && raw.endsWith('}')) || (raw.startsWith('[') && raw.endsWith(']'))) {
                            try {
                                extracted[cat].push(JSON.parse(raw));
                            } catch (e) {
                                status.textContent = `Invalid JSON in ${cat}`;
                                return;
                            }
                        } else {
                            extracted[cat].push(raw);
                        }
                    }
                }
            }
        }

        // Object categories
        document.querySelectorAll('#review-content .review-section .review-item-json').forEach(wrap => {
            const cb = wrap.querySelector('input[type="checkbox"]');
            if (!cb || !cb.checked || !cb.dataset.isObject) return;
            const cat = cb.dataset.category;
            const fields = wrap.querySelector('.review-item-fields');
            if (fields) {
                const item = {};
                fields.querySelectorAll('input, textarea').forEach(el => {
                    item[el.dataset.field] = el.value;
                });
                extracted[cat] = item;
            } else {
                const ta = wrap.querySelector('textarea');
                try {
                    extracted[cat] = JSON.parse(ta.value);
                } catch (e) {
                    status.textContent = `Invalid JSON in ${cat}`;
                    throw new Error('json-error');
                }
            }
        });

        // Simple values
        document.querySelectorAll('#review-content .review-section > label > input[type="checkbox"]').forEach(cb => {
            if (!cb.checked) return;
            const cat = cb.dataset.category;
            const span = document.getElementById('review-simple-' + cat);
            if (span) extracted[cat] = span.textContent;
        });

        status.textContent = 'Saving accepted items...';
        try {
            const resp = await AuthHelper.authenticatedFetch('/api/health-profile/apply-review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ extracted })
            });
            const data = await resp.json();
            if (resp.ok && data.success !== false) {
                status.textContent = 'Saved.';
                setTimeout(() => { closeReviewModal(); loadHealthProfile(); }, 600);
            } else {
                status.textContent = data.error || 'Save failed.';
            }
        } catch (e) {
            status.textContent = 'Network error.';
        }
    }

    async function reanalyzeFromReview() {
        const status = document.getElementById('review-status');
        const ta = document.getElementById('review-raw-text');
        if (!ta) { status.textContent = 'No raw text to re-analyze.'; return; }
        const text = ta.value.trim();
        if (!text) { status.textContent = 'Raw text is empty.'; return; }
        status.textContent = 'Re-analyzing edited text...';
        try {
            const resp = await AuthHelper.authenticatedFetch('/api/health-profile/analyze', {
                method: 'POST',
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            if (resp.ok && data.success !== false && data.pending_review) {
                status.textContent = 'Review the re-analyzed data before saving.';
                openReviewModal(data.pending_review, {
                    extracted_text: text,
                    source_file: currentMeta.source_file,
                    stored_document: currentMeta.stored_document
                });
            } else {
                status.textContent = data.error || 'Re-analysis failed.';
            }
        } catch (e) {
            status.textContent = 'Network error.';
        }
    }

    document.getElementById('review-close').addEventListener('click', closeReviewModal);
    document.getElementById('review-accept-all').addEventListener('click', () => setReviewAll(true));
    document.getElementById('review-reject-all').addEventListener('click', () => setReviewAll(false));
    document.getElementById('review-save').addEventListener('click', saveReview);

    // Data Manager
    function closeDataManager() {
        document.getElementById('data-manager-modal').classList.remove('active');
    }

    async function openDataManagerModal() {
        const modal = document.getElementById('data-manager-modal');
        modal.classList.add('active');
        const status = document.getElementById('dm-status');
        status.textContent = 'Loading...';
        try {
            const resp = await AuthHelper.authenticatedFetch('/api/health-profile');
            const data = await resp.json();
            if (!resp.ok || !data.profile) {
                status.textContent = data.error || 'Failed to load profile.';
                return;
            }
            dmCurrentProfile = data.profile;
            renderDataManager(data.profile);
            status.textContent = '';
            const dmSearch = document.getElementById('dm-search');
            if (dmSearch) {
                dmSearch.value = '';
                dmSearch.oninput = (e) => renderDataManager(dmCurrentProfile, e.target.value);
            }
        } catch (e) {
            status.textContent = 'Network error.';
        }
    }

    function formatFieldValue(key, val) {
        if (val === null || val === undefined) return '';
        if (Array.isArray(val)) return val.map(v => String(v)).join(', ');
        if (typeof val === 'object') return JSON.stringify(val, null, 2);
        return String(val);
    }

    function renderItemCard(item, cat) {
        const hidden = new Set(['added_at', 'updated_at', 'user_id', 'id']);
        const preferred = {
            conditions: ['name', 'status', 'diagnosed_date', 'details'],
            test_results: ['test_name', 'value', 'reference_range', 'date', 'notes'],
            medications: ['name', 'dosage', 'frequency', 'prescribed_date', 'notes'],
            supplements: ['name', 'dosage', 'frequency', 'notes'],
            symptoms: ['name', 'severity', 'onset_date', 'frequency', 'notes'],
            action_plans: ['action', 'target_date', 'status', 'notes'],
            conversation_insights: ['topic', 'insight', 'priority', 'notes']
        };
        const order = (preferred[cat] || []).filter(k => k in item && !hidden.has(k));
        const extra = Object.keys(item).filter(k => !hidden.has(k) && !order.includes(k));
        const keys = [...order, ...extra];
        const fields = keys.map(k => {
            const label = k.replace(/_/g, ' ');
            const value = formatFieldValue(k, item[k]);
            return `<div class="dm-field"><span class="dm-label">${escapeHtml(label)}</span><span class="dm-value" style="white-space:pre-wrap">${escapeHtml(value)}</span></div>`;
        }).join('');
        const meta = item.added_at ? `<div class="dm-meta">Added: ${escapeHtml(String(item.added_at))}</div>` : '';
        return `<div class="dm-card">${fields}${meta}</div>`;
    }

    function renderDataManager(profile, filter = '') {
        const content = document.getElementById('dm-content');
        const index = document.getElementById('dm-index');
        content.innerHTML = '';
        if (index) index.innerHTML = '';
        const categories = ['conditions', 'medications', 'supplements', 'symptoms', 'test_results', 'action_plans', 'conversation_insights'];
        let any = false;

        categories.forEach(cat => {
            const items = profile[cat] || [];
            if (!items.length) return;
            any = true;

            const section = document.createElement('div');
            section.className = 'dm-category';
            section.id = 'dm-cat-' + cat;
            section.innerHTML = `<h4>${cat.replace(/_/g,' ')} (${items.length})</h4>`;

            const addBtn = document.createElement('button');
            addBtn.className = 'btn-secondary';
            addBtn.style.marginBottom = '10px';
            addBtn.innerHTML = `<i class="fas fa-plus"></i> Add ${cat.replace(/_/g, ' ')}`;
            addBtn.addEventListener('click', () => addDataItem(cat, section));
            section.appendChild(addBtn);

            items.forEach((item, idx) => {
                if (filter && !JSON.stringify(item).toLowerCase().includes(filter.toLowerCase())) return;
                const div = document.createElement('div');
                div.className = 'dm-item';
                div.dataset.category = cat;
                div.dataset.index = idx;
                div.innerHTML = `${renderItemCard(item, cat)}
                    <div class="dm-actions">
                        <button class="btn-secondary dm-edit">Edit</button>
                        <button class="btn-danger dm-delete">Delete</button>
                    </div>`;
                section.appendChild(div);
            });

            content.appendChild(section);
        });

        if (any) {
            index.style.display = 'flex';
            index.innerHTML = categories
                .filter(cat => (profile[cat] || []).length)
                .map(cat => `<a class="dm-index-link" data-cat="${cat}">${cat.replace(/_/g,' ')}</a>`)
                .join('');
            const container = content.parentElement;
            index.querySelectorAll('.dm-index-link').forEach(a => {
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    const target = document.getElementById('dm-cat-' + a.dataset.cat);
                    if (target && container) {
                        const offset = index.offsetHeight + 16;
                        const targetPos = target.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop;
                        container.scrollTo({ top: targetPos - offset, behavior: 'smooth' });
                    }
                });
            });
        } else {
            index.style.display = 'none';
            index.innerHTML = '';
        }

        if (!any) content.innerHTML = '<p>No saved items to manage.</p>';

        content.querySelectorAll('.dm-edit').forEach(btn => {
            const div = btn.closest('.dm-item');
            const cat = div.dataset.category;
            const idx = parseInt(div.dataset.index, 10);
            const item = (profile[cat] || [])[idx];
            btn.addEventListener('click', () => editDataItem(div, item, cat, idx));
        });
        content.querySelectorAll('.dm-delete').forEach(btn => {
            btn.addEventListener('click', () => deleteDataItem(btn.closest('.dm-item')));
        });
    }

    function addDataItem(cat, container) {
        const defaults = {
            conditions: { name: '', status: 'active', diagnosed_date: '', details: '' },
            medications: { name: '', dose: '', frequency: '', prescribed_date: '', notes: '' },
            supplements: { name: '', dose: '', frequency: '', prescribed_date: '', notes: '' },
            symptoms: { description: '', severity: 'moderate', onset_date: '', frequency: '', notes: '' },
            test_results: { test_name: '', value: '', reference_range: '', date: '', notes: '' },
            action_plans: { title: '', steps: '', target_date: '', status: 'active', notes: '' },
            conversation_insights: { insight: '', category: 'general' }
        };
        const div = document.createElement('div');
        div.className = 'dm-item';
        container.appendChild(div);
        editDataItem(div, defaults[cat] || { name: '', value: '', date: '' }, cat, -1);
        div.scrollIntoView({ behavior: 'smooth', block: 'start' });
        const firstInput = div.querySelector('input, textarea');
        if (firstInput) firstInput.focus();
    }

    function editDataItem(div, item, cat, idx) {
        div.innerHTML = '';
        const form = document.createElement('div');
        form.className = 'dm-edit-form';
        const hidden = new Set(['added_at', 'updated_at', 'user_id', 'id']);
        const fields = Object.keys(item).filter(k => !hidden.has(k));
        const inputs = {};

        fields.forEach(k => {
            const label = document.createElement('label');
            label.className = 'dm-edit-label';
            label.textContent = k.replace(/_/g, ' ');
            const isLong = (k === 'details' || k === 'notes' || k === 'insight' || k === 'description') || String(item[k] || '').length > 60;
            const el = document.createElement(isLong ? 'textarea' : 'input');
            if (isLong) el.rows = 3;
            el.value = item[k] === null || item[k] === undefined ? '' : String(item[k]);
            if (el.tagName === 'INPUT' && (k === 'date' || k.endsWith('_date'))) el.type = 'date';
            el.dataset.key = k;
            if (cat === 'test_results' && k === 'reference_range') el.placeholder = 'Use Default';
            form.appendChild(label);
            form.appendChild(el);
            inputs[k] = el;
        });

        const actions = document.createElement('div');
        actions.className = 'dm-actions';
        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn-primary';
        saveBtn.textContent = 'Save';
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn-secondary';
        cancelBtn.textContent = 'Cancel';
        actions.appendChild(saveBtn);
        actions.appendChild(cancelBtn);
        form.appendChild(actions);

        div.appendChild(form);

        saveBtn.addEventListener('click', async () => {
            const status = document.getElementById('dm-status');
            if (cat === 'test_results') {
                const testName = (inputs['test_name']?.value || '').trim();
                const testValue = (inputs['value']?.value || '').trim();
                const refEl = inputs['reference_range'];
                let reference_range = (refEl?.value || '').trim();
                if (!reference_range && currentProfile && currentProfile.test_results) {
                    const key = normalizeTestType(testName).toLowerCase();
                    const existing = currentProfile.test_results.find(t => normalizeTestType(t.test_name).toLowerCase() === key && (t.reference_range || '').trim());
                    if (existing) reference_range = existing.reference_range.trim();
                }
                if (!reference_range) {
                    if (refEl) {
                        refEl.placeholder = 'Reference range';
                        refEl.focus();
                    }
                    status.textContent = 'Reference range is required when no default is available.';
                    return;
                }
                if (refEl) refEl.value = reference_range;
            }
            const updates = { ...item };
            Object.keys(inputs).forEach(k => updates[k] = inputs[k].value);
            status.textContent = 'Saving...';
            const isNew = idx === -1;
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/item', {
                    method: isNew ? 'POST' : 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: isNew
                        ? JSON.stringify({ category: cat, item: updates })
                        : JSON.stringify({ category: cat, index: idx, updates })
                });
                const data = await resp.json();
                if (resp.ok && data.success !== false) {
                    renderDataManager(data.profile);
                    status.textContent = 'Saved.';
                } else {
                    status.textContent = data.error || 'Save failed.';
                }
            } catch (e) { status.textContent = 'Network error.'; }
        });

        cancelBtn.addEventListener('click', () => openDataManagerModal());
    }

    async function deleteDataItem(div) {
        const cat = div.dataset.category;
        const idx = parseInt(div.dataset.index, 10);
        if (!confirm(`Delete this ${cat.replace(/_/g, ' ')} item?`)) return;
        const status = document.getElementById('dm-status');
        status.textContent = 'Deleting...';
        try {
            const resp = await AuthHelper.authenticatedFetch('/api/health-profile/item', {
                method: 'DELETE',
                body: JSON.stringify({ category: cat, index: idx })
            });
            const data = await resp.json();
            if (resp.ok && data.success !== false) {
                openDataManagerModal();
                status.textContent = 'Deleted.';
            } else {
                status.textContent = data.error || 'Delete failed.';
            }
        } catch (e) { status.textContent = 'Network error.'; }
    }

    document.getElementById('data-manager-btn').addEventListener('click', openDataManagerModal);
    document.getElementById('dm-close').addEventListener('click', closeDataManager);

    // ---------- Install prompt ----------
    function updateInstallPrompt() {
        const wrap = document.getElementById('install-wrap');
        if (!wrap) return;
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches || (window.navigator.standalone === true);
        if (isStandalone) {
            wrap.classList.remove('visible');
        } else {
            wrap.classList.add('visible');
        }
    }
    updateInstallPrompt();

    document.getElementById('install-pwa-btn').addEventListener('click', () => {
        const steps = document.getElementById('install-steps');
        steps.classList.toggle('show');
        const hint = document.getElementById('install-hint');
        hint.textContent = steps.classList.contains('show')
            ? 'Tap again to hide instructions'
            : 'Tap for install instructions';
    });

    // ---------- Vitals / Emergency (stored on this phone) ----------
    const VITALS_KEY = 'drHealth.vitals.v1';
    function loadVitals() {
        try { return JSON.parse(localStorage.getItem(VITALS_KEY) || '{}'); }
        catch (e) { return {}; }
    }
    function saveVitalsObject(v) { localStorage.setItem(VITALS_KEY, JSON.stringify(v)); }
    function getDefaultVitals() { return { name:'', age:'', blood:'', conditions:'', medications:'', allergies:'', history:'', doctors:'', ecName:'', ecRel:'', ecPhone:'' }; }
    function getVitals() { return { ...getDefaultVitals(), ...loadVitals() }; }

    async function syncVitalsFromServer() {
        try {
            const resp = await AuthHelper.authenticatedFetch('/api/health-profile/vitals');
            if (!resp.ok) throw new Error('Server not available');
            const data = await resp.json();
            if (data.success) {
                const local = loadVitals();
                const merged = { ...(data.vitals || {}), ...local };
                saveVitalsObject(merged);
                return merged;
            }
        } catch (e) { console.error('Could not sync vitals from server', e); }
        return getVitals();
    }

    function openEmergency() {
        renderEmergency();
        document.getElementById('emergency-modal').classList.add('active');
        syncVitalsFromServer().then(() => renderEmergency());
    }
    function closeEmergency() {
        document.getElementById('emergency-modal').classList.remove('active');
    }
    function editEmergency() {
        const v = getVitals();
        document.getElementById('emergency-view').style.display = 'none';
        document.getElementById('emergency-edit').style.display = 'block';
        document.getElementById('v-name').value = v.name || '';
        document.getElementById('v-age').value = v.age || '';
        document.getElementById('v-blood').value = v.blood || '';
        document.getElementById('v-conditions').value = v.conditions || '';
        document.getElementById('v-medications').value = v.medications || '';
        document.getElementById('v-allergies').value = v.allergies || '';
        document.getElementById('v-history').value = v.history || '';
        document.getElementById('v-doctors').value = v.doctors || '';
        document.getElementById('v-ec-name').value = v.ecName || '';
        document.getElementById('v-ec-rel').value = v.ecRel || '';
        document.getElementById('v-ec-phone').value = v.ecPhone || '';
    }
    async function saveVitals() {
        const v = {
            name: document.getElementById('v-name').value.trim(),
            age: document.getElementById('v-age').value.trim(),
            blood: document.getElementById('v-blood').value.trim(),
            conditions: document.getElementById('v-conditions').value.trim(),
            medications: document.getElementById('v-medications').value.trim(),
            allergies: document.getElementById('v-allergies').value.trim(),
            history: document.getElementById('v-history').value.trim(),
            doctors: document.getElementById('v-doctors').value.trim(),
            ecName: document.getElementById('v-ec-name').value.trim(),
            ecRel: document.getElementById('v-ec-rel').value.trim(),
            ecPhone: document.getElementById('v-ec-phone').value.trim(),
        };
        saveVitalsObject(v);
        document.getElementById('emergency-edit').style.display = 'none';
        document.getElementById('emergency-view').style.display = 'block';
        renderEmergency();
        try {
            await AuthHelper.authenticatedFetch('/api/health-profile/vitals', {
                method: 'PUT',
                body: JSON.stringify(v)
            });
        } catch (e) { console.error('Could not sync vitals to server', e); }
    }
    function renderEmergency() {
        const v = getVitals();
        const view = document.getElementById('emergency-view');
        const hasData = v.name || v.age || v.blood || v.conditions || v.medications || v.allergies || v.history || v.doctors || v.ecName || v.ecPhone;
        if (!hasData) {
            view.innerHTML = '<p class="emergency-empty">No emergency info saved yet. Add it below — it is stored only on this phone.</p>';
            document.getElementById('emergency-edit').style.display = 'block';
            document.getElementById('emergency-view').style.display = 'block';
            return;
        }
        let html = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">' +
            '<span class="emergency-empty">Stored only on this phone</span>' +
            '<button class="action" id="emergency-edit-btn" style="margin-top:0;padding:8px 14px;font-size:0.85rem;">Edit</button></div>';
        const section = (title, text) => text ? `<div class="emergency-section"><h3>${title}</h3><p>${text.replace(/\n/g,'<br>')}</p></div>` : '';
        const list = (title, text) => {
            if (!text) return '';
            const items = text.split(/[\n,]+/).map(s => s.trim()).filter(Boolean);
            if (!items.length) return '';
            return `<div class="emergency-section"><h3>${title}</h3><ul>${items.map(i => `<li>${i}</li>`).join('')}</ul></div>`;
        };
        html += section('Name', v.name);
        html += section('Age / Blood type', [v.age, v.blood].filter(Boolean).join(' / '));
        html += list('Medical conditions', v.conditions);
        html += list('Current medications', v.medications);
        html += list('Allergies', v.allergies);
        html += section('Medical history', v.history);
        html += section('Doctors', v.doctors);
        html += `<div class="emergency-section"><h3>Emergency contact</h3>`;
        html += v.ecName ? `<p class="big">${v.ecName}</p>` : '';
        html += v.ecRel ? `<p>${v.ecRel}</p>` : '';
        html += v.ecPhone ? `<p class="big">${v.ecPhone}</p>` : '';
        html += '</div>';
        view.innerHTML = html;
        document.getElementById('emergency-edit').style.display = 'none';
        document.getElementById('emergency-view').style.display = 'block';
        document.getElementById('emergency-edit-btn').addEventListener('click', editEmergency);
    }

    async function bootApp() {
        const creds = getStoredCredentials();
        if (creds && creds.username && creds.password) {
            if (typeof creds.username !== 'string' || typeof creds.password !== 'string') {
                clearStoredCredentials();
                return;
            }
            document.getElementById('login-username').value = creds.username;
            document.getElementById('login-password').value = creds.password;
            await doLogin(creds.username, creds.password);
            return;
        }
        if (AuthHelper.isAuthenticated()) {
            document.getElementById('login-screen').classList.add('hidden');
            initApp();
            return;
        }
        document.getElementById('login-screen').classList.remove('hidden');
    }

    // ---------- Boot ----------
    document.getElementById('emergency-btn').addEventListener('click', openEmergency);
    document.getElementById('emergency-close').addEventListener('click', closeEmergency);
    document.getElementById('v-save').addEventListener('click', saveVitals);
    bootApp();