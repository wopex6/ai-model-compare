/**
 * Explicit Context UI Module
 * Displays user's stated context (goals, preferences, values) with management capabilities
 */

const ExplicitContextUI = {
    containerId: 'explicit-context-panel',
    isLoaded: false,
    currentCharacter: 'coordinator',
    
    /**
     * Initialize the explicit context UI
     */
    init(containerId = 'explicit-context-panel', character = 'coordinator') {
        this.containerId = containerId;
        this.currentCharacter = character;
        this.loadContext();
        console.log('✅ ExplicitContextUI initialized');
    },
    
    /**
     * Load and display explicit context from API
     */
    async loadContext() {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        try {
            const response = await AuthHelper.authenticatedFetch(
                `/api/user/explicit-context/ui-data?character=${this.currentCharacter}`
            );
            const data = await response.json();
            
            if (data.success) {
                this.render(container, data);
                this.isLoaded = true;
            } else {
                container.innerHTML = '<p class="context-error">Unable to load context</p>';
            }
        } catch (error) {
            console.error('Error loading explicit context:', error);
            container.innerHTML = '<p class="context-error">Error loading context</p>';
        }
    },
    
    /**
     * Render the context UI
     */
    render(container, data) {
        if (!data.has_context) {
            container.innerHTML = `
                <div class="context-empty">
                    <p style="margin: 0; color: #888; font-size: 0.85rem;">
                        <i class="fas fa-lightbulb" style="color: #ffc107;"></i>
                        Tell me about your goals, preferences, or how you're feeling - I'll remember!
                    </p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="context-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-weight: 600; color: #333; font-size: 0.9rem;">
                    <i class="fas fa-brain" style="color: #667eea;"></i> What I Know About You
                </span>
                <span style="font-size: 0.75rem; color: #888;">${data.total_items} items</span>
            </div>
            <div class="context-help" style="font-size: 0.75rem; color: #666; margin-bottom: 12px; padding: 8px; background: #f8f9fa; border-radius: 6px;">
                ${data.help_text}
            </div>
        `;
        
        for (const [type, group] of Object.entries(data.groups)) {
            html += `
                <div class="context-group" style="margin-bottom: 12px;">
                    <div class="group-header" style="font-size: 0.85rem; font-weight: 500; color: #444; margin-bottom: 6px;">
                        ${group.label}
                    </div>
                    <div class="group-items">
            `;
            
            for (const item of group.items) {
                const colorMap = {
                    'pink': '#ec4899',
                    'blue': '#3b82f6',
                    'gray': '#6b7280',
                    'green': '#10b981',
                    'purple': '#8b5cf6',
                    'indigo': '#6366f1',
                    'orange': '#f59e0b'
                };
                const borderColor = colorMap[group.color] || '#667eea';
                
                html += `
                    <div class="context-item" data-id="${item.id}" style="
                        background: white;
                        border-left: 3px solid ${borderColor};
                        padding: 8px 10px;
                        margin-bottom: 6px;
                        border-radius: 0 6px 6px 0;
                        font-size: 0.8rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                    ">
                        <div style="flex: 1;">
                            <div style="color: #333;">${this.escapeHtml(item.value)}</div>
                            ${item.original ? `<div style="font-size: 0.7rem; color: #888; margin-top: 2px; font-style: italic;">"${this.escapeHtml(item.original.substring(0, 50))}${item.original.length > 50 ? '...' : ''}"</div>` : ''}
                        </div>
                        ${item.can_delete ? `
                            <button onclick="ExplicitContextUI.deleteItem(${item.id})" 
                                style="background: none; border: none; color: #ccc; cursor: pointer; padding: 2px 4px; font-size: 14px;"
                                title="Remove this">×</button>
                        ` : ''}
                    </div>
                `;
            }
            
            html += `</div></div>`;
        }
        
        container.innerHTML = html;
    },
    
    /**
     * Delete a context item
     */
    async deleteItem(itemId) {
        if (!confirm('Remove this from what I know about you?')) return;
        
        try {
            const response = await AuthHelper.authenticatedFetch(
                `/api/user/explicit-context/${itemId}`,
                { method: 'DELETE' }
            );
            const data = await response.json();
            
            if (data.success) {
                // Reload the context display
                this.loadContext();
            } else {
                alert('Failed to remove: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting context:', error);
            alert('Error removing item');
        }
    },
    
    /**
     * Update character and reload
     */
    setCharacter(character) {
        this.currentCharacter = character;
        this.loadContext();
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    /**
     * Toggle visibility of the panel
     */
    toggle() {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        const isVisible = container.style.display !== 'none';
        container.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible && !this.isLoaded) {
            this.loadContext();
        }
    }
};

// Export for use
window.ExplicitContextUI = ExplicitContextUI;
