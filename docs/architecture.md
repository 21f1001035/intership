# IIT Ropar Screening Bot — Architecture

## Overview

The IIT Ropar Screening Bot is an automated internship screening system designed to conduct structured, deterministic AI-driven interviews with student applicants. Administrators upload a resume for a candidate, the system parses it, and then presents the student with a series of thematic questions via a web-based chat interface. Once the interview is complete, a scoring and recommendation engine evaluates the transcript and provides a shortlisting recommendation to the admin panel.

The system is intentionally scoped: it is not a general-purpose chatbot. Every interview follows a bounded state machine with hard limits on turns and follow-up questions. The LLM is used as a tool for language generation and scoring — never as a free-form autonomous agent.

---

## System Architecture Diagram (ASCII)

```
                         ┌─────────────────────────────────────────────────────┐
                         │                    BROWSER                          │
                         │   Student Portal (Vue 3)  │  Admin Dashboard (Vue 3)│
                         └────────────────┬────────────────────────────────────┘
                                          │ HTTP / HTTPS
                                          ▼
                         ┌────────────────────────────┐
                         │         NGINX              │
                         │  (Reverse Proxy / TLS)     │
                         └────────┬───────────────────┘
                                  │
                  ┌───────────────┴──────────────────┐
                  ▼                                  ▼
   ┌──────────────────────────┐      ┌───────────────────────────┐
   │   FastAPI Backend        │      │   Vue 3 Frontend (static) │
   │   (Python 3.11)          │      │   served from nginx:80    │
   │                          │      └───────────────────────────┘
   │  ┌────────────────────┐  │
   │  │  Interview Engine  │  │
   │  │  (Orchestrator)    │  │
   │  └────────┬───────────┘  │
   │           │              │
   │  ┌────────▼───────────┐  │         ┌──────────────────────┐
   │  │  LLM Provider      │◄─┼─────────►   OpenAI API (gpt-4o)│
   │  │  Abstraction Layer │  │         └──────────────────────┘
   │  └────────────────────┘  │
   │                          │
   │  ┌────────────────────┐  │         ┌──────────────────────┐
   │  │  Resume Parser     │  │         │   Celery Workers     │
   │  │  (pdfplumber)      │  │         │   (async tasks)      │
   │  └────────────────────┘  │         └──────────┬───────────┘
   │                          │                    │
   │  ┌────────────────────┐  │         ┌──────────▼───────────┐
   │  │  Scoring Engine    │  │         │   Redis (broker +    │
   │  └────────────────────┘  │         │   result backend)    │
   │                          │         └──────────────────────┘
   │  ┌────────────────────┐  │
   │  │  Recommendation    │  │         ┌──────────────────────┐
   │  │  Engine            │  │         │  PostgreSQL 16        │
   │  └────────────────────┘  ├────────►│  (primary data store)│
   └──────────────────────────┘         └──────────────────────┘
```

---

## Core Design Principles

### 1. Deterministic Orchestration
The application layer owns all interview state and flow logic. The LLM is invoked as a pure generation tool: it receives a carefully constructed prompt and returns text. It never decides which question to ask next, when to end the interview, or how many follow-ups to allow. All of those decisions are made by the Python orchestrator based on explicit rules.

### 2. Full Auditability
Every message sent to and received from the LLM is stored in the database. Every score, every recommendation, and every state transition is logged with a timestamp and (where applicable) a rationale. An admin can replay the full history of any interview.

### 3. Provider Abstraction
The LLM integration is hidden behind a `BaseLLMProvider` abstract class. The system ships with an `OpenAIProvider` implementation. Swapping to Anthropic Claude or a local model requires implementing three methods — no changes to the orchestrator.

### 4. Storage Abstraction
Resume files are handled through a `BaseStorageBackend` abstract class. The default implementation writes to the local filesystem. A `DigitalOceanSpacesBackend` can be dropped in by changing one environment variable.

### 5. Bounded Interview Engine
The engine enforces hard limits: a maximum number of total turns (`INTERVIEW_MAX_TURNS`, default 12) and a maximum number of follow-up questions per theme (`INTERVIEW_MAX_FOLLOWUPS_PER_THEME`, default 2). This prevents runaway LLM usage and ensures consistent candidate experience.

---

## Component Breakdown

### Frontend (Vue 3)
- Built with Vue 3 Composition API and TypeScript.
- Pinia for state management.
- Two distinct views: the **Student Portal** (accessed via a unique application token link) and the **Admin Dashboard** (protected by JWT login).
- The student portal is a simple chat interface. On page load it fetches the current interview state and renders the transcript so far, allowing a student to resume a session.
- The admin dashboard provides application listing, filtering by status, resume viewing, full transcript review, score breakdowns, and manual status override.

### Backend API (FastAPI)
- Python 3.11, async throughout.
- SQLAlchemy 2.x with async engine for all database operations.
- Alembic for schema migrations.
- Pydantic v2 for request/response validation and settings management.
- Structured JSON logging.
- All routes prefixed under `/api/v1/`.

### Interview Orchestrator
The central piece of backend logic (`app/services/interview_engine.py`). It:
1. Reads the current `Interview` record and its `Message` history from the database.
2. Determines which theme is active and how many turns remain.
3. Constructs the full prompt context (system prompt + resume summary + message history).
4. Calls the LLM provider.
5. Persists the new assistant message.
6. Evaluates whether to continue, ask a follow-up, advance to the next theme, or close the interview.
7. Updates the `Interview` status accordingly.

### LLM Provider Abstraction
`app/services/llm/base.py` defines `BaseLLMProvider` with three abstract methods:
- `chat_completion(messages, system_prompt) -> str` — single turn, returns text.
- `structured_output(messages, schema) -> dict` — forces JSON output matching a Pydantic schema (used for scoring).
- `estimate_tokens(text) -> int` — for cost tracking.

`app/services/llm/openai_provider.py` implements these using the `openai` Python SDK with `gpt-4o` by default.

### Resume Parser
`app/services/resume_parser.py` uses `pdfplumber` to extract text from uploaded PDFs. The raw text is then passed to the LLM via a structured prompt to produce a normalised summary dict (skills, projects, education, work experience). This summary is stored on the `Application` record and used in all subsequent interview prompts.

### Scoring Engine
`app/services/scoring.py` is invoked once the interview reaches the `completed` state. It sends the full transcript and resume summary to the LLM and requests a structured JSON score across predefined dimensions (technical depth, communication, relevant experience, problem-solving). Each dimension is scored 1–10 with a brief rationale. Scores are stored in a `Score` record linked to the interview.

### Recommendation Engine
`app/services/recommendation.py` applies a deterministic rule set on top of the scores. Weighted averages are computed; if the result exceeds the `SHORTLIST_THRESHOLD` the status becomes `shortlisted`, if it is below `REJECT_THRESHOLD` it becomes `rejected`, otherwise `hold`. Edge cases (very short interviews, parser errors) are flagged as `needs_review`. Admins can override any status at any time.

### Celery Workers
Long-running tasks (resume parsing + LLM summarisation at upload time, and post-interview scoring) are dispatched as Celery tasks and processed asynchronously. Redis serves as both the broker and result backend. This keeps all API endpoints fast and prevents HTTP timeouts on LLM calls.

### PostgreSQL Schema Overview
Key tables:
- `applications` — applicant metadata, resume file path, resume summary JSON, current status.
- `interviews` — one per application, tracks state, turn count, active theme index, timestamps.
- `messages` — ordered list of `{role, content, timestamp}` records belonging to an interview.
- `scores` — dimension scores and rationale JSON, linked to an interview.
- `admins` — admin accounts with bcrypt-hashed passwords.

### Redis Usage
- Celery broker: task queue for background jobs.
- Celery result backend: stores task results for status polling.
- (Optional future use) rate limiting per application token.

---

## Interview State Machine

```
                     ┌──────────┐
             upload  │          │
         ────────────► received │
                     │          │
                     └────┬─────┘
                          │ student opens link
                          ▼
              ┌───────────────────────┐
              │  interview_in_progress│
              └───────────┬───────────┘
                          │ max turns reached OR
                          │ all themes exhausted
                          ▼
                    ┌──────────┐
                    │completed │
                    └────┬─────┘
                         │ scoring engine runs
                         ▼
          ┌──────────────────────────────────┐
          │                                  │
     ┌────▼──────┐  ┌──────┐  ┌──────────┐  ┌──────────────┐
     │shortlisted│  │ hold │  │ rejected │  │ needs_review │
     └───────────┘  └──────┘  └──────────┘  └──────────────┘
          ▲              ▲          ▲               ▲
          └──────────────┴──────────┴───────────────┘
                    admin can override to any terminal state
```

Valid transitions:
- `received` → `interview_in_progress` (on first student message)
- `interview_in_progress` → `completed` (engine closes interview)
- `completed` → `shortlisted | hold | rejected | needs_review` (scoring engine)
- Any state → any terminal state (admin override)

---

## Interview Engine Flow

1. Student loads the chat page with their unique `application_token`.
2. The backend authenticates the token and loads (or creates) the `Interview` record.
3. If `status == received`, the engine generates a personalised opening message and transitions to `interview_in_progress`.
4. For each student message:
   a. The message is persisted to `messages`.
   b. The engine checks: has the turn limit been reached? If yes, generate a closing message and set `status = completed`, dispatch scoring task, return.
   c. Otherwise, determine the active theme and follow-up count.
   d. If the current theme has exhausted its follow-up budget, advance `active_theme_index`.
   e. If all themes are exhausted, close the interview.
   f. Construct the full prompt and call `llm_provider.chat_completion()`.
   g. Persist the assistant message.
   h. Return the assistant message to the frontend.
5. The Celery scoring task calls `scoring.py` then `recommendation.py` and updates the `Application` status.

---

## LLM Integration

The application uses the `openai` Python SDK directly. LangChain is intentionally not used — it adds significant complexity, hidden prompts, and makes debugging harder. Every prompt sent to the LLM is a hand-authored Python string visible in the source code.

The `OpenAIProvider` class:
- Uses `AsyncOpenAI` for non-blocking I/O.
- `chat_completion` calls `client.chat.completions.create()` with `model`, `messages`, and `temperature=0.7`.
- `structured_output` passes `response_format={"type": "json_object"}` and includes the target JSON schema in the system prompt. The response is parsed with `json.loads()` and validated against the Pydantic model.
- All calls are wrapped in try/except blocks; errors are logged and re-raised as `LLMProviderError` so the orchestrator can handle them gracefully (e.g., retry once, then mark the interview `needs_review`).

To add an Anthropic Claude provider:
1. Create `app/services/llm/anthropic_provider.py` implementing `BaseLLMProvider`.
2. Set `LLM_PROVIDER=anthropic` in `.env`.
3. The factory in `app/services/llm/__init__.py` instantiates the correct class.

---

## API Design

All routes are under `/api/v1/`. Authentication is via `Authorization: Bearer <token>` where the token is either an `application_token` (students) or a JWT (admins).

### Student Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/interview/{token}` | Load interview state and transcript |
| POST | `/interview/{token}/message` | Submit a student message, receive AI reply |

### Admin Routes
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Admin login, returns JWT |
| GET | `/applications` | List all applications (paginated, filterable) |
| POST | `/applications` | Create a new application + upload resume |
| GET | `/applications/{id}` | Full application detail with scores |
| PATCH | `/applications/{id}/status` | Override application status |
| GET | `/applications/{id}/transcript` | Full message transcript |
| DELETE | `/applications/{id}` | Delete an application |

### System Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (returns DB and Redis status) |

---

## Security Model

### Student Authentication
Each application is assigned a cryptographically random `application_token` (UUID4 or secrets.token_urlsafe). This token is the only credential the student needs. It is delivered out-of-band (e.g., via email by the admin). There is no student registration or password.

### Admin Authentication
Admins log in with email + password. Passwords are hashed with `bcrypt` (passlib). On successful login a short-lived JWT (1 hour, HS256) is returned. All admin API routes are protected by a FastAPI dependency that validates the JWT.

### Password Hashing
`passlib[bcrypt]` with a work factor of 12. Passwords are never stored in plaintext and never returned in API responses.

### CORS Configuration
The `CORS_ORIGINS` environment variable accepts a JSON array of allowed origins. In production this must be set to exactly the frontend domain. In development `["http://localhost:5173"]` is the default.

### Input Validation
All request bodies are validated by Pydantic v2 models. File uploads are restricted to `application/pdf` MIME type and a configurable maximum size (default 10 MB).

---

## Deployment

### Development (Docker Compose)
`docker-compose.yml` brings up six services: `db` (Postgres 16), `redis` (Redis 7), `backend` (FastAPI with hot reload), `worker` (Celery), and `frontend` (Vite dev server). Health checks ensure the backend and worker do not start before the database is ready.

### Production (DigitalOcean Droplet)
`docker-compose.prod.yml` is the production configuration. Key differences from development:
- No source-code volume mounts; images are built and deployed.
- Backend runs with `--workers 2` (Uvicorn multi-process).
- Celery runs with `--concurrency=2`.
- All secrets come from `.env.prod` (never committed to source control).
- An `nginx` service sits in front, handling TLS termination (via Let's Encrypt certificates placed at `infra/nginx/ssl/`), HTTP→HTTPS redirect, static file caching, gzip compression, and security headers.
- All services have `restart: unless-stopped`.

### SSL / TLS
Certificates are managed with Certbot outside the Docker Compose stack and mounted read-only into the nginx container at `infra/nginx/ssl/`. Renewal is handled by a host-level cron job running `certbot renew`.

---

## Future Extensions

- **Email Integration**: Use SendGrid or SMTP to automatically deliver the application token link to candidates on application creation. A Celery task handles delivery.
- **DigitalOcean Spaces Storage**: Implement `DOSpacesStorageBackend` and set `STORAGE_BACKEND=do_spaces`. Resumes are stored in object storage instead of the local filesystem, making the backend stateless and horizontally scalable.
- **Anthropic Claude Provider**: Implement `AnthropicProvider` as described in the LLM Integration section. Useful for cost comparison or when GPT-4o is unavailable.
- **WebSocket Chat**: Replace the polling-based chat with a WebSocket connection for a more responsive student experience. FastAPI natively supports WebSockets.
- **Multi-track Support**: Add a `track` field to `Application` (e.g., "ML", "Backend", "Frontend"). Each track has its own set of interview themes and scoring rubric, loaded from a YAML config file.
- **Bulk Import**: Allow admins to upload a CSV of applicant details to create applications in bulk, with Celery handling the resume download and parsing.
