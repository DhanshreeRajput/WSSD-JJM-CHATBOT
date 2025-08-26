# rag_services.py - Optimized version for faster responses
import tempfile
import os
import time
import hashlib
import re
import langid
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain_community.retrievers import TFIDFRetriever
from langchain.prompts import PromptTemplate
from langchain.globals import set_verbose
from langchain.callbacks.base import BaseCallbackHandler
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Removed TTS dependency - now hardcoded to False for text-only mode
TTS_AVAILABLE = False

# For language detection of the query
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0 # for consistent results
except ImportError:
    print("Warning: langdetect not installed. Query language validation will be skipped. pip install langdetect")

set_verbose(False) # Disable verbose logging for speed

# Enhanced caching with better performance
_query_cache = {}
_cache_max_size = 100  # Increased cache size
_cache_lock = threading.Lock()

def get_query_hash(query_text):
    """Generate a hash for caching queries"""
    return hashlib.md5(query_text.encode()).hexdigest()

def cache_result(query_hash, result):
    """Thread-safe cache result"""
    with _cache_lock:
        global _query_cache
        if len(_query_cache) >= _cache_max_size:
            # Remove oldest entry (FIFO)
            try:
                oldest_key = next(iter(_query_cache))
                del _query_cache[oldest_key]
            except StopIteration:
                pass
        _query_cache[query_hash] = result

def get_cached_result(query_hash):
    """Thread-safe get cached result"""
    with _cache_lock:
        return _query_cache.get(query_hash)

def clear_query_cache():
    """Clear the RAG query cache"""
    with _cache_lock:
        global _query_cache
        _query_cache.clear()
        print("RAG query cache cleared.")

def detect_language_langid(text):
    """Return the ISO 639-1 language code and full language name, if supported."""
    lang, _ = langid.classify(text)
    return lang, SUPPORTED_LANGUAGES.get(lang, "Unsupported")

# --- Optimized RAG Chain Building ---
def build_rag_chain_from_files(pdf_file, txt_file, ollama_base_url="http://localhost:11434", enhanced_mode=True, model_choice="llama3.1:8b"):
    """
    Build a RAG chain from PDF and/or TXT files using Ollama with optimizations.
    """
    pdf_path = txt_path = None
    if not (pdf_file or txt_file):
        raise ValueError("At least one file (PDF or TXT) must be provided.")
    
    temp_files_to_clean = []
    try:
        if pdf_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(pdf_file.getvalue())
                pdf_path = tmp_pdf.name
                temp_files_to_clean.append(pdf_path)
        if txt_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_txt:
                tmp_txt.write(txt_file.getvalue())
                txt_path = tmp_txt.name
                temp_files_to_clean.append(txt_path)

        all_docs = []
        if pdf_path:
            all_docs.extend(PyPDFLoader(pdf_path).load())
        if txt_path:
            all_docs.extend(TextLoader(txt_path, encoding="utf-8").load())
        
        if not all_docs:
            raise ValueError("No valid documents loaded or documents are empty.")

        # Optimized parameters for faster processing
        chunk_size = 250 if enhanced_mode else 300  # Smaller chunks for faster retrieval
        max_chunks = 3 if enhanced_mode else 5      # Fewer chunks for faster processing
        max_tokens = 300  # Reduced tokens for faster generation

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=50,  # Reduced overlap for speed
            separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
            length_function=len
        )
        splits = splitter.split_documents(all_docs)
        
        if not splits:
            raise ValueError("Document splitting resulted in no chunks. Check document content and splitter settings.")
            
        retriever = TFIDFRetriever.from_documents(splits, k=min(max_chunks, len(splits)))

        # Streamlined template for faster processing
        template = """You are a concise Knowledge Assistant for quick government scheme queries.

Your task is to give a brief, direct answer (maximum 2-3 lines) in the user's language.

Guidelines:
* Always answer in the **same language as the question**.
* Be direct and concise - maximum 2-3 sentences.
* Provide only the most essential information.
* Include contact numbers (104/102) only when specifically asked about contact details.
* No markdown formatting, no section headers, no bullet points.
* If no relevant information exists, respond briefly:
  - **Marathi**: "कृपया 104/102 हेल्पलाइन संपर्क साधा."  
  - **Hindi**: "कृपया 104/102 हेल्पलाइन संपर्क करें।"  
  - **English**: "Please contact 104/102 helpline."

Context: {context}

Question: {question}

Brief Answer:"""

        custom_prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Optimized Ollama LLM settings
        llm = Ollama(
            base_url=ollama_base_url,
            model=model_choice,
            temperature=0.1,
            num_predict=max_tokens,  # Limit response length
            top_k=10,               # Reduce sampling space
            top_p=0.9,              # Focus on likely tokens
            repeat_penalty=1.1,     # Prevent repetition
            callbacks=[]            # Remove callbacks for speed
        )
        
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={"prompt": custom_prompt, "verbose": False}
        )
            
    finally:
        for f_path in temp_files_to_clean:
            if os.path.exists(f_path):
                os.unlink(f_path)

def build_rag_chain_with_model_choice(pdf_file, txt_file, ollama_base_url="http://localhost:11434", model_choice="llama3.1:8b", enhanced_mode=True):
    """
    Build RAG chain with Ollama model. This is the primary RAG chain builder.
    """
    return build_rag_chain_from_files(pdf_file, txt_file, ollama_base_url, enhanced_mode, model_choice)

def detect_language(text):
    """
    Fast language detection with caching
    """
    try:
        # Simple character-based detection for speed
        text_clean = text.strip().lower()
        
        # Quick checks for common patterns
        if any(char in text for char in ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ए', 'ऐ', 'ओ', 'औ']):
            return 'hi'
        elif any(char in text for char in ['क', 'ख', 'ग', 'घ', 'च', 'छ', 'ज', 'झ', 'ट', 'ठ']):
            return 'mr'
        else:
            return 'en'
        
    except Exception:
        return 'en'

# --- Optimized Query Processing ---
def process_scheme_query_with_retry(rag_chain, user_query, max_retries=2):
    """
    Optimized query processing with timeout and faster execution
    """
    # Quick language detection
    supported_languages = {"en", "hi", "mr"}
    detected_lang = detect_language(user_query)
    
    if detected_lang not in supported_languages:
        return (
            "Sorry, only Marathi, Hindi, and English are supported.",
            "",
            detected_lang,
            {"text_cache": "skipped", "audio_cache": "not_generated"}
        )

    # Check cache first
    query_hash = get_query_hash(user_query.lower().strip())
    cached_result = get_cached_result(query_hash)
    
    if cached_result:
        return (cached_result, "", detected_lang, {"text_cache": "hit", "audio_cache": "not_generated"})

    # Process with timeout for faster response
    def execute_query():
        try:
            result = rag_chain.invoke({"query": user_query})
            if isinstance(result, dict):
                return result.get('result', 'No results found.')
            elif isinstance(result, tuple) and len(result) > 0:
                return str(result[0])
            else:
                return str(result)
        except Exception as e:
            raise e

    # Execute with timeout
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(execute_query)
        try:
            result_text = future.result(timeout=15)  # 15 second timeout
            cache_result(query_hash, result_text)
            return (result_text, "", detected_lang, {"text_cache": "miss", "audio_cache": "not_generated"})
        
        except TimeoutError:
            return ("Response timeout. Please try a simpler question.", "", detected_lang, {"text_cache": "timeout", "audio_cache": "not_generated"})
        except Exception as e:
            error_msg = f"Error: {str(e)[:100]}..."  # Truncate long errors
            return (error_msg, "", detected_lang, {"text_cache": "error", "audio_cache": "not_generated"})

def get_model_options():
    """Return available Ollama models with their characteristics."""
    return {
        "llama3.1:8b": {
            "name": "BharatGPT 3B Indic (Recommended)", 
            "description": "Best for Indian languages including Hindi, Marathi, and English."
        },
        "llama3.2:3b": {
            "name": "Llama 3.2 3B", 
            "description": "General purpose model, good for English queries."
        },
        "gemma2:2b": {
            "name": "Gemma 2 2B", 
            "description": "Lightweight fallback option."
        }
    }

def check_ollama_connection(base_url="http://localhost:11434", model="llama3.1:8b"):
    """Fast connection check with timeout"""
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=3)  # Reduced timeout
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            if model in model_names:
                return True, "Connected"
            else:
                return False, f"Model not found"
        else:
            return False, f"Server error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection failed"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}..."