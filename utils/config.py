import os
from dotenv import load_dotenv
from typing import Optional

def load_env_vars():
    """Load environment variables from .env file"""
    load_dotenv()

# Load environment variables
load_env_vars()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Application Settings
APP_NAME = os.getenv("APP_NAME", "SAMNEX AI Local")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# File Upload Settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
SUPPORTED_FILE_TYPES = os.getenv("SUPPORTED_FILE_TYPES", "pdf,txt").split(",")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_files")

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", 30))
RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", 5))

# Session Management
SESSION_TIMEOUT_HOURS = int(os.getenv("SESSION_TIMEOUT_HOURS", 24))
MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", 50))

# Language Support
SUPPORTED_LANGUAGES = os.getenv("SUPPORTED_LANGUAGES", "en,hi,mr").split(",")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Model Performance Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 400))
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", 8))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))

# Cache Settings
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", 50))
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", 24))

def get_config_summary():
    """Get a summary of current configuration"""
    return {
        "ollama": {
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL
        },
        "redis": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": REDIS_DB,
            "password_set": bool(REDIS_PASSWORD)
        },
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "debug": DEBUG,
            "log_level": LOG_LEVEL
        },
        "files": {
            "max_size_mb": MAX_FILE_SIZE_MB,
            "supported_types": SUPPORTED_FILE_TYPES,
            "upload_dir": UPLOAD_DIR
        },
        "performance": {
            "chunk_size": CHUNK_SIZE,
            "max_chunks": MAX_CHUNKS,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE
        },
        "languages": {
            "supported": SUPPORTED_LANGUAGES,
            "default": DEFAULT_LANGUAGE
        }
    }

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate Ollama URL format
    if not OLLAMA_BASE_URL.startswith(("http://", "https://")):
        errors.append("OLLAMA_BASE_URL must start with http:// or https://")
    
    # Validate numeric values
    if MAX_FILE_SIZE_MB <= 0:
        errors.append("MAX_FILE_SIZE_MB must be positive")
    
    if CHUNK_SIZE <= 0:
        errors.append("CHUNK_SIZE must be positive")
    
    if MAX_CHUNKS <= 0:
        errors.append("MAX_CHUNKS must be positive")
    
    if MAX_TOKENS <= 0:
        errors.append("MAX_TOKENS must be positive")
    
    if not (0.0 <= TEMPERATURE <= 2.0):
        errors.append("TEMPERATURE must be between 0.0 and 2.0")
    
    # Validate supported languages
    valid_langs = {"en", "hi", "mr"}
    if not set(SUPPORTED_LANGUAGES).issubset(valid_langs):
        errors.append(f"SUPPORTED_LANGUAGES must be subset of {valid_langs}")
    
    if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
        errors.append("DEFAULT_LANGUAGE must be in SUPPORTED_LANGUAGES")
    
    return errors

def print_config():
    """Print current configuration"""
    config = get_config_summary()
    print("=" * 50)
    print("SAMNEX AI - LOCAL OLLAMA CONFIGURATION")
    print("=" * 50)
    
    print(f"Ollama URL: {config['ollama']['base_url']}")
    print(f"Ollama Model: {config['ollama']['model']}")
    print(f"Redis: {config['redis']['host']}:{config['redis']['port']}")
    print(f"Upload Directory: {config['files']['upload_dir']}")
    print(f"Supported Languages: {', '.join(config['languages']['supported'])}")
    print(f"Debug Mode: {config['app']['debug']}")
    
    # Validate configuration
    errors = validate_config()
    if errors:
        print("\n⚠️  Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration is valid")
    
    print("=" * 50)