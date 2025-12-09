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
    sessionId: null,  // Now from database, not cookies
    userId: null,  // NEW: User ID from authentication
    config: {
        inputElementId: 'userInput',
        sendButtonId: 'sendBtn',
        chatEndpoint: null,  // e.g., '/scientist/chat'
        historyEndpoint: null,  // e.g., '/scientist/history'
        sessionEndpoint: null,  // NEW: e.g., '/scientist/session'
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
            sessionEndpoint: config.sessionEndpoint || `/${characterId}/session`  // NEW
        };
        
        // Set up event listeners
        this._setupEventListeners();
        
        // Get authenticated session from backend, then load history
        this._getAuthenticatedSession().then(() => {
            this.loadHistory();
        }).catch(error => {
            console.error('Failed to initialize session:', error);
        });
        
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
        
        // Clear input after sending
        if (inputElement) {
            inputElement.value = '';
        }
        
        // Optional callback: message sent
        if (this.config.onMessageSent) {
            this.config.onMessageSent(message);
        }
        
        try {
            // Send to backend using AuthHelper for Smart Response authentication
            // No need to send session_id - backend gets it from user_id + character_id
            const response = await AuthHelper.authenticatedFetch(this.config.chatEndpoint, {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    include_context: this.config.includeContext
                })
            });
            
            const data = await response.json();
            
            // Session ID comes from backend (no need to update cookies)
            if (data.session_id && !this.sessionId) {
                this.sessionId = data.session_id;
                console.log(`🆕 Session ID: ${this.sessionId}`);
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
     * Get authenticated session from backend (database-backed)
     * @private
     */
    async _getAuthenticatedSession() {
        try {
            // Call backend to get session for this user+character
            const response = await AuthHelper.authenticatedFetch(this.config.sessionEndpoint, {
                method: 'GET'
            });
            
            const data = await response.json();
            
            if (data.session_id) {
                this.sessionId = data.session_id;
                this.userId = data.user_id;
                console.log(`✓ Session loaded: ${this.sessionId} for user ${this.userId}, character ${this.characterId}`);
                
                // Optional callback: session created
                if (this.config.onSessionCreated) {
                    this.config.onSessionCreated(this.sessionId);
                }
            } else {
                console.error('Failed to get session:', data.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Error getting authenticated session:', error);
            // User not authenticated - session will be null
            this.sessionId = null;
            this.userId = null;
        }
    },
    
    /**
     * Load conversation history from backend (database-backed)
     */
    async loadHistory() {
        try {
            if (!this.sessionId) {
                console.log('No session available, skipping history load');
                return;
            }
            
            console.log(`Loading history for user ${this.userId}, character ${this.characterId}`);
            
            // Call backend - no need to pass session_id, backend gets it from auth
            const response = await AuthHelper.authenticatedFetch(this.config.historyEndpoint, {
                method: 'GET'
            });
            
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                // Clear existing messages
                MessageHandler.messagesContainer.innerHTML = '';
                
                // Display each message
                data.messages.forEach(msg => {
                    MessageHandler.addMessage({
                        content: msg.content,
                        role: msg.sender_type,  // 'user' or 'assistant'
                        timestamp: msg.timestamp,
                        source: msg.metadata?.source,
                        shouldScroll: false
                    });
                });
                
                // Scroll to bottom after all messages loaded
                MessageHandler.messagesContainer.scrollTop = MessageHandler.messagesContainer.scrollHeight;
                console.log(`✓ Loaded ${data.messages.length} messages from database`);
                
                // Optional callback: history loaded
                if (this.config.onHistoryLoaded) {
                    this.config.onHistoryLoaded(data.messages);
                }
            } else {
                console.log('No conversation history found, starting new conversation');
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
        // Send directly without setting input value (more efficient)
        // Input will be cleared by sendMessage() after sending
        this.sendMessage(message);
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
