# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

June Review Table is an AI-powered document review tool that extracts structured answers from PDFs with citation-backed reasoning. Users upload PDFs, define extraction columns, and AI populates cells with answers, reasoning, and source references.

## Development Commands

```bash
# Start infrastructure (postgres, redis, minio)
task dev

# Start everything in Docker
task up

# Stop everything
task down

# Run all tests
task test

# Build Docker images
task build

# Database migrations
task migrate

# Seed test data
task seed

# Service-specific commands
task api:dev          # Run API server with hot reload
task api:test        # Run API server tests
task api:migrate      # Run database migrations
task frontend:dev    # Run frontend dev server
task frontend:test    # Run frontend tests
```

## Architecture

Monorepo with 5 services coordinated via Taskfile:

| Service | Tech | Port | Purpose |
|---------|------|------|---------|
| api-server | Python/FastAPI | 8000 | All CRUD, presigned URLs, task queueing |
| document-worker | Python | - | PDF parsing (LiteParse), chunking, embeddings |
| extraction-worker | Python | - | RAG pipeline, LLM calls, cell extraction |
| sse-service | Go | 8080 | SSE connections, event routing from Redis |
| frontend | React/TypeScript | 3000 | SPA with TanStack Table, Zustand, shadcn/ui |

Infrastructure: PostgreSQL 16 (pgvector), Redis (queues + pub/sub), MinIO (S3-compatible storage).

### Data Flow

1. **Document Upload**: Frontend → presigned URL → S3 → confirm → API enqueues to `document_parsing` queue
2. **Document Processing**: Document Worker parses PDF, generates embeddings, stores chunks in pgvector, publishes `doc_ready` event
3. **Cell Extraction**: User clicks Run → API enqueues tasks to `extraction_tasks` queue → Extraction Worker does RAG + LLM call → publishes `cell_completed` event
4. **Real-time Updates**: SSE Service subscribes to Redis pub/sub, pushes events to connected frontends

### Key Patterns

- **Service layer abstraction**: Routes never touch DB directly. Route → Service (business logic) → DB Session (injected).
- **Soft delete**: Tables and documents use `deleted_at` timestamp. Queries filter `deleted_at IS NULL`.
- **Cell matrix**: When adding a column/document, batch-insert empty cells for all rows/columns to ensure grid completeness.
- **Worker callbacks**: Workers call API Server HTTP endpoints to save results, not direct DB access.
- **Presigned URLs**: API Server never handles file bytes. Frontend uploads/downloads directly to/from S3.

## Service Structure

```
services/api-server/app/
├── main.py              # FastAPI app, lifespan, middleware
├── config.py            # Settings from env vars (pydantic-settings)
├── dependencies.py      # DB session, Redis, S3 client injection
├── routes/              # HTTP endpoints
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic (no HTTP/DB imports)
└── utils/redis_tasks.py # Helper to publish tasks

services/extraction-worker/app/
├── main.py              # Entry point
├── consumer.py          # Redis queue consumer loop
├── handler.py           # Orchestrates pipeline for one cell
├── rag/pipeline.py      # Retrieve chunks, build context
├── llm/client.py        # LLM abstraction (OpenAI/Anthropic)
└── clients/api_client.py

services/document-worker/app/
├── main.py              # Entry point
├── consumer.py          # Redis queue consumer loop
├── handler.py           # Orchestrates pipeline for one document
├── parsing/parser.py    # LiteParse wrapper
├── parsing/chunker.py   # Split pages into chunks with bbox
├── embedding/client.py # Embedding API abstraction
└── clients/             # S3, API, Redis clients

frontend/src/
├── stores/              # Zustand state (table-store, ui-store, upload-store)
├── api/                 # HTTP client wrappers
├── hooks/use-sse.ts     # SSE connection lifecycle
├── components/          # table/, drawer/, viewer/, forms/
└── pages/               # login.tsx, tables.tsx, table.tsx
```

## Cell States

| Status | Meaning |
|--------|---------|
| `empty` | New cell, never extracted |
| `extracting` | Worker processing |
| `completed` | Has answer, reasoning, sources |
| `stale` | Column prompt changed, needs re-extraction |
| `error` | Extraction failed |

## Redis Queues

| Queue | Publisher | Consumer |
|-------|-----------|----------|
| `document_parsing` | API Server | Document Worker |
| `extraction_tasks` | API Server | Extraction Worker |

## Redis Pub/Sub Events

| Event | Publisher | Channel Pattern |
|-------|-----------|-----------------|
| `doc_ready` | Document Worker | `table:{table_id}` |
| `doc_error` | Document Worker | `table:{table_id}` |
| `cell_completed` | Extraction Worker | `table:{table_id}` |
| `cell_error` | Extraction Worker | `table:{table_id}` |

## Configuration

All config via environment variables. Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`.

Key variables:
- `DATABASE_URL`: PostgreSQL async connection string
- `REDIS_URL`: Redis connection string
- `S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`: MinIO/S3 config
- `OPENAI_API_KEY`: Required for embeddings and LLM calls

## Testing

- API tests use `pytest` with a test database
- Worker tests mock external services (S3, LLM API)
- SSE service tests use `go test`
- Frontend tests use Vitest

## Frontend State

Three Zustand stores:
- `table-store`: Table metadata, documents, columns, cells (keyed by `"doc_id::col_id"`)
- `ui-store`: Layout state machine, selection, viewer state
- `upload-store`: Upload queue with 5 concurrent uploads

Layout transitions: `table_only` → `table_and_drawer` → `drawer_and_viewer`

## Design System

See `docs/DESIGN.md` for typography, colors, spacing, and component patterns. Uses shadcn/ui with custom theme. Key tokens: `--background`, `--surface`, `--foreground`, `--accent` (warm amber for CTAs).