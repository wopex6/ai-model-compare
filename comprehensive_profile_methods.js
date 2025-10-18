// Comprehensive Profile Methods for Multi-User App

// Add these methods to the IntegratedAIChatbot class

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
    document.getElementById('personal-name').value = personalInfo.name || '';
    document.getElementById('personal-email').value = personalInfo.email || '';
    document.getElementById('personal-age').value = personalInfo.age || '';
    document.getElementById('personal-location').value = personalInfo.location || '';
    document.getElementById('personal-occupation').value = personalInfo.occupation || '';
    document.getElementById('personal-interests').value = Array.isArray(personalInfo.interests) ? personalInfo.interests.join(', ') : '';
    document.getElementById('personal-bio').value = personalInfo.bio || '';
}

loadPreferences(preferences) {
    document.getElementById('pref-communication-style').value = preferences.communication_style || 'friendly';
    document.getElementById('pref-language').value = preferences.language_preference || 'en';
    document.getElementById('pref-personality-type').value = preferences.personality_type || '';
    document.getElementById('pref-learning-style').value = preferences.learning_style || 'mixed';
    document.getElementById('pref-topics').value = Array.isArray(preferences.topics_of_interest) ? preferences.topics_of_interest.join(', ') : '';
    document.getElementById('pref-goals').value = Array.isArray(preferences.goals) ? preferences.goals.join(', ') : '';
}

loadPrivacySettings(privacySettings) {
    document.getElementById('privacy-data-sharing').checked = privacySettings.data_sharing || false;
    document.getElementById('privacy-analytics').checked = privacySettings.analytics || false;
    document.getElementById('privacy-personalization').checked = privacySettings.personalization || false;
    document.getElementById('privacy-marketing').checked = privacySettings.marketing || false;
}

updateProfileCompletion(percentage) {
    document.getElementById('profile-completion-text').textContent = `Profile: ${percentage}% Complete`;
}

switchProfilePage(page) {
    // Update navigation
    document.querySelectorAll('.profile-nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // Update pages
    document.querySelectorAll('.profile-page').forEach(page => page.classList.remove('active'));
    document.getElementById(`profile-page-${page}`).classList.add('active');
}

async handlePersonalInfoUpdate(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const personalInfo = Object.fromEntries(formData);
    
    // Convert interests to array
    if (personalInfo.interests) {
        personalInfo.interests = personalInfo.interests.split(',').map(s => s.trim()).filter(s => s);
    }
    
    try {
        const response = await this.apiCall('/api/user/comprehensive-profile/personal', 'PUT', personalInfo);
        const result = await response.json();
        
        if (result.success) {
            this.showNotification('Personal information updated successfully!', 'success');
            this.loadProfile(); // Reload to update completion percentage
        } else {
            this.showNotification('Failed to update personal information', 'error');
        }
    } catch (error) {
        this.showNotification('Error updating personal information', 'error');
    }
}

async handlePreferencesUpdate(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const preferences = Object.fromEntries(formData);
    
    // Convert arrays
    if (preferences.topics_of_interest) {
        preferences.topics_of_interest = preferences.topics_of_interest.split(',').map(s => s.trim()).filter(s => s);
    }
    if (preferences.goals) {
        preferences.goals = preferences.goals.split(',').map(s => s.trim()).filter(s => s);
    }
    
    try {
        const response = await this.apiCall('/api/user/comprehensive-profile/preferences', 'PUT', preferences);
        const result = await response.json();
        
        if (result.success) {
            this.showNotification('Preferences updated successfully!', 'success');
            this.loadProfile();
        } else {
            this.showNotification('Failed to update preferences', 'error');
        }
    } catch (error) {
        this.showNotification('Error updating preferences', 'error');
    }
}

async handlePrivacyUpdate(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const privacySettings = {};
    
    // Handle checkboxes
    privacySettings.data_sharing = formData.has('data_sharing');
    privacySettings.analytics = formData.has('analytics');
    privacySettings.personalization = formData.has('personalization');
    privacySettings.marketing = formData.has('marketing');
    
    try {
        const response = await this.apiCall('/api/user/comprehensive-profile/privacy', 'PUT', privacySettings);
        const result = await response.json();
        
        if (result.success) {
            this.showNotification('Privacy settings updated successfully!', 'success');
        } else {
            this.showNotification('Failed to update privacy settings', 'error');
        }
    } catch (error) {
        this.showNotification('Error updating privacy settings', 'error');
    }
}
