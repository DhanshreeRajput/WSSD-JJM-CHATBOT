# WSSD JJM Chatbot (FastAPI + Ollama RAG)

A local, multilingual chatbot for Jal Jeevan Mission (WSSD) powered by a Retrieval-Augmented Generation (RAG) pipeline running on Ollama. The system answers strictly from your uploaded PDFs/TXTs and supports English, Hindi, and Marathi with a web chat widget.

## Features
- Multilingual UI and answers: English (`en`), Hindi (`hi`), Marathi (`mr`)
- KB-only mode (no hallucinations): refuses when info isn’t in uploaded docs
- Local LLM with Ollama; configurable model (default `llama3.1:8b`)
- Fast TF‑IDF retrieval and prompt designed for grounding
- Greeting intent: mirrors user greeting (e.g., “Good Morning …”) per language
- Rate limiting per session and simple health/status endpoints
- Frontend chat widget with live language switching and quick suggestions

## Repository layout
```
WSSD-JJM-CHATBOT/
  fastapp.py           # FastAPI backend
  rag_services.py      # RAG chain build + query logic
  config.py            # App & model configuration (env-aware)
  index.php            # Demo chat widget (static page, can serve as .html too)
  uploaded_files/      # Place your PDF/TXT knowledge base files here
  requirements.txt     # Python deps
  README.md            # This file
  logo/                # UI logos (jjm_new_logo.svg, main_logo.png)
```

## Prerequisites
- Windows 10/11, macOS, or Linux
- Python 3.11+ (3.13 supported)
- Ollama installed and running
  - Download and install: `https://ollama.com`
  - After install, ensure the service is running
- A supported model pulled, e.g.:
  - `ollama pull llama3.1:8b`

## Quick start
1) Create/activate a virtual environment and install deps
```bash
python -m venv .venv
. .venv/Scripts/activate    # Windows PowerShell
# or: source .venv/bin/activate  (macOS/Linux)
python -m pip install -U pip
pip install -r requirements.txt
```

2) Prepare your knowledge base
- Copy PDFs and/or TXTs into `uploaded_files/`.
- The backend will load the newest `.pdf` and `.txt` in that folder at startup.

3) Start Ollama and confirm the model is available
```bash
ollama run llama3.1:8b  # will download on first run
```

4) Run the backend
```bash
python fastapp.py
```
You should see logs including:
- “Checking Ollama connection … Connected”
- “Initializing multilingual RAG system … RAG system initialized …”

API docs: `http://localhost:8000/docs`
Health: `http://localhost:8000/health/`
Status: `http://localhost:8000/`

5) Open the chat widget demo
- Open `index.php` directly in a modern browser (it is a static page; you can rename to `index.html`).
- Or serve via PHP: `php -S localhost:8080` in this folder and navigate to `http://localhost:8080`.

## Configuration
All configuration is centralized in `config.py` and overridable via environment variables:

- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `llama3.1:8b`)
- `UPLOAD_DIR` (default `uploaded_files`)
- `RATE_LIMIT_SECONDS` (default `0.1`)
- `SUPPORTED_LANGUAGES` (`["en","hi","mr"]`)
- `DEFAULT_LANGUAGE` (`en`)
- `CHUNK_SIZE`, `MAX_CHUNKS`, `MAX_TOKENS`, `TEMPERATURE`
- `REQUEST_TIMEOUT`, `CACHE_SIZE`, `ENABLE_THREADING`
- `STRICT_KB_ONLY` (default `true`) → when true, the model is forced to answer strictly from retrieved context and will refuse if not grounded

To print config at startup, the app calls `print_config()`.

## Language behavior
- The frontend language dropdown switches all UI labels and sends the chosen language with each query.
- The backend runs the language‑specific RAG chain (`en`, `hi`, `mr`) and enforces answers in that language.
- Greeting messages mirror the user phrase per language (e.g., “Good Morning!” vs “सुप्रभात!” vs “शुभ सकाळ!”).

## KB‑only enforcement
- Prompt includes grounding rules (when `STRICT_KB_ONLY=true`).
- Pre‑retrieval relevance check validates overlap with documents; if none, a polite refusal is returned in the selected language.

## API endpoints (backend)
- `POST /query/`
  - Request: `{ input_text, model?, enhanced_mode?, session_id?, language }`
  - Response: `{ reply, language, detected_language }`
- `GET /health/` → system and connections health
- `GET /` → status, configuration, uptime
- `GET /languages/` → supported languages and labels

## Frontend usage (index.php)
- Click the circular chat bubble to open/close the widget.
- Pick a language (English/Hindi/Marathi) from the header dropdown; UI and answers follow the selection.
- Use quick suggestions or type your question. The widget shows typing indicators and connection status.
- Logos:
  - Chat header logo: `logo/jjm_new_logo.svg` (size controlled via CSS)
  - Chat bubble logo: `logo/main_logo.png` (size controlled via `.chat-bubble img`)

## How to add/update documents
1) Place new `.pdf` and/or `.txt` files in `uploaded_files/`.
2) Restart the backend. It will pick the most recently modified `.pdf` and `.txt`.

## Troubleshooting
- Ollama connection failed / model not found
  - Ensure Ollama is running: open the app/service or `ollama serve`
  - Pull the model: `ollama pull llama3.1:8b`
  - Verify tags: visit `http://localhost:11434/api/tags`
- “System is not ready …”
  - Ensure at least one `.pdf` or `.txt` exists in `uploaded_files/`
  - Check backend logs for “RAG chain built successfully”
- Answers not in selected language
  - Confirm the UI dropdown is set; the payload includes `language`
  - Ensure the chosen language is in `SUPPORTED_LANGUAGES`
- Hallucinations/out‑of‑KB answers
  - Keep `STRICT_KB_ONLY=true`. If you want looser behavior, set to `false`.
- Logo not visible
  - Confirm file paths: `logo/jjm_new_logo.svg`, `logo/main_logo.png`
  - Hard refresh (Ctrl+F5) after changes

## Deployment notes
- Windows: run with `python fastapp.py`; serve `index.php` as static (rename to `.html`) or via IIS/PHP.
- Linux/macOS: `uvicorn` can be used for production with systemd/nginx.
- Set environment variables in your process manager or `.env` (dotenv supported in `config.py`).
- For remote access, configure CORS in `fastapp.py` appropriately.

## Security considerations
- This project is for local/controlled environments. If exposing publicly:
  - Restrict CORS origins and methods
  - Add authentication for API endpoints
  - Sanitize & validate uploads and inputs

## Development tips
- Lint/typecheck: keep functions small and explicit; avoid broad try/except.
- When modifying `fastapp.py` or `rag_services.py`, watch the console for startup/health logs.

## License
Internal project for WSSD. If you need a formal license, add it here.

---
If you need a one‑page quickstart or screenshots, tell me and I’ll add them.