

# Infrastructure — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## Containers

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| api-server | python:3.12-slim | 8000 | All CRUD, queue publishing, presigned URLs |
| extraction-worker | python:3.12-slim | — | LLM calls, RAG pipeline |
| document-worker | python:3.12-slim + node:18 | — | LiteParse, chunking, embeddings |
| sse-service | golang:1.22-alpine → scratch | 8080 | SSE connections, event routing |
| frontend | node:18 → nginx:alpine | 3000 | React SPA static files |
| postgres | postgres:16 | 5432 | Relational + vector data |
| redis | redis:7-alpine | 6379 | Task queues + pub/sub |
| minio | minio/minio | 9000/9001 | S3-compatible object storage |

Workers have no ports — they are queue consumers, not HTTP servers.

## Docker Compose

```yaml
# docker-compose.yml (structure, not full file)

services:
  # --- Infrastructure ---
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: june
      POSTGRES_USER: june
      POSTGRES_PASSWORD: june
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports: ["9000:9000", "9001:9001"]
    volumes:
      - minio_data:/data

  # --- Application ---
  api-server:
    build: ./services/api-server
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis, minio]

  extraction-worker:
    build: ./services/extraction-worker
    env_file: .env
    depends_on: [redis, api-server]

  document-worker:
    build: ./services/document-worker
    env_file: .env
    depends_on: [redis, minio, api-server]

  sse-service:
    build: ./services/sse-service
    ports: ["8080:8080"]
    env_file: .env
    depends_on: [redis]

  frontend:
    build: ./frontend
    ports: ["3000:80"]

  gateway:
    build: ./services/gateway
    ports: ["80:80"]
    depends_on: [api-server, sse-service, frontend]

volumes:
  postgres_data:
  minio_data:
```

## Nginx Gateway

Routes requests by path prefix to the correct service:

```nginx
# services/gateway/nginx.conf

upstream api {
    server api-server:8000;
}

upstream sse {
    server sse-service:8080;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;

    # API routes
    location /api/tables/ {
        proxy_pass http://api;
    }

    location /api/documents/ {
        proxy_pass http://api;
    }

    # SSE routes (special proxy config for long-lived connections)
    location ~ ^/api/tables/[^/]+/events$ {
        proxy_pass http://sse;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;   # 24 hours — don't kill SSE connections
    }

    # Frontend (everything else)
    location / {
        proxy_pass http://frontend;
    }
}
```

Key SSE proxy settings: `proxy_buffering off` prevents Nginx from buffering events. `proxy_read_timeout 86400s` prevents Nginx from killing idle SSE connections. `Connection ''` prevents Nginx from adding `Connection: close`.

---

## S3 / MinIO

**Bucket:** `june-documents`

**Key naming convention:**

```
documents/{doc_id}/{original_file_name}

Example:
documents/550e8400-e29b-41d4-a716-446655440000/NovaChem.pdf
```

**Presigned URL flow:**

```
Upload:
1. API Server generates presigned PUT URL (valid 15 minutes)
2. Frontend uploads directly to MinIO via PUT
3. Frontend confirms upload → API Server verifies with HEAD request

Download:
1. API Server generates presigned GET URL (valid 1 hour)
2. Frontend fetches PDF directly from MinIO for Document Viewer
```

API Server never touches file bytes. MinIO handles all upload/download bandwidth.

**MinIO setup for local dev:**

```bash
# Create bucket on first run (handled by init script or manual)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/june-documents
```

**MinIO console:** `http://localhost:9001` — browse uploaded files, check bucket status.

---

## Redis

### Queues

Task queues use Redis lists with `LPUSH` (enqueue) and `BRPOP` (consume, blocking).

#### document_parsing

Published by API Server when a document upload is confirmed. Consumed by Document Worker.

```json
{
  "task_id": "task_001",
  "document_id": "doc_001",
  "file_key": "documents/doc_001/NovaChem.pdf",
  "table_id": "tbl_abc123",
  "retry_count": 0
}
```

#### extraction_tasks

Published by API Server when user clicks Run or Re-run. Consumed by Extraction Worker. Each task is a table-level trigger — the worker fetches the full cell manifest from the API Server.

```json
{
  "table_id": "tbl_abc123",
  "type": "run_all",
  "cell_id": "cell_xyz" // Optional: present for single-cell reruns
}
```

The worker calls `GET /api/tables/{table_id}/extraction-manifest?cell_id={cell_id}` to get the specific cell(s) to process. This prevents "blind" reruns from duplicating work on other already-extracting cells.

### Pub/Sub

Event channels use Redis pub/sub with pattern `table:{table_id}`.

SSE Service subscribes with `PSUBSCRIBE table:*` — one subscription catches all tables.

Workers publish with `PUBLISH table:tbl_abc123 {event_json}`.

### Event Catalog

| Event | Publisher | Channel | Data |
|-------|-----------|---------|------|
| `doc_ready` | Document Worker | `table:{table_id}` | `{ type, document_id, table_id, page_count }` |
| `doc_error` | Document Worker | `table:{table_id}` | `{ type, document_id, table_id, error }` |
| `cell_completed` | Extraction Worker | `table:{table_id}` | `{ type, cell_id, table_id, document_id, column_id, answer, reasoning, source_references }` |
| `cell_error` | Extraction Worker | `table:{table_id}` | `{ type, cell_id, table_id, document_id, column_id, error }` |
| `run_completed` | Extraction Worker | `table:{table_id}` | `{ type, table_id, total, completed, failed }` |

`run_completed` is published by the Extraction Worker after all cells in a manifest have been processed (completed or errored).

### Retry Policy

```
Retry count:    3 attempts max
Backoff:        2^retry × 5 seconds (5s, 10s, 20s)
Dead letter:    After 3 failures, task is not re-enqueued
                Document/cell is marked as "error" in DB
                User can manually retry via UI
```

Workers increment `retry_count` before re-enqueuing. If `retry_count >= MAX_RETRIES`, the task is dropped and the document/cell is marked as error.

---

## PostgreSQL

**Version:** 16 with pgvector extension.

**Init script** (`infra/postgres/init.sql`):

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

**Connection pooling:** SQLAlchemy async engine with pool size configured via env var. Default: `pool_size=10, max_overflow=20`.

**Backups:** Not configured in V1 local dev. For production: pg_dump cron or managed database snapshots.

---

## Environment Variables

Master list — all services read from the same `.env` file in local dev:

| Variable | Used By | Example |
|----------|---------|---------|
| `DATABASE_URL` | api-server | `postgresql+asyncpg://june:june@postgres:5432/june` |
| `REDIS_URL` | api-server, extraction-worker, document-worker, sse-service | `redis://redis:6379/0` |
| `S3_ENDPOINT_URL` | api-server, document-worker | `http://minio:9000` |
| `S3_ACCESS_KEY` | api-server, document-worker | `minioadmin` |
| `S3_SECRET_KEY` | api-server, document-worker | `minioadmin` |
| `S3_BUCKET_NAME` | api-server, document-worker | `june-documents` |
| `S3_PRESIGNED_EXPIRY` | api-server | `3600` |
| `API_SERVER_URL` | extraction-worker, document-worker | `http://api-server:8000` |
| `LLM_PROVIDER` | extraction-worker | `openai` |
| `OPENAI_API_KEY` | extraction-worker, document-worker | `sk-...` |
| `OPENAI_MODEL` | extraction-worker | `gpt-4o` |
| `EMBEDDING_PROVIDER` | document-worker | `openai` |
| `EMBEDDING_MODEL` | document-worker | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION` | document-worker | `1536` |
| `PARSER` | document-worker | `liteparse` |
| `MAX_CONCURRENT_PARSES` | document-worker | `1` |
| `MAX_CONCURRENT_EMBEDS` | document-worker | `5` |
| `MAX_CONCURRENT_EXTRACTIONS` | extraction-worker | `20` |
| `MAX_RETRIES` | extraction-worker, document-worker | `3` |
| `PORT` | sse-service | `8080` |
| `HEARTBEAT_INTERVAL` | sse-service | `30` |
| `CORS_ORIGINS` | api-server | `http://localhost:3000` |
| `JWT_SECRET` | api-server | `your-secret-key` |

**`.env.example`** is committed to the repo with placeholder values. `.env` is gitignored.