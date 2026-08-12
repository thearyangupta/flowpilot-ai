# FlowPilot AI

FlowPilot AI is a production-oriented **AI workflow automation backend** built with FastAPI, PostgreSQL, Redis, Celery, pgvector, and Google Gemini.

It combines reliable asynchronous workflows, Gmail automation, human approval, and a tenant-safe **Retrieval-Augmented Generation (RAG)** pipeline with grounded responses and measurable retrieval quality.

## Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic  
**Async:** Redis, Celery, Celery Beat  
**AI / RAG:** Google Gemini, pgvector, PostgreSQL Full-Text Search  
**Auth & Integrations:** JWT, Google OAuth 2.0, Gmail API  
**Infrastructure:** Docker  
**Testing:** Pytest

## Key Features

### Workflow & Reliability

- Stateful asynchronous workflow execution
- Celery workers with dedicated queues
- Retry policies with exponential backoff and jitter
- Idempotent execution requests
- Checkpoint-based recovery and resume
- Heartbeats and stale-execution recovery
- Execution events and audit trails

### Gmail Automation

- Secure Google OAuth with PKCE and state validation
- Encrypted OAuth credential storage with key rotation
- Durable Gmail message ingestion and deduplication
- MIME normalization
- AI-powered email classification
- Threaded Gmail draft creation
- Human approval before sending
- Worker-side approval revalidation

### Knowledge & RAG

- Knowledge document ingestion and deduplication
- Token-aware chunking with overlap and versioning
- Batch and replay-safe embeddings
- pgvector + HNSW cosine indexing
- Hybrid vector + full-text retrieval
- Reciprocal Rank Fusion (RRF)
- Tenant-safe knowledge retrieval
- Token-budgeted context construction
- Grounded Gemini responses with source labels
- Citation allow-list validation
- Explicit `needs_knowledge` refusal for unsupported answers

### RAG Evaluation

- Versioned golden retrieval cases
- Recall@k
- Citation validity rate
- Unsupported refusal rate
- p50 / p95 retrieval latency
- Versioned retrieval configuration comparison

## Architecture

```text
                         FastAPI
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
           PostgreSQL    Redis      Gmail / Gemini
           + pgvector       │
                │           ▼
                │      Celery Workers
                │           │
                │           ▼
                │     Workflow Engine
                │
                ▼
        Knowledge Pipeline
                │
      ┌─────────┴──────────┐
      ▼                    ▼
 Vector Search        Full-Text Search
      │                    │
      └─────────┬──────────┘
                ▼
               RRF
                ▼
        Grounded Context
                ▼
              Gemini
                ▼
       Citation Validation
                ▼
     GROUNDED / NEEDS_KNOWLEDGE
```

## Engineering Highlights

FlowPilot is designed around production backend and AI engineering principles:

- **Reliability:** retries, idempotency, checkpoints, heartbeats, recovery
- **Security:** JWT, OAuth PKCE, encrypted credentials, tenant isolation
- **AI Safety:** structured outputs, bounded context, citation validation, explicit refusal
- **RAG Quality:** hybrid retrieval, deterministic ranking, golden evaluations and latency measurement
- **Architecture:** service-layer boundaries, provider abstractions and background workers

## Project Structure

```text
app/
├── ai/          # Gemini providers and structured AI outputs
├── api/         # FastAPI routes
├── core/        # Auth, configuration and encryption
├── domain/      # Workflow execution rules
├── evaluation/  # RAG evaluation
├── models/      # SQLAlchemy models
├── services/    # Business logic, Gmail and knowledge services
└── worker/      # Celery workers and scheduled tasks

tests/
└── ...          # AI, workflow, execution and knowledge tests
```

## Run Locally

```bash
git clone https://github.com/thearyangupta/flowpilot-ai.git
cd flowpilot-ai

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
alembic upgrade head

uvicorn app.main:app --reload
```

Run workers:

```bash
celery -A app.worker.celery_app worker --pool=solo --loglevel=info
celery -A app.worker.celery_app beat --loglevel=info
```

Run tests:

```bash
pytest -q
```

## Current Status

FlowPilot currently includes:

**Workflow Engine → Reliability → Google OAuth → Gmail Automation → Human Approval → Knowledge Ingestion → Embeddings → Hybrid Retrieval → Grounded Generation → RAG Evaluation**

The project is actively being developed as a production-oriented backend and AI engineering system.

## License

Built for learning, portfolio development, and production engineering practice.