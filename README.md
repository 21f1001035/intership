# IIT Ropar Internship Screening Bot

## Overview

The IIT Ropar Internship Screening Bot automates the first-round screening of internship applicants. An administrator uploads a candidate's resume; the system parses it with an LLM and conducts a structured, thematic interview through a web chat interface. Once the interview concludes, a scoring and recommendation engine produces a shortlisting decision that the admin can review, override, and act on.

The system is designed for the IIT Ropar research internship programme but is straightforwardly adaptable to any institution or company running high-volume screening rounds.

---

## Features

- **Automated resume parsing** — PDFs are parsed with `pdfplumber` and summarised by GPT-4o into structured skill/experience profiles.
- **Deterministic interview orchestration** — the application controls all state and flow; the LLM is a generation tool, not an autonomous agent.
- **Thematic questioning** — interviews are divided into configurable themes (e.g., technical background, project experience, motivation). Hard limits on turns and follow-ups per theme ensure consistency.
- **Full transcript storage** — every message is persisted; interviews can be resumed after disconnection.
- **Automated scoring** — GPT-4o scores transcripts across multiple dimensions with rationale; a rule-based engine maps scores to a recommendation.
- **Admin dashboard** — list, filter, and review applications; read full transcripts; view score breakdowns; override recommendations.
- **Unique token-based student access** — no registration required; students access their interview via a secure link.
- **Background task processing** — Celery + Redis handles resume parsing and scoring asynchronously.
- **Provider abstraction** — swap the LLM backend (OpenAI → Anthropic → local) by implementing one class.
- **Storage abstraction** — swap file storage (local → DigitalOcean Spaces) via an environment variable.
- **Docker-first** — full development and production stacks defined with Docker Compose.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3, TypeScript, Pinia, Vite |
| Backend API | FastAPI (Python 3.11), Uvicorn |
| ORM | SQLAlchemy 2.x (async) + Alembic |
| Task Queue | Celery 5 |
| Message Broker | Redis 7 |
| Database | PostgreSQL 16 |
| LLM | OpenAI GPT-4o (via `openai` SDK) |
| PDF Parsing | pdfplumber |
| Auth | JWT (admins), application token (students), passlib/bcrypt |
| Containerisation | Docker, Docker Compose |
| Reverse Proxy | Nginx (Alpine) |
| TLS | Let's Encrypt / Certbot |
| Hosting (prod) | DigitalOcean Droplet (Ubuntu 22.04) |

---

## Quick Start (Local Development)

### Prerequisites

- Docker Desktop (includes Docker Compose v2)
- Node.js 20+ (only needed if developing the frontend outside Docker)
- Python 3.11+ (only needed if developing the backend outside Docker)
- An OpenAI API key

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/iit-ropar-screening-bot.git
cd iit-ropar-screening-bot
cp backend/.env.example backend/.env
# Open backend/.env and set OPENAI_API_KEY=sk-...
```

### 2. Start with Docker Compose

```bash
docker-compose up --build
```

All five services (Postgres, Redis, backend, Celery worker, frontend) will start. The first build takes 2–4 minutes. Subsequent starts are fast.

### 3. Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Seed Admin User

```bash
docker-compose exec backend python -m scripts.seed_admin
```

This creates the initial admin account using `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `backend/.env`.

### 5. Access the App

| Service | URL |
|---|---|
| Student portal | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Interactive API docs (Swagger) | http://localhost:8000/docs |
| ReDoc API docs | http://localhost:8000/redoc |

---

## Development Without Docker

If you prefer to run services natively (e.g., for faster iteration with a debugger), you will need Postgres and Redis running locally.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set DATABASE_URL, REDIS_URL, OPENAI_API_KEY
alembic upgrade head
python -m scripts.seed_admin
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000.

To run the Celery worker in a separate terminal:

```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000/api in .env
npm run dev
```

The frontend will be available at http://localhost:5173.

---

## Production Deployment (DigitalOcean Droplet)

### Server Setup

Provision a fresh Ubuntu 22.04 droplet (4 GB RAM minimum recommended). SSH in as root or a sudo user.

```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin
systemctl enable docker
systemctl start docker
```

### Deploy

```bash
git clone https://github.com/your-org/iit-ropar-screening-bot.git /opt/iit-screening
cd /opt/iit-screening
cp .env.prod.example .env.prod
# Edit .env.prod — set all CHANGE_THIS_* values and your real domain
```

Start all services:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Run migrations and seed the admin:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec backend python -m scripts.seed_admin
```

### SSL / TLS Setup

1. Point your domain's A record to the droplet's IP.
2. Install Certbot on the host:
   ```bash
   apt install -y certbot
   ```
3. Obtain a certificate (ensure port 80 is open and the nginx container is running):
   ```bash
   certbot certonly --webroot -w /opt/iit-screening/infra/certbot/www \
       -d your-domain.com --email admin@your-domain.com --agree-tos
   ```
4. Copy the certificates to the location the nginx container expects:
   ```bash
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem \
       /opt/iit-screening/infra/nginx/ssl/fullchain.pem
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem \
       /opt/iit-screening/infra/nginx/ssl/privkey.pem
   ```
5. Update `server_name your-domain.com` in `infra/nginx/nginx.prod.conf`.
6. Restart nginx: `docker compose -f docker-compose.prod.yml restart nginx`

Add a cron job for renewal:

```bash
0 3 * * * certbot renew --quiet && \
    cp /etc/letsencrypt/live/your-domain.com/fullchain.pem \
       /opt/iit-screening/infra/nginx/ssl/fullchain.pem && \
    cp /etc/letsencrypt/live/your-domain.com/privkey.pem \
       /opt/iit-screening/infra/nginx/ssl/privkey.pem && \
    docker compose -f /opt/iit-screening/docker-compose.prod.yml restart nginx
```

---

## Environment Variables

### Backend (`backend/.env` / `.env.prod`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `REDIS_URL` | Yes | — | Redis connection string |
| `SECRET_KEY` | Yes | — | 64-char random string for JWT signing |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | OpenAI model name |
| `STORAGE_BACKEND` | No | `local` | `local` or `do_spaces` |
| `LOCAL_STORAGE_PATH` | No | `/app/uploads` | Path for local file storage |
| `ADMIN_EMAIL` | Yes | — | Initial admin email (seed script) |
| `ADMIN_PASSWORD` | Yes | — | Initial admin password (seed script) |
| `CORS_ORIGINS` | No | `["http://localhost:5173"]` | JSON array of allowed CORS origins |
| `APP_ENV` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | Python log level |
| `INTERVIEW_MAX_TURNS` | No | `12` | Hard limit on total interview turns |
| `INTERVIEW_MAX_FOLLOWUPS_PER_THEME` | No | `2` | Max follow-up questions per theme |

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_URL` | No | `http://localhost:8000/api` | Backend API base URL |

---

## API Documentation

The API is self-documented. When the backend is running, visit:

- **Swagger UI** — http://localhost:8000/docs (interactive, supports authentication)
- **ReDoc** — http://localhost:8000/redoc (clean reference format)

All endpoints are under `/api/v1/`. Student endpoints authenticate via the `application_token` query parameter or `Authorization: Bearer <token>` header. Admin endpoints require a JWT obtained from `POST /api/v1/auth/login`.

---

## Interview Flow

1. Admin creates an application and uploads the candidate's resume PDF.
2. The system parses the resume in the background and generates a structured profile.
3. Admin shares the unique student portal link (containing the `application_token`) with the candidate.
4. The candidate opens the link and is greeted by a personalised opening message.
5. The interview proceeds through a series of thematic questions (technical background, project experience, motivation, etc.). Each theme allows a limited number of follow-up questions.
6. When the turn limit is reached or all themes are exhausted, the engine sends a closing message and marks the interview as `completed`.
7. The scoring engine runs asynchronously: it sends the full transcript to GPT-4o and requests structured scores, then applies a rule-based algorithm to produce a recommendation (`shortlisted`, `hold`, `rejected`, or `needs_review`).
8. The admin sees the recommendation in the dashboard and can accept it or override it.

---

## Admin Dashboard

Access the admin dashboard at `http://localhost:5173/admin` (development) or `https://your-domain.com/admin` (production).

Log in with the credentials set in `ADMIN_EMAIL` and `ADMIN_PASSWORD`.

**Dashboard capabilities:**
- View all applications with status badges and last-activity timestamps.
- Filter by status (`received`, `interview_in_progress`, `completed`, `shortlisted`, `hold`, `rejected`, `needs_review`).
- Open any application to view the full resume summary, interview transcript, dimension scores with rationale, and the recommendation.
- Override the status to any value with a free-text note.
- Download the original resume PDF.
- Delete an application (permanent).

---

## Project Structure

```
iit-ropar-screening-bot/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app factory, middleware, router registration
│   │   ├── config.py           # Pydantic settings (reads from .env)
│   │   ├── database.py         # SQLAlchemy async engine and session factory
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── application.py
│   │   │   ├── interview.py
│   │   │   ├── message.py
│   │   │   ├── score.py
│   │   │   └── admin.py
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── routers/            # FastAPI route handlers
│   │   │   ├── auth.py
│   │   │   ├── applications.py
│   │   │   └── interview.py
│   │   ├── services/           # Business logic
│   │   │   ├── interview_engine.py   # Core orchestrator
│   │   │   ├── resume_parser.py
│   │   │   ├── scoring.py
│   │   │   ├── recommendation.py
│   │   │   └── llm/
│   │   │       ├── base.py           # Abstract LLM provider
│   │   │       ├── openai_provider.py
│   │   │       └── __init__.py       # Provider factory
│   │   ├── workers/
│   │   │   ├── celery_app.py         # Celery application instance
│   │   │   └── tasks.py              # Task definitions
│   │   └── utils/
│   │       ├── auth.py               # JWT helpers, password hashing
│   │       └── storage.py            # Storage backend abstraction
│   ├── alembic/                # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── scripts/
│   │   └── seed_admin.py       # Creates initial admin account
│   ├── tests/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # Vue 3 application
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   ├── stores/             # Pinia stores
│   │   ├── views/
│   │   │   ├── StudentChat.vue
│   │   │   ├── AdminLogin.vue
│   │   │   └── AdminDashboard.vue
│   │   ├── components/
│   │   └── api/                # Axios API client
│   ├── public/
│   ├── Dockerfile              # Production (multi-stage, nginx)
│   ├── Dockerfile.dev          # Development (Vite dev server)
│   ├── nginx.conf              # Nginx config baked into prod image
│   ├── package.json
│   └── vite.config.ts
│
├── infra/
│   ├── nginx/
│   │   ├── nginx.dev.conf      # Dev reverse proxy config
│   │   ├── nginx.prod.conf     # Prod config (TLS, gzip, security headers)
│   │   └── ssl/                # TLS certificates (not in git)
│   └── certbot/
│       ├── conf/               # Let's Encrypt config (not in git)
│       └── www/                # ACME challenge webroot
│
├── docs/
│   └── architecture.md         # This document's companion
│
├── docker-compose.yml          # Development stack
├── docker-compose.prod.yml     # Production stack
├── .env.prod.example           # Production env template
├── .gitignore
└── README.md
```
