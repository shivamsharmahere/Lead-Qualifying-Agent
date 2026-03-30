<div align="center">
  <h1>🤖 AI-Powered Lead Capture Chatbot</h1>
  <p>
    A production-grade, highly scalable real estate AI chatbot backend designed to capture, qualify, and manage inbound user leads with near-zero latency.
  </p>
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
  [![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
</div>

---

## 🚀 Overview

Built for high performance, this AI Chatbot leverages **FastAPI** natively alongside asynchronous execution loops to provide robust webhooks and REST API interfaces. Powered by the **Groq API** (Llama 3.1 70B), the context-aware assistant expertly engages users in natural conversation. The background service securely intercepts real estate lead data via invisible HTML injections, seamlessly handling extraction, priority scoring, follow-up scheduling via **APScheduler**, and reliable mapping to **PostgreSQL** via **Alembic** and **SQLAlchemy**. A stunning **Streamlit** dashboard provides a beautiful local admin interface for managing captured leads in real time.

## ✨ Core Features

- **⚡ Blazing Fast Asynchronous Chat**: Sub-3-second end-to-end responses using asynchronous networking.
- **🛡️ Idempotent Webhooks**: Secure session and message deduplication (SHA-256 caching), ensuring complete safety against webhook and network retries.
- **🔍 Invisible JSON Data Extraction**: Injects targeted behavior prompting the LLM to secretly embed user data in HTML comments (`<!-- LEAD_DATA: {} -->`). This is silently extracted from the message payloads before delivering only the conversational response to the end-user.
- **🎯 Dynamic Priority Scoring**: An intelligent rule engine safely loaded via `Pydantic Settings` that assigns automated classifications (`HIGH`, `MEDIUM`, `LOW`, `PENDING`) based strictly on extracted user budget and timeline constraints.
- **⏰ Smart Automated Follow-ups**: An integrated APScheduler job routinely scans for unprioritized or stagnant interactions, reliably dispatching re-engagement hooks to reactivate dead leads.
- **📊 Real-Time Analytics Dashboard**: A pristine Streamlit UI directly connected to your local database to track historical and live interactions, visualize converted leads, and assess overall system efficiency.

---

## 🏭 Built for Production

This bot isn't just a prototype—it incorporates industry-standard practices designed for real-world scaling and stability:

- **Scalable, Industry-Standard Directory Structure**: Adheres to modern FastAPI paradigms (separating `api`, `core`, `models`, `schemas`, and `services`) ensuring clean code separation as the codebase grows.
- **Robust Caching & Idempotency**: Prevents processing the same webhook payload multiple times using SHA-256 caching natively, avoiding redundant LLM costs or duplicated leads on network retries.
- **Config-Driven Operations**: Uses `Pydantic Settings` for strict environment validation (budget thresholds, logging levels, limits), failing fast on start-up if production environments lack critical parameters.
- **Async-First Execution**: Fully leverages Python's `asyncio` using `Asyncpg` and asynchronous LLM clients to eliminate blocking I/O constraints under heavy concurrent traffic.
- **Dependency Injected Database**: Features safe connection pooling and SQLAlchemy session management strictly mapped via FastAPI dependency injections, ensuring database connections never leak.

---

## 🛠️ Architecture & Tech Stack

```mermaid
graph LR
    User([User Client]) <--> API[FastAPI Webhook Engine]
    API <-->|Context & Prompts| LLM[Groq Llama 3 API]
    API <-->|Store Sessions & Leads| DB[(PostgreSQL + Asyncpg)]
    DB --> Web[Streamlit Admin Dashboard]
    Job[APScheduler] -->|Scan & Follow-up| DB
```

- **Backend Logic**: Python 3.10+, FastAPI, Pydantic v2
- **Database Engine**: PostgreSQL 16+ (Neon/Local), SQLAlchemy 2 (async), Alembic
- **Intelligence**: Groq Cloud (Llama3.1 70B/8B Variants), Langchain-Groq
- **Event Scheduling**: APScheduler (AsyncIOScheduler)
- **Frontend Panel**: Streamlit
- **Quality Assurance**: Pytest, Pytest-Asyncio, HTTPX

---

## 🚦 Getting Started

### 1. Prerequisites
- **Python 3.10+** (3.11 recommended)
- A highly performant **Groq API Key** (Provision at [console.groq.com](https://console.groq.com))
- A **PostgreSQL Database** connection string (ensure your dialect explicitly calls `postgresql+asyncpg://`)

### 2. Installation
Clone the repository and switch into the workspace:

```bash
git clone https://github.com/yourusername/lead-capturing-bot.git
cd lead-capturing-bot
```

Create and activate a robust virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

Install locked project dependencies safely:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Safely map `.env.example` directly to a local `.env`:

```bash
cp .env.example .env
```

Hydrate the `.env` variables:
```env
# Critical Infrastructure
GROQ_API_KEY="gsk_your_groq_api_key_here"
GROQ_MODEL="groq/llama-3.1-70b-versatile"
DATABASE_URL="postgresql+asyncpg://admin:password@localhost:5432/leadbot_db"

# Settings Engine Controls
LOG_LEVEL="INFO"
MAX_CONTEXT_MESSAGES=20
FOLLOW_UP_INACTIVITY_MINUTES=30
FOLLOW_UP_MAX_COUNT=3
HIGH_PRIORITY_BUDGET_INR=7000000
HIGH_PRIORITY_TIMELINE_MONTHS=3
```

### 4. Database Setup
Ensure robust schema validation mapping directly via Alembic automated migrations:
```bash
alembic upgrade head
```

### 5. Launch the Application!
Our custom CLI runner securely hosts your infrastructure gracefully shutting down all child processes when necessary:

```bash
# Run BOTH backend & dashboard natively:
python main.py

# Or run exclusively the backend daemon:
python main.py --b

# Or run exclusively the Streamlit dashboard:
python main.py --f
```

Endpoints online:
- **FastAPI Core**: `http://localhost:8000`
- **Streamlit Admin**: `http://localhost:8501`

---

## 📁 Repository Structure

```text
├── app/                  # FastAPI Core
│   ├── api/              # Routers, Webhook Receivers, Endpoint Controllers
│   ├── agents/           # Langchain Agents & Structured LLM Prompts
│   ├── core/             # Pydantic Settings, Middleware Configurations
│   ├── models/           # SQLAlchemy Relational Models Mapping
│   ├── schemas/          # Strict Request Validation & Response Serialization
│   └── services/         # Pluggable Feature Services (Scoring, JSON Extracting)
├── dashboard/            # Local Streamlit UI Component Root
├── alembic/              # Async PostgreSQL Revision Managers
├── main.py               # Central Multi-Process Coordinator
├── requirements.txt      # Dependency Definitions
└── pytest.ini            # Global Testing Configuration
```

---

## 🔌 Core API Documentation

### 1. `POST` Webhook Receiver
Directly simulates an inbound messaging layer, querying the LLM synchronously, parsing background hidden entities, securely writing data to Postgres.

```bash
curl -X POST "http://localhost:8000/webhook" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "session_001", "message": "Im looking for a 3BHK in Gurgaon. My budget is 85 lakhs and I need it in 2 months."}'
```
**JSON Payload Returned**:
```json
{
  "session_id": "session_001",
  "reply": "Excellent choice! A 3BHK in Gurgaon is very doable with your budget. I can note these preferences for our agents.",
  "lead_extracted": true,
  "lead_priority": "HIGH"
}
```

### 2. `GET` Fetch Chat History
Returns stripped message history (ignoring internal reasoning and raw system prompts) for clean integrations dynamically formatting assistant history.
```bash
curl http://localhost:8000/reply/session_001
```

**Conversation Payload Returned**:
```json
{
  "session_id": "session_28b5159ff261",
  "messages": [
    {
      "role": "user",
      "content": "Hi"
    },
    {
      "role": "assistant",
      "content": "Hi, this is Alex! We help people with software development, finding properties, buying cars, and a few other things — so whatever you need, we've probably got you covered. What can I do for you today?"
    },
    {
      "role": "user",
      "content": "I wanted to buy a flat in Gurgaon can you help me in that"
    },
    {
      "role": "assistant",
      "content": "Oh nice, so you're looking to buy a flat in Gurgaon — I can definitely help with that! Tell me a bit more about what you have in mind, like size or area preference?"
    },
    {
      "role": "user",
      "content": "I am thinking to buy a 3BHK flat in a good society"
    },
    {
      "role": "assistant",
      "content": "Got it — so you're after a 3BHK in a good society in Gurgaon. Okay so just to make sure I've got this right — you're looking for a 3BHK flat in a nice society in Gurgaon, is that correct?"
    },
    {
      "role": "user",
      "content": "yes"
    },
    {
      "role": "assistant",
      "content": "Perfect! And may I have your good name, please?"
    },
    {
      "role": "user",
      "content": "My name is Shivam Sharma"
    },
    {
      "role": "assistant",
      "content": "Great to meet you, Shivam! And what's the best email to reach you at?"
    },
    {
      "role": "user",
      "content": "shivamsharma.aiml@gmail.com"
    },
    {
      "role": "assistant",
      "content": "Perfect, thanks Shivam! And what kind of budget are you working with for this?"
    },
    {
      "role": "user",
      "content": "Umm ! I am thinking about 80 Lakh to 1 CR"
    },
    {
      "role": "assistant",
      "content": "Nice range — 80 lakh to 1 crore, got it! And is it just yourself making this decision, or is someone else involved too?"
    },
    {
      "role": "user",
      "content": "Naa its just me"
    },
    {
      "role": "assistant",
      "content": "Got it — just you! And what’s the most important thing to you in this — like what would make it the perfect place so we can find the right solution for you?"
    },
    {
      "role": "user",
      "content": "Yaa, it would be best if the flat is near the main area of Gurgoan or DLF"
    },
    {
      "role": "assistant",
      "content": "Perfect — so close to main Gurgaon or DLF for convenience. And when are you looking to get this sorted — is there a particular deadline?"
    },
    {
      "role": "user",
      "content": "could it be possible to do that in 2 months"
    },
    {
      "role": "assistant",
      "content": "Absolutely, two months is doable! Honestly, based on everything you've told me, we do have some really good options that could work well for you. What I'll do is have our team put together something specific to your budget and location and get back to you within 24 hours — does that work?"
    },
    {
      "role": "user",
      "content": "yeah sure"
    },
    {
      "role": "assistant",
      "content": "Perfect! We'll be in touch very soon, Shivam. Feel free to reach out if anything comes up in the meantime!"
    },
    {
      "role": "assistant",
      "content": "Hi Shivam Sharma, given your timeline, I have some great properties options that could be a perfect fit. Shall we continue?"
    }
  ]
}
```

### 3. `GET` Lead Retrieval
Structured endpoint securely paginating database lead components for immediate integration.
```bash
curl "http://localhost:8000/leads?limit=10&offset=0"
```

---

## 🔮 Roadmap & Future Optimizations

While already robust for scaling, the following capabilities can be augmented into the architecture to ensure enterprise-level fault tolerance and lower latency:
- **Distributed Rate Limiting**: Implement strict throttling per IP or session hash at the ingress layer (via Redis) to prevent DDoS conditions from exhausting backend LLM quotas.
- **LLM Response Caching**: Deploying semantic or substring caching for extremely common conversational intents. If users ask repetitive questions (e.g., "What are your operating hours?"), these could be served directly from memory.
- **Prompt Caching**: Utilizing native prompt-caching parameters on the LLM side to temporarily store our heavy persona instruction sets. This drastically lowers per-token overheads during lengthy user interactions.
- **Vectorized RAG Integration**: Expand the persona via a vector database (like Milvus or Pinecone) allowing the assistant to actively pull specific floor plans or live inventory statuses dynamically during the conversation.

---

## 🧪 Testing

Boot the exhaustive `pytest` suite safely covering mock dependency injection, async I/O routines, extraction boundaries, and critical idempotency metrics:

```bash
pytest -v
```

---
<div align="center">
  <i>Maintained with ❤️ for rapid prototyping and robust reliability.</i>
</div>