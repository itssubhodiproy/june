

# API Server — Service Design

*Last updated: 2025-07-01 · Status: Active*

---

## Responsibility

Single FastAPI application serving all CRUD operations for tables, columns, cells, and documents. Generates presigned S3 URLs. Enqueues tasks to Redis queues. Manages the PostgreSQL database as the sole writer. Every frontend action and every worker callback flows through this service.

## Tech Stack

- **Framework:** FastAPI (async, Python 3.12)
- **ORM:** SQLAlchemy 2.0 (async engine)
- **Validation:** Pydantic v2
- **Migrations:** Alembic
- **Redis:** aioredis (queue publishing)
- **S3:** boto3 (presigned URL generation)
- **Server:** Uvicorn (ASGI)

## Folder Structure

```
services/api-server/
├── Dockerfile
├── pyproject.toml
├── alembic.ini
├── alembic/
│   └── versions/
├── app/
│   ├── main.py                 ← FastAPI app, lifespan, middleware
│   ├── config.py               ← Settings from env vars (pydantic-settings)
│   ├── dependencies.py         ← DB session, Redis, S3 client injection
│   │
│   ├── routes/
│   │   ├── tables.py           ← /api/tables/**
│   │   ├── columns.py          ← /api/tables/{id}/columns/**
│   │   ├── cells.py            ← /api/tables/{id}/cells/**
│   │   ├── documents.py        ← /api/documents/**
│   │   ├── extraction.py       ← /api/tables/{id}/run, rerun
│   │   └── jobs.py             ← /api/jobs/**
│   │
│   ├── models/                 ← SQLAlchemy ORM models
│   │   ├── base.py             ← DeclarativeBase, common mixins
│   │   ├── workspace.py
│   │   ├── user.py
│   │   ├── table.py
│   │   ├── column.py
│   │   ├── cell.py
│   │   ├── document.py
│   │   ├── table_document.py
│   │   ├── document_chunk.py   ← pgvector model
│   │   └── job.py
│   │
│   ├── schemas/                ← Pydantic request/response schemas
│   │   ├── table.py
│   │   ├── column.py
│   │   ├── cell.py
│   │   ├── document.py
│   │   └── job.py
│   │
│   ├── services/               ← Business logic (no HTTP, no DB imports)
│   │   ├── table_service.py
│   │   ├── column_service.py
│   │   ├── cell_service.py
│   │   ├── document_service.py
│   │   ├── extraction_service.py
│   │   └── storage_service.py  ← S3 presigned URL generation
│   │
│   ├── middleware/
│   │   ├── auth.py             ← Authentication middleware
│   │   └── error_handler.py    ← Global exception → JSON error response
│   │
│   └── utils/
│       └── redis_tasks.py      ← Helper to publish tasks to Redis queues
└── tests/
    ├── conftest.py             ← Fixtures: test DB, test client
    ├── test_tables.py
    ├── test_columns.py
    ├── test_documents.py
    └── test_extraction.py
```

## Configuration

All configuration via environment variables, loaded by `pydantic-settings`:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://user:pass@postgres:5432/june` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `S3_ENDPOINT_URL` | MinIO/S3 endpoint | `http://minio:9000` |
| `S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | S3 secret key | `minioadmin` |
| `S3_BUCKET_NAME` | Bucket for document storage | `june-documents` |
| `S3_PRESIGNED_EXPIRY` | Presigned URL expiry in seconds | `3600` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `JWT_SECRET` | JWT signing secret | `your-secret-key` |

## Key Implementation Notes

**Dependency injection pattern.** Database sessions, Redis connections, and S3 clients are injected via FastAPI's `Depends()`. Routes never instantiate clients directly. This makes testing trivial — swap real dependencies for mocks.

```
Route → depends on → Service (business logic)
                      depends on → DB Session (injected)
                      depends on → Redis Client (injected)
                      depends on → S3 Client (injected)
```

**Soft delete pattern.** Tables and documents use `deleted_at` timestamp. Every query includes `.where(Model.deleted_at.is_(None))`. A `SoftDeleteMixin` on the base model provides `soft_delete()` method and a default query filter.

**Cell matrix management.** When a column is added, the API Server batch-inserts empty cells for every document in the table. When a document is added (via upload-url), empty cells are batch-inserted for every column. This ensures the cell grid is always complete — no missing cells.

```
POST /columns (add column)
  → INSERT INTO cells (table_id, document_id, column_id, status)
    SELECT table_id, document_id, {new_col_id}, 'empty'
    FROM table_documents WHERE table_id = {table_id}

POST /documents/upload-url (add document)
  → INSERT INTO cells (table_id, document_id, column_id, status)
    SELECT {table_id}, {new_doc_id}, id, 'empty'
    FROM columns WHERE table_id = {table_id}
```

**Column edit → stale cells.** When a column's `prompt` or `type` is updated via PATCH, all `completed` cells in that column are set to `stale` in the same transaction:

```
UPDATE cells SET status = 'stale', updated_at = now()
WHERE column_id = {col_id} AND status = 'completed'
```

**Run extraction logic.** `POST /api/tables/{id}/run` does three things in one request:
1. Query all cells where `status IN ('empty', 'stale')` AND the document's `parse_status = 'ready'`
2. Set their status to `'extracting'`
3. For each cell, publish a task to the `extraction_tasks` Redis queue
4. Create a `jobs` record with the total count
5. Return `202 Accepted` with the job ID

**Worker callbacks.** Both workers call back to the API Server via HTTP to save results:
- Document Worker: `POST /api/documents/{id}/chunks` and `PATCH /api/documents/{id}`
- Extraction Worker: `PUT /api/tables/{id}/cells/{cell_id}` (internal endpoint, not listed in public API — same route, but called by worker with service-level auth)

The cell save endpoint atomically updates the cell AND increments `jobs.completed_cells` (or `failed_cells`). When `completed_cells + failed_cells = total_cells`, job status flips to `'completed'`.

**Auto-save.** There is no "save" endpoint. Every mutation (create, update, delete) is persisted in the same request that performs it. The frontend shows a subtle "Saved" / "Saving..." indicator based on in-flight request count.

## Error Handling

Global exception handler in middleware converts all exceptions to the standard error response shape:

```json
{ "error": { "code": "NOT_FOUND", "message": "Table not found" } }
```

- `ValueError` / Pydantic `ValidationError` → 400
- Custom `NotFoundException` → 404
- Custom `ConflictException` → 409
- Unhandled exceptions → 500 with generic message (details logged, not exposed)

All errors are logged with request ID, timestamp, and stack trace. Request IDs are generated in middleware and passed through to enable tracing.

## Testing Strategy

- **Unit tests:** Service layer functions with mocked DB sessions. Test business logic without network.
- **Integration tests:** Route tests using FastAPI `TestClient` with a real test database (separate Postgres instance or schema). Test full request → response including validation and DB writes.
- **Fixtures:** `conftest.py` provides test database setup/teardown, seeded workspace, and authenticated test client.
- **Run:** `task api:test` → `pytest tests/ -v`