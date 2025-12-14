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
        preferences: '/api/domain-characters/preferences'
    },
    
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
    selectCharacter(characterId) {
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
        
        console.log(`✓ Selected character: ${characterId}`);
    },
    
    /**
     * Send message to domain characters via routing
     * Integrates with ConversationBox pattern
     * @param {string} message - User message
     * @param {boolean} useAi - Whether to generate AI responses
     */
    async sendMessage(message, useAi = true) {
        if (!message || !message.trim()) return null;
        
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
                return data;
            } else {
                console.error('Routing failed:', data.error);
                return null;
            }
        } catch (error) {
            console.error('Error routing message:', error);
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
