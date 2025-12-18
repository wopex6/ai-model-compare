/**
 * Unified Message Handler for All Characters
 * Handles display and interaction with messages consistently across all character chats
 * 
 * Usage:
 * 1. Include: <script src="/static/message_handler.js"></script>
 * 2. Initialize: MessageHandler.init('character-name', {theme config})
 * 3. Display: MessageHandler.addMessage({content, role, timestamp, source})
 * 4. Load history: MessageHandler.loadHistory(sessionId)
 */

const MessageHandler = {
    // Configuration
    characterName: null,
    theme: null,
    messagesContainer: null,
    
    /**
     * Initialize the message handler for a specific character
     * @param {string} characterName - Character identifier (e.g., 'scientist', 'coach')
     * @param {object} theme - Theme configuration {userColor, botColor, gradient, etc.}
     */
    init(characterName, theme = {}) {
        this.characterName = characterName;
        this.theme = {
            userColor: theme.userColor || '#00695C',
            botColor: theme.botColor || '#26A69A',
            userGradient: theme.userGradient || 'linear-gradient(135deg, #00695C, #26A69A)',
            botBackground: theme.botBackground || 'rgba(38, 166, 154, 0.15)',
            userTimestampColor: '#FFFFFF',  // White - high contrast on colored backgrounds
            botTimestampColor: '#888',      // Gray - subtle
            messageClass: theme.messageClass || 'message',  // Allow custom message class
            bubbleClass: theme.bubbleClass || 'message-bubble',  // Allow custom bubble class
            characterDisplayName: theme.characterDisplayName || 'Assistant',
            ...theme
        };
        this.messagesContainer = document.getElementById('chatMessages') || document.getElementById('chat-messages');
        
        console.log(`✅ MessageHandler initialized for ${characterName}`);
    },
    
    /**
     * Add a message to the chat display
     * UNIVERSAL: Works for all characters, all message types
     * 
     * @param {object} options - Message options
     * @param {string} options.content - Message text content
     * @param {string} options.role - 'user' or 'assistant' (or 'bot')
     * @param {string} options.timestamp - ISO timestamp (optional)
     * @param {string} options.source - 'smart_response' or 'direct_ai' (optional, for debugging)
     * @param {boolean} options.shouldScroll - Auto-scroll to bottom (default: true)
     * @param {object} options.metadata - Additional metadata (optional)
     */
    addMessage({
        content,
        role,
        timestamp = null,
        source = null,
        shouldScroll = true,
        metadata = {}
    }) {
        if (!this.messagesContainer) {
            console.error('❌ MessageHandler: messagesContainer not found');
            return;
        }
        
        // Normalize role: 'assistant' or 'bot' → 'bot', 'user' → 'user'
        const sender = (role === 'assistant' || role === 'bot') ? 'bot' : 'user';
        
        // Create message container
        const messageDiv = document.createElement('div');
        messageDiv.className = `${this.theme.messageClass} ${sender}`;
        messageDiv.dataset.role = role;
        if (source) messageDiv.dataset.source = source;
        
        // Create message bubble
        const bubble = document.createElement('div');
        bubble.className = this.theme.bubbleClass;
        
        // Format timestamp - show date for non-today messages
        let timeStr = '';
        if (timestamp) {
            const date = new Date(timestamp);
            const today = new Date();
            const isToday = date.toDateString() === today.toDateString();
            
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            const timeOnly = `${hours}:${minutes}`;
            
            // Show date for non-today messages
            let displayTime = timeOnly;
            if (!isToday) {
                const day = date.getDate().toString().padStart(2, '0');
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                displayTime = `${day}/${month} ${timeOnly}`;
            }
            
            const color = sender === 'user' ? this.theme.userTimestampColor : this.theme.botTimestampColor;
            timeStr = `<span class="timestamp" style="font-size: 0.75em; color: ${color}; margin-left: 8px;">${displayTime}</span>`;
        }
        
        // Add source badge if provided (for debugging/transparency)
        let sourceBadge = '';
        if (source && sender === 'bot') {
            // Check if message is from Smart Response (quick_reply or smart_response)
            const isSmartResponse = source === 'smart_response' || source === 'quick_reply' || source.includes('smart_response');
            const badgeText = isSmartResponse ? 'SR' : 'AI';
            const badgeTitle = isSmartResponse ? 'Smart Response' : 'Direct AI';
            sourceBadge = `<span class="source-badge" style="font-size: 0.65em; opacity: 0.5; margin-left: 4px;" title="${badgeTitle}">[${badgeText}]</span>`;
        }
        
        // Format message content
        const senderLabel = sender === 'bot' ? `<strong>${this.getBotDisplayName()}:</strong>` : '<strong>You:</strong>';
        bubble.innerHTML = `${senderLabel} ${content}${sourceBadge}${timeStr}`;
        
        messageDiv.appendChild(bubble);
        this.messagesContainer.appendChild(messageDiv);
        
        // Debug log
        const preview = content.substring(0, 30);
        console.log(`✅ Added ${sender} message to DOM: "${preview}..." ${source ? `[${source}]` : ''}`);
        
        // Auto-scroll
        if (shouldScroll) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    },
    
    /**
     * Get bot display name for current character
     * @returns {string} Display name
     */
    getBotDisplayName() {
        // Use theme config if provided, otherwise fallback to defaults
        return this.theme.characterDisplayName || 'Assistant';
    },
    
    /**
     * Load and display conversation history
     * UNIVERSAL: Works for all message types (Smart Response, Direct AI, etc.)
     * 
     * @param {string} sessionId - Session ID to load
     * @param {string} endpoint - API endpoint (e.g., '/scientist/history')
     * @returns {Promise<object>} History data
     */
    async loadHistory(sessionId, endpoint) {
        if (!sessionId) {
            console.log('No existing session found, starting new conversation');
            return { messages: [] };
        }
        
        try {
            console.log(`Loading history for session: ${sessionId}`);
            
            const response = await fetch(`${endpoint}?session_id=${sessionId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                console.log(`Loaded ${data.messages.length} messages from history`);
                
                // Debug: Show breakdown
                const userMsgs = data.messages.filter(m => m.role === 'user').length;
                const assistantMsgs = data.messages.filter(m => m.role === 'assistant').length;
                console.log(`📊 Message breakdown: User: ${userMsgs}, Assistant: ${assistantMsgs}`);
                
                // Clear any welcome message
                this.messagesContainer.innerHTML = '';
                
                // Display all messages using unified handler
                data.messages.forEach((msg, index) => {
                    const preview = msg.content.substring(0, 50);
                    console.log(`   ${index + 1}. [${msg.role}] ${preview}...`);
                    
                    this.addMessage({
                        content: msg.content,
                        role: msg.role,
                        timestamp: msg.timestamp || new Date().toISOString(),
                        source: msg.metadata?.source || null,
                        shouldScroll: false  // Don't scroll for each message
                    });
                });
                
                // Scroll to bottom once
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            } else {
                console.log('No messages in history');
            }
            
            return data;
        } catch (error) {
            console.error('Error loading conversation history:', error);
            return { messages: [] };
        }
    },
    
    /**
     * Clear all messages from display
     */
    clearMessages() {
        if (this.messagesContainer) {
            this.messagesContainer.innerHTML = '';
        }
    },
    
    /**
     * Setup textarea for multi-line input (max 6 lines)
     * Enter = newline, Shift+Enter = send
     * Call this once - applies to userInput element
     * 
     * @param {function} sendCallback - Function to call when sending (e.g., sendMessage)
     * @param {string} inputId - Input element ID (default: 'userInput')
     */
    setupMultiLineInput(sendCallback, inputId = 'userInput') {
        const input = document.getElementById(inputId);
        if (!input) return;
        
        // Configure for multi-line (max 6 lines)
        input.style.resize = 'none';
        input.style.overflow = 'hidden';
        input.style.minHeight = '40px';
        input.style.maxHeight = '144px'; // ~6 lines
        input.style.lineHeight = '24px';
        if (input.tagName === 'TEXTAREA') {
            input.rows = 1;
        }
        
        // Remove any inline onkeypress handler
        input.removeAttribute('onkeypress');
        
        // Auto-expand as user types
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            const maxHeight = 144;
            input.style.height = Math.min(input.scrollHeight, maxHeight) + 'px';
            input.style.overflow = input.scrollHeight > maxHeight ? 'auto' : 'hidden';
        });
        
        // Enter = newline, Shift+Enter = send
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault();
                if (sendCallback) sendCallback();
            }
            // Plain Enter = newline (default)
        });
        
        console.log('✅ Multi-line input configured (Enter=newline, Shift+Enter=send)');
    }
};

// Auto-setup multi-line input on page load (finds userInput and sendMessage automatically)
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const input = document.getElementById('userInput');
        if (input && typeof sendMessage === 'function') {
            MessageHandler.setupMultiLineInput(sendMessage);
        }
    }, 100); // Small delay to ensure sendMessage is defined
});
