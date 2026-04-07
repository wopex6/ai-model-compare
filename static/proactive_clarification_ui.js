/**
 * Proactive Clarification UI Module
 * Displays clarifying questions when the system needs more context
 */

const ProactiveClarificationUI = {
    containerId: 'clarification-container',
    currentQuestions: [],
    isVisible: false,
    
    /**
     * Initialize the clarification UI
     */
    init(containerId = 'clarification-container') {
        this.containerId = containerId;
        this.createContainer();
        console.log('✅ ProactiveClarificationUI initialized');
    },
    
    /**
     * Create the floating container if it doesn't exist
     */
    createContainer() {
        if (document.getElementById(this.containerId)) return;
        
        const container = document.createElement('div');
        container.id = this.containerId;
        container.style.cssText = `
            display: none;
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 320px;
            max-width: 90vw;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            overflow: hidden;
            animation: slideUp 0.3s ease;
        `;
        
        container.innerHTML = `
            <style>
                @keyframes slideUp {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                .clarification-header {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 12px 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .clarification-header h4 {
                    margin: 0;
                    font-size: 0.9rem;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .clarification-close {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .clarification-body {
                    padding: 15px;
                    max-height: 300px;
                    overflow-y: auto;
                }
                .clarification-question {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 10px;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 1px solid transparent;
                }
                .clarification-question:hover {
                    background: #e9ecef;
                    border-color: #667eea;
                }
                .clarification-question .q-text {
                    font-size: 0.85rem;
                    color: #333;
                    margin-bottom: 6px;
                }
                .clarification-question .q-reason {
                    font-size: 0.75rem;
                    color: #666;
                }
                .clarification-dismiss {
                    text-align: center;
                    padding: 10px;
                    border-top: 1px solid #eee;
                }
                .clarification-dismiss button {
                    background: none;
                    border: none;
                    color: #888;
                    font-size: 0.8rem;
                    cursor: pointer;
                }
                .clarification-dismiss button:hover {
                    color: #333;
                }
            </style>
            <div class="clarification-header">
                <h4><span>💭</span> Quick Questions</h4>
                <button class="clarification-close" onclick="ProactiveClarificationUI.hide()">×</button>
            </div>
            <div class="clarification-body" id="clarification-questions"></div>
            <div class="clarification-dismiss">
                <button onclick="ProactiveClarificationUI.dismiss()">Not now</button>
            </div>
        `;
        
        document.body.appendChild(container);
    },
    
    /**
     * Show clarifying questions
     * @param {Array} questions - Array of {question, reason, priority}
     */
    show(questions) {
        if (!questions || questions.length === 0) return;
        
        this.currentQuestions = questions;
        const container = document.getElementById(this.containerId);
        const body = document.getElementById('clarification-questions');
        
        if (!container || !body) return;
        
        body.innerHTML = questions.map((q, i) => `
            <div class="clarification-question" onclick="ProactiveClarificationUI.selectQuestion(${i})">
                <div class="q-text">${this.escapeHtml(q.question)}</div>
                ${q.reason ? `<div class="q-reason">💡 ${this.escapeHtml(q.reason)}</div>` : ''}
            </div>
        `).join('');
        
        container.style.display = 'block';
        this.isVisible = true;
    },
    
    /**
     * Hide the clarification UI
     */
    hide() {
        const container = document.getElementById(this.containerId);
        if (container) {
            container.style.display = 'none';
        }
        this.isVisible = false;
    },
    
    /**
     * Dismiss and don't show again for this session
     */
    dismiss() {
        this.hide();
        sessionStorage.setItem('clarificationDismissed', 'true');
    },
    
    /**
     * User selected a question - insert into input
     */
    selectQuestion(index) {
        const question = this.currentQuestions[index];
        if (!question) return;
        
        // Find the input field and insert the answer prompt (works on both pages)
        const input = document.getElementById('userInput') || document.getElementById('chat-input');
        if (input) {
            input.value = `Regarding "${question.question.substring(0, 50)}...": `;
            input.focus();
        }
        
        this.hide();
    },
    
    /**
     * Check for clarification questions from API response
     */
    checkResponse(responseData) {
        if (sessionStorage.getItem('clarificationDismissed') === 'true') return;
        
        if (responseData.clarification_questions && responseData.clarification_questions.length > 0) {
            this.show(responseData.clarification_questions);
        }
    },
    
    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Export for use
window.ProactiveClarificationUI = ProactiveClarificationUI;
