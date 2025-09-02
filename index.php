<?php
// Include the API helper
require_once 'api_helper.php';

// Initialize the API client
$api = new MahaJalAPI('http://localhost:8000'); // Change this to your FastAPI server URL

// Handle language setting
$language = isset($_POST['language']) ? $_POST['language'] : (isset($_GET['lang']) ? $_GET['lang'] : 'en');
if (!in_array($language, ['en', 'mr'])) {
    $language = 'en';
}

// Initialize variables
$bot_response = '';
$user_message = '';
$error_message = '';
$api_status = $api->checkHealth();

// Handle form submission
if ($_POST && isset($_POST['user_message'])) {
    $user_message = trim($_POST['user_message']);
    
    if (!empty($user_message)) {
        // Send query to FastAPI backend
        $result = $api->sendQuery($user_message, $language);
        
        if ($result['success']) {
            $bot_response = $result['data']['reply'];
        } else {
            $error_message = 'Error: ' . $result['error'];
        }
    } else {
        $error_message = $language == 'mr' ? 'कृपया एक संदेश टाइप करा' : 'Please type a message';
    }
}

// Get suggestions for the current language
$suggestions = $api->getSuggestions($language);

// Auto-start conversation with welcome message if no previous interaction
$show_welcome = empty($_POST) && empty($_GET['lang']);
if ($show_welcome) {
    $result = $api->sendQuery('hello', $language);
    if ($result['success']) {
        $bot_response = $result['data']['reply'];
    }
}
?>

<!DOCTYPE html>
<html lang="<?php echo $language; ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo $language == 'mr' ? 'महा-जल समाधान चॅटबॉट' : 'Maha-Jal Samadhan Chatbot'; ?></title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            line-height: 1.6;
        }

        .chat-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 900px;
            min-height: 700px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            padding: 25px;
            text-align: center;
            position: relative;
        }

        .chat-header h1 {
            font-size: 1.6rem;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .chat-header p {
            opacity: 0.9;
            font-size: 0.95rem;
        }

        .status-indicator {
            position: absolute;
            top: 25px;
            right: 25px;
            display: inline-flex;
            align-items: center;
            font-size: 0.8rem;
            background: rgba(255, 255, 255, 0.1);
            padding: 5px 12px;
            border-radius: 15px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }

        .status-online {
            background-color: #4CAF50;
        }

        .status-offline {
            background-color: #f44336;
        }

        .language-selector {
            position: absolute;
            top: 25px;
            left: 25px;
        }

        .language-selector select {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 8px 12px;
            border-radius: 15px;
            font-size: 0.85rem;
            cursor: pointer;
        }

        .language-selector select option {
            background: #4CAF50;
            color: white;
        }

        .chat-messages {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            background: #f8f9fa;
            max-height: 450px;
        }

        .message {
            margin-bottom: 25px;
            display: flex;
            align-items: flex-start;
        }

        .message.user {
            justify-content: flex-end;
        }

        .message.bot {
            justify-content: flex-start;
        }

        .message-content {
            max-width: 75%;
            padding: 18px 22px;
            border-radius: 20px;
            line-height: 1.5;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .message.user .message-content {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-bottom-right-radius: 8px;
        }

        .message.bot .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        .suggestions {
            padding: 0 30px 25px;
            background: #f8f9fa;
        }

        .suggestions h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 0.95rem;
            font-weight: 600;
        }

        .suggestion-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .suggestion-btn {
            background: #e3f2fd;
            border: 1px solid #2196F3;
            color: #2196F3;
            padding: 10px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            outline: none;
        }

        .suggestion-btn:hover {
            background: #2196F3;
            color: white;
            transform: translateY(-1px);
        }

        .chat-input {
            background: white;
            padding: 25px;
            border-top: 1px solid #e0e0e0;
        }

        .input-group {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .input-group input[type="text"] {
            flex: 1;
            padding: 16px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            outline: none;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }

        .input-group input[type="text"]:focus {
            border-color: #4CAF50;
        }

        .input-group button {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 16px 28px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: transform 0.2s ease;
            min-width: 90px;
        }

        .input-group button:hover {
            transform: translateY(-2px);
        }

        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px 20px;
            margin: 15px 30px;
            border-radius: 10px;
            border-left: 4px solid #c62828;
        }

        .welcome-message {
            text-align: center;
            padding: 50px 30px;
            color: #666;
        }

        .welcome-message h2 {
            color: #4CAF50;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .welcome-message p {
            font-size: 0.95rem;
        }

        /* Make links in bot messages clickable */
        .message.bot .message-content a {
            color: #2196F3;
            text-decoration: none;
            font-weight: 500;
        }

        .message.bot .message-content a:hover {
            text-decoration: underline;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .chat-container {
                min-height: 90vh;
                max-width: 100%;
            }
            
            .message-content {
                max-width: 90%;
                padding: 15px 18px;
            }
            
            .language-selector,
            .status-indicator {
                position: static;
                margin: 8px 0;
            }
            
            .chat-header {
                text-align: left;
                padding: 20px;
            }
            
            .chat-header h1 {
                font-size: 1.3rem;
            }
            
            .chat-messages {
                padding: 20px;
            }
            
            .suggestions {
                padding: 0 20px 20px;
            }
            
            .chat-input {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="language-selector">
                <form method="GET" style="display: inline;">
                    <select name="lang" onchange="this.form.submit()">
                        <option value="en" <?php echo $language == 'en' ? 'selected' : ''; ?>>English</option>
                        <option value="mr" <?php echo $language == 'mr' ? 'selected' : ''; ?>>मराठी</option>
                    </select>
                </form>
            </div>
            
            <div class="status-indicator">
                <div class="status-dot <?php echo $api_status ? 'status-online' : 'status-offline'; ?>"></div>
                <?php echo $api_status ? ($language == 'mr' ? 'ऑनलाइन' : 'Online') : ($language == 'mr' ? 'ऑफलाइन' : 'Offline'); ?>
            </div>
            
            <h1><?php echo $language == 'mr' ? 'महा-जल समाधान' : 'Maha-Jal Samadhan'; ?></h1>
            <p><?php echo $language == 'mr' ? 'सार्वजनिक तक्रार निवारण प्रणाली - चॅटबॉट' : 'Public Grievance Redressal System - Chatbot'; ?></p>
        </div>

        <div class="chat-messages">
            <?php if (!empty($error_message)): ?>
                <div class="error-message">
                    <?php echo htmlspecialchars($error_message); ?>
                </div>
            <?php endif; ?>

            <?php if (!empty($user_message)): ?>
                <div class="message user">
                    <div class="message-content">
                        <?php echo nl2br(htmlspecialchars($user_message)); ?>
                    </div>
                </div>
            <?php endif; ?>

            <?php if (!empty($bot_response)): ?>
                <div class="message bot">
                    <div class="message-content">
                        <?php 
                        // Make URLs clickable in bot responses
                        $response_with_links = preg_replace(
                            '/(https?:\/\/[^\s]+)/',
                            '<a href="$1" target="_blank">$1</a>',
                            htmlspecialchars($bot_response)
                        );
                        echo nl2br($response_with_links); 
                        ?>
                    </div>
                </div>
            <?php endif; ?>

            <?php if (empty($user_message) && empty($bot_response) && !$show_welcome): ?>
                <div class="welcome-message">
                    <h2><?php echo $language == 'mr' ? 'आपले स्वागत आहे!' : 'Welcome!'; ?></h2>
                    <p><?php echo $language == 'mr' ? 'आपली तक्रार नोंदविण्यासाठी किंवा माहिती मिळविण्यासाठी मला संदेश पाठवा.' : 'Send me a message to register your grievance or get information.'; ?></p>
                </div>
            <?php endif; ?>
        </div>

        <?php if (!empty($suggestions)): ?>
            <div class="suggestions">
                <h3><?php echo $language == 'mr' ? 'सुचविलेले विकल्प:' : 'Suggested Options:'; ?></h3>
                <div class="suggestion-buttons">
                    <?php foreach ($suggestions as $suggestion): ?>
                        <button class="suggestion-btn" onclick="document.getElementById('user_input').value='<?php echo addslashes($suggestion); ?>'; document.getElementById('chat-form').submit();">
                            <?php echo htmlspecialchars($suggestion); ?>
                        </button>
                    <?php endforeach; ?>
                </div>
            </div>
        <?php endif; ?>

        <div class="chat-input">
            <form method="POST" id="chat-form">
                <input type="hidden" name="language" value="<?php echo $language; ?>">
                <div class="input-group">
                    <input 
                        type="text" 
                        name="user_message" 
                        id="user_input"
                        placeholder="<?php echo $language == 'mr' ? 'आपला संदेश इथे टाइप करा...' : 'Type your message here...'; ?>" 
                        required
                        autocomplete="off"
                        maxlength="500"
                    >
                    <button type="submit">
                        <?php echo $language == 'mr' ? 'पाठवा' : 'Send'; ?>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Auto-focus on input field
        document.getElementById('user_input').focus();
        
        // Handle form submission with Enter key
        document.getElementById('user_input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('chat-form').submit();
            }
        });
        
        // Auto-scroll to bottom of messages
        const messagesContainer = document.querySelector('.chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Auto-clear input after suggestion click
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                setTimeout(() => {
                    document.getElementById('user_input').value = '';
                }, 100);
            });
        });
    </script>
</body>
</html>
