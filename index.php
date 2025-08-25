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
            margin: 10px;
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

        /* Language Selector */
        .language-selector {
            position: absolute;
            bottom: 10px;
            right: 80px;
            background: rgba(255, 255, 255, 0.1);
            padding: 5px 10px;
            border-radius: 12px;
            font-size: 11px;
            color: white;
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
            top: 5px;
            left: 5px;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #e74c3c;
            transition: background-color 0.3s;
        }

        .connection-status.connected {
            background: #27ae60;
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
                        <h3>WSSD Assistant</h3>
                        <p id="connectionStatus">Connecting...</p>
                    </div>
                    <div class="connection-status" id="connectionIndicator"></div>
                </div>
                <button class="close-chat" id="closeChat">&times;</button>
                <div class="language-selector">
                    <span id="currentLang">English-IN</span>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-content">
                        Hello! I'm your AI assistant. How can I help you today?
                        <div class="message-time">Just now</div>
                    </div>
                </div>
            </div>

            <div class="typing-indicator" id="typingIndicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
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
            RETRY_DELAY: 1000
        };

        // DOM Elements
        const chatBubble = document.getElementById('chatBubble');
        const chatWindow = document.getElementById('chatWindow');
        const closeChat = document.getElementById('closeChat');
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const chatForm = document.getElementById('chatForm');
        const typingIndicator = document.getElementById('typingIndicator');
        const notificationBadge = document.getElementById('notificationBadge');
        const clearChatBtn = document.getElementById('clearChat');
        const newSessionBtn = document.getElementById('newSession');
        const connectionStatus = document.getElementById('connectionStatus');
        const connectionIndicator = document.getElementById('connectionIndicator');
        const suggestionButtons = document.getElementById('suggestionButtons');

        // State
        let isWindowOpen = false;
        let isTyping = false;
        let messageCount = 0;
        let isConnected = false;

        // Utility Functions
        function generateSessionId() {
            return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
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

        function updateConnectionStatus(connected) {
            isConnected = connected;
            connectionIndicator.className = `connection-status ${connected ? 'connected' : ''}`;
            connectionStatus.textContent = connected ? 'Online • Ready to help' : 'Offline • Reconnecting...';
        }

        // UI Functions
        function toggleChatWindow() {
            isWindowOpen = !isWindowOpen;
            chatWindow.style.display = isWindowOpen ? 'flex' : 'none';
            
            if (isWindowOpen) {
                messageInput.focus();
                notificationBadge.style.display = 'none';
                messageCount = 0;
            }
        }

        function addMessage(content, isUser = false, timestamp = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
            
            const time = timestamp || getCurrentTime();
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${isUser ? escapeHtml(content) : content}
                    <div class="message-time">${time}</div>
                </div>
            `;
            
            chatMessages.insertBefore(messageDiv, typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            if (!isUser && !isWindowOpen) {
                messageCount++;
                notificationBadge.textContent = messageCount;
                notificationBadge.style.display = 'flex';
            }
        }

        function showTyping() {
            isTyping = true;
            typingIndicator.style.display = 'block';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideTyping() {
            isTyping = false;
            typingIndicator.style.display = 'none';
        }

        function showStatus(message, type = 'error') {
            const statusDiv = document.createElement('div');
            statusDiv.className = `status-indicator ${type}`;
            statusDiv.textContent = message;
            
            chatMessages.insertBefore(statusDiv, typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.remove();
                }
            }, 5000);
        }

        function formatBotResponse(text) {
            // Convert markdown-style formatting to HTML
            let formatted = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/## (.*?)(\n|$)/g, '<h4>$1</h4>')
                .replace(/### (.*?)(\n|$)/g, '<h5>$1</h5>')
                .replace(/\n/g, '<br>');
            
            return formatted;
        }

        // API Functions
        async function sendMessage(message, retries = 0) {
            if (!message.trim()) return;

            // Disable form
            sendBtn.disabled = true;
            messageInput.disabled = true;

            // Add user message to chat
            addMessage(message, true);
            messageInput.value = '';
            showTyping();

            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/query/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        input_text: message,
                        model: 'hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0',
                        enhanced_mode: true,
                        session_id: CONFIG.SESSION_ID
                    })
                });

                hideTyping();

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.reply || `Server error: ${response.status}`);
                }

                const data = await response.json();
                updateConnectionStatus(true);
                
                if (data.reply) {
                    const formattedReply = formatBotResponse(data.reply);
                    addMessage(formattedReply, false);
                } else {
                    showStatus('Received empty response from server', 'error');
                }
            } catch (error) {
                hideTyping();
                updateConnectionStatus(false);
                console.error('Error sending message:', error);
                
                if (retries < CONFIG.MAX_RETRIES) {
                    setTimeout(() => {
                        sendMessage(message, retries + 1);
                    }, CONFIG.RETRY_DELAY);
                    showStatus(`Retrying... (${retries + 1}/${CONFIG.MAX_RETRIES})`, 'error');
                } else {
                    showStatus(error.message, 'error');
                    addMessage("I'm having trouble connecting right now. Please try again later or contact support.", false);
                }
            } finally {
                // Re-enable form
                sendBtn.disabled = false;
                messageInput.disabled = false;
                messageInput.focus();
            }
        }

        async function clearChat() {
            try {
                // Clear local chat
                const messages = chatMessages.querySelectorAll('.message:not(.bot):not(:first-child), .status-indicator');
                messages.forEach(msg => msg.remove());
                
                // Keep only the first welcome message
                const firstMessage = chatMessages.querySelector('.message.bot');
                firstMessage.querySelector('.message-content').innerHTML = `
                    Chat cleared! How can I help you today?
                    <div class="message-time">${getCurrentTime()}</div>
                `;
                
                showStatus('Chat cleared successfully', 'success');
            } catch (error) {
                console.error('Error clearing chat:', error);
                showStatus('Failed to clear chat', 'error');
            }
        }

        async function startNewSession() {
            try {
                CONFIG.SESSION_ID = generateSessionId();
                
                // Clear local chat
                const messages = chatMessages.querySelectorAll('.message:not(.bot):not(:first-child), .status-indicator');
                messages.forEach(msg => msg.remove());
                
                // Update welcome message
                const firstMessage = chatMessages.querySelector('.message.bot');
                firstMessage.querySelector('.message-content').innerHTML = `
                    New session started! How can I help you today?
                    <div class="message-time">${getCurrentTime()}</div>
                `;
                
                showStatus('New session started', 'success');
            } catch (error) {
                console.error('Error starting new session:', error);
                showStatus('Failed to start new session', 'error');
            }
        }

        async function checkConnection() {
            try {
                const response = await fetch(`${CONFIG.API_BASE_URL}/health/`);
                const data = await response.json();
                
                updateConnectionStatus(response.ok && data.ollama_status?.connected);
                
                return response.ok;
            } catch (error) {
                console.error('Connection check failed:', error);
                updateConnectionStatus(false);
                return false;
            }
        }

        // Event Listeners
        chatBubble.addEventListener('click', toggleChatWindow);
        closeChat.addEventListener('click', toggleChatWindow);

        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (message && !sendBtn.disabled && isConnected) {
                sendMessage(message);
            } else if (!isConnected) {
                showStatus('Not connected to server. Please wait...', 'error');
            }
        });

        // Suggestion button clicks
        suggestionButtons.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-btn')) {
                const suggestion = e.target.textContent;
                messageInput.value = suggestion;
                if (isConnected) {
                    sendMessage(suggestion);
                }
            }
        });

        // Quick actions
        clearChatBtn.addEventListener('click', clearChat);
        newSessionBtn.addEventListener('click', startNewSession);

        // Input validation
        messageInput.addEventListener('input', function() {
            const length = this.value.length;
            const maxLength = parseInt(this.getAttribute('maxlength'));
            
            if (length > maxLength - 50) {
                this.style.borderColor = '#f39c12';
            } else {
                this.style.borderColor = '#e1e8ed';
            }
            
            // Enable/disable send button
            sendBtn.disabled = !this.value.trim() || !isConnected;
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isWindowOpen) {
                toggleChatWindow();
            }
        });

        // Initialize
        console.log('Chatbot initialized with session:', CONFIG.SESSION_ID);
        console.log('API Base URL:', CONFIG.API_BASE_URL);

        // Initial connection check
        window.addEventListener('load', async () => {
            await checkConnection();
            
            // Periodic connection check
            setInterval(checkConnection, 30000); // Check every 30 seconds
        });
    </script>
</body>
</html>