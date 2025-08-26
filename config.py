# config.py - Optimized for faster responses
import os
from dotenv import load_dotenv

def load_env_vars():
    load_dotenv()

load_env_vars()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Application Settings
APP_NAME = os.getenv("APP_NAME", "SAMNEX AI Local")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# File Upload Settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_files")

# Rate Limiting (optimized for speed)
RATE_LIMIT_SECONDS = float(os.getenv("RATE_LIMIT_SECONDS", 0.1))  # Reduced from 0.2

# Language Support
SUPPORTED_LANGUAGES = ["en", "hi", "mr"]
DEFAULT_LANGUAGE = "en"

# Model Performance Settings (optimized for faster response)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 250))        # Reduced from 300
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", 3))          # Reduced from 5
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 300))        # Reduced from 500
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))

# New performance settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))  # 15 second timeout
CACHE_SIZE = int(os.getenv("CACHE_SIZE", 100))          # Larger cache
ENABLE_THREADING = os.getenv("ENABLE_THREADING", "true").lower() == "true"

def print_config():
    print("=" * 50)
    print("SAMNEX AI - OPTIMIZED CONFIGURATION")
    print("=" * 50)
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    print(f"Upload Directory: {UPLOAD_DIR}")
    print(f"Supported Languages: {', '.join(SUPPORTED_LANGUAGES)}")
    print(f"Debug Mode: {DEBUG}")
    print(f"Rate Limit: {RATE_LIMIT_SECONDS} seconds")
    print(f"Request Timeout: {REQUEST_TIMEOUT} seconds")
    print(f"Chunk Size: {CHUNK_SIZE}")
    print(f"Max Chunks: {MAX_CHUNKS}")
    print(f"Max Tokens: {MAX_TOKENS}")
    print(f"Cache Size: {CACHE_SIZE}")
    print("=" * 50)

def validate_config():
    errors = []
    if not OLLAMA_BASE_URL.startswith(("http://", "https://")):
        errors.append("OLLAMA_BASE_URL must start with http:// or https://")
    if MAX_FILE_SIZE_MB <= 0:
        errors.append("MAX_FILE_SIZE_MB must be positive")
    if CHUNK_SIZE <= 0:
        errors.append("CHUNK_SIZE must be positive")
    if not (0.0 <= TEMPERATURE <= 2.0):
        errors.append("TEMPERATURE must be between 0.0 and 2.0")
    if REQUEST_TIMEOUT <= 0:
        errors.append("REQUEST_TIMEOUT must be positive")
    return errors