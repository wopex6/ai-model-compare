/**
 * Personality Interpretation Display Module
 * Shows inline personality interpretations in chat for Master/Admin users
 * Phase 3.1 Feature
 */

class PersonalityInterpretationDisplay {
    constructor() {
        this.hasAccess = false;
        this.checkAccess();
    }

    async checkAccess() {
        try {
            // Check if user has personality access (Master or Admin)
            const response = await fetch('/api/personality/stats');
            if (response.ok) {
                this.hasAccess = true;
                console.log('✅ Personality interpretation display enabled (Master/Admin access)');
            }
        } catch (error) {
            // No access or error - disable feature silently
            this.hasAccess = false;
        }
    }

    /**
     * Get the most recent interpretation for a user message
     */
    async getLatestInterpretation() {
        if (!this.hasAccess) return null;

        try {
            const response = await fetch('/api/personality/interpretations?limit=1');
            if (response.ok) {
                const data = await response.json();
                if (data.interpretations && data.interpretations.length > 0) {
                    return data.interpretations[0];
                }
            }
        } catch (error) {
            console.error('Error fetching interpretation:', error);
        }
        return null;
    }

    /**
     * Create interpretation badge HTML
     */
    createInterpretationBadge(interpretation) {
        if (!interpretation) return '';

        const confidence = Math.round(interpretation.confidence * 100);
        const confidenceClass = confidence >= 70 ? 'high' : confidence >= 50 ? 'medium' : 'low';

        return `
            <div class="personality-interpretation-badge" style="
                margin-top: 8px;
                padding: 10px;
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
                border-left: 3px solid #667eea;
                border-radius: 8px;
                font-size: 12px;
                line-height: 1.5;
            ">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <i class="fas fa-brain" style="color: #667eea;"></i>
                    <strong style="color: #667eea;">Personality Insight</strong>
                    <span class="confidence-badge confidence-${confidenceClass}" style="
                        margin-left: auto;
                        padding: 2px 8px;
                        border-radius: 12px;
                        font-size: 10px;
                        font-weight: bold;
                        ${confidenceClass === 'high' ? 'background: #28a745; color: white;' :
                          confidenceClass === 'medium' ? 'background: #ffc107; color: #333;' :
                          'background: #dc3545; color: white;'}
                    ">${confidence}%</span>
                </div>
                <div style="color: #555; font-size: 11px;">
                    <div style="margin-bottom: 4px;">
                        <strong>Interpreted as:</strong> ${this.escapeHtml(interpretation.interpretation)}
                    </div>
                    ${interpretation.recommended_approach ? `
                        <div style="color: #666; font-style: italic;">
                            → ${this.escapeHtml(interpretation.recommended_approach)}
                        </div>
                    ` : ''}
                </div>
                <button class="view-details-btn" onclick="personalityDisplay.viewInterpretationDetails('${interpretation.id}')" style="
                    margin-top: 8px;
                    padding: 4px 12px;
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 10px;
                    transition: background 0.2s;
                " onmouseover="this.style.background='#5568d3'" onmouseout="this.style.background='#667eea'">
                    View Details
                </button>
            </div>
        `;
    }

    /**
     * Add interpretation badge after a user message
     * Call this after user sends a message and before AI responds
     */
    async displayInterpretationForLastMessage(messageElement) {
        if (!this.hasAccess) return;

        // Wait a moment for interpretation to be processed
        await new Promise(resolve => setTimeout(resolve, 500));

        const interpretation = await this.getLatestInterpretation();
        if (interpretation && interpretation.confidence >= 0.5) {
            const badge = this.createInterpretationBadge(interpretation);
            
            // Add badge after the message
            const badgeContainer = document.createElement('div');
            badgeContainer.innerHTML = badge;
            messageElement.appendChild(badgeContainer.firstElementChild);
        }
    }

    /**
     * View full interpretation details in a modal
     */
    async viewInterpretationDetails(interpretationId) {
        // Fetch full details
        const response = await fetch('/api/personality/interpretations?limit=50');
        const data = await response.json();
        const interpretation = data.interpretations.find(i => i.id == interpretationId);

        if (!interpretation) {
            alert('Interpretation details not found');
            return;
        }

        // Create modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 15px;
                padding: 30px;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            ">
                <h2 style="color: #667eea; margin-bottom: 20px;">
                    <i class="fas fa-brain"></i> Interpretation Details
                </h2>
                
                <div style="margin-bottom: 15px;">
                    <strong>Your Message:</strong>
                    <p style="color: #666; font-size: 14px; margin-top: 5px;">"${this.escapeHtml(interpretation.raw_message)}"</p>
                </div>

                <div style="margin-bottom: 15px;">
                    <strong>Event Type:</strong>
                    <span style="
                        display: inline-block;
                        padding: 4px 12px;
                        background: #667eea;
                        color: white;
                        border-radius: 15px;
                        font-size: 12px;
                        margin-left: 10px;
                    ">${interpretation.event_type}</span>
                </div>

                <div style="margin-bottom: 15px;">
                    <strong>Interpretation:</strong>
                    <p style="color: #333; font-size: 14px; margin-top: 5px;">${this.escapeHtml(interpretation.interpretation)}</p>
                </div>

                ${interpretation.emotional_impact ? `
                    <div style="margin-bottom: 15px;">
                        <strong>Emotional Impact:</strong>
                        <p style="color: #666; font-size: 14px; margin-top: 5px;">${this.escapeHtml(interpretation.emotional_impact)}</p>
                    </div>
                ` : ''}

                <div style="margin-bottom: 15px;">
                    <strong>Recommended Approach:</strong>
                    <p style="color: #666; font-size: 14px; margin-top: 5px; font-style: italic;">${this.escapeHtml(interpretation.recommended_approach)}</p>
                </div>

                <div style="margin-bottom: 15px;">
                    <strong>Confidence:</strong>
                    <div style="margin-top: 5px;">
                        <div style="
                            height: 20px;
                            background: #e9ecef;
                            border-radius: 10px;
                            overflow: hidden;
                        ">
                            <div style="
                                height: 100%;
                                width: ${interpretation.confidence * 100}%;
                                background: linear-gradient(90deg, #667eea, #764ba2);
                                transition: width 0.5s ease;
                            "></div>
                        </div>
                        <span style="font-size: 12px; color: #666; margin-top: 5px; display: block;">
                            ${Math.round(interpretation.confidence * 100)}% confidence
                        </span>
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <strong>Traits Used:</strong>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        ${Object.entries(interpretation.traits_used || {}).map(([trait, value]) => `
                            <div style="margin: 3px 0;">
                                <span style="text-transform: capitalize;">${trait}:</span>
                                <span style="font-weight: bold;">${Math.round(value * 100)}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div style="margin-bottom: 20px; padding: 10px; background: #f8f9fa; border-radius: 8px; font-size: 12px; color: #666;">
                    <i class="fas fa-user"></i> Character: ${interpretation.character}<br>
                    <i class="fas fa-clock"></i> ${new Date(interpretation.created_at).toLocaleString()}
                </div>

                <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="
                    width: 100%;
                    padding: 12px;
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                ">Close</button>
            </div>
        `;

        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        document.body.appendChild(modal);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create global instance
const personalityDisplay = new PersonalityInterpretationDisplay();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PersonalityInterpretationDisplay;
}
