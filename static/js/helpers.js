/**
 * Common JavaScript Helpers
 * Shared utilities for all templates
 * Phase 2 Polish - Template Refactoring
 */

// ============================================
// AUTHENTICATION HELPERS
// ============================================

/**
 * Get authentication token from localStorage
 * @returns {string|null} Auth token or null if not found
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}

/**
 * Check if user is authenticated
 * @returns {boolean} True if token exists
 */
function isAuthenticated() {
    return getAuthToken() !== null;
}

/**
 * Handle authentication errors in API responses
 * @param {Response} response - Fetch API response object
 * @returns {boolean} True if auth error was handled
 */
function handleAuthError(response) {
    if (response.status === 401) {
        showNotification('Session expired. Please login again.', 'error');
        setTimeout(() => {
            window.location.href = '/chatchat';
        }, 1500);
        return true;
    }
    if (response.status === 403) {
        showNotification('Access denied. Insufficient permissions.', 'error');
        setTimeout(() => {
            window.location.href = '/chatchat';
        }, 1500);
        return true;
    }
    return false;
}

/**
 * Create authenticated fetch headers
 * @returns {Object} Headers object with auth token
 */
function getAuthHeaders() {
    const token = getAuthToken();
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}


// ============================================
// API HELPERS
// ============================================

/**
 * Make an authenticated API request
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise} Fetch promise
 */
async function apiRequest(url, options = {}) {
    const defaults = {
        headers: getAuthHeaders()
    };
    
    const config = { ...defaults, ...options };
    
    try {
        const response = await fetch(url, config);
        
        // Handle auth errors
        if (handleAuthError(response)) {
            throw new Error('Authentication error');
        }
        
        return response;
    } catch (error) {
        console.error('API Request Error:', error);
        logFrontendError(error, 'API Request', url);
        throw error;
    }
}

/**
 * Log frontend error to server
 * @param {Error|string} error - Error object or message
 * @param {string} context - Where the error occurred
 * @param {string} url - URL where error occurred
 */
async function logFrontendError(error, context = '', url = window.location.href) {
    try {
        const errorData = {
            error: error.message || String(error),
            stack_trace: error.stack || '',
            context: context,
            url: url,
            user_agent: navigator.userAgent,
            timestamp: new Date().toISOString()
        };
        
        await fetch('/api/log-error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(errorData)
        });
    } catch (e) {
        // Silent fail - don't break app if error logging fails
        console.error('Failed to log error:', e);
    }
}


// ============================================
// UI HELPERS
// ============================================

/**
 * Show notification to user
 * @param {string} message - Notification message
 * @param {string} type - 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (0 = permanent)
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to document
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
    }
    container.appendChild(notification);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            notification.remove();
        }, duration);
    }
}

/**
 * Get icon for notification type
 * @param {string} type - Notification type
 * @returns {string} Font Awesome icon class
 */
function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

/**
 * Format date string to readable format
 * @param {string} dateString - ISO date string
 * @param {boolean} includeTime - Include time in output
 * @returns {string} Formatted date
 */
function formatDate(dateString, includeTime = true) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return date.toLocaleDateString('en-US', options);
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {string} dateString - ISO date string
 * @returns {string} Relative time string
 */
function formatRelativeTime(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    if (diffDay < 7) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
    
    return formatDate(dateString, false);
}

/**
 * Escape HTML to prevent XSS
 * @param {string} unsafe - Unsafe HTML string
 * @returns {string} Escaped HTML
 */
function escapeHtml(unsafe) {
    const div = document.createElement('div');
    div.textContent = unsafe;
    return div.innerHTML;
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}


// ============================================
// CONTEXT API HELPERS
// ============================================

/**
 * Get user's stored context
 * @param {string} character - Character name or 'all'
 * @returns {Promise<Object>} Context data
 */
async function getUserContext(character = 'all') {
    try {
        const response = await apiRequest(`/api/user/context?character=${character}`);
        if (!response.ok) {
            throw new Error('Failed to get user context');
        }
        return await response.json();
    } catch (error) {
        console.error('Error getting user context:', error);
        throw error;
    }
}

/**
 * Update user context item
 * @param {number} contextId - Context item ID
 * @param {Object} updates - Fields to update
 * @returns {Promise<Object>} Response data
 */
async function updateUserContext(contextId, updates) {
    try {
        const response = await apiRequest(`/api/user/context/${contextId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
        if (!response.ok) {
            throw new Error('Failed to update context');
        }
        return await response.json();
    } catch (error) {
        console.error('Error updating context:', error);
        throw error;
    }
}

/**
 * Delete user context item
 * @param {number} contextId - Context item ID
 * @returns {Promise<Object>} Response data
 */
async function deleteUserContext(contextId) {
    try {
        const response = await apiRequest(`/api/user/context/${contextId}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error('Failed to delete context');
        }
        return await response.json();
    } catch (error) {
        console.error('Error deleting context:', error);
        throw error;
    }
}


// ============================================
// STORAGE HELPERS
// ============================================

/**
 * Safe localStorage getter
 * @param {string} key - Storage key
 * @param {*} defaultValue - Default value if key not found
 * @returns {*} Stored value or default
 */
function getStorage(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(key);
        return value !== null ? JSON.parse(value) : defaultValue;
    } catch (error) {
        console.error('Error reading from storage:', error);
        return defaultValue;
    }
}

/**
 * Safe localStorage setter
 * @param {string} key - Storage key
 * @param {*} value - Value to store
 * @returns {boolean} True if successful
 */
function setStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error writing to storage:', error);
        return false;
    }
}

/**
 * Remove item from localStorage
 * @param {string} key - Storage key
 */
function removeStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('Error removing from storage:', error);
    }
}


// ============================================
// GLOBAL ERROR HANDLER
// ============================================

// Catch unhandled errors
window.addEventListener('error', (event) => {
    logFrontendError(event.error, 'Unhandled Error', window.location.href);
});

// Catch unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    logFrontendError(
        new Error(event.reason),
        'Unhandled Promise Rejection',
        window.location.href
    );
});


// ============================================
// NOTIFICATION STYLES (Auto-inject)
// ============================================

(function injectNotificationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-width: 300px;
            max-width: 500px;
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            background: white;
            animation: slideIn 0.3s ease-out;
        }
        
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
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .notification-content i {
            font-size: 20px;
        }
        
        .notification-success {
            border-left: 4px solid #28a745;
        }
        .notification-success i {
            color: #28a745;
        }
        
        .notification-error {
            border-left: 4px solid #dc3545;
        }
        .notification-error i {
            color: #dc3545;
        }
        
        .notification-warning {
            border-left: 4px solid #ffc107;
        }
        .notification-warning i {
            color: #ffc107;
        }
        
        .notification-info {
            border-left: 4px solid #17a2b8;
        }
        .notification-info i {
            color: #17a2b8;
        }
        
        .notification-close {
            background: none;
            border: none;
            color: #999;
            cursor: pointer;
            font-size: 16px;
            padding: 4px 8px;
        }
        
        .notification-close:hover {
            color: #333;
        }
    `;
    document.head.appendChild(style);
})();

console.log('✓ Common helpers loaded');
