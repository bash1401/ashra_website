// Extract invite code from URL path
function getInviteCode() {
    const pathParts = window.location.pathname.split('/');
    const inviteCode = pathParts[pathParts.length - 1];
    
    // If no invite code in path, try to get from query parameter
    if (!inviteCode || inviteCode === 'handler.js') {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('code') || urlParams.get('invite') || 'UNKNOWN';
    }
    
    return inviteCode;
}

// Redirect to the main page with the invite code
function redirectToMainPage() {
    const inviteCode = getInviteCode();
    const mainPageUrl = `https://www.bashtech.info/habitstreaks/join/group/index.html?code=${inviteCode}`;
    console.log('🔄 Redirecting to:', mainPageUrl);
    window.location.href = mainPageUrl;
}

// Redirect immediately
redirectToMainPage();