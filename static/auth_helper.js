/**
 * Authentication Helper for Character Chat
 * Centralized authentication logic to avoid code duplication
 * 
 * Usage in templates:
 * 1. Include: <script src="/static/auth_helper.js"></script>
 * 2. Use: const response = await AuthHelper.authenticatedFetch('/character/chat', {...})
 */

const AuthHelper = {
    /**
     * Get the current auth token from localStorage
     * @returns {string|null} JWT token or null if not authenticated
     */
    getAuthToken() {
        return localStorage.getItem('authToken');
    },

    /**
     * Check if user is authenticated
     * @returns {boolean} True if user has valid token
     */
    isAuthenticated() {
        return !!this.getAuthToken();
    },

    /**
     * Get headers for authenticated requests
     * Automatically includes Content-Type and Authorization
     * @returns {object} Headers object ready for fetch
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const authToken = this.getAuthToken();
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        return headers;
    },

    /**
     * Make an authenticated fetch request
     * Automatically includes auth token if available
     * 
     * @param {string} url - API endpoint
     * @param {object} options - Fetch options (method, body, etc.)
     * @returns {Promise<Response>} Fetch response
     * 
     * @example
     * const response = await AuthHelper.authenticatedFetch('/coach/chat', {
     *     method: 'POST',
     *     body: JSON.stringify({ message: 'Hello' })
     * });
     */
    async authenticatedFetch(url, options = {}) {
        // Merge provided options with auth headers
        const fetchOptions = {
            ...options,
            headers: {
                ...this.getAuthHeaders(),
                ...(options.headers || {})
            }
        };
        
        return fetch(url, fetchOptions);
    },

    /**
     * Post a message to a character endpoint with authentication
     * Convenience method for chat endpoints
     * 
     * @param {string} characterEndpoint - e.g., '/coach/chat', '/sage/chat'
     * @param {string} message - User's message
     * @param {boolean} includeContext - Whether to include conversation context
     * @returns {Promise<object>} Response data
     * 
     * @example
     * const data = await AuthHelper.chatWithCharacter('/coach/chat', 'Hello!', true);
     */
    async chatWithCharacter(characterEndpoint, message, includeContext = true) {
        const response = await this.authenticatedFetch(characterEndpoint, {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                include_context: includeContext
            })
        });
        
        if (!response.ok) {
            throw new Error(`Chat request failed: ${response.statusText}`);
        }
        
        return response.json();
    },

    /**
     * Callbacks to run after successful authentication
     */
    _onAuthCallbacks: [],

    /**
     * Register a callback to run after authentication
     * @param {function} callback - Function to call after auth
     */
    onAuthenticated(callback) {
        if (typeof callback === 'function') {
            this._onAuthCallbacks.push(callback);
        }
    },

    /**
     * Store auth token (called after login)
     * @param {string} token - JWT token
     */
    setAuthToken(token) {
        localStorage.setItem('authToken', token);
        
        // Run all registered callbacks
        console.log(`🔐 Token set, running ${this._onAuthCallbacks.length} auth callbacks`);
        this._onAuthCallbacks.forEach(cb => {
            try {
                cb();
            } catch (e) {
                console.error('Auth callback error:', e);
            }
        });
    },

    /**
     * Remove auth token (logout)
     */
    clearAuthToken() {
        localStorage.removeItem('authToken');
    },

    /**
     * Debug: Log current authentication status to console
     */
    debugAuthStatus() {
        const token = this.getAuthToken();
        if (token) {
            console.log('✓ Authenticated (token present)');
            // Don't log the actual token for security
            console.log('  Token length:', token.length);
        } else {
            console.log('⚠️ Not authenticated (no token)');
        }
    }
};

// Make available globally
window.AuthHelper = AuthHelper;
