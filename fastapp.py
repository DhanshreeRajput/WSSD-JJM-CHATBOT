from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional
import time
import json
import hashlib
import os
import logging
import glob
from contextlib import asynccontextmanager
import asyncio
import traceback
import re

# Import with error handling
try:
    from rag_services import (
        build_rag_chain_with_model_choice, 
        process_scheme_query_with_retry, 
        detect_language,
        check_ollama_connection,
        clear_query_cache
    )
    from config import (
        OLLAMA_BASE_URL, 
        OLLAMA_MODEL, 
        UPLOAD_DIR, 
        RATE_LIMIT_SECONDS,
        print_config
    )
except ImportError as e:
    print(f"⚠️ Error importing modules: {e}")
    print("Please ensure rag_services.py and config.py are in the same directory as this file.")
    # Set default values as fallback
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.1:8b"
    UPLOAD_DIR = "uploaded_files"
    RATE_LIMIT_SECONDS = 2
    
    def print_config():
        print("Using fallback configuration due to import error")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    input_text: str
    model: str = "llama3.1:8b"
    enhanced_mode: bool = True
    session_id: Optional[str] = None
    language: str = "en"  # Added language parameter

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
        supported_languages = ['en', 'hi', 'mr']
        if v not in supported_languages:
            raise ValueError(f'Language must be one of: {supported_languages}')
        return v

# Global variables - now with language support
CURRENT_RAG_CHAINS = {}  # Store RAG chains per language
CURRENT_MODEL_KEY = None
CHAT_HISTORY = {}
RATE_LIMIT_TRACKER = {}
SYSTEM_STATUS = {
    "startup_time": time.time(),
    "total_queries": 0,
    "successful_queries": 0,
    "failed_queries": 0,
    "last_error": None,
    "supported_languages": ["en", "hi", "mr"]
}

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import random
    adjectives = ["sharp", "sleepy", "fluffy", "dazzling", "crazy", "bold", "happy", "silly"]
    animals = ["lion", "swan", "tiger", "elephant", "zebra", "giraffe", "panda", "koala"]
    return f"{random.choice(adjectives)}_{random.choice(animals)}_{os.urandom(2).hex()}_{int(time.time())}"

def generate_model_key(model: str, pdf_name: str, txt_name: str, language: str = "en") -> str:
    """Generate a unique key for the model configuration with language"""
    key_string = f"{model}_{pdf_name}_{txt_name}_{language}"
    return hashlib.md5(key_string.encode()).hexdigest()

def setup_upload_directory():
    """Create upload directory if it doesn't exist"""
    try:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)
            logger.info(f"Created upload directory: {UPLOAD_DIR}")
        return UPLOAD_DIR
    except Exception as e:
        logger.error(f"Failed to create upload directory: {e}")
        return None

def load_backend_files():
    """Load files from backend directory and initialize RAG systems for all languages"""
    global CURRENT_RAG_CHAINS, CURRENT_MODEL_KEY
    
    try:
        upload_dir = setup_upload_directory()
        if not upload_dir:
            return None, "Failed to setup upload directory"
        
        # Look for PDF and TXT files
        pdf_files = glob.glob(os.path.join(UPLOAD_DIR, "*.pdf"))
        txt_files = glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))
        
        logger.info(f"Found {len(pdf_files)} PDF files and {len(txt_files)} TXT files in {os.path.abspath(UPLOAD_DIR)}")
        
        if not (pdf_files or txt_files):
            return None, f"No files found in {os.path.abspath(UPLOAD_DIR)}. Please add PDF or TXT files to this directory."
            
        # Check Ollama connection first
        try:
            is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
            if not is_connected:
                return None, f"Ollama connection failed: {connection_msg}"
        except Exception as e:
            return None, f"Failed to check Ollama connection: {str(e)}"
        
        # Use the most recent files if multiple exist
        pdf_file = max(pdf_files, key=os.path.getmtime) if pdf_files else None
        txt_file = max(txt_files, key=os.path.getmtime) if txt_files else None
        
        pdf_name = os.path.basename(pdf_file) if pdf_file else "None"
        txt_name = os.path.basename(txt_file) if txt_file else "None"
        
        logger.info(f"Using files: PDF={pdf_name}, TXT={txt_name}")
        
        # Create file objects that mimic uploaded files
        class MockUploadedFile:
            def __init__(self, file_path):
                self.file_path = file_path
                
            def getvalue(self):
                with open(self.file_path, 'rb') as f:
                    return f.read()
        
        pdf_file_obj = MockUploadedFile(pdf_file) if pdf_file else None
        txt_file_obj = MockUploadedFile(txt_file) if txt_file else None
        
        # Build RAG chains for all supported languages
        supported_languages = SYSTEM_STATUS["supported_languages"]
        CURRENT_RAG_CHAINS = {}
        
        for language in supported_languages:
            try:
                logger.info(f"Building RAG chain for language: {language}")
                rag_chain = build_rag_chain_with_model_choice(
                    pdf_file_obj,
                    txt_file_obj,
                    OLLAMA_BASE_URL,
                    model_choice=OLLAMA_MODEL,
                    enhanced_mode=True,
                    target_language=language
                )
                CURRENT_RAG_CHAINS[language] = rag_chain
                logger.info(f"RAG chain built successfully for {language}")
            except Exception as e:
                logger.error(f"Failed to build RAG chain for {language}: {e}")
                return None, f"Failed to build RAG chain for {language}: {str(e)}"
        
        # Generate model key
        model_key = generate_model_key(OLLAMA_MODEL, pdf_name, txt_name, "multi")
        CURRENT_MODEL_KEY = model_key
        
        logger.info("All RAG chains built successfully")
        return model_key, f"RAG system initialized with {pdf_name}, {txt_name} for languages: {', '.join(supported_languages)}"
        
    except Exception as e:
        logger.error(f"Failed to load backend files: {e}")
        logger.error(traceback.format_exc())
        return None, str(e)

def check_rate_limit(session_id: str) -> tuple[bool, str]:
    """Simple rate limiting - configurable cooldown per session"""
    current_time = time.time()
    last_request = RATE_LIMIT_TRACKER.get(session_id, 0)
    
    time_since_last = current_time - last_request
    if time_since_last < RATE_LIMIT_SECONDS:
        remaining = RATE_LIMIT_SECONDS - time_since_last
        return False, f"Please wait {remaining:.1f} seconds before sending another message"
    
    RATE_LIMIT_TRACKER[session_id] = current_time
    return True, "OK"

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
        
        # Keep only last 50 messages per session
        CHAT_HISTORY[session_id] = CHAT_HISTORY[session_id][:50]
        
    except Exception as e:
        logger.error(f"Failed to add to chat history: {e}")

def validate_input(text: str, language: str = "en") -> tuple[bool, str]:
    """Validate user input with language awareness"""
    try:
        text = text.strip()
        
        if not text:
            return False, "Empty message"
        
        if len(text) > 500:
            return False, "Message too long (max 500 characters)"
        
        # Check for supported languages
        supported_languages = {"en", "hi", "mr"}
        if language not in supported_languages:
            return False, f"Language '{language}' not supported. Use: {', '.join(supported_languages)}"
        
        return True, "Valid"
        
    except Exception as e:
        logger.error(f"Input validation error: {e}")
        return False, "Validation error"

def detect_greeting(text: str) -> tuple[bool, str]:
    """Detect greeting intent and return a normalized key (e.g., 'good_morning')."""
    try:
        t = text.strip().lower()
        t = re.sub(r"[!.,🙂🙏✨⭐️]+", "", t)
        patterns = [
            (r"\bgood\s*morning\b|\bसुप्रभात\b|\bशुभ\s*सकाळ\b", "good_morning"),
            (r"\bgood\s*afternoon\b|\bशुभ\s*दुपार\b", "good_afternoon"),
            (r"\bgood\s*evening\b|\bशुभ\s*संध्या\b|\bशुभ\s*संध्याकाळ\b", "good_evening"),
            (r"\bhello\b|\bhey+\b|\bhii+\b|\bhi\b|\bनमस्ते\b|\bनमस्कार\b|\bहॅलो\b|\bहेलो\b|\bहाय\b", "hello"),
            (r"\bgood\s*night\b", "good_night"),
        ]
        for regex, key in patterns:
            if re.search(regex, t):
                return True, key
        return False, ""
    except Exception:
        return False, ""

def greeting_reply(language: str, key: str) -> str:
    """Return a specific greeting reply per detected key and language."""
    replies = {
        'en': {
            'good_morning': "Good Morning! How may I help you today?",
            'good_afternoon': "Good Afternoon! How may I help you today?",
            'good_evening': "Good Evening! How may I help you today?",
            'good_night': "Good Night! Before you go, is there anything I can help with?",
            'hello': "Hello! How may I help you today?",
        },
        'hi': {
            'good_morning': "सुप्रभात! मैं आज आपकी किस प्रकार सहायता कर सकता/सकती हूँ?",
            'good_afternoon': "शुभ दोपहर! मैं आपकी कैसे सहायता कर सकता/सकती हूँ?",
            'good_evening': "शुभ संध्या! मैं आपकी किस प्रकार मदद कर सकता/सकती हूँ?",
            'good_night': "शुभ रात्रि! जाने से पहले क्या मैं किसी तरह मदद कर सकता/सकती हूँ?",
            'hello': "नमस्ते! मैं आज आपकी किस प्रकार सहायता कर सकता/सकती हूँ?",
        },
        'mr': {
            'good_morning': "शुभ सकाळ! आज मी तुम्हाला कशात मदत करू शकतो/शकते?",
            'good_afternoon': "शुभ दुपार! मी कशी मदत करू शकतो/शकते?",
            'good_evening': "शुभ संध्याकाळ! मी कशात मदत करू शकतो/शकते?",
            'good_night': "शुभ रात्री! जाण्यापूर्वी मी काही मदत करू शकतो/शकते का?",
            'hello': "नमस्कार! आज मी तुम्हाला कशात मदत करू शकतो/शकते?",
        }
    }
    return replies.get(language, replies['en']).get(key, replies.get(language, replies['en'])['hello'])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("=" * 60)
    print("🚀 STARTING WSSD AI CHATBOT BACKEND (MULTILINGUAL)")
    print("=" * 60)
    
    # Print configuration
    try:
        print_config()
    except:
        print("Configuration printing failed, using defaults")
    
    try:
        # Check Ollama connection
        print("🔍 Checking Ollama connection...")
        try:
            is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
            if not is_connected:
                print(f"❌ {connection_msg}")
                print(f"💡 Please run: ollama run {OLLAMA_MODEL}")
            else:
                print(f"✅ {connection_msg}")
        except Exception as e:
            print(f"❌ Ollama check failed: {e}")
        
        # Initialize RAG system
        print("🔧 Initializing multilingual RAG system...")
        try:
            model_key, message = load_backend_files()
            if model_key:
                print(f"✅ {message}")
                print(f"🔑 Model key: {model_key}")
                print(f"🌐 Languages supported: {', '.join(SYSTEM_STATUS['supported_languages'])}")
            else:
                print(f"❌ Failed to initialize RAG system: {message}")
                print(f"📁 Please ensure PDF/TXT files exist in: {os.path.abspath(UPLOAD_DIR)}")
        except Exception as e:
            print(f"❌ RAG initialization failed: {e}")
        
        print("=" * 60)
        print("🎯 Backend ready! Access the API at:")
        print("   • Docs: http://localhost:8000/docs")
        print("   • Health: http://localhost:8000/health/")
        print("   • Status: http://localhost:8000/status/")
        print("=" * 60)
            
    except Exception as e:
        print(f"❌ Startup error: {e}")
        logger.error(traceback.format_exc())
    
    yield
    
    print("🔥 FastAPI application shutting down...")
    if CURRENT_RAG_CHAINS:
        print("🧹 Cleaning up RAG chains...")
    print("👋 Goodbye!")

# Initialize FastAPI app
app = FastAPI(
    title="WSSD AI ChatBot Backend (Multilingual)", 
    description="Local Ollama-powered RAG chatbot with multilingual support (English, Hindi, Marathi)",
    version="1.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
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
        try:
            ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        except Exception as e:
            ollama_connected, ollama_msg = False, f"Connection check failed: {str(e)}"
        
        uptime = time.time() - SYSTEM_STATUS["startup_time"]
        
        return {
            "message": "WSSD AI ChatBot Backend is running (Multilingual)",
            "mode": "local_ollama_multilingual",
            "version": "1.1.0",
            "uptime_seconds": round(uptime, 2),
            "docs": "/docs",
            "health": "/health/",
            "status": "/status/",
            "system_status": {
                "rag_initialized": len(CURRENT_RAG_CHAINS) > 0,
                "languages_available": list(CURRENT_RAG_CHAINS.keys()),
                "ollama_connected": ollama_connected,
                "ollama_message": ollama_msg,
                "files_found": bool(glob.glob(os.path.join(UPLOAD_DIR, "*.pdf")) or 
                                  glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))),
                "upload_directory": os.path.abspath(UPLOAD_DIR),
                "active_sessions": len(CHAT_HISTORY),
                "total_queries": SYSTEM_STATUS["total_queries"],
                "success_rate": round(
                    (SYSTEM_STATUS["successful_queries"] / max(1, SYSTEM_STATUS["total_queries"])) * 100, 2
                )
            },
            "config": {
                "ollama_url": OLLAMA_BASE_URL,
                "model": OLLAMA_MODEL,
                "upload_dir": UPLOAD_DIR,
                "rate_limit_seconds": RATE_LIMIT_SECONDS,
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
                'hi': "कृपया एक वैध प्रश्न प्रदान करें।",
                'mr': "कृपया एक वैध प्रश्न प्रदान करा।"
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

        # Quick greeting intent handling (mirrors user phrase)
        is_greet, greet_key = detect_greeting(input_text)
        if is_greet:
            SYSTEM_STATUS["successful_queries"] += 1
            session_id = request.session_id or "default"
            reply_text = greeting_reply(language, greet_key)
            add_to_chat_history(session_id, input_text, reply_text, language)
            return {"reply": reply_text, "language": language, "detected_language": language}

        # Check RAG system initialization for the requested language
        if language not in CURRENT_RAG_CHAINS:
            SYSTEM_STATUS["failed_queries"] += 1
            error_msg = {
                'en': f"System is not ready for {language}. Please check if documents are loaded and Ollama is running.",
                'hi': f"{language} के लिए सिस्टम तैयार नहीं है। कृपया जांचें कि दस्तावेज़ लोड हैं और Ollama चल रहा है।",
                'mr': f"{language} साठी सिस्टम तयार नाही. कृपया तपासा की दस्तऐवज लोड केले आहेत आणि Ollama चालू आहे."
            }
            return JSONResponse(
                status_code=503,
                content={"reply": error_msg.get(language, error_msg['en'])}
            )

        # Get the appropriate RAG chain for the language
        rag_chain = CURRENT_RAG_CHAINS[language]

        # Process the query using the RAG system with language specification
        try:
            result = process_scheme_query_with_retry(rag_chain, input_text, target_language=language)
            assistant_reply = result[0] if isinstance(result, tuple) else result or ""

            # Validate response
            if len(assistant_reply.strip()) < 5:
                SYSTEM_STATUS["failed_queries"] += 1
                error_msg = {
                    'en': "No relevant information found in the uploaded documents. Please ask a question that is covered in your PDF/TXT files.",
                    'hi': "अपलोड किए गए दस्तावेज़ों में कोई प्रासंगिक जानकारी नहीं मिली। कृपया ऐसा प्रश्न पूछें जो आपकी PDF/TXT फाइलों में शामिल हो।",
                    'mr': "अपलोड केलेल्या दस्तऐवजांमध्ये कोणतीही संबंधित माहिती सापडली नाही. कृपया तुमच्या PDF/TXT फाईल्समध्ये समाविष्ट असलेला प्रश्न विचारा."
                }
                return JSONResponse(
                    status_code=400,
                    content={"reply": error_msg.get(language, error_msg['en'])}
                )

            # Success
            SYSTEM_STATUS["successful_queries"] += 1
            
            # Add to chat history
            session_id = request.session_id or "default"
            add_to_chat_history(session_id, input_text, assistant_reply, language)
            
            return {
                "reply": assistant_reply,
                "language": language,
                "detected_language": result[2] if isinstance(result, tuple) and len(result) > 2 else language
            }

        except Exception as query_error:
            SYSTEM_STATUS["failed_queries"] += 1
            SYSTEM_STATUS["last_error"] = str(query_error)
            logger.error(f"Query processing error for language {language}: {query_error}")
            
            error_msg = {
                'en': "An error occurred while processing your query. Please try again later.",
                'hi': "आपके प्रश्न को संसाधित करते समय एक त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।",
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
        try:
            ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        except Exception as e:
            ollama_connected, ollama_msg = False, f"Health check failed: {str(e)}"
        
        system_status = "healthy" if (ollama_connected and len(CURRENT_RAG_CHAINS) > 0) else "degraded"
        if not ollama_connected:
            system_status = "critical"
        
        uptime = time.time() - SYSTEM_STATUS["startup_time"]
        
        return {
            "status": system_status,
            "timestamp": time.time(),
            "uptime_seconds": round(uptime, 2),
            "ollama_status": {
                "connected": ollama_connected,
                "message": ollama_msg,
                "base_url": OLLAMA_BASE_URL,
                "model": OLLAMA_MODEL
            },
            "rag_status": {
                "initialized": len(CURRENT_RAG_CHAINS) > 0,
                "languages_available": list(CURRENT_RAG_CHAINS.keys()),
                "model_key": CURRENT_MODEL_KEY
            },
            "system_info": {
                "active_sessions": len(CHAT_HISTORY),
                "rate_limited_sessions": len(RATE_LIMIT_TRACKER),
                "upload_directory": UPLOAD_DIR,
                "files_available": bool(glob.glob(os.path.join(UPLOAD_DIR, "*.pdf")) or 
                                     glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))),
                "total_queries": SYSTEM_STATUS["total_queries"],
                "successful_queries": SYSTEM_STATUS["successful_queries"],
                "failed_queries": SYSTEM_STATUS["failed_queries"],
                "success_rate": round(
                    (SYSTEM_STATUS["successful_queries"] / max(1, SYSTEM_STATUS["total_queries"])) * 100, 2
                ),
                "supported_languages": SYSTEM_STATUS["supported_languages"]
            },
            "last_error": SYSTEM_STATUS["last_error"]
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

# Additional endpoints...
@app.get("/suggestions/")
async def get_suggestions(language: str = "en"):
    """Get suggested questions for the UI in specified language"""
    suggestions_by_language = {
        "en": [
            "What government schemes are available?",
            "How do I apply for benefits?",
            "What are the eligibility criteria?",
            "Where can I get more information?",
            "What documents are required?",
            "How long does the process take?"
        ],
        "hi": [
            "सरकारी योजनाएं क्या उपलब्ध हैं?",
            "मुझे कैसे आवेदन करना चाहिए?",
            "पात्रता मापदंड क्या हैं?",
            "मुझे और जानकारी कहाँ मिल सकती है?",
            "कौन से दस्तावेज़ चाहिए?",
            "प्रक्रिया में कितना समय लगता है?"
        ],
        "mr": [
            "कोणत्या सरकारी योजना उपलब्ध आहेत?",
            "मी कसा अर्ज करू?",
            "पात्रता निकष काय आहेत?",
            "मला अधिक माहिती कुठे मिळेल?",
            "कोणते कागदपत्रे लागतील?",
            "प्रक्रियेला किती वेळ लागतो?"
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
            "hi": {"name": "Hindi", "native_name": "हिंदी"},
            "mr": {"name": "Marathi", "native_name": "मराठी"}
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")