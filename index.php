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

        .rating-container {
            display: flex;
            gap: 8px;
            margin: 10px 0;
            justify-content: center;
        }

        .rating-button {
            background: linear-gradient(135deg, #f1f3f4 0%, #e8eaed 100%);
            border: 2px solid #e1e8ed;
            padding: 10px 16px;
            border-radius: 50%;
            font-size: 14px;
            font-weight: 600;
            color: #5f6368;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .rating-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
        }

        .rating-button.selected {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
            transform: translateY(-1px);
        }

        .rating-button:active {
            transform: translateY(-1px);
        }

        .submit-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 10px 20px;
            border-radius: 16px;
            font-size: 12px;
            color: white;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-top: 10px;
        }

        .submit-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        }

        .submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            background: #ccc;
        }

        .submit-btn:active:not(:disabled) {
            transform: translateY(-1px);
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
        <h1>Welcome to the WSSD JJM Chatbot</h1>
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
                        <h3>Maha-Jal Samadhan PGRS</h3>
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
        // PGRS Script Configuration
        const PGRS_SCRIPTS = {
            en: {
                welcome: "Welcome to the Maha-Jal Samadhan Public Grievance Redressal System.",
                question1: "Would you like to register a Grievance on the Maha-Jal Samadhan Public Grievance Redressal System?",
                question2: "Has a Grievance already been registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
                question21: "Would you like to check the status of the grievance which you have registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
                question22: "Would you like to provide feedback regarding the resolution of your grievance addressed through the Maha-Jal Samadhan Public Grievance Redressal System?",
                register_methods: "You can register your Grievance on the Maha-Jal Samadhan Public Grievance Redressal System through two methods:",
                website_method: "1. Registering a Grievance via the Maha-Jal Samadhan Website",
                website_link: "https://mahajalsamadhan.in/log-grievance",
                app_method: "2. Registering a Grievance via the Maha-Jal Samadhan Mobile App",
                app_link: "https://play.google.com/store/apps/details?id=in.mahajalsamadhan.user&pli=1",
                grievance_id_prompt: "Please enter your Grievance ID (For example: \"G-12safeg7678\")",
                invalid_grievance_id: "The Grievance ID you have entered is incorrect or invalid. Please enter the correct Grievance ID to proceed.",
                status_prefix: "The current status of your Grievance is as follows:",
                rating_prompt: "With reference to the resolution of your grievance on the Maha-Jal Samadhan Public Grievance Redressal System, how would you rate the quality of service on a scale of 1 to 5, where: 1 = Unsatisfactory and 5 = Satisfactory?",
                rating_request: "Please provide your rating between 1 and 5:",
                invalid_input: "The information you have entered is invalid. Please try again.",
                thank_you: "Thank you for using the Maha-Jal Samadhan Public Grievance Redressal System.",
                yes: "YES",
                no: "NO",
                website_button: "Register via Website",
                app_button: "Download Mobile App",
                suggestions_title: "Quick Suggestions:",
                suggestions: [
                    "I want to register a grievance",
                    //"Would you like to register a Grievance on the Maha-Jal Samadhan Public Grievance Redressal System?",
                    //"Has a Grievance already been registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
                    //"Would you like to check the status of the grievance which you have registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
                    //"Would you like to provide feedback regarding the resolution of your grievance addressed through the Maha-Jal Samadhan Public Grievance Redressal System?"
                ]
            },
            mr: {
                welcome: "नमस्कार, महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर आपले स्वागत आहे.",
                question1: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर आपण तक्रार नोंदू इच्छिता का?",
                question2: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर तक्रार नोंदविण्यात आलेली आहे का?",
                question21: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर आपण केलेल्या तक्रारीची स्थिती पाहू इच्छिता का?",
                question22: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीद्वारे सोडविण्यात आलेल्या आपल्या तक्रारीच्या निराकरणाबाबत अभिप्राय देऊ इच्छिता का?",
                register_methods: "आपण 'महा-जल समाधान' सार्वजनिक तक्रार निवारण प्रणालीवर आपली तक्रार दोन पद्धतींनी नोंदवू शकता:",
                website_method: "१. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर वेबसाईटद्वारे तक्रार नोंदणी",
                website_link: "https://mahajalsamadhan.in/log-grievance",
                app_method: "२. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर मोबाईल अॅपद्वारे तक्रार नोंदणी",
                app_link: "https://play.google.com/store/apps/details?id=in.mahajalsamadhan.user&pli=1",
                grievance_id_prompt: "कृपया आपण आपल्या तक्रारीचा \"Grievance ID\" म्हणजेच तक्रार नोंदणी क्रमांक दाखल/नमूद करा. (उदाहरणार्थ - \"G-12safeg7678\")",
                invalid_grievance_id: "आपण आपल्या तक्रारीचा \"Grievance ID\" म्हणजेच तक्रार नोंदणी क्रमांक चुकीचा दाखल केला आहे. कृपया योग्य \"Grievance ID\" म्हणजेच तक्रार नोंदणी क्रमांक दाखल/नमूद करा",
                status_prefix: "आपल्या तक्रारीची सद्यस्थिती पुढीलप्रमाणे आहे:",
                rating_prompt: "महा-जल समाधान' सार्वजनिक तक्रार निवारण प्रणालीवर आपल्या तक्रारीच्या निराकरणासंदर्भात, सेवा गुणवत्तेच्या दृष्टीने आपण १ ते ५ या श्रेणीमध्ये किती गुण देऊ इच्छिता ?१ म्हणजे 'असमाधानकारक' आणि ५ म्हणजे 'समाधानकारक'.",
                rating_request: "कृपया आपल्यादवारे देण्यात आलेले गुण १ ते ५ मध्ये देण्यात यावे",
                invalid_input: "आपण दिलेली माहिती अवैध आहे. कृपया पुन्हा प्रयत्न करा.",
                thank_you: "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीचा वापर केल्याबद्दल आपले धन्यवाद.",
                yes: "होय",
                no: "नाही",
                website_button: "वेबसाईटवरून नोंदणी करा",
                app_button: "मोबाईल अँप डाउनलोड करा",
                suggestions_title: "त्वरित सूचना:",
                suggestions: [
                    "मला तक्रार नोंदवायची आहे",
                    //"महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये आपण तक्रार नोंदवू इच्छिता का?",
                    //"महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदविण्यात आलेली तक्रार आहे का?",
                    //"आपण नोंदवलेल्या तक्रारीची स्थिती तपासू इच्छिता का?",
                    //"आपल्या तक्रारीच्या निराकरणाबाबत अभिप्राय द्याल का?"
                ]
            }
        };

        // State Management
        let currentLanguage = 'en';
        let chatState = 'start';
        let pendingGrievanceId = '';
        let selectedRating = null;
        let isWindowOpen = false;

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

        function addInputMessage(content, inputType = 'text') {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            
            let inputHtml = '';
            if (inputType === 'rating') {
                inputHtml = `
                    <div class="rating-container">
                        ${[1,2,3,4,5].map(num => 
                            `<button class="rating-button" data-rating="${num}">${num}</button>`
                        ).join('')}
                    </div>
                    <button class="submit-btn" id="submitRating" disabled>Submit Rating</button>
                `;
            } else {
                inputHtml = `
                    <input type="text" class="input-field" id="grievanceInput" placeholder="Enter Grievance ID" maxlength="20">
                    <button class="submit-btn" id="submitGrievanceId">Submit</button>
                `;
            }
            
            messageDiv.innerHTML = `
                <div class="message-content">
                    ${content}
                    ${inputHtml}
                    <div class="message-time">${getCurrentTime()}</div>
                </div>
            `;
            
            elements.chatMessages.insertBefore(messageDiv, elements.typingIndicator);
            scrollToBottom();
            
            if (inputType === 'rating') {
                setupRatingButtons(messageDiv);
            } else {
                setupGrievanceIdInput(messageDiv);
            }
        }

        function setupRatingButtons(container) {
            const ratingButtons = container.querySelectorAll('.rating-button');
            const submitBtn = container.querySelector('#submitRating');
            
            ratingButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    ratingButtons.forEach(b => b.classList.remove('selected'));
                    e.target.classList.add('selected');
                    selectedRating = parseInt(e.target.dataset.rating);
                    submitBtn.disabled = false;
                });
            });
            
            submitBtn.addEventListener('click', () => {
                if (selectedRating) {
                    addMessage(`Rating: ${selectedRating}`, true);
                    handleRatingSubmission(selectedRating);
                }
            });
        }

        function setupGrievanceIdInput(container) {
            const input = container.querySelector('#grievanceInput');
            const submitBtn = container.querySelector('#submitGrievanceId');
            
            input.addEventListener('input', () => {
                submitBtn.disabled = input.value.trim().length === 0;
            });
            
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && input.value.trim()) {
                    submitBtn.click();
                }
            });
            
            submitBtn.addEventListener('click', () => {
                const grievanceId = input.value.trim();
                if (grievanceId) {
                    addMessage(`Grievance ID: ${grievanceId}`, true);
                    handleGrievanceIdSubmission(grievanceId);
                }
            });
            
            setTimeout(() => input.focus(), 100);
        }

        function loadQuickSuggestions() {
            const script = PGRS_SCRIPTS[currentLanguage];
            elements.suggestionsTitle.textContent = script.suggestions_title;
            
            elements.suggestionsGrid.innerHTML = '';
            
            // Show first 6 suggestions to avoid overcrowding
            const suggestionsToShow = script.suggestions.slice(0, 6);
            
            suggestionsToShow.forEach(suggestion => {
                const suggestionBtn = document.createElement('button');
                suggestionBtn.className = 'quick-suggestion-btn';
                suggestionBtn.textContent = suggestion;
                suggestionBtn.addEventListener('click', () => {
                    handleQuickSuggestion(suggestion);
                });
                elements.suggestionsGrid.appendChild(suggestionBtn);
            });
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

        function processQuickSuggestion(suggestion) {
            const script = PGRS_SCRIPTS[currentLanguage];
            const lowerSuggestion = suggestion.toLowerCase();
            
            // Handle greetings
            if (lowerSuggestion.includes('hello') || lowerSuggestion.includes('नमस्कार')) {
                addMessage(script.welcome);
                setTimeout(() => {
                    addOptionsMessage(script.question1, [script.yes, script.no]);
                    chatState = 'start';
                }, 1000);
                return;
            }
            
            // Handle yes/no responses
            if (lowerSuggestion === 'yes' || lowerSuggestion === 'होय') {
                handleUserChoice(0); // YES option
                return;
            }
            
            if (lowerSuggestion === 'no' || lowerSuggestion === 'नाही') {
                handleUserChoice(1); // NO option
                return;
            }
            
            // Handle specific questions as if starting conversation
            if (lowerSuggestion.includes('register') || lowerSuggestion.includes('grievance') || 
                lowerSuggestion.includes('तक्रार') || lowerSuggestion.includes('नोंदव')) {
                
                chatState = 'start';
                addOptionsMessage(script.question1, [script.yes, script.no]);
                return;
            }
            
            // For other suggestions that are questions, start the conversation
            if (lowerSuggestion.includes('?') || lowerSuggestion.includes('का?')) {
                chatState = 'start';
                addMessage(script.welcome);
                setTimeout(() => {
                    addOptionsMessage(script.question1, [script.yes, script.no]);
                }, 1000);
                return;
            }
            
            // Default response for unrecognized suggestions
            addMessage(script.welcome);
            setTimeout(() => {
                addOptionsMessage(script.question1, [script.yes, script.no]);
                chatState = 'start';
            }, 1000);
        }

        // PGRS Flow Logic
        function handleUserChoice(optionIndex) {
            const script = PGRS_SCRIPTS[currentLanguage];
            
            switch (chatState) {
                case 'start':
                    if (optionIndex === 0) { // YES - Register grievance
                        chatState = 'register';
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
                    } else { // NO - Already registered
                        chatState = 'already_registered';
                        setTimeout(() => {
                            addOptionsMessage(script.question2, [script.yes, script.no]);
                        }, 500);
                    }
                    break;
                
                case 'already_registered':
                    if (optionIndex === 0) { // YES - Has grievance registered
                        chatState = 'check_or_feedback';
                        setTimeout(() => {
                            addOptionsMessage(script.question21, [script.yes, script.no]);
                            chatState = 'check_status';
                        }, 500);
                    } else { // NO - Doesn't have grievance
                        setTimeout(() => {
                            addMessage(script.thank_you);
                            chatState = 'end';
                        }, 500);
                    }
                    break;
                
                case 'check_status':
                    if (optionIndex === 0) { // YES - Check status
                        setTimeout(() => {
                            addInputMessage(script.grievance_id_prompt, 'text');
                            chatState = 'awaiting_grievance_id';
                        }, 500);
                    } else { // NO - Don't check status
                        setTimeout(() => {
                            addOptionsMessage(script.question22, [script.yes, script.no]);
                            chatState = 'feedback_choice';
                        }, 500);
                    }
                    break;
                
                case 'feedback_choice':
                    if (optionIndex === 0) { // YES - Give feedback
                        setTimeout(() => {
                            addMessage(script.rating_prompt);
                            addInputMessage(script.rating_request, 'rating');
                            chatState = 'awaiting_rating';
                        }, 500);
                    } else { // NO - No feedback
                        setTimeout(() => {
                            addMessage(script.thank_you);
                            chatState = 'end';
                        }, 500);
                    }
                    break;
            }
        }

        function handleGrievanceIdSubmission(grievanceId) {
            const script = PGRS_SCRIPTS[currentLanguage];
            
            // Simple validation - check if it looks like a grievance ID
            const grievanceIdPattern = /^G-[A-Za-z0-9]+$/;
            
            if (grievanceIdPattern.test(grievanceId)) {
                // Valid format - simulate status check
                setTimeout(() => {
                    addMessage(script.status_prefix);
                    addMessage("Status: Under Review - Your grievance is being processed by the concerned department. Expected resolution time: 7-10 working days.", false);
                    setTimeout(() => {
                        addMessage(script.thank_you);
                        chatState = 'end';
                    }, 1000);
                }, 500);
            } else {
                // Invalid format
                setTimeout(() => {
                    addMessage(script.invalid_grievance_id);
                    addInputMessage(script.grievance_id_prompt, 'text');
                }, 500);
            }
        }

        function handleRatingSubmission(rating) {
            const script = PGRS_SCRIPTS[currentLanguage];
            
            if (rating >= 1 && rating <= 5) {
                setTimeout(() => {
                    addMessage(`Thank you for rating our service ${rating}/5. Your feedback helps us improve our services.`);
                    setTimeout(() => {
                        addMessage(script.thank_you);
                        chatState = 'end';
                    }, 1000);
                }, 500);
            } else {
                setTimeout(() => {
                    addMessage(script.invalid_input);
                    addInputMessage(script.rating_request, 'rating');
                }, 500);
            }
        }

        // UI Control Functions
        function toggleChatWindow() {
            isWindowOpen = !isWindowOpen;
            elements.chatWindow.style.display = isWindowOpen ? 'flex' : 'none';
            
            if (isWindowOpen) {
                loadQuickSuggestions();
                if (chatState === 'start') {
                    startConversation();
                }
            }
        }

        function startConversation() {
            const script = PGRS_SCRIPTS[currentLanguage];
            
            // Clear any existing messages
            const existingMessages = elements.chatMessages.querySelectorAll('.message');
            existingMessages.forEach(msg => msg.remove());
            
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
            
            // Save language preference
            try {
                localStorage.setItem('pgrs_language', langCode);
            } catch (e) {
                console.warn('Could not save language preference:', e);
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
            console.log('PGRS ChatBot initialized');
            
            // Load saved language preference
            try {
                const savedLanguage = localStorage.getItem('pgrs_language');
                if (savedLanguage && PGRS_SCRIPTS[savedLanguage]) {
                    currentLanguage = savedLanguage;
                    elements.languageSelect.value = savedLanguage;
                }
            } catch (e) {
                console.warn('Could not load language preference:', e);
            }
            
            // Load initial suggestions
            loadQuickSuggestions();
        });

        console.log('PGRS ChatBot script loaded successfully');
    </script>
</body>
</html>