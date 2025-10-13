// Universal redirect script for GitHub Pages
(function() {
    // Extract invite code from URL
    function getInviteCode() {
        const pathParts = window.location.pathname.split('/');
        const inviteCode = pathParts[pathParts.length - 1];
        
        // If no invite code in path, try to get from query parameter
        if (!inviteCode || inviteCode === 'redirect.js') {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('code') || 'UNKNOWN';
        }
        
        return inviteCode;
    }
    
    // Try to open the app
    function tryOpenApp() {
        const inviteCode = getInviteCode();
        const appScheme = `habitstreaks://join/group/${inviteCode}`;
        
        // Track if the page loses focus (app opened)
        let pageHidden = false;
        let timeoutId;
        
        // Listen for page visibility change
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                pageHidden = true;
                clearTimeout(timeoutId);
            }
        });
        
        // Listen for page blur (app might have opened)
        window.addEventListener('blur', function() {
            pageHidden = true;
            clearTimeout(timeoutId);
        });
        
        // Create a hidden iframe to try opening the app
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = appScheme;
        document.body.appendChild(iframe);
        
        // Set a timeout to show fallback if app doesn't open
        timeoutId = setTimeout(() => {
            if (!pageHidden) {
                // App didn't open, show fallback
                iframe.remove();
                showFallback();
            }
        }, 2000);
    }
    
    // Show fallback page
    function showFallback() {
        const inviteCode = getInviteCode();
        
        // Create fallback content
        const fallbackHTML = `
            <div class="container">
                <div class="logo">🏃‍♂️</div>
                <h1>Join Group Challenge</h1>
                <p class="subtitle">Download Habit Streaks to join this group challenge and build better habits together!</p>
                
                <div class="invite-code">
                    <div class="invite-code-label">Group Invite Code</div>
                    <div class="invite-code-value">${inviteCode}</div>
                </div>
                
                <div class="app-buttons">
                    <a href="https://play.google.com/store/apps/details?id=com.bashtech.habittracker" class="app-button android-button">
                        📱 Download for Android
                    </a>
                </div>
                
                <a href="https://www.bashtech.info/habit_streaks/" class="redirect-button">
                    🌐 Visit App Page
                </a>
                
                <div class="instructions">
                    <strong>How to join:</strong><br>
                    1. Download the app using the button above<br>
                    2. Open the app and sign up<br>
                    3. Go to "Group Challenges" and tap "Join Group"<br>
                    4. Enter the invite code: <strong>${inviteCode}</strong>
                </div>
            </div>
        `;
        
        // Replace the loading content
        document.body.innerHTML = fallbackHTML;
    }
    
    // Initialize
    tryOpenApp();
})();
