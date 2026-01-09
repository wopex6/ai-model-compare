/**
 * Voice Input Module
 * Provides speech-to-text functionality for chat input.
 */

class VoiceInput {
    constructor(options = {}) {
        this.targetInput = options.targetInput || '#user-input';
        this.onResult = options.onResult || null;
        this.onError = options.onError || null;
        this.language = options.language || 'en-US';
        
        this.recognition = null;
        this.isListening = false;
        this.isSupported = this._checkSupport();
        
        if (this.isSupported) {
            this._initRecognition();
        }
    }
    
    _checkSupport() {
        return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    }
    
    _initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = this.language;
        
        this.recognition.onstart = () => {
            this.isListening = true;
            this._updateUI(true);
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            this._updateUI(false);
        };
        
        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Update input field
            const input = document.querySelector(this.targetInput);
            if (input) {
                if (finalTranscript) {
                    input.value = (input.value + ' ' + finalTranscript).trim();
                    if (this.onResult) {
                        this.onResult(finalTranscript, true);
                    }
                } else if (interimTranscript) {
                    // Show interim in a temporary way
                    input.placeholder = interimTranscript;
                }
            }
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.isListening = false;
            this._updateUI(false);
            
            if (this.onError) {
                this.onError(event.error);
            }
        };
    }
    
    _updateUI(listening) {
        const btn = document.querySelector('#voice-btn, .voice-input-btn');
        if (btn) {
            btn.classList.toggle('listening', listening);
            btn.innerHTML = listening 
                ? '<i class="fas fa-microphone-slash"></i>' 
                : '<i class="fas fa-microphone"></i>';
        }
    }
    
    start() {
        if (!this.isSupported) {
            alert('Voice input is not supported in your browser. Please use Chrome or Edge.');
            return false;
        }
        
        if (this.isListening) {
            this.stop();
            return false;
        }
        
        try {
            this.recognition.start();
            return true;
        } catch (e) {
            console.error('Failed to start voice recognition:', e);
            return false;
        }
    }
    
    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    toggle() {
        if (this.isListening) {
            this.stop();
        } else {
            this.start();
        }
    }
}

/**
 * Message Export Module
 * Exports conversation history to various formats.
 */

class MessageExporter {
    constructor(options = {}) {
        this.appName = options.appName || 'AI Life Companion';
    }
    
    exportToJSON(messages, filename = 'conversation.json') {
        const data = {
            exported_at: new Date().toISOString(),
            app: this.appName,
            message_count: messages.length,
            messages: messages.map(m => ({
                role: m.role || m.sender,
                content: m.content || m.message,
                timestamp: m.timestamp || new Date().toISOString()
            }))
        };
        
        this._download(JSON.stringify(data, null, 2), filename, 'application/json');
    }
    
    exportToTXT(messages, filename = 'conversation.txt') {
        let text = `${this.appName} - Conversation Export\n`;
        text += `Exported: ${new Date().toLocaleString()}\n`;
        text += '='.repeat(50) + '\n\n';
        
        messages.forEach(m => {
            const role = (m.role || m.sender || 'unknown').toUpperCase();
            const content = m.content || m.message || '';
            const time = m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : '';
            
            text += `[${role}] ${time}\n`;
            text += content + '\n\n';
        });
        
        this._download(text, filename, 'text/plain');
    }
    
    exportToMarkdown(messages, filename = 'conversation.md') {
        let md = `# ${this.appName} - Conversation\n\n`;
        md += `*Exported: ${new Date().toLocaleString()}*\n\n---\n\n`;
        
        messages.forEach(m => {
            const role = m.role || m.sender || 'unknown';
            const content = m.content || m.message || '';
            const isUser = role.toLowerCase() === 'user';
            
            md += isUser ? '**You:**\n' : '**Assistant:**\n';
            md += content + '\n\n';
        });
        
        this._download(md, filename, 'text/markdown');
    }
    
    exportToHTML(messages, filename = 'conversation.html') {
        let html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>${this.appName} - Conversation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .message { margin: 15px 0; padding: 12px 16px; border-radius: 12px; }
        .user { background: #667eea; color: white; margin-left: 20%; }
        .assistant { background: #f0f0f0; margin-right: 20%; }
        .meta { font-size: 12px; color: #888; margin-top: 5px; }
        h1 { color: #667eea; }
    </style>
</head>
<body>
    <h1>${this.appName}</h1>
    <p><em>Exported: ${new Date().toLocaleString()}</em></p>
    <hr>
`;
        
        messages.forEach(m => {
            const role = m.role || m.sender || 'unknown';
            const content = m.content || m.message || '';
            const cssClass = role.toLowerCase() === 'user' ? 'user' : 'assistant';
            
            html += `    <div class="message ${cssClass}">${this._escapeHtml(content)}</div>\n`;
        });
        
        html += '</body>\n</html>';
        
        this._download(html, filename, 'text/html');
    }
    
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    _download(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

/**
 * Conversation Sharing Module
 * Generates shareable links or snippets.
 */

class ConversationSharer {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || window.location.origin;
    }
    
    async shareViaWebShare(title, text) {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: title,
                    text: text,
                    url: window.location.href
                });
                return true;
            } catch (e) {
                if (e.name !== 'AbortError') {
                    console.error('Share failed:', e);
                }
                return false;
            }
        }
        return false;
    }
    
    copyToClipboard(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text)
                .then(() => {
                    this._showNotification('Copied to clipboard!');
                    return true;
                })
                .catch(() => {
                    return this._fallbackCopy(text);
                });
        }
        return Promise.resolve(this._fallbackCopy(text));
    }
    
    _fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            this._showNotification('Copied to clipboard!');
            return true;
        } catch (e) {
            return false;
        } finally {
            document.body.removeChild(textarea);
        }
    }
    
    formatForSharing(messages, maxLength = 500) {
        let text = '';
        
        for (const m of messages.slice(-5)) {  // Last 5 messages
            const role = (m.role || m.sender || '').toUpperCase();
            const content = m.content || m.message || '';
            
            const line = `${role}: ${content}\n`;
            if (text.length + line.length > maxLength) break;
            text += line;
        }
        
        return text.trim();
    }
    
    _showNotification(message) {
        // Try to show a toast notification
        const existing = document.querySelector('.share-toast');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.className = 'share-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10000;
            animation: fadeInUp 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }
}

// Export for use
window.VoiceInput = VoiceInput;
window.MessageExporter = MessageExporter;
window.ConversationSharer = ConversationSharer;

// Auto-initialize if elements exist
document.addEventListener('DOMContentLoaded', () => {
    // Initialize voice input if button exists
    const voiceBtn = document.querySelector('#voice-btn, .voice-input-btn');
    if (voiceBtn) {
        const voiceInput = new VoiceInput();
        voiceBtn.addEventListener('click', () => voiceInput.toggle());
        
        if (!voiceInput.isSupported) {
            voiceBtn.style.display = 'none';
        }
    }
});
