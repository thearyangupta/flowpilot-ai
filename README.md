# FlowPilot AI

FlowPilot AI is a production-oriented workflow automation platform built with **FastAPI, PostgreSQL, Redis, Celery, and Google Gemini**.

It combines reliable asynchronous workflow execution, AI-powered decisions, recovery mechanisms, and secure Google OAuth credential management.

---

## Tech Stack

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- Celery
- Google Gemini
- Google OAuth 2.0
- PyJWT
- Pydantic
- Docker
- Pytest

---

## Features

- Project and workflow management
- Stateful workflow execution engine
- Redis and Celery background execution
- Dedicated workflow and maintenance queues
- Step registry architecture
- AI-powered email classification
- Structured LLM outputs with Pydantic
- Retry policies with exponential backoff and jitter
- Idempotent execution requests
- Checkpoint-based recovery and resume
- Heartbeat and stale-execution monitoring
- Execution events and audit timeline
- Scheduled maintenance with Celery Beat
- Internal user identity and active-user validation
- Short-lived FlowPilot JWT sessions
- Google OAuth with state and PKCE protection
- Google ID-token verification
- Encrypted OAuth credential storage
- MultiFernet encryption-key rotation
- Google access-token refresh and scope validation
- Google connection revocation and disconnect

---

## Architecture

```text
                   Client
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   Authentication             FastAPI API
 Google OAuth + JWT                │
          │                        ▼
          └──────────────► Service Layer
                                   │
                                   ▼
                              PostgreSQL
                                   │
                                   ▼
                         Redis Message Broker
                      ┌────────────┴────────────┐
                      ▼                         ▼
               Workflow Queue          Maintenance Queue
                      ▼                         ▼
                Celery Worker             Celery Worker
                      │                         │
                      └────────────┬────────────┘
                                   ▼
                            Workflow Runner
                      ┌────────────┼────────────┐
                      ▼            ▼            ▼
               Step Registry   Retry Engine  Checkpoints
                                   │
                                   ▼
                           Execution Events
```

---

## Project Structure

```text
app/
├── ai/          # AI providers, schemas and decision services
├── api/         # FastAPI routes and dependencies
├── core/        # Configuration, JWT, OAuth and encryption
├── db/          # SQLAlchemy session and base
├── domain/      # Execution rules and step registry
├── models/      # Database models
├── schemas/     # API request and response schemas
├── services/    # Application and integration services
├── worker/      # Celery workers and scheduled tasks
└── main.py

tests/
├── ai/
├── conftest.py
├── test_execution_service.py
├── test_projects.py
├── test_workflows.py
└── ...
```

---

## Quick Start

### Clone

```bash
git clone https://github.com/thearyangupta/flowpilot-ai.git
cd flowpilot-ai
```

### Install

```bash
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Configure

Create a `.env` file.

```env
APP_NAME=FlowPilot AI
ENVIRONMENT=development

DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@localhost:5432/flowpilot
TEST_DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@localhost:5432/flowpilot_test

REDIS_BROKER_URL=redis://localhost:6379/0
REDIS_RESULT_URL=redis://localhost:6379/1

GEMINI_API_KEY=<KEY>

JWT_SECRET=<LONG_RANDOM_SECRET>

GOOGLE_CLIENT_ID=<CLIENT_ID>
GOOGLE_CLIENT_SECRET=<CLIENT_SECRET>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

TOKEN_ENCRYPTION_KEYS=<CURRENT_FERNET_KEY>
```

### Run

```bash
alembic upgrade head

uvicorn app.main:app --reload

celery -A app.worker.celery_app worker --pool=solo --loglevel=info

celery -A app.worker.celery_app beat --loglevel=info
```

---

## API

### Projects

```
POST /api/v1/projects
```

### Workflows

```
POST /api/v1/projects/{project_id}/workflows
```

### Executions

```
POST /api/v1/projects/{project_id}/workflows/{workflow_id}/executions

GET /api/v1/projects/{project_id}/workflows/{workflow_id}/executions

GET /api/v1/executions/{execution_id}

GET /api/v1/executions/{execution_id}/events

POST /api/v1/executions/{execution_id}/resume
```

---

## Testing

```bash
python -m pytest
```

The project includes:

- AI unit tests
- Workflow engine tests
- Execution service tests
- Evaluation tests
- Integration tests

---

## Current Capabilities

- Production-grade FastAPI backend
- Redis-backed asynchronous workflow execution
- Celery workers and scheduled background jobs
- AI-powered workflow decision engine
- Reliable execution with retries, checkpoints, and recovery
- Idempotent workflow execution
- Execution auditing and event tracking
- Secure JWT-based user authentication
- Google OAuth 2.0 authentication with PKCE
- Encrypted OAuth credential storage with MultiFernet key rotation
- Automatic Google access-token refresh and scope validation
- Docker-based local development

---

## License

This project is built for learning, portfolio, and production engineering practice.