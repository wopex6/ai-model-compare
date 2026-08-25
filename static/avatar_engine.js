/**
 * AvatarEngine — Animated SVG character system
 * Supports: girl, boy, woman, man, man_ancient
 * Features: mouth visemes, facial expressions, eye blink, speech bubble, TTS sound, mute
 *
 * Public API (per AvatarController):
 *   speak(text)        — animate + TTS + bubble
 *   stopSpeaking()     — stop animation + TTS
 *   setExpression(e)   — set facial expression
 *   setType(t)         — change avatar type
 *   applyCharacter(id, gender) — map character ID → type
 *   setMuted(bool)     — mute/unmute TTS
 *   show() / hide()
 *   destroy()
 *
 * Static helpers:
 *   AvatarEngine.buildPanelHTML(id)
 *   AvatarEngine.createPanel(el)
 *   AvatarEngine.CHARACTER_MAP, PALETTES, detectExpression
 *   AvatarEngine.isMuted() / AvatarEngine.setGlobalMute(bool)
 */

const AvatarEngine = (() => {

    // ─── Global mute state ────────────────────────────────────────────────────────
    let _globalMuted = (() => {
        try { return localStorage.getItem('avatarMuted') === 'true'; } catch { return false; }
    })();

    // ─── Character → avatar type mapping ───────────────────────────────────────
    const CHARACTER_MAP = {
        // AI Characters (chatchat)
        super_motivational_coach: 'man',
        wisdom_sage:              'man',
        stoic_philosopher:        'man_ancient',
        psychologist:             'woman',
        zen_master:               'man',
        business_coach:           'man',
        life_coach:               'man',
        scientist:                'woman',
        medical_advisor:           'man',
        coordinator:              'girl',
        // Domain characters (life companion)
        work:                     'man',
        relationships:            'woman',
        mental_health:            'woman',
        physical_health:          'boy',
        finance:                  'man',
        learning:                 'girl',
        creativity:               'girl',
    };

    const CHARACTER_NAMES = {
        super_motivational_coach: 'Coach Max',
        wisdom_sage:              'Sage Wei',
        stoic_philosopher:        'Marcus',
        psychologist:             'Dr. Elena',
        zen_master:               'Master Kai',
        business_coach:           'Coach Ryan',
        life_coach:               'Coach Jordan',
        scientist:                'Dr. Nova',
        medical_advisor:           'Dr. Health',
        coordinator:              'Aria',
        work:                     'Alex',
        relationships:            'Luna',
        mental_health:            'Sage',
        physical_health:          'Finn',
        finance:                  'Marcus',
        learning:                 'Nova',
        creativity:               'Muse',
    };

    // ─── Colour palettes per type ───────────────────────────────────────────────
    const PALETTES = {
        girl: {
            skin: '#FDDBB4', skinDark: '#F0C090',
            hair: '#7B3F00', hairHL: '#A0522D',
            eye: '#5C4033', pupil: '#1A0A00',
            lip: '#E07070', blush: '#F4A0A0',
            shirt: '#E879A0', shirtDark: '#C45A82',
            accessory: '#FFD700',
            label: 'Aria',
        },
        boy: {
            skin: '#FDDBB4', skinDark: '#F0C090',
            hair: '#3B2A1A', hairHL: '#6B4226',
            eye: '#3B5A8A', pupil: '#0A1A2A',
            lip: '#C07060', blush: '#F4A0A0',
            shirt: '#4A90D9', shirtDark: '#2E6BAE',
            accessory: '#888',
            label: 'Leo',
        },
        woman: {
            skin: '#F5C9A0', skinDark: '#E0A870',
            hair: '#2C1A0E', hairHL: '#5C3A1E',
            eye: '#3A6040', pupil: '#0A1A0A',
            lip: '#C05050', blush: '#ECA090',
            shirt: '#7B68EE', shirtDark: '#5A4EC8',
            accessory: '#FFD700',
            label: 'Dr. Elena',
        },
        man: {
            skin: '#F0C090', skinDark: '#D8A060',
            hair: '#1A1A2A', hairHL: '#3A3A4A',
            eye: '#3A4A2A', pupil: '#0A0A0A',
            lip: '#B06050', blush: 'none',
            shirt: '#2C5282', shirtDark: '#1A3A5C',
            accessory: '#888',
            label: 'Coach',
        },
        man_ancient: {
            skin: '#D4A870', skinDark: '#B88050',
            hair: '#C0B090', hairHL: '#E0D0B0',
            eye: '#4A3020', pupil: '#0A0A0A',
            lip: '#A06050', blush: 'none',
            shirt: '#6B4C2A', shirtDark: '#4A3010',
            accessory: '#C8A800',
            label: 'Marcus',
        },
    };

    // ─── Mouth viseme paths (relative to mouth centre) ─────────────────────────
    // Each is an SVG path `d` attribute drawn around (0,0)
    const VISEMES = {
        rest:   'M -10 0 Q 0 4 10 0',                       // slight smile
        open:   'M -10 -3 Q 0 10 10 -3 Q 0 -3 -10 -3 Z',   // open oval
        wide:   'M -12 -2 Q 0 12 12 -2 Q 0 -5 -12 -2 Z',   // wide open
        round:  'M -7 0 Q -7 8 0 8 Q 7 8 7 0 Q 7 -4 0 -4 Q -7 -4 -7 0 Z', // round O
        narrow: 'M -5 0 Q 0 6 5 0 Q 0 -2 -5 0 Z',          // small open
        closed: 'M -10 0 Q 0 2 10 0',                       // closed
        smile:  'M -10 -2 Q 0 8 10 -2',                     // happy smile
        frown:  'M -10 2 Q 0 -6 10 2',                      // sad
    };

    // ─── Expression → face-part overrides ──────────────────────────────────────
    const EXPRESSIONS = {
        neutral:     { brow: 0, eyeScale: 1,    mouthViseme: 'rest',   blushAlpha: 0.3 },
        happy:       { brow: -3, eyeScale: 0.9, mouthViseme: 'smile',  blushAlpha: 0.7 },
        thinking:    { brow: -5, eyeScale: 1.1, mouthViseme: 'closed', blushAlpha: 0.1, lookDir: 1 },
        surprised:   { brow: -8, eyeScale: 1.3, mouthViseme: 'open',   blushAlpha: 0.5 },
        encouraging: { brow: -4, eyeScale: 0.9, mouthViseme: 'smile',  blushAlpha: 0.6 },
        sad:         { brow: 4,  eyeScale: 0.95,mouthViseme: 'frown',  blushAlpha: 0.2 },
    };

    // ─── Sentiment → expression mapping ────────────────────────────────────────
    function detectExpression(text) {
        if (!text) return 'neutral';
        const t = text.toLowerCase();
        if (/\b(great|amazing|wonderful|congrat|excellent|awesome|fantastic|yay|well done)\b/.test(t)) return 'happy';
        if (/\b(sorry|sad|difficult|hard|struggle|pain|lonely|lost|miss|griev)\b/.test(t)) return 'sad';
        if (/\b(wow|incredible|surprising|really\?|unbeliev|shocking)\b/.test(t)) return 'surprised';
        if (/\b(you can|believe in|keep going|proud|you've got|let's go|try again|don't give up)\b/.test(t)) return 'encouraging';
        if (/\b(hmm|let me think|consider|analyz|reflect|wonder|perhaps|ponder)\b/.test(t)) return 'thinking';
        return 'neutral';
    }

    // ─── SVG builder ────────────────────────────────────────────────────────────
    function buildSVG(type, expression, mouthViseme, blinkPhase) {
        const p = PALETTES[type] || PALETTES.girl;
        const expr = EXPRESSIONS[expression] || EXPRESSIONS.neutral;
        const viseme = VISEMES[mouthViseme || expr.mouthViseme] || VISEMES.rest;
        const blink = blinkPhase; // 0=open, 1=closed
        const lookX = (expr.lookDir || 0) * 3;

        // head centre (100,105), face radius ~55
        const cx = 100, cy = 105, r = 55;
        // eye positions
        const lEx = cx - 20, lEy = cy - 8;
        const rEx = cx + 20, rEy = cy - 8;
        // mouth centre
        const mx = cx, my = cy + 22;
        // brow y offset
        const browY = expr.brow;
        // eye height (blink)
        const eyeH = blink ? 1 : 10 * expr.eyeScale;
        const eyeW = 13;

        // Build hair shape based on type
        let hairPath = '';
        let accessories = '';
        if (type === 'girl') {
            hairPath = `
                <ellipse cx="${cx}" cy="${cy - 45}" rx="58" ry="28" fill="${p.hair}"/>
                <path d="M ${cx-55} ${cy-20} Q ${cx-70} ${cy+30} ${cx-60} ${cy+70}" stroke="${p.hair}" stroke-width="22" fill="none" stroke-linecap="round"/>
                <path d="M ${cx+55} ${cy-20} Q ${cx+70} ${cy+30} ${cx+60} ${cy+70}" stroke="${p.hair}" stroke-width="22" fill="none" stroke-linecap="round"/>
                <ellipse cx="${cx}" cy="${cy - 52}" rx="42" ry="20" fill="${p.hairHL}"/>
            `;
            accessories = `<circle cx="${cx-38}" cy="${cy-60}" r="6" fill="${p.accessory}"/>`;
        } else if (type === 'boy') {
            hairPath = `
                <ellipse cx="${cx}" cy="${cy - 48}" rx="55" ry="24" fill="${p.hair}"/>
                <rect x="${cx-50}" y="${cy-70}" width="100" height="30" rx="10" fill="${p.hair}"/>
                <path d="M ${cx-45} ${cy-55} Q ${cx-20} ${cy-75} ${cx+20} ${cy-75} Q ${cx+45} ${cy-60} ${cx+40} ${cy-50}" fill="${p.hairHL}"/>
            `;
        } else if (type === 'woman') {
            hairPath = `
                <ellipse cx="${cx}" cy="${cy - 45}" rx="58" ry="26" fill="${p.hair}"/>
                <path d="M ${cx-55} ${cy-20} Q ${cx-65} ${cy+40} ${cx-50} ${cy+80}" stroke="${p.hair}" stroke-width="18" fill="none" stroke-linecap="round"/>
                <path d="M ${cx+55} ${cy-20} Q ${cx+65} ${cy+40} ${cx+50} ${cy+80}" stroke="${p.hair}" stroke-width="18" fill="none" stroke-linecap="round"/>
                <ellipse cx="${cx}" cy="${cy - 50}" rx="40" ry="16" fill="${p.hairHL}" opacity="0.5"/>
            `;
            accessories = `<ellipse cx="${cx-42}" cy="${cy-10}" rx="5" ry="8" fill="${p.accessory}" opacity="0.9"/>
                           <ellipse cx="${cx+42}" cy="${cy-10}" rx="5" ry="8" fill="${p.accessory}" opacity="0.9"/>`;
        } else if (type === 'man') {
            hairPath = `
                <ellipse cx="${cx}" cy="${cy - 50}" rx="54" ry="20" fill="${p.hair}"/>
                <rect x="${cx-50}" y="${cy-68}" width="100" height="22" rx="8" fill="${p.hair}"/>
            `;
        } else if (type === 'man_ancient') {
            // White/grey hair + beard
            hairPath = `
                <ellipse cx="${cx}" cy="${cy - 48}" rx="54" ry="22" fill="${p.hair}"/>
                <path d="M ${cx-35} ${cy+28} Q ${cx-40} ${cy+55} ${cx-20} ${cy+75} Q ${cx} ${cy+85} ${cx+20} ${cy+75} Q ${cx+40} ${cy+55} ${cx+35} ${cy+28}" fill="${p.hair}" opacity="0.9"/>
                <path d="M ${cx-25} ${cy+28} Q ${cx-28} ${cy+55} ${cx} ${cy+70} Q ${cx+28} ${cy+55} ${cx+25} ${cy+28}" fill="${p.hairHL}" opacity="0.6"/>
            `;
        }

        // Shirt / body shape
        const shirtY = cy + r - 5;
        const bodyPath = `<path d="M ${cx-70} 210 Q ${cx-60} ${shirtY+5} ${cx} ${shirtY} Q ${cx+60} ${shirtY+5} ${cx+70} 210 L ${cx+80} 240 L ${cx-80} 240 Z" fill="${p.shirt}"/>
                          <path d="M ${cx-10} ${shirtY} L ${cx-15} 240 M ${cx+10} ${shirtY} L ${cx+15} 240" stroke="${p.shirtDark}" stroke-width="2" opacity="0.4"/>`;

        // Neck
        const neckPath = `<rect x="${cx-12}" y="${cy+r-8}" width="24" height="20" rx="8" fill="${p.skin}"/>`;

        // Blush
        const blushA = p.blush === 'none' ? 0 : (expr.blushAlpha || 0.3);
        const blushEls = p.blush !== 'none' ? `
            <ellipse cx="${lEx-8}" cy="${lEy+14}" rx="14" ry="8" fill="${p.blush}" opacity="${blushA}"/>
            <ellipse cx="${rEx+8}" cy="${rEy+14}" rx="14" ry="8" fill="${p.blush}" opacity="${blushA}"/>
        ` : '';

        // Eyebrows
        const browLift = browY;
        const browsPath = `
            <path d="M ${lEx-11} ${lEy - 14 + browLift} Q ${lEx} ${lEy - 19 + browLift} ${lEx+11} ${lEy - 14 + browLift}" 
                  stroke="${p.hair}" stroke-width="3" fill="none" stroke-linecap="round"/>
            <path d="M ${rEx-11} ${rEy - 14 + browLift} Q ${rEx} ${rEy - 19 + browLift} ${rEx+11} ${rEy - 14 + browLift}" 
                  stroke="${p.hair}" stroke-width="3" fill="none" stroke-linecap="round"/>
        `;

        // Eyes
        const eyesPath = `
            <ellipse cx="${lEx}" cy="${lEy}" rx="${eyeW/2}" ry="${eyeH/2}" fill="white"/>
            <ellipse cx="${lEx + lookX}" cy="${lEy}" rx="${eyeH > 3 ? 5 : 0}" ry="${eyeH > 3 ? 5 : 0}" fill="${p.eye}"/>
            <ellipse cx="${lEx + lookX}" cy="${lEy}" rx="${eyeH > 3 ? 2.5 : 0}" ry="${eyeH > 3 ? 2.5 : 0}" fill="${p.pupil}"/>
            ${eyeH > 3 ? `<ellipse cx="${lEx + lookX - 1.5}" cy="${lEy - 1.5}" rx="1.5" ry="1.5" fill="white" opacity="0.8"/>` : ''}
            
            <ellipse cx="${rEx}" cy="${rEy}" rx="${eyeW/2}" ry="${eyeH/2}" fill="white"/>
            <ellipse cx="${rEx + lookX}" cy="${rEy}" rx="${eyeH > 3 ? 5 : 0}" ry="${eyeH > 3 ? 5 : 0}" fill="${p.eye}"/>
            <ellipse cx="${rEx + lookX}" cy="${rEy}" rx="${eyeH > 3 ? 2.5 : 0}" ry="${eyeH > 3 ? 2.5 : 0}" fill="${p.pupil}"/>
            ${eyeH > 3 ? `<ellipse cx="${rEx + lookX - 1.5}" cy="${rEy - 1.5}" rx="1.5" ry="1.5" fill="white" opacity="0.8"/>` : ''}
            
            <!-- eyelid lines -->
            <path d="M ${lEx - eyeW/2} ${lEy} Q ${lEx} ${lEy - eyeH/2 - 1} ${lEx + eyeW/2} ${lEy}" 
                  stroke="${p.skinDark}" stroke-width="1.5" fill="none"/>
            <path d="M ${rEx - eyeW/2} ${rEy} Q ${rEx} ${rEy - eyeH/2 - 1} ${rEx + eyeW/2} ${rEy}" 
                  stroke="${p.skinDark}" stroke-width="1.5" fill="none"/>
        `;

        // Nose
        const nosePath = `<path d="M ${cx-5} ${cy+8} Q ${cx-8} ${cy+16} ${cx-5} ${cy+18} Q ${cx} ${cy+20} ${cx+5} ${cy+18} Q ${cx+8} ${cy+16} ${cx+5} ${cy+8}" 
                                stroke="${p.skinDark}" stroke-width="1.5" fill="none" opacity="0.5"/>`;

        // Mouth (translate viseme path to mouth centre)
        const mouthPath = `<g transform="translate(${mx},${my})">
            <path d="${viseme}" stroke="${p.lip}" stroke-width="2.5" fill="${mouthViseme === 'open' || mouthViseme === 'wide' || mouthViseme === 'round' ? '#5A1A1A' : 'none'}" stroke-linecap="round"/>
            ${mouthViseme === 'open' || mouthViseme === 'wide' ? `<path d="M -6 2 L 6 2" stroke="white" stroke-width="3" opacity="0.7"/>` : ''}
        </g>`;

        return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240" width="160" height="192">
            <defs>
                <radialGradient id="faceGrad" cx="50%" cy="40%" r="60%">
                    <stop offset="0%" stop-color="${p.skin}"/>
                    <stop offset="100%" stop-color="${p.skinDark}"/>
                </radialGradient>
                <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0004"/>
                </filter>
            </defs>
            <!-- Body/shirt -->
            ${bodyPath}
            ${neckPath}
            <!-- Hair back layer -->
            ${hairPath}
            <!-- Face -->
            <ellipse cx="${cx}" cy="${cy}" rx="${r}" ry="${r+3}" fill="url(#faceGrad)" filter="url(#softShadow)"/>
            <!-- Blush -->
            ${blushEls}
            <!-- Features -->
            ${browsPath}
            ${eyesPath}
            ${nosePath}
            ${mouthPath}
            <!-- Accessories -->
            ${accessories}
        </svg>`;
    }

    // ─── Viseme sequence for speaking animation ─────────────────────────────────
    const SPEAK_SEQUENCE = ['rest','open','narrow','wide','round','narrow','open','rest','closed','open','narrow','rest'];
    const SPEAK_INTERVAL_MS = 120;

    // ─── Main AvatarController class ────────────────────────────────────────────
    class AvatarController {
        constructor(containerEl) {
            this.container = containerEl;
            this.type = 'girl';
            this.expression = 'neutral';
            this.mouthViseme = 'rest';
            this.blinkPhase = 0;        // 0=open 1=closed
            this._speakTimer = null;
            this._blinkTimer = null;
            this._speakIdx = 0;
            this._visible = false;
            this._currentText = '';
            this._render();
            this._startBlink();
        }

        // Public API
        setType(type) {
            this.type = PALETTES[type] ? type : 'girl';
            this._render();
        }

        setExpression(expr) {
            this.expression = EXPRESSIONS[expr] ? expr : 'neutral';
            this._render();
        }

        speak(text) {
            console.log('[Avatar] speak() called, chars:', text ? text.length : 0);
            this._currentText = text || '';
            this.setExpression(detectExpression(text));
            this._startSpeaking();
            this._showBubble(text);
            this._speak(text);
        }

        stopSpeaking() {
            this._stopSpeaking();
            this._cancelTTS();
            this.mouthViseme = 'rest';
            this._render();
        }

        setMuted(muted) {
            this._muted = !!muted;
            this._syncMuteBtn();
            if (muted) this._cancelTTS();
        }

        show() {
            this._visible = true;
            this.container.style.display = 'flex';
        }

        hide() {
            this._visible = false;
            this.container.style.display = 'none';
        }

        // Choose type from character_id + user gender
        applyCharacter(characterId, userGender) {
            let type = CHARACTER_MAP[characterId] || null;
            if (!type) {
                // Default: opposite gender to user
                if (userGender === 'male') type = 'girl';
                else if (userGender === 'female') type = 'boy';
                else type = 'girl';
            }
            this.setType(type);
            // Update label — use per-character name, fall back to palette default
            const labelEl = this.container.querySelector('.avatar-name');
            if (labelEl) labelEl.textContent = CHARACTER_NAMES[characterId] || (PALETTES[type] || PALETTES.girl).label;
        }

        // ─── Internal ────────────────────────────────────────────────────────────
        _speak(text) {
            console.log('[Avatar TTS] _speak called, text length:', text ? text.length : 0,
                '| _muted:', this._muted, '| _globalMuted:', _globalMuted,
                '| speechSynthesis:', !!window.speechSynthesis);
            if (!text || this._muted || _globalMuted) { console.warn('[Avatar TTS] Blocked by mute/empty'); return; }
            if (!window.speechSynthesis) { console.warn('[Avatar TTS] No speechSynthesis API'); return; }

            // Cancel any ongoing speech first
            this._ttsCancelled = true;
            window.speechSynthesis.cancel();

            // Chrome drops speak() called synchronously after cancel().
            // Defer the start by one event-loop tick.
            setTimeout(() => {
                this._ttsCancelled = false;

                const chunks = this._splitText(text);
                console.log('[Avatar TTS] Starting', chunks.length, 'chunk(s)');

                // Pick voice ONCE so every chunk uses the same voice
                const gender = this._ttsGender();
                const pitch  = gender === 'female' ? 1.2 : gender === 'old' ? 0.85 : 1.0;
                let chosenVoice = null;
                const voices = window.speechSynthesis.getVoices();
                if (voices.length) {
                    const lang = voices.filter(v => v.lang.startsWith('en'));
                    const FEMALE_NAMES = ['female','zira','samantha','victoria','karen','moira','aria','jenny','jane','susan','hazel','eva','natasha','tessa','fiona','allison','ava','lisa','catherine','linda'];
                    const MALE_NAMES   = ['male','david','mark','daniel','alex','james','guy','richard','george','rishi','ryan','fred','bruce'];
                    const gendered = lang.filter(v => {
                        const n = v.name.toLowerCase();
                        if (gender === 'female') return FEMALE_NAMES.some(k => n.includes(k));
                        return MALE_NAMES.some(k => n.includes(k));
                    });
                    // Fallback: for female, exclude voices with known male names
                    if (!gendered.length && gender === 'female') {
                        const fallback = lang.filter(v => !MALE_NAMES.some(k => v.name.toLowerCase().includes(k)));
                        chosenVoice = fallback.length ? fallback[0] : (lang.length ? lang[0] : null);
                    } else {
                        chosenVoice = gendered.length ? gendered[0] : (lang.length ? lang[0] : null);
                    }
                }
                console.log('[Avatar TTS] Voice:', chosenVoice ? chosenVoice.name : 'default');

                let idx = 0;

                const speakNext = () => {
                    if (idx >= chunks.length || this._ttsCancelled) {
                        console.log('[Avatar TTS] Done (idx=' + idx + ', cancelled=' + this._ttsCancelled + ')');
                        this._stopSpeaking();
                        this.mouthViseme = 'rest';
                        this._render();
                        return;
                    }

                    const chunkText = chunks[idx++];
                    const utt = new SpeechSynthesisUtterance(chunkText);
                    utt.rate = 1.05;
                    utt.pitch = pitch;
                    utt.volume = 0.9;
                    if (chosenVoice) utt.voice = chosenVoice;
                    console.log('[Avatar TTS] Speaking chunk', idx, '| voice:', utt.voice ? utt.voice.name : 'default');

                    utt.onstart = () => console.log('[Avatar TTS] onstart chunk', idx);
                    utt.onend = () => { console.log('[Avatar TTS] onend chunk', idx); speakNext(); };
                    utt.onerror = (e) => {
                        console.error('[Avatar TTS] onerror chunk', idx, e.error);
                        if (e.error !== 'interrupted') speakNext();
                    };

                    this._currentUtt = utt;
                    window.speechSynthesis.speak(utt);
                    console.log('[Avatar TTS] speechSynthesis.speak() called, pending:', window.speechSynthesis.pending, 'speaking:', window.speechSynthesis.speaking);
                };

                speakNext();
            }, 50);
        }

        _splitText(text) {
            // Split at sentence endings, keeping chunks ≤ 200 chars
            const MAX = 200;
            const sentences = text.match(/[^.!?\n]{1,200}[.!?\n]?/g) || [text];
            const chunks = [];
            for (const s of sentences) {
                if (s.trim()) chunks.push(s.trim());
            }
            return chunks.length ? chunks : [text.slice(0, MAX)];
        }

        _cancelTTS() {
            this._ttsCancelled = true;
            this._currentUtt = null;
            if (window.speechSynthesis) window.speechSynthesis.cancel();
        }

        _ttsGender() {
            if (this.type === 'girl' || this.type === 'woman') return 'female';
            if (this.type === 'man_ancient') return 'old';
            return 'male';
        }

        _syncMuteBtn() {
            const btn = this.container && this.container.querySelector('.avatar-mute-btn');
            if (!btn) return;
            const muted = this._muted || _globalMuted;
            btn.title = muted ? 'Unmute' : 'Mute';
            btn.textContent = muted ? '🔇' : '🔊';
            btn.classList.toggle('active', muted);
        }

        _render() {
            const svgWrap = this.container.querySelector('.avatar-svg-wrap');
            if (!svgWrap) return;
            svgWrap.innerHTML = buildSVG(this.type, this.expression, this.mouthViseme, this.blinkPhase);
        }

        _startSpeaking() {
            this._stopSpeaking();
            this._speakIdx = 0;
            this._speakTimer = setInterval(() => {
                this.mouthViseme = SPEAK_SEQUENCE[this._speakIdx % SPEAK_SEQUENCE.length];
                this._speakIdx++;
                this._render();
            }, SPEAK_INTERVAL_MS);
        }

        _stopSpeaking() {
            if (this._speakTimer) { clearInterval(this._speakTimer); this._speakTimer = null; }
        }

        _startBlink() {
            const scheduleBlink = () => {
                const delay = 2500 + Math.random() * 3000;
                this._blinkTimer = setTimeout(() => {
                    this.blinkPhase = 1;
                    this._render();
                    setTimeout(() => {
                        this.blinkPhase = 0;
                        this._render();
                        scheduleBlink();
                    }, 120);
                }, delay);
            };
            scheduleBlink();
        }

        _showBubble(text) {
            const bubble = this.container.querySelector('.avatar-bubble');
            if (!bubble) return;
            bubble.textContent = text;
            bubble.classList.add('visible');
            // Truncate long text in bubble
            if (text && text.length > 180) {
                bubble.textContent = text.slice(0, 177) + '…';
            }
        }

        hideBubble() {
            const bubble = this.container.querySelector('.avatar-bubble');
            if (bubble) bubble.classList.remove('visible');
        }

        destroy() {
            this._stopSpeaking();
            this._cancelTTS();
            if (this._blinkTimer) clearTimeout(this._blinkTimer);
        }
    }

    // ─── Factory / singleton per container ──────────────────────────────────────
    function createPanel(containerEl) {
        return new AvatarController(containerEl);
    }

    // ─── Build the DOM panel HTML ────────────────────────────────────────────────
    function buildPanelHTML(avatarId) {
        const muted = _globalMuted;
        return `<div class="avatar-panel" id="${avatarId}">
            <div class="avatar-header">
                <span class="avatar-name">Aria</span>
                <div class="avatar-controls">
                    <button class="avatar-ctrl-btn avatar-mute-btn" title="${muted ? 'Unmute' : 'Mute'}" id="${avatarId}-mute">${muted ? '🔇' : '🔊'}</button>
                    <button class="avatar-ctrl-btn" title="Minimise" id="${avatarId}-toggle">
                        <svg width="14" height="14" viewBox="0 0 14 14"><path d="M2 7 L12 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                    </button>
                    <button class="avatar-ctrl-btn" title="Close avatar" id="${avatarId}-close">&times;</button>
                </div>
            </div>
            <div class="avatar-body">
                <div class="avatar-speech-wrap">
                    <div class="avatar-bubble"></div>
                </div>
                <div class="avatar-svg-wrap"></div>
            </div>
            <div class="avatar-expression-bar">
                <button class="expr-btn active" data-expr="neutral" title="Neutral">😐</button>
                <button class="expr-btn" data-expr="happy" title="Happy">😊</button>
                <button class="expr-btn" data-expr="thinking" title="Thinking">🤔</button>
                <button class="expr-btn" data-expr="surprised" title="Surprised">😮</button>
                <button class="expr-btn" data-expr="encouraging" title="Encouraging">💪</button>
            </div>
        </div>`;
    }

    // ─── Global mute helpers ─────────────────────────────────────────────────────
    function isMuted() { return _globalMuted; }
    function setGlobalMute(val) {
        _globalMuted = !!val;
        try { localStorage.setItem('avatarMuted', String(_globalMuted)); } catch {}
        if (_globalMuted && window.speechSynthesis) window.speechSynthesis.cancel();
        // Sync all mute buttons in all panels
        document.querySelectorAll('.avatar-mute-btn').forEach(btn => {
            btn.title = _globalMuted ? 'Unmute' : 'Mute';
            btn.textContent = _globalMuted ? '🔇' : '🔊';
            btn.classList.toggle('active', _globalMuted);
        });
    }

    // ─── PhotoAvatarController class for MediaPipe-based photo avatars ─────────────
    class PhotoAvatarController {
        constructor(containerEl, imageUrl) {
            this.container = containerEl;
            this.imageUrl = imageUrl;
            this.photoAvatar = null;
            this._isReady = false;
            this.expression = 'neutral';
            this._bubbleText = '';
        }

        async init() {
            console.log('[PhotoAvatarController] init() starting');
            if (!window.PhotoAvatar) {
                console.error('[PhotoAvatarController] PhotoAvatar class not loaded');
                return;
            }
            console.log('[PhotoAvatarController] Creating PhotoAvatar with container:', this.container);
            this.photoAvatar = new PhotoAvatar(this.container, this.imageUrl);
            try {
                await this.photoAvatar.init();
                this._isReady = true;
                console.log('[PhotoAvatarController] Ready');
            } catch (err) {
                console.error('[PhotoAvatarController] Init failed:', err);
            }
        }

        setType(type) {
            // No-op for photo avatars - face is fixed
        }

        setExpression(expr) {
            this.expression = expr;
            // Could map expressions to subtle head tilt or eye movement in future
        }

        speak(text) {
            console.log('[PhotoAvatarController] speak() called, ready:', this._isReady);
            if (!this._isReady || !this.photoAvatar) {
                console.warn('[PhotoAvatarController] Not ready, cannot speak');
                return;
            }
            this._showBubble(text);
            this.photoAvatar.speak(text);
        }

        stopSpeaking() {
            if (this.photoAvatar) this.photoAvatar.stop();
            this.hideBubble();
        }

        applyCharacter(characterId, userGender) {
            // Character applied via image URL at construction time
            // Could swap image based on characterId here
        }

        _showBubble(text) {
            const bubble = this.container.querySelector('.avatar-bubble');
            if (!bubble) return;
            bubble.textContent = text;
            bubble.classList.add('visible');
            if (text && text.length > 180) {
                bubble.textContent = text.slice(0, 177) + '…';
            }
        }

        hideBubble() {
            const bubble = this.container.querySelector('.avatar-bubble');
            if (bubble) bubble.classList.remove('visible');
        }

        destroy() {
            if (this.photoAvatar) {
                this.photoAvatar.destroy();
                this.photoAvatar = null;
            }
        }
    }

    // ─── Factory for photo-based avatars ──────────────────────────────────────────
    async function createPhotoPanel(containerEl, imageUrl) {
        const ctrl = new PhotoAvatarController(containerEl, imageUrl);
        await ctrl.init();
        return ctrl;
    }

    // ─── LivePortraitAvatarController for advanced animation ──────────────────────
    class LivePortraitAvatarController {
        constructor(containerEl, imageUrl) {
            this.container = containerEl;
            this.imageUrl = imageUrl;
            this.avatar = null;
            this._isReady = false;
            this.expression = 'neutral';
        }

        async init() {
            console.log('[LivePortraitController] init() starting');
            if (!window.LivePortraitAvatar) {
                console.error('[LivePortraitController] LivePortraitAvatar class not loaded');
                return;
            }
            this.avatar = new LivePortraitAvatar(this.container, this.imageUrl);
            try {
                await this.avatar.init();
                this._isReady = true;
                console.log('[LivePortraitController] Ready');
            } catch (err) {
                console.error('[LivePortraitController] Init failed:', err);
            }
        }

        setType(type) { /* No-op - face is fixed */ }

        setExpression(expr) {
            this.expression = expr;
            if (this.avatar) this.avatar.setExpression(expr);
        }

        speak(text) {
            console.log('[LivePortraitController] speak() called, ready:', this._isReady);
            if (!this._isReady || !this.avatar) {
                console.warn('[LivePortraitController] Not ready, cannot speak');
                return;
            }
            this._showBubble(text);
            this.avatar.speak(text);
        }

        stopSpeaking() {
            if (this.avatar) this.avatar.stop();
            this.hideBubble();
        }

        applyCharacter(characterId, userGender) {
            // Character applied via image URL at construction time
        }

        _showBubble(text) {
            const bubble = this.container.querySelector('.avatar-bubble');
            if (!bubble) return;
            bubble.textContent = text;
            bubble.classList.add('visible');
            if (text && text.length > 180) {
                bubble.textContent = text.slice(0, 177) + '…';
            }
        }

        hideBubble() {
            const bubble = this.container.querySelector('.avatar-bubble');
            if (bubble) bubble.classList.remove('visible');
        }

        destroy() {
            if (this.avatar) {
                this.avatar.destroy();
                this.avatar = null;
            }
        }
    }

    // ─── Factory for LivePortrait avatars ─────────────────────────────────────────
    async function createLivePortraitPanel(containerEl, imageUrl) {
        const ctrl = new LivePortraitAvatarController(containerEl, imageUrl);
        await ctrl.init();
        return ctrl;
    }

    // ─── Public surface ──────────────────────────────────────────────────────────
    return { 
        createPanel, createPhotoPanel, createLivePortraitPanel, 
        buildPanelHTML, CHARACTER_MAP, PALETTES, 
        detectExpression, isMuted, setGlobalMute, 
        PhotoAvatarController, LivePortraitAvatarController 
    };

})();

window.AvatarEngine = AvatarEngine;
