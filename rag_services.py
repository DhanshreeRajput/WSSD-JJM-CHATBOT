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

def post_process_response(response_text):
    """Final post-processing to remove any instruction artifacts"""
    
    # If response contains instruction-like text, extract only the factual content
    lines = response_text.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip lines that look like instructions
        if any(phrase in line.lower() for phrase in [
            'be direct and concise', 
            'maximum 2-3 sentences',
            'provide only the most essential',
            'include contact numbers',
            'guidelines:', 
            'your task is',
            'answer in the same language',
            'keep the answer to'
        ]):
            continue
        
        # Skip lines that start with bullet points or asterisks
        if line.startswith(('*', '•', '-')) and any(word in line.lower() for word in ['direct', 'concise', 'essential', 'contact']):
            continue
            
        if line and len(line) > 10:
            clean_lines.append(line)
    
    if clean_lines:
        result = ' '.join(clean_lines)
        # Limit to first 2 sentences
        sentences = re.split(r'[.!?]+', result)
        if len(sentences) >= 2:
            result = '. '.join(sentences[:2]).strip() + '.'
        return result
    
    return response_text

def clean_response(response_text, original_query):
    """Clean the response to ensure it's concise and removes template artifacts"""
    
    # Remove template instructions and common artifacts
    template_patterns = [
        r"You are an?.*?Assistant.*?(?:\n|\.)",
        r"Your task is.*?(?:\n|\.)",
        r"Guidelines:.*?(?:\n|$)",
        r"Based on the context.*?(?:\n|\.)",
        r"Keep the answer.*?(?:\n|\.)",
        r"\*.*?(?:\n|$)",  # Remove lines starting with *
        r"Context:.*?(?:\n|$)",
        r"Question:.*?(?:\n|$)",
        r"Answer:.*?(?:\n|$)",
        r"Brief Answer:.*?(?:\n|$)"
    ]
    
    cleaned_text = response_text
    for pattern in template_patterns:
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove bullet points and formatting
    cleaned_text = re.sub(r'[•\-*]\s*', '', cleaned_text)
    cleaned_text = re.sub(r'\n+', ' ', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = cleaned_text.strip()
    
    # If response starts with common instruction phrases, remove them
    instruction_starters = [
        "be direct and concise",
        "provide only the most essential",
        "include contact numbers",
        "maximum 2-3 sentences",
        "only use information"
    ]
    
    for starter in instruction_starters:
        if cleaned_text.lower().startswith(starter):
            # Find the first sentence that doesn't contain instructions
            sentences = re.split(r'[.!?]+', cleaned_text)
            for i, sentence in enumerate(sentences):
                if len(sentence.strip()) > 20 and not any(inst in sentence.lower() for inst in instruction_starters):
                    cleaned_text = '. '.join(sentences[i:])
                    break
    
    # Limit to 2-3 sentences
    sentences = re.split(r'[.!?]+', cleaned_text)
    if len(sentences) > 3:
        cleaned_text = '. '.join(sentences[:2]) + '.'
    
    # Fallback responses
    if len(cleaned_text.strip()) < 10:
        lang = detect_language(original_query)
        if lang == 'hi':
            return "कृपया 104/102 हेल्पलाइन संपर्क करें।"
        elif lang == 'mr':
            return "कृपया 104/102 हेल्पलाइन संपर्क साधा."
        else:
            return "Please contact 104/102 helpline."
    
    return cleaned_text.strip()

# --- RAG Chain Building ---
def build_rag_chain_from_files(pdf_file, txt_file, ollama_base_url="http://localhost:11434", enhanced_mode=True, model_choice="gemma3:270m"):
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

        # Adjust parameters for local model - smaller chunks for better performance
        chunk_size = 300 if enhanced_mode else 400
        max_chunks = 3 if enhanced_mode else 5
        max_tokens = 150  # Reduced for shorter responses

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=max(60, int(chunk_size * 0.2)), # Overlap as a percentage of chunk_size
            separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
            length_function=len
        )
        splits = splitter.split_documents(all_docs)
        
        if not splits:
            raise ValueError("Document splitting resulted in no chunks. Check document content and splitter settings.")
            
        retriever = TFIDFRetriever.from_documents(splits, k=min(max_chunks, len(splits)))

        # Ultra-simple template to prevent any instruction leakage
        template = """{context}

Q: {question}
A:"""

        custom_prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Initialize Ollama LLM with strict parameters
        llm = Ollama(
            base_url=ollama_base_url,
            model=model_choice,
            temperature=0.0,  # Make it completely deterministic
            num_predict=100,  # Further reduced for very short responses
            top_k=1,  # Use only the most probable token
            top_p=0.1,  # Very focused sampling
            callbacks=[]  # Remove callback to avoid extra logging
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

def build_rag_chain_with_model_choice(pdf_file, txt_file, ollama_base_url="http://localhost:11434", model_choice="gemma3:270m", enhanced_mode=True):
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
            "केवळ मराठी, हिंदी आणि इंग्रजी भाषा समर्थित आहे.",
            "",
            detected_lang,
            {"text_cache": "skipped", "audio_cache": "not_generated"}
        )

    # Check cache first
    query_hash = get_query_hash(user_query.lower().strip())
    cached_result = get_cached_result(query_hash)
    
    if cached_result:
        result_text = cached_result
        cache_status = "cached"
    else:
        cache_status = "not_cached"
        
        # Check for comprehensive queries
        comprehensive_keywords = [
            "all schemes", "list schemes", "complete list", "सर्व योजना", 
            "total schemes", "how many schemes", "scheme names", "सर्व", "यादी"
        ]
        
        is_comprehensive_query = any(keyword in user_query.lower() for keyword in comprehensive_keywords)
        
        for attempt in range(max_retries):
            try:
                if is_comprehensive_query:
                    result_text = query_all_schemes_optimized(rag_chain)
                else:
                    # Process the query
                    result = rag_chain.invoke({"query": user_query})
                    
                    # Extract the actual result properly
                    if isinstance(result, dict):
                        result_text = result.get('result', 'No results found.')
                    elif isinstance(result, str):
                        result_text = result
                    else:
                        result_text = str(result)
                    
                    # Additional cleaning for instruction artifacts
                    result_text = post_process_response(result_text)
                
                # Clean the result to remove any template artifacts
                result_text = clean_response(result_text, user_query)
                
                # Cache the result
                cache_result(query_hash, result_text)
                cache_status = "cached"
                break
                
            except Exception as e:
                error_str = str(e)
                
                if "connection" in error_str.lower() or "timeout" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # Progressive backoff
                        time.sleep(wait_time)
                        continue
                    else:
                        result_text = "Ollama server unavailable. Please try again."
                        break
                
                elif "Request too large" in error_str or "context" in error_str.lower():
                    result_text = "Query too complex. Please ask about specific schemes."
                    break
                
                else:
                    result_text = "Error processing query."
                    break
        else:
            result_text = "Unable to process query."
    
    # Return format: (text_result, empty_audio_string, language, cache_info)
    return (result_text, "", detected_lang, {"text_cache": cache_status, "audio_cache": "not_generated"})

# --- Scheme Extraction & Specialized Queries ---
def extract_schemes_from_text(text_content):
    """Helper function to extract schemes from text content using regex patterns."""
    # Normalize text: collapse multiple whitespaces, handle newlines
    text = re.sub(r'\s+', ' ', str(text_content)).replace('\n', ' ')

    # More comprehensive patterns, including common Marathi and English scheme indicators
    patterns = [
        r'\b(?:[A-Z][\w\'-]+(?: [A-Z][\w\'-]+)* )?(?:योजना|कार्यक्रम|अभियान|मिशन|धोरण|निधी|कार्ड|Scheme|Yojana|Programme|Abhiyan|Mission|Initiative|Program|Policy|Fund|Card)\b',
        r'\b(?:Pradhan Mantri|Mukhyamantri|CM|PM|National|Rashtriya|State|Rajya|प्रधानमंत्री|मुख्यमंत्री|राष्ट्रीय|राज्य) (?:[A-Z][\w\'-]+ ?)+',
        r'\b[A-Z]{2,}(?:-[A-Z]{2,})? Scheme\b',
        r'\b(?:[०-९]+|[0-9]+)\.\s+([A-Z][\w\s\'-]+(?:योजना|Scheme|कार्यक्रम|Karyakram|अभियान|Abhiyan))',
        r'•\s+([A-Z][\w\s\'-]+(?:योजना|Scheme|कार्यक्रम|Karyakram|अभियान|Abhiyan))'
    ]
    
    extracted_schemes = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            scheme_name = match[1] if isinstance(match, tuple) else match
            cleaned_name = scheme_name.strip().rstrip('.,:;-').title()
            if len(cleaned_name) > 4 and len(cleaned_name.split()) < 10:
                extracted_schemes.add(cleaned_name)

    return sorted(list(extracted_schemes))

def query_all_schemes_optimized(rag_chain):
    """Optimized scheme extractor using targeted queries and regex."""
    try:
        context_query = "List all government schemes mentioned in documents"
        response = rag_chain.invoke({"query": context_query})
        content_to_parse = response.get('result', '')
        
        all_extracted_schemes = extract_schemes_from_text(content_to_parse)

        if not all_extracted_schemes:
            return "No government schemes found in documents."

        # Keep it concise - max 5 schemes
        limited_schemes = all_extracted_schemes[:5]
        response_text = f"Found {len(limited_schemes)} main schemes: " + ", ".join(limited_schemes)
        return response_text
    except Exception as e:
        return f"Error extracting schemes: {str(e)}"

def get_model_options():
    """Return available Ollama models with their characteristics."""
    return {
        "gemma3:270m": {
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

def check_ollama_connection(base_url="http://localhost:11434", model="gemma3:270m"):
    """Check if Ollama server is running and model is available"""
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