from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import io
import base64
import json
import hashlib
import redis
import pickle
from contextlib import asynccontextmanager
import os
import random
import logging
import re
import glob

def translate_text(text: str, target_lang: str) -> str:
    """
    Dummy translation function. Replace with real translation API/service.
    Supported: 'hi' (Hindi), 'mr' (Marathi), 'en' (English)
    """
    # For now, just return the original text (no translation)
    # Integrate with Google Translate, Microsoft Translator, or similar for real use
    return text

# Core services - Updated imports for Ollama local mode
from core.rag_services import (
    build_rag_chain_with_model_choice, 
    process_scheme_query_with_retry, 
    detect_language,
    check_ollama_connection
)
from utils.config import load_env_vars, OLLAMA_BASE_URL, OLLAMA_MODEL

load_env_vars()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost") 
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

class RedisManager:
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            print("Redis connected successfully")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        return self.redis_client is not None
    
    def set_rag_chain(self, key: str, rag_chain, expire_hours: int = 24):
        if not self.is_available():
            return False
        try:
            serialized = pickle.dumps(rag_chain)
            self.redis_client.setex(f"rag_chain:{key}", expire_hours * 3600, serialized)
            return True
        except Exception as e:
            print(f"Failed to store RAG chain: {e}")
            return False
    
    def get_rag_chain(self, key: str):
        if not self.is_available():
            return None
        try:
            data = self.redis_client.get(f"rag_chain:{key}")
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            print(f"Failed to retrieve RAG chain: {e}")
            return None
    
    def set_chat_history(self, session_id: str, history: List[dict], expire_hours: int = 48):
        if not self.is_available():
            return False
        try:
            serialized = json.dumps(history)
            self.redis_client.setex(f"chat:{session_id}", expire_hours * 3600, serialized)
            return True
        except Exception as e:
            print(f"Failed to store chat history: {e}")
            return False
    
    def get_chat_history(self, session_id: str) -> List[dict]:
        if not self.is_available():
            return []
        try:
            data = self.redis_client.get(f"chat:{session_id}")
            if data:
                return json.loads(data.decode('utf-8'))
            return []
        except Exception as e:
            print(f"Failed to retrieve chat history: {e}")
            return []
    
    def add_chat_message(self, session_id: str, message: dict):
        history = self.get_chat_history(session_id)
        history.insert(0, message)
        history = history[:50]
        self.set_chat_history(session_id, history)
    
    def set_rate_limit(self, key: str, expire_seconds: int = 60):
        if not self.is_available():
            return False
        try:
            self.redis_client.setex(f"rate_limit:{key}", expire_seconds, "1")
            return True
        except Exception:
            return False
    
    def check_rate_limit(self, key: str) -> bool:
        if not self.is_available():
            return False
        try:
            return self.redis_client.exists(f"rate_limit:{key}") > 0
        except Exception:
            return False

redis_manager = RedisManager()

class LangChainStateManager:
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self._rag_cache = {}
        self._memory_fallback = {}
    
    def store_rag_chain_config(self, model_key: str, 
                              pdf_bytes: Optional[bytes] = None,
                              txt_bytes: Optional[bytes] = None,
                              model_choice: str = "hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0",
                              enhanced_mode: bool = True,
                              pdf_name: str = "None",
                              txt_name: str = "None",
                              rag_chain=None):
        config = {
            "model_choice": model_choice,
            "enhanced_mode": enhanced_mode,
            "pdf_name": pdf_name,
            "txt_name": txt_name,
            "timestamp": time.time(),
            "pdf_content": base64.b64encode(pdf_bytes).decode() if pdf_bytes else None,
            "txt_content": base64.b64encode(txt_bytes).decode() if txt_bytes else None,
            "pdf_size": len(pdf_bytes) if pdf_bytes else 0,
            "txt_size": len(txt_bytes) if txt_bytes else 0,
        }
        stored = False
        if self.redis.is_available():
            try:
                config_json = json.dumps(config)
                self.redis.redis_client.setex(
                    f"rag_config:{model_key}", 
                    24 * 3600,
                    config_json
                )
                stored = True
                logging.info(f"RAG config stored in Redis for key: {model_key}")
            except Exception as e:
                logging.error(f"Failed to store config in Redis: {e}")
        if not stored:
            self._memory_fallback[f"rag_config:{model_key}"] = config
            logging.info(f"RAG config stored in memory for key: {model_key}")
        if rag_chain:
            self._rag_cache[model_key] = {
                "chain": rag_chain,
                "created_at": time.time()
            }
            logging.info(f"RAG chain cached in memory for key: {model_key}")
        return True
    
    def get_rag_chain(self, model_key: str, ollama_base_url: str):
        if model_key in self._rag_cache:
            cached = self._rag_cache[model_key]
            if time.time() - cached["created_at"] < 3600:
                logging.info(f"Returning cached RAG chain for key: {model_key}")
                return cached["chain"]
            else:
                del self._rag_cache[model_key]
                logging.info(f"Removed stale cached RAG chain for key: {model_key}")
        config = self._get_rag_config(model_key)
        if not config:
            logging.warning(f"No config found for RAG key: {model_key}")
            return None
        rag_chain = self._rebuild_rag_chain(config, ollama_base_url)
        if rag_chain:
            self._rag_cache[model_key] = {
                "chain": rag_chain,
                "created_at": time.time()
            }
            logging.info(f"RAG chain rebuilt and cached for key: {model_key}")
        return rag_chain
    
    def _get_rag_config(self, model_key: str) -> Optional[Dict[str, Any]]:
        if self.redis.is_available():
            try:
                data = self.redis.redis_client.get(f"rag_config:{model_key}")
                if data:
                    return json.loads(data.decode('utf-8'))
            except Exception as e:
                logging.error(f"Failed to get config from Redis: {e}")
        return self._memory_fallback.get(f"rag_config:{model_key}")
    
    def _rebuild_rag_chain(self, config: Dict[str, Any], ollama_base_url: str):
        try:
            from core.rag_services import build_rag_chain_with_model_choice
            pdf_bytes = None
            txt_bytes = None
            if config.get("pdf_content"):
                pdf_bytes = base64.b64decode(config["pdf_content"])
            if config.get("txt_content"):
                txt_bytes = base64.b64decode(config["txt_content"])
            pdf_io = io.BytesIO(pdf_bytes) if pdf_bytes else None
            txt_io = io.BytesIO(txt_bytes) if txt_bytes else None
            rag_chain = build_rag_chain_with_model_choice(
                pdf_io,
                txt_io,
                ollama_base_url,
                model_choice=config["model_choice"],
                enhanced_mode=config["enhanced_mode"]
            )
            logging.info("RAG chain rebuilt successfully")
            return rag_chain
        except Exception as e:
            logging.error(f"Failed to rebuild RAG chain: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def clear_cache(self, model_key: Optional[str] = None):
        if model_key:
            self._rag_cache.pop(model_key, None)
            logging.info(f"Cleared cache for key: {model_key}")
        else:
            self._rag_cache.clear()
            logging.info("Cleared all RAG chain cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cached_chains": len(self._rag_cache),
            "memory_configs": len(self._memory_fallback),
            "redis_available": self.redis.is_available()
        }
    
    def get_chat_history(self, session_id: str = "default"):
        if self.redis.is_available():
            return self.redis.get_chat_history(session_id)
        return []
    
    def add_chat_message(self, message: dict, session_id: str = "default"):
        if self.redis.is_available():
            self.redis.add_chat_message(session_id, message)
            # Always also add to the "default" session if not already default
            if session_id != "default":
                self.redis.add_chat_message("default", message)
        else:
            # In-memory fallback
            key = f"chat:{session_id}"
            default_key = "chat:default"
            self._memory_fallback.setdefault(key, []).insert(0, message)
            self._memory_fallback[key] = self._memory_fallback[key][:50]
            if session_id != "default":
                self._memory_fallback.setdefault(default_key, []).insert(0, message)
                self._memory_fallback[default_key] = self._memory_fallback[default_key][:50]

state_manager = LangChainStateManager(redis_manager)

def get_session_id(session_id: Optional[str] = None) -> str:
    return session_id or "default"

def generate_model_key(model: str, enhanced: bool, pdf_name: str, txt_name: str) -> str:
    key_string = f"{model}_{enhanced}_{pdf_name}_{txt_name}"
    return hashlib.md5(key_string.encode()).hexdigest()

_last_query_time = {}

def check_rate_limit_delay(session_id="default", min_delay=2):
    """Check if we need to wait before making another query (fallback, per session_id)"""
    current_time = time.time()
    last_time = _last_query_time.get(session_id, 0)
    time_since_last = current_time - last_time
    if time_since_last < min_delay:
        wait_time = min_delay - time_since_last
        return wait_time
    _last_query_time[session_id] = current_time
    return 0

class QueryRequest(BaseModel):
    input_text: str
    model: str = "hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0"
    enhanced_mode: bool = True
    session_id: Optional[str] = None
    model_key: Optional[str] = None

UPLOAD_DIR = "uploaded_files"
CURRENT_MODEL_KEY = None  # Global variable 

def setup_upload_directory():
    """Create upload directory if it doesn't exist"""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    return UPLOAD_DIR

# Add this function to handle backend file loading
def load_backend_files():
    """Load files from backend directory and initialize RAG system"""
    global CURRENT_MODEL_KEY
    
    setup_upload_directory()
    
    # Look for PDF and TXT files
    pdf_files = glob.glob(os.path.join(UPLOAD_DIR, "*.pdf"))
    txt_files = glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))
    
    if not (pdf_files or txt_files):
        return None, "No files found in backend"
        
    try:
        # Check Ollama connection first
        is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        if not is_connected:
            return None, f"Ollama connection failed: {connection_msg}"
        
        # Use the last modified files if multiple exist
        pdf_file = max(pdf_files, key=os.path.getmtime) if pdf_files else None
        txt_file = max(txt_files, key=os.path.getmtime) if txt_files else None
        
        pdf_name = os.path.basename(pdf_file) if pdf_file else "None"
        txt_name = os.path.basename(txt_file) if txt_file else "None"
        
        # Generate model key
        model_key = generate_model_key(OLLAMA_MODEL, True, pdf_name, txt_name)
        
        # Check if RAG chain already exists
        existing_chain = state_manager.get_rag_chain(model_key, OLLAMA_BASE_URL)
        if existing_chain:
            CURRENT_MODEL_KEY = model_key
            return model_key, "Using existing RAG system"
            
        # Build new RAG chain
        pdf_bytes = open(pdf_file, 'rb').read() if pdf_file else None
        txt_bytes = open(txt_file, 'rb').read() if txt_file else None
        
        rag_chain = build_rag_chain_with_model_choice(
            io.BytesIO(pdf_bytes) if pdf_bytes else None,
            io.BytesIO(txt_bytes) if txt_bytes else None,
            OLLAMA_BASE_URL,
            model_choice=OLLAMA_MODEL,
            enhanced_mode=True
        )
        
        # Store configuration
        state_manager.store_rag_chain_config(
            model_key=model_key,
            pdf_bytes=pdf_bytes,
            txt_bytes=txt_bytes,
            pdf_name=pdf_name,
            txt_name=txt_name,
            rag_chain=rag_chain
        )
        
        CURRENT_MODEL_KEY = model_key
        return model_key, "RAG system initialized successfully"
        
    except Exception as e:
        logging.error(f"Failed to load backend files: {e}")
        return None, str(e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for FastAPI"""
    print("Starting up FastAPI application with Local Ollama...")
    print(f"Ollama Base URL: {OLLAMA_BASE_URL}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    
    try:
        # Check Ollama connection first
        is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        if not is_connected:
            print(f"❌ {connection_msg}")
            print("Please run: ollama run hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0")
        else:
            print(f"✅ {connection_msg}")
        
        model_key, message = load_backend_files()
        if model_key:
            print(f"✅ RAG system initialized successfully: {message}")
            print(f"Using model key: {model_key}")
        else:
            print(f"❌ Failed to initialize RAG system: {message}")
            print("Please ensure PDF/TXT files exist in the uploaded_files directory")
    except Exception as e:
        print(f"Startup error: {e}")
        
    yield
    
    if redis_manager.is_available():
        redis_manager.redis_client.close()
    print("FastAPI application shutting down...")

app = FastAPI(title="SAMNEX AI - Local Ollama", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    try:
        redis_status = redis_manager.is_available()
        ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
        
        return {
            "message": "AI Agent FastAPI backend is running (Local Ollama Mode).",
            "mode": "local_ollama",
            "docs": "/docs", 
            "health": "/health/",
            "redis_available": redis_status,
            "ollama_status": {
                "connected": ollama_connected,
                "message": ollama_msg,
                "base_url": OLLAMA_BASE_URL,
                "model": OLLAMA_MODEL
            },
            "system_status": {
                "rag_initialized": CURRENT_MODEL_KEY is not None,
                "current_model_key": CURRENT_MODEL_KEY,
                "files_found": bool(glob.glob(os.path.join(UPLOAD_DIR, "*.pdf")) or 
                                  glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))),
                "upload_dir": os.path.abspath(UPLOAD_DIR),
                "tts_enabled": False,
                "transcription_enabled": False
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Startup error: {str(e)}"})

def validate_language(text: str) -> bool:
    """Validate input language and format"""
    text = text.strip()
    if not text:
        return False
    
    supported_patterns = {
        'en': r'[a-zA-Z]',  
        'hi': r'[\u0900-\u097F]',  
        'mr': r'[\u0900-\u097F]'   
    }
    if re.search(supported_patterns['en'], text):
        return True
    if re.search(supported_patterns['hi'], text):
        return True
    return False

def validate_knowledge_query(text: str) -> bool:
    lowered = text.lower()
    if 'talk like' in lowered or 'speak like' in lowered or 'act like' in lowered:
        return False
    return True

def process_response(text: str) -> str:
    """Process and clean the response"""
    # Remove conversational elements
    text = text.replace("my friend", "")
    text = text.replace("let me tell you", "")
    text = text.replace("Arre", "")
    text = text.replace("yaar", "")
    text = text.replace("Plus", "Additionally")

    # Remove any casual language markers
    casual_words = ["well,", "you see,", "basically,", "actually,", "you know,"]
    for word in casual_words:
        text = text.replace(word, "")

    # Ensure markdown headings (##, ###) are on new lines and bolded
    import re
    text = re.sub(r'(#+\s*[^\n]+)', r'\n\1', text)
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()

    return text

@app.post("/query/")
async def get_answer_optimized(req: QueryRequest):
    input_text = req.input_text.strip()
    if not input_text:
        return JSONResponse(status_code=400, content={"reply": "I'm sorry, I cannot assist with that topic. For more details, please contact the 104/102 helpline numbers."})

    # Check Ollama connection before processing
    is_connected, connection_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
    if not is_connected:
        return JSONResponse(
            status_code=503,
            content={"reply": f"Ollama service unavailable: {connection_msg}. Please ensure Ollama is running with the BharatGPT model."}
        )

    detected_lang = detect_language(input_text)
    if not validate_language(input_text):
        return JSONResponse(
            status_code=400,
            content={"reply": "⚠️Only Marathi, Hindi, and English are allowed. Queries in other languages are strictly not supported."}
        )
    if not validate_knowledge_query(input_text):
        return JSONResponse(
            status_code=400, 
            content={"reply": "I'm sorry, I cannot assist with that topic. For more details, please contact the 104/102 helpline numbers."}
        )

    session_id = req.session_id or "default"
    wait_time = check_rate_limit_delay(session_id)
    if wait_time:
        return JSONResponse(status_code=429, content={"reply": "Unable to answer right now, please try again after sometime. For more details, please contact the 104/102 helpline numbers."})

    if not CURRENT_MODEL_KEY:
        return JSONResponse(
            status_code=400, 
            content={"reply": "No RAG system initialized. Please check backend file configuration."}
        )
    
    rag_chain = state_manager.get_rag_chain(CURRENT_MODEL_KEY, OLLAMA_BASE_URL)
    if not rag_chain:
        return JSONResponse(
            status_code=400, 
            content={"reply": "RAG system not found. Please check backend configuration."}
        )

    try:
        # Modified for text-only with Ollama
        result = process_scheme_query_with_retry(rag_chain, input_text)
        assistant_reply = result[0] if isinstance(result, tuple) else result or ""

        # Only allow answers found in the uploaded documents
        assistant_reply = process_response(assistant_reply)
        if len(assistant_reply.strip()) < 10:
            return JSONResponse(
                status_code=400,
                content={"reply": "No relevant information found in the uploaded documents. Please ask a question that is covered in your PDF/TXT files."}
            )

        # Translate answer to user's language if needed
        detected_lang = detect_language(input_text)
        if detect_language(assistant_reply) != detected_lang:
            assistant_reply = translate_text(assistant_reply, detected_lang)

        message = {
            "user": input_text,
            "assistant": assistant_reply,
            "model": req.model,
            "timestamp": time.strftime("%H:%M:%S"),
            "lang": detected_lang,
            "session_id": session_id
        }
        state_manager.add_chat_message(message, session_id)
        return {
            "reply": assistant_reply,
            "session_id": session_id,
            "model_key": CURRENT_MODEL_KEY,
            "lang": detected_lang,
            "mode": "local_ollama",
            "model_used": OLLAMA_MODEL
        }
    except Exception as e:
        logging.error(f"Query processing error: {e}")
        return JSONResponse(status_code=500, content={"reply": "No relevant information found in the uploaded documents. Please ask a question that is covered in your PDF/TXT files."})

@app.get("/chat-history/")
async def get_chat_history(session_id: str = Depends(get_session_id)):
    history = state_manager.get_chat_history(session_id)
    return {
        "chat_history": history,
        "session_id": session_id,
        "redis_available": redis_manager.is_available(),
        "mode": "local_ollama"
    }

@app.get("/health/")
async def health_check():
    ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    return {
        "status": "ok" if ollama_connected else "degraded",
        "redis_available": redis_manager.is_available(),
        "ollama_status": {
            "connected": ollama_connected,
            "message": ollama_msg,
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL
        },
        "timestamp": time.time(),
        "mode": "local_ollama",
        "features": {
            "rag_enabled": True,
            "tts_enabled": False,
            "transcription_enabled": False,
            "local_processing": True
        }
    }

@app.get("/sessions/")
async def list_sessions():
    if not redis_manager.is_available():
        return {"error": "Redis not available"}
    try:
        keys = redis_manager.redis_client.keys("chat:*")
        sessions = [key.decode().replace("chat:", "") for key in keys]
        return {"sessions": sessions, "mode": "local_ollama"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    if redis_manager.is_available():
        try:
            redis_manager.redis_client.delete(f"chat:{session_id}")
            return {"message": f"Session {session_id} cleared", "mode": "local_ollama"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})
    else:
        # If using in-memory fallback, clear chat history if present
        state_manager._memory_fallback[f"chat:{session_id}"] = []
        return {"message": f"Session {session_id} cleared (memory only)", "mode": "local_ollama"}

@app.post("/sessions/start")
async def start_session():
    """Create a new session with a unique ID"""
    try:
        adjectives = ["sharp", "sleepy", "fluffy", "dazzling", "crazy", "bold", "happy", "silly", "wobbly", "grumpy"]
        animals = ["lion", "swan", "tiger", "elephant", "zebra", "giraffe", "panda","koala","llama"] 
        session_id=  f"{random.choice(adjectives)}_{random.choice(animals)}_{os.urandom(2).hex()}"
        
        if redis_manager.is_available():
            redis_manager.set_chat_history(session_id, [], expire_hours=24)
            return {"session_id": session_id, "message": "New session started", "mode": "local_ollama"}
        else:
            state_manager._memory_fallback[f"chat:{session_id}"] = []
            return {"session_id": session_id, "message": "New session started (memory only)", "mode": "local_ollama"}
            
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Failed to start session: {str(e)}"}
        )

@app.post("/sessions/{session_id}/end")
async def end_session(session_id: str):
    """End a specific session and clean up its resources"""
    try:
        if redis_manager.is_available():
            pattern = f"rag_chain:*_{session_id}"
            for key in redis_manager.redis_client.scan_iter(pattern):
                redis_manager.redis_client.delete(key)
        else:
            state_manager._memory_fallback.pop(f"chat:{session_id}", None)

            state_manager.clear_cache(f"*_{session_id}")
            
        return {"message": f"Session {session_id} ended and cleaned up", "mode": "local_ollama"}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to end session: {str(e)}"}
        )

@app.get("/status/")
async def get_system_status():
    """Get comprehensive system status for local Ollama mode"""
    ollama_connected, ollama_msg = check_ollama_connection(OLLAMA_BASE_URL, OLLAMA_MODEL)
    
    return {
        "mode": "local_ollama",
        "system_status": {
            "rag_initialized": CURRENT_MODEL_KEY is not None,
            "current_model_key": CURRENT_MODEL_KEY,
            "redis_available": redis_manager.is_available(),
            "ollama_connected": ollama_connected,
            "ollama_message": ollama_msg,
            "files_found": bool(glob.glob(os.path.join(UPLOAD_DIR, "*.pdf")) or 
                              glob.glob(os.path.join(UPLOAD_DIR, "*.txt"))),
            "upload_dir": os.path.abspath(UPLOAD_DIR),
        },
        "ollama_config": {
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
            "status": "connected" if ollama_connected else "disconnected"
        },
        "features": {
            "text_queries": True,
            "multilingual_support": True,
            "caching": True,
            "session_management": True,
            "local_processing": True,
            "tts": False,
            "speech_transcription": False
        },
        "supported_languages": ["en", "hi", "mr"],
        "cache_stats": state_manager.get_cache_stats(),
        "timestamp": time.time()
    }

@app.get("/ollama/models")
async def get_available_models():
    """Get list of available Ollama models"""
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return {
                "available_models": models,
                "current_model": OLLAMA_MODEL,
                "ollama_url": OLLAMA_BASE_URL
            }
        else:
            return JSONResponse(
                status_code=503,
                content={"error": f"Ollama server responded with status {response.status_code}"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"error": f"Cannot connect to Ollama: {str(e)}"}
        )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)