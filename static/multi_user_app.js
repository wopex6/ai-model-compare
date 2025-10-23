// General State Management System
class StateManager {
    constructor() {
        this.stateConfig = {
            // Define state hierarchy and restoration methods
            'currentTab': {
                restoreMethod: 'switchTab',
                children: {
                    'psychology': {
                        'currentPsychologySection': { restoreMethod: 'switchPsychologySection' }
                    },
                    'profile': {
                        'currentProfilePage': { restoreMethod: 'switchProfilePage' }
                    },
                    'conversations': {
                        'selectedConversation': { restoreMethod: 'selectConversation' }
                    },
                    'chat': {
                        'selectedChatSession': { restoreMethod: 'selectChatSession' }
                    }
                }
            }
        };
        
        // Initialize scroll position tracking
        this.initScrollTracking();
    }

    // Save any state automatically
    saveState(key, value) {
        localStorage.setItem(key, value);
    }

    // Get saved state
    getState(key) {
        return localStorage.getItem(key);
    }

    // Restore all states automatically
    async restoreStates(app) {
        // Wait for DOM to be ready
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const mainState = this.getState('currentTab');
        if (mainState) {
            // Restore main tab
            if (app[this.stateConfig.currentTab.restoreMethod]) {
                app[this.stateConfig.currentTab.restoreMethod](mainState);
            }
            
            // Restore child states
            await new Promise(resolve => setTimeout(resolve, 200));
            const childConfig = this.stateConfig.currentTab.children[mainState];
            if (childConfig) {
                for (const [stateKey, config] of Object.entries(childConfig)) {
                    const stateValue = this.getState(stateKey);
                    if (stateValue && app[config.restoreMethod]) {
                        app[config.restoreMethod](stateValue);
                    }
                }
            }
        } else {
            // Default state
            if (app.switchTab) {
                app.switchTab('home');
            }
        }
        
        // Restore scroll positions after all content is loaded
        this.restoreScrollPositions();
    }

    // Initialize scroll position tracking
    initScrollTracking() {
        // Track scroll position on various scrollable elements
        this.scrollElements = [
            { selector: 'window', key: 'mainScroll' },
            { selector: '#dashboard-screen', key: 'dashboardScroll' },
            { selector: '#psychology-tab', key: 'psychologyScroll' },
            { selector: '#profile-tab', key: 'profileScroll' },
            { selector: '#conversations-tab', key: 'conversationsScroll' },
            { selector: '#chat-tab', key: 'chatScroll' },
            { selector: '#assessment-history-container', key: 'historyScroll' },
            { selector: '#psychology-chart-container', key: 'chartScroll' }
        ];
        
        // Debounced scroll save function
        this.saveScrollDebounced = this.debounce(() => {
            this.saveScrollPositions();
        }, 250);
    }

    // Save scroll positions for all tracked elements
    saveScrollPositions() {
        this.scrollElements.forEach(({ selector, key }) => {
            let element, scrollTop, scrollLeft;
            
            if (selector === 'window') {
                scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            } else {
                element = document.querySelector(selector);
                if (element) {
                    scrollTop = element.scrollTop;
                    scrollLeft = element.scrollLeft;
                }
            }
            
            if (scrollTop !== undefined || scrollLeft !== undefined) {
                this.saveState(`${key}_top`, scrollTop || 0);
                this.saveState(`${key}_left`, scrollLeft || 0);
            }
        });
    }

    // Immediate scroll restoration (no delay) for main window
    restoreMainScrollImmediate() {
        const scrollTop = parseInt(this.getState('mainScroll_top')) || 0;
        const scrollLeft = parseInt(this.getState('mainScroll_left')) || 0;
        
        if (scrollTop > 0 || scrollLeft > 0) {
            console.log('🔧 Flash Debug: StateManager attempting immediate scroll to', scrollTop, scrollLeft);
            
            // Try immediate scroll first
            const attemptScroll = () => {
                const maxScroll = document.body.scrollHeight - window.innerHeight;
                console.log('🔧 Flash Debug: Page dimensions - height:', document.body.scrollHeight, 'window:', window.innerHeight, 'maxScroll:', maxScroll);
                
                if (maxScroll >= scrollTop) {
                    window.scrollTo(scrollLeft, scrollTop);
                    console.log('🔧 Flash Debug: StateManager scroll position set to', window.pageYOffset, window.pageXOffset);
                    return true; // Success
                } else {
                    console.log('🔧 Flash Debug: Page not tall enough yet, max scroll:', maxScroll, 'target:', scrollTop);
                    return false; // Failed, need to retry
                }
            };
            
            // Try immediately
            if (!attemptScroll()) {
                // If failed, retry with short intervals until success
                let attempts = 0;
                const retryInterval = setInterval(() => {
                    attempts++;
                    if (attemptScroll() || attempts > 20) {
                        clearInterval(retryInterval);
                        if (attempts > 20) {
                            console.log('🔧 Flash Debug: Gave up after 20 attempts, page may not be tall enough');
                        }
                    }
                }, 100); // Try every 100ms
            }
        }
    }

    // Restore scroll positions for all tracked elements
    restoreScrollPositions() {
        // Immediately restore main window scroll (no flash)
        this.restoreMainScrollImmediate();
        
        // Wait a bit for content to load, then restore other elements
        setTimeout(() => {
            this.scrollElements.forEach(({ selector, key }) => {
                const scrollTop = parseInt(this.getState(`${key}_top`)) || 0;
                const scrollLeft = parseInt(this.getState(`${key}_left`)) || 0;
                
                if (selector === 'window') {
                    // Main window already restored immediately
                    return;
                } else {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.scrollTop = scrollTop;
                        element.scrollLeft = scrollLeft;
                    }
                }
            });
        }, 150); // Reduced delay
    }

    // Start tracking scroll positions
    startScrollTracking() {
        // Track window scroll
        window.addEventListener('scroll', this.saveScrollDebounced, { passive: true });
        
        // Track scroll on specific elements
        this.scrollElements.forEach(({ selector }) => {
            if (selector !== 'window') {
                const element = document.querySelector(selector);
                if (element) {
                    element.addEventListener('scroll', this.saveScrollDebounced, { passive: true });
                }
            }
        });
    }

    // Stop tracking scroll positions
    stopScrollTracking() {
        window.removeEventListener('scroll', this.saveScrollDebounced);
        
        this.scrollElements.forEach(({ selector }) => {
            if (selector !== 'window') {
                const element = document.querySelector(selector);
                if (element) {
                    element.removeEventListener('scroll', this.saveScrollDebounced);
                }
            }
        });
    }

    // Debounce utility function
    debounce(func, wait) {
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

    // Clear all states
    clearAllStates() {
        const stateKeys = Object.keys(localStorage).filter(key => 
            key.startsWith('current') || 
            key.startsWith('selected') || 
            key.startsWith('active') ||
            key.endsWith('Scroll') ||
            key.endsWith('_top') ||
            key.endsWith('_left')
        );
        stateKeys.forEach(key => localStorage.removeItem(key));
    }
}

class IntegratedAIChatbot {
    constructor() {
        this.authToken = localStorage.getItem('authToken');
        this.currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
        this.currentConversation = null;
        this.currentChatSession = null;
        
        // Initialize flags to prevent duplicate operations
        this.isCreatingChat = false;
        this.isSubmittingConversation = false;
        
        // Admin chat specific properties
        this.adminChatRefreshInterval = null;
        this.adminUserChatRefreshInterval = null;
        this.currentAdminChatUserId = null;
        
        // Reply functionality
        this.replyingTo = null;
        this.replyingToContext = null;
        
        // Message notification tracking
        this.lastAdminMessageCount = 0;
        this.lastUserMessageCount = 0;
        this.notificationTimeout = null;
        
        // Message content tracking to prevent unnecessary re-renders
        this.lastAdminMessagesHash = null;
        this.lastUserMessagesHash = null;
        
        // Initialize general state manager
        this.stateManager = new StateManager();
        this.init();
        
        // Check if user is already logged in
        if (this.authToken && this.currentUser) {
            // Restore scroll position immediately to prevent flash
            this.stateManager.restoreMainScrollImmediate();
            
            // Show dashboard
            this.showDashboard();
            
            // Verify token is still valid in background
            this.verifyAuthToken().catch(() => {
                // If verification fails, user will be logged out automatically
            });
        } else {
            this.showScreen('login-screen');
        }
    }
    
    formatTimestamp(timestamp) {
        /**Format timestamp to local time with AM/PM */
        if (!timestamp) return '';
        
        // SQLite returns timestamps in UTC without 'Z' suffix
        // Add 'Z' to indicate UTC if not already present
        let utcTimestamp = timestamp;
        if (typeof timestamp === 'string' && !timestamp.endsWith('Z') && !timestamp.includes('+')) {
            utcTimestamp = timestamp.replace(' ', 'T') + 'Z';
        }
        
        const date = new Date(utcTimestamp);
        const options = {
            month: 'numeric',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        };
        
        return date.toLocaleString('en-US', options);
    }

    init() {
        this.setupEventListeners();
        // this.checkAuthStatus();
    }

    setupEventListeners() {
        // Auth form listeners
        document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('signup-form').addEventListener('submit', (e) => this.handleSignup(e));
        document.getElementById('show-signup').addEventListener('click', (e) => {
            e.preventDefault();
            this.showScreen('signup-screen');
        });
        document.getElementById('show-login').addEventListener('click', (e) => {
            e.preventDefault();
            this.showScreen('login-screen');
        });

        // Dashboard navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        document.getElementById('logout-btn').addEventListener('click', () => this.handleLogout());

        // Profile navigation
        document.querySelectorAll('.profile-nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchProfilePage(e.target.dataset.page));
        });

        // Psychology navigation
        document.querySelectorAll('.psychology-nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchPsychologySection(e.target.dataset.section));
        });

        // Chart controls
        document.querySelectorAll('input[name="chart-type"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.updateChart(e.target.value));
        });

        // Profile forms
        document.getElementById('personal-info-form').addEventListener('submit', (e) => this.handlePersonalInfoUpdate(e));
        document.getElementById('preferences-form').addEventListener('submit', (e) => this.handlePreferencesUpdate(e));
        document.getElementById('privacy-form').addEventListener('submit', (e) => this.handlePrivacyUpdate(e));

        // Psychology traits
        document.getElementById('add-trait-btn').addEventListener('click', () => this.showTraitModal());
        document.getElementById('trait-form').addEventListener('submit', (e) => this.handleTraitSubmit(e));
        document.getElementById('close-trait-modal').addEventListener('click', () => this.hideTraitModal());
        document.getElementById('cancel-trait').addEventListener('click', () => this.hideTraitModal());

        // Conversations
        document.getElementById('new-conversation-btn').addEventListener('click', () => this.showConversationModal());
        document.getElementById('conversation-form').addEventListener('submit', (e) => this.handleConversationSubmit(e));
        document.getElementById('close-conversation-modal').addEventListener('click', () => this.hideConversationModal());
        document.getElementById('cancel-conversation').addEventListener('click', () => this.hideConversationModal());
        document.getElementById('send-message-btn').addEventListener('click', () => this.sendMessage());
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // AI Chat - Use once() to ensure single execution per attachment
        const newChatBtn = document.getElementById('new-chat-btn');
        const handleNewChat = () => {
            console.log('New Chat button clicked at', new Date().toLocaleTimeString());
            
            // Immediately disable button
            newChatBtn.disabled = true;
            newChatBtn.textContent = 'Creating...';
            this.isCreatingChat = true;
            console.log('✅ Button disabled, creating chat...');
            
            // Call createNewChat
            this.createNewChat().finally(() => {
                // Re-attach the listener for next time (using once again)
                newChatBtn.addEventListener('click', handleNewChat, { once: true });
                console.log('✅ Handler re-attached for next click');
            });
        };
        
        // Attach with {once: true} to auto-remove after first click
        newChatBtn.addEventListener('click', handleNewChat, { once: true });
        document.getElementById('send-chat-btn').addEventListener('click', () => this.sendChatMessage());
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendChatMessage();
        });

        // Admin Chat
        document.getElementById('send-admin-message-btn').addEventListener('click', () => this.sendAdminMessage());
        document.getElementById('admin-chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendAdminMessage();
        });
        
        // Admin Reply (for administrators)
        const adminReplyBtn = document.getElementById('send-admin-reply-btn');
        if (adminReplyBtn) {
            adminReplyBtn.addEventListener('click', () => this.sendAdminReply());
        }
        const adminReplyInput = document.getElementById('admin-reply-input');
        if (adminReplyInput) {
            adminReplyInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendAdminReply();
            });
        }
        
        // User Search (for administrators)
        const userSearchInput = document.getElementById('user-search-input');
        if (userSearchInput) {
            userSearchInput.addEventListener('input', () => this.searchUsers());
        }
        
        // Role Filter (for administrators)
        const userRoleFilter = document.getElementById('user-role-filter');
        if (userRoleFilter) {
            userRoleFilter.addEventListener('change', () => this.filterUsersByRole());
        }
        
        // Sortable Table Headers (for administrators)
        // These will be attached after the table is rendered
        this.attachSortHandlers();

        // Settings
        document.getElementById('change-password-form').addEventListener('submit', (e) => this.handlePasswordChange(e));
        
        // Email Verification
        document.getElementById('verify-email-btn').addEventListener('click', () => this.showVerificationModal());
        document.getElementById('resend-code-btn').addEventListener('click', () => this.resendVerificationCode());
        document.getElementById('verification-form').addEventListener('submit', (e) => this.handleVerificationSubmit(e));
        document.getElementById('close-verification-modal').addEventListener('click', () => this.hideVerificationModal());
        document.getElementById('cancel-verification').addEventListener('click', () => this.hideVerificationModal());

        // Modal backdrop clicks
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });
    }

    async checkAuthStatus() {
        if (this.authToken) {
            try {
                const response = await this.apiCall('/api/auth/user', 'GET');
                if (response.ok) {
                    const user = await response.json();
                    this.currentUser = user;
                    this.showDashboard();
                } else {
                    this.clearAuth();
                    this.showScreen('login-screen');
                }
            } catch (error) {
                this.clearAuth();
                this.showScreen('login-screen');
            }
        } else {
            this.showScreen('login-screen');
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const loginData = Object.fromEntries(formData);

        // Handle remember username functionality
        const rememberUsername = document.getElementById('remember-username').checked;
        const username = loginData.username;
        
        if (rememberUsername) {
            localStorage.setItem('rememberedUsername', username);
        } else {
            localStorage.removeItem('rememberedUsername');
        }

        try {
            const response = await this.apiCall('/api/auth/login', 'POST', loginData);
            const result = await response.json();

            if (response.ok) {
                console.log('🔧 Login Debug: Login successful, setting up user data');
                this.authToken = result.token;
                localStorage.setItem('authToken', this.authToken);
                this.currentUser = { id: result.user_id, username: result.username };
                localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                console.log('🔧 Login Debug: User data saved, calling showDashboard');
                this.showNotification('Login successful!', 'success');
                await this.showDashboard();
                console.log('🔧 Login Debug: showDashboard completed');
            } else {
                console.log('🔧 Login Debug: Login failed:', result.error);
                this.showNotification(result.error || 'Login failed', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const signupData = Object.fromEntries(formData);

        if (signupData.password !== signupData.confirmPassword) {
            this.showNotification('Passwords do not match', 'error');
            return;
        }

        try {
            const response = await this.apiCall('/api/auth/signup', 'POST', {
                username: signupData.username,
                email: signupData.email,
                password: signupData.password
            });
            const result = await response.json();

            if (response.ok) {
                this.authToken = result.token;
                localStorage.setItem('authToken', this.authToken);
                this.currentUser = { id: result.user_id, username: result.username };
                this.showNotification('Account created successfully!', 'success');
                this.showDashboard();
            } else {
                this.showNotification(result.error || 'Signup failed', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async verifyAuthToken() {
        try {
            const response = await this.apiCall('/api/user/profile');
            if (!response.ok) {
                console.log('Token verification failed, logging out');
                // Token is invalid, logout
                this.handleLogout();
                return false;
            }
            return true;
        } catch (error) {
            console.log('Token verification error, logging out:', error);
            // Network error or invalid token, logout
            this.handleLogout();
            return false;
        }
    }

    handleLogout() {
        this.authToken = null;
        this.currentUser = null;
        this.currentConversation = null;
        this.currentChatSession = null;
        
        // Stop scroll tracking
        this.stateManager.stopScrollTracking();
        
        // Clear all localStorage data
        this.clearAllState();
        
        // Clear chat messages to prevent showing previous user's messages
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        
        const conversationMessages = document.getElementById('conversation-messages');
        if (conversationMessages) {
            conversationMessages.innerHTML = '';
        }
        
        // Clear chat sessions list
        const chatSessionsList = document.getElementById('chat-sessions-list');
        if (chatSessionsList) {
            chatSessionsList.innerHTML = '';
        }
        
        // Reset scroll position to top
        window.scrollTo(0, 0);
        
        // Remove any inline styles that might have been set
        const dashboard = document.getElementById('dashboard-screen');
        const loginScreen = document.getElementById('login-screen');
        const signupScreen = document.getElementById('signup-screen');
        
        if (dashboard) {
            dashboard.style.display = '';
            dashboard.classList.remove('ready');
        }
        if (loginScreen) {
            loginScreen.style.display = '';
        }
        if (signupScreen) {
            signupScreen.style.display = '';
        }
        
        // Use showScreen to properly manage visibility
        this.showScreen('login-screen');
        
        // Restore remembered username after showing login screen
        if (loginScreen) {
            
            // Restore remembered username if it exists
            const savedUsername = localStorage.getItem('rememberedUsername');
            const usernameInput = document.getElementById('login-username');
            const rememberCheckbox = document.getElementById('remember-username');
            
            if (savedUsername && usernameInput) {
                usernameInput.value = savedUsername;
                if (rememberCheckbox) {
                    rememberCheckbox.checked = true;
                }
            } else if (usernameInput) {
                usernameInput.value = '';
                if (rememberCheckbox) {
                    rememberCheckbox.checked = false;
                }
            }
            
            // Setup password toggle functionality and clear password
            const passwordInput = document.getElementById('login-password');
            const passwordToggle = document.getElementById('password-toggle');
            const toggleText = passwordToggle?.querySelector('.toggle-text');
            
            if (passwordInput) {
                // Clear password field for security
                passwordInput.value = '';
                // Reset password field to hidden
                passwordInput.type = 'password';
            }
            
            if (passwordToggle && toggleText) {
                toggleText.textContent = 'Show';
                
                // Remove any existing listeners and add new one
                passwordToggle.replaceWith(passwordToggle.cloneNode(true));
                const newToggle = document.getElementById('password-toggle');
                const newToggleText = newToggle.querySelector('.toggle-text');
                
                newToggle.addEventListener('click', function() {
                    if (passwordInput.type === 'password') {
                        passwordInput.type = 'text';
                        newToggleText.textContent = 'Hide';
                    } else {
                        passwordInput.type = 'password';
                        newToggleText.textContent = 'Show';
                    }
                });
            }
        }
        
        this.showNotification('Logged out successfully', 'success');
        this.showScreen('login-screen');
    }

    clearAllState() {
        // Clear authentication
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        
        // Use state manager to clear all states
        this.stateManager.clearAllStates();
    }

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(screenId).classList.add('active');
    }

    async showDashboard() {
        console.log('🔧 Dashboard Debug: showDashboard called at', performance.now(), 'ms');
        
        // Show the dashboard screen (single method)
        this.showScreen('dashboard-screen');
        
        // Ensure body is visible
        document.body.classList.add('loaded');
        console.log('🔧 Dashboard Debug: Body loaded class added in showDashboard');
        
        // Only restore scroll if not already done
        if (!this.scrollRestored) {
            console.log('🔧 Dashboard Debug: Restoring scroll position');
            this.stateManager.restoreMainScrollImmediate();
            this.scrollRestored = true;
            console.log('🔧 Dashboard Debug: Scroll restored in showDashboard');
        } else {
            console.log('🔧 Dashboard Debug: Scroll already restored, skipping');
        }
        
        console.log('🔧 Dashboard Debug: Loading user data');
        await this.loadUserData();
        console.log('🔧 Dashboard Debug: User data loaded');
        
        // Use general state manager to restore all states (but default to home if no saved state)
        const savedTab = this.stateManager.getState('currentTab');
        console.log('🔧 Dashboard Debug: Saved tab state:', savedTab);
        
        // Immediately restore the correct tab to prevent empty dashboard flash
        if (!savedTab) {
            // No saved state, go to home tab
            console.log('🔧 Dashboard Debug: No saved tab, switching to home immediately');
            this.switchTab('home');
            console.log('🔧 Dashboard Debug: Switched to home tab (no saved state)');
        } else {
            // Restore saved states immediately
            console.log('🔧 Dashboard Debug: Restoring saved states immediately');
            this.stateManager.restoreStates(this);
            console.log('🔧 Dashboard Debug: Restored saved states immediately');
        }
        
        // Start tracking scroll positions (only once)
        if (!this.scrollTrackingStarted) {
            setTimeout(() => {
                this.stateManager.startScrollTracking();
                this.scrollTrackingStarted = true;
                console.log('🔧 Dashboard Debug: Started scroll tracking');
            }, 200);
        }
        
        console.log('🔧 Dashboard Debug: showDashboard completed');
        
        // Update username display in navbar
        this.updateNavUsername();
        
        // Check if user is admin
        this.checkAdminAccess();
        
        // Check email verification status
        this.checkEmailVerification();
        
        // Check for unread admin messages
        this.checkUnreadAdminMessages();
        
        // Check if user should see personality test banner
        if (typeof window.checkPersonalityTestStatus === 'function') {
            window.checkPersonalityTestStatus();
        }
    }

    updateNavUsername() {
        // Update the username display in the navbar
        const usernameElement = document.getElementById('nav-username');
        if (usernameElement && this.currentUser) {
            usernameElement.textContent = this.currentUser.username || 'User';
        }
    }

    async loadUserData() {
        await Promise.all([
            this.loadProfile(),
            this.loadPsychologyTraits(),
            this.loadConversations(),
            this.loadChatSessions(),
            this.loadMessageUsage()
        ]);
    }
    
    async loadMessageUsage() {
        try {
            const response = await this.apiCall('/api/user/message-usage', 'GET');
            if (response.ok) {
                this.messageUsage = await response.json();
                this.updateUsageDisplay();
            }
        } catch (error) {
            console.error('Failed to load message usage:', error);
        }
    }
    
    updateUsageDisplay() {
        const usageElement = document.getElementById('message-usage-info');
        if (!usageElement || !this.messageUsage) return;
        
        const { role, current_count, limit, remaining } = this.messageUsage;
        
        let html = '';
        if (role === 'administrator') {
            html = '<span class="role-badge admin">👑 Administrator - Unlimited</span>';
        } else if (role === 'paid') {
            html = '<span class="role-badge paid">💎 Paid User - Unlimited</span>';
        } else {
            html = `<span class="role-badge guest">👤 Guest - ${remaining}/${limit} messages remaining today</span>`;
        }
        
        usageElement.innerHTML = html;
    }

    switchTab(tabName) {
        console.log('🔧 Tab Debug: switchTab called with:', tabName);
        
        // Update navigation
        const navBtns = document.querySelectorAll('.nav-btn');
        console.log('🔧 Tab Debug: Found nav buttons:', navBtns.length);
        navBtns.forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeNavBtn = document.querySelector(`[data-tab="${tabName}"]`);
        console.log('🔧 Tab Debug: Active nav button found:', !!activeNavBtn);
        if (activeNavBtn) {
            activeNavBtn.classList.add('active');
            console.log('🔧 Tab Debug: Nav button activated for:', tabName);
        }

        // Update tab content
        const tabContents = document.querySelectorAll('.tab-content');
        console.log('🔧 Tab Debug: Found tab contents:', tabContents.length);
        tabContents.forEach(tab => {
            tab.classList.remove('active');
        });
        
        const activeTab = document.getElementById(`${tabName}-tab`);
        console.log('🔧 Tab Debug: Active tab element found:', !!activeTab, 'for ID:', `${tabName}-tab`);
        if (activeTab) {
            activeTab.classList.add('active');
            console.log('🔧 Tab Debug: Tab content activated for:', tabName);
        }

        // Save state using general state manager
        this.stateManager.saveState('currentTab', tabName);
        console.log('🔧 Tab Debug: Tab state saved:', tabName);

        // Stop auto-refresh intervals when leaving chat tabs
        if (tabName !== 'admin-chat') {
            this.stopAdminChatAutoRefresh();
        }
        if (tabName !== 'admin') {
            this.stopAdminUserChatAutoRefresh();
        }

        // Load data for specific tabs
        if (tabName === 'chat') {
            this.loadChatSessions();
        } else if (tabName === 'conversations') {
            this.loadConversations();
        } else if (tabName === 'psychology') {
            this.loadPsychologyData();
        } else if (tabName === 'admin-chat') {
            this.loadAdminChat();
        } else if (tabName === 'admin') {
            this.loadAdminData();
        }
    }

    switchPsychologySection(section) {
        // Update navigation
        document.querySelectorAll('.psychology-nav-btn').forEach(btn => btn.classList.remove('active'));
        const activeBtn = document.querySelector(`[data-section="${section}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        
        // Update sections
        document.querySelectorAll('.psychology-section').forEach(sectionEl => sectionEl.classList.remove('active'));
        const activeSection = document.getElementById(`psychology-${section}`);
        if (activeSection) activeSection.classList.add('active');

        // Save state using general state manager
        this.stateManager.saveState('currentPsychologySection', section);

        // Load data for specific sections
        if (section === 'history') {
            this.loadAssessmentHistory();
        } else if (section === 'chart') {
            this.loadPsychologyChart();
        }
    }

    // Profile methods
    async loadProfile() {
        try {
            // Load comprehensive profile
            const response = await this.apiCall('/api/user/comprehensive-profile');
            const profile = await response.json();
            
            if (profile && profile.personal_info) {
                this.loadPersonalInfo(profile.personal_info);
                this.loadPreferences(profile.preferences);
                this.loadPrivacySettings(profile.privacy_settings);
                this.updateProfileCompletion(profile.metadata?.profile_completion || 0);
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
    }

    loadPersonalInfo(personalInfo) {
        const nameEl = document.getElementById('personal-name');
        const emailEl = document.getElementById('personal-email');
        const ageEl = document.getElementById('personal-age');
        const locationEl = document.getElementById('personal-location');
        const occupationEl = document.getElementById('personal-occupation');
        const interestsEl = document.getElementById('personal-interests');
        const bioEl = document.getElementById('personal-bio');

        if (nameEl) nameEl.value = personalInfo.name || '';
        if (emailEl) emailEl.value = personalInfo.email || '';
        if (ageEl) ageEl.value = personalInfo.age || '';
        if (locationEl) locationEl.value = personalInfo.location || '';
        if (occupationEl) occupationEl.value = personalInfo.occupation || '';
        if (interestsEl) interestsEl.value = Array.isArray(personalInfo.interests) ? personalInfo.interests.join(', ') : '';
        if (bioEl) bioEl.value = personalInfo.bio || '';
    }

    loadPreferences(preferences) {
        const commStyleEl = document.getElementById('pref-communication-style');
        const langEl = document.getElementById('pref-language');
        const personalityEl = document.getElementById('pref-personality-type');
        const learningEl = document.getElementById('pref-learning-style');
        const topicsEl = document.getElementById('pref-topics');
        const goalsEl = document.getElementById('pref-goals');

        if (commStyleEl) commStyleEl.value = preferences.communication_style || 'friendly';
        if (langEl) langEl.value = preferences.language_preference || 'en';
        if (personalityEl) personalityEl.value = preferences.personality_type || '';
        if (learningEl) learningEl.value = preferences.learning_style || 'mixed';
        if (topicsEl) topicsEl.value = Array.isArray(preferences.topics_of_interest) ? preferences.topics_of_interest.join(', ') : '';
        if (goalsEl) goalsEl.value = Array.isArray(preferences.goals) ? preferences.goals.join(', ') : '';
    }

    loadPrivacySettings(privacySettings) {
        const dataSharingEl = document.getElementById('privacy-data-sharing');
        const analyticsEl = document.getElementById('privacy-analytics');
        const personalizationEl = document.getElementById('privacy-personalization');
        const marketingEl = document.getElementById('privacy-marketing');

        if (dataSharingEl) dataSharingEl.checked = privacySettings.data_sharing || false;
        if (analyticsEl) analyticsEl.checked = privacySettings.analytics || false;
        if (personalizationEl) personalizationEl.checked = privacySettings.personalization || false;
        if (marketingEl) marketingEl.checked = privacySettings.marketing || false;
    }

    updateProfileCompletion(percentage) {
        const completionEl = document.getElementById('profile-completion-text');
        if (completionEl) {
            completionEl.textContent = `Profile: ${percentage}% Complete`;
        }
    }

    switchProfilePage(page) {
        // Update navigation
        document.querySelectorAll('.profile-nav-btn').forEach(btn => btn.classList.remove('active'));
        const activeBtn = document.querySelector(`[data-page="${page}"]`);
        if (activeBtn) activeBtn.classList.add('active');
        
        // Update pages
        document.querySelectorAll('.profile-page').forEach(pageEl => pageEl.classList.remove('active'));
        const activePage = document.getElementById(`profile-page-${page}`);
        if (activePage) activePage.classList.add('active');

        // Save state using general state manager
        this.stateManager.saveState('currentProfilePage', page);
    }

    async loadPsychologyData() {
        // Load comprehensive profile for psychology data
        try {
            const response = await this.apiCall('/api/user/comprehensive-profile');
            const profile = await response.json();
            
            if (profile && profile.preferences) {
                this.psychologyProfile = profile;
                this.loadAssessmentHistory();
                this.loadPsychologyChart();
            }
        } catch (error) {
            console.error('Error loading psychology data:', error);
        }
    }

    loadAssessmentHistory() {
        const container = document.getElementById('assessment-history-container');
        if (!container || !this.psychologyProfile) return;

        const assessmentHistory = this.psychologyProfile.preferences.assessment_history || [];
        
        if (assessmentHistory.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No Assessment History</h3>
                    <p>Complete psychological assessments to see your progress over time.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = assessmentHistory.map(assessment => {
            const date = new Date(assessment.timestamp).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
                <div class="assessment-item">
                    <div class="assessment-header">
                        <div class="assessment-date">${date}</div>
                    </div>
                    <div class="assessment-scores">
                        <div class="score-group">
                            <h4>Carl Jung Types</h4>
                            <div class="score-item">
                                <span class="score-name">Extraversion/Introversion:</span>
                                <span class="score-value">${assessment.jung_types.extraversion_introversion.toFixed(1)}</span>
                            </div>
                            <div class="score-item">
                                <span class="score-name">Sensing/Intuition:</span>
                                <span class="score-value">${assessment.jung_types.sensing_intuition.toFixed(1)}</span>
                            </div>
                            <div class="score-item">
                                <span class="score-name">Thinking/Feeling:</span>
                                <span class="score-value">${assessment.jung_types.thinking_feeling.toFixed(1)}</span>
                            </div>
                            <div class="score-item">
                                <span class="score-name">Judging/Perceiving:</span>
                                <span class="score-value">${assessment.jung_types.judging_perceiving.toFixed(1)}</span>
                            </div>
                        </div>
                        <div class="score-group">
                            <h4>Big Five Traits</h4>
                            <div class="score-item">
                                <span class="score-name">Openness:</span>
                                <span class="score-value">${assessment.big_five.openness}/10</span>
                            </div>
                            <div class="score-item">
                                <span class="score-name">Conscientiousness:</span>
                                <span class="score-value">${assessment.big_five.conscientiousness}/10</span>
                            </div>
                            <div class="score-item">
                                <span class="score-name">Extraversion:</span>
                                <span class="score-value">${assessment.big_five.extraversion}/10</span>
                            </div>
                            <div class="score-item">
                                <span class="score-name">Agreeableness:</span>
                                <span class="score-value">${assessment.big_five.agreeableness}/10</span>
                            </div>
                            <div class="score-item">
                                <span class="score-name">Neuroticism:</span>
                                <span class="score-value">${assessment.big_five.neuroticism}/10</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    loadPsychologyChart() {
        if (!this.psychologyProfile) return;
        
        const chartType = document.querySelector('input[name="chart-type"]:checked')?.value || 'jung';
        this.updateChart(chartType);
    }

    updateChart(chartType) {
        const canvas = document.getElementById('psychology-chart-canvas');
        if (!canvas || !this.psychologyProfile) return;

        const ctx = canvas.getContext('2d');
        const assessmentHistory = this.psychologyProfile.preferences.assessment_history || [];
        
        if (assessmentHistory.length === 0) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#666';
            ctx.font = '16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('No assessment data available', canvas.width / 2, canvas.height / 2);
            return;
        }

        // Simple line chart implementation
        this.drawChart(ctx, canvas, assessmentHistory, chartType);
    }

    drawChart(ctx, canvas, data, chartType) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const padding = 60;
        const chartWidth = canvas.width - 2 * padding;
        const chartHeight = canvas.height - 2 * padding;
        
        // Draw axes
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();
        
        // Prepare data based on chart type for axis labels
        let yRange;
        if (chartType === 'jung') {
            yRange = [-10, 10];
        } else {
            yRange = [0, 10];
        }
        
        // Draw vertical axis labels
        ctx.fillStyle = '#666';
        ctx.font = '12px Arial';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        
        const numTicks = 11; // 11 ticks for 0-10 or -10 to +10
        for (let i = 0; i < numTicks; i++) {
            const value = yRange[0] + (i / (numTicks - 1)) * (yRange[1] - yRange[0]);
            const y = canvas.height - padding - (i / (numTicks - 1)) * chartHeight;
            
            // Draw tick mark
            ctx.strokeStyle = '#ddd';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(padding - 5, y);
            ctx.lineTo(padding + 5, y);
            ctx.stroke();
            
            // Draw grid line
            if (i > 0 && i < numTicks - 1) {
                ctx.strokeStyle = '#f0f0f0';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(canvas.width - padding, y);
                ctx.stroke();
            }
            
            // Draw label
            ctx.fillStyle = '#666';
            ctx.fillText(value.toFixed(0), padding - 10, y);
        }
        
        // Draw horizontal axis labels (dates)
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        data.forEach((assessment, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            const date = new Date(assessment.timestamp);
            const dateLabel = `${date.getMonth() + 1}/${date.getDate()}`;
            ctx.fillText(dateLabel, x, canvas.height - padding + 10);
        });
        
        // Prepare data based on chart type
        let traits, colors, traitLabels;
        if (chartType === 'jung') {
            traits = ['extraversion_introversion', 'sensing_intuition', 'thinking_feeling', 'judging_perceiving'];
            colors = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2'];
            traitLabels = [
                'Introversion vs Extraversion',
                'Sensing vs Intuition', 
                'Feeling vs Thinking',
                'Perceiving vs Judging'
            ];
        } else {
            traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
            colors = ['#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#d32f2f'];
            traitLabels = [
                'Closedness vs Openness',
                'Carelessness vs Conscientiousness',
                'Introversion vs Extraversion',
                'Antagonism vs Agreeableness',
                'Emotional Stability vs Neuroticism'
            ];
        }
        
        // Draw lines for each trait
        traits.forEach((trait, index) => {
            ctx.strokeStyle = colors[index];
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            data.forEach((assessment, dataIndex) => {
                const x = padding + (dataIndex / (data.length - 1)) * chartWidth;
                const value = chartType === 'jung' ? assessment.jung_types[trait] : assessment.big_five[trait];
                const y = canvas.height - padding - ((value - yRange[0]) / (yRange[1] - yRange[0])) * chartHeight;
                
                if (dataIndex === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            
            ctx.stroke();
        });
        
        // Draw legend with better spacing and consistent A vs B labels
        const legendStartY = 20;
        const legendItemHeight = 20;
        const legendItemsPerRow = chartType === 'jung' ? 2 : 3; // 2 items per row for Jung, 3 for Big Five
        
        traitLabels.forEach((traitLabel, index) => {
            const row = Math.floor(index / legendItemsPerRow);
            const col = index % legendItemsPerRow;
            const legendX = padding + col * 200; // Increased spacing to 200px for longer labels
            const legendY = legendStartY + row * legendItemHeight;
            
            // Draw color box
            ctx.fillStyle = colors[index];
            ctx.fillRect(legendX, legendY, 15, 15);
            
            // Draw trait label with consistent A vs B format
            ctx.fillStyle = '#333';
            ctx.font = '11px Arial';
            ctx.textAlign = 'left';
            
            // Shorten long labels for better fit
            let displayLabel = traitLabel;
            if (traitLabel.length > 25) {
                displayLabel = traitLabel.substring(0, 22) + '...';
            }
            
            ctx.fillText(displayLabel, legendX + 20, legendY + 12);
        });
    }

    // Psychology traits methods
    async loadPsychologyTraits() {
        // Load current traits from comprehensive profile instead
        if (this.psychologyProfile && this.psychologyProfile.preferences) {
            this.renderCurrentTraits(this.psychologyProfile.preferences);
        } else {
            // Load comprehensive profile if not already loaded
            try {
                const response = await this.apiCall('/api/user/comprehensive-profile');
                const profile = await response.json();
                
                if (profile && profile.preferences) {
                    this.psychologyProfile = profile;
                    this.renderCurrentTraits(profile.preferences);
                }
            } catch (error) {
                console.error('Failed to load psychology traits:', error);
            }
        }
    }

    getTraitDescription(value, traitA, traitB) {
        if (value <= 3) {
            return `Strong ${traitA} (${value}/10)`;
        } else if (value <= 4) {
            return `Moderate ${traitA} (${value}/10)`;
        } else if (value <= 6) {
            return `Balanced between ${traitA} and ${traitB} (${value}/10)`;
        } else if (value <= 7) {
            return `Moderate ${traitB} (${value}/10)`;
        } else {
            return `Strong ${traitB} (${value}/10)`;
        }
    }

    renderCurrentTraits(preferences) {
        const traitsGrid = document.getElementById('traits-grid');
        if (!traitsGrid) return;

        // Get the most current trait values
        const jungTypes = preferences.jung_types || {};
        const bigFive = preferences.big_five || {};
        
        // Convert Carl Jung traits to 1-10 scale (from -10 to +10 range)
        const jungTraits = [
            {
                name: 'Introversion vs Extraversion',
                value: Math.round(((jungTypes.extraversion_introversion || 0) + 10) / 2),
                description: this.getTraitDescription(Math.round(((jungTypes.extraversion_introversion || 0) + 10) / 2), 'Introversion', 'Extraversion'),
                category: 'Carl Jung'
            },
            {
                name: 'Sensing vs Intuition', 
                value: Math.round(((jungTypes.sensing_intuition || 0) + 10) / 2),
                description: this.getTraitDescription(Math.round(((jungTypes.sensing_intuition || 0) + 10) / 2), 'Sensing', 'Intuition'),
                category: 'Carl Jung'
            },
            {
                name: 'Feeling vs Thinking',
                value: Math.round(((jungTypes.thinking_feeling || 0) + 10) / 2),
                description: this.getTraitDescription(Math.round(((jungTypes.thinking_feeling || 0) + 10) / 2), 'Feeling', 'Thinking'),
                category: 'Carl Jung'
            },
            {
                name: 'Perceiving vs Judging',
                value: Math.round(((jungTypes.judging_perceiving || 0) + 10) / 2),
                description: this.getTraitDescription(Math.round(((jungTypes.judging_perceiving || 0) + 10) / 2), 'Perceiving', 'Judging'),
                category: 'Carl Jung'
            }
        ];

        // Big Five traits (already 0-10 scale)
        const bigFiveTraits = [
            {
                name: 'Closedness vs Openness',
                value: Math.round(bigFive.openness || 5),
                description: this.getTraitDescription(Math.round(bigFive.openness || 5), 'Closedness to Experience', 'Openness to Experience'),
                category: 'Big Five'
            },
            {
                name: 'Carelessness vs Conscientiousness',
                value: Math.round(bigFive.conscientiousness || 5),
                description: this.getTraitDescription(Math.round(bigFive.conscientiousness || 5), 'Carelessness', 'Conscientiousness'),
                category: 'Big Five'
            },
            {
                name: 'Introversion vs Extraversion',
                value: Math.round(bigFive.extraversion || 5),
                description: this.getTraitDescription(Math.round(bigFive.extraversion || 5), 'Introversion', 'Extraversion'),
                category: 'Big Five'
            },
            {
                name: 'Antagonism vs Agreeableness',
                value: Math.round(bigFive.agreeableness || 5),
                description: this.getTraitDescription(Math.round(bigFive.agreeableness || 5), 'Antagonism', 'Agreeableness'),
                category: 'Big Five'
            },
            {
                name: 'Emotional Stability vs Neuroticism',
                value: Math.round(bigFive.neuroticism || 5),
                description: this.getTraitDescription(Math.round(bigFive.neuroticism || 5), 'Emotional Stability', 'Neuroticism'),
                category: 'Big Five'
            }
        ];

        const allTraits = [...jungTraits, ...bigFiveTraits];

        if (allTraits.length === 0) {
            traitsGrid.innerHTML = `
                <div class="empty-state">
                    <h3>No Psychology Traits</h3>
                    <p>Complete psychological assessments to see your personality traits.</p>
                </div>
            `;
            return;
        }

        traitsGrid.innerHTML = allTraits.map(trait => {
            const percentage = (trait.value / 10) * 100;
            const colorClass = trait.category === 'Carl Jung' ? 'jung-trait' : 'bigfive-trait';
            
            return `
                <div class="current-trait-card ${colorClass}">
                    <div class="trait-header">
                        <div class="trait-category">${trait.category}</div>
                        <div class="trait-score">${trait.value}/10</div>
                    </div>
                    <div class="trait-name">${trait.name}</div>
                    <div class="trait-bar">
                        <div class="trait-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div class="trait-description">${trait.description}</div>
                </div>
            `;
        }).join('');
    }

    renderTraits(traits) {
        const traitsGrid = document.getElementById('traits-grid');
        
        if (traits.length === 0) {
            traitsGrid.innerHTML = `
                <div class="empty-state">
                    <h3>No Psychology Traits</h3>
                    <p>Add your first psychology trait to help the AI understand your personality better.</p>
                </div>
            `;
            return;
        }

        traitsGrid.innerHTML = traits.map(trait => `
            <div class="trait-card">
                <div class="trait-header">
                    <div class="trait-name">${trait.trait_name}</div>
                    <div class="trait-value">${trait.trait_value}</div>
                </div>
                <div class="trait-description">${trait.trait_description || 'No description'}</div>
                <div class="trait-actions">
                    <button class="btn btn-small btn-primary" onclick="app.editTrait('${trait.trait_name}', ${trait.trait_value}, '${trait.trait_description || ''}')">Edit</button>
                </div>
            </div>
        `).join('');
    }

    showTraitModal(traitName = '', traitValue = '', description = '') {
        document.getElementById('trait-modal-title').textContent = traitName ? 'Edit Psychology Trait' : 'Add Psychology Trait';
        document.getElementById('trait-name').value = traitName;
        document.getElementById('trait-value').value = traitValue;
        document.getElementById('trait-description').value = description;
        document.getElementById('trait-modal').classList.add('active');
    }

    hideTraitModal() {
        document.getElementById('trait-modal').classList.remove('active');
        document.getElementById('trait-form').reset();
    }

    editTrait(traitName, traitValue, description) {
        this.showTraitModal(traitName, traitValue, description);
    }

    async handleTraitSubmit(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const traitData = Object.fromEntries(formData);

        try {
            const isEdit = document.getElementById('trait-modal-title').textContent.includes('Edit');
            const url = isEdit ? `/api/user/psychology-traits/${traitData.traitName}` : '/api/user/psychology-traits';
            const method = isEdit ? 'PUT' : 'POST';

            const response = await this.apiCall(url, method, {
                traitName: traitData.traitName,
                traitValue: parseFloat(traitData.traitValue),
                description: traitData.description
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification(`Psychology trait ${isEdit ? 'updated' : 'created'} successfully!`, 'success');
                this.hideTraitModal();
                await this.loadPsychologyTraits();
            } else {
                this.showNotification(result.error || 'Failed to save trait', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    // Conversation methods
    async loadConversations() {
        try {
            const response = await this.apiCall('/api/user/conversations', 'GET');
            if (response.ok) {
                const conversations = await response.json();
                this.renderConversations(conversations);
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }

    renderConversations(conversations) {
        const conversationsList = document.getElementById('conversations-list');
        
        if (conversations.length === 0) {
            conversationsList.innerHTML = `
                <div class="empty-state">
                    <h3>No Conversations</h3>
                    <p>Start your first conversation!</p>
                </div>
            `;
            return;
        }

        conversationsList.innerHTML = conversations.map(conv => {
            const date = new Date(conv.updated_at);
            const formattedDate = date.toLocaleDateString();
            const formattedTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const datetime = `${formattedDate} ${formattedTime}`;
            
            return `
                <div class="conversation-item" data-session-id="${conv.session_id}" onclick="app.selectConversation('${conv.session_id}')">
                    <div class="conversation-title">${conv.title}</div>
                    <div class="conversation-date">${datetime}</div>
                </div>
            `;
        }).join('');
    }

    async selectConversation(sessionId) {
        // Update UI
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        const selectedItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }

        this.currentConversation = sessionId;
        
        // Save state using general state manager
        this.stateManager.saveState('selectedConversation', sessionId);
        
        const messageInputArea = document.getElementById('message-input-area');
        if (messageInputArea) {
            messageInputArea.style.display = 'block';
        }

        // Load messages
        try {
            const response = await this.apiCall(`/api/user/conversations/${sessionId}/messages`, 'GET');
            if (response.ok) {
                const messages = await response.json();
                this.renderConversationMessages(messages);
            }
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    }

    renderConversationMessages(messages) {
        const messagesContainer = document.getElementById('conversation-messages');
        
        if (messages.length === 0) {
            messagesContainer.innerHTML = '<p class="no-conversation">No messages in this conversation yet.</p>';
            return;
        }

        messagesContainer.innerHTML = messages.map(msg => {
            // Fix encoding issues in message content
            const cleanContent = this.fixTextEncoding(msg.content);
            
            // Format timestamp
            const timestamp = this.formatTimestamp(msg.timestamp);
            
            return `
                <div class="message ${msg.sender_type}">
                    <div class="message-content">${cleanContent}</div>
                    ${timestamp ? `<div class="message-timestamp">${timestamp}</div>` : ''}
                </div>
            `;
        }).join('');

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showConversationModal() {
        document.getElementById('conversation-modal').classList.add('active');
    }

    hideConversationModal() {
        document.getElementById('conversation-modal').classList.remove('active');
        document.getElementById('conversation-form').reset();
    }

    async handleConversationSubmit(e) {
        e.preventDefault();
        
        // Prevent duplicate submission
        if (this.isSubmittingConversation) {
            console.log('Conversation submission already in progress');
            return;
        }
        
        this.isSubmittingConversation = true;
        const formData = new FormData(e.target);
        const conversationData = Object.fromEntries(formData);

        try {
            const response = await this.apiCall('/api/user/conversations', 'POST', conversationData);
            const result = await response.json();

            if (response.ok) {
                this.showNotification('Conversation created successfully!', 'success');
                this.hideConversationModal();
                await this.loadConversations();
            } else {
                this.showNotification(result.error || 'Failed to create conversation', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            this.isSubmittingConversation = false;
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const content = messageInput.value.trim();

        if (!content || !this.currentConversation) return;

        try {
            const response = await this.apiCall(`/api/user/conversations/${this.currentConversation}/messages`, 'POST', {
                senderType: 'user',
                content: content
            });

            if (response.ok) {
                const result = await response.json();
                messageInput.value = '';
                
                // Reload messages to show both user message and AI response
                await this.selectConversation(this.currentConversation);
            }
        } catch (error) {
            this.showNotification('Failed to send message', 'error');
        }
    }

    // AI Chat methods
    async loadChatSessions() {
        try {
            const response = await this.apiCall('/api/user/conversations', 'GET');
            if (response.ok) {
                const sessions = await response.json();
                this.renderChatSessions(sessions);
            }
        } catch (error) {
            console.error('Failed to load chat sessions:', error);
        }
    }

    renderChatSessions(sessions) {
        const chatSessionsList = document.getElementById('chat-sessions-list');
        
        if (sessions.length === 0) {
            chatSessionsList.innerHTML = `
                <div class="empty-state">
                    <h3>No Chat Sessions</h3>
                    <p>Start your first AI conversation!</p>
                </div>
            `;
            return;
        }

        chatSessionsList.innerHTML = sessions.map(session => `
            <div class="chat-session-item" data-session-id="${session.session_id}">
                <div class="session-content" onclick="window.integratedAIChatbot.selectChatSession('${session.session_id}')">
                    <div class="session-title">${session.title}</div>
                    <div class="session-date">${new Date(session.updated_at).toLocaleDateString()}</div>
                </div>
                <button class="delete-chat-btn" onclick="event.stopPropagation(); window.integratedAIChatbot.deleteChat('${session.session_id}')" title="Delete chat">×</button>
            </div>
        `).join('');
    }

    async selectChatSession(sessionId) {
        // Update UI
        document.querySelectorAll('.chat-session-item').forEach(item => {
            item.classList.remove('active');
        });
        const selectedItem = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('active');
        }

        this.currentChatSession = sessionId;
        
        // Save state using general state manager
        this.stateManager.saveState('selectedChatSession', sessionId);

        // Load messages
        try {
            const response = await this.apiCall(`/api/user/conversations/${sessionId}/messages`, 'GET');
            if (response.ok) {
                const messages = await response.json();
                this.renderChatMessages(messages);
            }
        } catch (error) {
            console.error('Failed to load chat messages:', error);
        }
    }

    renderChatMessages(messages) {
        const messagesContainer = document.getElementById('chat-messages');
        
        if (messages.length === 0) {
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <h3>Start Chatting with AI!</h3>
                    <p>Your conversation will be personalized based on your profile and psychology traits.</p>
                </div>
            `;
            return;
        }

        messagesContainer.innerHTML = messages.map(msg => {
            // Fix encoding issues in message content
            const cleanContent = this.fixTextEncoding(msg.content);
            
            // Format timestamp
            const timestamp = this.formatTimestamp(msg.timestamp);
            
            return `
                <div class="message ${msg.sender_type}">
                    <div class="message-content">${cleanContent}</div>
                    ${timestamp ? `<div class="message-timestamp">${timestamp}</div>` : ''}
                </div>
            `;
        }).join('');

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async createNewChat() {
        // Flag is already set by caller (either handler or checked in sendChatMessage)
        // Just proceed with the actual creation
        const newChatBtn = document.getElementById('new-chat-btn');
        
        try {
            console.log('Creating new chat...');
            const response = await this.apiCall('/api/user/conversations', 'POST', {
                title: `Chat ${new Date().toLocaleString()}`
            });
            const result = await response.json();

            if (response.ok) {
                console.log('Chat created successfully:', result.session_id);
                this.showNotification('New chat created!', 'success');
                await this.loadChatSessions();
                this.selectChatSession(result.session_id);
            } else {
                console.error('Failed to create chat:', result.error);
                this.showNotification(result.error || 'Failed to create chat', 'error');
            }
        } catch (error) {
            console.error('Network error creating chat:', error);
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            // Re-enable button and reset flag
            this.isCreatingChat = false;
            if (newChatBtn) {
                newChatBtn.disabled = false;
                newChatBtn.textContent = 'New Chat';
            }
            console.log('Chat creation complete, button re-enabled');
        }
    }

    async deleteChat(sessionId) {
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await this.apiCall(`/api/user/conversations/${sessionId}`, 'DELETE');
            
            if (response.ok) {
                this.showNotification('Chat deleted successfully', 'success');
                
                // If the deleted chat was selected, clear the chat area
                if (this.currentChatSession === sessionId) {
                    this.currentChatSession = null;
                    document.getElementById('chat-messages').innerHTML = `
                        <div class="empty-state">
                            <h3>Start Chatting with AI!</h3>
                            <p>Your conversation will be personalized based on your profile and psychology traits.</p>
                        </div>
                    `;
                }
                
                // Reload the chat list
                await this.loadChatSessions();
            } else {
                const result = await response.json();
                this.showNotification(result.error || 'Failed to delete chat', 'error');
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async sendChatMessage() {
        const chatInput = document.getElementById('chat-input');
        const content = chatInput.value.trim();

        if (!content) return;

        // If no current session, create one
        if (!this.currentChatSession) {
            // Don't create if already creating
            if (this.isCreatingChat) {
                console.log('⛔ Cannot send message: chat creation already in progress');
                this.showNotification('Please wait, creating chat...', 'info');
                return;
            }
            // Set flag before calling
            this.isCreatingChat = true;
            await this.createNewChat();
            // Wait a bit for the session to be created
            await new Promise(resolve => setTimeout(resolve, 500));
        }

        if (!this.currentChatSession) {
            this.showNotification('Please create a chat session first', 'error');
            return;
        }

        try {
            // Show user message immediately with timestamp
            const messagesContainer = document.getElementById('chat-messages');
            const userMessage = document.createElement('div');
            userMessage.className = 'message user';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = content;
            
            const timestamp = document.createElement('div');
            timestamp.className = 'message-timestamp';
            timestamp.id = 'temp-user-timestamp';
            timestamp.textContent = this.formatTimestamp(new Date());
            
            userMessage.appendChild(messageContent);
            userMessage.appendChild(timestamp);
            messagesContainer.appendChild(userMessage);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            chatInput.value = '';
            chatInput.disabled = true;

            // Show thinking indicator
            const thinkingMessage = document.createElement('div');
            thinkingMessage.className = 'message thinking';
            thinkingMessage.id = 'thinking-indicator';
            thinkingMessage.innerHTML = `
                AI is thinking
                <div class="thinking-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            messagesContainer.appendChild(thinkingMessage);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            // Send to API
            const response = await this.apiCall(`/api/user/conversations/${this.currentChatSession}/messages`, 'POST', {
                senderType: 'user',
                content: content
            });

            // Remove thinking indicator
            const thinkingIndicator = document.getElementById('thinking-indicator');
            if (thinkingIndicator) {
                thinkingIndicator.remove();
            }

            if (response.ok) {
                const result = await response.json();
                
                // Update user message timestamp with server time
                if (result.timestamp) {
                    const tempTimestamp = document.getElementById('temp-user-timestamp');
                    if (tempTimestamp) {
                        tempTimestamp.textContent = this.formatTimestamp(result.timestamp);
                        tempTimestamp.id = ''; // Remove temp ID
                    }
                }
                
                // Update usage info if provided
                if (result.usage) {
                    this.messageUsage = result.usage;
                    this.updateUsageDisplay();
                }
                
                // Show AI response with timestamp
                if (result.ai_response) {
                    const aiMessage = document.createElement('div');
                    aiMessage.className = 'message assistant';
                    
                    const aiContent = document.createElement('div');
                    aiContent.className = 'message-content';
                    aiContent.textContent = result.ai_response;
                    
                    const aiTimestamp = document.createElement('div');
                    aiTimestamp.className = 'message-timestamp';
                    // Use client timestamp for local time
                    aiTimestamp.textContent = this.formatTimestamp(result.timestamp || new Date());
                    
                    aiMessage.appendChild(aiContent);
                    aiMessage.appendChild(aiTimestamp);
                    messagesContainer.appendChild(aiMessage);
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
            } else if (response.status === 403) {
                // Handle limit reached
                const result = await response.json();
                if (result.limit_reached) {
                    // Remove the optimistically added user message
                    userMessage.remove();
                    chatInput.value = content; // Restore the message
                    
                    this.showNotification(result.error || 'Message limit reached', 'error');
                    
                    // Update usage display
                    if (result.usage) {
                        this.messageUsage = result.usage;
                        this.updateUsageDisplay();
                    }
                } else {
                    this.showNotification('Access denied', 'error');
                }
            } else {
                this.showNotification('Failed to send message', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
        }
    }

    // Settings methods
    async handlePasswordChange(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const passwordData = Object.fromEntries(formData);

        if (passwordData.newPassword !== passwordData.confirmNewPassword) {
            this.showNotification('New passwords do not match', 'error');
            return;
        }

        try {
            const response = await this.apiCall('/api/auth/change-password', 'POST', {
                currentPassword: passwordData.currentPassword,
                newPassword: passwordData.newPassword
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Password changed successfully!', 'success');
                e.target.reset();
            } else {
                this.showNotification(result.error || 'Failed to change password', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    // Utility methods
    async apiCall(url, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json; charset=utf-8',
            }
        };

        if (this.authToken) {
            options.headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        
        // Handle 401 Unauthorized globally (except for login/signup)
        if (response.status === 401 && !url.includes('/api/auth/login') && !url.includes('/api/auth/signup')) {
            console.log('401 Unauthorized - logging out');
            this.handleLogout();
        }
        
        return response;
    }

    // Helper method to properly decode text content
    async getTextContent(response) {
        const text = await response.text();
        return this.fixTextEncoding(text);
    }

    // Helper method to fix text encoding issues
    fixTextEncoding(text) {
        if (!text || typeof text !== 'string') return text;
        
        // Fix common encoding issues
        let cleaned = text
            .replace(/â€™/g, "'")   // Fix apostrophe
            .replace(/â€œ/g, '"')   // Fix opening quote
            .replace(/â€\u009d/g, '"') // Fix closing quote (alternative)
            .replace(/â€/g, '"')    // Fix closing quote
            .replace(/â€"/g, '—')   // Fix em dash
            .replace(/â€"/g, '–')   // Fix en dash
            .replace(/Â/g, '')      // Remove non-breaking space artifacts
            .replace(/â€¦/g, '…')   // Fix ellipsis
            .replace(/â€¢/g, '•')   // Fix bullet point
            .replace(/Ã¡/g, 'á')    // Fix accented a
            .replace(/Ã©/g, 'é')    // Fix accented e
            .replace(/Ã­/g, 'í')    // Fix accented i
            .replace(/Ã³/g, 'ó')    // Fix accented o
            .replace(/Ãº/g, 'ú')    // Fix accented u
            .replace(/â€œ/g, '"')   // Fix smart quotes
            .replace(/â€\u009d/g, '"') // Fix smart quotes end
            .replace(/â€˜/g, "'")   // Fix smart single quote start
            .replace(/â€™/g, "'")   // Fix smart single quote end
            .replace(/â€/g, '"');   // Catch remaining quote artifacts
        
        // Fix AI-generated double quotes patterns
        cleaned = cleaned
            .replace(/""([^"]*)""/g, '"$1"')  // Fix double double quotes around content
            .replace(/""\s*([^"]*?)\s*""/g, '"$1"')  // Fix with spaces
            .replace(/^""\s*(.+?)\s*""$/g, '"$1"')   // Fix at start/end of string
            .replace(/(\w)""(\w)/g, '$1"$2')         // Fix between words
            .replace(/""([a-zA-Z])/g, '"$1')         // Fix before letters
            .replace(/([a-zA-Z])""/g, '$1"')         // Fix after letters
            .replace(/\s""\s/g, ' " ')               // Fix standalone double quotes
            .replace(/''/g, '"')                     // Fix double single quotes
            .replace(/"{2,}/g, '"');                 // Fix multiple consecutive quotes
        
        // Fix corrupted emojis and special characters
        cleaned = cleaned
            .replace(/ðŸ˜Š/g, '😊')          // Fix smiling face emoji
            .replace(/ðŸ˜‚/g, '😂')          // Fix laughing emoji
            .replace(/ðŸ˜/g, '😍')           // Fix heart eyes emoji
            .replace(/ðŸ˜Ž/g, '😎')          // Fix cool emoji
            .replace(/ðŸ˜¢/g, '😢')          // Fix crying emoji
            .replace(/ðŸ˜±/g, '😱')          // Fix shocked emoji
            .replace(/ðŸ˜´/g, '😴')          // Fix sleeping emoji
            .replace(/ðŸ¤"/g, '🤔')          // Fix thinking emoji
            .replace(/ðŸ'/g, '👍')           // Fix thumbs up
            .replace(/ðŸ'Ž/g, '👎')          // Fix thumbs down
            .replace(/â¤ï¸/g, '❤️')          // Fix heart
            .replace(/ðŸ"¥/g, '🔥')          // Fix fire emoji
            .replace(/âœ¨/g, '✨')           // Fix sparkles
            .replace(/ðŸŽ‰/g, '🎉')          // Fix party emoji
            .replace(/ðŸš€/g, '🚀')          // Fix rocket emoji
            .replace(/ðŸ¤–/g, '🤖')          // Fix robot emoji
            .replace(/ðŸ§ /g, '🧠')          // Fix brain emoji
            .replace(/ðŸ'¡/g, '💡')          // Fix lightbulb emoji
            .replace(/âš¡/g, '⚡')           // Fix lightning emoji
            .replace(/ðŸŽ¯/g, '🎯');         // Fix target emoji
        
        return cleaned;
    }

    async checkAdminAccess() {
        /**Check if user is admin and show admin tab */
        try {
            const response = await this.apiCall('/api/user/profile', 'GET');
            if (response.ok) {
                const profile = await response.json();
                if (profile.user_role === 'administrator') {
                    // Show admin tab
                    const adminTabBtn = document.getElementById('admin-tab-btn');
                    if (adminTabBtn) {
                        adminTabBtn.style.display = 'block';
                    }
                    
                    // Hide "Contact Admin" button for administrators
                    const contactAdminBtn = document.getElementById('admin-chat-tab-btn');
                    if (contactAdminBtn) {
                        contactAdminBtn.style.display = 'none';
                    }
                }
            }
        } catch (error) {
            console.error('Error checking admin access:', error);
        }
    }

    async loadAdminData() {
        /**Load admin statistics and user data */
        try {
            // Load statistics
            const statsResponse = await this.apiCall('/api/admin/statistics', 'GET');
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                document.getElementById('stat-total-users').textContent = stats.total_users;
                document.getElementById('stat-total-messages').textContent = stats.total_messages;
                document.getElementById('stat-messages-today').textContent = stats.messages_today;
                document.getElementById('stat-active-today').textContent = stats.active_today;
            }

            // Load users
            const usersResponse = await this.apiCall('/api/admin/users', 'GET');
            if (usersResponse.ok) {
                const users = await usersResponse.json();
                this.renderAdminUsersTable(users);
            }
            
            // Load user chats
            await this.loadAdminChatsList();
        } catch (error) {
            console.error('Error loading admin data:', error);
            this.showNotification('Failed to load admin data', 'error');
        }
    }

    renderAdminUsersTable(users) {
        /**Render the admin users table */
        const tbody = document.getElementById('admin-users-table');
        
        // Store all users for search and sort functionality
        this.allUsers = users;
        this.currentSortColumn = 'created_at';
        this.currentSortDirection = 'desc';
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center;">No users found</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => {
            const createdDate = new Date(user.created_at).toLocaleDateString();
            const lastActive = user.last_active ? new Date(user.last_active).toLocaleDateString() : 'Never';
            const isDeleted = user.is_deleted;
            const rowStyle = isDeleted ? 'opacity: 0.5; background: #f9f9f9;' : '';
            const deleteBtn = isDeleted 
                ? `<button class="btn-small btn-success" onclick="app.restoreUser(${user.id})" title="Restore User">
                       <i class="fas fa-undo"></i> Restore
                   </button>`
                : `<button class="btn-small btn-danger" onclick="app.deleteUser(${user.id}, '${user.username}')" title="Delete User">
                       <i class="fas fa-trash"></i> Delete
                   </button>`;
            
            return `
                <tr style="${rowStyle}" 
                    data-username="${user.username.toLowerCase()}" 
                    data-email="${user.email.toLowerCase()}"
                    data-role="${user.role}"
                    data-id="${user.id}"
                    data-total-messages="${user.total_messages}"
                    data-total-conversations="${user.total_conversations}"
                    data-last-active="${user.last_active || ''}"
                    data-created-at="${user.created_at}">
                    <td>${user.id}</td>
                    <td class="sticky-column" style="position: sticky; left: 0; background: ${isDeleted ? '#f9f9f9' : 'white'}; z-index: 1;">
                        <strong>${user.username}${isDeleted ? ' <span style="color: #999;">(Deleted)</span>' : ''}</strong>
                    </td>
                    <td>${user.email}</td>
                    <td><span class="role-badge ${user.role}">${user.role}</span></td>
                    <td>${user.total_messages}</td>
                    <td>${user.total_conversations}</td>
                    <td>${lastActive}</td>
                    <td>${createdDate}</td>
                    <td>${deleteBtn}</td>
                </tr>
            `;
        }).join('');
        
        // Attach sort handlers after rendering
        this.attachSortHandlers();
    }
    
    searchUsers() {
        /**Search users by username or email */
        const searchInput = document.getElementById('user-search-input');
        const searchTerm = searchInput.value.toLowerCase();
        this.applyFilters();
    }
    
    filterUsersByRole() {
        /**Filter users by selected role */
        this.applyFilters();
    }
    
    applyFilters() {
        /**Apply both search and role filters */
        const searchInput = document.getElementById('user-search-input');
        const roleFilter = document.getElementById('user-role-filter');
        const searchTerm = searchInput.value.toLowerCase();
        const selectedRole = roleFilter.value;
        const tbody = document.getElementById('admin-users-table');
        const rows = tbody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const username = row.getAttribute('data-username');
            const email = row.getAttribute('data-email');
            const role = row.getAttribute('data-role');
            
            if (username && email && role) {
                // Check search filter
                const matchesSearch = searchTerm === '' || 
                                    username.includes(searchTerm) || 
                                    email.includes(searchTerm);
                
                // Check role filter
                const matchesRole = selectedRole === 'all' || role === selectedRole;
                
                // Show row only if it matches both filters
                if (matchesSearch && matchesRole) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        });
    }
    
    sortUsersTable(column) {
        /**Sort the users table by specified column */
        const tbody = document.getElementById('admin-users-table');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Toggle sort direction if same column
        if (this.currentSortColumn === column) {
            this.currentSortDirection = this.currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSortColumn = column;
            this.currentSortDirection = 'asc';
        }
        
        // Sort rows
        rows.sort((a, b) => {
            let aVal = a.getAttribute(`data-${column.replace('_', '-')}`) || '';
            let bVal = b.getAttribute(`data-${column.replace('_', '-')}`) || '';
            
            // Convert to numbers for numeric columns
            if (['id', 'total_messages', 'total_conversations'].includes(column)) {
                aVal = parseInt(aVal) || 0;
                bVal = parseInt(bVal) || 0;
            }
            
            // Handle dates
            if (['created_at', 'last_active'].includes(column)) {
                aVal = aVal ? new Date(aVal).getTime() : 0;
                bVal = bVal ? new Date(bVal).getTime() : 0;
            }
            
            if (aVal < bVal) return this.currentSortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.currentSortDirection === 'asc' ? 1 : -1;
            return 0;
        });
        
        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
        
        // Update sort icons
        document.querySelectorAll('.sortable i').forEach(icon => {
            icon.className = 'fas fa-sort';
        });
        const currentHeader = document.querySelector(`.sortable[data-column="${column}"] i`);
        if (currentHeader) {
            currentHeader.className = this.currentSortDirection === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
        }
    }
    
    attachSortHandlers() {
        /**Attach click handlers to sortable table headers */
        // Use setTimeout to ensure headers exist after DOM render
        setTimeout(() => {
            document.querySelectorAll('.sortable').forEach(header => {
                header.addEventListener('click', (e) => {
                    const column = header.getAttribute('data-column');
                    if (column) {
                        this.sortUsersTable(column);
                    }
                });
            });
        }, 100);
    }
    
    async deleteUser(userId, username) {
        /**Soft delete a user (logical delete) */
        if (!confirm(`Are you sure you want to delete user "${username}"?\n\nThis will mark the user as deleted but preserve their data.`)) {
            return;
        }
        
        try {
            const response = await this.apiCall(`/api/admin/users/${userId}/delete`, 'POST');
            
            if (response.ok) {
                this.showNotification(`User "${username}" has been deleted`, 'success');
                // Reload users table
                await this.loadAdminData();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete user', 'error');
            }
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }
    
    async restoreUser(userId) {
        /**Restore a soft-deleted user */
        try {
            const response = await this.apiCall(`/api/admin/users/${userId}/restore`, 'POST');
            
            if (response.ok) {
                this.showNotification('User has been restored', 'success');
                // Reload users table
                await this.loadAdminData();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to restore user', 'error');
            }
        } catch (error) {
            console.error('Error restoring user:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async checkEmailVerification() {
        /**Check if email is verified and show banner if not */
        try {
            const response = await this.apiCall('/api/auth/check-verification', 'GET');
            if (response.ok) {
                const data = await response.json();
                console.log('Email verification status:', data.verified);
                
                const banner = document.getElementById('email-verification-banner');
                if (banner) {
                    if (!data.verified) {
                        // Show verification banner for unverified users
                        banner.style.display = 'block';
                        console.log('Showing verification banner - user not verified');
                    } else {
                        // Hide banner for verified users
                        banner.style.display = 'none';
                        console.log('Hiding verification banner - user is verified');
                    }
                }
            }
        } catch (error) {
            console.error('Error checking email verification:', error);
        }
    }

    showVerificationModal() {
        const modal = document.getElementById('verification-modal');
        if (modal) {
            modal.classList.add('active');
            document.getElementById('verification-code').focus();
        }
    }

    hideVerificationModal() {
        const modal = document.getElementById('verification-modal');
        if (modal) {
            modal.classList.remove('active');
            document.getElementById('verification-form').reset();
        }
    }

    async handleVerificationSubmit(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const code = formData.get('code');

        try {
            const response = await this.apiCall('/api/auth/verify-email', 'POST', { code });
            
            if (response.ok) {
                this.showNotification('Email verified successfully!', 'success');
                this.hideVerificationModal();
                
                // Hide verification banner
                const banner = document.getElementById('email-verification-banner');
                if (banner) {
                    banner.style.display = 'none';
                }
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Verification failed', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async resendVerificationCode() {
        try {
            const response = await this.apiCall('/api/auth/resend-verification', 'POST');
            
            if (response.ok) {
                this.showNotification('Verification code sent! Check your email.', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to send code', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async loadAdminChat(scrollToBottom = true) {
        /**Load admin chat messages */
        try {
            // Load messages
            const response = await this.apiCall('/api/admin-chat/messages', 'GET');
            if (response.ok) {
                const messages = await response.json();
                this.renderAdminMessages(messages, scrollToBottom);
            }
            
            // Check for unread messages
            this.checkUnreadAdminMessages();
            
            // Start auto-refresh for this chat
            this.startAdminChatAutoRefresh();
        } catch (error) {
            console.error('Error loading admin chat:', error);
        }
    }
    
    startAdminChatAutoRefresh() {
        /**Start auto-refreshing admin chat messages */
        // Clear any existing interval
        if (this.adminChatRefreshInterval) {
            clearInterval(this.adminChatRefreshInterval);
        }
        
        // Refresh every 5 seconds
        this.adminChatRefreshInterval = setInterval(async () => {
            try {
                const response = await this.apiCall('/api/admin-chat/messages', 'GET');
                if (response.ok) {
                    const messages = await response.json();
                    
                    // Check for new messages from admin
                    if (messages.length > this.lastAdminMessageCount) {
                        const newMessages = messages.slice(this.lastAdminMessageCount);
                        const adminMessages = newMessages.filter(msg => msg.sender_type === 'admin');
                        
                        if (adminMessages.length > 0) {
                            // Show notification for the most recent admin message
                            const lastAdminMsg = adminMessages[adminMessages.length - 1];
                            this.showMessageNotification('admin', lastAdminMsg.message);
                        }
                    }
                    
                    this.lastAdminMessageCount = messages.length;
                    this.renderAdminMessages(messages);
                }
                this.checkUnreadAdminMessages();
            } catch (error) {
                console.error('Error auto-refreshing admin chat:', error);
            }
        }, 5000);
    }
    
    stopAdminChatAutoRefresh() {
        /**Stop auto-refreshing admin chat messages */
        if (this.adminChatRefreshInterval) {
            clearInterval(this.adminChatRefreshInterval);
            this.adminChatRefreshInterval = null;
        }
    }
    
    renderAdminMessages(messages, scrollToBottom = false) {
        /**Render admin chat messages with file attachments */
        const container = document.getElementById('admin-chat-messages');
        
        if (messages.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999;">No messages yet. Start a conversation with the admin!</p>';
            return;
        }
        
        // Create hash of messages to detect actual changes
        const messagesHash = JSON.stringify(messages.map(m => ({ id: m.id, message: m.message, timestamp: m.timestamp })));
        
        // Skip re-render if content hasn't changed (prevents video interruption)
        if (messagesHash === this.lastAdminMessagesHash && !scrollToBottom) {
            return; // Content unchanged, skip re-render
        }
        this.lastAdminMessagesHash = messagesHash;
        
        // Save current scroll position
        const wasAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
        const savedScrollPos = container.scrollTop;
        
        container.innerHTML = messages.map(msg => {
            const timestamp = this.formatTimestamp(msg.timestamp);
            const isUser = msg.sender_type === 'user';
            
            // Render file attachment if present
            const fileHtml = (msg.file_url && window.fileUploadHandler) 
                ? window.fileUploadHandler.renderFileAttachment(msg.file_url, msg.file_name, msg.file_size)
                : '';
            
            // Render reply context if this is a reply
            const replyHtml = msg.reply_to ? `
                <div style="background: rgba(0,0,0,0.1); padding: 6px 8px; border-radius: 4px; margin-bottom: 8px; font-size: 0.85rem; border-left: 3px solid ${isUser ? 'rgba(255,255,255,0.5)' : '#667eea'};">
                    <i class="fas fa-reply" style="font-size: 10px; margin-right: 4px;"></i>
                    <strong>${msg.reply_to_sender === 'user' ? 'You' : 'Admin'}:</strong> ${(msg.reply_to_message || '').substring(0, 50)}${msg.reply_to_message && msg.reply_to_message.length > 50 ? '...' : ''}
                </div>
            ` : '';
            
            return `
                <div style="margin-bottom: 16px; display: flex; justify-content: ${isUser ? 'flex-end' : 'flex-start'};">
                    <div style="max-width: 70%; padding: 12px; border-radius: 12px; background: ${isUser ? '#667eea' : '#f1f3f4'}; color: ${isUser ? 'white' : '#333'}; position: relative; padding-right: 75px;">
                        ${replyHtml}
                        ${msg.message ? `<div>${msg.message}</div>` : ''}
                        ${fileHtml}
                        <div style="font-size: 0.75rem; opacity: 0.7; margin-top: 4px; text-align: right;">${timestamp}</div>
                        <button onclick="app.setReplyTo(${msg.id}, '${(msg.message || 'File attachment').replace(/'/g, "\\'")}', '${msg.sender_type}')" 
                                style="position: absolute; top: 8px; right: 36px; background: rgba(255,255,255,0.2); border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center; color: ${isUser ? 'white' : '#666'}; transition: background 0.2s;"
                                onmouseover="this.style.background='rgba(103,126,234,0.8)'; this.style.color='white';"
                                onmouseout="this.style.background='rgba(255,255,255,0.2)'; this.style.color='${isUser ? 'white' : '#666'}';"
                                title="Reply to this message">
                            <i class="fas fa-reply" style="font-size: 10px;"></i>
                        </button>
                        <button onclick="app.deleteAdminMessage(${msg.id})" 
                                style="position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.2); border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center; color: ${isUser ? 'white' : '#666'}; transition: background 0.2s;"
                                onmouseover="this.style.background='rgba(255,71,87,0.8)'; this.style.color='white';"
                                onmouseout="this.style.background='rgba(255,255,255,0.2)'; this.style.color='${isUser ? 'white' : '#666'}';"
                                title="Delete message">
                            <i class="fas fa-trash" style="font-size: 10px;"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        // Restore scroll position or scroll to bottom
        if (scrollToBottom || wasAtBottom) {
            // If explicitly requested or user was at bottom, scroll to bottom
            container.scrollTop = container.scrollHeight;
        } else {
            // Preserve scroll position during auto-refresh
            container.scrollTop = savedScrollPos;
        }
    }
    
    async sendAdminMessage() {
        /**Send a message to admin */
        const input = document.getElementById('admin-chat-input');
        const message = input.value.trim();
        
        // Check if there's an uploaded file
        const uploadedFileData = window.fileUploadHandler ? window.fileUploadHandler.getUploadedFileData('admin-chat') : null;
        console.log('Sending admin message - message:', message, 'uploadedFileData:', uploadedFileData);
        
        if (!message && !uploadedFileData) {
            this.showNotification('Please type a message or attach a file', 'error');
            return;
        }
        
        try {
            const payload = { message: message || '' };
            
            // If file is uploaded, add file data
            if (uploadedFileData) {
                payload.file_url = uploadedFileData.file_url;
                payload.file_name = uploadedFileData.original_filename;
                payload.file_size = uploadedFileData.file_size;
            }
            
            // If replying to a message, add reply_to
            if (this.replyingTo) {
                payload.reply_to = this.replyingTo;
            }
            
            const response = await this.apiCall('/api/admin-chat/send', 'POST', payload);
            
            if (response.ok) {
                input.value = '';
                // Clear attached file
                if (window.fileUploadHandler) {
                    window.fileUploadHandler.clearAttachedFile('admin-chat');
                }
                // Clear reply
                this.cancelReply();
                // Reload messages
                await this.loadAdminChat();
                this.showNotification('Message sent to admin', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to send message', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }
    
    async checkUnreadAdminMessages() {
        /**Check for unread messages from admin */
        try {
            const response = await this.apiCall('/api/admin-chat/unread-count', 'GET');
            if (response.ok) {
                const data = await response.json();
                const badge = document.getElementById('admin-chat-badge');
                if (badge) {
                    if (data.count > 0) {
                        badge.textContent = data.count;
                        badge.style.display = 'inline-block';
                    } else {
                        badge.style.display = 'none';
                    }
                }
            }
        } catch (error) {
            console.error('Error checking unread messages:', error);
        }
    }
    
    // Admin Chat Management Methods
    async loadAdminChatsList() {
        /**Load list of users with admin messages (admin view) */
        try {
            const response = await this.apiCall('/api/admin/chats', 'GET');
            if (response.ok) {
                const chats = await response.json();
                this.renderAdminChatsList(chats);
            }
        } catch (error) {
            console.error('Error loading admin chats:', error);
        }
    }
    
    renderAdminChatsList(chats) {
        /**Render list of users with messages */
        const container = document.getElementById('admin-chat-users-list');
        
        if (chats.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999; padding: 16px;">No user messages yet</p>';
            return;
        }
        
        container.innerHTML = chats.map(chat => {
            const lastMessage = chat.last_message ? this.formatTimestamp(chat.last_message) : 'No messages';
            const unreadBadge = chat.unread_count > 0 ? `<span class="badge">${chat.unread_count}</span>` : '';
            
            return `
                <div class="admin-chat-user-item" data-user-id="${chat.user_id}" style="padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; margin-bottom: 4px;">${chat.username}</div>
                        <div style="font-size: 0.85rem; color: #666;">${lastMessage}</div>
                    </div>
                    ${unreadBadge}
                </div>
            `;
        }).join('');
        
        // Add click handlers
        container.querySelectorAll('.admin-chat-user-item').forEach(item => {
            item.addEventListener('click', () => {
                const userId = parseInt(item.dataset.userId);
                const username = item.querySelector('div').textContent;
                this.viewAdminUserChat(userId, username);
            });
        });
    }
    
    async viewAdminUserChat(userId, username) {
        /**View messages for a specific user */
        this.currentAdminChatUserId = userId;
        
        try {
            const response = await this.apiCall(`/api/admin/chats/${userId}/messages`, 'GET');
            if (response.ok) {
                const messages = await response.json();
                this.renderAdminUserMessages(messages, username, true);
                
                // Show reply box
                document.getElementById('admin-chat-reply-box').style.display = 'block';
                
                // Update header
                document.getElementById('admin-chat-header').innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-user-circle" style="font-size: 24px;"></i>
                        <div>
                            <div style="font-weight: 600;">${username}</div>
                            <div style="font-size: 0.85rem; color: #666;">User ID: ${userId}</div>
                        </div>
                    </div>
                `;
                
                // Reload chats list to update unread counts
                await this.loadAdminChatsList();
                
                // Start auto-refresh for this conversation
                this.startAdminUserChatAutoRefresh(userId, username);
            }
        } catch (error) {
            console.error('Error loading user messages:', error);
            this.showNotification('Failed to load messages', 'error');
        }
    }
    
    startAdminUserChatAutoRefresh(userId, username) {
        /**Start auto-refreshing admin view of user chat */
        // Clear any existing interval
        if (this.adminUserChatRefreshInterval) {
            clearInterval(this.adminUserChatRefreshInterval);
        }
        
        // Refresh every 3 seconds
        this.adminUserChatRefreshInterval = setInterval(async () => {
            try {
                const response = await this.apiCall(`/api/admin/chats/${userId}/messages`, 'GET');
                if (response.ok) {
                    const messages = await response.json();
                    
                    // Check for new messages from user (admin view)
                    if (messages.length > this.lastUserMessageCount) {
                        const newMessages = messages.slice(this.lastUserMessageCount);
                        const userMessages = newMessages.filter(msg => msg.sender_type === 'user');
                        
                        if (userMessages.length > 0) {
                            // Show notification for the most recent user message
                            const lastUserMsg = userMessages[userMessages.length - 1];
                            this.showMessageNotification('user', lastUserMsg.message, username);
                        }
                    }
                    
                    this.lastUserMessageCount = messages.length;
                    this.renderAdminUserMessages(messages, username);
                }
                await this.loadAdminChatsList();
            } catch (error) {
                console.error('Error auto-refreshing admin user chat:', error);
            }
        }, 3000);
    }
    
    stopAdminUserChatAutoRefresh() {
        /**Stop auto-refreshing admin user chat */
        if (this.adminUserChatRefreshInterval) {
            clearInterval(this.adminUserChatRefreshInterval);
            this.adminUserChatRefreshInterval = null;
        }
    }
    
    renderAdminUserMessages(messages, username, scrollToBottom = false) {
        /**Render messages for admin view with file attachments */
        const container = document.getElementById('admin-chat-messages-view');
        
        if (messages.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #999;">No messages yet</p>';
            return;
        }
        
        // Create hash of messages to detect actual changes
        const messagesHash = JSON.stringify(messages.map(m => ({ id: m.id, message: m.message, timestamp: m.timestamp })));
        
        // Skip re-render if content hasn't changed (prevents video interruption)
        if (messagesHash === this.lastUserMessagesHash && !scrollToBottom) {
            return; // Content unchanged, skip re-render
        }
        this.lastUserMessagesHash = messagesHash;
        
        // Save current scroll position
        const wasAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 50;
        const savedScrollPos = container.scrollTop;
        
        container.innerHTML = messages.map(msg => {
            const timestamp = this.formatTimestamp(msg.timestamp);
            const isAdmin = msg.sender_type === 'admin';
            
            // Render file attachment if present
            const fileHtml = (msg.file_url && window.fileUploadHandler) 
                ? window.fileUploadHandler.renderFileAttachment(msg.file_url, msg.file_name, msg.file_size)
                : '';
            
            // Render reply context if this is a reply
            const replyHtml = msg.reply_to ? `
                <div style="background: rgba(0,0,0,0.1); padding: 6px 8px; border-radius: 4px; margin-bottom: 8px; font-size: 0.85rem; border-left: 3px solid ${isAdmin ? 'rgba(255,255,255,0.5)' : '#667eea'};">
                    <i class="fas fa-reply" style="font-size: 10px; margin-right: 4px;"></i>
                    <strong>${msg.reply_to_sender === 'admin' ? 'Admin' : username}:</strong> ${(msg.reply_to_message || '').substring(0, 50)}${msg.reply_to_message && msg.reply_to_message.length > 50 ? '...' : ''}
                </div>
            ` : '';
            
            return `
                <div style="margin-bottom: 16px; display: flex; justify-content: ${isAdmin ? 'flex-end' : 'flex-start'};">
                    <div style="max-width: 70%; padding: 12px; border-radius: 12px; background: ${isAdmin ? '#667eea' : '#f1f3f4'}; color: ${isAdmin ? 'white' : '#333'}; position: relative; padding-right: 75px;">
                        <div style="font-size: 0.85rem; opacity: 0.8; margin-bottom: 4px;">${isAdmin ? 'You (Admin)' : username}</div>
                        ${replyHtml}
                        ${msg.message ? `<div>${msg.message}</div>` : ''}
                        ${fileHtml}
                        <div style="font-size: 0.75rem; opacity: 0.7; margin-top: 4px; text-align: right;">${timestamp}</div>
                        <button onclick="app.setReplyTo(${msg.id}, '${(msg.message || 'File attachment').replace(/'/g, "\\'")}', '${msg.sender_type}')" 
                                style="position: absolute; top: 8px; right: 36px; background: rgba(255,255,255,0.2); border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center; color: ${isAdmin ? 'white' : '#666'}; transition: background 0.2s;"
                                onmouseover="this.style.background='rgba(103,126,234,0.8)'; this.style.color='white';"
                                onmouseout="this.style.background='rgba(255,255,255,0.2)'; this.style.color='${isAdmin ? 'white' : '#666'}';"
                                title="Reply to this message">
                            <i class="fas fa-reply" style="font-size: 10px;"></i>
                        </button>
                        <button onclick="app.deleteAdminMessage(${msg.id})" 
                                style="position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.2); border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer; display: flex; align-items: center; justify-content: center; color: ${isAdmin ? 'white' : '#666'}; transition: background 0.2s;"
                                onmouseover="this.style.background='rgba(255,71,87,0.8)'; this.style.color='white';"
                                onmouseout="this.style.background='rgba(255,255,255,0.2)'; this.style.color='${isAdmin ? 'white' : '#666'}';"
                                title="Delete message">
                            <i class="fas fa-trash" style="font-size: 10px;"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        // Restore scroll position or scroll to bottom
        if (scrollToBottom || wasAtBottom) {
            // If explicitly requested or user was at bottom, scroll to bottom
            container.scrollTop = container.scrollHeight;
        } else {
            // Preserve scroll position during auto-refresh
            container.scrollTop = savedScrollPos;
        }
    }
    
    async sendAdminReply() {
        /**Send a reply to user as admin */
        if (!this.currentAdminChatUserId) {
            this.showNotification('Please select a user first', 'error');
            return;
        }
        
        const input = document.getElementById('admin-reply-input');
        const message = input.value.trim();
        
        // Check if there's an uploaded file
        const uploadedFileData = window.fileUploadHandler ? window.fileUploadHandler.getUploadedFileData('admin-reply') : null;
        
        if (!message && !uploadedFileData) {
            this.showNotification('Please type a message or attach a file', 'error');
            return;
        }
        
        try {
            const payload = { message: message || '' };
            
            // If file is uploaded, add file data
            if (uploadedFileData) {
                payload.file_url = uploadedFileData.file_url;
                payload.file_name = uploadedFileData.original_filename;
                payload.file_size = uploadedFileData.file_size;
            }
            
            // If replying to a message, add reply_to
            if (this.replyingTo) {
                payload.reply_to = this.replyingTo;
            }
            
            const response = await this.apiCall(`/api/admin/chats/${this.currentAdminChatUserId}/send`, 'POST', payload);
            
            if (response.ok) {
                input.value = '';
                // Clear attached file
                if (window.fileUploadHandler) {
                    window.fileUploadHandler.clearAttachedFile('admin-reply');
                }
                // Clear reply
                this.cancelReply();
                // Reload messages
                const header = document.getElementById('admin-chat-header');
                const username = header.querySelector('div > div').textContent;
                await this.viewAdminUserChat(this.currentAdminChatUserId, username);
                this.showNotification('Reply sent', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to send reply', 'error');
            }
        } catch (error) {
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    async deleteAdminMessage(messageId) {
        /**Delete an admin chat message */
        if (!confirm('Are you sure you want to delete this message?')) {
            return;
        }
        
        try {
            const response = await this.apiCall(`/api/admin-chat/message/${messageId}`, 'DELETE');
            
            if (response.ok) {
                this.showNotification('Message deleted', 'success');
                // Reload messages based on current context
                if (this.currentAdminChatUserId) {
                    // Admin viewing user chat
                    const header = document.getElementById('admin-chat-header');
                    const username = header.querySelector('div > div').textContent;
                    await this.viewAdminUserChat(this.currentAdminChatUserId, username);
                } else {
                    // User viewing admin chat
                    await this.loadAdminChat();
                }
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete message', 'error');
            }
        } catch (error) {
            console.error('Error deleting message:', error);
            this.showNotification('Network error. Please try again.', 'error');
        }
    }

    setReplyTo(messageId, messageText, senderType) {
        /**Set a message to reply to */
        this.replyingTo = messageId;
        this.replyingToContext = {
            message: messageText,
            sender: senderType
        };
        
        // Show reply indicator
        const indicator = document.getElementById('admin-reply-indicator') || document.getElementById('admin-chat-reply-indicator');
        if (indicator) {
            const preview = indicator.querySelector('.reply-preview');
            const senderName = senderType === 'admin' ? 'Admin' : 'User';
            if (preview) {
                preview.textContent = `${senderName}: ${messageText.substring(0, 60)}${messageText.length > 60 ? '...' : ''}`;
            }
            indicator.style.display = 'flex';
        }
    }

    cancelReply() {
        /**Cancel replying to a message */
        this.replyingTo = null;
        this.replyingToContext = null;
        
        // Hide reply indicators
        const indicators = document.querySelectorAll('[id$="-reply-indicator"]');
        indicators.forEach(indicator => {
            indicator.style.display = 'none';
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 4000);
    }

    showMessageNotification(senderType, message, username = null) {
        /**Show a notification for new message in top-right corner */
        const notification = document.getElementById('message-notification');
        const senderEl = notification.querySelector('.notification-sender');
        const messageEl = notification.querySelector('.notification-message');
        
        // Set sender name
        if (senderType === 'admin') {
            senderEl.textContent = 'New message from Admin';
            notification.className = 'message-notification admin-msg';
        } else {
            senderEl.textContent = username ? `New message from ${username}` : 'New message from User';
            notification.className = 'message-notification user-msg';
        }
        
        // Set message preview (max 100 chars)
        messageEl.textContent = message ? message.substring(0, 100) + (message.length > 100 ? '...' : '') : 'File attachment';
        
        // Show notification
        notification.style.display = 'block';
        
        // Clear any existing timeout
        if (this.notificationTimeout) {
            clearTimeout(this.notificationTimeout);
        }
        
        // Auto-dismiss after 10 seconds
        this.notificationTimeout = setTimeout(() => {
            this.closeMessageNotification();
        }, 10000);
    }

    closeMessageNotification() {
        /**Close the message notification */
        const notification = document.getElementById('message-notification');
        notification.classList.add('closing');
        
        setTimeout(() => {
            notification.style.display = 'none';
            notification.classList.remove('closing');
        }, 300); // Match animation duration
        
        if (this.notificationTimeout) {
            clearTimeout(this.notificationTimeout);
            this.notificationTimeout = null;
        }
    }
}

// App is initialized in multi_user.html to make it globally accessible
// DO NOT instantiate here - it would create duplicate event listeners
