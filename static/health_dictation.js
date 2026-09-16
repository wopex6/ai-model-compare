/*
 * Shared voice dictation: the single floating pill that dictates into
 * whichever text box last had focus.  Used by the Dr. Health PWA and the
 * health-profile website so neither drifts on language lists, spoken
 * punctuation, voice commands or the SpeechRecognition/MediaRecorder paths.
 */
(function () {
    'use strict';

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function isIOSDevice() {
        const ua = navigator.userAgent || '';
        const platform = navigator.platform || '';
        const maxTouch = navigator.maxTouchPoints || 0;
        return /iPad|iPhone|iPod/i.test(ua) || (platform === 'MacIntel' && maxTouch > 1);
    }

    function isHuaweiDevice() {
        return /huawei|honor/i.test(navigator.userAgent || '');
    }

    // Dictation works via SpeechRecognition where available, otherwise by
    // recording in-app and transcribing server-side — which also covers iOS
    // and Huawei, where SpeechRecognition is missing or unsafe to open.
    function dictationSupported() {
        if (window.SpeechRecognition || window.webkitSpeechRecognition) return true;
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
    }

    // Dictation languages for the diary mic.  `short` is the pill label —
    // shown the way iOS shows it on the keyboard bubble.
    const DIARY_LANG_KEY = 'drHealth.diaryLang';
    const DIARY_LANGS = [
        { value: 'en-GB', short: 'EN', label: 'English' },
        { value: 'yue-Hant-HK', short: '廣', label: 'Cantonese' },
        { value: 'cmn-Hans-CN', short: '普', label: 'Mandarin', alt: 'zh-CN' },
    ];
    function diaryLang() {
        try {
            const v = localStorage.getItem(DIARY_LANG_KEY);
            const found = DIARY_LANGS.find(l => l.value === v);
            if (found) return found;
        } catch (e) {}
        // No saved choice — follow the browser's language: zh-CN/Hans →
        // Mandarin, other zh (HK/TW/Hant) → Cantonese, else English.
        const nav = (navigator.language || '').toLowerCase();
        if (nav.indexOf('zh') === 0) {
            return /cn|hans/.test(nav) ? DIARY_LANGS[2] : DIARY_LANGS[1];
        }
        return DIARY_LANGS[0];
    }

    // ---------- Global dictation pill ----------
    // One floating pill dictates into whichever text box last had focus.  The
    // pill greys out when nothing editable is focused.
    let _dictateTarget = null;

    function editableEl(el) {
        if (!el || el.readOnly || el.disabled) return null;
        if (el.tagName === 'TEXTAREA') return el;
        if (el.tagName === 'INPUT' && /^(text|search|url|tel|email|password|number)?$/i.test(el.type || 'text')) return el;
        return null;
    }

    function updateDictatePill() {
        const pill = document.querySelector('.hf-dictate-pill');
        if (pill) pill.classList.toggle('inactive', !editableEl(_dictateTarget));
    }

    function installDictationTracker() {
        if (installDictationTracker._done) return;
        installDictationTracker._done = true;
        document.addEventListener('focusin', (e) => {
            const ed = editableEl(e.target);
            if (ed) { _dictateTarget = ed; updateDictatePill(); }
        }, true);
        document.addEventListener('focusout', () => {
            // Recompute from activeElement after the focus settles.  Focus
            // landing INSIDE the dictation pill keeps the previous target —
            // that is the mic/lang tap itself.  Focus landing anywhere else
            // non-editable deactivates the pill.
            setTimeout(() => {
                const ae = document.activeElement;
                const ed = editableEl(ae);
                if (ed) {
                    _dictateTarget = ed;
                } else if (!ae || !ae.closest || !ae.closest('.hf-dictate-pill')) {
                    _dictateTarget = null;
                }
                updateDictatePill();
            }, 0);
        }, true);
    }

    // Dictation feedback must work on every screen — the hub's status banner
    // is invisible outside the Health tab, so use a floating toast instead.
    let _dictateToastTimer = null;
    function dictateToast(text, isError) {
        if (!text) return;
        let t = document.getElementById('hf-dictate-toast');
        if (!t) {
            t = document.createElement('div');
            t.id = 'hf-dictate-toast';
            t.className = 'hf-dictate-toast';
            document.body.appendChild(t);
        }
        t.textContent = text;
        t.classList.toggle('error', !!isError);
        t.classList.add('show');
        clearTimeout(_dictateToastTimer);
        _dictateToastTimer = setTimeout(() => t.classList.remove('show'), 2800);
    }

    // Spoken punctuation commands.  Saying "comma" (or 逗號) turns the
    // auto-inserted sentence end into a comma; other marks work the same way.
    const PUNCT_EN = {
        'comma': ',', 'period': '.', 'full stop': '.', 'question mark': '?',
        'exclamation mark': '!', 'exclamation point': '!', 'semicolon': ';', 'colon': ':'
    };
    const PUNCT_ZH = {
        '逗號': '，', '逗号': '，', '句號': '。', '句号': '。', '句點': '。',
        '問號': '？', '问号': '？', '感嘆號': '！', '感叹号': '！'
    };
    const NL_WORDS = new Set(['new line', 'newline', '換行', '换行']);
    const PARA_WORDS = new Set(['new paragraph', '新段落', '換段落', '分段落']);
    // Whole-utterance commands (matched against the full trimmed segment, so
    // a word like "取消" inside a real sentence can't trigger them).
    const CMD_UNDO = new Set(['scratch that', 'undo', 'undo that', 'delete that',
        '刪除', '删掉', '刪掉', '撤回']);
    const CMD_STOP = new Set(['stop recording', 'stop dictation', 'stop listening',
        '停止錄音', '停止录音']);

    function isCJKLang(lang) {
        return /^(zh|yue|cmn)/i.test(lang || '');
    }

    // Normalize one recognised segment: trim stray spaces, convert spoken
    // punctuation words to real marks.  CJK gets no spaces at all.
    function transformDictation(raw, isCJK) {
        let s = (raw || '').trim();
        if (!s) return '';
        if (isCJK) {
            s = s.replace(/\s+/g, '');
            for (const w of Object.keys(PUNCT_ZH)) s = s.split(w).join(PUNCT_ZH[w]);
            for (const w of PARA_WORDS) s = s.split(w).join('\n\n');
            for (const w of NL_WORDS) s = s.split(w).join('\n');
            return s;
        }
        const parts = s.split(/\s+/);
        let out = '';
        for (let i = 0; i < parts.length; i++) {
            let key = parts[i].toLowerCase();
            const next = parts[i + 1];
            const two = next ? key + ' ' + next.toLowerCase() : '';
            if (two && (PUNCT_EN[two] !== undefined || NL_WORDS.has(two) || PARA_WORDS.has(two))) { key = two; i++; }
            if (NL_WORDS.has(key)) { out = out.replace(/\s+$/, '') + '\n'; continue; }
            if (PARA_WORDS.has(key)) { out = out.replace(/\s+$/, '') + '\n\n'; continue; }
            const p = PUNCT_EN[key];
            if (p !== undefined) { out = out.replace(/\s+$/, '') + p; continue; }
            if (out && !/\s$/.test(out)) out += ' ';
            out += parts[i];
        }
        return out;
    }

    function micHelpText() {
        const isIOS = isIOSDevice();
        const isAndroid = /Android/i.test(navigator.userAgent || '');
        const isStandalone = 'standalone' in navigator && navigator.standalone;
        if (isIOS) {
            if (isStandalone) return 'iPhone: a home-screen PWA cannot use the microphone. Use the iOS keyboard microphone icon to dictate into the Entry field, or open Dr. Health in Safari.';
            return 'iPhone: if Safari/Chrome does not appear in Settings → Privacy & Security → Microphone, use the iOS keyboard microphone icon to dictate into the Entry field.';
        }
        if (isAndroid) return 'Microphone access blocked. Android: Settings → Apps → (this browser/PWA) → Permissions → Microphone → Allow.';
        return 'Microphone access blocked. Please allow microphone access in your browser/PWA settings.';
    }

        // Wire the single global dictation pill: the mic dictates into
        // whichever editable field last had focus; the language chip opens a
        // menu.  Do NOT preventDefault on pointerdown/touchstart here — on
        // mobile that suppresses the click event and the tap does nothing.
        // Focus tracking in installDictationTracker already keeps the target
        // when focus moves into the pill.  Idempotent via _wired flags.
    function wire(rootEl) {
            if (!rootEl) return;
            installDictationTracker();
            rootEl.querySelectorAll('.hf-diary-mic').forEach(function (btn) {
                if (btn._wired) return;
                btn._wired = true;
                btn.addEventListener('click', function () {
                    recordInto(editableEl(_dictateTarget), this);
                });
            });
            rootEl.querySelectorAll('.hf-mic-lang').forEach(function (pill) {
                if (!pill._wired) pill.textContent = diaryLang().short;
                if (pill._wired) return;
                pill._wired = true;
                pill.addEventListener('click', function (e) {
                    e.stopPropagation();
                    e.preventDefault();
                    const menu = pill.parentElement.querySelector('.hf-lang-menu');
                    if (!menu) return;
                    if (menu.style.display === 'block') { menu.style.display = 'none'; return; }
                    const cur = diaryLang().value;
                    menu.innerHTML = DIARY_LANGS.map(l =>
                        '<button type="button" class="' + (l.value === cur ? 'sel' : '') +
                        '" data-dlang="' + esc(l.value) + '" data-dshort="' + esc(l.short) + '">' +
                        esc(l.short + '  ' + l.label) + '</button>').join('');
                    menu.style.display = 'block';
                    menu.querySelectorAll('[data-dlang]').forEach(function (opt) {
                        opt.addEventListener('click', function (ev) {
                            ev.stopPropagation();
                            const v = this.getAttribute('data-dlang');
                            try { localStorage.setItem(DIARY_LANG_KEY, v); } catch (e2) {}
                            // Language is a global preference — refresh every chip.
                            rootEl.querySelectorAll('.hf-mic-lang').forEach(function (p) {
                                p.textContent = opt.getAttribute('data-dshort');
                            });
                            menu.style.display = 'none';
                        });
                    });
                });
            });
            updateDictatePill();
    }

    async function recordInto(target, micBtn) {
            // The pill is hidden on iOS and Huawei/Honor — guard anyway.
            if (isIOSDevice()) {
                dictateToast(micHelpText(), true);
                return;
            }
            if (isHuaweiDevice()) {
                dictateToast('Voice dictation is not available on this device.', true);
                return;
            }
            if (!dictationSupported()) {
                dictateToast(micHelpText(), true);
                return;
            }
            // Second tap while recording = stop — checked before the target
            // check so it works even when nothing is focused mid-session.
            const active = micBtn && micBtn._session;
            if (active) {
                active.wantStop = true;
                try { if (active.rec) active.rec.stop(); } catch (e) {}
                try { if (active.mr && active.mr.state !== 'inactive') active.mr.stop(); } catch (e) {}
                return;
            }

            // Dictate into whichever text box last had focus.
            if (!target || !document.contains(target)) {
                dictateToast('Tap a text box first, then the mic.', true);
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            // iOS and Huawei never reach here (gated above).  On other
            // devices without SpeechRecognition (e.g. Firefox), fall back to
            // in-app recording + server transcription.
            const useUpload = !SpeechRecognition;

            if (useUpload) {
                _recordViaUpload(target, micBtn);
            } else {
                _recordViaSpeech(target, micBtn, SpeechRecognition);
            }
    }

    // ---------- Shared write-session (speech + upload paths) ----------
    // Both dictation engines feed final transcript segments through the same
    // pipeline: voice commands, punctuation transforms, auto sentence end,
    // cursor-follow and edit resync.
    function _newWriteSession() {
        return { wantStop: false, cur: null, pre: '', post: '', written: '',
            lastShown: '', isCJK: isCJKLang(diaryLang().value) };
    }
    function _writeGap(session) {
        return (session.pre && !/\s$/.test(session.pre) && !session.isCJK) ? ' ' : '';
    }
    function _dropInterim(session) {
        // Strip any not-yet-final text we displayed — keep only finals.
        if (session.cur && document.contains(session.cur)) {
            const w = session.written ? _writeGap(session) + session.written : '';
            session.cur.value = session.pre + w + session.post;
        }
    }
    function _syncTarget(session) {
        // Text follows the cursor: each segment goes to whichever editable
        // box is focused right now.
        const t = editableEl(_dictateTarget) || session.cur;
        if (!t) return null;
        if (t !== session.cur) {
            _dropInterim(session);
            session.cur = t;
            const pos = (typeof t.selectionStart === 'number') ? t.selectionStart : t.value.length;
            session.pre = t.value.slice(0, pos);
            session.post = t.value.slice(pos);
            session.written = '';
            session.lastShown = '';
        } else if (t.value !== session.pre + session.lastShown + session.post) {
            // The user edited the field (e.g. backspaced dictated words) —
            // resync the insertion point to the caret so deleted text does
            // not come back.
            const pos = (typeof t.selectionStart === 'number') ? t.selectionStart : t.value.length;
            session.pre = t.value.slice(0, pos);
            session.post = t.value.slice(pos);
            session.written = '';
            session.lastShown = '';
        }
        return t;
    }
    // Apply one final transcript segment to session.written.
    // Returns 'stop' when a stop command fired, else 'ok'.
    function _applyFinal(session, raw) {
        // Recognisers add their own capitalisation/punctuation ("Scratch
        // that.") — normalise before matching commands.  A command can also
        // share a segment with preceding speech ("take meds, stop
        // recording." as one Whisper chunk), so peel command phrases off the
        // end repeatedly; CJK commands need no space before them.
        const TAIL = /[.!?。，！？,;:；：\s]+$/;
        let text = (raw || '').replace(TAIL, '');
        const actions = [];
        for (;;) {
            const n = text.toLowerCase().replace(/\s+/g, ' ').replace(TAIL, '');
            let found = null, type = null;
            for (const c of CMD_UNDO) {
                if (n === c || n.endsWith(' ' + c) ||
                    (/[㐀-鿿豈-﫿]/.test(c[0]) && n.endsWith(c))) { found = c; type = 'undo'; break; }
            }
            if (!found) for (const c of CMD_STOP) {
                if (n === c || n.endsWith(' ' + c) ||
                    (/[㐀-鿿豈-﫿]/.test(c[0]) && n.endsWith(c))) { found = c; type = 'stop'; break; }
            }
            if (!found) break;
            actions.unshift(type);
            text = (n === found) ? '' : text.slice(0, text.length - found.length).replace(TAIL, '');
        }
        if (text) {
            let seg = transformDictation(text, session.isCJK);
            if (seg) {
        if (/^[,;:.!?，。！？；：]/.test(seg)) {
            // A leading spoken mark replaces the auto period.
            session.written = session.written.replace(/[,;:.!?，。！？；：\s]+$/, '');
            if (session.written) session.written += seg;
            else session.written = seg.replace(/^[,;:.!?，。！？；：]+\s*/, '');
        } else {
            if (session.written && !session.isCJK && !/\s$/.test(session.written)) session.written += ' ';
            if (!session.isCJK && /[.!?]\s*$/.test(session.written) && /^[a-z]/.test(seg)) {
                seg = seg[0].toUpperCase() + seg.slice(1);
            }
            session.written += seg;
        }
        // Auto sentence end — skipped when the speaker already supplied
        // punctuation or a line break.
        if (!/[,;:.!?，。！？；：\n]\s*$/.test(session.written)) {
            session.written += session.isCJK ? '。' : '.';
        }
            }
        }
        for (const a of actions) {
            if (a === 'undo') {
                // Remove the last dictated sentence, punctuation included.
                session.written = session.written.replace(/\s*[^.!?。！？\n]*[.!?。！？]?\s*$/, '');
            } else {
                session.wantStop = true;
            }
        }
        return session.wantStop ? 'stop' : 'ok';
    }
    function _render(session, interim) {
        const t = session.cur;
        if (!t) return;
        const interimTxt = (interim || '').trim();
        const shown = session.written +
            (session.written && interimTxt ? (session.isCJK ? '' : ' ') : '') + interimTxt;
        const shownTxt = (shown ? _writeGap(session) : '') + shown;
        t.value = session.pre + shownTxt + session.post;
        session.lastShown = shownTxt;
        const caret = (session.pre + shownTxt).length;
        try { t.selectionStart = t.selectionEnd = caret; } catch (err) {}
    }

    function _recordViaSpeech(target, micBtn, SpeechRecognition) {
            const session = _newWriteSession();
            session.rec = null; session.restarts = 0; session.next = 0;
            session.langTag = diaryLang().value; session.triedAlt = false;
            session.startedAt = 0; session.gotResult = false; session.fastFails = 0;
            if (micBtn) micBtn._session = session;
            const finish = (msg, isErr) => {
                _dropInterim(session);
                if (micBtn) { micBtn.classList.remove('recording'); micBtn._session = null; }
                if (msg) dictateToast(msg, !!isErr);
            };
            // SpeechRecognition needs to reach the browser vendor's speech
            // service (Google on Chrome).  Where that is unreachable, fall
            // back to in-app recording + server transcription instead of
            // dying in a restart loop.
            const fallback = (msg) => {
                session.wantStop = true;
                _dropInterim(session);
                if (micBtn) { micBtn.classList.remove('recording'); micBtn._session = null; }
                dictateToast(msg || 'Browser speech unavailable — using the recorder instead.');
                _recordViaUpload(target, micBtn);
            };
            const start = () => {
                // Chrome on Android ends the session on a pause even with
                // continuous=true, so restart transparently until the user
                // taps the mic again.  Results reset per instance, so the
                // result pointer resets too; written text already in the
                // field is preserved via session.pre/written.
                session.next = 0;
                session.startedAt = Date.now();
                const rec = new SpeechRecognition();
                session.rec = rec;
                rec.lang = session.langTag;
                rec.continuous = true;
                rec.interimResults = true;
                rec.onstart = () => {
                    dictateToast('Listening… tap the mic again to stop.');
                    if (micBtn) micBtn.classList.add('recording');
                };
                rec.onresult = (e) => {
                    session.restarts = 0;
                    session.gotResult = true;
                    if (!_syncTarget(session)) return;
                    let interim = '';
                    for (let i = session.next; i < e.results.length; i++) {
                        const r = e.results[i];
                        if (!r.isFinal) { interim += r[0].transcript; continue; }
                        session.next = i + 1;
                        if (_applyFinal(session, r[0].transcript) === 'stop') {
                            try { rec.stop(); } catch (e2) {}
                        }
                    }
                    _render(session, interim);
                };
                rec.onerror = (e) => {
                    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
                        session.wantStop = true;
                        finish(micHelpText(), true);
                    } else if (e.error === 'language-not-supported') {
                        const alt = diaryLang().alt;
                        if (alt && !session.triedAlt) {
                            // e.g. Mandarin: cmn-Hans-CN is the spec tag but
                            // some Chrome builds only accept zh-CN.
                            session.triedAlt = true;
                            session.langTag = alt;
                            return; // onend restarts with the fallback tag
                        }
                        session.wantStop = true;
                        finish('This language is not supported by your browser. Try English.', true);
                    } else if (e.error === 'network') {
                        // The vendor speech service is unreachable (blocked
                        // network, extension, or region) — no point retrying.
                        session.wantStop = true;
                        fallback();
                    }
                    // 'no-speech', 'aborted' — onend handles restart.
                };
                rec.onend = () => {
                    session.rec = null;
                    if (session.wantStop) {
                        if (micBtn && !micBtn._session) return; // fallback took over
                        finish('Voice recorded.');
                        return;
                    }
                    // Sessions dying within ~2s with zero results = the
                    // service itself is broken — switch engines.
                    if (Date.now() - session.startedAt < 2000 && !session.gotResult) session.fastFails++;
                    else session.fastFails = 0;
                    if (session.fastFails >= 3) { fallback(); return; }
                    if (session.restarts >= 10) {
                        finish('Voice input stopped (too many silences). Tap the mic to start again.', true);
                        return;
                    }
                    session.restarts++;
                    start();
                };
                try { rec.start(); } catch (e) {
                    session.wantStop = true;
                    finish('Could not start voice input: ' + e.message, true);
                }
            };
            start();
    }

        // Rolling-segment recorder: restarts MediaRecorder every SEG_MS so
        // each upload is a complete file — transcribed text appears while the
        // user is still speaking.  Each recorder produces its own header, so
        // segments are independently valid.
    async function _recordViaUpload(target, micBtn) {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
                dictateToast('Voice recording is not supported in this browser.', true);
                return;
            }
            let stream;
            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    audio: { echoCancellation: true, noiseSuppression: true }
                });
            } catch (e) {
                dictateToast('Microphone access was denied. Allow it for this site in the browser settings.', true);
                return;
            }
            const mime = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm'
                : (MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : '');
            const SEG_MS = 4000;
            const session = _newWriteSession();
            session.mr = null; session.segStart = 0;
            session.timer = null; session.queue = Promise.resolve();
            if (micBtn) micBtn._session = session;

            const newRecorder = () => {
                const chunks = [];
                let r;
                try {
                    r = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
                } catch (e) { return null; }
                r.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
                r.onstop = () => {
                    clearTimeout(session.timer);
                    const blob = new Blob(chunks, { type: r.mimeType || 'audio/webm' });
                    const dur = Date.now() - session.segStart;
                    session.queue = session.queue.then(() => _uploadChunk(blob, dur, session));
                    if (!session.wantStop) {
                        session.segStart = Date.now();
                        session.mr = newRecorder();
                        if (session.mr) {
                            try { session.mr.start(1000); } catch (e) {}
                            session.timer = setTimeout(() => {
                                if (session.mr && session.mr.state === 'recording') session.mr.stop();
                            }, SEG_MS);
                        }
                    } else {
                        stream.getTracks().forEach(t => t.stop());
                        if (micBtn) { micBtn.classList.remove('recording'); micBtn._session = null; }
                    }
                };
                return r;
            };

            session.segStart = Date.now();
            session.mr = newRecorder();
            if (!session.mr) {
                stream.getTracks().forEach(t => t.stop());
                dictateToast('Could not start recording.', true);
                return;
            }
            try {
                session.mr.start(1000);
            } catch (e) {
                stream.getTracks().forEach(t => t.stop());
                dictateToast('Could not start recording: ' + e.message, true);
                return;
            }
            session.timer = setTimeout(() => {
                if (session.mr && session.mr.state === 'recording') session.mr.stop();
            }, SEG_MS);
            if (micBtn) micBtn.classList.add('recording');
            dictateToast('Recording… tap the mic again to stop.');
    }

    async function _uploadChunk(blob, durMs, session) {
            // Near-empty clips make the transcriber hallucinate stock phrases.
            if (!blob || blob.size < 2000 || durMs < 600) return;
            // Segments spoken after a voice "stop recording" are dropped —
            // a manual stop still lets the final in-flight chunk through.
            if (session.stoppedByCmd) return;
            try {
                const fd = new FormData();
                const ext = (blob.type || '').includes('mp4') ? 'm4a' : 'webm';
                fd.append('audio', blob, 'diary.' + ext);
                fd.append('lang', diaryLang().value);
                const res = await AuthHelper.authenticatedFetch('/api/health-profile/transcribe', {
                    method: 'POST', body: fd
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.success && data.text) {
                    // Same pipeline as SpeechRecognition: commands, spoken
                    // punctuation, auto sentence end, cursor-follow.
                    if (!_syncTarget(session)) return;
                    if (_applyFinal(session, data.text) === 'stop') {
                        session.stoppedByCmd = true;
                        if (session.mr && session.mr.state !== 'inactive') {
                            try { session.mr.stop(); } catch (e) {}
                        }
                    }
                    _render(session);
                } else if (!res.ok || !data.success) {
                    dictateToast('Transcription failed' + (data.error ? ': ' + data.error : '.'), true);
                }
            } catch (e) {
                dictateToast('Transcription failed: ' + e.message, true);
            }
    }

    // The pill is offered only where a dictation path can actually work.
    function pillAvailable() {
        return !(isIOSDevice() || isHuaweiDevice()) && dictationSupported();
    }

    window.HealthDictation = {
        wire: wire,
        pillAvailable: pillAvailable,
        isIOSDevice: isIOSDevice,
        isHuaweiDevice: isHuaweiDevice,
        dictationSupported: dictationSupported,
        diaryLang: diaryLang,
        micHelpText: micHelpText,
        toast: dictateToast,
    };
})();
