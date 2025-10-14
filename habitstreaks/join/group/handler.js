// Universal deep link handler for GitHub Pages
// This script will be included in all pages to handle deep linking

(function() {
    'use strict';
    
    // Extract invite code from URL
    function getInviteCode() {
        const pathParts = window.location.pathname.split('/');
        const inviteCode = pathParts[pathParts.length - 1];
        
        // If no invite code in path, try to get from query parameter
        if (!inviteCode || inviteCode === 'handler.js') {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('code') || 'UNKNOWN';
        }
        
        return inviteCode;
    }
    
    // Check if we're on a deep link page
    function isDeepLinkPage() {
        return window.location.pathname.includes('/habitstreaks/join/group/');
    }
    
    // Redirect to the main page if needed
    function redirectToMainPage() {
        if (isDeepLinkPage()) {
            const inviteCode = getInviteCode();
            const mainPageUrl = `https://www.bashtech.info/habitstreaks/join/group/universal.html?code=${inviteCode}`;
            window.location.href = mainPageUrl;
        }
    }
    
    // Auto-redirect if this is a deep link page
    if (isDeepLinkPage()) {
        redirectToMainPage();
    }
})();
