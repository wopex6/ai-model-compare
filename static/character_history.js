/**
 * Character Conversation History Manager
 * Shared module for managing conversation history across all character templates
 * Usage: Include this script in character templates and call initCharacterHistory(characterId)
 */

class CharacterHistoryManager {
    constructor(characterId) {
        this.characterId = characterId;
        this.sessionId = null;
        this.cookieName = `session_${characterId}`;
    }

    /**
     * Initialize history management - call this on page load
     */
    async init() {
        await this.loadConversationHistory();
    }

    /**
     * Load conversation history from backend
     */
    async loadConversationHistory() {
        try {
            // Get session ID from cookie
            this.sessionId = this.getCookie(this.cookieName);
            
            if (this.sessionId) {
                console.log(`📚 Loading history for ${this.characterId}, session: ${this.sessionId}`);
                
                // Fetch conversation history from backend
                const response = await fetch(`/${this.characterId}/history?session_id=${this.sessionId}`);
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    console.log(`✅ Loaded ${data.messages.length} messages from history`);
                    return data.messages;
                } else {
                    console.log(`📭 No messages in history for session ${this.sessionId}`);
                    return [];
                }
            } else {
                console.log(`🆕 No existing session found for ${this.characterId}, starting new conversation`);
                return [];
            }
        } catch (error) {
            console.error('❌ Error loading conversation history:', error);
            return [];
        }
    }

    /**
     * Update session ID (call this after receiving response from chat endpoint)
     * @param {string} newSessionId - Session ID from backend response
     */
    updateSession(newSessionId) {
        if (newSessionId) {
            const isNewSession = !this.sessionId;
            this.sessionId = newSessionId;
            this.setCookie(this.cookieName, newSessionId);
            
            if (isNewSession) {
                console.log(`🆕 New session created: ${newSessionId}`);
            } else {
                console.log(`🔄 Session updated: ${newSessionId}`);
            }
        }
    }

    /**
     * Get current session ID
     */
    getSessionId() {
        return this.sessionId;
    }

    /**
     * Get cookie value by name
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    /**
     * Set cookie with name and value
     */
    setCookie(name, value, days = 365) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    }

    /**
     * Clear session (for testing/logout)
     */
    clearSession() {
        this.sessionId = null;
        this.setCookie(this.cookieName, '', -1); // Expire cookie
        console.log(`🗑️ Session cleared for ${this.characterId}`);
    }
}

// Global helper function for easy initialization
function initCharacterHistory(characterId) {
    const historyManager = new CharacterHistoryManager(characterId);
    return historyManager;
}

// Export for use in templates
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CharacterHistoryManager, initCharacterHistory };
}
