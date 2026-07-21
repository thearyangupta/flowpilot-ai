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
- Pytest
- Docker

---

## Features Implemented

### Project Management
- Create projects
- Input validation
- UUID-based resources

### Workflow Management
- Create workflows under projects
- Nested resource validation

### Execution Management
- Create executions under workflows
- Execution status enum
- Default pending state
- Execution filtering
- Execution ordering

### Backend Engineering
- API versioning
- Service layer architecture
- SQLAlchemy ORM models
- Alembic database migrations
- Request ID middleware
- Structured request logging

### Testing
- Integration testing with Pytest
- FastAPI TestClient
- Isolated PostgreSQL test database
- Dependency override for testing

---

# Project Structure

```text
app/
├── api/
├── core/
├── db/
├── models/
├── schemas/
├── services/
└── main.py

tests/
├── conftest.py
├── test_health.py
├── test_projects.py
└── test_workflows.py
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

The tests run against the dedicated **flowpilot_test** database and do not modify development data.

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

# Development Progress


- Backend project setup
- Configuration management
- Database models
- SQLAlchemy relationships
- Alembic migrations
- Service layer
- Project APIs
- Workflow APIs
- Execution APIs
- Request logging
- Request ID middleware
- Integration testing
- Isolated test database

---

## Upcoming

- Enhanced error handling
- Background task execution
- AI workflow engine
- MCP integration
- Authentication & authorization
- Production deployment

---

## License

This project is developed for learning, portfolio, and production engineering practice.