/**
 * JWT Authentication Helper
 * Automatically adds JWT Bearer token to all AJAX requests
 */

// Get JWT token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Get access token
function getAccessToken() {
    return getCookie('access_token');
}

// Get CSRF token
function getCSRFToken() {
    return getCookie('csrftoken');
}

// Setup fetch to include JWT token
const originalFetch = window.fetch;
window.fetch = function(...args) {
    let [resource, config] = args;
    
    // Initialize config if not provided
    if (!config) {
        config = {};
    }
    
    // Initialize headers if not provided
    if (!config.headers) {
        config.headers = {};
    }
    
    // Add JWT token if available
    const token = getAccessToken();
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add CSRF token for POST, PUT, PATCH, DELETE
    const method = config.method ? config.method.toUpperCase() : 'GET';
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }
    }
    
    return originalFetch(resource, config);
};

// Setup XMLHttpRequest to include JWT token
(function() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;
    
    XMLHttpRequest.prototype.open = function(method, url, ...rest) {
        this._method = method;
        this._url = url;
        return originalOpen.call(this, method, url, ...rest);
    };
    
    XMLHttpRequest.prototype.send = function(...args) {
        // Add JWT token
        const token = getAccessToken();
        if (token) {
            this.setRequestHeader('Authorization', `Bearer ${token}`);
        }
        
        // Add CSRF token for POST, PUT, PATCH, DELETE
        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(this._method.toUpperCase())) {
            const csrfToken = getCSRFToken();
            if (csrfToken) {
                this.setRequestHeader('X-CSRFToken', csrfToken);
            }
        }
        
        return originalSend.apply(this, args);
    };
})();

// Log token info on page load (for debugging)
document.addEventListener('DOMContentLoaded', function() {
    const token = getAccessToken();
    if (token) {
        console.log('✅ JWT Access Token found in cookie');
        console.log('📝 Token will be sent as: Authorization: Bearer ' + token.substring(0, 20) + '...');
        
        // Decode JWT payload (just for display, not verification)
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            console.log('👤 Token user_id:', payload.user_id);
            console.log('⏰ Token expires:', new Date(payload.exp * 1000).toLocaleString());
        } catch (e) {
            console.log('❌ Could not decode token');
        }
    } else {
        console.log('ℹ️ No JWT token found (user not logged in)');
    }
});
