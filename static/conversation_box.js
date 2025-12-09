/**
 * Universal Conversation Box Module
 * Based on scientist.html template - handles all conversation logic
 * Eliminates redundancy across all character templates
 * 
 * Features:
 * - User input handling
 * - Message display (via MessageHandler)
 * - Smart Response integration
 * - AI communication
 * - Response consolidation
 * - Message history saving & loading
 * - Session management
 * - Error handling
 * - Customizable per character
 */

const ConversationBox = {
    // Configuration
    characterId: null,
    sessionId: null,
    config: {
        inputElementId: 'userInput',
        sendButtonId: 'sendBtn',
        chatEndpoint: null,  // e.g., '/scientist/chat'
        historyEndpoint: null,  // e.g., '/scientist/history'
        sessionCookieName: null,  // e.g., 'session_scientist'
        includeContext: true,
        errorMessage: 'I apologize, but I encountered an error. Please try again.',
        
        // Optional UI callbacks
        onMessageSent: null,  // Called after user message sent: (message) => {}
        onResponseReceived: null,  // Called after bot response: (data) => {}
        onError: null,  // Called on error: (error) => {}
        onSessionCreated: null,  // Called when new session created: (sessionId) => {}
        onHistoryLoaded: null  // Called after history loaded: (messages) => {}
    },
    
    /**
     * Initialize the conversation box
     * 
     * @param {string} characterId - Character identifier (e.g., 'scientist')
     * @param {object} config - Configuration options
     */
    init(characterId, config = {}) {
        this.characterId = characterId;
        
        // Merge config with defaults
        this.config = {
            ...this.config,
            ...config,
            // Auto-generate endpoints if not provided
            chatEndpoint: config.chatEndpoint || `/${characterId}/chat`,
            historyEndpoint: config.historyEndpoint || `/${characterId}/history`,
            sessionCookieName: config.sessionCookieName || `session_${characterId}`
        };
        
        // Set up event listeners
        this._setupEventListeners();
        
        // Load conversation history
        this.loadHistory();
        
        console.log(`✅ ConversationBox initialized for ${characterId}`);
    },
    
    /**
     * Set up event listeners for input and buttons
     * @private
     */
    _setupEventListeners() {
        const inputElement = document.getElementById(this.config.inputElementId);
        const sendButton = document.getElementById(this.config.sendButtonId);
        
        if (!inputElement) {
            console.error(`Input element '${this.config.inputElementId}' not found`);
            return;
        }
        
        // Enter key to send
        inputElement.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button click
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }
    },
    
    /**
     * Send a message to the backend
     * 
     * @param {string} messageText - Optional message text (uses input value if not provided)
     */
    async sendMessage(messageText = null) {
        const inputElement = document.getElementById(this.config.inputElementId);
        const message = messageText || (inputElement ? inputElement.value.trim() : '');
        
        if (!message) return;
        
        // Display user message
        MessageHandler.addMessage({
            content: message,
            role: 'user',
            timestamp: new Date().toISOString(),
            shouldScroll: true
        });
        
        // Clear input
        if (inputElement && !messageText) {
            inputElement.value = '';
        }
        
        // Optional callback: message sent
        if (this.config.onMessageSent) {
            this.config.onMessageSent(message);
        }
        
        try {
            // Send to backend
            const response = await fetch(this.config.chatEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    include_context: this.config.includeContext,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            // Update session ID
            if (data.session_id) {
                this._updateSessionId(data.session_id);
            }
            
            // Display bot response
            if (data.response) {
                MessageHandler.addMessage({
                    content: data.response,
                    role: 'bot',
                    timestamp: new Date().toISOString(),
                    source: data.type || 'direct_ai',
                    shouldScroll: true
                });
            } else if (data.error) {
                this._displayError(data.error);
            }
            
            // Optional callback: response received
            if (this.config.onResponseReceived) {
                this.config.onResponseReceived(data);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this._displayError(this.config.errorMessage);
            
            // Optional callback: error
            if (this.config.onError) {
                this.config.onError(error);
            }
        }
    },
    
    /**
     * Load conversation history from backend
     */
    async loadHistory() {
        try {
            // Get session ID from cookie
            this.sessionId = this._getCookie(this.config.sessionCookieName);
            
            if (this.sessionId) {
                console.log(`Loading history for session: ${this.sessionId}`);
                
                // Use MessageHandler to load and display history
                const data = await MessageHandler.loadHistory(
                    this.sessionId, 
                    this.config.historyEndpoint
                );
                
                // Optional callback: history loaded
                if (this.config.onHistoryLoaded && data && data.messages) {
                    this.config.onHistoryLoaded(data.messages);
                }
            } else {
                console.log('No existing session found, starting new conversation');
            }
        } catch (error) {
            console.error('Error loading conversation history:', error);
        }
    },
    
    /**
     * Send a quick/preset message
     * 
     * @param {string} message - The message to send
     */
    sendQuickMessage(message) {
        const inputElement = document.getElementById(this.config.inputElementId);
        if (inputElement) {
            inputElement.value = message;
        }
        this.sendMessage(message);
    },
    
    /**
     * Update session ID and store in cookie
     * @private
     */
    _updateSessionId(newSessionId) {
        const isNewSession = !this.sessionId;
        this.sessionId = newSessionId;
        this._setCookie(this.config.sessionCookieName, newSessionId);
        console.log(isNewSession ? `🆕 New session: ${newSessionId}` : `🔄 Session updated: ${newSessionId}`);
        
        // Optional callback: session created
        if (isNewSession && this.config.onSessionCreated) {
            this.config.onSessionCreated(newSessionId);
        }
    },
    
    /**
     * Display an error message
     * @private
     */
    _displayError(errorText) {
        MessageHandler.addMessage({
            content: errorText,
            role: 'bot',
            shouldScroll: true
        });
    },
    
    /**
     * Get cookie value
     * @private
     */
    _getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },
    
    /**
     * Set cookie value
     * @private
     */
    _setCookie(name, value, days = 365) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    }
};

// Make available globally for inline event handlers
window.ConversationBox = ConversationBox;

// Convenience function for quick messages (backward compatibility)
function sendQuickMessage(message) {
    if (window.ConversationBox) {
        ConversationBox.sendQuickMessage(message);
    }
}
