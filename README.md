# AI-Powered Lead Capture Chatbot

A production-grade, scalable backend that simulates a real estate AI chatbot capable of capturing, qualifying, and managing inbound user leads. 

Built with **FastAPI**, **Groq** (llama3-70b/8b), **PostgreSQL** (via Neon for cloud scale), and **Streamlit**.

## Features

- **Asynchronous Chat Loop**: Powered by `AsyncGroq` and `httpx` to provide under 2-3 seconds turnaround latency.
- **Idempotency**: Implements native webhook duplication checking via SHA-256 session and message content hashing. Safe for network retries.
- **Hidden JSON Extraction**: Instructs the LLM to reply with a formatted JSON block hidden in HTML comments `<!-- LEAD_DATA: {} -->`, safely extracted into backend memory before returning user-friendly messages. Regex-based fallback parser included.
- **Scoring Engine**: Evaluates `HIGH`, `MEDIUM`, `LOW`, and `PENDING` lead classification dependent upon highly configurable rule bounds (budget, timeline) loaded natively from environment variables via Pydantic Settings.
- **Automated Follow-ups (APScheduler)**: Background task runs every 15 minutes checking for inactive, unprioritized leads and dispatches intelligent nudge templates.
- **Analytics Dashboard**: Streamlit Dashboard pointing natively to the SQL store to generate live views, lead tables, metric grids, and conversation playbacks.

## Tech Stack Overview

- **Backend**: Python 3.10+, FastAPI, Pydantic v2
- **Database**: PostgreSQL 16+ (Hosted on Neon), SQLAlchemy 2 (async), Alembic for migrations
- **LLM**: Groq API
- **Task Runner**: APScheduler (AsyncIOScheduler)
- **Frontend / Admin**: Streamlit
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## Developer Setup

### 1. Requirements
- Python 3.10+
- A [Groq API Key](https://console.groq.com)
- A PostgreSQL Database string (e.g., from Neon). *Note: Ensure your connector string uses the `postgresql+asyncpg://` dialect!*

### 2. Local Quickstart & Installation

```bash
# Clone the repository and move into it
# Create the virtual environment
python -m venv venv

# Activate the virtual environment
# Windows:
.\venv\Scripts\Activate
# macOS/Linux:
source venv/bin/activate

# Install all dependencies (development & production)
pip install -r requirements.txt
```

### 3. Configuration Setup

Create a `.env` file in the root directory (based on `.env.example` parameters):

```env
# Example .env configuration
GROQ_API_KEY="gsk_your_groq_api_key_here"
DATABASE_URL="postgresql+asyncpg://user:password@ep-your-db-instance.region.aws.neon.tech/dbname?sslmode=require"

# Optional App Overrides
LOG_LEVEL="INFO"
MAX_CONTEXT_MESSAGES=20
FOLLOW_UP_INACTIVITY_MINUTES=30
FOLLOW_UP_MAX_COUNT=3
HIGH_PRIORITY_BUDGET_INR=7000000
HIGH_PRIORITY_TIMELINE_MONTHS=3
```

### 4. Database Migrations

Initialise your PostgreSQL database schema with Alembic:

```bash
alembic upgrade head
```

### 5. Start the Services

You can start both the FastAPI backend and the Streamlit dashboard together using the single root script:

```bash
python main.py
```

This will spin up the backend on `http://localhost:8000` and the Streamlit dashboard on `http://localhost:8501`. 
Press `Ctrl+C` to gracefully shut down both services.

*(Note: If you still prefer running them manually, use `uvicorn app.main:app` and `python -m streamlit run dashboard/main.py` in separate terminals).*

---

## Architecture Design Paradigm

- **`app/api/`**: The FastAPI endpoints interfacing with the outer web. Includes webhook receivers and REST endpoints.
- **`app/schemas/`**: Strict Pydantic models for incoming POST validation and outbound serialization.
- **`app/services/`**: Pluggable python classes encapsulating business logic:
  - `chat.py`: LLM pipeline connection.
  - `extraction.py`: Regex and JSON parser.
  - `lead.py` / `scoring.py`: Lead priority assignments and persistence.
  - `message.py`: Idempotency hashes and chat history bounds.
  - `followup.py`: Job templates for APScheduler.
- **`app/models/`**: SQLAlchemy 2 models mapping strictly to the database.

---

## API Examples

### 1. `GET /health`
Liveness probe checking DB and LLM configuration setup.
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

### 2. `POST /webhook`
Submits a user message, calls Groq, parses fields, and manages chat history.
```powershell
Invoke-RestMethod -Uri http://localhost:8000/webhook -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"session_id": "session_123", "message": "Hi, Im looking for a 3BHK in Gurgaon with a budget of 85 lakhs. Needs to be ready in 2 months."}'
```
**Response:**
```json
{
  "session_id": "session_123",
  "reply": "Hi there! Excellent choice, Gurgaon has some great 3BHK options...",
  "lead_extracted": true,
  "lead_priority": "high",
  "tokens_used": 156,
  "cached": false
}
```

### 3. `GET /reply/{session_id}`
Fetches the clean transcript representing user vs assistant history.
```bash
curl http://localhost:8000/reply/session_123
```

### 4. `GET /leads`
A Paginated API listing captured customer constraints, budgets, preferences, and priority scores.
```bash
curl "http://localhost:8000/leads?limit=10&offset=0"
```

---

## Testing

To run the full suite of unit and integration tests (Async httpx clients):
```bash
pytest -v
```

This will automatically pick up `pytest-asyncio` fixtures, execute DB mocking pipelines, and validate idempotency rules.