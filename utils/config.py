import os
from dotenv import load_dotenv

def load_env_vars():
    """Load environment variables from .env file"""
    load_dotenv()

# Load environment variables
load_env_vars()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0")

# Application Settings
APP_NAME = os.getenv("APP_NAME", "SAMNEX AI Local")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# File Upload Settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_files")

# Rate Limiting
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", 2))

# Language Support
SUPPORTED_LANGUAGES = ["en", "hi", "mr"]
DEFAULT_LANGUAGE = "en"

# Model Performance Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 400))
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", 8))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))

def print_config():
    """Print current configuration"""
    print("=" * 50)
    print("SAMNEX AI - LOCAL OLLAMA CONFIGURATION")
    print("=" * 50)
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
    print(f"Upload Directory: {UPLOAD_DIR}")
    print(f"Supported Languages: {', '.join(SUPPORTED_LANGUAGES)}")
    print(f"Debug Mode: {DEBUG}")
    print(f"Rate Limit: {RATE_LIMIT_SECONDS} seconds")
    print("=" * 50)

def validate_config():
    """Basic configuration validation"""
    errors = []
    
    if not OLLAMA_BASE_URL.startswith(("http://", "https://")):
        errors.append("OLLAMA_BASE_URL must start with http:// or https://")
    
    if MAX_FILE_SIZE_MB <= 0:
        errors.append("MAX_FILE_SIZE_MB must be positive")
    
    if CHUNK_SIZE <= 0:
        errors.append("CHUNK_SIZE must be positive")
    
    if not (0.0 <= TEMPERATURE <= 2.0):
        errors.append("TEMPERATURE must be between 0.0 and 2.0")
    
    return errors

if __name__ == "__main__":
    print_config()
    errors = validate_config()
    if errors:
        print("\n⚠️  Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration is valid")