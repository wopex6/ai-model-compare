/**
 * Smart Response Client - Common module for all AI characters
 * Handles authentication and smart response integration
 */

class SmartResponseClient {
    /**
     * Add smart response capability to any character chat
     * @param {string} characterId - Character identifier (e.g., 'coach', 'sage', 'marcus')
     * @param {Function} originalFetchFn - Original fetch function to call
     * @returns {Function} Enhanced fetch function with auth and logging
     */
    static enhanceFetch(characterId, originalFetchFn) {
        return async function(url, options = {}) {
            // Get auth token for Smart Response System
            const authToken = localStorage.getItem('authToken');
            
            // Add Authorization header if token exists
            if (authToken) {
                options.headers = options.headers || {};
                options.headers['Authorization'] = `Bearer ${authToken}`;
            }
            
            // Call original fetch
            const response = await originalFetchFn(url, options);
            
            // Log smart response activity (visible in browser console)
            const data = await response.clone().json();
            if (data.type === 'quick_reply') {
                console.log(`⚡ Smart Reply (${characterId}):`, data.response.substring(0, 50) + '...');
                console.log(`   Confidence: ${(data.confidence * 100).toFixed(0)}%`);
            } else if (data.type === 'full_ai') {
                console.log(`🤖 Full AI (${characterId}): Processing complex message`);
            }
            
            return response;
        };
    }
    
    /**
     * Simple wrapper to add auth header to fetch requests
     * Use this for character pages that already have their own chat logic
     */
    static getAuthHeaders() {
        const authToken = localStorage.getItem('authToken');
        const headers = { 'Content-Type': 'application/json' };
        
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        return headers;
    }
    
    /**
     * Check if user is authenticated
     */
    static isAuthenticated() {
        return !!localStorage.getItem('authToken');
    }
}

// Make available globally
window.SmartResponseClient = SmartResponseClient;
