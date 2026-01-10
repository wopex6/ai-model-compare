/**
 * User Settings Manager
 * Handles user preferences, notifications, and theme settings.
 */

class UserSettings {
    constructor() {
        this.STORAGE_KEY = 'user_settings';
        this.defaults = {
            theme: 'system',
            notifications: {
                enabled: true,
                sound: true,
                desktop: false,
                budgetAlerts: true,
                dailySummary: false
            },
            display: {
                fontSize: 'medium',
                messageSpacing: 'normal',
                showTimestamps: true,
                compactMode: false
            },
            chat: {
                enterToSend: true,
                showTypingIndicator: true,
                autoScroll: true,
                saveHistory: true
            },
            accessibility: {
                reducedMotion: false,
                highContrast: false
            }
        };
        this.settings = this.load();
    }

    load() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                return { ...this.defaults, ...JSON.parse(saved) };
            }
        } catch (e) {
            console.warn('Failed to load settings:', e);
        }
        return { ...this.defaults };
    }

    save() {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.settings));
            window.dispatchEvent(new CustomEvent('settingschange', { detail: this.settings }));
        } catch (e) {
            console.warn('Failed to save settings:', e);
        }
    }

    get(key) {
        const keys = key.split('.');
        let value = this.settings;
        for (const k of keys) {
            value = value?.[k];
        }
        return value;
    }

    set(key, value) {
        const keys = key.split('.');
        let obj = this.settings;
        for (let i = 0; i < keys.length - 1; i++) {
            obj = obj[keys[i]];
        }
        obj[keys[keys.length - 1]] = value;
        this.save();
        this.applySettings();
    }

    reset() {
        this.settings = { ...this.defaults };
        this.save();
        this.applySettings();
    }

    applySettings() {
        // Apply font size
        const fontSizes = { small: '14px', medium: '16px', large: '18px' };
        document.documentElement.style.setProperty('--base-font-size', fontSizes[this.settings.display.fontSize] || '16px');

        // Apply reduced motion
        if (this.settings.accessibility.reducedMotion) {
            document.documentElement.classList.add('reduce-motion');
        } else {
            document.documentElement.classList.remove('reduce-motion');
        }

        // Apply compact mode
        if (this.settings.display.compactMode) {
            document.body.classList.add('compact-mode');
        } else {
            document.body.classList.remove('compact-mode');
        }

        // Apply high contrast
        if (this.settings.accessibility.highContrast) {
            document.documentElement.classList.add('high-contrast');
        } else {
            document.documentElement.classList.remove('high-contrast');
        }
    }

    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.set('notifications.desktop', permission === 'granted');
            return permission === 'granted';
        }
        return false;
    }

    showNotification(title, body, options = {}) {
        if (!this.settings.notifications.enabled) return;
        
        if (this.settings.notifications.desktop && Notification.permission === 'granted') {
            new Notification(title, { body, icon: '/static/icons/icon-192.png', ...options });
        }

        if (this.settings.notifications.sound) {
            this.playNotificationSound();
        }
    }

    playNotificationSound() {
        try {
            const audio = new Audio('/static/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(() => {});
        } catch (e) {}
    }

    exportSettings() {
        return JSON.stringify(this.settings, null, 2);
    }

    importSettings(json) {
        try {
            const imported = JSON.parse(json);
            this.settings = { ...this.defaults, ...imported };
            this.save();
            this.applySettings();
            return true;
        } catch (e) {
            console.error('Failed to import settings:', e);
            return false;
        }
    }
}

// Settings Panel UI
class SettingsPanel {
    constructor(settings) {
        this.settings = settings;
        this.isOpen = false;
    }

    render() {
        return `
        <div class="settings-panel" id="settings-panel">
            <div class="settings-header">
                <h2><i class="fas fa-cog"></i> Settings</h2>
                <button class="btn-ghost" onclick="settingsPanel.close()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="settings-body">
                ${this.renderSection('Display', [
                    this.renderSelect('Theme', 'theme', ['system', 'light', 'dark']),
                    this.renderSelect('Font Size', 'display.fontSize', ['small', 'medium', 'large']),
                    this.renderToggle('Show Timestamps', 'display.showTimestamps'),
                    this.renderToggle('Compact Mode', 'display.compactMode')
                ])}
                
                ${this.renderSection('Notifications', [
                    this.renderToggle('Enable Notifications', 'notifications.enabled'),
                    this.renderToggle('Sound', 'notifications.sound'),
                    this.renderToggle('Desktop Notifications', 'notifications.desktop'),
                    this.renderToggle('Budget Alerts', 'notifications.budgetAlerts')
                ])}
                
                ${this.renderSection('Chat', [
                    this.renderToggle('Enter to Send', 'chat.enterToSend'),
                    this.renderToggle('Show Typing Indicator', 'chat.showTypingIndicator'),
                    this.renderToggle('Auto-scroll', 'chat.autoScroll'),
                    this.renderToggle('Save History', 'chat.saveHistory')
                ])}
                
                ${this.renderSection('Accessibility', [
                    this.renderToggle('Reduce Motion', 'accessibility.reducedMotion'),
                    this.renderToggle('High Contrast', 'accessibility.highContrast')
                ])}
            </div>
            <div class="settings-footer">
                <button class="btn btn-secondary btn-sm" onclick="userSettings.reset(); settingsPanel.refresh();">
                    Reset to Defaults
                </button>
                <button class="btn btn-primary btn-sm" onclick="settingsPanel.close();">
                    Done
                </button>
            </div>
        </div>
        `;
    }

    renderSection(title, items) {
        return `
        <div class="settings-section">
            <h3>${title}</h3>
            ${items.join('')}
        </div>
        `;
    }

    renderToggle(label, key) {
        const checked = this.settings.get(key) ? 'checked' : '';
        return `
        <div class="setting-row">
            <label>${label}</label>
            <label class="toggle">
                <input type="checkbox" ${checked} onchange="userSettings.set('${key}', this.checked)">
                <span class="toggle-slider"></span>
            </label>
        </div>
        `;
    }

    renderSelect(label, key, options) {
        const current = this.settings.get(key);
        const optionsHtml = options.map(opt => 
            `<option value="${opt}" ${opt === current ? 'selected' : ''}>${opt.charAt(0).toUpperCase() + opt.slice(1)}</option>`
        ).join('');
        return `
        <div class="setting-row">
            <label>${label}</label>
            <select onchange="userSettings.set('${key}', this.value)">${optionsHtml}</select>
        </div>
        `;
    }

    open() {
        let panel = document.getElementById('settings-panel');
        if (!panel) {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = this.render();
            document.body.appendChild(wrapper.firstElementChild);
            panel = document.getElementById('settings-panel');
        }
        panel.classList.add('open');
        this.isOpen = true;
    }

    close() {
        const panel = document.getElementById('settings-panel');
        if (panel) {
            panel.classList.remove('open');
        }
        this.isOpen = false;
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    refresh() {
        const panel = document.getElementById('settings-panel');
        if (panel) {
            panel.outerHTML = this.render();
            document.getElementById('settings-panel').classList.add('open');
        }
    }
}

// Add CSS for settings panel
const settingsStyles = document.createElement('style');
settingsStyles.textContent = `
.settings-panel {
    position: fixed;
    top: 0;
    right: -400px;
    width: 380px;
    height: 100vh;
    background: var(--bg-card);
    box-shadow: var(--shadow-xl);
    z-index: 1001;
    display: flex;
    flex-direction: column;
    transition: right var(--transition-normal);
}

.settings-panel.open {
    right: 0;
}

.settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--border-light);
}

.settings-header h2 {
    margin: 0;
    font-size: 18px;
    color: var(--text-primary);
}

.settings-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.settings-section {
    margin-bottom: 24px;
}

.settings-section h3 {
    font-size: 14px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
}

.setting-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-light);
}

.setting-row label:first-child {
    color: var(--text-primary);
    font-size: 14px;
}

.setting-row select {
    padding: 6px 12px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-medium);
    background: var(--bg-primary);
    color: var(--text-primary);
}

.toggle {
    position: relative;
    width: 48px;
    height: 26px;
}

.toggle input {
    opacity: 0;
    width: 0;
    height: 0;
}

.toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--border-medium);
    border-radius: 26px;
    transition: var(--transition-fast);
}

.toggle-slider::before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 3px;
    bottom: 3px;
    background: white;
    border-radius: 50%;
    transition: var(--transition-fast);
}

.toggle input:checked + .toggle-slider {
    background: var(--primary);
}

.toggle input:checked + .toggle-slider::before {
    transform: translateX(22px);
}

.settings-footer {
    display: flex;
    justify-content: space-between;
    padding: 20px;
    border-top: 1px solid var(--border-light);
}

@media (max-width: 480px) {
    .settings-panel {
        width: 100%;
        right: -100%;
    }
}
`;
document.head.appendChild(settingsStyles);

// Initialize
const userSettings = new UserSettings();
const settingsPanel = new SettingsPanel(userSettings);

// Apply settings on load
document.addEventListener('DOMContentLoaded', () => {
    userSettings.applySettings();
});
