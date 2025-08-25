import tempfile
import os
import time
import hashlib
import re
import langid
from core.transcription import SUPPORTED_LANGUAGES  
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from langchain_community.retrievers import TFIDFRetriever
from langchain.prompts import PromptTemplate
from langchain.globals import set_verbose
from langchain.callbacks.base import BaseCallbackHandler

# Removed TTS dependency - now hardcoded to False for text-only mode
TTS_AVAILABLE = False

# For language detection of the query
try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0 # for consistent results
except ImportError:
    print("Warning: langdetect not installed. Query language validation will be skipped. pip install langdetect")

set_verbose(True) # Optional: for Langchain verbosity

_query_cache = {}
_cache_max_size = 50

def get_query_hash(query_text):
    """Generate a hash for caching queries"""
    return hashlib.md5(query_text.encode()).hexdigest()

def cache_result(query_hash, result):
    """Cache query result"""
    global _query_cache
    if len(_query_cache) >= _cache_max_size:
        # Remove oldest entry (FIFO)
        try:
            oldest_key = next(iter(_query_cache))
            del _query_cache[oldest_key]
        except StopIteration: # Should not happen if cache_max_size > 0
            pass
    _query_cache[query_hash] = result

def get_cached_result(query_hash):
    """Get cached result if available"""
    return _query_cache.get(query_hash)

def clear_query_cache():
    """Clear the RAG query cache"""
    global _query_cache
    _query_cache.clear()
    print("RAG query cache cleared.")

def detect_language_langid(text):
    """Return the ISO 639-1 language code and full language name, if supported."""
    lang, _ = langid.classify(text)
    return lang, SUPPORTED_LANGUAGES.get(lang, "Unsupported")

# --- RAG Chain Building ---
def build_rag_chain_from_files(pdf_file, txt_file, ollama_base_url="http://localhost:11434", enhanced_mode=True, model_choice="hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0"):
    """
    Build a RAG chain from PDF and/or TXT files using Ollama.
    """
    pdf_path = txt_path = None
    if not (pdf_file or txt_file):
        raise ValueError("At least one file (PDF or TXT) must be provided.")
    
    temp_files_to_clean = []
    try:
        if pdf_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(pdf_file.getvalue()) # Use getvalue() for UploadedFile
                pdf_path = tmp_pdf.name
                temp_files_to_clean.append(pdf_path)
        if txt_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_txt:
                tmp_txt.write(txt_file.getvalue()) # Use getvalue() for UploadedFile
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
        chunk_size = 400 if enhanced_mode else 500
        max_chunks = 8 if enhanced_mode else 10
        max_tokens = 1000  # Conservative for local model

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=max(80, int(chunk_size * 0.2)), # Overlap as a percentage of chunk_size
            separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
            length_function=len
        )
        splits = splitter.split_documents(all_docs)
        
        if not splits:
            raise ValueError("Document splitting resulted in no chunks. Check document content and splitter settings.")
            
        retriever = TFIDFRetriever.from_documents(splits, k=min(max_chunks, len(splits)))

        template = """You are an efficient Knowledge Assistant, designed for answering questions specifically from the knowledge base provided to you.

Your task is to give a detailed response for the user query in the user language.

Ensure your response follows these guidelines:
* Always answer in the **same language as the Question**, regardless of the language of the source documents.
* If the source documents are in Marathi and the question is in English, translate and summarize the information into English.
* If the question is in Marathi, answer in Marathi. Do the same for English and Hindi.
* Use direct, everyday language.
* Maintain a personal and friendly tone.
* Provide detailed responses with toll-free numbers and website URLs *only if present in the knowledge base*.
* Use section headers like "Description", "Eligibility", or for Marathi: "उद्देशः", "अंतर्भूत घटकः".
* Format your answer using markdown with headings (##), bold, bullet lists where appropriate.
* If there is no relevant context for the question, simply say:  
  - **In Marathi**: "क्षमस्व, मी या विषयावर तुमची मदत करू शकत नाही. अधिक माहितीसाठी, कृपया १०४/१०२ हेल्पलाइन क्रमांकावर संपर्क साधा."  
  - **In Hindi**: "माफ़ कीजिए, मैं इस विषय पर आपकी मदद नहीं कर सकती। अधिक जानकारी के लिए कृपया 104/102 हेल्पलाइन नंबर पर संपर्क करें।"  
  - **In English**: "I'm sorry, I cannot assist with that topic. For more details, please contact the 104/102 helpline numbers."
* Remove duplicate information and provide only one consolidated answer.
* Do not provide answers based on assumptions or general knowledge. Use only the information provided in the knowledge base.
* If the user asks for jokes, casual conversation, or anything not related to the knowledge base, respond with the helpline apology message.

Context from knowledge base: {context}

Question: {question}

Answer:"""

        custom_prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Initialize Ollama LLM
        llm = Ollama(
            base_url=ollama_base_url,
            model=model_choice,
            temperature=0.1,  # Keep it deterministic
            num_predict=max_tokens,
            callbacks=[StrictContextCallback()]
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

def build_rag_chain_with_model_choice(pdf_file, txt_file, ollama_base_url="http://localhost:11434", model_choice="hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0", enhanced_mode=True):
    """
    Build RAG chain with Ollama model. This is the primary RAG chain builder.
    """
    return build_rag_chain_from_files(pdf_file, txt_file, ollama_base_url, enhanced_mode, model_choice)

def detect_language(text):
    """
    Auto-detect language from text
    Returns language code (e.g., 'en', 'hi', 'mr')
    """
    try:
        clean_text = re.sub(r'[^\w\s]', '', text)
        if len(clean_text.strip()) < 10:
            return 'en'
        
        detected = detect(clean_text)
        
        lang_mapping = {
            'hi': 'hi',
            'mr': 'mr',
            'en': 'en'
        }
        
        return lang_mapping.get(detected, 'en')
        
    except Exception as e:
        print(f"Language detection failed: {e}")
        return 'en'

# --- Query Processing ---
def process_scheme_query_with_retry(rag_chain, user_query, max_retries=3):
    """
    Process query with rate limit handling and caching.
    Returns: (text_result, empty_string, language_detected, cache_info)
    Modified for text-only mode with local Ollama
    """
    # Detect language and enforce allowed languages for text processing
    supported_languages = {"en", "hi", "mr"}
    detected_lang = detect_language(user_query)
    if detected_lang not in supported_languages:
        return (
            "⚠️ Sorry, only Marathi, Hindi, and English are supported. कृपया मराठी, हिंदी अथवा इंग्रजी भाषेत विचारा.",
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
                    result = rag_chain.invoke({"query": user_query})
                    if isinstance(result, dict):
                        result_text = result.get('result', 'No results found.')
                    elif isinstance(result, tuple) and len(result) > 0:
                        result_text = str(result[0])
                    else:
                        result_text = str(result)
                # Cache only the raw answer
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
                        result_text = "Unable to connect to local Ollama server. Please ensure Ollama is running with the BharatGPT model."
                        break
                
                elif "Request too large" in error_str or "context" in error_str.lower():
                    if is_comprehensive_query and attempt == 0:
                        simplified_query = "list main government schemes"
                        try:
                            result = rag_chain.invoke({"query": simplified_query})
                            result_text = result.get('result', 'No results found.')
                            result_text = f"[Simplified due to size limits] {result_text}"
                            break
                        except:
                            pass
                    
                    result_text = "Query too large for current model. Try asking about specific schemes or categories instead of requesting all schemes at once."
                    break
                
                else:
                    result_text = f"Error processing query: {error_str}"
                    break
        else:
            result_text = "Unable to process query after multiple attempts. Please try a simpler question."
    
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
        context_query = "Provide a comprehensive list of all government schemes, programs, and yojana mentioned in the documents."
        response = rag_chain.invoke({"query": context_query})
        content_to_parse = response.get('result', '')
        
        all_extracted_schemes = extract_schemes_from_text(content_to_parse)

        if not all_extracted_schemes:
            return "No government schemes were confidently extracted. The documents might not contain a clear list, or the format is not recognized."

        response_text = f"✅ Found {len(all_extracted_schemes)} potential schemes:\n\n"
        for i, scheme in enumerate(all_extracted_schemes, 1):
            response_text += f"{i}. {scheme}\n"
        response_text += "\n\nℹ️ Note: This list is extracted based on document content. Some names may be partial or inferred."
        return response_text
    except Exception as e:
        return f"Error during optimized scheme query: {str(e)}"

# --- Configuration/Helpers ---
def get_model_options():
    """Return available Ollama models with their characteristics."""
    return {
        "hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0": {
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

def check_ollama_connection(base_url="http://localhost:11434", model="hf.co/mradermacher/BharatGPT-3B-Indic-i1-GGUF:q4_0"):
    """Check if Ollama server is running and model is available"""
    try:
        import requests
        # Check if Ollama is running
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            if model in model_names:
                return True, "Ollama server is running and model is available"
            else:
                return False, f"Model '{model}' not found. Available models: {model_names}"
        else:
            return False, f"Ollama server responded with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Ollama server. Please ensure Ollama is running on http://localhost:11434"
    except Exception as e:
        return False, f"Error checking Ollama connection: {str(e)}"

class StrictContextCallback(BaseCallbackHandler):
    """Callback to monitor and log RAG responses"""
    
    def on_chain_end(self, outputs, **kwargs):
        """Check if response might contain external knowledge"""
        response = outputs.get("result", "")
        suspicious_phrases = [
            "I believe",
            "generally",
            "typically",
            "in most cases",
            "commonly",
            "as per my knowledge",
            "based on my understanding"
        ]
        
        for phrase in suspicious_phrases:
            if phrase.lower() in response.lower():
                print(f"Warning: Response may contain external knowledge. Suspicious phrase: {phrase}")