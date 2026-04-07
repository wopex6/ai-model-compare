/**
 * Automated Greeting Handler
 * 
 * Polls for automated greetings from the coordinator and displays them
 * in the conversation interface.
 * 
 * Features:
 * - Polls for new greetings every 30 seconds
 * - Tracks user activity to enable inactivity detection
 * - Displays greetings as coordinator messages
 * - Prevents duplicate greeting displays
 */

const GreetingHandler = {
    pollInterval: null,
    pollFrequency: 30000, // 30 seconds
    lastCheckTime: null,
    displayedGreetingIds: new Set(),
    
    /**
     * Initialize the greeting handler
     */
    init() {
        console.log('🎉 Initializing Greeting Handler');
        this.lastCheckTime = new Date().toISOString();
        
        // Start polling for greetings
        this.startPolling();
        
        // Track user activity
        this.setupActivityTracking();
        
        // Check immediately on init
        this.checkForGreetings();
    },
    
    /**
     * Start polling for new greetings
     */
    startPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
        
        this.pollInterval = setInterval(() => {
            this.checkForGreetings();
        }, this.pollFrequency);
        
        console.log(`✅ Greeting polling started (every ${this.pollFrequency / 1000}s)`);
    },
    
    /**
     * Stop polling for greetings
     */
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            console.log('🛑 Greeting polling stopped');
        }
    },
    
    /**
     * Check for new greetings from the server
     */
    async checkForGreetings() {
        try {
            const url = `/api/greetings/pending?since=${encodeURIComponent(this.lastCheckTime)}`;
            const response = await AuthHelper.authenticatedFetch(url);
            
            if (response.status === 401) {
                console.log('⚠️ Session expired - stopping greeting checks');
                this.stopPolling();
                return;
            }
            
            const data = await response.json();
            
            if (data.success && data.greetings && data.greetings.length > 0) {
                console.log(`📬 Received ${data.greetings.length} new greeting(s)`);
                
                for (const greeting of data.greetings) {
                    // Check if we've already displayed this greeting
                    if (!this.displayedGreetingIds.has(greeting.id)) {
                        this.displayGreeting(greeting);
                        this.displayedGreetingIds.add(greeting.id);
                    }
                }
                
                // Update last check time to most recent greeting
                const latestGreeting = data.greetings[0];
                this.lastCheckTime = latestGreeting.sent_at;
            }
        } catch (error) {
            console.error('❌ Error checking for greetings:', error);
        }
    },
    
    /**
     * Display a greeting in the conversation interface
     */
    displayGreeting(greeting) {
        console.log(`💬 Displaying ${greeting.type} greeting:`, greeting.message.substring(0, 50) + '...');
        
        // Add greeting as a coordinator message
        if (typeof MessageHandler !== 'undefined' && MessageHandler.addMessage) {
            MessageHandler.addMessage({
                content: greeting.message,
                role: 'bot',
                timestamp: greeting.sent_at,
                shouldScroll: true,
                metadata: {
                    characterName: 'Aria (Coordinator)',
                    isGreeting: true,
                    greetingType: greeting.type
                }
            });
        } else if (typeof DomainCharacters !== 'undefined' && DomainCharacters._addMessageToDisplay) {
            // For domain characters page
            DomainCharacters._addMessageToDisplay(
                greeting.message,
                'bot',
                'coordinator',
                false,
                greeting.sent_at
            );
        } else {
            console.warn('⚠️ No message display handler available');
        }
        
        // Show a subtle notification
        this.showGreetingNotification(greeting.type);
    },
    
    /**
     * Show a subtle notification when greeting is received
     */
    showGreetingNotification(greetingType) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-size: 14px;
            animation: slideIn 0.3s ease-out;
        `;
        
        const icon = greetingType === 'daily' ? '🌟' : '💬';
        notification.textContent = `${icon} New message from Aria`;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },
    
    /**
     * Setup activity tracking to detect user interactions
     */
    setupActivityTracking() {
        let activityTimeout = null;
        
        const trackActivity = () => {
            // Debounce activity updates (only send once per minute)
            if (activityTimeout) {
                clearTimeout(activityTimeout);
            }
            
            activityTimeout = setTimeout(() => {
                this.updateUserActivity('interaction');
            }, 60000); // 1 minute debounce
        };
        
        // Track various user interactions
        document.addEventListener('click', trackActivity);
        document.addEventListener('keypress', trackActivity);
        document.addEventListener('scroll', trackActivity);
        
        console.log('✅ Activity tracking enabled');
    },
    
    /**
     * Update user activity on the server
     */
    async updateUserActivity(activityType = 'interaction') {
        try {
            await AuthHelper.authenticatedFetch('/api/greetings/activity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    activity_type: activityType,
                    metadata: {
                        timestamp: new Date().toISOString(),
                        page: window.location.pathname
                    }
                })
            });
        } catch (error) {
            // Silently fail - activity tracking is not critical
            console.debug('Activity update failed:', error);
        }
    }
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export for use
window.GreetingHandler = GreetingHandler;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => GreetingHandler.init());
} else {
    GreetingHandler.init();
}
