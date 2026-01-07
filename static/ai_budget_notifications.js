/**
 * AI Budget Notifications Module
 * Displays AI budget warnings and notifications to users
 */

const AIBudgetNotifications = {
    checkInterval: 60000, // Check every minute
    lastCheck: 0,
    notificationContainer: null,
    isInitialized: false,
    
    /**
     * Initialize the notification system
     */
    init() {
        if (this.isInitialized) return;
        
        this.createContainer();
        this.checkNotifications();
        
        // Set up periodic checking
        setInterval(() => this.checkNotifications(), this.checkInterval);
        
        this.isInitialized = true;
        console.log('✅ AIBudgetNotifications initialized');
    },
    
    /**
     * Create the notification container
     */
    createContainer() {
        if (document.getElementById('ai-budget-notification')) return;
        
        const container = document.createElement('div');
        container.id = 'ai-budget-notification';
        container.style.cssText = `
            display: none;
            position: fixed;
            top: 20px;
            right: 20px;
            max-width: 350px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 10000;
            overflow: hidden;
            animation: slideIn 0.3s ease;
        `;
        
        container.innerHTML = `
            <style>
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                #ai-budget-notification .notif-header {
                    padding: 12px 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                #ai-budget-notification .notif-header.warning {
                    background: linear-gradient(135deg, #f59e0b, #fbbf24);
                    color: white;
                }
                #ai-budget-notification .notif-header.danger {
                    background: linear-gradient(135deg, #ef4444, #f87171);
                    color: white;
                }
                #ai-budget-notification .notif-header.info {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                }
                #ai-budget-notification .notif-title {
                    font-weight: 600;
                    font-size: 0.9rem;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                #ai-budget-notification .notif-close {
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
                #ai-budget-notification .notif-body {
                    padding: 15px;
                    font-size: 0.85rem;
                    color: #333;
                }
                #ai-budget-notification .notif-actions {
                    padding: 10px 15px;
                    border-top: 1px solid #eee;
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                }
                #ai-budget-notification .notif-btn {
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 0.8rem;
                    cursor: pointer;
                    border: none;
                }
                #ai-budget-notification .notif-btn.primary {
                    background: #667eea;
                    color: white;
                }
                #ai-budget-notification .notif-btn.secondary {
                    background: #f0f0f0;
                    color: #333;
                }
            </style>
            <div class="notif-header warning" id="notif-header">
                <span class="notif-title"><span>⚠️</span> <span id="notif-title-text">AI Budget Alert</span></span>
                <button class="notif-close" onclick="AIBudgetNotifications.dismiss()">×</button>
            </div>
            <div class="notif-body" id="notif-body">
                Loading...
            </div>
            <div class="notif-actions">
                <button class="notif-btn secondary" onclick="AIBudgetNotifications.dismiss()">Dismiss</button>
                <button class="notif-btn primary" onclick="AIBudgetNotifications.acknowledge()">Got it</button>
            </div>
        `;
        
        document.body.appendChild(container);
        this.notificationContainer = container;
    },
    
    /**
     * Check for new notifications
     */
    async checkNotifications() {
        try {
            const response = await AuthHelper.authenticatedFetch('/api/ai-budget/notifications?unread=true');
            const data = await response.json();
            
            if (data.notifications && data.notifications.length > 0) {
                // Show the most recent unread notification
                const notif = data.notifications[0];
                this.show(notif);
            }
        } catch (error) {
            // Silently fail - user may not be authenticated
            console.debug('Budget notification check failed:', error.message);
        }
    },
    
    /**
     * Show a notification
     */
    show(notification) {
        if (!this.notificationContainer) return;
        
        const header = document.getElementById('notif-header');
        const titleText = document.getElementById('notif-title-text');
        const body = document.getElementById('notif-body');
        
        // Determine severity
        let severity = 'info';
        let icon = '💡';
        let title = 'AI Budget Notice';
        
        if (notification.notification_type === 'daily_limit_reached') {
            severity = 'danger';
            icon = '🚨';
            title = 'Daily Limit Reached';
        } else if (notification.notification_type === 'daily_limit_warning') {
            severity = 'warning';
            icon = '⚠️';
            title = 'Budget Warning';
        } else if (notification.notification_type === 'circuit_breaker') {
            severity = 'danger';
            icon = '🛑';
            title = 'Circuit Breaker Activated';
        } else if (notification.notification_type === 'unusual_pattern') {
            severity = 'warning';
            icon = '📊';
            title = 'Unusual Usage Pattern';
        }
        
        header.className = `notif-header ${severity}`;
        titleText.innerHTML = `${icon} ${title}`;
        body.textContent = notification.message || 'AI usage notification';
        
        // Store current notification ID for acknowledgment
        this.currentNotificationId = notification.id;
        
        this.notificationContainer.style.display = 'block';
    },
    
    /**
     * Dismiss without acknowledging (will show again)
     */
    dismiss() {
        if (this.notificationContainer) {
            this.notificationContainer.style.display = 'none';
        }
    },
    
    /**
     * Acknowledge notification (won't show again)
     */
    async acknowledge() {
        if (this.currentNotificationId) {
            try {
                await AuthHelper.authenticatedFetch('/api/ai-budget/notifications/acknowledge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notification_id: this.currentNotificationId })
                });
            } catch (error) {
                console.error('Failed to acknowledge notification:', error);
            }
        }
        this.dismiss();
    },
    
    /**
     * Get current budget status (for display in UI)
     */
    async getStatus() {
        try {
            const response = await AuthHelper.authenticatedFetch('/api/ai-budget/status');
            return await response.json();
        } catch (error) {
            console.error('Failed to get budget status:', error);
            return null;
        }
    }
};

// Export for use
window.AIBudgetNotifications = AIBudgetNotifications;
