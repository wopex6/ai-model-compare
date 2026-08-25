/**
 * AvatarWidget — Shared initialiser for all pages using the avatar system.
 *
 * Usage (any page):
 *   AvatarWidget.init({ characterId, userGender, containerSelector, greeting });
 *
 * The widget:
 *   - Builds the panel HTML inside `containerSelector` (default '#avatar-side')
 *   - Wires the toggle chip (#avatar-toggle-chip) if present
 *   - Wires close / minimise / mute buttons
 *   - Wires expression bar
 *   - Optionally shows a greeting speech bubble after a short delay
 *   - Returns the AvatarController so the caller can call .speak() / .setExpression()
 */

const AvatarWidget = (() => {

    // ── Wire all control buttons for one panel ────────────────────────────────
    function _wirePanel(panelId, ctrl, opts = {}) {
        const { onClose, onToggle } = opts;

        // Mute button — global mute toggle
        const muteBtn = document.getElementById(panelId + '-mute');
        if (muteBtn) {
            muteBtn.addEventListener('click', () => {
                AvatarEngine.setGlobalMute(!AvatarEngine.isMuted());
            });
        }

        // Minimise button
        const toggleBtn = document.getElementById(panelId + '-toggle');
        const panel = document.getElementById(panelId);
        if (toggleBtn && panel) {
            toggleBtn.addEventListener('click', () => {
                panel.classList.toggle('collapsed');
                if (onToggle) onToggle(panel.classList.contains('collapsed'));
            });
        }

        // Close button
        const closeBtn = document.getElementById(panelId + '-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                if (onClose) onClose();
            });
        }

        // Expression bar
        if (panel) {
            panel.querySelectorAll('.expr-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    panel.querySelectorAll('.expr-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    ctrl.setExpression(btn.dataset.expr);
                });
            });
        }
    }

    // ── Build + inject one panel into a container element ─────────────────────
    function _buildIn(containerId, panelId, characterId, userGender, photoUrl = null, livePortraitUrl = null) {
        const container = document.getElementById(containerId);
        if (!container || container.querySelector('.avatar-panel')) return null;

        // LivePortrait avatar mode (advanced animation)
        if (livePortraitUrl) {
            return _buildPhotoAvatar(container, panelId, characterId, userGender, livePortraitUrl, true);
        }

        // Photo avatar mode (basic MediaPipe)
        if (photoUrl) {
            return _buildPhotoAvatar(container, panelId, characterId, userGender, photoUrl, false);
        }

        container.innerHTML = AvatarEngine.buildPanelHTML(panelId);
        const panelEl = document.getElementById(panelId);
        if (!panelEl) return null;

        const ctrl = AvatarEngine.createPanel(panelEl);
        ctrl.applyCharacter(characterId, userGender);
        return ctrl;
    }

    // ── Helper to build photo/LivePortrait avatars with proxy controller ────────────
    function _buildPhotoAvatar(container, panelId, characterId, userGender, imageUrl, isLivePortrait) {
        container.innerHTML = _buildPhotoPanelHTML(panelId);
        const canvasContainer = document.getElementById(panelId + '-canvas');
        if (!canvasContainer) return null;
        
        // Create proxy controller that queues calls until real controller is ready
        const pendingCalls = [];
        let realCtrl = null;
        
        const proxyCtrl = {
            _isPhoto: true,
            _isLivePortrait: isLivePortrait,
            _isProxy: true,
            speak: (text) => {
                if (realCtrl) realCtrl.speak(text);
                else pendingCalls.push(['speak', text]);
            },
            stopSpeaking: () => {
                if (realCtrl) realCtrl.stopSpeaking();
                else pendingCalls.push(['stopSpeaking']);
            },
            setExpression: (expr) => {
                if (realCtrl) realCtrl.setExpression(expr);
                else pendingCalls.push(['setExpression', expr]);
            },
            applyCharacter: (id, gender) => {
                if (realCtrl) realCtrl.applyCharacter(id, gender);
                else pendingCalls.push(['applyCharacter', id, gender]);
            }
        };
        
        // Choose between LivePortrait and basic Photo avatar
        const createFn = isLivePortrait 
            ? AvatarEngine.createLivePortraitPanel 
            : AvatarEngine.createPhotoPanel;
        
        createFn(canvasContainer, imageUrl).then(ctrl => {
            if (ctrl) {
                realCtrl = ctrl;
                ctrl.applyCharacter(characterId, userGender);
                // Flush pending calls
                pendingCalls.forEach(([method, ...args]) => {
                    if (realCtrl[method]) realCtrl[method](...args);
                });
            }
        });
        
        return proxyCtrl;
    }

    // ── Build photo avatar panel HTML (simpler - just canvas container + bubble)
    function _buildPhotoPanelHTML(panelId) {
        return `<div id="${panelId}" class="avatar-panel photo-avatar-panel">
            <div class="avatar-header">
                <span class="avatar-name">Avatar</span>
                <button class="avatar-mute-btn" id="${panelId}-mute" title="Mute">🔊</button>
                <button class="avatar-toggle-btn" id="${panelId}-toggle" title="Minimise">−</button>
                <button class="avatar-close-btn" id="${panelId}-close" title="Close">×</button>
            </div>
            <div class="avatar-canvas-container" id="${panelId}-canvas" style="width:200px;height:250px;display:flex;align-items:center;justify-content:center;">
                <!-- Canvas will be injected here by PhotoAvatar -->
            </div>
            <div class="avatar-bubble"></div>
        </div>`;
    }

    // ── Main init ─────────────────────────────────────────────────────────────
    /**
     * @param {Object} opts
     * @param {string}  opts.characterId       - e.g. 'stoic_philosopher'
     * @param {string}  [opts.userGender]      - 'male' | 'female' | null
     * @param {string}  [opts.sideContainerId] - id of the side panel container (default 'avatar-side')
     * @param {string}  [opts.floatContainerId]- id of the float container (default 'avatar-floater')
     * @param {string}  [opts.toggleChipId]    - id of toggle chip (default 'avatar-toggle-chip')
     * @param {string}  [opts.greeting]        - text to speak on load (null = no greeting)
     * @param {number}  [opts.greetingDelay]   - ms before greeting (default 1200)
     * @param {boolean} [opts.showByDefault]   - whether side panel starts visible (default from localStorage)
     * @param {string}  [opts.photoUrl]        - URL to photo for basic MediaPipe avatar
     * @param {string}  [opts.livePortraitUrl]  - URL to photo for advanced LivePortrait avatar
     * @returns {{ side: AvatarController|null, float: AvatarController|null }}
     */
    function init(opts = {}) {
        if (!window.AvatarEngine) return { side: null, float: null };

        const {
            characterId = 'coordinator',
            userGender = null,
            sideContainerId = 'avatar-side',
            floatContainerId = 'avatar-floater',
            toggleChipId = 'avatar-toggle-chip',
            greeting = null,
            greetingDelay = 1200,
            showByDefault = null,
            photoUrl = null,           // URL to photo for MediaPipe avatar
            livePortraitUrl = null,  // URL to photo for LivePortrait avatar (advanced)
        } = opts;

        // Persist so chatchat dashboard always shows the last-visited character's avatar
        try { localStorage.setItem('activeCharacterId', characterId); } catch {}

        const sidePanelId  = sideContainerId  + '-panel';
        const floatPanelId = floatContainerId + '-panel';

        // Build panels (livePortrait takes precedence over photoUrl)
        const sideCtrl  = _buildIn(sideContainerId,  sidePanelId,  characterId, userGender, null, null);
        const floatCtrl = _buildIn(floatContainerId, floatPanelId, characterId, userGender, photoUrl, livePortraitUrl);

        // Determine initial side visibility
        const sideContainer = document.getElementById(sideContainerId);
        const storedVisible = localStorage.getItem('avatarVisible') === 'true';
        const startVisible = showByDefault !== null ? showByDefault : storedVisible;

        if (sideContainer) {
            sideContainer.style.display = startVisible ? 'flex' : 'none';
        }

        // Wire toggle chip
        const chip = document.getElementById(toggleChipId);
        if (chip) {
            if (startVisible) chip.classList.add('active');
            chip.addEventListener('click', () => {
                const isShown = sideContainer && sideContainer.style.display !== 'none';
                if (isShown) {
                    if (sideContainer) sideContainer.style.display = 'none';
                    chip.classList.remove('active');
                    localStorage.setItem('avatarVisible', 'false');
                } else {
                    if (sideContainer) sideContainer.style.display = 'flex';
                    chip.classList.add('active');
                    localStorage.setItem('avatarVisible', 'true');
                }
            });
        }

        // Wire side panel controls
        if (sideCtrl) {
            _wirePanel(sidePanelId, sideCtrl, {
                onClose: () => {
                    if (sideContainer) sideContainer.style.display = 'none';
                    if (chip) chip.classList.remove('active');
                    localStorage.setItem('avatarVisible', 'false');
                }
            });
        }

        // Wire float panel controls
        const floatContainer = document.getElementById(floatContainerId);
        if (floatCtrl) {
            _wirePanel(floatPanelId, floatCtrl, {
                onClose: () => {
                    if (floatContainer) floatContainer.classList.remove('visible');
                }
            });
        }

        // Greeting on float panel
        if (greeting !== null && floatCtrl && floatContainer) {
            setTimeout(() => {
                floatContainer.classList.add('visible');
                floatCtrl.speak(greeting);
            }, greetingDelay);
        }

        return { side: sideCtrl, float: floatCtrl };
    }

    // ── Small badge SVG for character cards ───────────────────────────────────
    /**
     * Render a static mini avatar SVG into every .char-avatar-badge element
     * that has id="badge-{characterId}".
     * @param {string} userGender
     */
    function renderBadges(userGender) {
        if (!window.AvatarEngine) return;
        document.querySelectorAll('.char-avatar-badge[id^="badge-"]').forEach(el => {
            if (el.querySelector('svg')) return; // already rendered
            const charId = el.id.replace('badge-', '');
            const tmpWrap = document.createElement('div');
            tmpWrap.style.display = 'none';
            const tmpId = '_tmp_badge_' + charId;
            tmpWrap.innerHTML = AvatarEngine.buildPanelHTML(tmpId);
            document.body.appendChild(tmpWrap);
            const tmpPanel = document.getElementById(tmpId);
            if (tmpPanel) {
                const tmpCtrl = AvatarEngine.createPanel(tmpPanel);
                tmpCtrl.applyCharacter(charId, userGender);
                const svg = tmpPanel.querySelector('.avatar-svg-wrap svg');
                if (svg) {
                    const clone = svg.cloneNode(true);
                    clone.setAttribute('width', '52');
                    clone.setAttribute('height', '62');
                    el.appendChild(clone);
                }
                tmpCtrl.destroy();
            }
            document.body.removeChild(tmpWrap);
        });
    }

    // ── Hook speak / stopSpeaking into a send-message flow ────────────────────
    /**
     * Wire avatar speaking to a response string.
     * @param {AvatarController[]} controllers  - array of ctrl objects (side, float…)
     * @param {string} responseText
     */
    function onAIResponse(controllers, responseText) {
        if (!responseText) return;
        controllers.filter(Boolean).forEach(ctrl => ctrl.speak(responseText));
    }

    function onAIThinking(controllers) {
        controllers.filter(Boolean).forEach(ctrl => ctrl.setExpression('thinking'));
    }

    return { init, renderBadges, onAIResponse, onAIThinking };

})();

window.AvatarWidget = AvatarWidget;
