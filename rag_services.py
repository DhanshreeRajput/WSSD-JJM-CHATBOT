# rag_services.py - Fixed version with improved knowledge base retrieval
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
from config import STRICT_KB_ONLY, SUPPORTED_LANGUAGES
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Removed TTS dependency - now hardcoded to False for text-only mode
TTS_AVAILABLE = False

# Language mappings and templates
LANGUAGE_PROMPTS = {
    'en': "Answer in English only. Use only the provided context to answer. Be concise and direct.",
    'hi': "केवल हिंदी में उत्तर दें। प्रदान किए गए संदर्भ का उपयोग करके उत्तर दें। संक्षिप्त और स्पष्ट जवाब दें।",
    'mr': "फक्त मराठीत उत्तर द्या। प्रदान केलेल्या संदर्भाचा वापर करून उत्तर द्या। संक्षिप्त आणि स्पष्ट उत्तर द्या।"
}

FALLBACK_RESPONSES = {
    'en': "Please contact 104/102 helpline for more information.",
    'hi': "अधिक जानकारी के लिए कृपया 104/102 हेल्पलाइन संपर्क करें।",
    'mr': "अधिक माहितीसाठी कृपया 104/102 हेल्पलाइन संपर्क साधा।"
}

# More lenient refusal when nothing relevant is found in KB
KB_REFUSAL = {
    'en': "Based on the available documents, I couldn't find specific information about that. Please try asking about government schemes, eligibility criteria, or application processes.",
    'hi': "उपलब्ध दस्तावेज़ों के आधार पर, मुझे इस बारे में विशिष्ट जानकारी नहीं मिली। कृपया सरकारी योजनाओं, पात्रता मापदंड, या आवेदन प्रक्रियाओं के बारे में पूछें।",
    'mr': "उपलब्ध दस्तावेजांच्या आधारे, मला याबद्दल विशिष्ट माहिती सापडली नाही। कृपया सरकारी योजना, पात्रता निकष, किंवा अर्ज प्रक्रियेबद्दल विचारा।"
}

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

def get_query_hash(query_text, language='en'):
    """Generate a hash for caching queries with language"""
    return hashlib.md5(f"{query_text}_{language}".encode()).hexdigest()

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

def get_language_instruction(language_code):
    """Get language-specific instruction for the model"""
    return LANGUAGE_PROMPTS.get(language_code, LANGUAGE_PROMPTS['en'])

def is_content_relevant(query, documents, threshold=0.3):
    """
    Check if the retrieved documents are relevant to the query.
    Uses a more lenient approach to determine relevance.
    """
    if not documents:
        return False
        
    # Extract key terms from query (excluding common words)
    query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
    
    # Remove very common words that don't indicate relevance
    stop_words = {
        'what', 'how', 'when', 'where', 'who', 'which', 'why', 'can', 'will', 'would',
        'should', 'could', 'the', 'and', 'for', 'are', 'you', 'have', 'get', 'know',
        'tell', 'give', 'show', 'find', 'help', 'need', 'want', 'about', 'information',
        'details', 'please', 'करें', 'है', 'के', 'में', 'से', 'को', 'का', 'की', 'पर',
        'आहे', 'च्या', 'ला', 'ने', 'त', 'या', 'ची', 'कर', 'आण', 'मध'
    }
    
    query_words -= stop_words
    
    if not query_words:
        return True  # If no meaningful words left, assume relevant
    
    # Check relevance across all documents
    total_matches = 0
    total_words = len(query_words)
    
    for doc in documents:
        doc_text = (getattr(doc, 'page_content', '') or '').lower()
        matches = sum(1 for word in query_words if word in doc_text)
        total_matches += matches
    
    # More lenient threshold - if any key terms found, consider relevant
    relevance_score = total_matches / (total_words * len(documents)) if total_words > 0 else 0
    return relevance_score > threshold or total_matches > 0

def post_process_response(response_text, target_language='en'):
    """Final post-processing to remove any instruction artifacts and ensure language consistency"""
    
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
            'keep the answer to',
            'answer in english only',
            'केवल हिंदी में',
            'फक्त मराठीत'
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
        sentences = re.split(r'[.!?।]+', result)
        if len(sentences) >= 2:
            result = '. '.join(sentences[:2]).strip()
            if not result.endswith(('.', '।', '?', '!')):
                result += '।' if target_language in ['hi', 'mr'] else '.'
        return result
    
    return response_text

def clean_response(response_text, original_query, target_language='en'):
    """Clean the response to ensure it's concise and in the correct language"""
    
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
        r"Brief Answer:.*?(?:\n|$)",
        r"Answer in \w+ only.*?(?:\n|\.)",
        r"केवल हिंदी में.*?(?:\n|।)",
        r"फक्त मराठीत.*?(?:\n|।)"
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
        "only use information",
        "answer in english only",
        "केवल हिंदी में",
        "फक्त मराठीत"
    ]
    
    for starter in instruction_starters:
        if cleaned_text.lower().startswith(starter.lower()):
            # Find the first sentence that doesn't contain instructions
            sentences = re.split(r'[.!?।]+', cleaned_text)
            for i, sentence in enumerate(sentences):
                if len(sentence.strip()) > 20 and not any(inst in sentence.lower() for inst in instruction_starters):
                    cleaned_text = '. '.join(sentences[i:])
                    break
    
    # Limit to 2-3 sentences
    sentence_separators = r'[.!?।]+'
    sentences = re.split(sentence_separators, cleaned_text)
    if len(sentences) > 3:
        cleaned_text = '. '.join(sentences[:2])
        if not cleaned_text.endswith(('.', '।', '?', '!')):
            cleaned_text += '।' if target_language in ['hi', 'mr'] else '.'
    
    # Fallback responses in correct language
    if len(cleaned_text.strip()) < 10:
        return FALLBACK_RESPONSES.get(target_language, FALLBACK_RESPONSES['en'])
    
    return cleaned_text.strip()

# --- RAG Chain Building ---
def build_rag_chain_from_files(pdf_file, txt_file, ollama_base_url="http://localhost:11434", enhanced_mode=True, model_choice="gemma3:270m", target_language='en'):
    """
    Build a RAG chain from PDF and/or TXT files using Ollama with language-specific optimization.
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
                txt_path = tmp_tmp.name
                temp_files_to_clean.append(txt_path)

        all_docs = []
        if pdf_path:
            all_docs.extend(PyPDFLoader(pdf_path).load())
        if txt_path:
            all_docs.extend(TextLoader(txt_path, encoding="utf-8").load())
        
        if not all_docs:
            raise ValueError("No valid documents loaded or documents are empty.")

        # Improved chunking for better retrieval
        chunk_size = 500 if enhanced_mode else 600
        max_chunks = 8 if enhanced_mode else 6

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=max(80, int(chunk_size * 0.15)),
            separators=["\n\n", "\n", ". ", "! ", "? ", "। ", ", ", " ", ""],
            length_function=len
        )
        splits = splitter.split_documents(all_docs)
        
        if not splits:
            raise ValueError("Document splitting resulted in no chunks. Check document content and splitter settings.")
            
        # Use more chunks for better retrieval
        retriever = TFIDFRetriever.from_documents(splits, k=min(max_chunks, len(splits)))

        # Improved template with better context handling
        language_instruction = get_language_instruction(target_language)
        
        template = f"""{language_instruction}

Use the following context to answer the question. If the context contains relevant information, provide a helpful answer. If no relevant information is found, say that the information is not available in the documents.

Context: {{context}}

Question: {{question}}

Helpful Answer:"""

        custom_prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Initialize Ollama LLM with improved parameters
        llm = Ollama(
            base_url=ollama_base_url,
            model=model_choice,
            temperature=0.1,  # Slightly higher for better responses
            num_predict=150,  # More tokens for complete answers
            top_k=10,  # Allow more token choices
            top_p=0.3,  # Broader sampling for better quality
            callbacks=[]
        )
        
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,  # Enable source documents for relevance checking
            chain_type_kwargs={"prompt": custom_prompt, "verbose": False}
        )
            
    finally:
        for f_path in temp_files_to_clean:
            if os.path.exists(f_path):
                os.unlink(f_path)

def build_rag_chain_with_model_choice(pdf_file, txt_file, ollama_base_url="http://localhost:11434", model_choice="gemma3:270m", enhanced_mode=True, target_language='en'):
    """
    Build RAG chain with Ollama model and language specification.
    """
    return build_rag_chain_from_files(pdf_file, txt_file, ollama_base_url, enhanced_mode, model_choice, target_language)

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

# --- Improved Query Processing with Better Knowledge Base Handling ---
def process_scheme_query_with_retry(rag_chain, user_query, max_retries=2, target_language='en'):
    """
    Improved query processing with better knowledge base utilization and language enforcement
    """
    # Quick language detection
    supported_languages = {"en", "hi", "mr"}
    detected_lang = detect_language(user_query)
    
    # Use target language if specified, otherwise use detected language
    response_language = target_language if target_language in supported_languages else detected_lang
    
    if response_language not in supported_languages:
        if target_language == 'hi':
            return ("केवल मराठी, हिंदी आणि इंग्रजी भाषा समर्थित आहे.", "", 'hi', {"text_cache": "skipped", "audio_cache": "not_generated"})
        elif target_language == 'mr':
            return ("केवल मराठी, हिंदी आणि इंग्रजी भाषा समर्थित आहे.", "", 'mr', {"text_cache": "skipped", "audio_cache": "not_generated"})
        else:
            return ("Only Marathi, Hindi, and English languages are supported.", "", 'en', {"text_cache": "skipped", "audio_cache": "not_generated"})

    # Check cache first with language consideration
    query_hash = get_query_hash(user_query.lower().strip(), response_language)
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
                    result_text = query_all_schemes_optimized(rag_chain, response_language)
                else:
                    # Get relevant documents first to check relevance
                    try:
                        if hasattr(rag_chain, 'retriever') and rag_chain.retriever:
                            docs = rag_chain.retriever.get_relevant_documents(user_query)
                        else:
                            docs = []
                    except Exception:
                        docs = []
                    
                    # More lenient relevance checking
                    if docs and is_content_relevant(user_query, docs, threshold=0.1):  # Lower threshold
                        # Process the query with language context
                        language_aware_query = f"Answer in {response_language}: {user_query}"
                        result = rag_chain.invoke({"query": language_aware_query})
                        
                        # Extract the actual result properly
                        if isinstance(result, dict):
                            result_text = result.get('result', '')
                            source_docs = result.get('source_documents', [])
                            
                            # Check if we got source documents and a meaningful response
                            if source_docs and len(result_text.strip()) > 10:
                                # Good result with sources
                                pass
                            elif not source_docs:
                                # No source documents, try a broader search
                                broader_query = f"information about {user_query.split()[-1] if user_query.split() else user_query}"
                                result = rag_chain.invoke({"query": broader_query})
                                result_text = result.get('result', '') if isinstance(result, dict) else str(result)
                        elif isinstance(result, str):
                            result_text = result
                        else:
                            result_text = str(result)
                        
                        # Clean and validate the response
                        result_text = clean_response(result_text, user_query, response_language)
                        
                        # If we still don't have a good response, use fallback
                        if len(result_text.strip()) < 15 or 'NO_CONTEXT_ANSWER' in result_text:
                            result_text = KB_REFUSAL.get(response_language, KB_REFUSAL['en'])
                    else:
                        # No relevant documents found, but provide helpful guidance
                        result_text = KB_REFUSAL.get(response_language, KB_REFUSAL['en'])
                
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
                        result_text = FALLBACK_RESPONSES.get(response_language, "Server unavailable. Please try again.")
                        break
                
                elif "Request too large" in error_str or "context" in error_str.lower():
                    if response_language == 'hi':
                        result_text = "प्रश्न बहुत जटिल है। कृपया विशिष्ट योजनाओं के बारे में पूछें।"
                    elif response_language == 'mr':
                        result_text = "प्रश्न खूप जटिल आहे. कृपया विशिष्ट योजनांबद्दल विचारा."
                    else:
                        result_text = "Query too complex. Please ask about specific schemes."
                    break
                
                else:
                    result_text = FALLBACK_RESPONSES.get(response_language, "Error processing query.")
                    break
        else:
            result_text = FALLBACK_RESPONSES.get(response_language, "Unable to process query.")
    
    # Return format: (text_result, empty_audio_string, language, cache_info)
    return (result_text, "", response_language, {"text_cache": cache_status, "audio_cache": "not_generated"})

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

def query_all_schemes_optimized(rag_chain, target_language='en'):
    """Optimized scheme extractor using targeted queries and regex with language support."""
    try:
        # Multiple queries to get comprehensive results
        queries = []
        if target_language == 'hi':
            queries = [
                "सभी सरकारी योजनाओं की सूची",
                "योजना नाम और विवरण",
                "उपलब्ध कार्यक्रम और अभियान"
            ]
            response_prefix = "मुख्य योजनाएं मिलीं"
        elif target_language == 'mr':
            queries = [
                "सर्व सरकारी योजनांची यादी",
                "योजना नावे आणि तपशील",
                "उपलब्ध कार्यक्रम आणि अभियान"
            ]
            response_prefix = "मुख्य योजना सापडल्या"
        else:
            queries = [
                "List all government schemes mentioned in documents",
                "Available schemes and programs",
                "Government initiatives and policies"
            ]
            response_prefix = "Found main schemes"
        
        all_schemes = set()
        
        # Run multiple queries to get comprehensive results
        for query in queries:
            try:
                response = rag_chain.invoke({"query": query})
                content = response.get('result', '') if isinstance(response, dict) else str(response)
                schemes = extract_schemes_from_text(content)
                all_schemes.update(schemes)
            except Exception:
                continue
        
        if not all_schemes:
            return FALLBACK_RESPONSES.get(target_language, "No government schemes found in documents.")

        # Keep it reasonable - max 8 schemes
        limited_schemes = sorted(list(all_schemes))[:8]
        
        if target_language == 'hi':
            response_text = f"{len(limited_schemes)} मुख्य योजनाएं मिलीं: " + ", ".join(limited_schemes)
        elif target_language == 'mr':
            response_text = f"{len(limited_schemes)} मुख्य योजना सापडल्या: " + ", ".join(limited_schemes)
        else:
            response_text = f"Found {len(limited_schemes)} main schemes: " + ", ".join(limited_schemes)
            
        return response_text
    except Exception as e:
        if target_language == 'hi':
            return f"योजना निकालने में त्रुटि: {str(e)}"
        elif target_language == 'mr':
            return f"योजना काढण्यात त्रुटी: {str(e)}"
        else:
            return f"Error extracting schemes: {str(e)}"

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
        response = requests.get(f"{base_url}/api/tags", timeout=5)  # Increased timeout
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            if model in model_names:
                return True, "Connected and model available"
            else:
                available_models = ", ".join(model_names[:3])  # Show first 3 models
                return False, f"Model '{model}' not found. Available: {available_models}"
        else:
            return False, f"Server error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection failed - Ollama server not running"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}..."