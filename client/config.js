// API Configuration - Auto-detects local vs production
const CONFIG = {
    // If running locally, use localhost, otherwise use relative path
    API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000'
        : '',  // Empty string means same origin (relative URLs)
    
    WS_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'ws://localhost:8000'
        : `wss://${window.location.host}`  // Use secure WebSocket in production
};

// Export for use in other scripts
window.CONFIG = CONFIG;
