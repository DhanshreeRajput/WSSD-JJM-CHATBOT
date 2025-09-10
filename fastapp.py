from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, ValidationError
from typing import Optional
import time
import os
import logging
import re
import csv
import io
from datetime import datetime
from contextlib import asynccontextmanager

# Import database functions from our separate module
from database import (
    db_manager,
    init_database,
    close_database,
    get_grievance_status,
    search_user_grievances,
    get_db_statistics,
    test_db_connection,
    get_db_info
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Configuration constants
RATE_LIMIT_SECONDS = 2
SYSTEM_STATUS = {
    "startup_time": time.time(),
    "total_queries": 0,
    "successful_queries": 0,
    "failed_queries": 0,
    "last_error": None,
    "supported_languages": ["en", "mr"],
    "database_connected": False
}

class QueryRequest(BaseModel):
    input_text: str
    session_id: Optional[str] = None
    language: str = "en"

    @field_validator('input_text')
    @classmethod
    def validate_input_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Input text cannot be empty')
        if len(v) > 500:
            raise ValueError('Input text too long (max 500 characters)')
        return v.strip()

    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        supported_languages = ['en', 'mr']
        if v not in supported_languages:
            raise ValueError(f'Language must be one of: {supported_languages}')
        return v

class RatingRequest(BaseModel):
    rating: int
    session_id: Optional[str] = None
    language: str = "en"
    grievance_id: Optional[str] = None
    feedback_text: Optional[str] = None

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v not in [1, 2, 3, 4, 5]:
            raise ValueError('Rating must be between 1 and 5')
        return v

class GrievanceStatusRequest(BaseModel):
    grievance_id: str
    language: str = "en"

    @field_validator('grievance_id')
    @classmethod
    def validate_grievance_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Grievance ID cannot be empty')
        return v.strip()

class UserSearchRequest(BaseModel):
    user_identifier: str
    language: str = "en"

    @field_validator('user_identifier')
    @classmethod
    def validate_user_identifier(cls, v):
        if not v or not v.strip():
            raise ValueError('User identifier cannot be empty')
        return v.strip()

# Global variables
CHAT_HISTORY = {}
RATE_LIMIT_TRACKER = {}
USER_SESSION_STATE = {}
RATINGS_DATA = []  # Store ratings data for CSV export

# Rating labels mapping - Fixed Marathi characters
RATING_LABELS = {
    "en": {
        1: "Poor",
        2: "Fair",
        3: "Good",
        4: "Very Good",
        5: "Excellent"
    },
    "mr": {
        1: "खराब",
        2: "सामान्य",
        3: "चांगले",
        4: "खूप चांगले",
        5: "उत्कृष्ट"
    }
}

# Updated Maha-Jal Knowledge Base with proper status check flow
MAHA_JAL_KNOWLEDGE_BASE = {
    "en": {
        "welcome_message": "Welcome to Public Grievance Redressal System portal AI-ChatBot.",
        "initial_question": "Would you like to register a Grievance on the Maha-Jal Samadhan Public Grievance Redressal System?",
        "check_existing_question": "Has a Grievance already been registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
        "status_check_question": "Would you like to check the status of the grievance which you have registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
        "grievance_id_prompt": "Please enter your Grievance ID (For example: \"G-12safeg7678\")",
        "feedback_question": "Would you like to provide feedback regarding the resolution of your grievance addressed through the Maha-Jal Samadhan Public Grievance Redressal System?",
        "rating_question": "Please rate your experience with the Maha-Jal Samadhan Public Grievance Redressal System:",
        "rating_request": "Rate from 1 (Poor) to 5 (Excellent)",
        "invalid_rating": "The information you have entered is invalid. Please try again.",
        "rating_thank_you": "Thank you for your feedback. Your rating has been recorded.",
        "grievance_not_found": "Sorry, no grievance found with the provided ID. Please check your Grievance ID and try again.",
        "database_error": "Unable to fetch grievance information at the moment. Please try again later.",
        "invalid_grievance_id": "Please provide a valid Grievance ID in the correct format (For example: \"G-12safeg7678\")",
        "options": {"yes": "YES", "no": "NO"},
        "yes_response": {
            "intro": "You can register your Grievance on the Maha-Jal Samadhan Public Grievance Redressal System through two methods:",
            "method1": {
                "title": "1. Registering a Grievance via the Maha-Jal Samadhan Website",
                "description": "You can register your Grievance by clicking the link below and visiting the official website:",
                "link": "Link: https://mahajalsamadhan.in/log-grievance"
            },
            "method2": {
                "title": "2. Registering a Grievance via the Maha-Jal Samadhan Mobile App",
                "description": "You can download the mobile application using the link below and submit your Grievance through the app:",
                "link": "Download Link: https://play.google.com/store/apps/details?id=in.mahajalsamadhan.user&pli=1"
            }
        },
        "no_response": "Thank you for using the Maha-Jal Samadhan Public Grievance Redressal System.",
        "help_text": "Please type 'YES' or 'NO' to proceed with your query.",
        "track_grievance_help": "You can also track your grievance status at: https://mahajalsamadhan.in/view-grievance"
    },
    "mr": {
        "welcome_message": "नमस्कार, सार्वजनिक तक्रार निवारण प्रणाली पोर्टल एआय-चॅटबॉटमध्ये आपले स्वागत आहे.",
        "initial_question": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये आपण तक्रार नोंदवू इच्छिता का?",
        "check_existing_question": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदविण्यात आलेली तक्रार आहे का?",
        "status_check_question": "आपण महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदवलेल्या तक्रारीची स्थिती तपासू इच्छिता का?",
        "grievance_id_prompt": "कृपया आपला तक्रार क्रमांक प्रविष्ट करा (उदाहरणार्थ: \"G-12safeg7678\")",
        "feedback_question": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीद्वारे सोडविण्यात आलेल्या आपल्या तक्रारीच्या निराकरणाबाबत अभिप्राय द्यायला इच्छिता का?",
        "rating_question": "कृपया महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीच्या अनुभवाला रेटिंग द्या:",
        "rating_request": "१ (खराब) ते ५ (उत्कृष्ट) पर्यंत रेटिंग द्या",
        "invalid_rating": "आपण दिलेली माहिती अवैध आहे. कृपया पुन्हा प्रयत्न करा.",
        "rating_thank_you": "आपल्या अभिप्रायाबद्दल धन्यवाद. आपले रेटिंग नोंदवले गेले आहे.",
        "grievance_not_found": "माफ करा, दिलेल्या क्रमांकासह कोणतीही तक्रार आढळली नाही. कृपया आपला तक्रार क्रमांक तपासा आणि पुन्हा प्रयत्न करा.",
        "database_error": "सध्या तक्रार माहिती मिळवता येत नाही. कृपया नंतर प्रयत्न करा.",
        "invalid_grievance_id": "कृपया योग्य तक्रार क्रमांक प्रदान करा (उदाहरणार्थ: \"G-12safeg7678\")",
        "options": {"yes": "होय", "no": "नाही"},
        "yes_response": {
            "intro": "आपण 'महा-जल समाधान' सार्वजनिक तक्रार निवारण प्रणालीमध्ये आपली तक्रार दोन पद्धतींनी नोंदवू शकता:",
            "method1": {
                "title": "१. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये वेबसाईटद्वारे तक्रार नोंदणीसाठी आपण खालील लिंकवर क्लिक करून वेबसाईटवर तक्रार नोंदवू शकता:",
                "description": "लिंक -",
                "link": "https://mahajalsamadhan.in/log-grievance"
            },
            "method2": {
                "title": "२. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये मोबाईल अॅपद्वारे तक्रार नोंदणी",
                "description": "आपण खालील लिंकद्वारे मोबाइल अॅप डाउनलोड करून तक्रार नोंदवू शकता:",
                "link": "https://play.google.com/store/apps/details?id=in.mahajalsamadhan.user&pli=1"
            }
        },
        "no_response": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीचा वापर केल्याबद्दल आपले धन्यवाद.",
        "help_text": "कृपया 'होय' किंवा 'नाही' टाइप करून आपल्या प्रश्नासह पुढे जा.",
        "track_grievance_help": "आपण आपल्या तक्रारीची स्थिती येथे देखील तपासू शकता: https://mahajalsamadhan.in/view-grievance"
    }
}

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import random
    adjectives = ["sharp", "sleepy", "fluffy", "dazzling", "crazy", "bold", "happy", "silly"]
    animals = ["lion", "swan", "tiger", "elephant", "zebra", "giraffe", "panda", "koala"]
    return f"{random.choice(adjectives)}_{random.choice(animals)}_{os.urandom(2).hex()}_{int(time.time())}"

def add_to_chat_history(session_id: str, user_msg: str, bot_msg: str, language: str = "en"):
    """Add message to chat history with language support"""
    try:
        if session_id not in CHAT_HISTORY:
            CHAT_HISTORY[session_id] = []
        CHAT_HISTORY[session_id].insert(0, {
            "user": user_msg,
            "assistant": bot_msg,
            "language": language,
            "timestamp": time.strftime("%H:%M:%S"),
            "session_id": session_id,
            "created_at": time.time()
        })
        CHAT_HISTORY[session_id] = CHAT_HISTORY[session_id][:50]
    except Exception as e:
        logger.error(f"Failed to add to chat history: {e}")

def save_rating_data(rating: int, session_id: str, language: str, grievance_id: str = None, feedback_text: str = None):
    """Save rating data for CSV export with proper UTF-8 handling"""
    try:
        # Create ratings directory if it doesn't exist
        ratings_dir = os.path.join(os.path.dirname(__file__), 'ratings_data')
        os.makedirs(ratings_dir, exist_ok=True)
        
        # Prepare CSV file path
        csv_path = os.path.join(ratings_dir, 'ratings_log.csv')
        
        # Prepare rating entry
        rating_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": session_id,
            "rating": rating,
            "rating_label": RATING_LABELS[language][rating],
            "language": language,
            "grievance_id": grievance_id or "N/A",
            "feedback_text": feedback_text or "N/A",
            "ip_address": "N/A"  # Can be extended later to capture real IP
        }
        
        # Append to CSV file
        is_new_file = not os.path.exists(csv_path)
        
        with open(csv_path, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=rating_entry.keys())
            
            # Write headers if this is a new file
            if is_new_file:
                writer.writeheader()
                
            writer.writerow(rating_entry)
            
        # Store in memory and log
        RATINGS_DATA.append(rating_entry)
        logger.info(f"Rating saved successfully: {rating}/5 ({RATING_LABELS[language][rating]}) for session {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving rating data: {e}")
        return False

def detect_greeting(text: str) -> tuple[bool, str]:
    """Detect greeting intent and return a normalized key"""
    try:
        t = text.strip().lower()
        t = re.sub(r"[!.,🙂🙏✨⭐️]+", "", t)
        patterns = [
            (r"\bgood\s*morning\b|\bशुभ\s*सकाळ\b", "good_morning"),
            (r"\bgood\s*afternoon\b|\bशुभ\s*दुपार\b", "good_afternoon"),
            (r"\bgood\s*evening\b|\bशुभ\s*संध्याकाळ\b", "good_evening"),
            (r"\bhello\b|\bhey+\b|\bhii+\b|\bhi\b|\bनमस्ते\b|\bनमस्कार\b|\bहॅलो\b|\bहेलो\b|\bहाय\b", "hello"),
            (r"\bgood\s*night\b|\bशुभ\s*रात्री\b", "good_night"),
        ]
        for regex, key in patterns:
            if re.search(regex, t):
                return True, key
        return False, ""
    except Exception:
        return False, ""

def detect_grievance_id(text: str) -> Optional[str]:
    """Detect potential grievance ID in text - Updated for Maha-Jal Samadhan format"""
    # Updated patterns for Maha-Jal Samadhan format
    patterns = [
        r'\b([GgRr]-[a-zA-Z0-9]+)\b',  # G-12safeg7678 or GR-12345abc
        r'\b([GgRr][0-9a-zA-Z]+)\b',   # G12345abc or GR12345abc
        r'\b(MJS-[0-9a-zA-Z]+)\b',     # MJS-12345 (if they use this prefix)
        r'\b([0-9]{6,})\b'             # At least 6 digits
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None

def validate_grievance_id_format(grievance_id: str) -> bool:
    """Validate if the grievance ID matches expected Maha-Jal Samadhan format"""
    if not grievance_id:
        return False
    
    # Check for various valid formats
    valid_patterns = [
        r'^[GgRr]-[a-zA-Z0-9]{6,}$',  # G-12safeg7678
        r'^[GgRr][0-9a-zA-Z]{6,}$',   # G12safeg7678
        r'^MJS-[0-9a-zA-Z]{6,}$',     # MJS-123456
        r'^[0-9]{6,}$'                # 123456789
    ]
    for pattern in valid_patterns:
        if re.match(pattern, grievance_id.strip()):
            return True
    return False

def detect_exact_status_question(text: str, language: str) -> bool:
    """Detect the exact status check question from suggestions - FIXED VERSION"""
    text_lower = text.lower().strip()
    
    if language == "en":
        # Match various forms of the status check question
        status_patterns = [
            "would you like to check the status of your grievance"
        ]
        return any(pattern in text_lower for pattern in status_patterns)
    else:  # Marathi
        status_patterns = [
            "आपण महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदवलेल्या तक्रारीची स्थिती तपासू इच्छिता का",
            "तक्रारीची स्थिती तपासू इच्छिता का",
            "स्थिती तपासू इच्छिता का",
            "तक्रारीची स्थिती"
        ]
        return any(pattern in text for pattern in status_patterns)

def greeting_reply(language: str, key: str) -> str:
    """Return a specific greeting reply per detected key and language"""
    replies = {
        'en': {
            'good_morning': "Good Morning! " + MAHA_JAL_KNOWLEDGE_BASE["en"]["welcome_message"],
            'good_afternoon': "Good Afternoon! " + MAHA_JAL_KNOWLEDGE_BASE["en"]["welcome_message"],
            'good_evening': "Good Evening! " + MAHA_JAL_KNOWLEDGE_BASE["en"]["welcome_message"],
            'good_night': "Good Night! " + MAHA_JAL_KNOWLEDGE_BASE["en"]["welcome_message"],
            'hello': "Hello! " + MAHA_JAL_KNOWLEDGE_BASE["en"]["welcome_message"],
        },
        'mr': {
            'good_morning': "शुभ सकाळ! " + MAHA_JAL_KNOWLEDGE_BASE["mr"]["welcome_message"],
            'good_afternoon': "शुभ दुपार! " + MAHA_JAL_KNOWLEDGE_BASE["mr"]["welcome_message"],
            'good_evening': "शुभ संध्याकाळ! " + MAHA_JAL_KNOWLEDGE_BASE["mr"]["welcome_message"],
            'good_night': "शुभ रात्री! " + MAHA_JAL_KNOWLEDGE_BASE["mr"]["welcome_message"],
            'hello': MAHA_JAL_KNOWLEDGE_BASE["mr"]["welcome_message"],
        }
    }
    return replies.get(language, replies['en']).get(key, replies.get(language, replies['en'])['hello'])

def detect_yes_no_response(text: str, language: str) -> str:
    """Detect yes/no responses in both languages"""
    text = text.strip().lower()
    yes_patterns_en = [r'\byes\b', r'\by\b', r'\byeah\b', r'\byep\b']
    no_patterns_en = [r'\bno\b', r'\bn\b', r'\bnope\b']
    yes_patterns_mr = [r'\bहोय\b', r'\bहो\b']
    no_patterns_mr = [r'\bनाही\b', r'\bना\b']

    for pattern in yes_patterns_en + yes_patterns_mr:
        if re.search(pattern, text):
            return "yes"
    for pattern in no_patterns_en + no_patterns_mr:
        if re.search(pattern, text):
            return "no"
    return "unknown"

def format_simple_grievance_status(grievance_data: dict, language: str) -> str:
    """Format grievance status data into a readable message"""
    if not grievance_data:
        return "Grievance not found" if language == "en" else "तक्रार आढळली नाही"
    
    logger.info(f"Formatting grievance data: {grievance_data}")
    
    # Format dates
    submitted_date = grievance_data['grievance_logged_date'].strftime('%d-%b-%Y') if grievance_data.get('grievance_logged_date') else 'Not available'
    resolved_date = grievance_data['resolved_date'].strftime('%d-%b-%Y') if grievance_data.get('resolved_date') else None
    
    if language == "en":
        status_message = f"""The current status of your Grievance is as follows:
Grievance ID: {grievance_data['grievance_id']}
Status: {grievance_data['grievance_status']}
Submitted: {submitted_date}
Category: {grievance_data.get('grievance_name', 'Not specified')}
Department: {grievance_data.get('organization_name', 'Not specified')}"""

        # Add location details if available
        if grievance_data.get('district_name'):
            status_message += f"\nDistrict: {grievance_data['district_name']}"
        if grievance_data.get('block_name'):
            status_message += f"\nBlock: {grievance_data['block_name']}"
        if grievance_data.get('grampanchayat_name'):
            status_message += f"\nGram Panchayat: {grievance_data['grampanchayat_name']}"
        
        # Add resolution information if resolved
        if resolved_date:
            status_message += f"\nResolved on: {resolved_date}"
            if grievance_data.get('resolved_user_name'):
                status_message += f"\nResolved by: {grievance_data['resolved_user_name']}"
    else:
        # Marathi version
        status_message = f"""आपल्या तक्रारीची सद्यस्थिती खालीलप्रमाणे आहे:
तक्रार क्रमांक: {grievance_data['grievance_id']}
स्थिती: {grievance_data['grievance_status']}
दाखल दिनांक: {submitted_date}
श्रेणी: {grievance_data.get('grievance_name', 'निर्दिष्ट नाही')}
विभाग: {grievance_data.get('organization_name', 'निर्दिष्ट नाही')}"""

        if grievance_data.get('district_name'):
            status_message += f"\nजिल्हा: {grievance_data['district_name']}"
        if grievance_data.get('block_name'):
            status_message += f"\nतालुका: {grievance_data['block_name']}"
        if grievance_data.get('grampanchayat_name'):
            status_message += f"\nग्रामपंचायत: {grievance_data['grampanchayat_name']}"
            
        if resolved_date:
            status_message += f"\nनिराकरण दिनांक: {resolved_date}"
            if grievance_data.get('resolved_user_name'):
                status_message += f"\nनिराकरण करणारे: {grievance_data['resolved_user_name']}"
        
    # Format the submitted date
    submitted_date = grievance_data['submitted_date'].strftime('%d-%b-%Y') if grievance_data.get('submitted_date') else 'N/A'
    
    # Format the status message based on language
    if language == "en":
        status_msg = f"""The current status of your Grievance is as follows:
Grievance ID: {grievance_data['grievance_id']}
Status: {grievance_data['grievance_status']}
Submitted: {submitted_date}
Department: {grievance_data.get('department_name', 'Water Supply Department')}
Category: {grievance_data.get('grievance_name', 'N/A')}
Sub-category: {grievance_data.get('sub_grievance_name', 'N/A')}"""

        # Add location details
        if grievance_data.get('district_name'):
            status_msg += f"\nDistrict: {grievance_data['district_name']}"
        if grievance_data.get('block_name'):
            status_msg += f"\nBlock: {grievance_data['block_name']}"
        if grievance_data.get('grampanchayat_name'):
            status_msg += f"\nGram Panchayat: {grievance_data['grampanchayat_name']}"

        # Add estimated resolution time if applicable
        if grievance_data.get('estimated_days') and grievance_data['grievance_status'] not in ['Resolved', 'Closed']:
            status_msg += f"\nEstimated Resolution: {grievance_data['estimated_days']} working days"
        
        # Add current processing level
        if grievance_data.get('current_level'):
            status_msg += f"\nCurrently being processed at: {grievance_data['current_level']}"
            
        # Add resolution information if resolved
        if grievance_data['grievance_status'] in ['Resolved', 'Closed']:
            if grievance_data.get('resolved_date'):
                resolved_date = grievance_data['resolved_date'].strftime('%d-%b-%Y')
                status_msg += f"\nResolved on: {resolved_date}"
            if grievance_data.get('resolved_user_name'):
                status_msg += f"\nResolved by: {grievance_data['resolved_user_name']}"
    
    else:  # Marathi
        status_msg = f"""आपल्या तक्रारीची सद्यस्थिती खालीलप्रमाणे आहे:
तक्रार क्रमांक: {grievance_data['grievance_unique_number']}
स्थिती: {grievance_data['grievance_status']}
दाखल दिनांक: {submitted_date}
विभाग: {grievance_data.get('department_name', 'पाणी पुरवठा विभाग')}"""

        if grievance_data.get('estimated_days'):
            status_msg += f"\nअंदाजे निराकरण कालावधी: {grievance_data['estimated_days']} कार्यदिवस"
        
        if grievance_data.get('current_level'):
            status_msg += f"\nसध्याची पातळी: {grievance_data['current_level']}"
            
        if grievance_data['grievance_status'] == 'Resolved' and grievance_data.get('resolved_date'):
            resolved_date = grievance_data['resolved_date'].strftime('%d-%b-%Y')
            status_msg += f"\nनिराकरण दिनांक: {resolved_date}"
            
        if grievance_data.get('status_remarks'):
            status_msg += f"\nशेरा: {grievance_data['status_remarks']}"
    
    return status_msg
    """Format SIMPLE grievance status information for display - FIXED VERSION"""
    if language == "mr":
        status_msg = f"""🔍 तक्रार स्थिती: {grievance_data['status']}
🆔 तक्रार क्रमांक: {grievance_data['grievance_number']}
📝 श्रेणी: {grievance_data['category']}
📅 तारीख: {grievance_data['created_at'][:10] if grievance_data['created_at'] else 'N/A'}"""
    else:
        status_msg = f"""🔍 Grievance Status: {grievance_data['status']}
🆔 Grievance ID: {grievance_data['grievance_number']}
📝 Category: {grievance_data['category']}
📅 Date: {grievance_data['created_at'][:10] if grievance_data['created_at'] else 'N/A'}"""
    
    return status_msg.strip()

def get_initial_response_with_status_option(language: str) -> str:
    """Get enhanced initial response with status check option"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"""{kb['welcome_message']}

प्रश्न क्र. १: {kb['initial_question']}
उत्तर १ - "{kb['options']['yes']}"
उत्तर २ - "{kb['options']['no']}"

प्रश्न क्र. २: {kb['status_check_question']}
उत्तर - "स्थिती तपासा" किंवा आपला तक्रार क्रमांक टाइप करा
उदाहरण: G-12safeg7678"""
    else:
        return f"""{kb['welcome_message']}

Question 1: {kb['initial_question']}
Answer 1: "{kb['options']['yes']}"
Answer 2: "{kb['options']['no']}"

Question 2: {kb['status_check_question']}
Answer: Type "Check Status" or enter your Grievance ID
Example: G-12safeg7678"""

def get_initial_response(language: str) -> str:
    """Get the initial welcome message and question"""
    return get_initial_response_with_status_option(language)

def get_feedback_question(language: str) -> str:
    """Get the feedback question"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"""प्रश्न क्र. २.२: {kb['feedback_question']}
उत्तर १ - "{kb['options']['yes']}"
उत्तर २ - "{kb['options']['no']}\""""
    else:
        return f"""Question 2.2: {kb['feedback_question']}
Answer 1: "{kb['options']['yes']}"
Answer 2: "{kb['options']['no']}\""""

def get_rating_request(language: str) -> str:
    """Get the rating request message"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"""{kb['rating_question']}
{kb['rating_request']}
१ - {RATING_LABELS['mr'][1]}
२ - {RATING_LABELS['mr'][2]}
३ - {RATING_LABELS['mr'][3]}
४ - {RATING_LABELS['mr'][4]}
५ - {RATING_LABELS['mr'][5]}"""
    else:
        return f"""{kb['rating_question']}
{kb['rating_request']}
1 - {RATING_LABELS['en'][1]}
2 - {RATING_LABELS['en'][2]}
3 - {RATING_LABELS['en'][3]}
4 - {RATING_LABELS['en'][4]}
5 - {RATING_LABELS['en'][5]}"""

def get_yes_response(language: str) -> str:
    """Get the response for 'YES' answer"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    yes_resp = kb['yes_response']
    if language == "mr":
        response = f"""उत्तर १ - "{kb['options']['yes']}"
{yes_resp['intro']}

{yes_resp['method1']['title']}
{yes_resp['method1']['description']}
{yes_resp['method1']['link']}

{yes_resp['method2']['title']}
{yes_resp['method2']['description']}
{yes_resp['method2']['link']}"""
    else:
        response = f"""Answer 1: "{kb['options']['yes']}"
{yes_resp['intro']}

{yes_resp['method1']['title']}
{yes_resp['method1']['description']}
{yes_resp['method1']['link']}

{yes_resp['method2']['title']}
{yes_resp['method2']['description']}
{yes_resp['method2']['link']}"""
    return response

def get_no_response(language: str) -> str:
    """Get the thank you response for 'no' answer"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"""उत्तर २ - "{kb['options']['no']}"
{kb['no_response']}"""
    else:
        return f"""Answer 2: "{kb['options']['no']}"
{kb['no_response']}"""

async def process_maha_jal_query(input_text: str, session_id: str, language: str) -> str:
    """Process user queries for the Maha-Jal system"""
    logger.info(f"Processing query: {input_text} for session: {session_id} in language: {language}")
    
    # Check if input contains a grievance ID pattern
    grievance_id_match = re.search(r'[Gg]-[a-zA-Z0-9]+', input_text)
    if grievance_id_match:
        grievance_id = grievance_id_match.group()
        logger.info(f"Detected grievance ID: {grievance_id}")
        
        try:
            # Get grievance data from database
            grievance_data = await db_manager.get_grievance_status(grievance_id)
            
            if grievance_data:
                logger.info(f"Found grievance data: {grievance_data}")
                return format_simple_grievance_status(grievance_data, language)
            else:
                return MAHA_JAL_KNOWLEDGE_BASE[language]["grievance_not_found"]
        except Exception as e:
            logger.error(f"Error fetching grievance status: {e}")
            return MAHA_JAL_KNOWLEDGE_BASE[language]["database_error"]
    """Enhanced Maha-Jal Samadhan query processing with IMPROVED status check flow"""
    if session_id not in USER_SESSION_STATE:
        USER_SESSION_STATE[session_id] = {"stage": "initial", "language": language}

    session_state = USER_SESSION_STATE[session_id]
    response_type = detect_yes_no_response(input_text, language)

    # Enhanced logging
    logger.info(f"🔍 Session {session_id} - Stage: {session_state.get('stage')} - Input: '{input_text}'")
    logger.info(f"🔍 Status check detection: {detect_status_check_intent(input_text, language)}")
    logger.info(f"🔍 Exact status question: {detect_exact_status_question(input_text, language)}")

    # PRIORITY 1: Handle ANY status check intent (broad detection)
    if (detect_exact_status_question(input_text, language) or 
        detect_status_check_intent(input_text, language)):
        
        # Check if grievance ID is already in the input
        grievance_id = detect_grievance_id(input_text)
        
        if grievance_id and validate_grievance_id_format(grievance_id):
            # ID found in input, fetch status directly
            try:
                grievance_data = await get_grievance_status(grievance_id)
                if grievance_data:
                    session_state["stage"] = "status_shown"
                    status_response = format_simple_grievance_status(grievance_data, language)
                    status_response += f"\n\n🔗 {MAHA_JAL_KNOWLEDGE_BASE[language]['track_grievance_help']}"
                    logger.info(f"✅ Status found for ID: {grievance_id}")
                    return status_response
                else:
                    return MAHA_JAL_KNOWLEDGE_BASE[language]['grievance_not_found']
            except Exception as e:
                logger.error(f"Error fetching grievance status: {e}")
                return MAHA_JAL_KNOWLEDGE_BASE[language]['database_error']
        else:
            # No ID found, ask for it
            session_state["stage"] = "waiting_for_grievance_id"
            logger.info(f"✅ Session {session_id} moved to waiting_for_grievance_id stage")
            return MAHA_JAL_KNOWLEDGE_BASE[language]['grievance_id_prompt']

    # PRIORITY 2: Handle grievance ID input if we're waiting for it
    if session_state.get("stage") == "waiting_for_grievance_id":
        grievance_id = detect_grievance_id(input_text) or input_text.strip()
        
        if grievance_id and validate_grievance_id_format(grievance_id):
            try:
                grievance_data = await get_grievance_status(grievance_id)
                if grievance_data:
                    session_state["stage"] = "status_shown"
                    status_response = format_simple_grievance_status(grievance_data, language)
                    status_response += f"\n\n🔗 {MAHA_JAL_KNOWLEDGE_BASE[language]['track_grievance_help']}"
                    return status_response
                else:
                    return MAHA_JAL_KNOWLEDGE_BASE[language]['grievance_not_found']
            except Exception as e:
                logger.error(f"Error fetching grievance status: {e}")
                return MAHA_JAL_KNOWLEDGE_BASE[language]['database_error']
        else:
            return MAHA_JAL_KNOWLEDGE_BASE[language]['invalid_grievance_id']

    # Handle feedback question flow
    if "feedback" in input_text.lower() or "अभिप्राय" in input_text.lower():
        session_state["stage"] = "feedback_question"
        return get_feedback_question(language)

    # Handle initial stage or direct questions
    if session_state["stage"] == "initial" or any(keyword in input_text.lower() for keyword in
                                                  ["register", "grievance", "complaint", "तक्रार", "नोंदवू", "शिकायत"]):
        if response_type == "yes":
            session_state["stage"] = "registration_info"
            return get_yes_response(language)
        elif response_type == "no":
            session_state["stage"] = "feedback_question"
            return get_feedback_question(language)
        else:
            session_state["stage"] = "awaiting_response"
            return get_initial_response_with_status_option(language)

    # Handle other stages...
    elif session_state["stage"] == "feedback_question":
        if response_type == "yes":
            session_state["stage"] = "rating_request"
            return get_rating_request(language)
        elif response_type == "no":
            session_state["stage"] = "completed"
            return MAHA_JAL_KNOWLEDGE_BASE[language]['no_response']
        else:
            return MAHA_JAL_KNOWLEDGE_BASE[language]['help_text']

    elif session_state["stage"] == "awaiting_response":
        if response_type == "yes":
            session_state["stage"] = "registration_info"
            return get_yes_response(language)
        elif response_type == "no":
            session_state["stage"] = "feedback_question"
            return get_feedback_question(language)
        else:
            return MAHA_JAL_KNOWLEDGE_BASE[language]['help_text']

    # Default response
    else:
        return get_initial_response_with_status_option(language)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("=" * 70)
    print("🚀 STARTING MAHA-JAL SAMADHAN CHATBOT BACKEND WITH DATABASE")
    print("=" * 70)
    print("🌐 Languages: English, Marathi")
    print("🎯 System: Maha-Jal Samadhan Public Grievance Redressal")
    print("💡 Mode: Q&A with PostgreSQL Database Integration")
    print("⭐ Features: SIMPLE Grievance status check, 5-star rating system")
    print("=" * 70)

    # Initialize database connection
    try:
        await init_database()
        connection_test = await test_db_connection()
        SYSTEM_STATUS["database_connected"] = connection_test
        if connection_test:
            print("✅ Database connection: SUCCESS")
            # Get database info
            db_info = await get_db_info()
            if db_info.get("connected"):
                print(f"📊 Database: {db_info.get('database_name', 'N/A')}")
                print(f"👤 User: {db_info.get('user', 'N/A')}")
                print(f"🔢 Pool size: {db_info.get('pool_current_size', 0)}")
        else:
            print("❌ Database connection: FAILED")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        SYSTEM_STATUS["database_connected"] = False

    print("=" * 70)
    print("🎯 Backend ready! Access the API at:")
    print(" • Docs: http://localhost:8000/docs")
    print(" • Health: http://localhost:8000/health/")
    print(" • SIMPLE Status Check: http://localhost:8000/grievance/status/")
    print(" • Database Stats: http://localhost:8000/database/stats/")
    print(" • Ratings Export: http://localhost:8000/ratings/export")
    print("=" * 70)

    yield

    print("🔥 Shutting down...")
    await close_database()
    print("👋 Goodbye!")

# Initialize FastAPI app
app = FastAPI(
    title="Maha-Jal Samadhan Chatbot Backend with Database",
    description="Public Grievance Redressal System Chatbot with bilingual support, PostgreSQL database integration and SIMPLE status system",
    version="3.3.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your actual domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    """Additional CORS handling"""
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    """Handle preflight OPTIONS requests"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/")
async def root():
    """Root endpoint with system status"""
    try:
        uptime = time.time() - SYSTEM_STATUS["startup_time"]
        db_info = await get_db_info() if SYSTEM_STATUS["database_connected"] else {"connected": False}
        return {
            "message": "Maha-Jal Samadhan Chatbot Backend with SIMPLE Status is running",
            "system": "Public Grievance Redressal System with Database Integration",
            "mode": "Q&A System with PostgreSQL Database + SIMPLE 5-star rating",
            "version": "3.3.0",
            "uptime_seconds": round(uptime, 2),
            "system_status": {
                "active_sessions": len(CHAT_HISTORY),
                "total_queries": SYSTEM_STATUS["total_queries"],
                "total_ratings": len(RATINGS_DATA),
                "supported_languages": SYSTEM_STATUS["supported_languages"],
                "database_connected": SYSTEM_STATUS["database_connected"],
                "database_info": db_info
            }
        }
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"System error: {str(e)}"}
        )

@app.post("/query/")
async def process_query(request: QueryRequest):
    """Main query processing endpoint with SIMPLE status responses"""
    try:
        SYSTEM_STATUS["total_queries"] += 1
        input_text = request.input_text.strip()
        language = request.language.lower()

        if not input_text:
            SYSTEM_STATUS["failed_queries"] += 1
            error_msg = {
                'en': "Please provide a valid query.",
                'mr': "कृपया एक वैध प्रश्न प्रदान करा."
            }
            return JSONResponse(
                status_code=400,
                content={"reply": error_msg.get(language, error_msg['en'])}
            )

        if language not in SYSTEM_STATUS["supported_languages"]:
            SYSTEM_STATUS["failed_queries"] += 1
            return JSONResponse(
                status_code=400,
                content={"reply": f"Language '{language}' not supported. Use: {', '.join(SYSTEM_STATUS['supported_languages'])}"}
            )

        session_id = request.session_id or generate_session_id()

        # CRITICAL: Log session state for debugging
        logger.info(f"🔍 QUERY DEBUG - Session: {session_id} - Input: '{input_text}' - Language: {language}")
        logger.info(f"🔍 CURRENT SESSION STATE: {USER_SESSION_STATE.get(session_id, 'NEW SESSION')}")

        # Check for greeting intent
        is_greet, greet_key = detect_greeting(input_text)
        if is_greet:
            SYSTEM_STATUS["successful_queries"] += 1
            reply_text = greeting_reply(language, greet_key)
            add_to_chat_history(session_id, input_text, reply_text, language)
            return {
                "reply": reply_text,
                "language": language,
                "session_id": session_id,
                "detected_language": language
            }

        # Process Maha-Jal Samadhan specific query with database integration
        try:
            assistant_reply = await process_maha_jal_query(input_text, session_id, language)
            SYSTEM_STATUS["successful_queries"] += 1
            add_to_chat_history(session_id, input_text, assistant_reply, language)

            # Log final session state after processing
            logger.info(f"🔍 FINAL SESSION STATE: {USER_SESSION_STATE.get(session_id)}")

            return {
                "reply": assistant_reply,
                "language": language,
                "session_id": session_id,
                "detected_language": language
            }

        except Exception as query_error:
            SYSTEM_STATUS["failed_queries"] += 1
            SYSTEM_STATUS["last_error"] = str(query_error)
            logger.error(f"Query processing error for language {language}: {query_error}")
            error_msg = {
                'en': "An error occurred while processing your query. Please try again later.",
                'mr': "तुमचा प्रश्न प्रक्रिया करतान त्रुटी झाली. कृपया नंतर पुन्हा प्रयत्न करा."
            }
            return JSONResponse(
                status_code=500,
                content={"reply": error_msg.get(language, error_msg['en'])}
            )

    except Exception as e:
        SYSTEM_STATUS["failed_queries"] += 1
        SYSTEM_STATUS["last_error"] = str(e)
        logging.error(f"Query processing error: {e}")
        return JSONResponse(
            status_code=500,
            content={"reply": "An error occurred while processing your query. Please try again later."}
        )

@app.post("/grievance/status/")
async def get_grievance_status_endpoint(request: GrievanceStatusRequest):
    """SIMPLE Grievance Status Check - Returns only essential information"""
    logger.info(f"Received grievance status request for ID: {request.grievance_id}, Language: {request.language}")
    
    try:
        # Initialize database connection if not already initialized
        if not db_manager.pool:
            logger.info("Initializing database connection...")
            await db_manager.init_pool()
        
        # Get grievance data from database
        grievance_data = await db_manager.get_grievance_status(request.grievance_id)
        
        logger.info(f"Retrieved grievance data: {grievance_data}")
        
        if grievance_data:
            # Format the response using the helper function
            formatted_status = format_simple_grievance_status(grievance_data, request.language)
            logger.info(f"Formatted status message: {formatted_status}")
            
            return JSONResponse(
                content={
                    "success": True,
                    "found": True,
                    "message": formatted_status,
                    "data": {
                        "grievance_id": grievance_data.get('grievance_id'),
                        "status": grievance_data.get('grievance_status'),
                        "submitted_date": grievance_data.get('submitted_date').strftime('%d-%b-%Y') if grievance_data.get('submitted_date') else None,
                        "department": grievance_data.get('department_name', 'Water Supply Department'),
                        "language": request.language
                    }
                }
            )
        
        # If no grievance data found
        error_msg = {
            'en': "Sorry, no grievance found with the provided ID. Please check your Grievance ID and try again.",
            'mr': "माफ करा, दिलेल्या क्रमांकासह कोणतीही तक्रार आढळली नाही. कृपया आपला तक्रार क्रमांक तपासा आणि पुन्हा प्रयत्न करा."
        }
        logger.warning(f"No grievance found with ID: {request.grievance_id}")
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "found": False,
                "message": error_msg.get(request.language, error_msg['en'])
            }
        )
    except Exception as e:
        logger.error(f"Error processing grievance status request: {str(e)}")
        error_msg = {
            'en': "An error occurred while fetching the grievance status. Please try again later.",
            'mr': "तक्रार स्थिती मिळवताना त्रुटी आली. कृपया नंतर पुन्हा प्रयत्न करा."
        }
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": error_msg.get(request.language, error_msg['en']),
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error fetching grievance status: {e}")
        error_msg = {
            'en': "Unable to fetch grievance information at the moment. Please try again later.",
            'mr': "सध्या तक्रार माहिती मिळवता येत नाही. कृपया नंतर प्रयत्न करा."
        }
        return JSONResponse(
            status_code=500,
            content={
                "found": False,
                "message": error_msg.get(request.language, error_msg['en'])
            }
        )

@app.post("/user/search/")
async def search_user_grievances_endpoint(request: UserSearchRequest):
    """Search grievances by user identifier (email, phone, name)"""
    try:
        grievances = await search_user_grievances(request.user_identifier)
        if grievances:
            return {
                "found": True,
                "count": len(grievances),
                "grievances": grievances,
                "language": request.language
            }
        else:
            error_msg = {
                'en': "No grievances found for the provided user information.",
                'mr': "दिलेल्या वापरकर्ता माहितीसाठी कोणत्याही तक्रारी आढळल्या नाहीत."
            }
            return JSONResponse(
                status_code=404,
                content={
                    "found": False,
                    "message": error_msg.get(request.language, error_msg['en'])
                }
            )
    except Exception as e:
        logger.error(f"Error searching user grievances: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "found": False,
                "message": "Error searching grievances. Please try again later."
            }
        )

@app.get("/database/debug/")
async def debug_database():
    """Debug endpoint to check database structure"""
    try:
        if not SYSTEM_STATUS["database_connected"]:
            return {"error": "Database not connected"}
        from database import get_db_tables, check_table_columns
        tables = await get_db_tables()
        table_info = {}
        for table in tables:
            columns = await check_table_columns(table)
            table_info[table] = columns
        return {
            "tables": tables,
            "table_structures": table_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Database debug error: {e}")
        return {"error": str(e)}

@app.get("/database/stats/")
async def get_database_stats():
    """Get database statistics"""
    try:
        if not SYSTEM_STATUS["database_connected"]:
            return JSONResponse(
                status_code=503,
                content={"error": "Database not connected"}
            )
        stats = await get_db_statistics()
        db_info = await get_db_info()
        return {
            "database_info": db_info,
            "grievance_statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get database statistics: {str(e)}"}
        )

@app.post("/rating/")
async def submit_rating(request: RatingRequest):
    """Submit user rating for service quality"""
    logger.info(f"Received rating request: {request.dict()}")
    
    try:
        session_id = request.session_id or generate_session_id()
        rating_label = RATING_LABELS[request.language][request.rating]
        
        # Save rating data
        success = save_rating_data(
            rating=request.rating,
            session_id=session_id,
            language=request.language,
            grievance_id=request.grievance_id,
            feedback_text=request.feedback_text
        )
        
        if success:
            # Get thank you message from knowledge base
            thank_you_msg = MAHA_JAL_KNOWLEDGE_BASE[request.language]['rating_thank_you']
            
            response_msg = {
                'en': f"Thank you for your {request.rating}-star rating! ({rating_label})",
                'mr': f"आपल्या {request.rating}-स्टार रेटिंगसाठी धन्यवाद! ({rating_label})"
            }
            
            logger.info(f"Successfully saved rating: {request.rating} stars for session {session_id}")
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": response_msg.get(request.language, response_msg['en']),
                    "thank_you": thank_you_msg,
                    "rating": request.rating,
                    "rating_label": rating_label,
                    "session_id": session_id
                }
            )
        else:
            error_msg = {
                'en': "Failed to save your rating. Please try again.",
                'mr': "आपले रेटिंग जतन करण्यात अयशस्वी. कृपया पुन्हा प्रयत्न करा."
            }
            logger.error(f"Failed to save rating for session {session_id}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": error_msg.get(request.language, error_msg['en'])
                }
            )
            
    except ValidationError as ve:
        logger.error(f"Validation error in rating submission: {ve}")
        error_msg = {
            'en': "Invalid rating data. Rating must be between 1 and 5.",
            'mr': "अवैध रेटिंग डेटा. रेटिंग 1 आणि 5 दरम्यान असावे."
        }
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": error_msg.get(request.language, error_msg['en']),
                "errors": str(ve)
            }
        )
        
    except Exception as e:
        logger.error(f"Error in rating submission: {str(e)}")
        error_msg = {
            'en': "An error occurred while processing your rating.",
            'mr': "आपले रेटिंग प्रक्रिया करताना त्रुटी आली."
        }
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": error_msg.get(request.language, error_msg['en']),
                "error": str(e)
            }
        )
        response_msg = f"{thank_you_msg}\n\nYour Rating: {request.rating}/5 ({rating_label})"
        if request.language == "mr":
            response_msg = f"{thank_you_msg}\n\nआपले रेटिंग: {request.rating}/५ ({rating_label})"

        user_msg = f"Rating: {request.rating}/5"
        add_to_chat_history(session_id, user_msg, response_msg, request.language)
        return {
            "reply": response_msg,
            "rating": request.rating,
            "rating_label": rating_label,
            "language": request.language,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Rating submission error: {e}")
        return JSONResponse(
            status_code=500,
            content={"reply": "An error occurred while submitting your rating. Please try again later."}
        )

@app.get("/ratings/export")
async def export_ratings():
    """Export ratings data as CSV file with proper UTF-8 encoding for Marathi text"""
    try:
        if not RATINGS_DATA:
            return JSONResponse(
                status_code=404,
                content={"error": "No ratings data available for export"}
            )

        output = io.StringIO()
        fieldnames = ["timestamp", "session_id", "rating", "feedback", "language", "grievance_id", "ip_address"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for rating_data in RATINGS_DATA:
            modified_row = {
                "timestamp": rating_data["timestamp"],
                "session_id": rating_data["session_id"],
                "rating": rating_data["rating"],
                "feedback": rating_data["rating_label"],
                "language": rating_data["language"],
                "grievance_id": rating_data["grievance_id"],
                "ip_address": rating_data["ip_address"]
            }
            writer.writerow(modified_row)

        csv_content = output.getvalue()
        output.close()

        utf8_bom = '\ufeff'
        csv_content_with_bom = utf8_bom + csv_content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"maha_jal_ratings_{timestamp}.csv"

        return StreamingResponse(
            io.BytesIO(csv_content_with_bom.encode('utf-8')),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to export ratings: {str(e)}"}
        )

@app.get("/ratings/stats")
async def get_rating_stats():
    """Get rating statistics"""
    try:
        if not RATINGS_DATA:
            return {
                "total_ratings": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "language_distribution": {}
            }

        total_ratings = len(RATINGS_DATA)
        ratings = [entry["rating"] for entry in RATINGS_DATA]
        average_rating = sum(ratings) / total_ratings if ratings else 0

        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[str(i)] = ratings.count(i)

        languages = [entry["language"] for entry in RATINGS_DATA]
        language_distribution = {}
        for lang in set(languages):
            language_distribution[lang] = languages.count(lang)

        return {
            "total_ratings": total_ratings,
            "average_rating": round(average_rating, 2),
            "rating_distribution": rating_distribution,
            "language_distribution": language_distribution,
            "latest_ratings": RATINGS_DATA[-10:] if len(RATINGS_DATA) >= 10 else RATINGS_DATA
        }
    except Exception as e:
        logger.error(f"Rating stats error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get rating statistics: {str(e)}"}
        )

@app.get("/health/")
async def health_check():
    """System health check endpoint with database connectivity"""
    try:
        uptime = time.time() - SYSTEM_STATUS["startup_time"]
        db_status = await test_db_connection() if SYSTEM_STATUS["database_connected"] else False
        SYSTEM_STATUS["database_connected"] = db_status

        return {
            "status": "healthy" if db_status else "degraded",
            "timestamp": time.time(),
            "uptime_seconds": round(uptime, 2),
            "system_info": {
                "active_sessions": len(CHAT_HISTORY),
                "total_queries": SYSTEM_STATUS["total_queries"],
                "successful_queries": SYSTEM_STATUS["successful_queries"],
                "failed_queries": SYSTEM_STATUS["failed_queries"],
                "total_ratings": len(RATINGS_DATA),
                "supported_languages": SYSTEM_STATUS["supported_languages"],
                "database_connected": db_status
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": time.time()
            }
        )

@app.get("/suggestions/")
async def get_suggestions(language: str = "en"):
    """Updated suggestions with specific status check option"""
    suggestions_by_language = {
        "en": [
            "I want to register a grievance",
            "Would you like to check the status of the grievance which you have registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
            "Check status G-12safeg7678",
            "Has a Grievance already been registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
            "Would you like to provide feedback regarding the resolution of your grievance addressed through the Maha-Jal Samadhan Public Grievance Redressal System?"
        ],
        "mr": [
            "मला तक्रार नोंदवायची आहे",
            "आपण महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदवलेल्या तक्रारीची स्थिती तपासू इच्छिता का?",
            "स्थिती तपासा G-12safeg7678",
            "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदविण्यात आलेली तक्रार आहे का?",
            "आपल्या तक्रारीच्या निराकरणाबाबत अभिप्राय द्यायला इच्छिता का?"
        ]
    }
    suggestions = suggestions_by_language.get(language, suggestions_by_language["en"])
    return {
        "suggestions": suggestions,
        "language": language,
        "total": len(suggestions)
    }

@app.get("/languages/")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "supported_languages": SYSTEM_STATUS["supported_languages"],
        "language_details": {
            "en": {"name": "English", "native_name": "English"},
            "mr": {"name": "Marathi", "native_name": "मराठी"}
        }
    }

# Add debug endpoint to check session states
@app.get("/debug/sessions")
async def debug_sessions():
    """Debug endpoint to check current session states"""
    return {
        "total_sessions": len(USER_SESSION_STATE),
        "sessions": USER_SESSION_STATE,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

