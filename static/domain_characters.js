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
 * 
 * Uses existing ConversationBox module - no code duplication
 */

const DomainCharacters = {
    // Configuration
    characters: [],
    selectedCharacter: null,
    coordinatorId: 'coordinator',
    
    // API endpoints (no hardcoding)
    endpoints: {
        list: '/api/domain-characters',
        info: (id) => `/api/domain-characters/${id}`,
        route: '/api/domain-characters/route',
        analyze: '/api/domain-characters/analyze',
        feedback: '/api/domain-characters/feedback',
        preferences: '/api/domain-characters/preferences',
        history: (id) => `/api/domain-characters/history/${id}`
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
        
        // Load characters
        await this.loadCharacters();
        
        // Set default to coordinator
        this.selectedCharacter = this.coordinatorId;
        
        console.log('✅ DomainCharacters initialized');
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
                
                // Display messages
                data.history.forEach(msg => {
                    if (msg.user_message) {
                        this._addMessageToDisplay(msg.user_message, 'user');
                    }
                    if (msg.ai_response) {
                        this._addMessageToDisplay(msg.ai_response, 'bot', characterId);
                    }
                });
                
                console.log(`✓ Loaded ${data.history.length} messages for ${characterId}`);
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
     * Add a message to the display
     * @private
     */
    _addMessageToDisplay(content, role, characterId = null, isWelcome = false) {
        const messagesContainer = document.getElementById('domain-chat-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        if (isWelcome) messageDiv.classList.add('welcome-message');
        
        if (role === 'bot' && characterId) {
            const character = this.characters.find(c => c.id === characterId);
            const displayName = character ? character.display_name : characterId;
            
            messageDiv.innerHTML = `
                <div class="character-attribution">${displayName}${character?.is_coordinator ? ' (Coordinator)' : ''}</div>
                <div class="message-content">${this._formatMessage(content)}</div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">${role === 'user' ? '<strong>You:</strong> ' : ''}${this._formatMessage(content)}</div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    },
    
    /**
     * Format message content (handle newlines, etc.)
     * @private
     */
    _formatMessage(content) {
        if (!content) return '';
        return content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
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
                
                return data;
            } else {
                console.error('Routing failed:', data.error);
                this._addMessageToDisplay('Sorry, there was an error processing your message.', 'bot', this.selectedCharacter);
                return null;
            }
        } catch (error) {
            console.error('Error routing message:', error);
            this._addMessageToDisplay('Sorry, there was an error connecting to the server.', 'bot', this.selectedCharacter);
            return null;
        }
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
