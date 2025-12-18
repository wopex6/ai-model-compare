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
            const response = await AuthHelper.authenticatedFetch(this.endpoints.list);
            const data = await response.json();
            
            if (data.success && data.characters) {
                this.characters = data.characters;
                console.log(`✓ Loaded ${data.characters.length} domain characters`);
                this._renderCharacterList();
            }
        } catch (error) {
            console.error('Failed to load domain characters:', error);
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
        
        // Show welcome message first
        this._showWelcomeMessage(characterId);
        
        try {
            const response = await AuthHelper.authenticatedFetch(this.endpoints.history(characterId));
            const data = await response.json();
            
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
                                // Use actual responder character, not the viewing character
                                this._addMessageToDisplay(resp.content, 'bot', resp.character || characterId, false, msg.timestamp);
                            }
                        });
                    } else if (msg.ai_response) {
                        // Single response - use msg.character if available (actual responder)
                        const responder = msg.character || characterId;
                        this._addMessageToDisplay(msg.ai_response, 'bot', responder, false, msg.timestamp);
                    }
                });
                
                console.log(`✓ Loaded ${data.history.length} messages for ${characterId}`);
                
                // Callback: history loaded (like ConversationBox)
                if (this.callbacks.onHistoryLoaded) {
                    this.callbacks.onHistoryLoaded(data.history);
                }
            }
        } catch (error) {
            console.error('Failed to load character history:', error);
        }
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
     * Add a message to the display using MessageHandler (shared module)
     * @private
     * @param {string} content - Message content
     * @param {string} role - 'user' or 'bot'
     * @param {string} characterId - Character ID (for bot messages)
     * @param {boolean} isWelcome - Whether this is a welcome message
     * @param {string} timestamp - ISO timestamp string (optional)
     */
    _addMessageToDisplay(content, role, characterId = null, isWelcome = false, timestamp = null) {
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
                metadata: { isWelcome, characterId }
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
            
            timeStr = `<span class="timestamp" style="font-size: 0.75em; color: ${role === 'user' ? '#fff' : '#888'}; margin-left: 8px;">${displayTime}</span>`;
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
        
        // Add user message to display immediately
        this._addMessageToDisplay(message, 'user');
        
        // Callback: message sent (like ConversationBox)
        if (this.callbacks.onMessageSent) {
            this.callbacks.onMessageSent(message);
        }
        
        try {
            const response = await AuthHelper.authenticatedFetch(this.endpoints.route, {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    character_id: this.selectedCharacter,
                    use_ai: useAi
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`✓ Routed to ${data.responding_count} character(s)`);
                
                // Display responses
                if (data.responses) {
                    data.responses.forEach(resp => {
                        if (resp.should_display) {
                            this._addMessageToDisplay(resp.content, 'bot', resp.character_id);
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
        
        item.innerHTML = `
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
