/**
 * Character Chat Helper - Centralized UI utilities for character chat
 * Eliminates code duplication across 8+ character templates
 * 
 * Usage:
 * 1. Include AFTER auth_helper.js:
 *    <script src="/static/auth_helper.js"></script>
 *    <script src="/static/character_chat_helper.js"></script>
 * 
 * 2. Use helper methods instead of duplicating code
 */

const CharacterChatHelper = {
    
    /**
     * Add a message to the chat interface
     * Handles message rendering with auto-scroll
     * 
     * @param {string} containerId - ID of chat messages container
     * @param {string} text - Message text
     * @param {string} sender - 'user' or 'bot'/'assistant'
     * @param {object} options - Optional configuration
     * @param {string} options.messageClass - Custom message wrapper class (default: 'message')
     * @param {string} options.bubbleClass - Custom bubble class (default: 'message-bubble')
     * @param {string} options.userAvatar - User avatar/emoji (default: '👤')
     * @param {string} options.botAvatar - Bot avatar/emoji (default: '🤖')
     * @param {boolean} options.autoScroll - Auto-scroll to bottom (default: true)
     * @param {string} options.timestamp - Show timestamp (default: auto-generate)
     * 
     * @example
     * CharacterChatHelper.addMessage('chatMessages', 'Hello!', 'user');
     * CharacterChatHelper.addMessage('chatMessages', 'Hi there!', 'bot', {
     *     botAvatar: '🍃',
     *     messageClass: 'sage-message'
     * });
     */
    addMessage(containerId, text, sender, options = {}) {
        const defaults = {
            messageClass: 'message',
            bubbleClass: 'message-bubble',
            userAvatar: '👤',
            botAvatar: '🤖',
            autoScroll: true,
            timestamp: null,
            messageId: null
        };
        
        const config = { ...defaults, ...options };
        const messagesDiv = document.getElementById(containerId);
        
        if (!messagesDiv) {
            console.error(`Container '${containerId}' not found`);
            return null;
        }
        
        // Create message wrapper
        const messageDiv = document.createElement('div');
        messageDiv.className = `${config.messageClass} ${sender}`;
        if (config.messageId) {
            messageDiv.id = config.messageId;
        }
        
        // Create message bubble
        const bubble = document.createElement('div');
        bubble.className = config.bubbleClass;
        
        // Add avatar
        const avatar = sender === 'user' ? config.userAvatar : config.botAvatar;
        if (avatar) {
            const avatarSpan = document.createElement('span');
            avatarSpan.className = 'message-avatar';
            avatarSpan.textContent = avatar;
            messageDiv.appendChild(avatarSpan);
        }
        
        // Add text content
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;
        bubble.appendChild(textDiv);
        
        // Add timestamp if configured
        if (config.timestamp !== false) {
            const time = config.timestamp || new Date().toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = time;
            bubble.appendChild(timeDiv);
        }
        
        messageDiv.appendChild(bubble);
        messagesDiv.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        if (config.autoScroll) {
            this.scrollToBottom(containerId);
        }
        
        return messageDiv;
    },
    
    /**
     * Scroll chat container to bottom
     * @param {string} containerId - ID of chat messages container
     * @param {boolean} smooth - Use smooth scrolling (default: false)
     */
    scrollToBottom(containerId, smooth = false) {
        const container = document.getElementById(containerId);
        if (container) {
            if (smooth) {
                container.scrollTo({
                    top: container.scrollHeight,
                    behavior: 'smooth'
                });
            } else {
                container.scrollTop = container.scrollHeight;
            }
        }
    },
    
    /**
     * Show typing indicator
     * @param {string} indicatorId - ID of typing indicator element
     * @param {string} chatContainerId - ID of chat container (for auto-scroll)
     */
    showTyping(indicatorId, chatContainerId = null) {
        const indicator = document.getElementById(indicatorId);
        if (indicator) {
            indicator.style.display = 'block';
            if (chatContainerId) {
                this.scrollToBottom(chatContainerId);
            }
        }
    },
    
    /**
     * Hide typing indicator
     * @param {string} indicatorId - ID of typing indicator element
     */
    hideTyping(indicatorId) {
        const indicator = document.getElementById(indicatorId);
        if (indicator) {
            indicator.style.display = 'none';
        }
    },
    
    /**
     * Handle chat errors with consistent messaging
     * @param {Error} error - The error object
     * @param {string} characterName - Character name for logging
     * @param {string} chatContainerId - Where to show error message
     * @param {string} customMessage - Custom error message (optional)
     */
    handleChatError(error, characterName, chatContainerId, customMessage = null) {
        console.error(`[${characterName}] Chat error:`, error);
        
        // Default error messages by character type
        const defaultMessages = {
            'coach': 'Hold on, let me refocus! Try again in a moment. 💪',
            'sage': 'The path wavers for a moment. Please try again when the time is right. 🍃',
            'marcus': 'Even in adversity, we persist. Please try your message again.',
            'psychologist': 'I apologize, but I had trouble processing that. Please try again.',
            'zen_master': 'The path to understanding requires patience. Please try again.',
            'scientist': 'Error in data transmission. Recalibrating...',
            'business_coach': 'Technical difficulty. Let\'s regroup and try again.',
            'life_coach': 'Hold on, let me reconnect with my energy! Try again. ✨',
            'default': 'I encountered an issue. Please try again.'
        };
        
        const message = customMessage || defaultMessages[characterName] || defaultMessages['default'];
        
        if (chatContainerId) {
            this.addMessage(chatContainerId, message, 'bot');
        }
        
        // TODO: Send error to server for logging
        // this.logErrorToServer(error, characterName);
    },
    
    /**
     * Send a chat message with authentication and error handling
     * Combines AuthHelper + error handling in one call
     * 
     * @param {string} endpoint - Chat endpoint (e.g., '/coach/chat')
     * @param {string} message - User's message
     * @param {string} characterName - Character identifier
     * @param {object} options - Additional options
     * @returns {Promise<object>} Response data
     */
    async sendChatMessage(endpoint, message, characterName, options = {}) {
        const defaults = {
            includeContext: true,
            onSuccess: null,
            onError: null,
            chatContainerId: null,
            typingIndicatorId: null
        };
        
        const config = { ...defaults, ...options };
        
        try {
            // Show typing if configured
            if (config.typingIndicatorId) {
                this.showTyping(config.typingIndicatorId, config.chatContainerId);
            }
            
            // Use AuthHelper for authenticated request
            const response = await AuthHelper.authenticatedFetch(endpoint, {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    include_context: config.includeContext
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Hide typing
            if (config.typingIndicatorId) {
                this.hideTyping(config.typingIndicatorId);
            }
            
            // Call success callback if provided
            if (config.onSuccess) {
                config.onSuccess(data);
            }
            
            return data;
            
        } catch (error) {
            // Hide typing on error
            if (config.typingIndicatorId) {
                this.hideTyping(config.typingIndicatorId);
            }
            
            // Handle error
            if (config.onError) {
                config.onError(error);
            } else {
                this.handleChatError(error, characterName, config.chatContainerId);
            }
            
            throw error;
        }
    },
    
    /**
     * Load data from an endpoint and display in element
     * Useful for daily insights, stats, etc.
     * 
     * @param {string} endpoint - API endpoint
     * @param {string} elementId - Element to update
     * @param {string} dataKey - Key in response JSON (e.g., 'insight', 'wisdom')
     * @param {string} fallbackText - Text to show on error
     */
    async loadCharacterData(endpoint, elementId, dataKey = null, fallbackText = '') {
        try {
            const response = await fetch(endpoint);
            const data = await response.json();
            
            const element = document.getElementById(elementId);
            if (element) {
                // If dataKey specified, extract that field, otherwise use whole response
                const content = dataKey ? data[dataKey] : data;
                element.textContent = content || fallbackText;
            }
        } catch (error) {
            console.error(`Error loading from ${endpoint}:`, error);
            const element = document.getElementById(elementId);
            if (element && fallbackText) {
                element.textContent = fallbackText;
            }
        }
    },
    
    /**
     * Update a stat counter element
     * @param {string} elementId - Element to update
     * @param {number|string} value - New value
     */
    updateStat(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    },
    
    /**
     * Clear all messages from chat
     * @param {string} containerId - Chat container ID
     */
    clearChat(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
        }
    },
    
    /**
     * Enable/disable input controls during processing
     * @param {string} inputId - Input element ID
     * @param {string} buttonId - Send button ID
     * @param {boolean} enabled - Enable or disable
     */
    setInputEnabled(inputId, buttonId, enabled) {
        const input = document.getElementById(inputId);
        const button = document.getElementById(buttonId);
        
        if (input) input.disabled = !enabled;
        if (button) button.disabled = !enabled;
    }
};

// Make available globally
window.CharacterChatHelper = CharacterChatHelper;
