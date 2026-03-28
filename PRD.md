**PRODUCT REQUIREMENTS DOCUMENT**

**AI-Powered Lead Capture Chatbot**

FastAPI • Groq LLM • PostgreSQL • Streamlit

| Version | 1.0.0 |
| --- | --- |
| Date | March 2026 |
| Tech Stack | FastAPI + Groq + PostgreSQL |
| Timeline | 4-5 Days |
| Status | Draft — For Review |

# 1\. Executive Summary

This document defines the full product requirements for an AI-powered Lead Capture Chatbot. The system uses FastAPI (Python) as the web framework, Groq (llama3-70b-8192) as the LLM provider, PostgreSQL for data persistence, and Streamlit for a real-time analytics dashboard.

The chatbot autonomously engages inbound users, qualifies leads through structured conversation, extracts key fields, scores lead priority, and triggers follow-up messages for inactive sessions — all with minimal human intervention.

| Core ObjectiveBuild a production-grade, scalable backend that simulates a real estate AI chatbot capable of capturing, qualifying, and managing inbound user leads. The codebase must follow industry best practices: idempotent operations, service-layer separation, async-first design, and >80% test coverage. |
| --- |

# 2\. Goals & Success Criteria

## 2.1 Primary Goals

*   Accept inbound user messages via a /webhook endpoint and persist them to the database.
*   Use Groq-hosted LLM to generate natural, context-aware replies maintaining full conversation history.
*   Extract structured lead fields (name, budget, preference/location, timeline) from free-form chat.
*   Score leads automatically as High, Medium, or Low priority using configurable rules.
*   Trigger personalised follow-up nudges after a configurable inactivity window.
*   Expose a Streamlit dashboard with live lead statistics and conversation replay.

## 2.2 Success Metrics

| Metric | Target | Priority |
| --- | --- | --- |
| API response latency (p95) | < 2 seconds end-to-end | High |
| Lead field extraction accuracy | > 85% field coverage per session | High |
| Follow-up trigger reliability | 100% for configured inactivity window | High |
| Idempotent webhook handling | Zero duplicate records on retry | High |
| Dashboard data refresh | < 5 seconds stale window | Medium |
| Unit test coverage (services) | > 80% | Medium |

# 3\. System Architecture

The system follows a layered, service-oriented architecture. Each concern is isolated into its own module to maximise testability, replaceability, and horizontal scalability.

## 3.1 Request Flow

| Data FlowUser Message -> POST /webhook -> MessageService (persist + idempotency check) -> ChatService (Groq LLM call) -> ExtractionService (parse lead fields) -> LeadService (upsert + score) -> JSON Response | Background: APScheduler -> FollowUpService -> inactive session nudge -> Streamlit Dashboard reads DB directly |
| --- |

## 3.2 Folder Structure

| Path | Responsibility |
| --- | --- |
| app/models/ | SQLAlchemy 2 ORM models — Lead, Message |
| app/schemas/ | Pydantic v2 request / response schemas |
| app/services/ | All business logic: chat, lead, extraction, scoring, follow-up |
| app/api/ | FastAPI routers — /webhook, /reply, /leads, /health |
| app/db.py | Async SQLAlchemy engine + session factory |
| app/config.py | Pydantic BaseSettings — typed env var loading |
| app/tasks.py | APScheduler follow-up job definitions |
| main.py | FastAPI app factory, lifespan, middleware, router registration |
| dashboard/app.py | Streamlit dashboard entry point |
| alembic/ | Database schema migration scripts |
| tests/ | pytest unit + integration test suite |
| requirements.txt | Pinned production dependencies (pip-compile) |
| .env.example | Environment variable template for contributors |

## 3.3 Technology Stack

| Component | Technology | Rationale |
| --- | --- | --- |
| Web Framework | FastAPI 0.111+ | Async-native, auto OpenAPI docs, Pydantic v2 integration |
| LLM Provider | Groq — llama3-70b-8192 | Ultra-low latency inference, OpenAI-compatible Python SDK |
| ORM | SQLAlchemy 2 (async) | Mature, async support, Alembic migration tooling |
| Database | PostgreSQL 16 | ACID guarantees, JSONB for flexible fields, battle-tested |
| Task Scheduler | APScheduler 3.x | In-process cron jobs for follow-up nudges |
| Settings | Pydantic BaseSettings | Type-safe env vars with .env file support |
| Dashboard | Streamlit | Rapid analytics UI with direct DB access |
| Testing | pytest + httpx | Async test client, fixture-based, coverage reporting |
| Migrations | Alembic | Schema versioning tied to SQLAlchemy models |

# 4\. Database Design

## 4.1 Leads Table

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| id | UUID (PK) | No | Auto-generated primary key |
| session_id | VARCHAR(64) UNIQUE | No | Unique conversation session identifier |
| name | VARCHAR(255) | Yes | Extracted lead full name |
| budget | NUMERIC(15,2) | Yes | Extracted budget value in INR |
| preference | TEXT | Yes | Location or property type preference |
| timeline_months | INTEGER | Yes | Purchase or move-in timeline in months |
| priority | ENUM (high/medium/low/pending) | No | Lead score classification |
| raw_data | JSONB | Yes | Full extracted payload for extensible fields |
| follow_up_count | INTEGER DEFAULT 0 | No | Number of follow-ups sent to this lead |
| follow_up_sent_at | TIMESTAMPTZ | Yes | Timestamp of most recent follow-up message |
| created_at | TIMESTAMPTZ | No | Record creation timestamp (auto-set) |
| updated_at | TIMESTAMPTZ | No | Last-updated timestamp (auto-maintained) |

## 4.2 Messages Table

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| id | UUID (PK) | No | Auto-generated primary key |
| session_id | VARCHAR(64) | No | Foreign key to leads.session_id (indexed) |
| role | ENUM (user/assistant) | No | Who sent this message |
| content | TEXT | No | Raw message text content |
| message_hash | VARCHAR(64) | No | SHA-256 of session_id + content for dedup |
| tokens_used | INTEGER | Yes | LLM tokens consumed for this turn |
| created_at | TIMESTAMPTZ | No | Message timestamp (auto-set) |
| Idempotency GuaranteeA unique index on messages(session_id, message_hash) prevents duplicate records. If a POST /webhook arrives with the same session and content, the endpoint returns the cached assistant reply without invoking the LLM — safe for network retries and at-least-once delivery guarantees. |
| --- |

# 5\. API Specification

## 5.1 POST /webhook — Receive User Message

Accepts an incoming user message. Persists it, calls the LLM, extracts lead fields, updates lead priority, and returns a structured response. This is the primary entry point for all chatbot interactions.

### Request Body

| Field | Type | Description |
| --- | --- | --- |
| session_id | string (required) | Unique identifier for the conversation session |
| message | string (required) | Raw user message content |
| metadata | object (optional) | Optional context: UTM source, channel, IP, etc. |

### Response Body

| Field | Type | Description |
| --- | --- | --- |
| session_id | string | Echo of the incoming session_id |
| reply | string | AI-generated assistant response shown to the user |
| lead_extracted | boolean | True if new lead fields were parsed this turn |
| lead_priority | string | null | high / medium / low / pending |
| tokens_used | integer | Total LLM tokens consumed for this exchange |
| cached | boolean | True if this response was served from dedup cache |

## 5.2 GET /reply/{session\_id} — Conversation History

Returns the complete ordered message history (user + assistant turns) for a given session, with timestamps and token counts.

## 5.3 GET /leads — Lead Listing

Returns a paginated, filterable list of all captured leads.

| Query Parameter | Type | Description |
| --- | --- | --- |
| priority | string (optional) | Filter by high | medium | low | pending |
| limit | integer (default: 20) | Page size — maximum 100 results per page |
| offset | integer (default: 0) | Pagination offset for cursor-based paging |

## 5.4 GET /health — Liveness Probe

Returns system health status including database connectivity and Groq API reachability. Used by load balancers, container orchestrators, and monitoring systems. Responds with HTTP 200 when healthy, HTTP 503 on partial or full degradation.

# 6\. AI Chatbot Design

## 6.1 LLM Integration — Groq

The ChatService wraps the Groq Python client (OpenAI-compatible SDK). Model: llama3-70b-8192 — chosen for its balance of response quality and ultra-low inference latency (typically under 300 ms). The service is fully async and uses httpx under the hood.

## 6.2 System Prompt Architecture

The system prompt is composed of three explicit layers:

*   Persona Layer: Defines the bot as a friendly, professional property advisor named Alex.
*   Extraction Layer: Instructs the model to naturally elicit name, budget, location preference, and timeline — one question at a time, never overwhelming the user.
*   Format Layer: Instructs the model to embed a structured JSON extraction block inside an HTML comment (<!-- LEAD\_DATA: {} -->) at the end of every response. This block is stripped server-side before the reply is shown to the user.

| Prompt Engineering NoteThe hidden JSON block decouples structured data extraction from the conversational reply. The model writes natural prose for the user while simultaneously outputting machine-readable fields for the extraction service — no separate extraction API call required. This halves LLM cost and latency. |
| --- |

## 6.3 Conversation Context Management

Full conversation history is loaded from the Messages table for each session and passed to the LLM as a structured message array (role: user / assistant). The service is fully stateless — no in-memory session state — enabling horizontal scaling without sticky sessions.

*   Context window: last N messages (default: 20, configurable via MAX\_CONTEXT\_MESSAGES).
*   Token tracking: cumulative token count stored per message for cost monitoring.
*   Streaming: optional SSE (Server-Sent Events) endpoint for token-by-token streaming to frontend clients.

## 6.4 Sample Conversation Flow

| Role | Message |
| --- | --- |
| Bot | Hi there! I'm Alex, your property advisor. May I start with your name? |
| User | Hi, I'm Priya |
| Bot | Great to meet you, Priya! Are you looking to buy or rent, and which areas are you considering? |
| User | Buying — South Delhi or Gurgaon |
| Bot | Excellent choices! What is your approximate budget for this purchase? |
| User | Around 80 lakhs |
| Bot | Perfect. And what is your target timeline — are you hoping to move within a few months? |
| User | Within 2 months ideally |
| System | Hidden extraction: { name: 'Priya', budget: 8000000, preference: 'South Delhi / Gurgaon', timeline_months: 2 } -> SCORE: HIGH |

# 7\. Lead Extraction Service

## 7.1 Extraction Strategy

The ExtractionService uses a two-pass approach. Primary: parse the structured JSON block embedded by the LLM in every response. Fallback: if the JSON block is missing or malformed, a regex-based parser scans the raw conversation text for recognisable patterns.

Extraction is incremental and additive: fields are merged (never overwritten) across conversation turns using an upsert pattern. A field once extracted is preserved even if subsequent turns do not mention it.

## 7.2 Field Parsing Rules

| Field | Expected Format | Parsing Notes |
| --- | --- | --- |
| name | String | First clearly stated name; ignores generic greetings like 'Hi' or 'Hello' |
| budget | Float (INR) | Parses '80L', '80 lakhs', '80,00,000', '8000000' -> 8000000.0 |
| preference | String | Location or property type; concatenated if multiple mentioned |
| timeline_months | Integer | Parses '2 months', 'next quarter' (->3), 'ASAP' (->1), '6 months' (->6) |

# 8\. Lead Scoring Engine

## 8.1 Scoring Rules

The ScoringService implements a deterministic, rule-based engine. Rules are evaluated in priority order and short-circuit on first match. Thresholds are loaded from config (env vars), not hardcoded — allowing non-developer updates.

| Priority | Condition | Example | Score |
| --- | --- | --- | --- |
| HIGH | Budget >= 70L AND timeline <= 3 months | 80L budget, move in 2 months | 100 |
| HIGH | Budget >= 1Cr (any timeline) | 1Cr+ buyer, flexible on date | 90 |
| MEDIUM | Budget >= 30L AND timeline <= 6 months | 35L, within 5 months | 60 |
| MEDIUM | Budget >= 70L AND timeline > 3 months | 80L but 8 months away | 50 |
| LOW | All other combinations | Budget < 30L or timeline > 6 months | 20 |
| PENDING | Insufficient data extracted yet | Only name captured so far | 0 |
| ExtensibilityScoring rules are stored in a Python dict (or optional YAML file) loaded at startup. Changing thresholds requires no code change — only a config update and service restart. Future iterations can replace this with a trained ML classifier. |
| --- |

# 9\. Follow-Up Logic

## 9.1 Inactivity Detection

A background APScheduler job runs every 15 minutes. It queries the Messages table for sessions where the last user message timestamp is older than FOLLOW\_UP\_INACTIVITY\_MINUTES (default: 30) and where follow\_up\_count is below FOLLOW\_UP\_MAX\_COUNT (default: 3) and no follow-up was sent in the last 24 hours.

## 9.2 Follow-Up Message Templates

*   Standard nudge (Turn 1): "Hi \[Name\], just checking in — are you still exploring properties? I'm happy to help!"
*   High-priority nudge (Turn 1, high score): "Hi \[Name\], given your \[X\]-month timeline, I have some great options in \[Location\] that could be a perfect fit. Shall we continue?"
*   Second nudge (Turn 2, 24h later): "Hi \[Name\], just a friendly reminder — great properties in \[Location\] are moving quickly at your budget level. Happy to share some options!"
*   Final nudge (Turn 3, 48h later): "This will be our last check-in, \[Name\]. Feel free to reach out any time — we'd love to help you find your ideal property."

## 9.3 Follow-Up Business Rules

*   Maximum 3 follow-up messages per lead session — enforced via follow\_up\_count column.
*   Follow-ups are personalised using extracted fields where available; generic fallback used otherwise.
*   Every follow-up message is stored in Messages table with role: assistant for full audit trail.
*   Race condition guard: if the user replies between the scheduler scan and the dispatch, the follow-up is cancelled for that cycle.
*   follow\_up\_sent\_at and follow\_up\_count on the Lead record are updated atomically after dispatch.

# 10\. Services Layer Design

## 10.1 Service Responsibilities

| Service | Responsibilities |
| --- | --- |
| ChatService | Build message history array, call Groq API async, return raw LLM text + token count |
| ExtractionService | Parse LLM output JSON block; regex fallback; return typed LeadFields dataclass |
| LeadService | Upsert Lead record, trigger ScoringService, expose lead CRUD operations |
| MessageService | Persist user + assistant messages; SHA-256 hash idempotency check |
| ScoringService | Evaluate priority rules against LeadFields; return Priority enum |
| FollowUpService | Query inactive leads, render personalised template, persist and dispatch nudge |

## 10.2 Design Principles

*   Idempotency: All write operations are safe to retry. DB upserts use INSERT ... ON CONFLICT DO UPDATE. Message deduplication via SHA-256 hash on (session\_id, content).
*   Single Responsibility: Each service has one clearly defined job. No service calls another service directly — coordination happens in the API layer or task runner.
*   Async-First: All database operations use async SQLAlchemy sessions. All outbound HTTP calls use httpx.AsyncClient with configured timeouts.
*   Dependency Injection: Services are injected into API handlers via FastAPI's Depends() pattern for clean testability and mock-ability in unit tests.
*   DRY Utilities: Pagination helpers, error envelope builders, and async session context managers are extracted into app/utils.py — shared across all services.
*   Refactored Prompts: LLM system prompt is maintained in a dedicated app/prompts.py module with version comments — not embedded in service code.

# 11\. Streamlit Dashboard

## 11.1 Dashboard Widgets

| Widget | Description |
| --- | --- |
| KPI Cards — Row 1 | Total Leads | High Priority | Average Budget | Active Sessions Today |
| Priority Distribution | Donut chart: High vs Medium vs Low vs Pending leads |
| Lead Capture Timeline | Line chart: number of leads captured per day over the last 30 days |
| Leads Data Table | Sortable, filterable table: name, budget, location, timeline, priority, created_at |
| Conversation Viewer | Session selector dropdown -> full chronological chat history for that session |
| Follow-Up Queue | Table of leads eligible for follow-up with last activity timestamp |
| Auto-Refresh | st.rerun() on a configurable timer — default every 30 seconds |

# 12\. Configuration & Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| GROQ_API_KEY | (required) | Groq API authentication key |
| GROQ_MODEL | llama3-70b-8192 | Groq model identifier string |
| DATABASE_URL | (required) | PostgreSQL async DSN — asyncpg driver |
| FOLLOW_UP_INACTIVITY_MINUTES | 30 | Inactivity threshold before follow-up triggers |
| FOLLOW_UP_MAX_COUNT | 3 | Maximum follow-up messages per session |
| MAX_CONTEXT_MESSAGES | 20 | Sliding context window sent to LLM |
| HIGH_PRIORITY_BUDGET_INR | 7000000 | Budget threshold for HIGH priority (70 lakhs) |
| HIGH_PRIORITY_TIMELINE_MONTHS | 3 | Timeline threshold for HIGH priority |
| API_RATE_LIMIT_PER_MIN | 60 | Per-IP rate limit on /webhook endpoint |
| LOG_LEVEL | INFO | Application log level — DEBUG / INFO / WARNING |
| CORS_ORIGINS | * | Allowed CORS origins, comma-separated |

# 13\. Error Handling & Resilience

## 13.1 Consistent Error Response Format

All API errors return a standard JSON envelope: { error: string, detail: string, request\_id: UUID }. HTTP status codes are used semantically — 400 for bad input, 422 for schema validation failure, 429 for rate limit exceeded, 503 for LLM or database unavailability.

## 13.2 Resilience Patterns

*   Groq API Retry: Exponential backoff with random jitter on 429 and 5xx responses — maximum 3 retries, 10-second hard timeout per attempt.
*   Graceful Degradation: If Groq is unavailable, /webhook returns a friendly holding message and marks the session for LLM reprocessing on next user message.
*   Database Connection Pool: SQLAlchemy async pool — minimum 5, maximum 20 connections. Connection wait timeout set to 5 seconds before raising a 503.
*   Request Tracing: Every request receives a unique request\_id (UUID) injected into headers and logs for end-to-end traceability.
*   Structured Logging: JSON-formatted logs with level, timestamp, request\_id, session\_id, and latency\_ms fields — no raw user message content in production logs.

# 14\. Testing Strategy

| Test Type | Tooling | Coverage Scope |
| --- | --- | --- |
| Unit Tests | pytest + pytest-asyncio | Services layer: scoring logic, extraction parsing, follow-up eligibility |
| Integration Tests | httpx.AsyncClient | All API endpoints against in-memory SQLite test database |
| Mock LLM Tests | pytest monkeypatch | Groq calls mocked with fixture responses for deterministic extraction tests |
| Idempotency Tests | pytest parametrize | Duplicate /webhook POSTs must not create duplicate DB records |
| Scoring Tests | pytest parametrize | All priority combinations verified with boundary value fixtures |
| Follow-Up Tests | pytest + freezegun | Inactivity window logic verified by freezing system time |

# 15\. Day-by-Day Delivery Plan

## Day 1 — Foundation

*   Project scaffold: folder structure, virtual environment, requirements.txt
*   SQLAlchemy models (Lead, Message) + Alembic migration scripts
*   Pydantic v2 schemas + app/config.py with BaseSettings
*   Async database connection + GET /health endpoint
*   Docker Compose: app + postgres services

## Day 2 — Core Chat Loop

*   Groq client integration in ChatService (async, with retry logic)
*   POST /webhook: persist user message, call LLM, store assistant reply
*   SHA-256 idempotency hash on message write
*   GET /reply/{session\_id}: full conversation history endpoint

## Day 3 — Intelligence Layer

*   System prompt with three-layer architecture (persona + extraction + format)
*   ExtractionService: JSON block parser + regex fallback
*   ScoringService: configurable rule engine returning Priority enum
*   LeadService: upsert + score write-back to leads table

## Day 4 — Automation & Dashboard

*   APScheduler setup with 15-minute follow-up scan job
*   FollowUpService: inactivity detection, template rendering, dispatch + guard
*   Streamlit dashboard: KPI cards, charts, leads table, conversation viewer
*   GET /leads endpoint with pagination and priority filter

## Day 5 — Polish & Delivery

*   Full pytest suite — unit + integration — targeting > 80% coverage
*   requirements.txt pinned with pip-compile for reproducible builds
*   README: architecture overview, local setup guide, sample .env, API examples
*   Sample conversation transcripts documenting lead extraction + scoring
*   Demo video walkthrough recording

# 16\. Risks & Mitigations

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Groq API rate limits hit under load | Medium | Token-bucket rate limiter + exponential retry with jitter |
| LLM extraction inconsistency across models | Medium | Structured JSON prompt layer + regex fallback + extraction unit tests |
| Follow-up double-send race condition | Low | DB-level follow_up_count guard checked in atomic UPDATE transaction |
| Database connection pool exhaustion | Low | Configured pool max + overflow wait timeout + /health probe alert |
| LLM context window overflow on long chats | Low | Sliding window capped at MAX_CONTEXT_MESSAGES — oldest turns dropped |
| PII leakage via application logs | Medium | Message content masked in INFO logs; only session_id and metadata logged |

# 17\. Future Enhancements

*   WebSocket endpoint for real-time bidirectional chat — replace request/response polling.
*   Multi-channel ingestion: WhatsApp, email, and web widget via a unified webhook adapter pattern.
*   ML-based lead scoring model trained on historical lead outcome data — replacing the rule engine.
*   CRM integration: automatically create or update records in Salesforce or HubSpot on lead qualification.
*   Voice input support: Whisper ASR transcription pipeline feeding into the existing chat flow.
*   Multi-language support: automatic language detection with in-language LLM responses.
*   A/B testing framework for chatbot persona variants and question ordering experiments.
*   Admin API: manual lead status overrides, bulk export (CSV/Excel), and priority re-scoring triggers.

AI Lead Capture Chatbot | PRD v1.0 | March 2026

**FastAPI • Groq LLM • PostgreSQL • Streamlit**