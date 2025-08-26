<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatBot UI - SAMNEX AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .demo-content {
            text-align: center;
            color: white;
            padding: 50px 20px;
        }

        .demo-content h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
        }

        .demo-content p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        /* Chat Widget Styles */
        .chat-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
        }

        .chat-bubble {
            position: relative;
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(255, 107, 53, 0.4);
            transition: all 0.3s ease;
            animation: pulse 2s infinite;
        }

        .chat-bubble:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(255, 107, 53, 0.6);
        }

        .chat-bubble svg {
            width: 28px;
            height: 28px;
            fill: white;
        }

        .notification-badge {
            position: absolute;
            top: -2px;
            right: -2px;
            background: #e74c3c;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            font-size: 12px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid white;
        }

        @keyframes pulse {
            0% { box-shadow: 0 4px 20px rgba(255, 107, 53, 0.4); }
            50% { box-shadow: 0 4px 20px rgba(255, 107, 53, 0.8); }
            100% { box-shadow: 0 4px 20px rgba(255, 107, 53, 0.4); }
        }

        /* Chat Window */
        .chat-window {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 380px;
            height: 500px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            display: none;
            flex-direction: column;
            overflow: hidden;
            z-index: 9999;
            animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .chat-header {
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            padding: 20px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
        }

        .chat-header-info {
            display: flex;
            align-items: center;
        }

        .chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
        }

        .chat-header-text h3 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 2px;
        }

        .chat-header-text p {
            font-size: 12px;
            opacity: 0.9;
        }

        .close-chat {
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .close-chat:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
            max-height: 300px;
            display: flex;
            flex-direction: column;
        }

        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }

        .message.user {
            justify-content: flex-end;
        }

        .message-content {
            max-width: 280px;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            word-wrap: break-word;
        }

        .message.bot .message-content {
            background: white;
            border: 1px solid #e1e8ed;
            color: #333;
            border-bottom-left-radius: 8px;
        }

        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 8px;
        }

        .message-time {
            font-size: 11px;
            color: #999;
            margin-top: 5px;
            text-align: right;
        }

        .message.bot .message-time {
            text-align: left;
        }

        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 18px;
            border-bottom-left-radius: 8px;
            max-width: 60px;
            margin-bottom: 15px;
        }

        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
            animation: typing 1.4s infinite;
        }

        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
                opacity: 0.5;
            }
            30% {
                transform: translateY(-10px);
                opacity: 1;
            }
        }

        .chat-input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e1e8ed;
        }

        .suggested-questions {
            margin-bottom: 15px;
        }

        .suggested-questions p {
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .suggestion-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 10px;
        }

        .suggestion-btn {
            background: #f1f3f4;
            border: none;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 12px;
            color: #5f6368;
            cursor: pointer;
            transition: all 0.2s;
        }

        .suggestion-btn:hover {
            background: #e8eaed;
            transform: translateY(-1px);
        }

        .chat-input-form {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #e1e8ed;
            border-radius: 24px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: #ff6b35;
        }

        .send-btn {
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }

        .send-btn:hover:not(:disabled) {
            transform: scale(1.05);
        }

        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .send-btn svg {
            width: 16px;
            height: 16px;
            fill: white;
        }

        .status-indicator {
            padding: 8px 16px;
            margin: 10px 0;
            border-radius: 8px;
            font-size: 12px;
            text-align: center;
        }

        .status-indicator.error {
            background: #ffe6e6;
            color: #c53030;
            border: 1px solid #feb2b2;
        }

        .status-indicator.success {
            background: #e6fffa;
            color: #2d7d72;
            border: 1px solid #81e6d9;
        }

        .status-indicator.info {
            background: #e6f3ff;
            color: #2563eb;
            border: 1px solid #93c5fd;
        }

        .quick-actions {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }

        .quick-action-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 8px 12px;
            border-radius: 16px;
            font-size: 11px;
            color: white;
            cursor: pointer;
            transition: all 0.2s;
        }

        .quick-action-btn:hover {
            transform: translateY(-1px);
            opacity: 0.9;
        }

        .connection-status {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #e74c3c;
            transition: background-color 0.3s;
        }

        .connection-status.connected {
            background: #27ae60;
        }

        .debug-info {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            max-width: 300px;
            display: none;
            z-index: 10001;
        }

        /* Responsive Design */
        @media (max-width: 480px) {
            .chat-window {
                right: 10px;
                left: 10px;
                width: auto;
                bottom: 80px;
            }
        }
    </style>
</head>
<body>
    <!-- Demo Content -->
    <div class="demo-content">
        <h1>SAMNEX AI Demo Page</h1>
        <p>Your FastAPI chatbot is ready! Click the orange chat bubble to start a conversation.</p>
        <br>
        <p style="font-size: 1em; opacity: 0.7;">This demo page shows how the chatbot widget integrates with your website.</p>
    </div>

    <!-- Debug Info -->
    <div class="debug-info" id="debugInfo">
        <div>Connection: <span id="debugConnection">Unknown</span></div>
        <div>Session: <span id="debugSession">None</span></div>
        <div>API URL: <span id="debugApi">Loading...</span></div>
        <div>Last Error: <span id="debugError">None</span></div>
    </div>

    <!-- Chat Widget -->
    <div class="chat-widget">
        <div class="chat-bubble" id="chatBubble">
            <svg viewBox="0 0 24 24">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
            </svg>
            <div class="notification-badge" id="notificationBadge" style="display: none;">0</div>
        </div>

        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <div class="chat-header-info">
                    <div class="chat-avatar">
                        <svg width="20" height="20" fill="white" viewBox="0 0 24 24">
                            <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V21C3 22.11 3.89 23 5 23H19C20.11 23 21 22.11 21 21V11L19 9H21ZM7 5H13V9H7V5Z"/>
                        </svg>
                    </div>
                    <div class="chat-header-text">
                        <h3>SAMNEX Assistant</h3>
                        <p id="connectionStatus">Connecting...</p>
                    </div>
                </div>
                <button class="close-chat" id="closeChat">&times;</button>
                <div class="connection-status" id="connectionIndicator"></div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="typing-indicator" id="typingIndicator">
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>

            <div class="chat-input-area">
                <div class="suggested-questions">
                    <p>Quick suggestions:</p>
                    <div class="suggestion-buttons" id="suggestionButtons">
                        <button class="suggestion-btn">What schemes are available?</button>
                        <button class="suggestion-btn">How to apply?</button>
                        <button class="suggestion-btn">Eligibility criteria?</button>
                    </div>
                    <div class="quick-actions">
                        <button class="quick-action-btn" id="clearChat">Clear Chat</button>
                        <button class="quick-action-btn" id="newSession">New Session</button>
                        <button class="quick-action-btn" id="toggleDebug">Debug</button>
                    </div>
                </div>

                <form class="chat-input-form" id="chatForm">
                    <input type="text" 
                           class="chat-input" 
                           id="messageInput" 
                           placeholder="Ask your query here" 
                           maxlength="500"
                           autocomplete="off">
                    <button type="submit" class="send-btn" id="sendBtn">
                        <svg viewBox="0 0 24 24">
                            <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/>
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    </div>

    <script>
        // Configuration
        const CONFIG = {
            API_BASE_URL: 'http://localhost:8000',
            SESSION_ID: generateSessionId(),
            MAX_RETRIES: 3,
            RETRY_DELAY: 2000,
            CONNECTION_CHECK_INTERVAL: 30000,
            DEBUG: false
        };

        // DOM Elements
        const elements = {
            chatBubble: document.getElementById('chatBubble'),
            chatWindow: document.getElementById('chatWindow'),
            closeChat: document.getElementById('closeChat'),
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            chatForm: document.getElementById('chatForm'),
            typingIndicator: document.getElementById('typingIndicator'),
            notificationBadge: document.getElementById('notificationBadge'),
            clearChatBtn: document.getElementById('clearChat'),
            newSessionBtn: document.getElementById('newSession'),
            toggleDebugBtn: document.getElementById('toggleDebug'),
            connectionStatus: document.getElementById('connectionStatus'),
            connectionIndicator: document.getElementById('connectionIndicator'),
            suggestionButtons: document.getElementById('suggestionButtons'),
            debugInfo: document.getElementById('debugInfo'),
            debugConnection: document.getElementById('debugConnection'),
            debugSession: document.getElementById('debugSession'),
            debugApi: document.getElementById('debugApi'),
            debugError: document.getElementById('debugError')
        };

        // State
        let isWindowOpen = false;
        let isTyping = false;
        let messageCount = 0;
        let isConnected = false;
        let isSending = false;
        let connectionCheckInterval;

        // Utility Functions
        function generateSessionId() {
            const adjectives = ["sharp", "sleepy", "fluffy", "dazzling", "crazy", "bold", "happy", "silly"];
            const animals = ["lion", "swan", "tiger", "elephant", "zebra", "giraffe", "panda", "koala"];
            const randomAdjective = adjectives[Math.floor(Math.random() * adjectives.length)];
            const randomAnimal = animals[Math.floor(Math.random() * animals.length)];
            const randomNumber = Math.floor(Math.random() * 1000);
            return `${randomAdjective}_${randomAnimal}_${randomNumber}_${Date.now()}`;
        }

        function getCurrentTime() {
            return new Date().toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true 
            });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function updateDebugInfo() {
            if (!CONFIG.DEBUG) return;
            
            elements.debugConnection.textContent = isConnected ? 'Connected' : 'Disconnected';
            elements.debugSession.textContent = CONFIG.SESSION_ID.substring(0, 20) + '...';
            elements.debugApi.textContent = CONFIG.API_BASE_URL;
        }

        function logError(error, context = '') {
            console.error(`[ChatBot Error${context ? ' - ' + context : ''}]:`, error);
            if (CONFIG.DEBUG) {
                elements.debugError.textContent = `${context}: ${error.message || error}`;
            }
        }

        function updateConnectionStatus(connected) {
            isConnected = connected;
            elements.connectionIndicator.className = `connection-status ${connected ? 'connected' : ''}`;
            elements.connectionStatus.textContent = connected ? 'Online • Ready to help' : 'Offline • Reconnecting...';
            
            updateSendButtonState();
            updateDebugInfo();
        }

        function updateSendButtonState() {
            const hasText = elements.messageInput.value.trim().length > 0;
            elements.sendBtn.disabled = !isConnected || isSending || !hasText;
        }

        // UI Functions
        function toggleChatWindow() {
            isWindowOpen = !isWindowOpen;
            elements.chatWindow.style.display = isWindowOpen ? 'flex' : 'none';
            
            if (isWindowOpen) {
                elements.messageInput.focus();
                elements.notificationBadge.style.display = 'none';
                messageCount = 0;
                
                // Initialize with welcome message if no messages exist
                const existingMessages = elements.chatMessages.querySelectorAll('.message');
                if (existingMessages.length === 0) {
                    addWelcomeMessage();
                }
                
                // Start connection check
                checkConnection();
            }
        }

        function addWelcomeMessage() {
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'message bot';
            welcomeDiv.innerHTML = `
                <div class="message-content">
                    Hello! I'm your AI assistant. I can help you with information from uploaded documents. How can I help you today?
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `;
            
            elements.chatMessages.insertBefore(welcomeDiv, elements.typingIndicator);
            scrollToBottom();
        }

        function addMessage(content, isUser = false, timestamp = null) {
            try {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
                
                const time = timestamp || getCurrentTime();
                
                messageDiv.innerHTML = `
                    <div class="message-content">
                        ${isUser ? escapeHtml(content) : content}
                        <div class="message-time">${time}</div>
                    </div>
                `;
                
                // Insert before typing indicator
                elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
                scrollToBottom();
                
                if (!isUser && !isWindowOpen) {
                    messageCount++;
                    elements.notificationBadge.textContent = messageCount;
                    elements.notificationBadge.style.display = 'flex';
                }
            } catch (error) {
                logError(error, 'addMessage');
            }
        }

        function scrollToBottom() {
            setTimeout(() => {
                elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
            }, 100);
        }

        function showTyping() {
            isTyping = true;
            elements.typingIndicator.style.display = 'block';
            scrollToBottom();
        }

        function hideTyping() {
            isTyping = false;
            elements.typingIndicator.style.display = 'none';
        }

        function showStatus(message, type = 'error') {
            try {
                const statusDiv = document.createElement('div');
                statusDiv.className = `status-indicator ${type}`;
                statusDiv.textContent = message;
                
                elements.chatMessages.insertBefore(statusDiv, elements.typingIndicator);
                scrollToBottom();
                
                setTimeout(() => {
                    if (statusDiv.parentNode) {
                        statusDiv.remove();
                    }
                }, 5000);
            } catch (error) {
                logError(error, 'showStatus');
            }
        }

        function formatBotResponse(text) {
            if (!text) return 'No response received.';
            
            // Convert markdown-style formatting to HTML
            let formatted = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/## (.*?)(\n|$)/g, '<h4 style="margin: 10px 0 5px 0; color: #333;">$1</h4>')
                .replace(/### (.*?)(\n|$)/g, '<h5 style="margin: 8px 0 4px 0; color: #555;">$1</h5>')
                .replace(/\n\n/g, '<br><br>')
                .replace(/\n/g, '<br>');
            
            return formatted;
        }

        // API Functions
        async function sendMessage(message, retries = 0) {
            if (!message.trim() || isSending) return;

            isSending = true;
            
            try {
                // Add user message to chat
                addMessage(message, true);
                elements.messageInput.value = '';
                showTyping();
                updateSendButtonState();

                console.log('Sending message:', message);

                const requestBody = {
                    input_text: message,
                    model: 'hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0',
                    enhanced_mode: true,
                    session_id: CONFIG.SESSION_ID
                };

                const response = await fetch(`${CONFIG.API_BASE_URL}/query/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                });

                hideTyping();

                if (!response.ok) {
                    let errorMessage;
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.reply || errorData.error || `Server error: ${response.status}`;
                    } catch {
                        errorMessage = `Server error: ${response.status} ${response.statusText}`;
                    }
                    throw new Error(errorMessage);
                }

                const data = await response.json();
                console.log('Response data:', data);
                
                updateConnectionStatus(true);
                
                if (data.reply) {
                    const formattedReply = formatBotResponse(data.reply);
                    addMessage(formattedReply, false);
                } else {
                    addMessage("I apologize, but I didn't receive a proper response. Please try again.", false);
                }
                
            } catch (error) {
                hideTyping();
                logError(error, 'sendMessage');
                
                if (retries < CONFIG.MAX_RETRIES && (
                    error.message.includes('fetch') || 
                    error.message.includes('network') ||
                    error.message.includes('connection') ||
                    error.message.includes('timeout') ||
                    error.message.includes('Server error: 503') ||
                    error.message.includes('Server error: 502')
                )) {
                    showStatus(`Connection issue. Retrying... (${retries + 1}/${CONFIG.MAX_RETRIES})`, 'info');
                    setTimeout(() => {
                        sendMessage(message, retries + 1);
                    }, CONFIG.RETRY_DELAY);
                    return; // Don't reset UI state yet
                } else {
                    updateConnectionStatus(false);
                    showStatus(error.message, 'error');
                    addMessage("I'm having trouble connecting right now. Please check if the backend server is running and try again.", false);
                }
            } finally {
                // Re-enable UI
                isSending = false;
                updateSendButtonState();
                elements.messageInput.focus();
            }
        }

        async function clearChat() {
            try {
                // Clear all messages except typing indicator
                const messages = elements.chatMessages.querySelectorAll('.message, .status-indicator');
                messages.forEach(msg => msg.remove());
                
                // Add new welcome message
                addWelcomeMessage();
                
                showStatus('Chat cleared successfully', 'success');
            } catch (error) {
                logError(error, 'clearChat');
                showStatus('Failed to clear chat', 'error');
            }
        }

        async function startNewSession() {
            try {
                CONFIG.SESSION_ID = generateSessionId();
                console.log('New session started:', CONFIG.SESSION_ID);
                
                // Clear all messages except typing indicator
                const messages = elements.chatMessages.querySelectorAll('.message, .status-indicator');
                messages.forEach(msg => msg.remove());
                
                // Add new welcome message
                addWelcomeMessage();
                
                showStatus('New session started', 'success');
                updateDebugInfo();
            } catch (error) {
                logError(error, 'startNewSession');
                showStatus('Failed to start new session', 'error');
            }
        }

        async function checkConnection() {
            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/health/`, {
                    method: 'GET'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('Health check response:', data);
                    
                    const connected = data.ollama_status?.connected && data.rag_status?.initialized;
                    updateConnectionStatus(connected);
                    
                    if (!connected) {
                        let message = 'System not ready';
                        if (!data.ollama_status?.connected) {
                            message = 'Ollama not connected';
                        } else if (!data.rag_status?.initialized) {
                            message = 'RAG system not initialized';
                        }
                        showStatus(message, 'error');
                    }
                    
                    return connected;
                } else {
                    updateConnectionStatus(false);
                    return false;
                }
            } catch (error) {
                console.error('Connection check failed:', error);
                updateConnectionStatus(false);
                return false;
            }
        }

        function toggleDebug() {
            CONFIG.DEBUG = !CONFIG.DEBUG;
            elements.debugInfo.style.display = CONFIG.DEBUG ? 'block' : 'none';
            elements.toggleDebugBtn.textContent = CONFIG.DEBUG ? 'Hide Debug' : 'Debug';
            updateDebugInfo();
        }

        // Event Listeners
        elements.chatBubble.addEventListener('click', toggleChatWindow);
        elements.closeChat.addEventListener('click', toggleChatWindow);
        
        elements.chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = elements.messageInput.value.trim();
            if (message && !isSending) {
                await sendMessage(message);
            }
        });

        elements.messageInput.addEventListener('input', updateSendButtonState);
        elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                elements.chatForm.dispatchEvent(new Event('submit'));
            }
        });

        elements.clearChatBtn.addEventListener('click', clearChat);
        elements.newSessionBtn.addEventListener('click', startNewSession);
        elements.toggleDebugBtn.addEventListener('click', toggleDebug);

        // Suggestion buttons
        elements.suggestionButtons.addEventListener('click', async (e) => {
            if (e.target.classList.contains('suggestion-btn')) {
                const suggestion = e.target.textContent;
                elements.messageInput.value = suggestion;
                updateSendButtonState();
                if (!isSending && isConnected) {
                    await sendMessage(suggestion);
                }
            }
        });

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            console.log('ChatBot UI initialized');
            updateDebugInfo();
            
            // Set up periodic connection checks
            connectionCheckInterval = setInterval(checkConnection, CONFIG.CONNECTION_CHECK_INTERVAL);
            
            // Initial connection check
            setTimeout(checkConnection, 1000);
        });

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (connectionCheckInterval) {
                clearInterval(connectionCheckInterval);
            }
        });

        console.log('ChatBot script loaded successfully');
    </script>
</body>
</html>