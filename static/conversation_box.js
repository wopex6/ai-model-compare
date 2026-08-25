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
        offlineMessage: 'You appear to be offline. Please connect to the internet and try again.',
        pendingStorageKey: null,  // localStorage key for unsent messages; defaults to drHealth.pending.<characterId>.v1
        enableSearch: true,  // Enable search functionality
        
        // Optional UI callbacks
        onMessageSent: null,  // Called after user message sent: (message) => {}
        onResponseReceived: null,  // Called after bot response: (data) => {}
        onError: null,  // Called on error: (error) => {}
        onSessionCreated: null,  // Called when new session created: (sessionId) => {}
        onHistoryLoaded: null,  // Called after history loaded: (messages) => {}
        localCache: false,       // Store conversation in localStorage for offline use
        localStorageKey: null    // localStorage key; defaults to drHealth.conversation.<characterId>.v1
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
        
        // Inject response-action button styles if not already present
        if (!document.getElementById('response-action-styles')) {
            const style = document.createElement('style');
            style.id = 'response-action-styles';
            style.textContent = `
                .response-actions { display: flex; gap: 6px; margin: 6px 0 8px 0; flex-wrap: wrap; }
                .response-action-btn { background: transparent; border: 1px solid rgba(255,255,255,0.2); border-radius: 14px; padding: 3px 10px; font-size: 0.75rem; color: rgba(255,255,255,0.5); cursor: pointer; transition: all 0.15s ease; line-height: 1.4; }
                .response-action-btn:hover { border-color: rgba(102,126,234,0.6); color: #8ea4f7; background: rgba(102,126,234,0.1); }
                .response-action-btn:active { transform: scale(0.97); }
                .too-long-btn { border-color: rgba(251,191,36,0.3); color: rgba(251,191,36,0.6); }
                .too-long-btn:hover { border-color: rgba(251,191,36,0.7); color: #fbbf24; background: rgba(251,191,36,0.1); }
                .too-short-btn { border-color: rgba(52,211,153,0.3); color: rgba(52,211,153,0.6); }
                .too-short-btn:hover { border-color: rgba(52,211,153,0.7); color: #34d399; background: rgba(52,211,153,0.1); }
                .clarification-card { background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 10px 14px; margin: 4px 0 8px 0; font-size: 0.9rem; color: #c4b5fd; }
                .clarification-card.critical { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.4); color: #fca5a5; }
                .clarification-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.7; margin-bottom: 4px; }
                .character-suggestion-bar { display: flex; align-items: center; gap: 8px; margin: 4px 0 8px 0; padding: 6px 12px; background: rgba(251,191,36,0.06); border: 1px solid rgba(251,191,36,0.2); border-radius: 10px; font-size: 0.75rem; color: rgba(251,191,36,0.8); flex-wrap: wrap; }
                .character-suggestion-bar a { color: #fbbf24; cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }
                .character-suggestion-bar a:hover { color: #fde68a; }
                .personalization-status { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; padding: 4px 0 6px 0; min-height: 22px; }
                .persona-chip { display: inline-flex; align-items: center; gap: 3px; padding: 2px 8px; border-radius: 10px; font-size: 0.68rem; background: rgba(102,126,234,0.1); border: 1px solid rgba(102,126,234,0.25); color: rgba(148,163,250,0.85); letter-spacing: 0.02em; }
                .persona-chip.emotion { background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.2); color: rgba(252,165,165,0.85); }
                .persona-chip.goal { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.2); color: rgba(110,231,183,0.85); }
                .persona-chip.verbosity { background: rgba(251,191,36,0.08); border-color: rgba(251,191,36,0.2); color: rgba(253,230,138,0.85); }
            `;
            document.head.appendChild(style);
        }
        
        // Create search UI if enabled
        if (this.config.enableSearch) {
            this._createSearchUI();
        }
        
        // Load local cache immediately so the app works offline
        if (this.config.localCache) {
            this._loadLocalHistory();
        }

        // Get authenticated session from backend, then load history
        this._getAuthenticatedSession().then(() => {
            this.loadHistory().then(() => {
                this._processPendingMessages();
            });
            this._loadPersonalizationStatus();
        }).catch(error => {
            console.error('Failed to initialize session:', error);
        });

        // Send any queued messages when the phone comes back online
        window.addEventListener('online', () => {
            console.log('Back online, processing pending messages...');
            if (!this.sessionId) {
                this._getAuthenticatedSession().then(() => this._processPendingMessages());
            } else {
                this._processPendingMessages();
            }
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
        let message = messageText || (inputElement ? inputElement.value.trim() : '');
        
        if (!message) return;

        // Optional callback: caller can transform message before display/send.
        if (this.config.beforeSend) {
            const transformed = this.config.beforeSend(message);
            if (transformed && typeof transformed === 'string') {
                message = transformed;
            }
        }
        
        // Display user message
        MessageHandler.addMessage({
            content: message,
            role: 'user',
            timestamp: new Date().toISOString(),
            shouldScroll: true
        });

        if (this.config.localCache) {
            this._appendLocalMessage({content: message, role: 'user', timestamp: new Date().toISOString()});
        }
        
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
            const payload = {
                message: message,
                include_context: this.config.includeContext
            };
            // Include action flags if set by response action buttons
            if (this._nextMessageFlags) {
                // Expire stale flags (>60s old)
                const age = Date.now() - (this._nextMessageFlags._ts || 0);
                if (age < 60000) {
                    const flags = {...this._nextMessageFlags};
                    delete flags._ts;
                    delete flags._auto;
                    Object.assign(payload, flags);
                }
                this._nextMessageFlags = null;
            }
            
            const response = await AuthHelper.authenticatedFetch(this.config.chatEndpoint, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            // Session ID comes from backend (no need to update cookies)
            if (data.session_id && !this.sessionId) {
                this.sessionId = data.session_id;
                console.log(`🆕 Session ID: ${this.sessionId}`);
            }
            
            // Display bot response
            if (data.response) {
                const isClarification = data.type === 'clarification';
                const isCritical      = isClarification && data.urgency === 'critical';

                if (isClarification) {
                    // Render as a distinct clarification card instead of a normal bubble
                    this._addClarificationCard(data.response, isCritical);
                } else {
                    MessageHandler.addMessage({
                        content: data.response,
                        role: 'bot',
                        timestamp: new Date().toISOString(),
                        source: data.type || 'direct_ai',
                        shouldScroll: true
                    });

                    if (this.config.localCache) {
                        this._appendLocalMessage({content: data.response, role: 'bot', timestamp: new Date().toISOString(), source: data.type || 'direct_ai'});
                    }

                    // Add response action buttons (only for normal AI responses)
                    this._addResponseActions();

                    // Show character suggestion if present
                    if (data.character_suggestion && data.character_suggestion.should_suggest !== false) {
                        this._addCharacterSuggestion(data.character_suggestion);
                    }
                }
            } else if (data.error) {
                this._displayError(data.error);
            }
            
            // Optional callback: response received
            if (this.config.onResponseReceived) {
                this.config.onResponseReceived(data);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);

            var isOffline = !navigator.onLine;
            if (isOffline) {
                this._addPendingMessage({content: message, timestamp: new Date().toISOString()});
                this._displayError(this.config.offlineMessage);
            } else {
                this._displayError(this.config.errorMessage);
            }

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
     * Get the localStorage key for this character
     * @private
     */
    _getLocalStorageKey() {
        return this.config.localStorageKey || `drHealth.conversation.${this.characterId}.v1`;
    },

    /**
     * Load conversation history from localStorage for offline use
     * @private
     */
    _loadLocalHistory() {
        try {
            const raw = localStorage.getItem(this._getLocalStorageKey());
            if (!raw) return;
            const messages = JSON.parse(raw);
            if (!Array.isArray(messages) || messages.length === 0) return;

            // Clear existing messages and render local history
            MessageHandler.messagesContainer.innerHTML = '';
            messages.forEach(msg => {
                MessageHandler.addMessage({
                    content: msg.content,
                    role: msg.role === 'assistant' ? 'bot' : (msg.role === 'bot' ? 'bot' : 'user'),
                    timestamp: msg.timestamp,
                    source: msg.source || null,
                    shouldScroll: false
                });
            });
            this.allMessages = messages;
            MessageHandler.messagesContainer.scrollTop = MessageHandler.messagesContainer.scrollHeight;
            console.log(`✓ Loaded ${messages.length} messages from localStorage`);
        } catch (error) {
            console.error('Error loading local conversation history:', error);
        }
    },

    /**
     * Save messages to localStorage
     * @private
     */
    _saveLocalMessages(messages) {
        try {
            const normalized = messages.map(msg => ({
                content: msg.content,
                role: msg.sender_type || msg.role || 'user',
                timestamp: msg.timestamp || new Date().toISOString(),
                source: msg.metadata?.source || msg.source || null
            }));
            localStorage.setItem(this._getLocalStorageKey(), JSON.stringify(normalized));
        } catch (error) {
            console.error('Error saving local conversation history:', error);
        }
    },

    /**
     * Append a single message to localStorage
     * @private
     */
    _appendLocalMessage(msg) {
        try {
            const key = this._getLocalStorageKey();
            const raw = localStorage.getItem(key);
            const messages = raw ? JSON.parse(raw) : [];
            messages.push({
                content: msg.content,
                role: msg.role,
                timestamp: msg.timestamp || new Date().toISOString(),
                source: msg.source || null
            });
            localStorage.setItem(key, JSON.stringify(messages));
        } catch (error) {
            console.error('Error appending local message:', error);
        }
    },

    _getPendingStorageKey() {
        return this.config.pendingStorageKey || `drHealth.pending.${this.characterId}.v1`;
    },

    _loadPendingMessages() {
        try {
            const raw = localStorage.getItem(this._getPendingStorageKey());
            return raw ? JSON.parse(raw) : [];
        } catch (error) {
            console.error('Error loading pending messages:', error);
            return [];
        }
    },

    _savePendingMessages(messages) {
        try {
            localStorage.setItem(this._getPendingStorageKey(), JSON.stringify(messages));
        } catch (error) {
            console.error('Error saving pending messages:', error);
        }
    },

    _addPendingMessage(msg) {
        const pending = this._loadPendingMessages();
        pending.push(msg);
        this._savePendingMessages(pending);
    },

    _removePendingMessage(msg) {
        const pending = this._loadPendingMessages().filter(p => p.timestamp !== msg.timestamp || p.content !== msg.content);
        this._savePendingMessages(pending);
    },

    async _processPendingMessages() {
        if (this._processingPending) return;
        this._processingPending = true;

        try {
            if (!this.sessionId) {
                console.log('No session available, skipping pending messages');
                return;
            }

            const pending = this._loadPendingMessages();
            if (pending.length === 0) return;
            if (!navigator.onLine) return;

            console.log(`Processing ${pending.length} pending messages...`);
            let sentAny = false;

            for (const msg of pending) {
                try {
                    await this._sendOnePending(msg);
                    this._removePendingMessage(msg);
                    sentAny = true;
                } catch (err) {
                    console.error('Failed to send pending message, will retry later:', err);
                    break;
                }
            }

            if (sentAny && 'Notification' in window && Notification.permission === 'granted') {
                try {
                    new Notification('Dr. Health', { body: 'A response is ready.' });
                } catch (_) {}
            }
        } finally {
            this._processingPending = false;
        }
    },

    async _sendOnePending(pending) {
        const payload = {
            message: pending.content,
            include_context: this.config.includeContext
        };

        const response = await AuthHelper.authenticatedFetch(this.config.chatEndpoint, {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.session_id && !this.sessionId) {
            this.sessionId = data.session_id;
        }

        if (data.response) {
            const isClarification = data.type === 'clarification';
            const isCritical = isClarification && data.urgency === 'critical';

            if (isClarification) {
                this._addClarificationCard(data.response, isCritical);
            } else {
                MessageHandler.addMessage({
                    content: data.response,
                    role: 'bot',
                    timestamp: new Date().toISOString(),
                    source: data.type || 'direct_ai',
                    shouldScroll: true
                });

                if (this.config.localCache) {
                    this._appendLocalMessage({content: data.response, role: 'bot', timestamp: new Date().toISOString(), source: data.type || 'direct_ai'});
                }

                this._addResponseActions();

                if (data.character_suggestion && data.character_suggestion.should_suggest !== false) {
                    this._addCharacterSuggestion(data.character_suggestion);
                }
            }

            if (this.config.onResponseReceived) {
                this.config.onResponseReceived(data);
            }
        } else if (data.error) {
            this._displayError(data.error);
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

                if (this.config.localCache) {
                    this._saveLocalMessages(data.messages);
                }

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
     * Add response action buttons ("Tell me more" / "Not what I meant") after a bot message
     * @private
     */
    _addResponseActions() {
        if (!MessageHandler.messagesContainer) return;
        
        const actionRow = document.createElement('div');
        actionRow.className = 'response-actions';
        
        const moreBtn = document.createElement('button');
        moreBtn.className = 'response-action-btn more-detail-btn';
        moreBtn.textContent = 'Tell me more';
        moreBtn.title = 'Get a more detailed response';
        moreBtn.addEventListener('click', () => {
            actionRow.remove();
            this._nextMessageFlags = { detail_requested: true, _ts: Date.now(), _auto: true };
            this.sendMessage('Could you elaborate on that?');
        });
        
        const redirectBtn = document.createElement('button');
        redirectBtn.className = 'response-action-btn redirect-btn';
        redirectBtn.textContent = 'Not what I meant';
        redirectBtn.title = 'Try a different approach';
        redirectBtn.addEventListener('click', () => {
            actionRow.remove();
            this._nextMessageFlags = { direction_change: true, _ts: Date.now() };
            const inputEl = document.getElementById(this.config.inputElementId);
            if (inputEl) {
                inputEl.value = "That's not quite what I meant. Let me clarify:";
                inputEl.focus();
                inputEl.setSelectionRange(inputEl.value.length, inputEl.value.length);
            }
        });
        
        const tooLongBtn = document.createElement('button');
        tooLongBtn.className = 'response-action-btn length-btn too-long-btn';
        tooLongBtn.textContent = 'Too long';
        tooLongBtn.title = 'Response was too detailed — prefer shorter answers';
        tooLongBtn.addEventListener('click', () => {
            actionRow.remove();
            this._nextMessageFlags = { _ts: Date.now() };
            // Signal preference and immediately request a shorter version
            this.sendMessage('Keep it shorter next time — can you give me a brief summary?');
        });

        const tooShortBtn = document.createElement('button');
        tooShortBtn.className = 'response-action-btn length-btn too-short-btn';
        tooShortBtn.textContent = 'Too short';
        tooShortBtn.title = 'Response was too brief — prefer more detail';
        tooShortBtn.addEventListener('click', () => {
            actionRow.remove();
            this._nextMessageFlags = { detail_requested: true, _ts: Date.now(), _auto: true };
            this.sendMessage('Could you elaborate on that in more detail?');
        });

        actionRow.appendChild(moreBtn);
        actionRow.appendChild(redirectBtn);
        actionRow.appendChild(tooLongBtn);
        actionRow.appendChild(tooShortBtn);
        MessageHandler.messagesContainer.appendChild(actionRow);
        MessageHandler.messagesContainer.scrollTop = MessageHandler.messagesContainer.scrollHeight;
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
     * Render a clarification/critical response as a distinct card
     * @private
     */
    _addClarificationCard(text, isCritical = false) {
        if (!MessageHandler.messagesContainer) return;
        const card = document.createElement('div');
        card.className = 'clarification-card' + (isCritical ? ' critical' : '');
        const label = document.createElement('div');
        label.className = 'clarification-label';
        label.textContent = isCritical ? 'Important' : 'Just to clarify';
        const body = document.createElement('div');
        body.textContent = text;
        card.appendChild(label);
        card.appendChild(body);
        MessageHandler.messagesContainer.appendChild(card);
        MessageHandler.messagesContainer.scrollTop = MessageHandler.messagesContainer.scrollHeight;
    },

    /**
     * Show a soft character-suggestion nudge bar below a response
     * @private
     */
    _addCharacterSuggestion(suggestion) {
        if (!MessageHandler.messagesContainer || !suggestion) return;
        if (!suggestion.message) return;
        const meta = encodeURIComponent(JSON.stringify({
            to: suggestion.character_id,
            need: suggestion.detected_need || '',
        }));
        const bar = document.createElement('div');
        bar.className = 'character-suggestion-bar';
        bar.innerHTML = `💡 ${suggestion.message.replace(
            suggestion.character_name,
            `<a onclick="ConversationBox._handleCharacterSwitch('${suggestion.character_id}','${meta}')">${suggestion.character_name}</a>`
        )}`;
        MessageHandler.messagesContainer.appendChild(bar);
        MessageHandler.messagesContainer.scrollTop = MessageHandler.messagesContainer.scrollHeight;
    },

    /**
     * Handle character switch suggestion click — report to backend then navigate
     * @private
     */
    async _handleCharacterSwitch(characterId, metaEncoded) {
        // Report the switch signal to the backend (non-blocking — don't wait)
        try {
            const meta = metaEncoded ? JSON.parse(decodeURIComponent(metaEncoded)) : {};
            AuthHelper.authenticatedFetch('/api/user/character-switch', {
                method: 'POST',
                body: JSON.stringify({
                    from_character: this.characterId || '',
                    to_character: characterId,
                    detected_need: meta.need || '',
                    suggestion_used: true,
                }),
            }).catch(() => {});  // Fire-and-forget
        } catch (_) {}

        if (this.config.onCharacterSwitch) {
            this.config.onCharacterSwitch(characterId);
        } else {
            window.location.href = `/${characterId}`;
        }
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
        
        if (!searchInput || !searchBar) return;
        
        // Toggle search bar (only if floating toggle exists)
        if (searchToggle) {
            searchToggle.addEventListener('click', () => this.toggleSearch());
        }
        
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
        let searchBar = document.getElementById('conversation-search-bar');
        
        // Create search UI if it doesn't exist (fallback)
        if (!searchBar) {
            this._createSearchUI();
            searchBar = document.getElementById('conversation-search-bar');
            if (!searchBar) return; // Still failed, give up
        }
        
        const searchInput = document.getElementById('conversation-search-input');
        
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
        this.searchResults = [];  // Now stores individual <mark> elements, not message bubbles
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
                this._highlightText(bubble, query);
            }
        });
        
        // Collect all mark elements as individual search results
        this.searchResults = Array.from(MessageHandler.messagesContainer.querySelectorAll('mark.search-highlight'));
        
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
     * Highlight search text in element using TreeWalker (safe for buttons)
     * @private
     */
    _highlightText(element, query) {
        // Store original HTML if not already stored
        if (!element.dataset.originalHtml) {
            element.dataset.originalHtml = element.innerHTML;
        }
        
        // Use TreeWalker to find text nodes, skipping buttons
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
            acceptNode: (node) => {
                let parent = node.parentElement;
                while (parent && parent !== element) {
                    if (parent.tagName === 'BUTTON' || parent.tagName === 'MARK' ||
                        parent.classList?.contains('pin-btn') || parent.classList?.contains('reply-btn')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    parent = parent.parentElement;
                }
                return NodeFilter.FILTER_ACCEPT;
            }
        }, false);
        
        const queryLower = query.toLowerCase();
        const nodesToHighlight = [];
        let node;
        
        // Collect matches first (can't modify DOM while walking)
        while (node = walker.nextNode()) {
            const text = node.textContent;
            const textLower = text.toLowerCase();
            let idx = textLower.indexOf(queryLower);
            while (idx !== -1) {
                nodesToHighlight.push({ node, start: idx, length: query.length });
                idx = textLower.indexOf(queryLower, idx + 1);
            }
        }
        
        // Apply highlights in reverse order to preserve positions
        for (let i = nodesToHighlight.length - 1; i >= 0; i--) {
            const { node, start, length } = nodesToHighlight[i];
            try {
                const range = document.createRange();
                range.setStart(node, start);
                range.setEnd(node, start + length);
                const mark = document.createElement('mark');
                mark.className = 'search-highlight';
                // Darker gray for non-current matches
                mark.style.cssText = 'background: #bdbdbd; padding: 0 2px; border-radius: 2px;';
                range.surroundContents(mark);
            } catch (e) {
                // Skip if range is invalid
            }
        }
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
        
        // Remove current highlight styling from previous
        if (this.currentSearchIndex >= 0 && this.searchResults[this.currentSearchIndex]) {
            const prev = this.searchResults[this.currentSearchIndex];
            prev.style.background = '#bdbdbd';  // Reset to non-current darker gray
            prev.style.outline = '';
        }
        
        // Calculate new index
        this.currentSearchIndex += direction;
        if (this.currentSearchIndex >= this.searchResults.length) {
            this.currentSearchIndex = 0;
        } else if (this.currentSearchIndex < 0) {
            this.currentSearchIndex = this.searchResults.length - 1;
        }
        
        // Highlight current result with distinct color (orange)
        const current = this.searchResults[this.currentSearchIndex];
        if (current) {
            current.style.background = '#ffcc80';  // Lighter orange for current
            current.style.outline = '2px solid #ff9800';  // Orange outline
            // Scroll to make current visible - use 'nearest' for better mobile experience
            current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
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
     * Fetch /api/user/personalization-profile and render status chips below the input.
     * Silently does nothing if the endpoint is unreachable or user has no profile yet.
     * @private
     */
    async _loadPersonalizationStatus() {
        try {
            const resp = await AuthHelper.authenticatedFetch(
                `/api/user/personalization-profile?character_id=${this.characterId || ''}`,
                { method: 'GET' }
            );
            if (!resp || !resp.ok) return;
            const data = await resp.json();
            this._renderPersonalizationStatus(data);
        } catch (_) {}
    },

    /**
     * Render up to 4 small adaptation chips below the user input field.
     * Shows: verbosity mode, current emotional state, active goal, current need mode.
     * @private
     */
    _renderPersonalizationStatus(profile) {
        if (!profile) return;
        const inputEl = document.getElementById(this.config.inputElementId);
        if (!inputEl) return;
        const container = inputEl.closest('form') || inputEl.parentElement;
        if (!container) return;

        // Remove any existing status bar
        const existing = document.getElementById('personalization-status-bar');
        if (existing) existing.remove();

        const chips = [];

        // Verbosity preference
        const verbosity = profile?.verbosity?.response_length;
        if (verbosity && verbosity !== 'balanced') {
            const label = verbosity === 'brief' ? '⚡ concise' : '📄 detailed';
            chips.push(`<span class="persona-chip verbosity" title="Response length preference">${label}</span>`);
        }

        // Emotional state (from explicit context)
        const emotion = profile?.emotional_state;
        if (emotion) {
            chips.push(`<span class="persona-chip emotion" title="Detected emotional state">😔 ${emotion}</span>`);
        }

        // Active goal
        const goal = profile?.active_goal;
        if (goal) {
            const short = goal.length > 28 ? goal.slice(0, 26) + '…' : goal;
            chips.push(`<span class="persona-chip goal" title="Goal: ${goal}">🎯 ${short}</span>`);
        }

        // Current need mode
        const need = profile?.current_need;
        if (need && need !== 'general') {
            chips.push(`<span class="persona-chip" title="Detected need type">✦ ${need}</span>`);
        }

        if (!chips.length) return;

        const bar = document.createElement('div');
        bar.id = 'personalization-status-bar';
        bar.className = 'personalization-status';
        bar.innerHTML = chips.join('');
        container.insertAdjacentElement('afterend', bar);
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
