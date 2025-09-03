from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional
import time
import os
import logging
import re
import csv
import io
from datetime import datetime
from contextlib import asynccontextmanager

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
    "supported_languages": ["en", "mr"]
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

# Global variables
CHAT_HISTORY = {}
RATE_LIMIT_TRACKER = {}
USER_SESSION_STATE = {}
RATINGS_DATA = []  # Store ratings data for CSV export

# Rating labels mapping
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

# Exact Maha-Jal Samadhan Knowledge Base from your PDF images
MAHA_JAL_KNOWLEDGE_BASE = {
    "en": {
        "welcome_message": "Welcome to the Maha-Jal Samadhan Public Grievance Redressal System.",
        "initial_question": "Would you like to register a Grievance on the Maha-Jal Samadhan Public Grievance Redressal System?",
        "check_existing_question": "Has a Grievance already been registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
        "feedback_question": "Would you like to provide feedback regarding the resolution of your grievance addressed through the Maha-Jal Samadhan Public Grievance Redressal System?",
        "rating_question": "With reference to the resolution of your grievance on the Maha-Jal Samadhan Public Grievance Redressal System, how would you rate the quality of service on a scale of 1 to 5, where: 1 = Unsatisfactory and 5 = Satisfactory?",
        "rating_request": "Please provide your rating between 1 and 5:",
        "invalid_rating": "The information you have entered is invalid. Please try again.",
        "rating_thank_you": "Thank you for your feedback. Your rating has been recorded.",
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
        "help_text": "Please type 'YES' or 'NO' to proceed with your query."
    },
    "mr": {
        "welcome_message": "नमस्कार, महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये आपले स्वागत आहे.",
        "initial_question": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये आपण तक्रार नोंदवू इच्छिता का?",
        "check_existing_question": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदविण्यात आलेली तक्रार आहे का?",
        "feedback_question": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीद्वारे सोडविण्यात आलेल्या आपल्या तक्रारीच्या निराकरणाबाबत अभिप्राय द्यायला इच्छिता का?",
        "rating_question": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीवर आपल्या तक्रारीच्या निराकरणासंदर्भात, सेवा गुणवत्तेच्या दृष्टीने आपण १ ते ५ या श्रेणीमध्ये किती गुण द्यायला इच्छिता? १ म्हणजे 'असमाधानकारक' आणि ५ म्हणजे 'समाधानकारक'.",
        "rating_request": "कृपया आपल्यादवारे देण्यात आलेले गुण १ ते ५ मध्ये देण्यात यावे:",
        "invalid_rating": "आपण दिलेली माहिती अवैध आहे. कृपया पुन्हा प्रयत्न करा.",
        "rating_thank_you": "आपल्या अभिप्रायाबद्दल धन्यवाद. आपले रेटिंग नोंदवले गेले आहे.",
        "options": {"yes": "होय", "no": "नाही"},
        "yes_response": {
            "intro": "आपण 'महा-जल समाधान' सार्वजनिक तक्रार निवारण प्रणालीमध्ये आपली तक्रार दोन पद्धतींनी नोंदवू शकता:",
            "method1": {
                "title": "१. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये वेबसाईटद्वारे तक्रार नोंदणीसाठी आपण खालील लिंकवर क्लिक करून वेबसाईटवर तक्रार नोंदवू शकता:",
                "description": "लिंक -",
                "link": "https://mahajalsamadhan.in/log-grievance"
            },
            "method2": {
                "title": "२. महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये मोबाईल अ‍ॅपद्वारे तक्रार नोंदणी",
                "description": "आपण खालील लिंकद्वारे मोबाइल अ‍ॅप डाउनलोड करून तक्रार नोंदवू शकता:",
                "link": "https://play.google.com/store/apps/details?id=in.mahajalsamadhan.user&pli=1"
            }
        },
        "no_response": "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीचा वापर केल्याबद्दल आपले धन्यवाद.",
        "help_text": "कृपया 'होय' किंवा 'नाही' टाइप करून आपल्या प्रश्नासह पुढे जा."
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
    """Save rating data for CSV export"""
    try:
        rating_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": session_id,
            "rating": rating,
            "rating_label": RATING_LABELS[language][rating],
            "language": language,
            "grievance_id": grievance_id or "N/A",
            "feedback_text": feedback_text or "N/A",
            "ip_address": "N/A"  # Can be populated from request if needed
        }
        RATINGS_DATA.append(rating_entry)
        logger.info(f"Rating saved: {rating}/5 for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save rating data: {e}")

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
    
    # English patterns
    yes_patterns_en = [r'\byes\b', r'\by\b', r'\byeah\b', r'\byep\b']
    no_patterns_en = [r'\bno\b', r'\bn\b', r'\bnope\b']
    
    # Marathi patterns
    yes_patterns_mr = [r'\bहोय\b', r'\bहो\b']
    no_patterns_mr = [r'\bनाही\b', r'\bना\b']
    
    # Check for yes patterns
    for pattern in yes_patterns_en + yes_patterns_mr:
        if re.search(pattern, text):
            return "yes"
    
    # Check for no patterns
    for pattern in no_patterns_en + no_patterns_mr:
        if re.search(pattern, text):
            return "no"
    
    return "unknown"

def get_initial_response(language: str) -> str:
    """Get the initial welcome message and question"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"{kb['welcome_message']}\n\nप्रश्न क्र. १: {kb['initial_question']}\n\nउत्तर १ - \"{kb['options']['yes']}\"\nउत्तर २ - \"{kb['options']['no']}\""
    else:
        return f"{kb['welcome_message']}\n\nQuestion 1:\n{kb['initial_question']}\n\nAnswer 1: \"{kb['options']['yes']}\"\nAnswer 2: \"{kb['options']['no']}\""

def get_feedback_question(language: str) -> str:
    """Get the feedback question"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"प्रश्न क्र. २.२: {kb['feedback_question']}\n\nउत्तर १ - \"{kb['options']['yes']}\"\nउत्तर २ - \"{kb['options']['no']}\""
    else:
        return f"Question 2.2: {kb['feedback_question']}\n\nAnswer 1: \"{kb['options']['yes']}\"\nAnswer 2: \"{kb['options']['no']}\""

def get_rating_request(language: str) -> str:
    """Get the rating request message"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"{kb['rating_question']}\n\n{kb['rating_request']}"
    else:
        return f"{kb['rating_question']}\n\n{kb['rating_request']}"

def get_yes_response(language: str) -> str:
    """Get the response for 'YES' answer"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    yes_resp = kb['yes_response']
    
    if language == "mr":
        response = f"उत्तर १ - \"{kb['options']['yes']}\"\n\n{yes_resp['intro']}\n\n"
        response += f"{yes_resp['method1']['title']}\n{yes_resp['method1']['description']}\n{yes_resp['method1']['link']}\n\n"
        response += f"{yes_resp['method2']['title']}\n{yes_resp['method2']['description']}\n{yes_resp['method2']['link']}"
    else:
        response = f"Answer 1: \"{kb['options']['yes']}\"\n\n{yes_resp['intro']}\n\n"
        response += f"{yes_resp['method1']['title']}\n{yes_resp['method1']['description']}\n{yes_resp['method1']['link']}\n\n"
        response += f"{yes_resp['method2']['title']}\n{yes_resp['method2']['description']}\n{yes_resp['method2']['link']}"
    
    return response

def get_no_response(language: str) -> str:
    """Get the thank you response for 'no' answer"""
    kb = MAHA_JAL_KNOWLEDGE_BASE[language]
    if language == "mr":
        return f"उत्तर २ - \"{kb['options']['no']}\"\n\n{kb['no_response']}"
    else:
        return f"Answer 2: \"{kb['options']['no']}\"\n\n{kb['no_response']}"

def process_maha_jal_query(input_text: str, session_id: str, language: str) -> str:
    """Process Maha-Jal Samadhan specific queries"""
    
    # Initialize session state if not exists
    if session_id not in USER_SESSION_STATE:
        USER_SESSION_STATE[session_id] = {"stage": "initial", "language": language}
    
    session_state = USER_SESSION_STATE[session_id]
    response_type = detect_yes_no_response(input_text, language)
    
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
            # First time or unclear response
            session_state["stage"] = "awaiting_response"
            return get_initial_response(language)
    
    # Handle feedback question stage
    elif session_state["stage"] == "feedback_question":
        if response_type == "yes":
            session_state["stage"] = "rating_request"
            return get_rating_request(language)
        elif response_type == "no":
            session_state["stage"] = "completed"
            return MAHA_JAL_KNOWLEDGE_BASE[language]['no_response']
        else:
            return MAHA_JAL_KNOWLEDGE_BASE[language]['help_text']
    
    # Handle awaiting response stage
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
        return get_initial_response(language)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("=" * 60)
    print("🚀 STARTING MAHA-JAL SAMADHAN CHATBOT BACKEND")
    print("=" * 60)
    
    print("🌏 Languages supported: English, Marathi")
    print("🎯 System: Maha-Jal Samadhan Public Grievance Redressal")
    print("💡 Mode: Hardcoded Q&A with Rating System")
    print("⭐ Features: 5-star rating system with CSV export")
    
    print("=" * 60)
    print("🎯 Backend ready! Access the API at:")
    print(" • Docs: http://localhost:8000/docs")
    print(" • Health: http://localhost:8000/health/")
    print(" • Status: http://localhost:8000/status/")
    print(" • Ratings CSV: http://localhost:8000/ratings/export")
    print("=" * 60)
    
    yield
    
    print("🔥 FastAPI application shutting down...")
    print("👋 Goodbye!")

# Initialize FastAPI app
app = FastAPI(
    title="Maha-Jal Samadhan Chatbot Backend with Rating System",
    description="Public Grievance Redressal System Chatbot with bilingual support and 5-star rating system",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware - IMPORTANT for PHP frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

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
        return {
            "message": "Maha-Jal Samadhan Chatbot Backend is running",
            "system": "Public Grievance Redressal System with Rating",
            "mode": "Hardcoded Q&A System with 5-star rating",
            "version": "2.1.0",
            "uptime_seconds": round(uptime, 2),
            "system_status": {
                "active_sessions": len(CHAT_HISTORY),
                "total_queries": SYSTEM_STATUS["total_queries"],
                "total_ratings": len(RATINGS_DATA),
                "supported_languages": SYSTEM_STATUS["supported_languages"]
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
    """Main query processing endpoint with language support"""
    try:
        # Update system statistics
        SYSTEM_STATUS["total_queries"] += 1
        
        # Validate input
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
        
        # Validate language
        if language not in SYSTEM_STATUS["supported_languages"]:
            SYSTEM_STATUS["failed_queries"] += 1
            return JSONResponse(
                status_code=400,
                content={"reply": f"Language '{language}' not supported. Use: {', '.join(SYSTEM_STATUS['supported_languages'])}"}
            )
        
        # Generate session ID if not provided
        session_id = request.session_id or generate_session_id()
        
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
        
        # Process Maha-Jal Samadhan specific query
        try:
            assistant_reply = process_maha_jal_query(input_text, session_id, language)
            
            # Success
            SYSTEM_STATUS["successful_queries"] += 1
            
            # Add to chat history
            add_to_chat_history(session_id, input_text, assistant_reply, language)
            
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
                'mr': "तुमचा प्रश्न प्रक्रिया करताना त्रुटी झाली. कृपया नंतर पुन्हा प्रयत्न करा."
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

@app.post("/rating/")
async def submit_rating(request: RatingRequest):
    """Submit user rating for service quality"""
    try:
        # Validate rating
        if request.rating not in [1, 2, 3, 4, 5]:
            error_msg = {
                'en': "The information you have entered is invalid. Please try again.",
                'mr': "आपण दिलेली माहिती अवैध आहे. कृपया पुन्हा प्रयत्न करा."
            }
            return JSONResponse(
                status_code=400,
                content={"reply": error_msg.get(request.language, error_msg['en'])}
            )
        
        # Generate session ID if not provided
        session_id = request.session_id or generate_session_id()
        
        # Save rating data
        save_rating_data(
            rating=request.rating,
            session_id=session_id,
            language=request.language,
            grievance_id=request.grievance_id,
            feedback_text=request.feedback_text
        )
        
        # Get rating label
        rating_label = RATING_LABELS[request.language][request.rating]
        
        # Prepare response message
        thank_you_msg = MAHA_JAL_KNOWLEDGE_BASE[request.language]['rating_thank_you']
        
        response_msg = f"{thank_you_msg}\n\nYour Rating: {request.rating}/5 ({rating_label})"
        if request.language == "mr":
            response_msg = f"{thank_you_msg}\n\nआपले रेटिंग: {request.rating}/५ ({rating_label})"
        
        # Add to chat history
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
    """Export ratings data as CSV file"""
    try:
        if not RATINGS_DATA:
            return JSONResponse(
                status_code=404,
                content={"error": "No ratings data available for export"}
            )
        
        # Create CSV content
        output = io.StringIO()
        fieldnames = ["timestamp", "session_id", "rating", "rating_label", "language", "grievance_id", "feedback_text", "ip_address"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for rating_data in RATINGS_DATA:
            writer.writerow(rating_data)
        
        # Prepare response
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"maha_jal_ratings_{timestamp}.csv"
        
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
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
        
        # Calculate statistics
        total_ratings = len(RATINGS_DATA)
        ratings = [entry["rating"] for entry in RATINGS_DATA]
        average_rating = sum(ratings) / total_ratings if ratings else 0
        
        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[str(i)] = ratings.count(i)
        
        # Language distribution
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
    """System health check endpoint"""
    try:
        uptime = time.time() - SYSTEM_STATUS["startup_time"]
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": round(uptime, 2),
            "system_info": {
                "active_sessions": len(CHAT_HISTORY),
                "total_queries": SYSTEM_STATUS["total_queries"],
                "successful_queries": SYSTEM_STATUS["successful_queries"],
                "failed_queries": SYSTEM_STATUS["failed_queries"],
                "total_ratings": len(RATINGS_DATA),
                "supported_languages": SYSTEM_STATUS["supported_languages"]
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
    """Get suggested questions for the UI in specified language"""
    suggestions_by_language = {
        "en": [
            "I want to register a grievance",
            "Would you like to register a Grievance on the Maha-Jal Samadhan Public Grievance Redressal System?",
            "Has a Grievance already been registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
            "Would you like to check the status of the grievance which you have registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
            "Would you like to provide feedback regarding the resolution of your grievance addressed through the Maha-Jal Samadhan Public Grievance Redressal System?"
        ],
        "mr": [
            "मला तक्रार नोंदवायची आहे",
            "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये आपण तक्रार नोंदवू इच्छिता का?",
            "महा-जल समाधान सार्वजनिक तक्रार निवारण प्रणालीमध्ये नोंदविण्यात आलेली तक्रार आहे का?",
            "आपण नोंदविलेल्या तक्रारीची स्थिती तपासू इच्छिता का?",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")