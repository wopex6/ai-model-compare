/**
 * Domain Character Module
 * Extends ConversationBox for domain character support
 * 
 * Features:
 * - Multi-character routing
 * - Threshold-based character activation
 * - Coordinator synthesis
 * - Character feedback
 * - Character selection UI
 * - Session management (like ConversationBox)
 * - Callbacks system (like ConversationBox)
 * - Quick messages (like ConversationBox)
 * 
 * Uses existing ConversationBox module - no code duplication
 */

const DomainCharacters = {
    // Configuration
    characters: [],
    selectedCharacter: null,
    coordinatorId: 'coordinator',
    
    // Session management (like ConversationBox)
    sessionId: null,
    userId: null,
    
    // API endpoints (no hardcoding)
    endpoints: {
        list: '/api/domain-characters',
        info: (id) => `/api/domain-characters/${id}`,
        route: '/api/domain-characters/route',
        analyze: '/api/domain-characters/analyze',
        feedback: '/api/domain-characters/feedback',
        preferences: '/api/domain-characters/preferences',
        history: (id) => `/api/domain-characters/history/${id}`,
        session: '/api/domain-characters/session'  // NEW: session endpoint
    },
    
    // Per-character conversation storage
    conversations: {},  // { character_id: [messages] }
    
    // UI element IDs (configurable)
    ui: {
        characterListId: 'domain-character-list',
        selectedCharacterId: 'selected-domain-character',
        analysisPanelId: 'character-analysis-panel',
        feedbackContainerId: 'character-feedback-container'
    },
    
    // Callbacks (like ConversationBox)
    callbacks: {
        onMessageSent: null,      // Called after user message sent: (message) => {}
        onResponseReceived: null, // Called after bot response: (data) => {}
        onError: null,            // Called on error: (error) => {}
        onSessionCreated: null,   // Called when session created: (sessionId) => {}
        onHistoryLoaded: null,    // Called after history loaded: (messages) => {}
        onCharacterChanged: null  // Called when character switched: (characterId) => {}
    },
    
    /**
     * Initialize domain character system
     * @param {Object} config - Configuration options
     */
    async init(config = {}) {
        // Merge config
        if (config.endpoints) {
            this.endpoints = { ...this.endpoints, ...config.endpoints };
        }
        if (config.ui) {
            this.ui = { ...this.ui, ...config.ui };
        }
        if (config.callbacks) {
            this.callbacks = { ...this.callbacks, ...config.callbacks };
        }
        
        // Get authenticated session (like ConversationBox)
        await this._getAuthenticatedSession();
        
        // Load characters
        await this.loadCharacters();
        
        // Set default to coordinator
        this.selectedCharacter = this.coordinatorId;
        
        // Update MessageHandler's currentCharacterId for consistent pin/highlight saving
        if (typeof MessageHandler !== 'undefined') {
            MessageHandler.currentCharacterId = this.coordinatorId;
        }
        
        console.log('✅ DomainCharacters initialized');
    },
    
    /**
     * Get authenticated session from backend (like ConversationBox)
     * @private
     */
    async _getAuthenticatedSession() {
        try {
            const response = await AuthHelper.authenticatedFetch(this.endpoints.session, {
                method: 'GET'
            });
            
            const data = await response.json();
            
            if (data.session_id) {
                this.sessionId = data.session_id;
                this.userId = data.user_id;
                console.log(`✓ Domain session loaded: ${this.sessionId} for user ${this.userId}`);
                
                // Callback: session created
                if (this.callbacks.onSessionCreated) {
                    this.callbacks.onSessionCreated(this.sessionId);
                }
            } else if (data.user_id) {
                // Session not required for domain characters, just user auth
                this.userId = data.user_id;
                console.log(`✓ User authenticated: ${this.userId}`);
            }
        } catch (error) {
            console.error('Error getting authenticated session:', error);
            this.sessionId = null;
            this.userId = null;
        }
    },
    
    /**
     * Load all domain characters from API
     */
    async loadCharacters() {
        try {
            // Use regular fetch since this endpoint doesn't require auth
            const response = await fetch(this.endpoints.list);
            const data = await response.json();
            
            if (data.success && data.characters) {
                this.characters = data.characters;
                console.log(`✓ Loaded ${data.characters.length} domain characters`);
                this._renderCharacterList();
            } else {
                console.error('Failed to load characters:', data.error || 'Unknown error');
                this._showCharacterLoadError(data.error || 'Failed to load characters');
            }
        } catch (error) {
            console.error('Failed to load domain characters:', error);
            this._showCharacterLoadError(error.message);
        }
    },
    
    /**
     * Show error message in character list
     * @private
     */
    _showCharacterLoadError(message) {
        const container = document.getElementById(this.ui.characterListId);
        if (container) {
            container.innerHTML = `<div class="error-msg" style="padding: 20px; color: #e74c3c; text-align: center;">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>`;
        }
    },
    
    /**
     * Select a specific character
     * @param {string} characterId - Character ID to select
     */
    async selectCharacter(characterId) {
        const previousCharacter = this.selectedCharacter;
        this.selectedCharacter = characterId;
        
        // Update UI
        const listElement = document.getElementById(this.ui.characterListId);
        if (listElement) {
            const items = listElement.querySelectorAll('.domain-char-item');
            items.forEach(item => {
                item.classList.toggle('selected', item.dataset.characterId === characterId);
            });
        }
        
        // Update selected display
        const selectedElement = document.getElementById(this.ui.selectedCharacterId);
        if (selectedElement) {
            const character = this.characters.find(c => c.id === characterId);
            if (character) {
                selectedElement.textContent = character.display_name;
                selectedElement.dataset.characterId = characterId;
            }
        }
        
        // Update header display
        this._updateCharacterHeader(characterId);
        
        // Load conversation history for this character
        if (previousCharacter !== characterId) {
            await this.loadCharacterHistory(characterId);
            
            // Update MessageHandler's currentCharacterId for consistent pin/highlight saving
            if (typeof MessageHandler !== 'undefined') {
                MessageHandler.currentCharacterId = characterId;
            }
            
            // Callback: character changed
            if (this.callbacks.onCharacterChanged) {
                this.callbacks.onCharacterChanged(characterId);
            }
        }
        
        console.log(`✓ Selected character: ${characterId}`);
    },
    
    /**
     * Update the character header display
     * @private
     */
    _updateCharacterHeader(characterId) {
        const character = this.characters.find(c => c.id === characterId);
        if (!character) return;
        
        // Use IDs from the HTML template
        const headerName = document.getElementById('selected-domain-character');
        const headerRole = document.getElementById('selected-character-domain');
        
        if (headerName) headerName.textContent = character.display_name;
        if (headerRole) headerRole.textContent = character.is_coordinator ? 
            'Coordinator - Sees the bigger picture' : 
            `${character.domain.charAt(0).toUpperCase() + character.domain.slice(1).replace('_', ' ')} Advisor`;
    },
    
    /**
     * Load conversation history for a character
     * @param {string} characterId - Character ID
     */
    async loadCharacterHistory(characterId) {
        // Clear current messages
        const messagesContainer = document.getElementById('domain-chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        
        try {
            const response = await AuthHelper.authenticatedFetch(this.endpoints.history(characterId));
            
            // Check for 401 - session expired
            if (response.status === 401) {
                console.warn('⚠️ Session expired - showing login prompt');
                this._showLoginPrompt(characterId);
                return;
            }
            
            const data = await response.json();
            console.log(`📜 History API response for ${characterId}:`, data);
            
            if (data.success && data.history && data.history.length > 0) {
                // Store in local cache
                this.conversations[characterId] = data.history;
                
                // Display messages with timestamps
                data.history.forEach(msg => {
                    if (msg.user_message) {
                        this._addMessageToDisplay(msg.user_message, 'user', null, false, msg.timestamp);
                    }
                    
                    // Handle multi-responses (coordinator view)
                    if (msg.responses && msg.responses.length > 0) {
                        msg.responses.forEach(resp => {
                            if (resp.content) {
                                // Generate client-side summary for long messages
                                const summaryData = this._generateClientSummary(resp.content);
                                // Use actual responder character, not the viewing character
                                this._addMessageToDisplay(resp.content, 'bot', resp.character || characterId, false, msg.timestamp, summaryData);
                            }
                        });
                    } else if (msg.ai_response) {
                        // Single response - use msg.character if available (actual responder)
                        const responder = msg.character || characterId;
                        // Generate client-side summary for long messages
                        const summaryData = this._generateClientSummary(msg.ai_response);
                        this._addMessageToDisplay(msg.ai_response, 'bot', responder, false, msg.timestamp, summaryData);
                    }
                });
                
                console.log(`✓ Loaded ${data.history.length} messages for ${characterId}`);
                console.log(`MessageHandler.highlightsEnabled = ${MessageHandler.highlightsEnabled}`);
                
                // Apply stored highlights after messages are loaded
                console.log('About to check if highlights enabled...');
                if (MessageHandler.highlightsEnabled) {
                    console.log('Attempting to apply stored highlights...');
                    setTimeout(() => {
                        console.log('Calling MessageHandler.applyStoredHighlights()');
                        MessageHandler.applyStoredHighlights();
                    }, 500);  // Increased delay to ensure DOM is ready
                } else {
                    console.log('Highlights NOT enabled - skipping applyStoredHighlights');
                }
                
                // Update pin button states after messages are loaded
                setTimeout(() => {
                    MessageHandler.loadPinnedMessages();
                }, 600);
                
                // Callback: history loaded (like ConversationBox)
                if (this.callbacks.onHistoryLoaded) {
                    this.callbacks.onHistoryLoaded(data.history);
                }
            } else {
                // No history - show welcome message
                this._showWelcomeMessage(characterId);
            }
        } catch (error) {
            console.error('Failed to load character history:', error);
            // On error, still show welcome message
            this._showWelcomeMessage(characterId);
        }
    },
    
    /**
     * Reload history with provided data (used by goToMessage for loading older history)
     * @param {Array} history - History data from API
     * @param {string} characterId - Character ID
     */
    async _reloadHistoryWithData(history, characterId) {
        // Clear current messages
        const messagesContainer = document.getElementById('domain-chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
        
        // Store in local cache
        this.conversations[characterId] = history;
        
        // Display messages with timestamps
        history.forEach(msg => {
            if (msg.user_message) {
                this._addMessageToDisplay(msg.user_message, 'user', null, false, msg.timestamp);
            }
            
            // Handle multi-responses (coordinator view)
            if (msg.responses && msg.responses.length > 0) {
                msg.responses.forEach(resp => {
                    if (resp.content) {
                        // Generate client-side summary for long messages
                        const summaryData = this._generateClientSummary(resp.content);
                        this._addMessageToDisplay(resp.content, 'bot', resp.character || characterId, false, msg.timestamp, summaryData);
                    }
                });
            } else if (msg.ai_response) {
                const responder = msg.character || characterId;
                // Generate client-side summary for long messages
                const summaryData = this._generateClientSummary(msg.ai_response);
                this._addMessageToDisplay(msg.ai_response, 'bot', responder, false, msg.timestamp, summaryData);
            }
        });
        
        console.log(`✓ Reloaded ${history.length} messages for pinned message navigation`);
    },
    
    /**
     * Show welcome message for a character
     * @private
     */
    _showWelcomeMessage(characterId) {
        const character = this.characters.find(c => c.id === characterId);
        if (!character) return;
        
        let welcomeMessage = '';
        if (character.is_coordinator) {
            welcomeMessage = `Hello! I'm ${character.display_name}, your life companion. I work with a team of specialized advisors to help you across all areas of your life.\n\nYou can talk to me for a holistic view, or select a specific advisor from the sidebar for domain-specific guidance.\n\nWhat's on your mind today?`;
        } else {
            welcomeMessage = `Hello! I'm ${character.display_name}, your ${character.domain.replace('_', ' ')} advisor. I'm here to help you with ${character.domain.replace('_', ' ')}-related concerns and questions.\n\nHow can I assist you today?`;
        }
        
        this._addMessageToDisplay(welcomeMessage, 'bot', characterId, true);
    },
    
    /**
     * Show login prompt when session has expired
     * @private
     */
    _showLoginPrompt(characterId) {
        const messagesContainer = document.getElementById('domain-chat-messages');
        if (!messagesContainer) return;
        
        // Create login prompt message
        const loginPrompt = document.createElement('div');
        loginPrompt.className = 'message bot-message session-expired-prompt';
        loginPrompt.innerHTML = `
            <div class="message-content" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 20px;">
                <div style="font-size: 24px; margin-bottom: 10px;">🔐</div>
                <div style="font-weight: bold; margin-bottom: 10px;">Session Expired</div>
                <div style="margin-bottom: 15px; opacity: 0.9;">Your session has expired. Please log in again to continue your conversation.</div>
                <button onclick="window.location.href='/'" style="background: white; color: #667eea; border: none; padding: 10px 24px; border-radius: 20px; font-weight: bold; cursor: pointer; transition: transform 0.2s;">
                    Log In
                </button>
            </div>
        `;
        messagesContainer.appendChild(loginPrompt);
        
        // Also disable the input
        const input = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        if (input) {
            input.disabled = true;
            input.placeholder = 'Please log in to continue...';
        }
        if (sendBtn) {
            sendBtn.disabled = true;
        }
    },
    
    /**
     * Generate a client-side summary for long messages
     * @private
     * @param {string} content - Message content
     * @returns {object} - { has_summary: boolean, summary: string }
     */
    _generateClientSummary(content) {
        // Only summarize long bot messages (>500 chars)
        if (!content || content.length < 500) {
            return { has_summary: false, summary: '' };
        }
        
        // Extract first meaningful paragraph or sentences
        const lines = content.split('\n').filter(l => l.trim());
        let summary = '';
        
        // Try to get first 2-3 sentences or ~150 chars
        for (const line of lines) {
            if (summary.length > 150) break;
            const cleanLine = line.replace(/^[#*\->\s]+/, '').trim();
            if (cleanLine) {
                summary += (summary ? ' ' : '') + cleanLine;
            }
        }
        
        // Truncate if still too long
        if (summary.length > 200) {
            summary = summary.substring(0, 197) + '...';
        }
        
        return { has_summary: true, summary: summary };
    },
    
    /**
     * Add a message to the display using MessageHandler (shared module)
     * @private
     * @param {string} content - Message content
     * @param {string} role - 'user' or 'bot'
     * @param {string} characterId - Character ID (for bot messages)
     * @param {boolean} isWelcome - Whether this is a welcome message
     * @param {string} timestamp - ISO timestamp string (optional)
     * @param {object} extraMetadata - Additional metadata (summary, etc.)
     */
    _addMessageToDisplay(content, role, characterId = null, isWelcome = false, timestamp = null, extraMetadata = {}) {
        // Get character display name for bot messages
        let displayName = null;
        if (role === 'bot' && characterId) {
            const character = this.characters.find(c => c.id === characterId);
            displayName = character ? character.display_name : characterId;
            if (character?.is_coordinator) {
                displayName += ' (Coordinator)';
            }
        }
        
        // Use MessageHandler for consistent display (shared with AI Characters)
        if (typeof MessageHandler !== 'undefined' && MessageHandler.messagesContainer) {
            // Temporarily update character name for this message
            const originalName = MessageHandler.theme?.characterDisplayName;
            if (displayName) {
                MessageHandler.theme.characterDisplayName = displayName;
            }
            
            MessageHandler.addMessage({
                content: content,
                role: role,
                timestamp: timestamp || (isWelcome ? null : new Date().toISOString()),
                shouldScroll: true,
                metadata: { isWelcome, characterId, ...extraMetadata }
            });
            
            // Restore original name
            if (displayName && originalName) {
                MessageHandler.theme.characterDisplayName = originalName;
            }
        } else {
            // Fallback: direct DOM manipulation if MessageHandler not available
            this._addMessageToDisplayFallback(content, role, displayName, isWelcome, timestamp);
        }
    },
    
    /**
     * Fallback message display (if MessageHandler not available)
     * @private
     */
    _addMessageToDisplayFallback(content, role, displayName, isWelcome, timestamp) {
        const messagesContainer = document.getElementById('domain-chat-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        if (isWelcome) messageDiv.classList.add('welcome-message');
        
        let timeStr = '';
        if (timestamp) {
            // Handle different timestamp formats (ISO with T, or space-separated from SQLite)
            // Database stores UTC, so append 'Z' to indicate UTC timezone
            let normalizedTimestamp = timestamp;
            if (typeof timestamp === 'string') {
                normalizedTimestamp = timestamp.replace('Z', '').replace('+00:00', '');
                if (!normalizedTimestamp.includes('T')) {
                    normalizedTimestamp = normalizedTimestamp.replace(' ', 'T');
                }
                normalizedTimestamp = normalizedTimestamp + 'Z';
            }
            
            const date = new Date(normalizedTimestamp);
            
            if (!isNaN(date.getTime())) {
                const today = new Date();
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                
                const isToday = date.toDateString() === today.toDateString();
                const isYesterday = date.toDateString() === yesterday.toDateString();
                
                const hours = date.getHours().toString().padStart(2, '0');
                const minutes = date.getMinutes().toString().padStart(2, '0');
                const timeOnly = `${hours}:${minutes}`;
                
                // Show "yesterday" or date for non-today messages
                let displayTime = timeOnly;
                if (isYesterday) {
                    displayTime = `yesterday ${timeOnly}`;
                } else if (!isToday) {
                    const day = date.getDate().toString().padStart(2, '0');
                    const month = (date.getMonth() + 1).toString().padStart(2, '0');
                    displayTime = `${day}/${month} ${timeOnly}`;
                }
                
                timeStr = `<span class="timestamp" style="font-size: 0.75em; color: ${role === 'user' ? '#fff' : '#888'}; margin-left: 8px;">${displayTime}</span>`;
            }
        }
        
        const formattedContent = content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        if (role === 'bot' && displayName) {
            messageDiv.innerHTML = `
                <div class="character-attribution">${displayName}${timeStr}</div>
                <div class="message-content">${formattedContent}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">${role === 'user' ? '<strong>You:</strong> ' : ''}${formattedContent}${timeStr}</div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },
    
    /**
     * Send message to domain characters via routing
     * Integrates with ConversationBox pattern
     * @param {string} message - User message
     * @param {boolean} useAi - Whether to generate AI responses
     */
    async sendMessage(message, useAi = true) {
        if (!message || !message.trim()) return null;
        
        // Add user message to display immediately with timestamp
        this._addMessageToDisplay(message, 'user', null, false, new Date().toISOString());
        
        // Track user activity for greeting system
        if (typeof GreetingHandler !== 'undefined' && GreetingHandler.updateUserActivity) {
            GreetingHandler.updateUserActivity('message_sent');
        }
        
        // Callback: message sent (like ConversationBox)
        if (this.callbacks.onMessageSent) {
            this.callbacks.onMessageSent(message);
        }
        
        try {
            // Check if replying to a specific message (WhatsApp-style)
            const replyToId = typeof MessageHandler !== 'undefined' ? MessageHandler.getReplyToId() : null;
            
            // Include action flags if set by response action buttons
            const payload = {
                message: message,
                character_id: this.selectedCharacter,
                use_ai: useAi,
                reply_to_message_id: replyToId
            };
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
            
            const response = await AuthHelper.authenticatedFetch(this.endpoints.route, {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            
            // Clear the reply state after sending
            if (replyToId && typeof MessageHandler !== 'undefined') {
                MessageHandler.clearReplyTo();
            }
            
            // Check for session expiry (401) before parsing JSON
            if (response.status === 401) {
                console.warn('⚠️ Session expired during message send');
                this._displayError('Your session has expired. Please log in again.');
                // Redirect to login after a short delay
                setTimeout(() => {
                    window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                }, 2000);
                return null;
            }
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`✓ Routed to ${data.responding_count} character(s)`);
                
                // Display responses with metadata (including summary)
                if (data.responses) {
                    data.responses.forEach(resp => {
                        if (resp.should_display) {
                            // Pass metadata including summary if available
                            const metadata = resp.metadata || {};
                            console.log('📋 Response metadata:', metadata);
                            console.log('📋 Has summary:', metadata.has_summary, 'Summary:', metadata.summary?.substring(0, 50));
                            this._addMessageToDisplay(
                                resp.content, 
                                'bot', 
                                resp.character_id, 
                                false, 
                                null, 
                                metadata
                            );
                            
                            // Display follow-up suggestions if available
                            if (metadata.follow_up_suggestions && metadata.follow_up_suggestions.length > 0) {
                                this._displayFollowUpSuggestions(metadata.follow_up_suggestions, resp.character_id);
                            }
                            
                            // Add response action buttons: "Tell me more" + "Not what I meant"
                            this._addResponseActions(resp.character_id);
                        }
                    });
                }
                
                // Callback: response received (like ConversationBox)
                if (this.callbacks.onResponseReceived) {
                    this.callbacks.onResponseReceived(data);
                }
                
                return data;
            } else {
                console.error('Routing failed:', data.error);
                this._displayError('Sorry, there was an error processing your message.');
                return null;
            }
        } catch (error) {
            console.error('Error routing message:', error);
            this._displayError('Sorry, there was an error connecting to the server.');
            
            // Callback: error (like ConversationBox)
            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }
            
            return null;
        }
    },
    
    /**
     * Send a quick/preset message (like ConversationBox)
     * @param {string} message - The message to send
     */
    sendQuickMessage(message) {
        this.sendMessage(message, true);
    },
    
    /**
     * Add response action buttons ("Tell me more" / "Not what I meant") after an AI message
     * @param {string} characterId - Character that provided the response
     * @private
     */
    _addResponseActions(characterId) {
        const messagesContainer = document.getElementById('domain-chat-messages');
        if (!messagesContainer) return;
        
        // Get character display name for natural message
        const charName = this.characters?.[characterId]?.display_name || characterId;
        
        const actionRow = document.createElement('div');
        actionRow.className = 'response-actions';
        
        const moreBtn = document.createElement('button');
        moreBtn.className = 'response-action-btn more-detail-btn';
        moreBtn.textContent = 'Tell me more';
        moreBtn.title = 'Get a more detailed response';
        moreBtn.addEventListener('click', () => {
            actionRow.remove();
            this._nextMessageFlags = { detail_requested: true, _ts: Date.now(), _auto: true, character_id: characterId };
            this.sendMessage(`Could you elaborate on that, ${charName}?`, true);
        });
        
        const redirectBtn = document.createElement('button');
        redirectBtn.className = 'response-action-btn redirect-btn';
        redirectBtn.textContent = 'Not what I meant';
        redirectBtn.title = 'Try a different approach';
        redirectBtn.addEventListener('click', () => {
            actionRow.remove();
            // Flag the next message as direction_change
            this._nextMessageFlags = { direction_change: true, _ts: Date.now() };
            const inputEl = document.getElementById('domain-chat-input') || document.getElementById('userInput');
            if (inputEl) {
                inputEl.value = "That's not quite what I meant. Let me clarify:";
                inputEl.focus();
                inputEl.setSelectionRange(inputEl.value.length, inputEl.value.length);
            }
        });
        
        actionRow.appendChild(moreBtn);
        actionRow.appendChild(redirectBtn);
        messagesContainer.appendChild(actionRow);
    },
    
    /**
     * Display an error message (unified with ConversationBox pattern)
     * @private
     */
    _displayError(errorText) {
        this._addMessageToDisplay(errorText, 'bot', this.selectedCharacter);
    },
    
    /**
     * Analyze message without generating responses
     * @param {string} message - Message to analyze
     */
    async analyzeMessage(message) {
        if (!message || !message.trim()) return null;
        
        try {
            const response = await AuthHelper.authenticatedFetch(this.endpoints.analyze, {
                method: 'POST',
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this._renderAnalysis(data.analysis);
                return data;
            }
            return null;
        } catch (error) {
            console.error('Error analyzing message:', error);
            return null;
        }
    },
    
    /**
     * Display follow-up suggestions as clickable buttons
     * @param {Array} suggestions - Array of suggestion objects
     * @param {string} characterId - Character that provided the response
     * @private
     */
    _displayFollowUpSuggestions(suggestions, characterId) {
        const messagesContainer = document.getElementById('domain-chat-messages');
        if (!messagesContainer || !suggestions || suggestions.length === 0) return;
        
        // Create suggestions container
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'follow-up-suggestions';
        suggestionsDiv.style.cssText = `
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 12px 16px;
            margin: 8px 0 16px 48px;
            animation: fadeIn 0.3s ease-out;
        `;
        
        // Add label
        const label = document.createElement('div');
        label.style.cssText = `
            width: 100%;
            font-size: 12px;
            color: #666;
            margin-bottom: 4px;
        `;
        label.textContent = '💡 You might want to ask:';
        suggestionsDiv.appendChild(label);
        
        // Create suggestion buttons
        suggestions.forEach(suggestion => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.style.cssText = `
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border: 1px solid #dee2e6;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 13px;
                color: #495057;
                cursor: pointer;
                transition: all 0.2s ease;
                max-width: 100%;
                text-align: left;
                white-space: normal;
                line-height: 1.4;
            `;
            btn.textContent = suggestion.text;
            btn.title = suggestion.intent || 'Click to ask this';
            
            // Hover effects
            btn.onmouseenter = () => {
                btn.style.background = 'linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%)';
                btn.style.borderColor = '#adb5bd';
                btn.style.transform = 'translateY(-1px)';
            };
            btn.onmouseleave = () => {
                btn.style.background = 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)';
                btn.style.borderColor = '#dee2e6';
                btn.style.transform = 'translateY(0)';
            };
            
            // Click handler - send the suggestion as a message
            btn.onclick = async () => {
                // Record the selection for learning (follow-up system)
                try {
                    await AuthHelper.authenticatedFetch('/api/user/suggestion-selected', {
                        method: 'POST',
                        body: JSON.stringify({
                            text: suggestion.text,
                            category: suggestion.category,
                            character_id: characterId
                        })
                    });
                } catch (e) {
                    console.log('Could not record suggestion selection:', e);
                }
                
                // Record engagement signal (intelligence system)
                try {
                    await AuthHelper.authenticatedFetch('/api/user/intelligence/record', {
                        method: 'POST',
                        body: JSON.stringify({
                            signal_type: 'suggestion_clicked',
                            character_id: characterId,
                            topic: suggestion.category,
                            context: { suggestion_text: suggestion.text }
                        })
                    });
                } catch (e) {
                    console.log('Could not record engagement:', e);
                }
                
                // Remove suggestions UI
                suggestionsDiv.remove();
                
                // Send the suggestion as a message
                this.sendMessage(suggestion.text);
            };
            
            suggestionsDiv.appendChild(btn);
        });
        
        messagesContainer.appendChild(suggestionsDiv);
        
        // Scroll to show suggestions
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },
    
    /**
     * Submit feedback for a character's response
     * @param {string} characterId - Character ID
     * @param {string} feedback - 'positive' or 'negative'
     */
    async submitFeedback(characterId, feedback) {
        try {
            const response = await AuthHelper.authenticatedFetch(this.endpoints.feedback, {
                method: 'POST',
                body: JSON.stringify({
                    character_id: characterId,
                    feedback: feedback
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`✓ Feedback submitted for ${characterId}: ${feedback}`);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error submitting feedback:', error);
            return false;
        }
    },
    
    /**
     * Get character by ID
     * @param {string} characterId - Character ID
     */
    getCharacter(characterId) {
        return this.characters.find(c => c.id === characterId);
    },
    
    /**
     * Get all domain characters (excluding coordinator)
     */
    getDomainCharacters() {
        return this.characters.filter(c => !c.is_coordinator);
    },
    
    /**
     * Get coordinator character
     */
    getCoordinator() {
        return this.characters.find(c => c.is_coordinator);
    },
    
    /**
     * Render character list in UI
     * @private
     */
    _renderCharacterList() {
        const container = document.getElementById(this.ui.characterListId);
        if (!container) return;
        
        container.innerHTML = '';
        
        // Add coordinator first
        const coordinator = this.getCoordinator();
        if (coordinator) {
            container.appendChild(this._createCharacterItem(coordinator, true));
        }
        
        // Add domain characters
        this.getDomainCharacters().forEach(char => {
            container.appendChild(this._createCharacterItem(char, false));
        });
    },
    
    /**
     * Create character list item element
     * @private
     */
    _createCharacterItem(character, isCoordinator) {
        const item = document.createElement('div');
        item.className = `domain-char-item ${isCoordinator ? 'coordinator' : ''} ${character.id === this.selectedCharacter ? 'selected' : ''}`;
        item.dataset.characterId = character.id;
        item.title = `${character.display_name} - ${character.domain}`;
        
        // Character icons mapping - unique face/head avatars for each domain
        const icons = {
            'coordinator': '⭐',
            // Domain characters with unique face icons
            'domain_work': '👔',
            'domain_relationships': '💑',
            'domain_mental_health': '🧘',
            'domain_physical_health': '🏃',
            'domain_finance': '💰',
            'domain_learning': '👨‍🎓',
            'domain_creativity': '👩‍🎨',
            // Legacy character IDs (if any)
            'life_coach': '🎯',
            'psychologist': '🧠',
            'stoic_philosopher': '🏛️',
            'career_mentor': '💼',
            'spiritual_guide': '🙏',
            'health_coach': '💪',
            'financial_advisor': '💰',
            'creative_muse': '🎨',
            'zen_master': '☯️',
            'scientist': '🔬',
            'wisdom_sage': '📚'
        };
        
        const icon = icons[character.id] || '👤';
        
        item.innerHTML = `
            <div class="char-icon">${icon}</div>
            <div class="char-name">${character.display_name}</div>
            <div class="char-domain">${character.domain}</div>
        `;
        
        item.addEventListener('click', () => this.selectCharacter(character.id));
        
        return item;
    },
    
    /**
     * Render analysis results
     * @private
     */
    _renderAnalysis(analysis) {
        const container = document.getElementById(this.ui.analysisPanelId);
        if (!container) return;
        
        container.innerHTML = '<h4>Character Analysis</h4>';
        
        analysis.forEach(item => {
            const div = document.createElement('div');
            div.className = `analysis-item ${item.would_respond ? 'would-respond' : ''}`;
            
            const concernPercent = Math.round(item.concern_level * 100);
            div.innerHTML = `
                <span class="char-name">${item.display_name}</span>
                <span class="concern-level" style="width: ${concernPercent}%">${concernPercent}%</span>
                ${item.would_respond ? '<span class="respond-badge">Would Respond</span>' : ''}
            `;
            
            container.appendChild(div);
        });
    },
    
    /**
     * Create feedback buttons for a response
     * @param {string} characterId - Character ID
     * @param {HTMLElement} container - Container element
     */
    addFeedbackButtons(characterId, container) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'character-feedback';
        feedbackDiv.innerHTML = `
            <button class="feedback-btn positive" data-feedback="positive" title="Helpful">👍</button>
            <button class="feedback-btn negative" data-feedback="negative" title="Not helpful">👎</button>
        `;
        
        feedbackDiv.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const feedback = e.target.dataset.feedback;
                const success = await this.submitFeedback(characterId, feedback);
                if (success) {
                    feedbackDiv.innerHTML = '<span class="feedback-thanks">Thanks for your feedback!</span>';
                }
            });
        });
        
        container.appendChild(feedbackDiv);
    }
};

/**
 * Domain Character Conversation Box
 * Extends ConversationBox for domain character support
 * Uses composition instead of modification
 */
const DomainConversationBox = {
    // Reference to base ConversationBox
    _baseBox: null,
    
    // Domain character specific config
    config: {
        showAnalysis: false,
        showFeedback: true,
        multiResponse: true  // Show multiple character responses
    },
    
    /**
     * Initialize domain conversation box
     * @param {Object} config - Configuration
     */
    async init(config = {}) {
        this.config = { ...this.config, ...config };
        
        // Initialize domain characters first
        await DomainCharacters.init(config.domainConfig || {});
        
        // Initialize base ConversationBox with domain routing
        ConversationBox.init('domain', {
            chatEndpoint: '/api/domain-characters/route',
            historyEndpoint: null,  // Domain characters don't use session-based history
            sessionEndpoint: null,
            includeContext: true,
            onMessageSent: (message) => this._onMessageSent(message),
            onResponseReceived: (data) => this._onResponseReceived(data),
            onError: (error) => this._onError(error)
        });
        
        this._baseBox = ConversationBox;
        
        // Override sendMessage to use domain routing
        this._setupDomainRouting();
        
        console.log('✅ DomainConversationBox initialized');
    },
    
    /**
     * Setup domain routing for messages
     * @private
     */
    _setupDomainRouting() {
        // Store original sendMessage
        const originalSend = ConversationBox.sendMessage.bind(ConversationBox);
        
        // Override with domain routing
        ConversationBox.sendMessage = async (messageText = null) => {
            const inputElement = document.getElementById(ConversationBox.config.inputElementId);
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
            if (inputElement) {
                inputElement.value = '';
            }
            
            // Analyze if enabled
            if (this.config.showAnalysis) {
                await DomainCharacters.analyzeMessage(message);
            }
            
            // Send to domain characters
            const data = await DomainCharacters.sendMessage(message, true);
            
            if (data && data.responses) {
                this._displayResponses(data.responses);
            }
        };
    },
    
    /**
     * Display multiple character responses
     * @private
     */
    _displayResponses(responses) {
        responses.forEach(resp => {
            if (resp.should_display) {
                // Create message with character attribution
                const messageDiv = MessageHandler.addMessage({
                    content: resp.content,
                    role: 'bot',
                    timestamp: new Date().toISOString(),
                    source: 'domain_character',
                    shouldScroll: true
                });
                
                // Add character name attribution
                if (messageDiv) {
                    const attribution = document.createElement('div');
                    attribution.className = 'character-attribution';
                    attribution.textContent = resp.display_name;
                    messageDiv.insertBefore(attribution, messageDiv.firstChild);
                    
                    // Add feedback buttons if enabled
                    if (this.config.showFeedback) {
                        DomainCharacters.addFeedbackButtons(resp.character_id, messageDiv);
                    }
                }
            }
        });
    },
    
    /**
     * Callback when message sent
     * @private
     */
    _onMessageSent(message) {
        console.log(`📤 Message sent: ${message.substring(0, 50)}...`);
    },
    
    /**
     * Callback when response received
     * @private
     */
    _onResponseReceived(data) {
        console.log(`📥 Response received from ${data.responding_count || 1} character(s)`);
    },
    
    /**
     * Callback on error
     * @private
     */
    _onError(error) {
        console.error('❌ Domain conversation error:', error);
    },
    
    /**
     * Select a domain character
     * @param {string} characterId - Character ID
     */
    selectCharacter(characterId) {
        DomainCharacters.selectCharacter(characterId);
    },
    
    /**
     * Get currently selected character
     */
    getSelectedCharacter() {
        return DomainCharacters.selectedCharacter;
    }
};

// Make available globally
window.DomainCharacters = DomainCharacters;
window.DomainConversationBox = DomainConversationBox;
