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

# Import with error handling
try:
    from rag_services import (  # Fixed import path - remove core/
        build_rag_chain_with_model_choice, 
        process_scheme_query_with_retry, 
        detect_language,
        check_ollama_connection,
        clear_query_cache
    )
    from config import (  # Fixed import path - remove utils/
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

    @field_validator('input_text')  # Fixed validator syntax
    @classmethod
    def validate_input_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Input text cannot be empty')
        if len(v) > 500:
            raise ValueError('Input text too long (max 500 characters)')
        return v.strip()

# Global variables
CURRENT_RAG_CHAIN = None
CURRENT_MODEL_KEY = None
CHAT_HISTORY = {}
RATE_LIMIT_TRACKER = {}
SYSTEM_STATUS = {
    "startup_time": time.time(),
    "total_queries": 0,
    "successful_queries": 0,
    "failed_queries": 0,
    "last_error": None
}

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import random
    adjectives = ["sharp", "sleepy", "fluffy", "dazzling", "crazy", "bold", "happy", "silly"]
    animals = ["lion", "swan", "tiger", "elephant", "zebra", "giraffe", "panda", "koala"]
    return f"{random.choice(adjectives)}_{random.choice(animals)}_{os.urandom(2).hex()}_{int(time.time())}"

def generate_model_key(model: str, pdf_name: str, txt_name: str) -> str:
    """Generate a unique key for the model configuration"""
    key_string = f"{model}_{pdf_name}_{txt_name}"
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
    """Load files from backend directory and initialize RAG system"""
    global CURRENT_RAG_CHAIN, CURRENT_MODEL_KEY
    
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
        
        # Generate model key
        model_key = generate_model_key(OLLAMA_MODEL, pdf_name, txt_name)
        
        # Create file objects that mimic uploaded files
        class MockUploadedFile:
            def __init__(self, file_path):
                self.file_path = file_path
                
            def getvalue(self):
                with open(self.file_path, 'rb') as f:
                    return f.read()
        
        pdf_file_obj = MockUploadedFile(pdf_file) if pdf_file else None
        txt_file_obj = MockUploadedFile(txt_file) if txt_file else None
        
        # Build RAG chain
        logger.info("Building RAG chain...")
        rag_chain = build_rag_chain_with_model_choice(
            pdf_file_obj,
            txt_file_obj,
            OLLAMA_BASE_URL,
            model_choice=OLLAMA_MODEL,
            enhanced_mode=True
        )
        
        CURRENT_RAG_CHAIN = rag_chain
        CURRENT_MODEL_KEY = model_key
        
        logger.info("RAG chain built successfully")
        return model_key, f"RAG system initialized with {pdf_name}, {txt_name}"
        
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

def add_to_chat_history(session_id: str, user_msg: str, bot_msg: str):
    """Add message to chat history"""
    try:
        if session_id not in CHAT_HISTORY:
            CHAT_HISTORY[session_id] = []
        
        CHAT_HISTORY[session_id].insert(0, {
            "user": user_msg,
            "assistant": bot_msg,
            "timestamp": time.strftime("%H:%M:%S"),
            "session_id": session_id,
            "created_at": time.time()
        })
        
        # Keep only last 50 messages per session
        CHAT_HISTORY[session_id] = CHAT_HISTORY[session_id][:50]
        
    except Exception as e:
        logger.error(f"Failed to add to chat history: {e}")

def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input"""
    try:
        text = text.strip()
        
        if not text:
            return False, "Empty message"
        
        if len(text) > 500:
            return False, "Message too long (max 500 characters)"
        
        # Check for supported languages
        import re
        supported_patterns = {
            'en': r'[a-zA-Z]',
            'hi': r'[\u0900-\u097F]',
            'mr': r'[\u0900-\u097F]'
        }
        
        is_supported = any(re.search(pattern, text) for pattern in supported_patterns.values())
        if not is_supported:
            return False, "Only English, Hindi, and Marathi are supported"
        
        return True, "Valid"
        
    except Exception as e:
        logger.error(f"Input validation error: {e}")
        return False, "Validation error"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("=" * 60)
    print("🚀 STARTING SAMNEX AI CHATBOT BACKEND")
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
        print("🔧 Initializing RAG system...")
        try:
            model_key, message = load_backend_files()
            if model_key:
                print(f"✅ {message}")
                print(f"🔑 Model key: {model_key}")
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
    
    print("🔄 FastAPI application shutting down...")
    if CURRENT_RAG_CHAIN:
        print("🧹 Cleaning up RAG chain...")
    print("👋 Goodbye!")

# Initialize FastAPI app
app = FastAPI(
    title="SAMNEX AI ChatBot Backend", 
    description="Local Ollama-powered RAG chatbot with multilingual support",
    version="1.0.0",
    lifespan=lifespan
)

# CRITICAL: Add CORS middleware BEFORE other middleware and routes
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
            "message": "SAMNEX AI ChatBot Backend is running",
            "mode": "local_ollama",
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "docs": "/docs",
            "health": "/health/",
            "status": "/status/",
            "system_status": {
                "rag_initialized": CURRENT_RAG_CHAIN is not None,
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
                "rate_limit_seconds": RATE_LIMIT_SECONDS
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
    """Main query processing endpoint"""
    start_time = time.time()
    SYSTEM_STATUS["total_queries"] += 1
    
    try:
        logger.info(f"Processing query: '{request.input_text[:50]}...' from session {request.session_id}")
        
        # Validate input
        is_valid, validation_msg = validate_input(request.input_text)
        if not is_valid:
            logger.warning(f"Invalid input: {validation_msg}")
            return JSONResponse(
                status_code=400,
                content={
                    "reply": "I'm sorry, I cannot assist with that topic. For more details, please contact the 104/102 helpline numbers.",
                    "error": validation_msg,
                    "status": "error"
                }
            )
        
        # Get or generate session ID
        session_id = request.session_id or generate_session_id()
        logger.info(f"Using session ID: {session_id}")
        
        # Check rate limit
        rate_ok, rate_msg = check_rate_limit(session_id)
        if not rate_ok:
            logger.warning(f"Rate limit exceeded for session {session_id}")
            return JSONResponse(
                status_code=429,
                content={
                    "reply": "Please wait a moment before sending another message.",
                    "error": rate_msg,
                    "status": "rate_limited"
                }
            )
        
        # Check system status
        if not CURRENT_RAG_CHAIN:
            logger.error("RAG chain not initialized")
            return JSONResponse(
                status_code=503,
                content={
                    "reply": "System is not ready. Please check if documents are loaded and Ollama is running.",
                    "error": "RAG system not initialized",
                    "status": "service_unavailable"
                }
            )
        
        # Check Ollama connection
        try:
            is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
            if not is_connected:
                logger.error(f"Ollama connection failed: {connection_msg}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "reply": f"AI service unavailable: {connection_msg}. Please try again later.",
                        "error": connection_msg,
                        "status": "ollama_unavailable"
                    }
                )
        except Exception as e:
            logger.error(f"Ollama connection check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "reply": "Unable to verify AI service status. Please try again later.",
                    "error": str(e),
                    "status": "connection_error"
                }
            )
        
        # Process query
        logger.info("Sending query to RAG chain...")
        try:
            result = process_scheme_query_with_retry(CURRENT_RAG_CHAIN, request.input_text)
        except Exception as e:
            logger.error(f"RAG processing error: {e}")
            SYSTEM_STATUS["failed_queries"] += 1
            SYSTEM_STATUS["last_error"] = str(e)
            return JSONResponse(
                status_code=500,
                content={
                    "reply": "I encountered an error processing your request. Please try again.",
                    "error": str(e),
                    "status": "processing_error"
                }
            )
        
        # Extract response
        if isinstance(result, tuple) and len(result) > 0:
            assistant_reply = result[0]
        else:
            assistant_reply = str(result)
        
        # Validate response
        if not assistant_reply or len(assistant_reply.strip()) < 5:
            assistant_reply = "I couldn't find relevant information in the documents. Please ask questions related to the uploaded content or try rephrasing your query."
        
        # Clean up response
        assistant_reply = assistant_reply.strip()
        
        # Add to chat history
        add_to_chat_history(session_id, request.input_text, assistant_reply)
        
        # Update success metrics
        SYSTEM_STATUS["successful_queries"] += 1
        processing_time = time.time() - start_time
        
        logger.info(f"Query processed successfully in {processing_time:.2f}s")
        
        return {
            "reply": assistant_reply,
            "session_id": session_id,
            "model_used": OLLAMA_MODEL,
            "timestamp": time.time(),
            "processing_time": round(processing_time, 3),
            "language": detect_language(request.input_text) if 'detect_language' in globals() else 'unknown',
            "status": "success"
        }
        
    except Exception as e:
        SYSTEM_STATUS["failed_queries"] += 1
        SYSTEM_STATUS["last_error"] = str(e)
        processing_time = time.time() - start_time
        
        logger.error(f"Query processing error after {processing_time:.2f}s: {e}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={
                "reply": "I encountered an error processing your request. Please try again or contact support.",
                "error": str(e),
                "processing_time": round(processing_time, 3),
                "status": "error"
            }
        )

@app.get("/health/")
async def health_check():
    """System health check endpoint"""
    try:
        try:
            ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        except Exception as e:
            ollama_connected, ollama_msg = False, f"Health check failed: {str(e)}"
        
        system_status = "healthy" if (ollama_connected and CURRENT_RAG_CHAIN) else "degraded"
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
                "initialized": CURRENT_RAG_CHAIN is not None,
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
                )
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
async def get_suggestions():
    """Get suggested questions for the UI"""
    suggestions = [
        "What government schemes are available?",
        "How do I apply for benefits?",
        "What are the eligibility criteria?",
        "Where can I get more information?",
        "What documents are required?",
        "How long does the process take?",
        "सरकारी योजनाएं क्या उपलब्ध हैं?",
        "मुझे कैसे आवेदन करना चाहिए?",
        "पात्रता मापदंड क्या हैं?"
    ]
    
    return {
        "suggestions": suggestions,
        "total": len(suggestions)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")