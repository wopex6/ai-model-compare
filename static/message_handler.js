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
    
    // Reply-to state (WhatsApp-style)
    replyingTo: null,  // { id, content, sender_type }
    
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
        // Use "user-message" or "bot-message" class format to match domain_characters.css
        messageDiv.className = `${this.theme.messageClass} ${sender}-message`;
        messageDiv.dataset.role = role;
        if (source) messageDiv.dataset.source = source;
        
        // Create message bubble
        const bubble = document.createElement('div');
        bubble.className = this.theme.bubbleClass;
        
        // Format timestamp - show "yesterday" or date for non-today messages
        let timeStr = '';
        if (timestamp) {
            // Handle different timestamp formats (ISO with T, or space-separated from SQLite)
            // Database stores UTC, so append 'Z' to indicate UTC timezone
            let normalizedTimestamp = timestamp;
            if (typeof timestamp === 'string') {
                // Remove any existing timezone indicator first
                normalizedTimestamp = timestamp.replace('Z', '').replace('+00:00', '');
                // Convert space to T for ISO format
                if (!normalizedTimestamp.includes('T')) {
                    normalizedTimestamp = normalizedTimestamp.replace(' ', 'T');
                }
                // Append Z to indicate UTC - JavaScript will convert to local time
                normalizedTimestamp = normalizedTimestamp + 'Z';
            }
            
            const date = new Date(normalizedTimestamp);
            
            // Validate the date is valid
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
                
                const color = sender === 'user' ? (this.theme.userTimestampColor || '#fff') : (this.theme.botTimestampColor || '#888');
                timeStr = `<span class="timestamp" style="font-size: 0.75em; color: ${color}; margin-left: 8px;">${displayTime}</span>`;
            }
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
        
        // Format message content - apply formatting for bot messages
        const formattedContent = sender === 'bot' ? this.formatBotResponse(content) : content;
        const senderLabel = sender === 'bot' ? `<strong>${this.getBotDisplayName()}:</strong>` : '<strong>You:</strong>';
        
        // Check if message has a summary (for long AI responses)
        const hasSummary = metadata.has_summary && metadata.summary;
        const summary = metadata.summary || '';
        
        // Add pin button (WhatsApp-style)
        const pinButton = `<button class="pin-btn" title="Pin message" onclick="MessageHandler.pinMessage(this)" 
            data-content="${content.replace(/"/g, '&quot;').replace(/'/g, '&#39;')}" 
            data-role="${role}" 
            data-timestamp="${timestamp || ''}"
            style="opacity: 0; position: absolute; right: 5px; top: 5px; background: none; border: none; cursor: pointer; font-size: 14px; transition: opacity 0.2s;">📌</button>`;
        
        // Add reply button (WhatsApp-style) - use data attributes to avoid escaping issues
        const messageId = metadata.id || metadata.message_id || Date.now();
        const safeContent = content.substring(0, 100).replace(/[\n\r]/g, ' ').replace(/[<>]/g, '');
        const replyButton = `<button class="reply-btn" title="Reply to this message" 
            data-msg-id="${messageId}"
            data-msg-content="${encodeURIComponent(safeContent)}"
            data-msg-role="${role}"
            style="opacity: 0; position: absolute; right: 30px; top: 5px; background: none; border: none; cursor: pointer; font-size: 14px; transition: opacity 0.2s;">↩️</button>`;
        
        // Add expand button for messages with summaries
        const expandButton = hasSummary ? `<button class="expand-btn" title="Show full response" 
            onclick="MessageHandler.toggleExpand(this)"
            style="opacity: 0; position: absolute; right: 55px; top: 5px; background: none; border: none; cursor: pointer; font-size: 14px; transition: opacity 0.2s;">📖</button>` : '';
        
        // Store message ID on the element for reference
        messageDiv.dataset.messageId = messageId;
        
        // Build content with summary/full toggle if applicable
        let displayContent;
        if (hasSummary) {
            const formattedSummary = this.formatBotResponse(summary);
            displayContent = `
                <div class="summary-content" style="display: block;">
                    <div style="background: linear-gradient(135deg, #e8f5e9, #c8e6c9); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #4CAF50;">
                        <div style="font-size: 0.85em; color: #2E7D32; font-weight: bold; margin-bottom: 4px;">📋 Summary</div>
                        ${formattedSummary}
                    </div>
                    <button onclick="MessageHandler.toggleExpand(this)" 
                        style="background: #E3F2FD; border: 1px solid #2196F3; border-radius: 4px; padding: 6px 12px; cursor: pointer; font-size: 0.85em; color: #1976D2;">
                        📖 Read Full Response
                    </button>
                </div>
                <div class="full-content" style="display: none;">
                    ${formattedContent}
                    <button onclick="MessageHandler.toggleExpand(this)" 
                        style="background: #FFF3E0; border: 1px solid #FF9800; border-radius: 4px; padding: 6px 12px; cursor: pointer; font-size: 0.85em; color: #E65100; margin-top: 8px;">
                        📋 Show Summary
                    </button>
                </div>
            `;
        } else {
            displayContent = formattedContent;
        }
        
        bubble.innerHTML = `${expandButton}${replyButton}${pinButton}${senderLabel} ${displayContent}${sourceBadge}${timeStr}`;
        bubble.style.position = 'relative';
        
        // Show pin, reply, and expand buttons on hover
        bubble.addEventListener('mouseenter', () => {
            const pinBtn = bubble.querySelector('.pin-btn');
            const replyBtn = bubble.querySelector('.reply-btn');
            const expandBtn = bubble.querySelector('.expand-btn');
            if (pinBtn) pinBtn.style.opacity = '1';
            if (replyBtn) replyBtn.style.opacity = '1';
            if (expandBtn) expandBtn.style.opacity = '1';
        });
        bubble.addEventListener('mouseleave', () => {
            const pinBtn = bubble.querySelector('.pin-btn');
            const replyBtn = bubble.querySelector('.reply-btn');
            const expandBtn = bubble.querySelector('.expand-btn');
            if (pinBtn) pinBtn.style.opacity = '0';
            if (replyBtn) replyBtn.style.opacity = '0';
            if (expandBtn) expandBtn.style.opacity = '0';
        });
        
        // Add click handler for reply button (using data attributes to avoid escaping issues)
        const replyBtn = bubble.querySelector('.reply-btn');
        if (replyBtn) {
            replyBtn.addEventListener('click', () => {
                const msgId = replyBtn.dataset.msgId;
                const msgContent = decodeURIComponent(replyBtn.dataset.msgContent || '');
                const msgRole = replyBtn.dataset.msgRole;
                this.setReplyTo(msgId, msgContent, msgRole);
            });
        }
        
        messageDiv.appendChild(bubble);
        this.messagesContainer.appendChild(messageDiv);
        
        // Debug log
        const preview = content.substring(0, 30);
        console.log(`✅ Added ${sender} message to DOM: "${preview}..." ${source ? `[${source}]` : ''} timestamp=${timestamp ? 'YES' : 'NO'}: ${timestamp}`);
        console.log(`   timeStr generated: "${timeStr.substring(0, 80)}..."`);
        console.log(`   Full bubble HTML: "${bubble.innerHTML.substring(0, 150)}..."`);
        
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
     * Format bot response for better readability
     * - Converts bullet points (-, *, •) to proper list items
     * - Converts numbered lists (1., 2., etc.) to proper formatting
     * - Adds paragraph breaks for better spacing
     * - Preserves markdown-style formatting
     * 
     * @param {string} content - Raw message content
     * @returns {string} Formatted HTML content
     */
    formatBotResponse(content) {
        if (!content) return '';
        
        // Split by newlines first
        let lines = content.split(/\n/);
        let formatted = [];
        let inList = false;
        let listType = null; // 'ul' or 'ol'
        
        for (let i = 0; i < lines.length; i++) {
            let line = lines[i].trim();
            
            // Skip empty lines but add spacing
            if (!line) {
                if (inList) {
                    formatted.push(listType === 'ul' ? '</ul>' : '</ol>');
                    inList = false;
                    listType = null;
                }
                formatted.push('<br>');
                continue;
            }
            
            // Check for bullet points (-, *, •)
            const bulletMatch = line.match(/^[-*•]\s+(.+)$/);
            if (bulletMatch) {
                if (!inList || listType !== 'ul') {
                    if (inList) formatted.push(listType === 'ul' ? '</ul>' : '</ol>');
                    formatted.push('<ul style="margin: 8px 0; padding-left: 20px;">');
                    inList = true;
                    listType = 'ul';
                }
                formatted.push(`<li style="margin: 4px 0;">${bulletMatch[1]}</li>`);
                continue;
            }
            
            // Check for numbered lists (1., 2., etc.) - use manual numbering for reliability
            const numberMatch = line.match(/^(\d+)[.)]\s+(.+)$/);
            if (numberMatch) {
                const itemNumber = numberMatch[1];
                if (!inList || listType !== 'ol') {
                    if (inList) formatted.push('</div>');
                    formatted.push('<div class="numbered-list" style="margin: 8px 0;">');
                    inList = true;
                    listType = 'ol';
                }
                formatted.push(`<div style="margin: 6px 0; padding-left: 8px; display: flex; gap: 8px;"><span style="font-weight: bold; color: #1976D2; min-width: 20px;">${itemNumber}.</span><span>${numberMatch[2]}</span></div>`);
                continue;
            }
            
            // Close any open list
            if (inList) {
                formatted.push(listType === 'ul' ? '</ul>' : '</div>');
                inList = false;
                listType = null;
            }
            
            // Check for headers (## or bold at start)
            if (line.startsWith('##')) {
                line = `<strong style="display: block; margin: 10px 0 5px 0;">${line.replace(/^#+\s*/, '')}</strong>`;
            } else if (line.startsWith('**') && line.endsWith('**')) {
                line = `<strong style="display: block; margin: 10px 0 5px 0;">${line.slice(2, -2)}</strong>`;
            }
            
            // Convert inline bold (**text**)
            line = line.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            
            // Convert inline italic (*text* or _text_)
            line = line.replace(/\*([^*]+)\*/g, '<em>$1</em>');
            line = line.replace(/_([^_]+)_/g, '<em>$1</em>');
            
            // Convert inline code (`code`)
            line = line.replace(/`([^`]+)`/g, '<code style="background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">$1</code>');
            
            // Wrap in paragraph
            formatted.push(`<p style="margin: 6px 0;">${line}</p>`);
        }
        
        // Close any remaining open list
        if (inList) {
            formatted.push(listType === 'ul' ? '</ul>' : '</div>');
        }
        
        return formatted.join('');
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
                
                // Load and apply highlights after messages are displayed
                if (this.highlightsEnabled) {
                    this.applyStoredHighlights();
                }
                
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
    
    // ==================== SUMMARY EXPAND/COLLAPSE FEATURE ====================
    
    /**
     * Toggle between summary and full response
     * @param {HTMLElement} button - The clicked button element
     */
    toggleExpand(button) {
        // Find the parent message bubble
        const bubble = button.closest('.message-content, .message-bubble, [class*="bubble"]') || button.parentElement.parentElement;
        if (!bubble) return;
        
        const summaryDiv = bubble.querySelector('.summary-content');
        const fullDiv = bubble.querySelector('.full-content');
        
        if (!summaryDiv || !fullDiv) return;
        
        // Toggle visibility
        if (summaryDiv.style.display !== 'none') {
            summaryDiv.style.display = 'none';
            fullDiv.style.display = 'block';
            console.log('📖 Expanded to full response');
        } else {
            summaryDiv.style.display = 'block';
            fullDiv.style.display = 'none';
            console.log('📋 Collapsed to summary');
        }
    },
    
    // ==================== REPLY-TO FEATURE (WhatsApp-style) ====================
    
    /**
     * Set the message being replied to
     * Shows a preview above the input field
     */
    setReplyTo(messageId, content, senderType) {
        this.replyingTo = {
            id: messageId,
            content: content.substring(0, 100),
            sender_type: senderType
        };
        
        // Show reply preview UI
        this.showReplyPreview();
        
        // Focus the input
        const input = document.getElementById('userInput');
        if (input) input.focus();
        
        console.log(`↩️ Replying to message ${messageId}: "${content.substring(0, 30)}..."`);
    },
    
    /**
     * Clear the reply-to state
     */
    clearReplyTo() {
        this.replyingTo = null;
        this.hideReplyPreview();
        console.log('↩️ Reply cleared');
    },
    
    /**
     * Get the current reply-to message ID (for sending)
     */
    getReplyToId() {
        return this.replyingTo?.id || null;
    },
    
    /**
     * Show the reply preview above the input
     */
    showReplyPreview() {
        // Remove existing preview
        this.hideReplyPreview();
        
        if (!this.replyingTo) return;
        
        // Find input container - try multiple selectors for different templates
        const selectors = [
            '#chat-input-area',
            '.chat-input-area', 
            '.message-input-area',
            '.message-input',
            '.chat-input',
            '.input-container',
            '.input-group'
        ];
        
        let inputContainer = null;
        for (const selector of selectors) {
            inputContainer = document.querySelector(selector);
            if (inputContainer) break;
        }
        
        if (!inputContainer) {
            console.warn('Could not find input container for reply preview');
            return;
        }
        
        const sender = this.replyingTo.sender_type === 'assistant' ? this.getBotDisplayName() : 'You';
        
        const preview = document.createElement('div');
        preview.id = 'reply-preview';
        preview.style.cssText = `
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            border-left: 4px solid #2196F3;
            padding: 8px 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
        `;
        preview.innerHTML = `
            <div style="flex: 1; overflow: hidden;">
                <div style="font-weight: bold; color: #1976D2; margin-bottom: 2px;">↩️ Replying to ${sender}</div>
                <div style="color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    ${this.replyingTo.content}...
                </div>
            </div>
            <button onclick="MessageHandler.clearReplyTo()" 
                style="background: none; border: none; cursor: pointer; font-size: 18px; padding: 4px; color: #666;"
                title="Cancel reply">✕</button>
        `;
        
        inputContainer.insertBefore(preview, inputContainer.firstChild);
    },
    
    /**
     * Hide the reply preview
     */
    hideReplyPreview() {
        const existing = document.getElementById('reply-preview');
        if (existing) existing.remove();
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
    },
    
    // ==================== CONVERSATION HIGHLIGHTS ====================
    
    highlightsEnabled: false,
    currentCharacterId: null,
    
    /**
     * Enable text highlighting on messages
     * Users can select text and save it as a highlight
     */
    enableHighlights(characterId = null) {
        this.highlightsEnabled = true;
        this.currentCharacterId = characterId;
        
        // Add highlight styles if not already added
        if (!document.getElementById('highlight-styles')) {
            const styles = document.createElement('style');
            styles.id = 'highlight-styles';
            styles.textContent = `
                .message-content {
                    user-select: text;
                    cursor: text;
                }
                .highlight-popup {
                    position: fixed;
                    background: #333;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 13px;
                    z-index: 10000;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    display: none;
                }
                .highlight-popup button {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 4px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-left: 8px;
                    font-size: 12px;
                }
                .highlight-popup button:hover {
                    background: #45a049;
                }
                .saved-highlight {
                    background: linear-gradient(to bottom, rgba(76, 175, 80, 0.4), rgba(76, 175, 80, 0.2));
                    padding: 2px 4px;
                    border-radius: 3px;
                    border-bottom: 2px solid rgba(76, 175, 80, 0.6);
                }
                .saved-highlight-yellow {
                    background: linear-gradient(to bottom, rgba(255, 235, 59, 0.4), rgba(255, 235, 59, 0.2));
                    border-bottom-color: rgba(255, 235, 59, 0.6);
                }
                .saved-highlight-blue {
                    background: linear-gradient(to bottom, rgba(33, 150, 243, 0.3), rgba(33, 150, 243, 0.15));
                    border-bottom-color: rgba(33, 150, 243, 0.6);
                }
                .saved-highlight-pink {
                    background: linear-gradient(to bottom, rgba(233, 30, 99, 0.3), rgba(233, 30, 99, 0.15));
                    border-bottom-color: rgba(233, 30, 99, 0.6);
                }
                .highlights-panel {
                    position: fixed;
                    right: 20px;
                    top: 80px;
                    width: 320px;
                    max-height: 70vh;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    z-index: 9999;
                    display: none;
                    overflow: hidden;
                }
                .highlights-panel-header {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 15px;
                    font-weight: 600;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .highlights-panel-content {
                    max-height: calc(70vh - 60px);
                    overflow-y: auto;
                    padding: 10px;
                }
                .highlight-item {
                    background: #f8f9fa;
                    border-left: 4px solid #ffc107;
                    padding: 12px;
                    margin-bottom: 10px;
                    border-radius: 0 8px 8px 0;
                    position: relative;
                }
                .highlight-item .highlight-text {
                    font-style: italic;
                    color: #333;
                    margin-bottom: 8px;
                }
                .highlight-item .highlight-meta {
                    font-size: 11px;
                    color: #666;
                }
                .highlight-item .highlight-delete {
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: none;
                    border: none;
                    color: #999;
                    cursor: pointer;
                    font-size: 16px;
                }
                .highlight-item .highlight-delete:hover {
                    color: #e74c3c;
                }
                .highlights-toggle {
                    position: fixed;
                    right: 20px;
                    top: 80px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 20px;
                    cursor: pointer;
                    z-index: 9998;
                    font-size: 13px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }
                .highlights-toggle:hover {
                    transform: scale(1.05);
                }
            `;
            document.head.appendChild(styles);
        }
        
        // Create highlight popup with color options
        if (!document.getElementById('highlight-popup')) {
            const popup = document.createElement('div');
            popup.id = 'highlight-popup';
            popup.className = 'highlight-popup';
            popup.innerHTML = `
                <span style="margin-right:8px;">Highlight:</span>
                <button onclick="MessageHandler.saveSelectedHighlight('green')" style="background:#4CAF50;" title="Green">
                    <i class="fas fa-bookmark"></i>
                </button>
                <button onclick="MessageHandler.saveSelectedHighlight('yellow')" style="background:#FFC107;color:#333;" title="Yellow">
                    <i class="fas fa-bookmark"></i>
                </button>
                <button onclick="MessageHandler.saveSelectedHighlight('blue')" style="background:#2196F3;" title="Blue">
                    <i class="fas fa-bookmark"></i>
                </button>
                <button onclick="MessageHandler.saveSelectedHighlight('pink')" style="background:#E91E63;" title="Pink">
                    <i class="fas fa-bookmark"></i>
                </button>
            `;
            document.body.appendChild(popup);
        }
        
        // Create highlights panel
        if (!document.getElementById('highlights-panel')) {
            const panel = document.createElement('div');
            panel.id = 'highlights-panel';
            panel.className = 'highlights-panel';
            panel.innerHTML = `
                <div class="highlights-panel-header">
                    <span><i class="fas fa-bookmark"></i> My Highlights</span>
                    <button onclick="MessageHandler.toggleHighlightsPanel()" style="background:none;border:none;color:white;cursor:pointer;font-size:18px;">&times;</button>
                </div>
                <div class="highlights-panel-content" id="highlights-list">
                    <p style="text-align:center;color:#888;padding:20px;">Loading...</p>
                </div>
            `;
            document.body.appendChild(panel);
        }
        
        // Skip floating toggle button if header button exists (Life Companion page)
        // The header already has highlightsBtn
        
        // Listen for text selection
        document.addEventListener('mouseup', (e) => this._handleTextSelection(e));
        
        console.log('✅ Highlights enabled');
    },
    
    _handleTextSelection(e) {
        if (!this.highlightsEnabled) return;
        
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        const popup = document.getElementById('highlight-popup');
        
        if (selectedText.length > 3) {
            // Check if selection is within a message (support various message class patterns)
            const range = selection.getRangeAt(0);
            const messageEl = range.commonAncestorContainer.closest ? 
                range.commonAncestorContainer.closest('.message, .message-bubble, .message-content, .message-life, .message-sci, [class*="message"]') :
                range.commonAncestorContainer.parentElement?.closest('.message, .message-bubble, .message-content, .message-life, .message-sci, [class*="message"]');
            
            if (messageEl) {
                // Store selection data including element reference for highlighting
                this._pendingHighlight = {
                    text: selectedText,
                    fullMessage: messageEl.textContent,
                    role: messageEl.classList.contains('user') || messageEl.closest('.user') ? 'user' : 'assistant',
                    messageElement: messageEl
                };
                
                // Position and show popup near selection
                const rect = range.getBoundingClientRect();
                popup.style.left = `${rect.left + rect.width/2 - 60}px`;
                popup.style.top = `${rect.bottom + 10}px`;
                popup.style.display = 'block';
                return;
            }
        }
        
        // Hide popup if click is not on popup itself
        if (!e.target.closest('.highlight-popup')) {
            popup.style.display = 'none';
        }
    },
    
    async saveSelectedHighlight(color = 'green') {
        if (!this._pendingHighlight) return;
        
        const popup = document.getElementById('highlight-popup');
        popup.style.display = 'none';
        
        // Get the current selection and apply highlight BEFORE async call
        const selection = window.getSelection();
        const textToHighlight = this._pendingHighlight.text;
        const messageEl = this._pendingHighlight.messageElement;
        
        // Apply visual highlight immediately
        let highlightApplied = false;
        if (selection.rangeCount > 0) {
            try {
                const range = selection.getRangeAt(0);
                highlightApplied = this._applyHighlightToRange(range, color, 'pending');
            } catch (e) {
                console.log('Could not apply highlight directly, will try text search');
            }
        }
        
        // If direct highlight failed, try finding and highlighting the text in the message
        if (!highlightApplied && messageEl && textToHighlight) {
            this._highlightTextInElement(messageEl, textToHighlight, color, 'pending');
        }
        
        // Clear selection
        window.getSelection().removeAllRanges();
        
        // Save to database
        try {
            const response = await AuthHelper.authenticatedFetch('/api/user/highlights', {
                method: 'POST',
                body: JSON.stringify({
                    highlighted_text: textToHighlight,
                    full_message: this._pendingHighlight.fullMessage,
                    message_role: this._pendingHighlight.role,
                    character_id: this.currentCharacterId,
                    color: color
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Update pending highlight with actual ID
                const pendingSpan = document.querySelector('.saved-highlight[data-highlight-id="pending"]');
                if (pendingSpan) {
                    pendingSpan.dataset.highlightId = data.highlight_id;
                }
                this._showToast('Highlight saved!');
            } else {
                // Remove the visual highlight if save failed
                const pendingSpan = document.querySelector('.saved-highlight[data-highlight-id="pending"]');
                if (pendingSpan) {
                    pendingSpan.outerHTML = pendingSpan.innerHTML;
                }
                this._showToast('Failed to save highlight', 'error');
            }
        } catch (error) {
            console.error('Error saving highlight:', error);
            this._showToast('Error saving highlight', 'error');
        }
        
        this._pendingHighlight = null;
    },
    
    _applyHighlightToRange(range, color, highlightId) {
        try {
            const span = document.createElement('span');
            span.className = `saved-highlight${color !== 'green' ? ` saved-highlight-${color}` : ''}`;
            span.dataset.highlightId = highlightId;
            range.surroundContents(span);
            return true;
        } catch (e) {
            // If surroundContents fails (selection spans multiple elements), use alternative method
            try {
                const contents = range.extractContents();
                const span = document.createElement('span');
                span.className = `saved-highlight${color !== 'green' ? ` saved-highlight-${color}` : ''}`;
                span.dataset.highlightId = highlightId;
                span.appendChild(contents);
                range.insertNode(span);
                return true;
            } catch (e2) {
                console.error('Failed to apply highlight:', e2);
                return false;
            }
        }
    },
    
    _highlightTextInElement(element, text, color, highlightId) {
        // Find and highlight text within an element using TreeWalker
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
        let node;
        let textNodes = [];
        
        // Collect all text nodes
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        
        // Try to find the text in the combined text content
        const fullText = textNodes.map(n => n.textContent).join('');
        let idx = fullText.indexOf(text);
        let searchLength = text.length;
        
        // If not found with exact text, try normalized version
        if (idx < 0) {
            const normalizeText = (t) => t.replace(/\s+/g, ' ').trim();
            const normalizedFull = normalizeText(fullText);
            const normalizedSearch = normalizeText(text);
            const normalizedIdx = normalizedFull.indexOf(normalizedSearch);
            
            if (normalizedIdx >= 0) {
                // Map normalized position back to original text position
                let origPos = 0;
                let normPos = 0;
                
                // Scan through original text, building normalized version until we reach normalizedIdx
                while (normPos < normalizedIdx && origPos < fullText.length) {
                    const char = fullText[origPos];
                    if (char.match(/\s/)) {
                        // Skip consecutive whitespace in original
                        while (origPos < fullText.length && fullText[origPos].match(/\s/)) {
                            origPos++;
                        }
                        normPos++; // One space in normalized
                    } else {
                        origPos++;
                        normPos++;
                    }
                }
                
                idx = origPos;
                
                // Calculate the actual length in original text
                normPos = 0;
                let origEndPos = origPos;
                while (normPos < normalizedSearch.length && origEndPos < fullText.length) {
                    const char = fullText[origEndPos];
                    if (char.match(/\s/)) {
                        while (origEndPos < fullText.length && fullText[origEndPos].match(/\s/)) {
                            origEndPos++;
                        }
                        normPos++;
                    } else {
                        origEndPos++;
                        normPos++;
                    }
                }
                searchLength = origEndPos - origPos;
            }
        }
        
        if (idx >= 0) {
            // Find which text node(s) contain this text
            let currentPos = 0;
            for (let i = 0; i < textNodes.length; i++) {
                const nodeText = textNodes[i].textContent;
                const nodeStart = currentPos;
                const nodeEnd = currentPos + nodeText.length;
                
                // Check if this node contains the start of our text
                if (idx >= nodeStart && idx < nodeEnd) {
                    const startOffset = idx - nodeStart;
                    const endOffset = Math.min(startOffset + searchLength, nodeText.length);
                    
                    try {
                        const range = document.createRange();
                        range.setStart(textNodes[i], startOffset);
                        
                        // Check if text spans multiple nodes
                        if (idx + searchLength <= nodeEnd) {
                            // Text is within this single node
                            range.setEnd(textNodes[i], endOffset);
                        } else {
                            // Text spans multiple nodes - just highlight what we can in this node
                            range.setEnd(textNodes[i], nodeText.length);
                        }
                        
                        this._applyHighlightToRange(range, color, highlightId);
                        return true;
                    } catch (e) {
                        console.error('Error creating range:', e);
                    }
                }
                
                currentPos = nodeEnd;
            }
        }
        
        return false;
    },
    
    _highlightTextInElementNormalized(element, normalizedText, color, highlightId) {
        // Fallback: try to find and highlight using normalized text matching
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
        let node;
        const normalizeText = (t) => t.replace(/\s+/g, ' ').trim();
        
        while (node = walker.nextNode()) {
            const normalized = normalizeText(node.textContent);
            if (normalized.includes(normalizedText)) {
                try {
                    const range = document.createRange();
                    range.selectNodeContents(node);
                    this._applyHighlightToRange(range, color, highlightId);
                    return true;
                } catch (e) {
                    console.error('Error in normalized highlight:', e);
                }
            }
        }
        return false;
    },
    
    async toggleHighlightsPanel() {
        const panel = document.getElementById('highlights-panel');
        const isVisible = panel.style.display === 'block';
        
        if (isVisible) {
            panel.style.display = 'none';
        } else {
            panel.style.display = 'block';
            await this.loadHighlights();
        }
    },
    
    async loadHighlights() {
        const list = document.getElementById('highlights-list');
        if (!list) return;
        
        try {
            const url = this.currentCharacterId ? 
                `/api/user/highlights?character_id=${this.currentCharacterId}` : 
                '/api/user/highlights';
            
            const response = await AuthHelper.authenticatedFetch(url);
            
            // Check if authentication failed
            if (response.status === 401) {
                list.innerHTML = `
                    <p style="text-align:center;color:#e74c3c;padding:20px;">
                        Session expired.<br>
                        <small>Please <a href="/login" style="color:#3498db;">log in</a> again to view highlights.</small>
                    </p>
                `;
                return;
            }
            
            const data = await response.json();
            
            if (data.highlights && data.highlights.length > 0) {
                list.innerHTML = data.highlights.map(h => `
                    <div class="highlight-item" data-id="${h.id}">
                        <button class="highlight-delete" onclick="MessageHandler.deleteHighlight(${h.id})">&times;</button>
                        <div class="highlight-text">"${this._escapeHtml(h.highlighted_text)}"</div>
                        <div class="highlight-meta">
                            ${h.character_id ? `<strong>${h.character_id}</strong> · ` : ''}
                            ${h.message_role || 'message'} · 
                            ${new Date(h.created_at).toLocaleDateString()}
                        </div>
                    </div>
                `).join('');
            } else {
                list.innerHTML = `
                    <p style="text-align:center;color:#888;padding:20px;">
                        No highlights yet.<br>
                        <small>Select text in messages to save highlights.</small>
                    </p>
                `;
            }
        } catch (error) {
            console.error('Error loading highlights:', error);
            list.innerHTML = `
                <p style="text-align:center;color:#e74c3c;padding:20px;">
                    Error loading highlights.<br>
                    <small>Please refresh the page.</small>
                </p>
            `;
        }
    },
    
    async deleteHighlight(highlightId) {
        if (!confirm('Delete this highlight?')) return;
        
        try {
            const response = await AuthHelper.authenticatedFetch(`/api/user/highlights/${highlightId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            if (data.success) {
                // Remove from DOM
                const item = document.querySelector(`.highlight-item[data-id="${highlightId}"]`);
                if (item) item.remove();
                this._showToast('Highlight deleted');
            }
        } catch (error) {
            console.error('Error deleting highlight:', error);
        }
    },
    
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    _showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: ${type === 'error' ? '#e74c3c' : '#4CAF50'};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 10001;
            font-size: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 2500);
    },
    
    async applyStoredHighlights() {
        if (!this.currentCharacterId) {
            console.log('⚠️ Cannot apply highlights: currentCharacterId not set');
            return;
        }
        
        try {
            const url = `/api/user/highlights?character_id=${this.currentCharacterId}`;
            console.log(`Fetching highlights from: ${url}`);
            const response = await AuthHelper.authenticatedFetch(url);
            
            // Check if authentication failed
            if (response.status === 401) {
                console.log('⚠️ Session expired - cannot apply highlights');
                return;
            }
            
            const data = await response.json();
            
            console.log('Highlights API response:', data);
            
            if (data.highlights && data.highlights.length > 0) {
                console.log(`Applying ${data.highlights.length} stored highlights for ${this.currentCharacterId}`);
                
                // Get all message elements - try multiple selectors
                const messages = this.messagesContainer.querySelectorAll('.message, .message-bubble, .message-content, [class*="message"]');
                console.log(`Found ${messages.length} message elements to search`);
                
                let appliedCount = 0;
                data.highlights.forEach((highlight, idx) => {
                    console.log(`  Highlight ${idx + 1}: "${highlight.highlighted_text.substring(0, 50)}..." (color: ${highlight.color})`);
                    
                    // Find the message containing this highlight text
                    let found = false;
                    for (let i = 0; i < messages.length; i++) {
                        const messageEl = messages[i];
                        const messageText = messageEl.textContent;
                        
                        // Normalize both texts for comparison (remove extra whitespace, normalize line breaks)
                        const normalizeText = (text) => text.replace(/\s+/g, ' ').trim();
                        const normalizedHighlight = normalizeText(highlight.highlighted_text);
                        const normalizedMessage = normalizeText(messageText);
                        
                        if (normalizedMessage.includes(normalizedHighlight)) {
                            console.log(`    ✓ Found in message element ${i}`);
                            // Apply highlight using the original (non-normalized) text
                            const success = this._highlightTextInElement(messageEl, highlight.highlighted_text, highlight.color || 'green', highlight.id);
                            if (success) {
                                appliedCount++;
                                found = true;
                                break;
                            } else {
                                console.log(`    ✗ _highlightTextInElement failed - trying with normalized text`);
                                // Try again with normalized text
                                const success2 = this._highlightTextInElementNormalized(messageEl, normalizedHighlight, highlight.color || 'green', highlight.id);
                                if (success2) {
                                    appliedCount++;
                                    found = true;
                                    break;
                                }
                            }
                        }
                    }
                    if (!found) {
                        console.log(`    ✗ Text not found in any of ${messages.length} messages`);
                    }
                });
                
                console.log(`✅ Applied ${appliedCount}/${data.highlights.length} stored highlights`);
            } else {
                console.log('No highlights to apply');
            }
        } catch (error) {
            console.error('Error applying stored highlights:', error);
        }
    },
    
    // ==================== PINNED MESSAGES (WhatsApp-style) ====================
    
    /**
     * Pin a message
     * @param {HTMLElement} button - The pin button clicked
     */
    async pinMessage(button) {
        const content = button.dataset.content;
        const role = button.dataset.role;
        const timestamp = button.dataset.timestamp;
        
        try {
            // Use currentCharacterId (matches what's used when loading) for consistency
            const characterId = this.currentCharacterId || this.characterName || 'coordinator';
            const response = await AuthHelper.authenticatedFetch('/api/user/pinned-messages', {
                method: 'POST',
                body: JSON.stringify({
                    content: content,
                    role: role,
                    timestamp: timestamp,
                    character_id: characterId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Visual feedback
                button.textContent = '📍';
                button.title = 'Pinned!';
                button.style.opacity = '1';
                setTimeout(() => {
                    button.textContent = '📌';
                    button.title = 'Pin message';
                    button.style.opacity = '0';
                }, 1500);
                
                // Refresh pinned messages panel if visible
                this.loadPinnedMessages();
                
                console.log('📌 Message pinned successfully');
            } else {
                alert(data.error || 'Failed to pin message');
            }
        } catch (error) {
            console.error('Error pinning message:', error);
            alert('Failed to pin message');
        }
    },
    
    /**
     * Load and display pinned messages
     */
    async loadPinnedMessages() {
        const panel = document.getElementById('pinned-messages-panel');
        if (!panel) return;
        
        try {
            // On domain-characters page, fetch ALL pins (including old ones saved as 'domain-characters')
            // This ensures backward compatibility with existing pins
            const isDomainPage = this.characterName === 'domain-characters';
            const url = isDomainPage 
                ? '/api/user/pinned-messages'  // Fetch all pins on domain page
                : `/api/user/pinned-messages?character_id=${this.currentCharacterId || this.characterName}`;
            const response = await AuthHelper.authenticatedFetch(url);
            const data = await response.json();
            
            if (data.success && data.pinned_messages) {
                this.renderPinnedMessages(data.pinned_messages);
            }
        } catch (error) {
            console.error('Error loading pinned messages:', error);
        }
    },
    
    /**
     * Render pinned messages in the panel
     * @param {Array} pinnedMessages - Array of pinned message objects
     */
    renderPinnedMessages(pinnedMessages) {
        const panel = document.getElementById('pinned-messages-panel');
        const content = document.getElementById('pinned-messages-content');
        if (!content) return;
        
        if (pinnedMessages.length === 0) {
            content.innerHTML = '<p style="color: #888; text-align: center; padding: 10px;">No pinned messages yet.<br>Hover over a message and click 📌 to pin it.</p>';
            return;
        }
        
        content.innerHTML = pinnedMessages.map(pin => {
            const isLong = pin.content.length > 150;
            const shortContent = isLong ? pin.content.substring(0, 150) + '...' : pin.content;
            const fullContent = pin.content.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            
            return `
            <div class="pinned-message" data-pin-id="${pin.id}" data-content="${encodeURIComponent(pin.content.substring(0, 100))}" data-timestamp="${pin.timestamp || ''}" style="background: ${pin.role === 'user' ? 'linear-gradient(135deg, #667eea22, #764ba222)' : '#f5f5f5'}; padding: 10px; margin-bottom: 8px; border-radius: 8px; position: relative; border-left: 3px solid ${pin.role === 'user' ? '#667eea' : '#26a69a'};">
                <div style="position: absolute; right: 5px; top: 5px; display: flex; gap: 8px;">
                    <button onclick="MessageHandler.goToMessageFromPin(this)" style="background: none; border: none; cursor: pointer; font-size: 11px; opacity: 0.6; color: #667eea;" title="Go to message">↗️</button>
                    <button onclick="MessageHandler.unpinMessage(${pin.id})" style="background: none; border: none; cursor: pointer; font-size: 12px; opacity: 0.6;" title="Unpin">✕</button>
                </div>
                <div style="font-size: 0.75em; color: #888; margin-bottom: 4px;">
                    ${pin.role === 'user' ? 'You' : 'Bot'} • ${this.formatPinTimestamp(pin.timestamp)}
                </div>
                <div class="pin-content-short" style="font-size: 0.9em; line-height: 1.4;">${shortContent}</div>
                ${isLong ? `
                    <div class="pin-content-full" style="display: none; font-size: 0.9em; line-height: 1.4; white-space: pre-wrap; max-height: 200px; overflow-y: auto; padding-bottom: 30px;">${fullContent}</div>
                    <button class="expand-pin-btn" onclick="MessageHandler.togglePinExpand(this)" style="background: none; border: none; color: #667eea; cursor: pointer; font-size: 0.8em; padding: 4px 0; margin-top: 4px;">▼ Show more</button>
                    <button class="collapse-pin-btn" onclick="MessageHandler.togglePinExpand(this)" style="display: none; position: sticky; bottom: 0; left: 0; right: 0; width: 100%; background: linear-gradient(transparent, ${pin.role === 'user' ? '#f0f0ff' : '#f5f5f5'} 30%); border: none; color: #667eea; cursor: pointer; font-size: 0.8em; padding: 8px 0 4px; margin-top: -24px;">▲ Show less</button>
                ` : ''}
                ${pin.note ? `<div style="font-size: 0.75em; color: #667eea; margin-top: 4px; font-style: italic;">📝 ${pin.note}</div>` : ''}
            </div>
        `}).join('');
    },
    
    /**
     * Toggle expand/collapse for a pinned message
     * @param {HTMLElement} button - The expand button clicked
     */
    togglePinExpand(button) {
        const container = button.closest('.pinned-message');
        const shortContent = container.querySelector('.pin-content-short');
        const fullContent = container.querySelector('.pin-content-full');
        const expandBtn = container.querySelector('.expand-pin-btn');
        const collapseBtn = container.querySelector('.collapse-pin-btn');
        
        if (fullContent.style.display === 'none') {
            // Expand
            shortContent.style.display = 'none';
            fullContent.style.display = 'block';
            if (expandBtn) expandBtn.style.display = 'none';
            if (collapseBtn) collapseBtn.style.display = 'block';
        } else {
            // Collapse
            shortContent.style.display = 'block';
            fullContent.style.display = 'none';
            if (expandBtn) expandBtn.style.display = 'block';
            if (collapseBtn) collapseBtn.style.display = 'none';
        }
    },
    
    /**
     * Go to message from pin button click (reads from data attributes)
     * @param {HTMLElement} button - The button clicked
     */
    goToMessageFromPin(button) {
        const container = button.closest('.pinned-message');
        if (!container) return;
        
        const encodedContent = container.dataset.content || '';
        const timestamp = container.dataset.timestamp || '';
        const contentSnippet = decodeURIComponent(encodedContent);
        
        this.goToMessage(contentSnippet, timestamp);
    },
    
    /**
     * Go to (scroll to and highlight) the original message in chat
     * @param {string} contentSnippet - First 100 chars of message content to match
     * @param {string} timestamp - Message timestamp to help identify
     */
    async goToMessage(contentSnippet, timestamp) {
        // Close the pinned panel first
        const panel = document.getElementById('pinned-messages-panel');
        if (panel) panel.style.display = 'none';
        document.getElementById('pinnedBtn')?.classList.remove('active');
        
        // First try to find in current view
        let targetMessage = this._findMessageInView(contentSnippet);
        
        if (targetMessage) {
            this._highlightAndScrollTo(targetMessage);
            return;
        }
        
        // Message not in current view - try to load more history
        console.log('📍 Message not in current view, loading more history...');
        
        // Try to load more history (up to 500 messages)
        const characterId = this.currentCharacterId || this.characterName || 'coordinator';
        try {
            // Determine the right API endpoint based on page type
            const isDomainPage = typeof DomainCharacters !== 'undefined';
            const isConversationBox = typeof ConversationBox !== 'undefined' && ConversationBox.config;
            
            let historyLoaded = false;
            
            if (isDomainPage) {
                const response = await AuthHelper.authenticatedFetch(
                    `/api/domain-characters/history/${characterId}?limit=500`
                );
                const data = await response.json();
                
                if (data.success && data.history && data.history.length > 0) {
                    if (DomainCharacters._reloadHistoryWithData) {
                        await DomainCharacters._reloadHistoryWithData(data.history, characterId);
                        historyLoaded = true;
                    }
                }
            } else if (isConversationBox && ConversationBox.config.historyEndpoint) {
                const response = await AuthHelper.authenticatedFetch(
                    `${ConversationBox.config.historyEndpoint}?limit=500`
                );
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    if (ConversationBox._reloadHistoryWithData) {
                        await ConversationBox._reloadHistoryWithData(data.messages, characterId);
                        historyLoaded = true;
                    }
                }
            }
            
            if (historyLoaded) {
                // Wait for DOM to update, then try to find again
                await new Promise(resolve => setTimeout(resolve, 300));
                targetMessage = this._findMessageInView(contentSnippet);
                
                if (targetMessage) {
                    this._highlightAndScrollTo(targetMessage);
                    return;
                }
            }
        } catch (error) {
            console.error('Error loading history for pinned message:', error);
        }
        
        // Still not found
        alert('Message not found. It may have been deleted or is from a different character.');
    },
    
    /**
     * Find a message in the current view by content
     * @param {string} contentSnippet - Content to search for
     * @returns {HTMLElement|null} Message element or null
     */
    _findMessageInView(contentSnippet) {
        const messages = this.messagesContainer?.querySelectorAll('.message, .message-bubble') || [];
        
        for (const msg of messages) {
            const msgContent = msg.querySelector('.message-content, .bubble-content');
            if (msgContent) {
                const text = (msgContent.textContent || msgContent.innerText || '').toLowerCase();
                // Search anywhere in the message, not just at the start
                const snippet = contentSnippet.substring(0, 50).replace(/\\n/g, '\n').trim().toLowerCase();
                if (snippet.length > 10 && text.includes(snippet.substring(0, 30))) {
                    return msg;
                }
            }
        }
        return null;
    },
    
    /**
     * Highlight and scroll to a message element
     * @param {HTMLElement} targetMessage - Message element to highlight
     */
    _highlightAndScrollTo(targetMessage) {
        // Scroll to message (top of message visible at top of viewport)
        targetMessage.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Highlight effect
        const originalBg = targetMessage.style.background;
        targetMessage.style.transition = 'background 0.3s';
        targetMessage.style.background = 'linear-gradient(135deg, #fff3cd, #ffeeba)';
        targetMessage.style.boxShadow = '0 0 10px rgba(255, 193, 7, 0.5)';
        
        setTimeout(() => {
            targetMessage.style.background = originalBg || '';
            targetMessage.style.boxShadow = '';
        }, 2000);
        
        console.log('📍 Scrolled to pinned message');
    },
    
    /**
     * Format timestamp for pinned message display
     * @param {string} timestamp - ISO timestamp string
     * @returns {string} Formatted timestamp
     */
    formatPinTimestamp(timestamp) {
        if (!timestamp) return '';
        try {
            let normalizedTimestamp = timestamp;
            if (typeof timestamp === 'string') {
                normalizedTimestamp = timestamp.replace('Z', '').replace('+00:00', '');
                if (!normalizedTimestamp.includes('T')) {
                    normalizedTimestamp = normalizedTimestamp.replace(' ', 'T');
                }
                normalizedTimestamp = normalizedTimestamp + 'Z';
            }
            const date = new Date(normalizedTimestamp);
            if (isNaN(date.getTime())) return '';
            
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);
            
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            
            if (date.toDateString() === today.toDateString()) {
                return `${hours}:${minutes}`;
            } else if (date.toDateString() === yesterday.toDateString()) {
                return `yesterday ${hours}:${minutes}`;
            } else {
                const day = date.getDate().toString().padStart(2, '0');
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                return `${day}/${month} ${hours}:${minutes}`;
            }
        } catch (e) {
            return '';
        }
    },
    
    /**
     * Unpin a message
     * @param {number} pinId - The pin ID to remove
     */
    async unpinMessage(pinId) {
        try {
            const response = await AuthHelper.authenticatedFetch(`/api/user/pinned-messages/${pinId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Remove from UI
                const pinElement = document.querySelector(`[data-pin-id="${pinId}"]`);
                if (pinElement) {
                    pinElement.style.opacity = '0';
                    pinElement.style.transform = 'translateX(100%)';
                    setTimeout(() => pinElement.remove(), 300);
                }
                
                // Refresh panel
                setTimeout(() => this.loadPinnedMessages(), 350);
                
                console.log('📌 Message unpinned');
            }
        } catch (error) {
            console.error('Error unpinning message:', error);
        }
    },
    
    /**
     * Toggle pinned messages panel visibility
     */
    togglePinnedPanel() {
        const panel = document.getElementById('pinned-messages-panel');
        const highlightsPanel = document.getElementById('highlights-panel');
        const pinnedBtn = document.getElementById('pinnedBtn');
        
        if (!panel) return;
        
        const isVisible = panel.style.display !== 'none';
        
        // Close other panels first
        if (highlightsPanel) highlightsPanel.style.display = 'none';
        document.getElementById('highlightsBtn')?.classList.remove('active');
        
        panel.style.display = isVisible ? 'none' : 'block';
        pinnedBtn?.classList.toggle('active', !isVisible);
        
        if (!isVisible) {
            this.loadPinnedMessages();
        }
    },
    
    /**
     * Toggle highlights panel visibility
     */
    toggleHighlightsPanel() {
        const panel = document.getElementById('highlights-panel');
        const pinnedPanel = document.getElementById('pinned-messages-panel');
        const highlightsBtn = document.getElementById('highlightsBtn');
        
        if (!panel) return;
        
        const isVisible = panel.style.display !== 'none';
        
        // Close other panels first
        if (pinnedPanel) pinnedPanel.style.display = 'none';
        document.getElementById('pinnedBtn')?.classList.remove('active');
        
        panel.style.display = isVisible ? 'none' : 'block';
        highlightsBtn?.classList.toggle('active', !isVisible);
        
        if (!isVisible) {
            this.loadHighlightsPanel();
        }
    },
    
    /**
     * Load and display highlights in panel
     */
    async loadHighlightsPanel() {
        const content = document.getElementById('highlights-content');
        if (!content) return;
        
        try {
            // On domain-characters page, fetch ALL highlights (including old ones)
            const isDomainPage = this.characterName === 'domain-characters';
            const url = isDomainPage 
                ? '/api/user/highlights'  // Fetch all highlights on domain page
                : `/api/user/highlights?character_id=${this.currentCharacterId || this.characterName}`;
            const response = await AuthHelper.authenticatedFetch(url);
            const data = await response.json();
            
            if (data.highlights && data.highlights.length > 0) {
                content.innerHTML = data.highlights.map(h => {
                    const searchText = h.full_message || h.highlighted_text || '';
                    return `
                    <div class="panel-item" data-highlight-id="${h.id}" data-content="${encodeURIComponent(searchText.substring(0, 100))}">
                        <div style="position: absolute; right: 5px; top: 5px; display: flex; gap: 8px;">
                            <button onclick="MessageHandler.goToHighlightFromPanel(this)" style="background: none; border: none; cursor: pointer; font-size: 11px; opacity: 0.6; color: #667eea;" title="Go to message">↗️</button>
                            <button onclick="MessageHandler.deleteHighlightFromPanel(${h.id})" style="background: none; border: none; cursor: pointer; font-size: 12px; opacity: 0.6;" title="Remove">✕</button>
                        </div>
                        <div style="font-size: 0.75em; color: #888; margin-bottom: 4px;">
                            ${h.message_role === 'user' ? 'You' : 'Bot'} • ${this.formatPinTimestamp(h.created_at)}
                        </div>
                        <div style="font-size: 0.9em; line-height: 1.4; background: ${h.color === 'green' ? '#c8e6c9' : h.color === 'yellow' ? '#fff9c4' : '#ffcdd2'}; padding: 4px 8px; border-radius: 4px; display: inline-block;">
                            ${h.highlighted_text.length > 100 ? h.highlighted_text.substring(0, 100) + '...' : h.highlighted_text}
                        </div>
                        ${h.note ? `<div style="font-size: 0.75em; color: #667eea; margin-top: 4px; font-style: italic;">📝 ${h.note}</div>` : ''}
                    </div>
                `}).join('');
            } else {
                content.innerHTML = '<p class="panel-empty">No highlights yet.<br>Select text in messages and click "Highlight" to save.</p>';
            }
        } catch (error) {
            console.error('Error loading highlights:', error);
            content.innerHTML = '<p class="panel-empty">Error loading highlights</p>';
        }
    },
    
    /**
     * Go to highlight from panel button click (reads from data attributes)
     * @param {HTMLElement} button - The button clicked
     */
    goToHighlightFromPanel(button) {
        const container = button.closest('.panel-item');
        if (!container) return;
        
        const encodedContent = container.dataset.content || '';
        const contentSnippet = decodeURIComponent(encodedContent);
        
        this.goToHighlight(contentSnippet);
    },
    
    /**
     * Go to a highlighted message in chat
     * @param {string} contentSnippet - Content to search for
     */
    async goToHighlight(contentSnippet) {
        // Close the highlights panel first
        const panel = document.getElementById('highlights-panel');
        if (panel) panel.style.display = 'none';
        document.getElementById('highlightsBtn')?.classList.remove('active');
        
        // Reuse the same logic as goToMessage
        let targetMessage = this._findMessageInView(contentSnippet);
        
        if (targetMessage) {
            this._highlightAndScrollTo(targetMessage);
            return;
        }
        
        // Message not in current view - try to load more history
        console.log('📍 Highlight message not in current view, loading more history...');
        
        const characterId = this.currentCharacterId || this.characterName || 'coordinator';
        try {
            const isDomainPage = typeof DomainCharacters !== 'undefined';
            const isConversationBox = typeof ConversationBox !== 'undefined' && ConversationBox.config;
            
            let historyLoaded = false;
            
            if (isDomainPage) {
                const response = await AuthHelper.authenticatedFetch(
                    `/api/domain-characters/history/${characterId}?limit=500`
                );
                const data = await response.json();
                
                if (data.success && data.history && data.history.length > 0) {
                    if (DomainCharacters._reloadHistoryWithData) {
                        await DomainCharacters._reloadHistoryWithData(data.history, characterId);
                        historyLoaded = true;
                    }
                }
            } else if (isConversationBox && ConversationBox.config.historyEndpoint) {
                const response = await AuthHelper.authenticatedFetch(
                    `${ConversationBox.config.historyEndpoint}?limit=500`
                );
                const data = await response.json();
                
                if (data.messages && data.messages.length > 0) {
                    if (ConversationBox._reloadHistoryWithData) {
                        await ConversationBox._reloadHistoryWithData(data.messages, characterId);
                        historyLoaded = true;
                    }
                }
            }
            
            if (historyLoaded) {
                await new Promise(resolve => setTimeout(resolve, 300));
                targetMessage = this._findMessageInView(contentSnippet);
                
                if (targetMessage) {
                    this._highlightAndScrollTo(targetMessage);
                    return;
                }
            }
        } catch (error) {
            console.error('Error loading history for highlight:', error);
        }
        
        alert('Message not found. It may have been deleted or is from a different character.');
    },
    
    /**
     * Delete highlight from panel
     */
    async deleteHighlightFromPanel(highlightId) {
        try {
            const response = await AuthHelper.authenticatedFetch(`/api/user/highlights/${highlightId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const el = document.querySelector(`[data-highlight-id="${highlightId}"]`);
                if (el) {
                    el.style.opacity = '0';
                    el.style.transform = 'translateX(100%)';
                    setTimeout(() => el.remove(), 300);
                }
                setTimeout(() => this.loadHighlightsPanel(), 350);
            }
        } catch (error) {
            console.error('Error deleting highlight:', error);
        }
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
