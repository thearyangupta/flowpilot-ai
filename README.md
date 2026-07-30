# FlowPilot AI

FlowPilot AI is a backend-first workflow automation platform built with FastAPI and PostgreSQL. The project focuses on building production-grade backend systems step by step, covering API design, database architecture, testing, observability, and AI integrations.

---

## Tech Stack

- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Google Gemini
- Pytest
- Docker

---

## Features Implemented

### Project Management

- Create and manage projects
- UUID-based resources
- Request validation with Pydantic

### Workflow Engine

- Create workflows under projects
- Ordered workflow steps
- Step registry architecture
- Domain validation for workflow definitions
- Extensible workflow execution pipeline

### Execution Engine

- Workflow execution state machine
- Step-level execution tracking
- Execution event timeline
- Retry mechanism with exponential backoff
- Idempotent execution requests
- Checkpoint-based workflow recovery
- Heartbeat monitoring for long-running executions
- Crash recovery and resume support
- Execution status management
- Execution filtering and ordering

### AI Decision Engine

- AI-powered email classification
- Structured outputs using Pydantic schemas
- Gemini provider integration
- Prompt engineering for consistent responses
- Safe fallback policy for invalid AI outputs
- DecisionService abstraction
- Tool-calling ready architecture

### Evaluation & Testing

- Labelled evaluation dataset
- Fake AI provider for deterministic tests
- Parametrized evaluation suite
- Evaluation metrics
- Decision metadata collection
- Integration testing with Pytest
- Reliability testing for retry behavior
- Idempotency validation tests
- Crash-and-resume recovery tests
- Execution event timeline verification
- Isolated PostgreSQL test database


### Backend Engineering

- Service layer architecture
- SQLAlchemy ORM models
- Alembic migrations
- Request ID middleware
- Structured request logging

---

## Architecture Overview

```text
Client Request
       │
       ▼
FastAPI API Layer
       │
       ▼
Service Layer
       │
       ▼
Workflow Execution Engine
       │
       ├── Step Registry
       ├── Retry Engine
       ├── Checkpoint Recovery
       ├── Execution Events
       └── AI Decision Service
       │
       ▼
PostgreSQL
```

## AI Workflow

```text
Incoming Email
        │
        ▼
Gemini Decision Provider
        │
        ▼
Structured EmailDecision
        │
        ▼
Schema Validation
        │
        ▼
DecisionService
        │
        ▼
Workflow Execution Engine
        │
        ▼
Step Execution
        │
        ▼
Retry & Recovery
        │
        ▼
Execution Event Timeline
```

# Project Structure

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
└── main.py

tests/
├── ai/
├── conftest.py
├── test_health.py
├── test_projects.py
├── test_workflows.py
└── ...
```

---

# Local Setup

## 1. Clone the repository

```bash
git clone https://github.com/thearyangupta/flowpilot-ai.git
cd flowpilot-ai
```

---

## 2. Create a virtual environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
APP_NAME=FlowPilot AI
ENVIRONMENT=development

DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@localhost:5432/flowpilot

TEST_DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@localhost:5432/flowpilot_test
```

> **Note:** The `.env` file is ignored by Git and should never be committed.

---

## 5. Create PostgreSQL Databases

Open PostgreSQL inside Docker:

```powershell
docker exec -it govprep-pg psql -U postgres
```

Create the databases:

```sql
CREATE DATABASE flowpilot;

CREATE DATABASE flowpilot_test;
```

Exit PostgreSQL:

```sql
\q
```

---

## 6. Run Database Migrations

```powershell
alembic upgrade head
```

---

## 7. Start the API

```powershell
uvicorn app.main:app --reload
```

API:

```
http://127.0.0.1:8000
```

Swagger:

```
http://127.0.0.1:8000/docs
```

Health Check:

```
http://127.0.0.1:8000/health
```

---

# Running Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

Current repository includes:

- Backend integration tests
- AI unit tests
- Evaluation tests
- Deterministic fake-provider tests

Tests execute against the dedicated **flowpilot_test** database without modifying development data.

---

# API Endpoints

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
```

---

## Current Capabilities

- Production-ready FastAPI backend
- PostgreSQL persistence with SQLAlchemy
- Alembic migration management
- Workflow execution engine
- Stateful workflow execution tracking
- Extensible step registry
- AI-powered email decision engine
- Structured LLM outputs with validation
- Safe fallback handling
- Retry mechanism with exponential backoff
- Idempotent execution requests
- Checkpoint-based execution recovery
- Heartbeat monitoring
- Execution event timeline
- Reliability and recovery test suite
- Evaluation framework for AI decisions
- Docker-based local development

---

## Roadmap

- Complete AI workflow execution integration
- MCP server integration
- Authentication & authorization
- Background task execution
- Production deployment
- Monitoring & observability

---

## License

This project is developed for learning, portfolio, and production engineering practice.