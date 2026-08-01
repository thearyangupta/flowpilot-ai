# FlowPilot AI

FlowPilot AI is a production-oriented workflow automation platform built with **FastAPI, PostgreSQL, Redis, Celery, and Google Gemini**. It focuses on reliable asynchronous workflow execution, AI-powered decision making, fault tolerance, and production backend engineering practices.

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
- Pydantic
- Docker
- Pytest

---

## Features

- Project and workflow management
- Stateful workflow execution engine
- Redis + Celery asynchronous execution
- Execution state machine
- Step registry architecture
- AI-powered email classification
- Structured LLM outputs with Pydantic
- Retry mechanism with exponential backoff
- Idempotent execution requests
- Checkpoint-based workflow recovery
- Heartbeat monitoring
- Automatic stale execution recovery
- Execution event timeline
- Background maintenance jobs with Celery Beat
- Dedicated PostgreSQL test database

---

## Architecture

```text
                Client
                   │
                   ▼
             FastAPI API
                   │
                   ▼
            Service Layer
                   │
          Create Execution
                   │
                   ▼
             PostgreSQL
                   │
                   ▼
          Redis Message Broker
          ┌──────────┴──────────┐
          ▼                     ▼
 Workflow Queue          Maintenance Queue
          ▼                     ▼
 Celery Worker         Celery Worker
          │                     │
          └──────────┬──────────┘
                     ▼
            Workflow Runner
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Step Registry   Retry Engine   Checkpoints
                     │
                     ▼
             Execution Events
                     │
                     ▼
               PostgreSQL
```

---

## Project Structure

```text
app/
├── ai/
├── api/
├── core/
├── db/
├── domain/
├── models/
├── schemas/
├── services/
├── worker/
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
- Redis-backed asynchronous processing
- Celery workflow workers
- AI-powered decision engine
- Reliable workflow execution
- Retry and recovery mechanisms
- Checkpoint-based resume
- Idempotent execution
- Heartbeat monitoring
- Execution auditing
- Docker-based local development

---

## License

This project is built for learning, portfolio, and production engineering practice.