<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WSSD JJM</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #fbfcfdff 0%, #f4f3f5ff 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .demo-content {
            text-align: center;
            color: blue;
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
            background: linear-gradient(135deg, #3b5fffff 0%, #7d99f8ff 100%);
            width: 72px;
            height: 74px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(103, 105, 245, 0.4);
            transition: all 0.3s ease;
            animation: pulse 2s infinite;
        }

        .chat-bubble:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(118, 120, 253, 0.6);
        }

        .chat-bubble svg {
            width: 28px;
            height: 28px;
            fill: white;
        }

        .chat-bubble img {
            width: 74px;
            height: 74px;
            object-fit: contain;
            display: block;
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
            0% { box-shadow: 0 4px 20px rgba(117, 160, 253, 0.4); }
            50% { box-shadow: 0 4px 20px rgba(132, 134, 255, 0.8); }
            100% { box-shadow: 0 4px 20px rgba(124, 153, 247, 0.4); }
        }

        /* Chat Window */
        .chat-window {
            position: fixed;
            bottom: 103px;
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
            background: linear-gradient(135deg, #e6e9f0ff 0%, #092becff 100%);
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
            width: auto;
            height: auto;
            border-radius: 0;
            background: transparent;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
        }

        .chat-avatar img {
            width: 72px;
            height: 72px;
            object-fit: contain;
            display: block;
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
            background: #606bfdff;
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
            transition: all 0.2s ease;
        }

        .suggestion-btn:hover {
            background: #e8eaed;
            transform: translateY(-1px);
        }

        .suggestion-btn:active {
            transform: translateY(0);
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
            border-color: #574bf7ff;
        }

        .send-btn {
            background: linear-gradient(135deg, #5161f1ff 0%, #858febff 100%);
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
            transition: all 0.2s ease;
        }

        .quick-action-btn:hover {
            transform: translateY(-1px);
            opacity: 0.9;
        }

        .quick-action-btn:active {
            transform: translateY(0);
        }

        /* Enhanced Button Animations - Applied to all interactive buttons */
        .pgrs-options {
            display: flex;
            flex-direction: row;
            gap: 4px;
            margin-top: 10px;
        }

        .option-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 7px 35px;
            border-radius: 16px;
            font-size: 12px;
            color: white;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 0px solid transparent;
        }

        .option-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        }

        .option-button:active {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }

        .link-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 10px 16px;
            border-radius: 16px;
            font-size: 12px;
            color: white;
            cursor: pointer;
            transition: all 0.2s ease;
            margin: 4px;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }

        .link-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        }

        .link-button:active {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }

        /* 5-Star Rating System Styles */
        .rating-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }

        .rating-title {
            font-size: 14px;
            font-weight: 600;
            color: #495057;
            text-align: center;
            margin-bottom: 10px;
        }

        .stars-container {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin: 10px 0;
        }

        .star {
            width: 32px;
            height: 32px;
            cursor: pointer;
            transition: all 0.3s ease;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
        }

        .star svg {
            width: 100%;
            height: 100%;
        }

        .star.empty svg {
            fill: #d1d5db;
            stroke: #9ca3af;
            stroke-width: 1;
        }

        .star.filled svg {
            fill: #fbbf24;
            stroke: #f59e0b;
            stroke-width: 1;
        }

        .star.hover svg {
            fill: #fcd34d;
            stroke: #f59e0b;
            stroke-width: 1;
            transform: scale(1.1);
        }

        .star:hover {
            transform: scale(1.15);
        }

        .rating-labels {
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #6b7280;
            margin-top: 5px;
            padding: 0 5px;
        }

        .rating-feedback {
            text-align: center;
            margin: 10px 0;
            font-size: 13px;
            font-weight: 500;
        }

        .rating-feedback.rating-1 { color: #dc2626; }
        .rating-feedback.rating-2 { color: #ea580c; }
        .rating-feedback.rating-3 { color: #ca8a04; }
        .rating-feedback.rating-4 { color: #16a34a; }
        .rating-feedback.rating-5 { color: #059669; }

        .message.bot.rating-confirmation {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            text-align: center;
            padding: 12px 16px;
            border-radius: 12px;
            margin: 8px 0;
            box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
        }

        .message.bot.thank-you {
            background: #f8fafc;
            color: #1e293b;
            text-align: center;
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border: 1px solid #e2e8f0;
        }

        .submit-rating-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
            align-self: center;
            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
        }

        .submit-rating-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }

        .submit-rating-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            background: #9ca3af;
            box-shadow: none;
        }

        .submit-rating-btn:active:not(:disabled) {
            transform: translateY(-1px);
        }

        .rating-success {
            background: #dcfce7;
            border: 1px solid #bbf7d0;
            color: #166534;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-size: 12px;
            margin-top: 10px;
        }

        .input-field {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #e1e8ed;
            border-radius: 12px;
            font-size: 14px;
            outline: none;
            transition: all 0.2s ease;
            margin-bottom: 10px;
        }

        .input-field:focus {
            border-color: #574bf7ff;
            box-shadow: 0 0 0 3px rgba(87, 75, 247, 0.1);
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

        /* Quick Suggestions Styles */
        .quick-suggestions {
            margin-bottom: 15px;
            max-height: 120px;
            overflow-y: auto;
        }

        .quick-suggestions h4 {
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .suggestions-grid {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .quick-suggestion-btn {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 11px;
            color: #495057;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
            line-height: 1.3;
        }

        .quick-suggestion-btn:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }

        .quick-suggestion-btn:active {
            transform: translateY(0);
        }

        /* Export Button */
        .export-ratings-btn {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border: none;
            padding: 8px 12px;
            border-radius: 16px;
            font-size: 11px;
            color: white;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-left: 8px;
        }

        .export-ratings-btn:hover {
            transform: translateY(-1px);
            opacity: 0.9;
            box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
        }

        .export-ratings-btn:active {
            transform: translateY(0);
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
        <h1>Welcome to PGRS Portal Chatbot.</h1>
    </div>   

    <!-- Chat Widget -->
    <div class="chat-widget">
        <div class="chat-bubble" id="chatBubble">
            <img src="logo/main_logo.png" alt="Chat" onerror="this.style.display='none'; this.parentNode.innerHTML='<svg viewBox=\'0 0 24 24\'><path d=\'M20,2H4A2,2 0 0,0 2,4V22L6,18H20A2,2 0 0,0 22,16V4A2,2 0 0,0 20,2M6,9H18V11H6V9M14,14H6V12H14V14M18,8H6V6H18V8Z\'/></svg>'"/>
            <div class="notification-badge" id="notificationBadge" style="display: none;">0</div>
        </div>

        <div class="chat-window" id="chatWindow">
            <div class="chat-header">
                <div class="chat-header-info">
                    <div class="chat-avatar">
                        <img src="logo/jjm_new_logo.svg" alt="PGRS Logo" onerror="this.style.display='none'">
                    </div>
                    <div class="chat-header-text">
                        <h3>Public Grievance Redressal System Portal</h3>
                        <p id="connectionStatus">Ready to help</p>
                    </div>
                </div>
                
                <div class="language-selector">
                    <select class="language-dropdown" id="languageSelect">
                        <option value="en">English</option>
                        <option value="mr">मराठी</option>
                    </select>
                </div>
                
                <button class="close-chat" id="closeChat">&times;</button>
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
                <!-- Quick Suggestions Section -->
                <div class="quick-suggestions" id="quickSuggestions">
                    <h4 id="suggestionsTitle">Quick Suggestions:</h4>
                    <div class="suggestions-grid" id="suggestionsGrid">
                        <!-- Dynamic suggestions will be loaded here -->
                    </div>
                </div>

                <div class="quick-actions">
                    <button class="quick-action-btn" id="restartBtn">Restart</button>
                    <button class="quick-action-btn" id="clearChatBtn">Clear Chat</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // API Configuration
        const API_BASE_URL = 'http://localhost:8000';
        
        // PGRS Script Configuration
        const PGRS_SCRIPTS = {
            en: {
                welcome: "Welcome to Public Grievance Redressal System portal AI-ChatBot.",
                question1: "Would you like to register a Grievance on the Maha-Jal Samadhan Public Grievance Redressal System?",
                question2: "Would you like to check the status of the grievance which you have registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
                question3: "Would you like to provide feedback regarding the resolution of your grievance addressed through the Maha-Jal Samadhan Public Grievance Redressal System?",
                register_methods: "You can register your Grievance on the Maha-Jal Samadhan Public Grievance Redressal System through two methods:",
                website_method: "1. Registering a Grievance via the Maha-Jal Samadhan Website",
                website_link: "https://mahajalsamadhan.in/log-grievance",
                app_method: "2. Registering a Grievance via the Maha-Jal Samadhan Mobile App",
                app_link: "https://play.google.com/store/apps/details?id=in.mahajalsamadhan.user&pli=1",
                grievance_id_prompt: "Please enter your Grievance ID (For example: \"G-12safeg7678\")",
                invalid_grievance_id: "The Grievance ID you have entered is incorrect or invalid. Please enter the correct Grievance ID to proceed.",
                status_prefix: "The current status of your Grievance is as follows:",
                rating_request: "Please provide your rating between 1 and 5:",
                invalid_input: "The information you have entered is invalid. Please try again.",
                thank_you: "Thank you for using the Maha-Jal Samadhan Public Grievance Redressal System.",
                yes: "YES",
                no: "NO",
                website_button: "Register via Website",
                app_button: "Download Mobile App",
                suggestions_title: "Quick Suggestions:",
                rating_labels: {
                    1: "Poor",
                    2: "Fair", 
                    3: "Good",
                    4: "Very Good",
                    5: "Excellent"
                },
                suggestions: [
                    "I want to check grievance status",
                    "I want to provide feedback"
                ]
            },
            mr: {
                welcome: "नमस्कार, सार्वजनिक तक्रार निवारण प्रणाली पोर्टल एआय-चॅटबॉटमध्ये आपले स्वागत आहे.",
                question1: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर आपण तक्रार नोंदू इच्छिता का?",
                question2: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर आपण केलेल्या तक्रारीची स्थिती पाहू इच्छिता का?",
                question3: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीद्वारे सोडविण्यात आलेल्या आपल्या तक्रारीच्या निराकरणाबाबत अभिप्राय देऊ इच्छिता का?",
                register_methods: "आपण 'महा-जल समाधान' सार्वजनिक तक्रार निवारण प्रणालीवर आपली तक्रार दोन पद्धतींनी नोंदवू शकता:",
                website_method: "१. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर वेबसाईटद्वारे तक्रार नोंदणी",
                website_link: "https://mahajalsamadhan.in/log-grievance",
                app_method: "२. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर मोबाईल अ‍ॅपद्वारे तक्रार नोंदणी",
                app_link: "https://play.google.com/store/apps/details?id=in.mahajalsamadhan.user&pli=1",
                grievance_id_prompt: "कृपया आपण आपल्या तक्रारीचा \"Grievance ID\" म्हणजेच तक्रार नोंदणी क्रमांक दाखल/नमूद करा. (उदाहरणार्थ - \"G-12safeg7678\")",
                invalid_grievance_id: "आपण आपल्या तक्रारीचा \"Grievance ID\" म्हणजेच तक्रार नोंदणी क्रमांक चुकीचा दाखल केला आहे. कृपया योग्य \"Grievance ID\" म्हणजेच तक्रार नोंदणी क्रमांक दाखल/नमूद करा",
                status_prefix: "आपल्या तक्रारीची सद्यस्थिती पुढीलप्रमाणे आहे:",
                rating_request: "कृपया आपल्याद्वारे देण्यात आलेले गुण १ ते ५ मध्ये देण्यात यावे:",
                invalid_input: "आपण दिलेली माहिती अवैध आहे. कृपया पुन्हा प्रयत्न करा.",
                thank_you: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीचा वापर केल्याबद्दल आपले धन्यवाद.",
                yes: "होय",
                no: "नाही",
                website_button: "वेबसाईटवरून नोंदणी करा",
                app_button: "मोबाईल अ‍ॅप डाउनलोड करा",
                suggestions_title: "त्वरित सूचना:",
                rating_labels: {
                    1: "खराब",
                    2: "सामान्य",
                    3: "चांगले", 
                    4: "खूप चांगले",
                    5: "उत्कृष्ट"
                },
                suggestions: [
                    
                    "मला तक्रार स्थिती तपासायची आहे",
                    "मला अभिप्राय द्यायचा आहे"
                ]
            }
        };

        // State Management
        let currentLanguage = 'en';
        let chatState = 'start';
        let pendingGrievanceId = '';
        let selectedRating = null;
        let isWindowOpen = false;
        let currentSessionId = null;

        // DOM Elements
        const elements = {
            chatBubble: document.getElementById('chatBubble'),
            chatWindow: document.getElementById('chatWindow'),
            closeChat: document.getElementById('closeChat'),
            chatMessages: document.getElementById('chatMessages'),
            typingIndicator: document.getElementById('typingIndicator'),
            languageSelect: document.getElementById('languageSelect'),
            restartBtn: document.getElementById('restartBtn'),
            clearChatBtn: document.getElementById('clearChatBtn'),
            quickSuggestions: document.getElementById('quickSuggestions'),
            suggestionsGrid: document.getElementById('suggestionsGrid'),
            suggestionsTitle: document.getElementById('suggestionsTitle')
        };

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

        function scrollToBottom() {
            setTimeout(() => {
                elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
            }, 100);
        }

        function showTypingIndicator() {
            elements.typingIndicator.style.display = 'block';
            scrollToBottom();
        }

        function hideTypingIndicator() {
            elements.typingIndicator.style.display = 'none';
        }

        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${content}
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `;
            
            elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
            scrollToBottom();
        }

        function addOptionsMessage(content, options) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            
            let optionsHtml = '';
            options.forEach((option, index) => {
                optionsHtml += `<button class="option-button" data-option="${index}">${option}</button>`;
            });
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${content}
                    <div class="pgrs-options">
                        ${optionsHtml}
                    </div>
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `;
            
            elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
            scrollToBottom();
            
            // Add event listeners to option buttons
            messageDiv.querySelectorAll('.option-button').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const optionIndex = parseInt(e.target.dataset.option);
                    const optionText = options[optionIndex];
                    addMessage(optionText, true);
                    handleUserChoice(optionIndex);
                });
            });
        }

        function addLinksMessage(content, links) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            
            let linksHtml = '';
            links.forEach(link => {
                linksHtml += `<button class="link-button" onclick="window.open('${link.url}', '_blank')">${link.text}</button>`;
            });
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${content}
                    ${linksHtml}
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `;
            
            elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
            scrollToBottom();
        }

        function addRatingMessage(content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            
            const script = PGRS_SCRIPTS[currentLanguage];
            const labels = script.rating_labels;
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${content}
                    <div class="rating-container">
                        <div class="rating-title">Rate our service quality</div>
                        <div class="stars-container" id="starsContainer">
                            ${[1,2,3,4,5].map(num => `
                                <div class="star empty" data-rating="${num}">
                                    <svg viewBox="0 0 24 24">
                                        <path d="M12,17.27L18.18,21L16.54,13.97L22,9.24L14.81,8.62L12,2L9.19,8.62L2,9.24L7.46,13.97L5.82,21L12,17.27Z"/>
                                    </svg>
                                </div>
                            `).join('')}
                        </div>
                        <div class="rating-labels">
                            <span>${labels[1]}</span>
                            <span>${labels[2]}</span>
                            <span>${labels[3]}</span>
                            <span>${labels[4]}</span>
                            <span>${labels[5]}</span>
                        </div>
                        <div class="rating-feedback" id="ratingFeedback"></div>
                        <button class="submit-rating-btn" id="submitRatingBtn" disabled>Submit Rating</button>
                    </div>
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `;
            
            elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
            scrollToBottom();
            
            setupRatingSystem(messageDiv);
        }

        function setupRatingSystem(container) {
            const stars = container.querySelectorAll('.star');
            const submitBtn = container.querySelector('#submitRatingBtn');
            const feedback = container.querySelector('#ratingFeedback');
            const script = PGRS_SCRIPTS[currentLanguage];
            
            let currentRating = 0;
            let hoverRating = 0;

            // Star hover and click functionality
            stars.forEach((star, index) => {
                const rating = index + 1;
                
                star.addEventListener('mouseenter', () => {
                    hoverRating = rating;
                    updateStarDisplay(stars, hoverRating, currentRating, true);
                    showFeedback(feedback, rating, script.rating_labels);
                });
                
                star.addEventListener('mouseleave', () => {
                    hoverRating = 0;
                    updateStarDisplay(stars, currentRating, currentRating, false);
                    if (currentRating > 0) {
                        showFeedback(feedback, currentRating, script.rating_labels);
                    } else {
                        feedback.textContent = '';
                        feedback.className = 'rating-feedback';
                    }
                });
                
                star.addEventListener('click', () => {
                    currentRating = rating;
                    selectedRating = rating;
                    updateStarDisplay(stars, currentRating, currentRating, false);
                    showFeedback(feedback, currentRating, script.rating_labels);
                    submitBtn.disabled = false;
                });
            });

            // Submit button functionality
            submitBtn.addEventListener('click', async () => {
                if (selectedRating) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Submitting...';
                    
                    try {
                        await submitRating(selectedRating);
                    } catch (error) {
                        console.error('Failed to submit rating:', error);
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Submit Rating';
                    }
                }
            });
        }

        function updateStarDisplay(stars, rating, currentRating, isHovering) {
            stars.forEach((star, index) => {
                const starRating = index + 1;
                star.className = 'star';
                
                if (starRating <= rating) {
                    if (isHovering) {
                        star.className += ' hover';
                    } else {
                        star.className += ' filled';
                    }
                } else {
                    star.className += ' empty';
                }
            });
        }

        function showFeedback(feedbackElement, rating, labels) {
            feedbackElement.textContent = labels[rating];
            feedbackElement.className = `rating-feedback rating-${rating}`;
        }

        async function submitRating(rating) {
            try {
                const ratingLabels = PGRS_SCRIPTS[currentLanguage].rating_labels;
                const script = PGRS_SCRIPTS[currentLanguage];
                
                // Send rating to backend
                const response = await fetch(`${API_BASE_URL}/rating/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        rating: rating,
                        session_id: currentSessionId,
                        language: currentLanguage,
                        grievance_id: pendingGrievanceId || 'NA',
                        feedback_text: document.getElementById('feedbackText')?.value || ''
                    })
                });

                if (response.ok) {
                    setTimeout(() => {
                        addMessage(script.thank_you, false);
                        chatState = 'end';
                        // Reset the pending grievance ID
                        pendingGrievanceId = '';
                    }, 500);
                } else {
                    throw new Error('Failed to submit rating');
                }
            } catch (error) {
                console.error('Rating submission error:', error);
                addMessage('Sorry, there was an error submitting your rating. Please try again.', false);
                // Reset chat state to allow retry
                chatState = 'rating';
            }
        }

        function loadQuickSuggestions() {
            const script = PGRS_SCRIPTS[currentLanguage];
            elements.suggestionsTitle.textContent = script.suggestions_title;
            
            elements.suggestionsGrid.innerHTML = '';
            
            script.suggestions.forEach(suggestion => {
                const suggestionBtn = document.createElement('button');
                suggestionBtn.className = 'quick-suggestion-btn';
                suggestionBtn.textContent = suggestion;
                suggestionBtn.addEventListener('click', () => {
                    handleQuickSuggestion(suggestion);
                });
                elements.suggestionsGrid.appendChild(suggestionBtn);
            });
        }

        // Show grievance input immediately
        function showGrievanceInput() {
            chatState = 'awaiting_grievance_id';
            const script = PGRS_SCRIPTS[currentLanguage];
            
            // Create input message immediately
            const inputDiv = document.createElement('div');
            inputDiv.className = 'message bot';
            inputDiv.innerHTML = `
                <div class="message-content">
                    Please enter your Grievance ID to check the status:
                    <div style="background: #e8f4fd; border: 3px solid #2196f3; border-radius: 15px; padding: 20px; margin: 15px 0;">
                        <div style="margin-bottom: 10px; font-weight: bold; color: #1976d2;">
                            Enter Grievance ID (Example: G-12safeg7678)
                        </div>
                        <input type="text" 
                               id="grievanceInput" 
                               placeholder="Type your Grievance ID here..." 
                               style="width: 100%; padding: 15px; border: 2px solid #2196f3; border-radius: 8px; font-size: 16px; margin-bottom: 15px; outline: none;"
                               maxlength="50">
                        <button id="checkStatusBtn" 
                                style="width: 100%; padding: 15px; background: #2196f3; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: not-allowed;" 
                                disabled>
                            Check Grievance Status
                        </button>
                    </div>
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `;
            
            elements.chatMessages.insertBefore(inputDiv, elements.typingIndicator);
            scrollToBottom();
            
            // Setup input immediately
            const input = document.getElementById('grievanceInput');
            const button = document.getElementById('checkStatusBtn');
            
            input.addEventListener('input', function() {
                const hasValue = this.value.trim().length > 0;
                button.disabled = !hasValue;
                button.style.backgroundColor = hasValue ? '#2196f3' : '#ccc';
                button.style.cursor = hasValue ? 'pointer' : 'not-allowed';
            });
            
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !button.disabled) {
                    processGrievanceId(this.value.trim());
                }
            });
            
            button.addEventListener('click', function() {
                if (!this.disabled) {
                    processGrievanceId(input.value.trim());
                }
            });
            
            input.focus();
        }

        // Process grievance ID
        async function fetchGrievanceStatus(grievanceId, language) {
    try {
        const response = await fetch(`${API_BASE_URL}/grievance/status/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grievance_id: grievanceId, language: language })
        });
        const data = await response.json();
        if (response.ok && data.found) {
            return { success: true, message: data.message };
        } else if (response.status === 404) {
            return { success: false, message: data.message || "Grievance not found." };
        } else {
            return { success: false, message: "Error fetching status. Please try again." };
        }
    } catch (error) {
        console.error("Network error", error);
        return { success: false, message: "Error connecting to server." };
    }
}


       async function processGrievanceId(grievanceId) {
    const script = PGRS_SCRIPTS[currentLanguage];

    // Disable input
    const input = document.getElementById('grievanceInput');
    const button = document.getElementById('checkStatusBtn');
    input.disabled = true;
    button.disabled = true;
    button.textContent = 'Processing...';
    button.style.backgroundColor = '#999';

    // Add user message
    addMessage(grievanceId, true);

    // Validate format
    const grievancePattern = /^G-[A-Za-z0-9]{8,}$/i;
    if (!grievancePattern.test(grievanceId)) {
        setTimeout(() => {
            addMessage(script.invalid_grievance_id, false);
            setTimeout(() => {
                showGrievanceInput(); // Show input again
            }, 1500);
        }, 1000);
        return;
    }

    showTypingIndicator(); // Optional: Show "Assistant is typing..."

    try {
        // Call backend API to fetch real-time status
        const result = await fetchGrievanceStatus(grievanceId, currentLanguage);

        if (result.success) {
            hideTypingIndicator();
            // Display backend's detailed status message
            addMessage(result.message, false);
            pendingGrievanceId = grievanceId;
            // Continue to feedback question
            setTimeout(() => {
                chatState = 'question3';
                addOptionsMessage(script.question3, [script.yes, script.no]);
            }, 2000);
        } else {
            hideTypingIndicator();
            // Show error message from API (e.g., "Grievance not found")
            addMessage(result.message, false);
            // Let user retry
            setTimeout(() => {
                showGrievanceInput();
            }, 1500);
        }
    } catch (error) {
        hideTypingIndicator();
        addMessage("Error connecting to the server. Please try again.", false);
        setTimeout(() => {
            showGrievanceInput();
        }, 1500);
    }
}


        function handleQuickSuggestion(suggestion) {
            // Add user message
            addMessage(suggestion, true);
            
            // Hide suggestions temporarily to avoid clutter
            elements.quickSuggestions.style.display = 'none';
            
            // Process the suggestion based on current state and content
            setTimeout(() => {
                processQuickSuggestion(suggestion);
                // Show suggestions again after processing
                setTimeout(() => {
                    elements.quickSuggestions.style.display = 'block';
                }, 1000);
            }, 500);
        }

        // Process quick suggestions - updated to handle grievance status
        function processQuickSuggestion(suggestion) {
            const script = PGRS_SCRIPTS[currentLanguage];
            const lowerSuggestion = suggestion.toLowerCase();
            
            // Handle feedback suggestions
            if (lowerSuggestion.includes('feedback') || lowerSuggestion.includes('अभिप्राय') || 
                lowerSuggestion.includes('द्यायचा')) {
                chatState = 'question3';
                setTimeout(() => {
                    addOptionsMessage(script.question3, [script.yes, script.no]);
                }, 500);
                return;
            }
            
            // Handle status check suggestions - trigger input directly
            if (lowerSuggestion.includes('status') || lowerSuggestion.includes('check') || 
                lowerSuggestion.includes('स्थिती') || lowerSuggestion.includes('तपासायची')) {
                setTimeout(() => {
                    showGrievanceInput();
                }, 500);
                return;
            }
            
            // Handle register grievance suggestions - Reset to start
            if (lowerSuggestion.includes('register') || lowerSuggestion.includes('grievance') || 
                lowerSuggestion.includes('तक्रार') || lowerSuggestion.includes('नोंदवायची')) {
                
                chatState = 'start';
                setTimeout(() => {
                    addOptionsMessage(script.question1, [script.yes, script.no]);
                }, 500);
                return;
            }
            
            // Default response - start from beginning
            setTimeout(() => {
                addOptionsMessage(script.question1, [script.yes, script.no]);
                chatState = 'start';
            }, 500);
        }

        // PGRS Flow Logic - CORRECTED
        function handleUserChoice(optionIndex) {
            const script = PGRS_SCRIPTS[currentLanguage];
            
            switch (chatState) {
                case 'start':
                    if (optionIndex === 0) { // YES - Register grievance
                        setTimeout(() => {
                            addMessage(script.register_methods);
                            addLinksMessage('', [
                                { text: script.website_button, url: script.website_link },
                                { text: script.app_button, url: script.app_link }
                            ]);
                            setTimeout(() => {
                                addMessage(script.thank_you);
                                chatState = 'end';
                            }, 1000);
                        }, 500);
                    } else { // NO - Don't want to give feedback
                        setTimeout(() => {
                            addMessage(script.thank_you);
                            chatState = 'end';
                        }, 500);
                    }
                    break;
                
                case 'question2':
                    if (optionIndex === 0) { // YES - Want to check status
                        // In a real implementation, this would ask for Grievance ID
                        // For demo purposes, we'll show a message about the process
                        setTimeout(() => {
                            addMessage("To check your grievance status, you would need to provide your Grievance ID. This feature connects to the backend system to fetch real-time status updates.");
                            setTimeout(() => {
                                chatState = 'question3';
                                addOptionsMessage(script.question3, [script.yes, script.no]);
                            }, 1000);
                        }, 500);
                    } else { // NO - Don't want to check status
                        chatState = 'question3';
                        setTimeout(() => {
                            addOptionsMessage(script.question3, [script.yes, script.no]);
                        }, 500);
                    }
                    break;
                
                case 'question3':
                    if (optionIndex === 0) { // YES - Want to give feedback
                        setTimeout(() => {
                            addRatingMessage(script.rating_request);
                            chatState = 'awaiting_rating';
                        }, 500);
                    } else { // NO - Don't want to give feedback
                        setTimeout(() => {
                            addMessage(script.thank_you);
                            chatState = 'end';
                        }, 500);
                    }
                    break;
            }
        }

        // UI Control Functions
        function toggleChatWindow() {
            isWindowOpen = !isWindowOpen;
            elements.chatWindow.style.display = isWindowOpen ? 'flex' : 'none';
            
            if (isWindowOpen) {
                if (!currentSessionId) {
                    currentSessionId = generateSessionId();
                }
                loadQuickSuggestions();
                if (chatState === 'start' && elements.chatMessages.querySelectorAll('.message').length === 0) {
                    startConversation();
                }
            }
        }

        function startConversation() {
            const script = PGRS_SCRIPTS[currentLanguage];
            
            // Clear any existing messages and reset state
            const existingMessages = elements.chatMessages.querySelectorAll('.message');
            existingMessages.forEach(msg => msg.remove());
            
            pendingGrievanceId = '';
            chatState = 'start';
            elements.quickSuggestions.style.display = 'block';
            
            setTimeout(() => {
                addMessage(script.welcome);
                setTimeout(() => {
                    addOptionsMessage(script.question1, [script.yes, script.no]);
                }, 1000);
            }, 500);
        }

        function clearChat() {
            const messages = elements.chatMessages.querySelectorAll('.message, .status-indicator');
            messages.forEach(msg => msg.remove());
            chatState = 'start';
            selectedRating = null;
            pendingGrievanceId = '';
            currentSessionId = generateSessionId();
            elements.quickSuggestions.style.display = 'block';
            loadQuickSuggestions();
        }

        function updateLanguage(langCode) {
            currentLanguage = langCode;
            
            // Update quick suggestions
            loadQuickSuggestions();
            
            // If chat is active, inform about language change
            if (isWindowOpen && elements.chatMessages.querySelectorAll('.message').length > 0) {
                const script = PGRS_SCRIPTS[langCode];
                addMessage(`Language switched to ${langCode === 'en' ? 'English' : 'मराठी'}. Restarting conversation...`);
                setTimeout(() => {
                    startConversation();
                }, 1000);
            }
        }

        // Event Listeners
        elements.chatBubble.addEventListener('click', toggleChatWindow);
        elements.closeChat.addEventListener('click', toggleChatWindow);
        
        elements.languageSelect.addEventListener('change', (e) => {
            updateLanguage(e.target.value);
        });
        
        elements.restartBtn.addEventListener('click', () => {
            startConversation();
        });
        
        elements.clearChatBtn.addEventListener('click', () => {
            clearChat();
        });

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            console.log('PGRS ChatBot with Rating System initialized');
            currentSessionId = generateSessionId();
            loadQuickSuggestions();
        });

        console.log('PGRS ChatBot with Rating System script loaded successfully');
    </script>
</body>
</html>