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
            padding: 15px 20px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
        }

        .chat-header-info {
            display: flex;
            align-items: center;
            flex: 1;
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

        /* Language Dropdown */
        .language-selector {
            display: flex;
            align-items: center;
            margin-right: 10px;
        }

        .language-dropdown {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 4px 8px;
            border-radius: 8px;
            font-size: 12px;
            cursor: pointer;
            outline: none;
            transition: all 0.2s;
        }

        .language-dropdown:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .language-dropdown option {
            background: #ff6b35;
            color: white;
            padding: 5px;
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
                
                <div class="language-selector">
                    <select class="language-dropdown" id="languageSelect">
                        <option value="en">English</option>
                        <option value="hi">हिंदी</option>
                        <option value="mr">मराठी</option>
                    </select>
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
                    <p id="suggestionsLabel">Quick suggestions:</p>
                    <div class="suggestion-buttons" id="suggestionButtons">
                        <button class="suggestion-btn" data-en="What schemes are available?" data-hi="कौन सी योजनाएं उपलब्ध हैं?" data-mr="कोणत्या योजना उपलब्ध आहेत?">Schemes</button>
                        <button class="suggestion-btn" data-en="How to apply?" data-hi="आवेदन कैसे करें?" data-mr="अर्ज कसा करायचा?">Apply</button>
                        <button class="suggestion-btn" data-en="Eligibility criteria?" data-hi="पात्रता मापदंड?" data-mr="पात्रता निकष?">Eligibility</button>
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
        // Language configurations
        const LANGUAGE_CONFIG = {
            en: {
                name: 'English',
                welcomeMessage: "Hello! I'm your AI assistant. I can help you with information from uploaded documents. How can I help you today?",
                placeholder: "Ask your query here",
                suggestionsLabel: "Quick suggestions:",
                connectionOnline: "Online • Ready to help",
                connectionOffline: "Offline • Reconnecting...",
                clearChat: "Clear Chat",
                newSession: "New Session",
                systemNotReady: "System is not ready. Please check if documents are loaded and Ollama is running.",
                errorProcessing: "I encountered an error processing your request. Please try again.",
                waitMessage: "Please wait a moment before sending another message.",
                noResponse: "I couldn't find relevant information in the documents. Please ask questions related to the uploaded content or try rephrasing your query."
            },
            hi: {
                name: 'हिंदी',
                welcomeMessage: "नमस्ते! मैं आपका AI सहायक हूं। मैं अपलोड किए गए दस्तावेजों की जानकारी से आपकी मदद कर सकता हूं। मैं आपकी कैसे सहायता कर सकता हूं?",
                placeholder: "यहां अपना प्रश्न पूछें",
                suggestionsLabel: "त्वरित सुझाव:",
                connectionOnline: "ऑनलाइन • मदद के लिए तैयार",
                connectionOffline: "ऑफलाइन • पुनः कनेक्ट हो रहा है...",
                clearChat: "चैट साफ़ करें",
                newSession: "नया सत्र",
                systemNotReady: "सिस्टम तैयार नहीं है। कृपया जांच लें कि दस्तावेज़ लोड हैं और Ollama चल रहा है।",
                errorProcessing: "आपके अनुरोध को प्रसंस्करण करने में एक त्रुटि आई। कृपया पुनः प्रयास करें।",
                waitMessage: "कृपया अगला संदेश भेजने से पहले थोड़ा इंतज़ार करें।",
                noResponse: "मुझे दस्तावेजों में प्रासंगिक जानकारी नहीं मिली। कृपया अपलोड की गई सामग्री से संबंधित प्रश्न पूछें या अपने प्रश्न को दूसरे तरीके से पूछने का प्रयास करें।"
            },
            mr: {
                name: 'मराठी',
                welcomeMessage: "नमस्कार! मी तुमचा AI सहाय्यक आहे। मी अपलोड केलेल्या दस्तावेजांमधील माहितीसह तुम्हाला मदत करू शकतो. मी तुमची कशी मदत करू शकतो?",
                placeholder: "इथे तुमचा प्रश्न विचारा",
                suggestionsLabel: "त्वरित सूचना:",
                connectionOnline: "ऑनलाइन • मदतीसाठी तयार",
                connectionOffline: "ऑफलाइन • पुन्हा कनेक्ट होत आहे...",
                clearChat: "चॅट साफ करा",
                newSession: "नवीन सत्र",
                systemNotReady: "सिस्टीम तयार नाही. कृपया तपासून पहा की दस्तावेज लोड झाले आहेत आणि Ollama चालू आहे.",
                errorProcessing: "तुमची विनंती प्रक्रिया करतांना एक त्रुटी आली. कृपया पुन्हा प्रयत्न करा.",
                waitMessage: "कृपया दुसरा संदेश पाठवण्यापूर्वी थोडा वेळ थांबा.",
                noResponse: "मला दस्तावेजांमध्ये संबंधित माहिती आढळली नाही. कृपया अपलोड केलेल्या सामग्रीशी संबंधित प्रश्न विचारा किंवा तुमचा प्रश्न वेगळ्या प्रकारे विचारण्याचा प्रयत्न करा."
            }
        };

        // Configuration
        const CONFIG = {
            API_BASE_URL: 'http://localhost:8000',
            SESSION_ID: generateSessionId(),
            MAX_RETRIES: 2,
            RETRY_DELAY: 1000,
            CONNECTION_CHECK_INTERVAL: 30000,
            CURRENT_LANGUAGE: 'en'
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
            connectionStatus: document.getElementById('connectionStatus'),
            connectionIndicator: document.getElementById('connectionIndicator'),
            suggestionButtons: document.getElementById('suggestionButtons'),
            suggestionsLabel: document.getElementById('suggestionsLabel'),
            languageSelect: document.getElementById('languageSelect')
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
            return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
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
            elements.connectionIndicator.className = `connection-status ${connected ? 'connected' : ''}`;
            
            const langConfig = LANGUAGE_CONFIG[CONFIG.CURRENT_LANGUAGE];
            elements.connectionStatus.textContent = connected ? langConfig.connectionOnline : langConfig.connectionOffline;
            
            updateSendButtonState();
        }

        function updateSendButtonState() {
            const hasText = elements.messageInput.value.trim().length > 0;
            elements.sendBtn.disabled = !isConnected || isSending || !hasText;
        }

        // Language Functions
        function updateLanguage(langCode) {
            CONFIG.CURRENT_LANGUAGE = langCode;
            const langConfig = LANGUAGE_CONFIG[langCode];
            
            // Update UI elements
            elements.messageInput.placeholder = langConfig.placeholder;
            elements.suggestionsLabel.textContent = langConfig.suggestionsLabel;
            elements.clearChatBtn.textContent = langConfig.clearChat;
            elements.newSessionBtn.textContent = langConfig.newSession;
            
            // Update connection status
            updateConnectionStatus(isConnected);
            
            // Update suggestion buttons
            updateSuggestionButtons();
            
            // Add language change message only if chat is open and has messages
            if (isWindowOpen && elements.chatMessages.querySelectorAll('.message').length > 0) {
                addLanguageChangeMessage(langConfig.name);
            }
            
            // Save language preference
            try {
                localStorage.setItem('chatbot_language', langCode);
            } catch (e) {
                console.warn('Could not save language preference:', e);
            }
        }

        function updateSuggestionButtons() {
            const langCode = CONFIG.CURRENT_LANGUAGE;
            const buttons = elements.suggestionButtons.querySelectorAll('.suggestion-btn');
            
            buttons.forEach(btn => {
                const text = btn.getAttribute(`data-${langCode}`);
                if (text) {
                    btn.textContent = text;
                }
            });
        }

        function addLanguageChangeMessage(languageName) {
            const message = `Language switched to ${languageName}`;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'status-indicator info';
            messageDiv.textContent = message;
            
            elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
            scrollToBottom();
            
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, 3000);
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
            const langConfig = LANGUAGE_CONFIG[CONFIG.CURRENT_LANGUAGE];
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'message bot';
            welcomeDiv.innerHTML = `
                <div class="message-content">
                    ${langConfig.welcomeMessage}
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
                
                elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
                scrollToBottom();
                
                if (!isUser && !isWindowOpen) {
                    messageCount++;
                    elements.notificationBadge.textContent = messageCount;
                    elements.notificationBadge.style.display = 'flex';
                }
            } catch (error) {
                console.error('Error adding message:', error);
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
                console.error('Error showing status:', error);
            }
        }

        // API Functions
        async function sendMessage(message, retries = 0) {
            if (!message.trim() || isSending) return;

            isSending = true;
            
            try {
                addMessage(message, true);
                elements.messageInput.value = '';
                showTyping();
                updateSendButtonState();

                const requestBody = {
                    input_text: message,
                    model: 'hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0',
                    enhanced_mode: true,
                    session_id: CONFIG.SESSION_ID
                };

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout

                const response = await fetch(`${CONFIG.API_BASE_URL}/query/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);
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
                updateConnectionStatus(true);
                
                if (data.reply) {
                    addMessage(data.reply, false);
                } else {
                    const langConfig = LANGUAGE_CONFIG[CONFIG.CURRENT_LANGUAGE];
                    addMessage(langConfig.noResponse, false);
                }
                
            } catch (error) {
                hideTyping();
                console.error('Send message error:', error);
                
                const langConfig = LANGUAGE_CONFIG[CONFIG.CURRENT_LANGUAGE];
                
                if (retries < CONFIG.MAX_RETRIES && (error.name === 'AbortError' || error.message.includes('fetch'))) {
                    showStatus(`Retrying... (${retries + 1}/${CONFIG.MAX_RETRIES})`, 'info');
                    setTimeout(() => {
                        sendMessage(message, retries + 1);
                    }, CONFIG.RETRY_DELAY);
                    return;
                } else {
                    updateConnectionStatus(false);
                    showStatus(error.message, 'error');
                    addMessage(langConfig.errorProcessing, false);
                }
            } finally {
                isSending = false;
                updateSendButtonState();
                elements.messageInput.focus();
            }
        }

        async function clearChat() {
            try {
                const messages = elements.chatMessages.querySelectorAll('.message, .status-indicator');
                messages.forEach(msg => msg.remove());
                
                addWelcomeMessage();
                showStatus('Chat cleared successfully', 'success');
            } catch (error) {
                console.error('Clear chat error:', error);
                showStatus('Failed to clear chat', 'error');
            }
        }

        async function startNewSession() {
            try {
                CONFIG.SESSION_ID = generateSessionId();
                console.log('New session started:', CONFIG.SESSION_ID);
                
                const messages = elements.chatMessages.querySelectorAll('.message, .status-indicator');
                messages.forEach(msg => msg.remove());
                
                addWelcomeMessage();
                showStatus('New session started', 'success');
            } catch (error) {
                console.error('New session error:', error);
                showStatus('Failed to start new session', 'error');
            }
        }

        async function checkConnection() {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);

                const response = await fetch(`${CONFIG.API_BASE_URL}/health/`, {
                    method: 'GET',
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (response.ok) {
                    const data = await response.json();
                    const connected = data.ollama_status?.connected && data.rag_status?.initialized;
                    updateConnectionStatus(connected);
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
        elements.clearChatBtn.addEventListener('click', clearChat);
        elements.newSessionBtn.addEventListener('click', startNewSession);

        // Language selector event listener - FIXED
        elements.languageSelect.addEventListener('change', (e) => {
            const selectedLang = e.target.value;
            console.log('Language changed to:', selectedLang);
            updateLanguage(selectedLang);
        });

        // Suggestion buttons
        elements.suggestionButtons.addEventListener('click', async (e) => {
            if (e.target.classList.contains('suggestion-btn')) {
                const langCode = CONFIG.CURRENT_LANGUAGE;
                const suggestion = e.target.getAttribute(`data-${langCode}`) || e.target.textContent;
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
            
            // Load saved language preference
            try {
                const savedLanguage = localStorage.getItem('chatbot_language');
                if (savedLanguage && LANGUAGE_CONFIG[savedLanguage]) {
                    CONFIG.CURRENT_LANGUAGE = savedLanguage;
                    elements.languageSelect.value = savedLanguage;
                }
            } catch (e) {
                console.warn('Could not load language preference:', e);
            }
            
            // Apply current language
            updateLanguage(CONFIG.CURRENT_LANGUAGE);
            
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