from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional
import time
import os
import logging
import re
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

# Global variables
CHAT_HISTORY = {}
RATE_LIMIT_TRACKER = {}
USER_SESSION_STATE = {}

# Exact Maha-Jal Samadhan Knowledge Base from your PDF images
MAHA_JAL_KNOWLEDGE_BASE = {
    "en": {
        "welcome_message": "Welcome to the Maha-Jal Samadhan Public Grievance Redressal System.",
        "initial_question": "Would you like to register a Grievance on the Maha-Jal Samadhan Public Grievance Redressal System?",
        "check_existing_question": "Has a Grievance already been registered on the Maha-Jal Samadhan Public Grievance Redressal System?",
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
    
    # Handle initial stage or direct questions
    if session_state["stage"] == "initial" or any(keyword in input_text.lower() for keyword in 
        ["register", "grievance", "complaint", "तक्रार", "नोंदवू", "शिकायत"]):
        
        if response_type == "yes":
            session_state["stage"] = "registration_info"
            return get_yes_response(language)
        elif response_type == "no":
            session_state["stage"] = "completed"
            return get_no_response(language)
        else:
            # First time or unclear response
            session_state["stage"] = "awaiting_response"
            return get_initial_response(language)
    
    # Handle awaiting response stage
    elif session_state["stage"] == "awaiting_response":
        if response_type == "yes":
            session_state["stage"] = "registration_info"
            return get_yes_response(language)
        elif response_type == "no":
            session_state["stage"] = "completed"
            return get_no_response(language)
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
    
    print("🌐 Languages supported: English, Marathi")
    print("🎯 System: Maha-Jal Samadhan Public Grievance Redressal")
    print("💡 Mode: Hardcoded Q&A (No RAG/Model required)")
    
    print("=" * 60)
    print("🎯 Backend ready! Access the API at:")
    print(" • Docs: http://localhost:8000/docs")
    print(" • Health: http://localhost:8000/health/")
    print(" • Status: http://localhost:8000/status/")
    print("=" * 60)
    
    yield
    
    print("🔥 FastAPI application shutting down...")
    print("👋 Goodbye!")

# Initialize FastAPI app
app = FastAPI(
    title="Maha-Jal Samadhan Chatbot Backend",
    description="Public Grievance Redressal System Chatbot with bilingual support (English, Marathi)",
    version="2.0.0",
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
            "system": "Public Grievance Redressal System",
            "mode": "Hardcoded Q&A System",
            "version": "2.0.0",
            "uptime_seconds": round(uptime, 2),
            "system_status": {
                "active_sessions": len(CHAT_HISTORY),
                "total_queries": SYSTEM_STATUS["total_queries"],
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
            "आपल्या तक्रारीच्या निराकरणाबाबत अभिप्राय द्याल का?"
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
