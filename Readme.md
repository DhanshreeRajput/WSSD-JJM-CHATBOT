	
 	
	 WSSD-JJM Chatbot

This project contains a lightweight frontend (PHP) chat widget and a FastAPI backend that powers a bilingual (English/Marathi) scripted grievance and feedback flow, including a 5 star rating system and CSV export.

### Features
- Bilingual scripted flow (English/Marathi)
- Greeting detection and guided questions
- 5 star rating with label mapping and CSV export
- Simple in memory session/chat history
- CORS enabled for local development

### Tech Stack
- Backend: FastAPI, Uvicorn, Pydantic
- Frontend: PHP (for serving), HTML/CSS/Vanilla JS
- Packaging: pip/venv (no build tools required)

### File/Directory Structure (detailed)
```
WSSD-JJM-CHATBOT/
├─ fastapp.py               # FastAPI application (all endpoints live here)
│  ├─ /                    # Root returns runtime info (uptime, sessions, etc.)
│  ├─ /query/              # Processes user input; returns guided responses
│  ├─ /rating/             # Accepts 1–5 ratings; stores in memory
│  ├─ /ratings/export      # Returns ratings as UTF 8 BOM CSV
│  ├─ /ratings/stats       # Returns rating stats (avg, distribution)
│  ├─ /health/             # Health probe
│  ├─ /languages/          # Supported languages metadata
│  └─ /suggestions/        # Quick suggestion strings for UI
│
├─ index.php               # Frontend chat widget and UI logic
│  ├─ API_BASE_URL         # Configure backend URL (default http://localhost:8000)
│  ├─ UI styles            # Chat bubble, window, messages, rating stars
│  └─ Flow logic           # Start → feedback → rating; quick suggestions
│
├─ api_helper.php          # Optional helper (not required by current widget)
│
├─ logo/
│  ├─ jjm_new_logo.svg     # Header/logo in chat window
│  └─ main_logo.png        # Floating chat bubble icon
│
└─ ratings_data/           # Optional folder if you later persist ratings to disk
```

Notes
- The backend currently stores chat history and ratings in memory. If you want persistence, you can save to CSV on each `/rating/` call (see "Optional: enable CSV persistence" below).
- `index.php` contains all widget UI/UX. Images are loaded from `logo/`.

---

## Prerequisites

- Windows 10/11 (PowerShell)
- Python 3.9+ (recommend 3.10 or newer)
- pip
- PHP 8+ (for serving `index.php`; you can also use any web server like Apache/Nginx)

---

## Backend (FastAPI) – Setup and Run

1) Create and activate a virtual environment

```powershell
cd C:\Users\saarsys\Desktop\JJM_WSSD_CHATBOT\WSSD-JJM-CHATBOT
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
pip install fastapi "uvicorn[standard]" pydantic
# optional (handy for testing): httpx requests
```

Or pin versions (example):

```powershell
pip install "fastapi==0.111.*" "uvicorn[standard]==0.30.*" "pydantic==2.*"
```

3) Run the API server

```powershell
python fastapp.py
```

The server will start on `http://localhost:8000/` and prints helpful links:
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health/`
- Status: `http://localhost:8000/status/`
- Ratings CSV export: `http://localhost:8000/ratings/export`

Notes
- CORS is open to `*` for local development. Restrict it in production.
- Data (chat history and ratings) is in memory and resets on restart.

Alternative run (explicit uvicorn):

```powershell
uvicorn fastapp:app --host 0.0.0.0 --port 8000 --reload
```

---

## Frontend (PHP) – Serve the Chat Widget

1) Ensure the backend is running on `http://localhost:8000`.
2) Serve the PHP page from the project root:

```powershell
cd C:\Users\saarsys\Desktop\JJM_WSSD_CHATBOT\WSSD-JJM-CHATBOT
php -S localhost:8080 index.php
```

3) Open `http://localhost:8080` in your browser. Click the circular chat bubble to open the widget.

If your backend runs at a different URL, update `API_BASE_URL` in `index.php` near the bottom of the file.

---

## API Overview

- `POST /query/`
  - Body: `{ "input_text": "string", "session_id": "optional", "language": "en|mr" }`
  - Returns guided responses and manages a simple state machine per `session_id`.

- `POST /rating/`
  - Body: `{ "rating": 1..5, "session_id": "optional", "language": "en|mr", "grievance_id": "optional", "feedback_text": "optional" }`
  - Saves rating in memory and returns a thank you message (with labels in the chosen language).

- `GET /ratings/export`
  - Downloads a UTF 8 BOM CSV containing recent ratings.

- `GET /ratings/stats`
  - Returns totals, averages, and distributions for ratings.

- `GET /health/`, `GET /languages/`, `GET /suggestions/`
  - Utility endpoints for monitoring and UI hints.

### Request/Response Examples

Query (English):
```powershell
curl -X POST "http://localhost:8000/query/" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_text\":\"hello\",\"language\":\"en\"}"
```

Query (Marathi):
```powershell
curl -X POST "http://localhost:8000/query/" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_text\":\"नमस्कार\",\"language\":\"mr\"}"
```

Rating example (PowerShell):
```powershell
curl -X POST "http://localhost:8000/rating/" ^
  -H "Content-Type: application/json" ^
  -d "{\"rating\":5,\"language\":\"en\"}"
```

---

## Common Issues

- Port already in use: Change the port in `fastapp.py` or stop the conflicting process.
- CORS errors in browser: Confirm backend is running and `API_BASE_URL` matches the backend origin.
- Images not loading: Ensure files in `logo/` are present and paths in `index.php` are correct.
- 404 on `/ratings/export`: You must submit at least one rating before exporting.

---

## Production Notes

- Restrict `allow_origins` in CORS middleware to your real domain.
- Use a process manager (e.g., systemd, NSSM on Windows) for the FastAPI app via `uvicorn` or `gunicorn` (with `uvicorn.workers.UvicornWorker`).
- Serve the PHP/HTML with a proper web server (Apache/Nginx/IIS) and point the site root at this folder.

### Configuration points
- Backend CORS: Edit `fastapp.py` inside the `add_middleware(CORSMiddleware, allow_origins=[...])` call.
- Frontend API URL: Edit `API_BASE_URL` constant in `index.php`.

### Optional: enable CSV persistence on write
By default ratings are kept in memory and only exported on request. If you want to append each rating to a CSV file under `ratings_data/`:
1. Create the folder if it does not exist.
2. In `fastapp.py`, inside `save_rating_data(...)`, append `rating_entry` to a CSV path (e.g., `ratings_data/ratings_log.csv`). Make sure to open the file with `encoding='utf-8-sig'` for proper Marathi characters and write headers if the file is empty.

### Logging
- The backend uses Python `logging` with level `INFO`. Adjust with `logging.basicConfig(level=logging.DEBUG)` during development if needed.

---

## Development Workflow

1) Run backend with `uvicorn` in `--reload` mode.
2) Serve frontend with `php -S` or your local web server.
3) Edit `index.php` styles or text; refresh browser.
4) Use `http://localhost:8000/docs` to try endpoints quickly.

Recommended VS Code/Cursor extensions: Python, PHP Intelephense, REST Client.

---

## License

Internal/Private project unless stated otherwise.


