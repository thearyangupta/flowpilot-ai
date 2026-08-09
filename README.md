# FlowPilot AI

FlowPilot AI is a production-oriented workflow automation platform built with FastAPI, PostgreSQL, Redis, Celery, and Google Gemini.

It combines reliable asynchronous workflow execution, AI-powered decisions, recovery mechanisms, secure Google OAuth, and event-driven external integrations.

---

## Tech Stack

* Python 3.11
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Redis
* Celery
* Google Gemini
* Google OAuth 2.0
* PyJWT
* Pydantic
* Docker
* Pytest

---

## Features

* Project and workflow management
* Stateful workflow execution engine
* Redis and Celery background execution
* Dedicated workflow and maintenance queues
* Step registry architecture
* AI-powered email classification
* Structured LLM outputs with Pydantic
* Retry policies with exponential backoff and jitter
* Idempotent execution requests
* Checkpoint-based recovery and resume
* Heartbeat and stale-execution monitoring
* Execution events and audit timeline
* Scheduled maintenance with Celery Beat
* Secure JWT-based user authentication
* Google OAuth with state and PKCE protection
* Google ID-token verification
* Encrypted OAuth credential storage with MultiFernet key rotation
* Google access-token refresh and scope validation
* Gmail V1 polling with pagination and message retrieval
* Durable Gmail message ingestion and provider-message deduplication
* MIME normalization and deterministic body hashing
* Idempotent Gmail-triggered workflow execution
* Gmail threaded draft creation
* Human approval workflow with ownership and audit events
* Worker-side approval recheck before sending
* Provider send confirmation and error classification

---

## Architecture

```text
                              Client
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
          Authentication                     FastAPI API
        Google OAuth + JWT                       │
                 │                               ▼
                 └──────────────────────► Service Layer
                                                 │
                              ┌──────────────────┴──────────────────┐
                              ▼                                     ▼
                         PostgreSQL                         External Providers
                              │                              Gmail / Gemini
                              ▼
                         Redis Broker
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Workflow Queue            Maintenance Queue
                 ▼                         ▼
          Celery Worker              Celery Worker
                 │
                 ▼
          Workflow Runner
        ┌────────┼─────────┐
        ▼        ▼         ▼
     Steps     Retry   Checkpoints
        │
        ▼
 Execution Events / Audit
```

### Gmail V1 Flow

```text
Celery Beat
    ↓
Gmail polling
    ↓
messages.list + pagination
    ↓
messages.get
    ↓
MIME normalization
    ↓
Durable GmailMessage ingestion
    ↓
(user_id, provider_message_id) dedup
    ↓
Idempotent Execution
    ↓
Celery workflow execution
    ↓
AI decision / draft
    ↓
Human approval
    ↓
Worker-side recheck
    ↓
Gmail send
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
└── worker/      # Celery workers and scheduled tasks

tests/
├── ai/
├── conftest.py
├── execution/
├── workflows/
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

Create a `.env` file with the required database, Redis, Gemini, JWT, Google OAuth, and encryption settings.

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

```text
POST /api/v1/projects
```

### Workflows

```text
POST /api/v1/projects/{project_id}/workflows
```

### Executions

```text
POST /api/v1/projects/{project_id}/workflows/{workflow_id}/executions

GET /api/v1/projects/{project_id}/workflows/{workflow_id}/executions

GET /api/v1/executions/{execution_id}

GET /api/v1/executions/{execution_id}/events

POST /api/v1/executions/{execution_id}/resume
```

---

## Testing

```bash
pytest -q
```

The project includes unit, workflow, execution, reliability, AI, and integration-oriented tests.

---

## Current Capabilities

* Production-oriented FastAPI backend
* Redis-backed asynchronous workflow execution
* Celery workers and scheduled background jobs
* AI-powered workflow decision engine
* Reliable execution with retries, checkpoints, and stale-run recovery
* Idempotent workflow execution
* Execution auditing and event tracking
* Secure JWT and Google OAuth authentication
* Encrypted OAuth credential storage with key rotation
* Gmail polling, durable ingestion, deduplication, and workflow triggering
* Human-in-the-loop approval before provider-side actions
* Gmail draft and send integration
* Docker-based local development

---

## License

This project is built for learning, portfolio, and production engineering practice.