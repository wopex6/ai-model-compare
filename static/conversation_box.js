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
 * - Conversation search
 * - Auto-scroll to latest messages
 */

const ConversationBox = {
    // Configuration
    characterId: null,
    sessionId: null,  // Now from database, not cookies
    userId: null,  // NEW: User ID from authentication
    searchVisible: false,  // Search bar visibility state
    allMessages: [],  // Store all messages for search
    config: {
        inputElementId: 'userInput',
        sendButtonId: 'sendBtn',
        chatEndpoint: null,  // e.g., '/scientist/chat'
        historyEndpoint: null,  // e.g., '/scientist/history'
        sessionEndpoint: null,  // NEW: e.g., '/scientist/session'
        includeContext: true,
        errorMessage: 'I apologize, but I encountered an error. Please try again.',
        enableSearch: true,  // Enable search functionality
        
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
        
        // Create search UI if enabled
        if (this.config.enableSearch) {
            this._createSearchUI();
        }
        
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
        
        // Configure textarea for multi-line input (max 6 lines)
        inputElement.style.resize = 'none';
        inputElement.style.overflow = 'hidden';
        inputElement.style.minHeight = '40px';
        inputElement.style.maxHeight = '144px'; // ~6 lines at 24px line height
        inputElement.rows = 1;
        
        // Auto-expand textarea as user types (up to 6 lines)
        inputElement.addEventListener('input', () => {
            inputElement.style.height = 'auto';
            const maxHeight = 144; // 6 lines
            inputElement.style.height = Math.min(inputElement.scrollHeight, maxHeight) + 'px';
            if (inputElement.scrollHeight > maxHeight) {
                inputElement.style.overflow = 'auto';
            } else {
                inputElement.style.overflow = 'hidden';
            }
        });
        
        // Enter = newline, Shift+Enter = send message
        inputElement.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
            // Plain Enter allows newline (default behavior)
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
                        role: msg.sender_type === 'assistant' ? 'bot' : msg.sender_type,  // Convert 'assistant' to 'bot'
                        timestamp: msg.timestamp,
                        source: msg.metadata?.source,
                        shouldScroll: false
                    });
                });
                
                // Apply stored highlights after messages are loaded
                if (MessageHandler.highlightsEnabled) {
                    setTimeout(() => MessageHandler.applyStoredHighlights(), 100);
                }
                
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
     * Reload history with provided data (used by goToMessage for loading older history)
     * @param {Array} messages - Messages data from API
     * @param {string} characterId - Character ID
     */
    async _reloadHistoryWithData(messages, characterId) {
        // Clear existing messages
        MessageHandler.messagesContainer.innerHTML = '';
        
        // Display each message
        messages.forEach(msg => {
            MessageHandler.addMessage({
                content: msg.content,
                role: msg.sender_type === 'assistant' ? 'bot' : msg.sender_type,
                timestamp: msg.timestamp,
                source: msg.metadata?.source,
                shouldScroll: false
            });
        });
        
        console.log(`✓ Reloaded ${messages.length} messages for pinned message navigation`);
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
    },
    
    /**
     * Create search UI elements
     * @private
     */
    _createSearchUI() {
        const messagesContainer = MessageHandler.messagesContainer;
        if (!messagesContainer) return;
        
        // Find or create container for search bar (insert before messages container)
        const chatContainer = messagesContainer.parentElement;
        if (!chatContainer) return;
        
        // Create search bar container
        const searchBar = document.createElement('div');
        searchBar.id = 'conversation-search-bar';
        searchBar.className = 'conversation-search-bar';
        searchBar.style.cssText = `
            display: none;
            padding: 10px 15px;
            background: #f5f5f5;
            border-bottom: 1px solid #ddd;
            position: sticky;
            top: 0;
            z-index: 100;
        `;
        searchBar.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <input type="text" id="conversation-search-input" placeholder="Search messages..." 
                    style="flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 20px; outline: none; font-size: 14px;">
                <span id="search-results-count" style="font-size: 12px; color: #666; min-width: 60px;"></span>
                <button id="search-prev-btn" style="padding: 5px 10px; border: none; background: #e0e0e0; border-radius: 4px; cursor: pointer;" title="Previous">▲</button>
                <button id="search-next-btn" style="padding: 5px 10px; border: none; background: #e0e0e0; border-radius: 4px; cursor: pointer;" title="Next">▼</button>
                <button id="search-close-btn" style="padding: 5px 10px; border: none; background: #e0e0e0; border-radius: 4px; cursor: pointer;" title="Close">✕</button>
            </div>
        `;
        
        // Insert search bar at the top of chat container
        chatContainer.insertBefore(searchBar, messagesContainer);
        
        // Create search toggle button (floating) - only if no header search button exists
        const headerSearchBtn = document.getElementById('searchBtn');
        if (!headerSearchBtn) {
            const searchToggle = document.createElement('button');
            searchToggle.id = 'search-toggle-btn';
            searchToggle.innerHTML = '🔍';
            searchToggle.title = 'Search conversations (Ctrl+F)';
            searchToggle.style.cssText = `
                position: absolute;
                top: 60px;
                right: 15px;
                padding: 8px 12px;
                border: none;
                background: rgba(255,255,255,0.9);
                border-radius: 20px;
                cursor: pointer;
                font-size: 14px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                z-index: 99;
                transition: all 0.2s;
            `;
            searchToggle.addEventListener('mouseenter', () => {
                searchToggle.style.background = 'rgba(255,255,255,1)';
                searchToggle.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
            });
            searchToggle.addEventListener('mouseleave', () => {
                searchToggle.style.background = 'rgba(255,255,255,0.9)';
                searchToggle.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
            });
            
            // Make chat container position relative for absolute positioning
            chatContainer.style.position = 'relative';
            chatContainer.appendChild(searchToggle);
        }
        
        // Set up search event listeners
        this._setupSearchListeners();
    },
    
    /**
     * Set up search event listeners
     * @private
     */
    _setupSearchListeners() {
        const searchInput = document.getElementById('conversation-search-input');
        const searchBar = document.getElementById('conversation-search-bar');
        const searchToggle = document.getElementById('search-toggle-btn');
        const prevBtn = document.getElementById('search-prev-btn');
        const nextBtn = document.getElementById('search-next-btn');
        const closeBtn = document.getElementById('search-close-btn');
        
        if (!searchInput || !searchBar || !searchToggle) return;
        
        // Toggle search bar
        searchToggle.addEventListener('click', () => this.toggleSearch());
        
        // Close search
        closeBtn?.addEventListener('click', () => this.closeSearch());
        
        // Search on input
        searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));
        
        // Navigate results
        prevBtn?.addEventListener('click', () => this.navigateSearch(-1));
        nextBtn?.addEventListener('click', () => this.navigateSearch(1));
        
        // Enter key navigates to next result
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.navigateSearch(e.shiftKey ? -1 : 1);
            } else if (e.key === 'Escape') {
                this.closeSearch();
            }
        });
        
        // Ctrl+F to open search
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                // Only intercept if we're on a character page with ConversationBox
                if (this.characterId && MessageHandler.messagesContainer) {
                    e.preventDefault();
                    this.toggleSearch(true);
                }
            }
        });
    },
    
    /**
     * Toggle search bar visibility
     * @param {boolean} forceOpen - Force open if true
     */
    toggleSearch(forceOpen = false) {
        const searchBar = document.getElementById('conversation-search-bar');
        const searchInput = document.getElementById('conversation-search-input');
        
        if (!searchBar) return;
        
        this.searchVisible = forceOpen || !this.searchVisible;
        searchBar.style.display = this.searchVisible ? 'block' : 'none';
        
        if (this.searchVisible && searchInput) {
            searchInput.focus();
            searchInput.select();
        } else {
            this.clearSearchHighlights();
        }
    },
    
    /**
     * Close search bar
     */
    closeSearch() {
        const searchBar = document.getElementById('conversation-search-bar');
        const searchInput = document.getElementById('conversation-search-input');
        
        if (searchBar) {
            searchBar.style.display = 'none';
            this.searchVisible = false;
        }
        if (searchInput) {
            searchInput.value = '';
        }
        this.clearSearchHighlights();
        this.searchResults = [];
        this.currentSearchIndex = -1;
    },
    
    // Search state
    searchResults: [],
    currentSearchIndex: -1,
    
    /**
     * Perform search in messages
     * @param {string} query - Search query
     */
    performSearch(query) {
        this.clearSearchHighlights();
        this.searchResults = [];
        this.currentSearchIndex = -1;
        
        const resultsCount = document.getElementById('search-results-count');
        
        if (!query || query.length < 2) {
            if (resultsCount) resultsCount.textContent = '';
            return;
        }
        
        const messages = MessageHandler.messagesContainer?.querySelectorAll('.message-bubble, .message-content');
        if (!messages) return;
        
        const queryLower = query.toLowerCase();
        
        messages.forEach((bubble, index) => {
            const text = bubble.textContent.toLowerCase();
            if (text.includes(queryLower)) {
                this.searchResults.push(bubble);
                this._highlightText(bubble, query);
            }
        });
        
        if (resultsCount) {
            resultsCount.textContent = this.searchResults.length > 0 
                ? `${this.searchResults.length} found` 
                : 'No results';
        }
        
        // Navigate to first result
        if (this.searchResults.length > 0) {
            this.navigateSearch(1);
        }
    },
    
    /**
     * Highlight search text in element
     * @private
     */
    _highlightText(element, query) {
        // Store original HTML if not already stored
        if (!element.dataset.originalHtml) {
            element.dataset.originalHtml = element.innerHTML;
        }
        
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        element.innerHTML = element.dataset.originalHtml.replace(regex, 
            '<mark style="background: #ffeb3b; padding: 0 2px; border-radius: 2px;">$1</mark>');
    },
    
    /**
     * Clear all search highlights
     */
    clearSearchHighlights() {
        const messages = MessageHandler.messagesContainer?.querySelectorAll('.message-bubble, .message-content');
        if (!messages) return;
        
        messages.forEach(bubble => {
            if (bubble.dataset.originalHtml) {
                bubble.innerHTML = bubble.dataset.originalHtml;
                delete bubble.dataset.originalHtml;
            }
            bubble.style.outline = '';
        });
    },
    
    /**
     * Navigate through search results
     * @param {number} direction - 1 for next, -1 for previous
     */
    navigateSearch(direction) {
        if (this.searchResults.length === 0) return;
        
        // Remove current highlight
        if (this.currentSearchIndex >= 0 && this.searchResults[this.currentSearchIndex]) {
            this.searchResults[this.currentSearchIndex].style.outline = '';
        }
        
        // Calculate new index
        this.currentSearchIndex += direction;
        if (this.currentSearchIndex >= this.searchResults.length) {
            this.currentSearchIndex = 0;
        } else if (this.currentSearchIndex < 0) {
            this.currentSearchIndex = this.searchResults.length - 1;
        }
        
        // Highlight and scroll to current result
        const current = this.searchResults[this.currentSearchIndex];
        if (current) {
            current.style.outline = '2px solid #ff9800';
            current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        // Update count display
        const resultsCount = document.getElementById('search-results-count');
        if (resultsCount) {
            resultsCount.textContent = `${this.currentSearchIndex + 1}/${this.searchResults.length}`;
        }
    },
    
    /**
     * Scroll to bottom of messages (latest messages)
     */
    scrollToBottom() {
        if (MessageHandler.messagesContainer) {
            MessageHandler.messagesContainer.scrollTop = MessageHandler.messagesContainer.scrollHeight;
        }
    },
    
    /**
     * Initialize search UI only (for pages that don't use full ConversationBox.init)
     * Call this after MessageHandler.init() to add search to any chat interface
     */
    initSearchOnly() {
        if (this.config.enableSearch) {
            this._createSearchUI();
        }
        console.log('✅ ConversationBox search initialized (standalone)');
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
