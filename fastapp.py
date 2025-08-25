from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import io
import json
import hashlib
import os
import logging
import glob
from contextlib import asynccontextmanager

# Core services
from core.rag_services import (
    build_rag_chain_with_model_choice, 
    process_scheme_query_with_retry, 
    detect_language,
    check_ollama_connection
)
from utils.config import OLLAMA_BASE_URL, OLLAMA_MODEL, UPLOAD_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    input_text: str
    model: str = "hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0"
    enhanced_mode: bool = True
    session_id: Optional[str] = None

# Global variables
CURRENT_RAG_CHAIN = None
CURRENT_MODEL_KEY = None
CHAT_HISTORY = {}  # In-memory chat storage
RATE_LIMIT_TRACKER = {}  # Simple rate limiting

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import random
    adjectives = ["sharp", "sleepy", "fluffy", "dazzling", "crazy", "bold", "happy", "silly"]
    animals = ["lion", "swan", "tiger", "elephant", "zebra", "giraffe", "panda", "koala"]
    return f"{random.choice(adjectives)}_{random.choice(animals)}_{os.urandom(2).hex()}"

def generate_model_key(model: str, pdf_name: str, txt_name: str) -> str:
    """Generate a unique key for the model configuration"""
    key_string = f"{model}_{pdf_name}_{txt_name}"
    return hashlib.md5(key_string.encode()).hexdigest()

def setup_upload_directory():
    """Create upload directory if it doesn't exist"""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    return UPLOAD_DIR

def load_backend_files():
    """Load files from backend directory and initialize RAG system"""
    global CURRENT_RAG_CHAIN, CURRENT_MODEL_KEY
    
    setup_upload_directory()
    
    # Look for PDF and TXT files
    pdf_files = glob.glob(os.path.join(UPLOAD_DIR, "*.pdf"))
    txt_files = glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))
    
    if not (pdf_files or txt_files):
        return None, "No files found in backend directory"
        
    try:
        # Check Ollama connection first
        is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        if not is_connected:
            return None, f"Ollama connection failed: {connection_msg}"
        
        # Use the most recent files if multiple exist
        pdf_file = max(pdf_files, key=os.path.getmtime) if pdf_files else None
        txt_file = max(txt_files, key=os.path.getmtime) if txt_files else None
        
        pdf_name = os.path.basename(pdf_file) if pdf_file else "None"
        txt_name = os.path.basename(txt_file) if txt_file else "None"
        
        # Generate model key
        model_key = generate_model_key(OLLAMA_MODEL, pdf_name, txt_name)
        
        # Build RAG chain
        pdf_bytes = open(pdf_file, 'rb').read() if pdf_file else None
        txt_bytes = open(txt_file, 'rb').read() if txt_file else None
        
        rag_chain = build_rag_chain_with_model_choice(
            io.BytesIO(pdf_bytes) if pdf_bytes else None,
            io.BytesIO(txt_bytes) if txt_bytes else None,
            OLLAMA_BASE_URL,
            model_choice=OLLAMA_MODEL,
            enhanced_mode=True
        )
        
        CURRENT_RAG_CHAIN = rag_chain
        CURRENT_MODEL_KEY = model_key
        
        return model_key, f"RAG system initialized successfully with {pdf_name}, {txt_name}"
        
    except Exception as e:
        logger.error(f"Failed to load backend files: {e}")
        return None, str(e)

def check_rate_limit(session_id: str) -> bool:
    """Simple rate limiting - 1 request per 2 seconds per session"""
    current_time = time.time()
    last_request = RATE_LIMIT_TRACKER.get(session_id, 0)
    
    if current_time - last_request < 2:  # 2 second cooldown
        return False
    
    RATE_LIMIT_TRACKER[session_id] = current_time
    return True

def add_to_chat_history(session_id: str, user_msg: str, bot_msg: str):
    """Add message to chat history"""
    if session_id not in CHAT_HISTORY:
        CHAT_HISTORY[session_id] = []
    
    CHAT_HISTORY[session_id].insert(0, {
        "user": user_msg,
        "assistant": bot_msg,
        "timestamp": time.strftime("%H:%M:%S"),
        "session_id": session_id
    })
    
    # Keep only last 50 messages
    CHAT_HISTORY[session_id] = CHAT_HISTORY[session_id][:50]

def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input"""
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
    
    # Check for inappropriate queries
    lowered = text.lower()
    inappropriate_keywords = ['talk like', 'speak like', 'act like', 'pretend to be']
    if any(keyword in lowered for keyword in inappropriate_keywords):
        return False, "Inappropriate query type"
    
    return True, "Valid"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("Starting FastAPI application with Local Ollama...")
    print(f"Ollama Base URL: {OLLAMA_BASE_URL}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    
    try:
        # Check Ollama connection
        is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        if not is_connected:
            print(f"❌ {connection_msg}")
            print(f"Please run: ollama run {OLLAMA_MODEL}")
        else:
            print(f"✅ {connection_msg}")
        
        # Initialize RAG system
        model_key, message = load_backend_files()
        if model_key:
            print(f"✅ {message}")
            print(f"Model key: {model_key}")
        else:
            print(f"❌ Failed to initialize RAG system: {message}")
            print(f"Please ensure PDF/TXT files exist in: {os.path.abspath(UPLOAD_DIR)}")
            
    except Exception as e:
        print(f"Startup error: {e}")
    
    yield
    print("FastAPI application shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="SAMNEX AI ChatBot Backend", 
    description="Local Ollama-powered RAG chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with system status"""
    try:
        ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        
        return {
            "message": "SAMNEX AI ChatBot Backend is running",
            "mode": "local_ollama",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health/",
            "system_status": {
                "rag_initialized": CURRENT_RAG_CHAIN is not None,
                "ollama_connected": ollama_connected,
                "ollama_message": ollama_msg,
                "files_found": bool(glob.glob(os.path.join(UPLOAD_DIR, "*.pdf")) or 
                                  glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))),
                "upload_directory": os.path.abspath(UPLOAD_DIR),
                "active_sessions": len(CHAT_HISTORY)
            },
            "config": {
                "ollama_url": OLLAMA_BASE_URL,
                "model": OLLAMA_MODEL,
                "upload_dir": UPLOAD_DIR
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"System error: {str(e)}"}
        )

@app.post("/query/")
async def process_query(request: QueryRequest):
    """Main query processing endpoint"""
    try:
        # Validate input
        is_valid, validation_msg = validate_input(request.input_text)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"reply": "I'm sorry, I cannot assist with that topic. For more details, please contact the 104/102 helpline numbers."}
            )
        
        # Get or generate session ID
        session_id = request.session_id or generate_session_id()
        
        # Check rate limit
        if not check_rate_limit(session_id):
            return JSONResponse(
                status_code=429,
                content={"reply": "Please wait a moment before sending another message."}
            )
        
        # Check system status
        if not CURRENT_RAG_CHAIN:
            return JSONResponse(
                status_code=503,
                content={"reply": "System is not ready. Please check if documents are loaded and Ollama is running."}
            )
        
        # Check Ollama connection
        is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        if not is_connected:
            return JSONResponse(
                status_code=503,
                content={"reply": f"AI service unavailable: {connection_msg}. Please try again later."}
            )
        
        # Process query
        result = process_scheme_query_with_retry(CURRENT_RAG_CHAIN, request.input_text)
        assistant_reply = result[0] if isinstance(result, tuple) else str(result)
        
        # Validate response
        if not assistant_reply or len(assistant_reply.strip()) < 10:
            assistant_reply = "I couldn't find relevant information in the documents. Please ask questions related to the uploaded content."
        
        # Clean up response
        assistant_reply = assistant_reply.strip()
        
        # Add to chat history
        add_to_chat_history(session_id, request.input_text, assistant_reply)
        
        return {
            "reply": assistant_reply,
            "session_id": session_id,
            "model_used": OLLAMA_MODEL,
            "timestamp": time.time(),
            "language": detect_language(request.input_text)
        }
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return JSONResponse(
            status_code=500,
            content={"reply": "I encountered an error processing your request. Please try again or contact support."}
        )

@app.get("/health/")
async def health_check():
    """System health check endpoint"""
    try:
        ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        
        system_status = "healthy" if (ollama_connected and CURRENT_RAG_CHAIN) else "degraded"
        
        return {
            "status": system_status,
            "timestamp": time.time(),
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
                                     glob.glob(os.path.join(UPLOAD_DIR, "*.txt")))
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "timestamp": time.time()
            }
        )

@app.get("/suggestions/")
async def get_suggestions():
    """Get suggested questions for the UI"""
    suggestions = [
        "What government schemes are available?",
        "How do I apply for benefits?",
        "What are the eligibility criteria?",
        "Where can I get more information?",
        "What documents are required?",
        "How long does the process take?"
    ]
    
    return {"suggestions": suggestions}

@app.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a specific session"""
    history = CHAT_HISTORY.get(session_id, [])
    return {
        "session_id": session_id,
        "chat_history": history,
        "message_count": len(history)
    }

@app.delete("/chat-history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a specific session"""
    if session_id in CHAT_HISTORY:
        del CHAT_HISTORY[session_id]
        return {"message": f"Chat history cleared for session {session_id}"}
    else:
        return {"message": f"No chat history found for session {session_id}"}

@app.post("/sessions/start")
async def start_new_session():
    """Start a new chat session"""
    session_id = generate_session_id()
    CHAT_HISTORY[session_id] = []
    
    return {
        "session_id": session_id,
        "message": "New session started",
        "timestamp": time.time()
    }

@app.get("/status/")
async def get_detailed_status():
    """Get detailed system status"""
    ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    return {
        "system": {
            "status": "operational" if (ollama_connected and CURRENT_RAG_CHAIN) else "degraded",
            "version": "1.0.0",
            "mode": "local_ollama",
            "uptime": time.time()
        },
        "services": {
            "ollama": {
                "connected": ollama_connected,
                "message": ollama_msg,
                "url": OLLAMA_BASE_URL,
                "model": OLLAMA_MODEL
            },
            "rag": {
                "initialized": CURRENT_RAG_CHAIN is not None,
                "model_key": CURRENT_MODEL_KEY
            }
        },
        "resources": {
            "active_sessions": len(CHAT_HISTORY),
            "upload_directory": os.path.abspath(UPLOAD_DIR),
            "available_files": {
                "pdf": len(glob.glob(os.path.join(UPLOAD_DIR, "*.pdf"))),
                "txt": len(glob.glob(os.path.join(UPLOAD_DIR, "*.txt")))
            }
        },
        "features": {
            "multilingual_support": True,
            "rate_limiting": True,
            "session_management": True,
            "local_processing": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")