This file is a merged representation of the entire codebase, combined into a single document by Repomix.
The content has been processed where comments have been removed, empty lines have been removed, content has been compressed (code blocks are separated by ⋮---- delimiter).

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Code comments have been removed from supported file types
- Empty lines have been removed from all files
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
api.md/
  api.md
architecture.md/
  architecture.md
DESIGN.md/
  DESIGN.md
frontend.md/
  frontend.md
image.png/
  image.png
infrastructure.md/
  infrastructure.md
local-setup.md/
  local-setup.md
product.md/
  product.md
README.md/
  README.md
schema.md/
  schema.md
services/
  api-server.md/
    api-server.md
  document-worker.md/
    document-worker.md
  extraction-worker.md/
    extraction-worker.md
  sse-service.md/
    sse-service.md
```

# Files

## File: api.md/api.md
````markdown
# API Reference — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

All endpoints are prefixed with `/api`. All request/response bodies are JSON. All IDs are UUIDs. Timestamps are ISO 8601. Authentication is via session cookie or Bearer token (handled by API Gateway).

---

## Tables

### POST /api/tables

Create a new review table.

```
Request:  { "name": "Review Table #81" }   // optional — auto-generates if omitted
Response: {
  "id": "tbl_abc123",
  "workspace_id": "ws_001",
  "name": "Review Table #81",
  "created_at": "2025-07-01T10:00:00Z",
  "updated_at": "2025-07-01T10:00:00Z"
}
Status: 201 Created
```

Name auto-generates as "Review Table #N" based on existing count in workspace.

---

### GET /api/tables

List all tables in the current workspace.

```
Response: {
  "tables": [
    {
      "id": "tbl_abc123",
      "name": "Review Table #81",
      "document_count": 50,
      "column_count": 5,
      "created_at": "2025-07-01T10:00:00Z",
      "updated_at": "2025-07-01T14:30:00Z"
    }
  ]
}
Status: 200 OK
```

---

### GET /api/tables/{table_id}

Get a table with all its data — documents, columns, and cells. This is the single hydration call the frontend makes on page load.

```
Response: {
  "id": "tbl_abc123",
  "name": "Review Table #81",
  "created_at": "2025-07-01T10:00:00Z",
  "updated_at": "2025-07-01T14:30:00Z",
  "documents": [
    {
      "id": "doc_001",
      "file_name": "NovaChem.pdf",
      "file_type": "pdf",
      "file_size": 2400000,
      "page_count": 42,
      "parse_status": "ready",
      "added_at": "2025-07-01T10:05:00Z"
    }
  ],
  "columns": [
    {
      "id": "col_001",
      "title": "Parties",
      "prompt": "Who are the parties to this agreement?",
      "type": "free_response",
      "order": 1
    },
    {
      "id": "col_002",
      "title": "Change of Control",
      "prompt": "Does this agreement contain a change of control provision?",
      "type": "yes_no",
      "order": 2
    }
  ],
  "cells": [
    {
      "id": "cell_xyz",
      "document_id": "doc_001",
      "column_id": "col_001",
      "status": "completed",
      "answer": "DataPulse Ltd. (Provider) and NovaChem GmbH (Client)",
      "reasoning": "Found in the preamble on page 1. The agreement identifies DataPulse Ltd., a company registered in England, as the Provider, and NovaChem GmbH, a company registered in Germany, as the Client.",
      "source_references": [
        {
          "chunk_id": "chunk_abc",
          "page": 1,
          "section": "Preamble",
          "quote": "This Master Services Agreement is entered into between DataPulse Ltd. and NovaChem GmbH"
        }
      ]
    }
  ]
}
Status: 200 OK
```

Notes:
- `cells` is a flat array. Frontend indexes by `document_id::column_id` for O(1) lookup.
- `parse_status` is `"not_ready"` or `"ready"` or `"error"`. Frontend uses this for faded/solid row styling.
- `columns` are ordered by the `order` field.

---

### PATCH /api/tables/{table_id}

Update table metadata (rename).

```
Request:  { "name": "Project Falcon DD" }
Response: {
  "id": "tbl_abc123",
  "name": "Project Falcon DD",
  "updated_at": "2025-07-01T15:00:00Z"
}
Status: 200 OK
```

---

### DELETE /api/tables/{table_id}

Delete a table and all associated data (columns, cells, document associations).

```
Response: { }
Status: 204 No Content
```

Backend soft-deletes (sets `deleted_at`). UI treats as permanent.

---

## Documents

### POST /api/documents/upload-url

Request a presigned S3 URL for direct browser upload.

```
Request: {
  "file_name": "NovaChem.pdf",
  "file_type": "application/pdf",
  "file_size": 2400000,
  "table_id": "tbl_abc123"
}
Response: {
  "doc_id": "doc_001",
  "upload_url": "https://minio:9000/bucket/documents/doc_001/NovaChem.pdf?X-Amz-...",
  "file_key": "documents/doc_001/NovaChem.pdf"
}
Status: 201 Created
```

Side effects:
- Creates `documents` record with `parse_status: "not_ready"`.
- Creates `table_documents` association.
- Does NOT enqueue parsing yet — wait for confirm.

---

### POST /api/documents/{doc_id}/confirm

Confirm that the file has been uploaded to S3. Triggers parsing.

```
Request:  { }
Response: {
  "doc_id": "doc_001",
  "parse_status": "not_ready"
}
Status: 200 OK
```

Side effects:
- Verifies file exists in S3 (HEAD request).
- Enqueues `document_parsing` task to Redis.
- Frontend row is already visible (added on upload-url call). Stays faded until `doc_ready` SSE event.

---

### GET /api/documents/{doc_id}/file

Get a presigned download URL for viewing the PDF in the Document Viewer.

```
Response: {
  "doc_id": "doc_001",
  "file_name": "NovaChem.pdf",
  "download_url": "https://minio:9000/bucket/documents/doc_001/NovaChem.pdf?X-Amz-...",
  "expires_in": 3600
}
Status: 200 OK
```

Frontend fetches the PDF via `download_url` and renders with react-pdf.

---

### GET /api/documents/{doc_id}/chunks/{chunk_id}

Get a specific chunk with bounding box data. Used when the user clicks a source reference chip to highlight text in the Document Viewer.

```
Response: {
  "id": "chunk_abc",
  "document_id": "doc_001",
  "chunk_index": 0,
  "text_content": "This Master Services Agreement is entered into between DataPulse Ltd., a company registered in England (\"Provider\"), and NovaChem GmbH, a company registered in Germany (\"Client\").",
  "page_number": 1,
  "section": "Preamble",
  "bbox": {
    "page_width": 612,
    "page_height": 792,
    "items": [
      { "text": "This Master Services Agreement", "x": 72, "y": 120, "width": 200, "height": 12 },
      { "text": "is entered into between", "x": 72, "y": 134, "width": 145, "height": 12 },
      { "text": "DataPulse Ltd.", "x": 220, "y": 134, "width": 85, "height": 12 }
    ]
  }
}
Status: 200 OK
```

Frontend scales bounding box coordinates by `render_dpi / 72` to position highlight overlays on the rendered PDF page.

---

### GET /api/documents/{doc_id}/chunks

Semantic search over a document's chunks. Used internally by the Extraction Worker for RAG retrieval.

```
Query params: ?query=liability+cap&top_k=10

Response: {
  "chunks": [
    {
      "id": "chunk_xyz",
      "chunk_index": 23,
      "text_content": "8.2 Limitation of Liability. The aggregate liability...",
      "page_number": 14,
      "section": "8.2",
      "similarity_score": 0.89,
      "bbox": { ... }
    }
  ]
}
Status: 200 OK
```

---

### POST /api/documents/{doc_id}/chunks

Batch store chunks with embeddings. Called by Document Worker after parsing.

```
Request: {
  "chunks": [
    {
      "chunk_index": 0,
      "text_content": "This Master Services Agreement...",
      "page_number": 1,
      "section": "Preamble",
      "bbox": {
        "page_width": 612,
        "page_height": 792,
        "items": [
          { "text": "...", "x": 72, "y": 120, "width": 200, "height": 12 }
        ]
      },
      "embedding": [0.023, -0.041, 0.067, ...]
    }
  ]
}
Response: { "stored": 47 }
Status: 201 Created
```

---

### PATCH /api/documents/{doc_id}

Update document metadata. Called by Document Worker when parsing completes or fails.

```
Request:  { "parse_status": "ready", "page_count": 42 }
Response: {
  "id": "doc_001",
  "parse_status": "ready",
  "page_count": 42,
  "updated_at": "2025-07-01T10:06:30Z"
}
Status: 200 OK
```

---

### DELETE /api/tables/{table_id}/documents/{doc_id}

Remove a document from a table. Deletes all cells for this document in this table.

```
Response: { }
Status: 204 No Content
```

Soft-deletes the `table_documents` association and all related cells. If the document is not associated with any other table, soft-deletes the document itself.

---

## Columns

### POST /api/tables/{table_id}/columns

Add a column to a table.

```
Request: {
  "title": "Liability Cap",
  "prompt": "What is the aggregate liability cap? Express as a dollar amount or formula.",
  "type": "currency"
}
Response: {
  "id": "col_003",
  "table_id": "tbl_abc123",
  "title": "Liability Cap",
  "prompt": "What is the aggregate liability cap? Express as a dollar amount or formula.",
  "type": "currency",
  "order": 3,
  "created_at": "2025-07-01T11:00:00Z"
}
Status: 201 Created
```

`order` is auto-assigned as max(existing orders) + 1. Column types: `free_response`, `yes_no`, `date`, `currency`, `verbatim`.

Side effects:
- Creates empty cell records for every document in the table (status: `"empty"`).

---

### PATCH /api/tables/{table_id}/columns/{col_id}

Edit a column's title, prompt, or type.

```
Request: {
  "prompt": "What is the aggregate liability cap, including any carve-outs or exceptions?"
}
Response: {
  "id": "col_003",
  "title": "Liability Cap",
  "prompt": "What is the aggregate liability cap, including any carve-outs or exceptions?",
  "type": "currency",
  "order": 3,
  "updated_at": "2025-07-01T12:00:00Z"
}
Status: 200 OK
```

Side effects:
- If `prompt` or `type` changed: all cells in this column are marked `status: "stale"`.
- Frontend dims stale cells and shows "Re-run" button on column header.

---

### DELETE /api/tables/{table_id}/columns/{col_id}

Delete a column and all its cells.

```
Response: { }
Status: 204 No Content
```

---

## Extraction

### POST /api/tables/{table_id}/run

Run extraction on all empty and stale cells.

```
Request:  { }
Response: {
  "job_id": "job_xyz",
  "table_id": "tbl_abc123",
  "total_cells": 200,
  "status": "running"
}
Status: 202 Accepted
```

Side effects:
- Identifies all cells where `status` is `"empty"` or `"stale"` AND document `parse_status` is `"ready"`.
- Sets their status to `"extracting"`.
- Enqueues one `extraction_tasks` Redis task per cell.
- Creates a `jobs` record for tracking.

Idempotent — safe to call multiple times. Only processes cells that need processing.

---

### POST /api/tables/{table_id}/cells/{cell_id}/rerun

Re-extract a single cell.

```
Request:  { }
Response: {
  "cell_id": "cell_xyz",
  "status": "extracting"
}
Status: 202 Accepted
```

Side effects:
- Sets cell status to `"extracting"`.
- Enqueues one `extraction_tasks` Redis task.

---

### GET /api/jobs/{job_id}

Get job progress.

```
Response: {
  "id": "job_xyz",
  "table_id": "tbl_abc123",
  "total_cells": 200,
  "completed_cells": 142,
  "failed_cells": 3,
  "status": "running",
  "created_at": "2025-07-01T12:00:00Z"
}
Status: 200 OK
```

`status`: `"running"`, `"completed"`, `"failed"`.

---

## SSE Events

### GET /api/tables/{table_id}/events

Opens an SSE connection. One per table session. Frontend uses native `EventSource` API.

```
Headers:
  Accept: text/event-stream
  Authorization: Bearer {token}
```

The connection stays open until the client disconnects or navigates away. SSE Service sends heartbeat comments (`: heartbeat`) every 30 seconds to keep the connection alive.

### Event Types

#### doc_ready

Document parsing completed. Row should transition from faded to solid.

```
event: doc_ready
data: { "document_id": "doc_001", "table_id": "tbl_abc123", "page_count": 42 }
```

#### doc_error

Document parsing failed.

```
event: doc_error
data: { "document_id": "doc_001", "table_id": "tbl_abc123", "error": "OCR failed on page 7" }
```

#### cell_completed

A single cell extraction finished. Frontend updates that cell from shimmer to answer.

```
event: cell_completed
data: {
  "cell_id": "cell_xyz",
  "table_id": "tbl_abc123",
  "document_id": "doc_001",
  "column_id": "col_003",
  "answer": "12 months aggregate fees",
  "reasoning": "Section 8.2 limits aggregate liability to twelve months of fees paid...",
  "source_references": [
    {
      "chunk_id": "chunk_xyz",
      "page": 14,
      "section": "8.2",
      "quote": "aggregate liability shall not exceed the total fees paid during the twelve month period"
    }
  ]
}
```

#### cell_error

A single cell extraction failed.

```
event: cell_error
data: {
  "cell_id": "cell_xyz",
  "table_id": "tbl_abc123",
  "document_id": "doc_001",
  "column_id": "col_003",
  "error": "Context too long for document"
}
```

#### run_completed

All cells in a run have finished (completed or errored).

```
event: run_completed
data: {
  "job_id": "job_xyz",
  "table_id": "tbl_abc123",
  "total": 200,
  "completed": 195,
  "failed": 5
}
```

---

## Error Responses

All error responses follow the same shape:

```
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Table not found"
  }
}
```

| Status | Code | When |
|--------|------|------|
| 400 | VALIDATION_ERROR | Invalid request body, missing required fields |
| 404 | NOT_FOUND | Table, document, column, or cell doesn't exist |
| 409 | CONFLICT | Document already associated with this table |
| 422 | INVALID_COLUMN_TYPE | Column type not in allowed enum |
| 500 | INTERNAL_ERROR | Unexpected server error |

---

## Rate Limits

Not enforced in V1. API Gateway (Nginx) can add rate limiting per-IP if needed. Designed for single-tenant workspace usage — not a public API.
````

## File: architecture.md/architecture.md
````markdown
# Architecture — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## System Architecture

![alt text](image.png)

**API Server** — Single FastAPI application. All CRUD for tables, columns, cells, documents. Generates presigned S3 URLs. Enqueues tasks to Redis. Serves the frontend's every need. Stateless.

**SSE Service** — Go. Holds long-lived SSE connections with frontends. Subscribes to Redis pub/sub. When a worker publishes an event, SSE Service pushes it to every connected client viewing that table. ~200 lines of Go. One goroutine per connection at 2KB each.

**Document Worker** — Python. Consumes `document_parsing` queue. Downloads PDF from S3, parses with LiteParse (local OCR + layout extraction with bounding boxes), chunks text, generates embeddings via external API, stores chunks in pgvector, publishes `doc_ready` event. CPU-bound. Low concurrency per instance (1-2 docs at a time). Scale horizontally.

**Extraction Worker** — Python. Consumes `extraction_tasks` queue. For each cell: retrieves relevant chunks from pgvector (RAG), constructs prompt, calls LLM, parses structured response (answer + reasoning + source references), saves cell result, publishes `cell_completed` event. IO-bound (waiting on LLM). High concurrency per instance (20-50 concurrent calls). Scale horizontally.

---

## Service Communication

| From | To | Via | Purpose |
|------|----|-----|---------|
| Frontend | API Server | HTTP | All CRUD, trigger runs, presigned URLs |
| Frontend | SSE Service | SSE | Receive real-time events (doc ready, cell completed) |
| API Server | Redis | LPUSH | Enqueue parsing and extraction tasks |
| API Server | S3 | AWS SDK | Generate presigned URLs |
| API Server | PostgreSQL | SQLAlchemy | Read/write all relational + vector data |
| Document Worker | Redis | BRPOP | Consume parsing tasks |
| Document Worker | S3 | HTTP | Download PDF files |
| Document Worker | API Server | HTTP | Store chunks, update doc status |
| Document Worker | Redis | PUBLISH | Emit doc_ready / doc_error events |
| Document Worker | Embedding API | HTTP | Generate vector embeddings |
| Extraction Worker | Redis | BRPOP | Consume extraction tasks |
| Extraction Worker | API Server | HTTP | Read chunks (RAG), save cell results |
| Extraction Worker | Redis | PUBLISH | Emit cell_completed / cell_error events |
| Extraction Worker | LLM API | HTTP | Generate cell answers |
| SSE Service | Redis | SUBSCRIBE | Listen for events from both workers |

---

## Data Flows

### Document Upload + Processing

```
1. Frontend selects files, requests presigned URL per file:
   POST /api/documents/upload-url → { doc_id, upload_url }

2. Frontend uploads directly to S3 via presigned URL (API Server never touches bytes)

3. Frontend confirms upload:
   POST /api/documents/{doc_id}/confirm
   → API Server creates DB record (status: "not_ready"), enqueues parsing task

4. Row appears in table immediately — faded with subtle pulse

5. Document Worker picks up task from Redis queue:
   Download from S3 → LiteParse (parse + OCR) → chunk text with bounding boxes
   → embed chunks → POST /api/documents/{doc_id}/chunks → PATCH status to "ready"
   → PUBLISH doc_ready event

6. SSE Service pushes event to frontend → row transitions from faded to solid
```

### Cell Extraction

```
1. User clicks Run:
   POST /api/tables/{id}/run
   → API Server finds all empty/stale cells, enqueues one task per cell

2. All target cells show skeleton shimmer animation

3. Extraction Worker picks up task:
   GET /api/documents/{doc_id}/chunks?query={prompt} → top-K chunks (RAG)
   → construct prompt with chunks + column question
   → call LLM → parse structured response (answer, reasoning, source_references)
   → PUT /api/tables/{id}/cells/{cell_id} → PUBLISH cell_completed event

4. SSE Service pushes event → frontend updates cell: shimmer → fade-in answer text

5. Repeats for all cells in parallel. Workers process at their own pace.
   User sees cells filling in progressively.
```

### Source Verification

```
1. User clicks cell → Memory Drawer opens (reads from client-side state, zero API calls)
   Shows answer + reasoning + source chips for every column of that document

2. User clicks source chip (📎 p.14, §8.2):
   → GET /api/documents/{doc_id}/file → presigned S3 download URL
   → Frontend loads PDF, navigates to page 14
   → GET /api/documents/{doc_id}/chunks/{chunk_id} → bounding box coordinates
   → Frontend draws highlight overlay at exact text position

3. Table hides. View becomes Memory Drawer (30%) + Document Viewer (70%).
   Esc returns to Table + Memory Drawer.
```

---

## Decisions

| # | Decision | Why | Rejected Alternatives |
|---|----------|-----|-----------------------|
| 1 | Single API Server (not three services) | Same scaling profile, shared DB, one-person team, eliminates inter-service HTTP calls | Separate table/document/extraction services — coordination overhead with no benefit |
| 2 | Python for API Server + both workers | AI/ML ecosystem dominance, team productivity, performance irrelevant for CRUD and IO-bound work | Go (learning curve, verbose CRUD), Node (weaker ORM ecosystem) |
| 3 | Go for SSE Service | Goroutines at 2KB/conn, 10K connections in 20MB, stdlib HTTP, tiny codebase (~200 lines) | Node (heavier per connection), Python (not ideal for connection-heavy) |
| 4 | Python for Document Worker (not Node) | LiteParse Python wrapper has <1% overhead. Keeps entire backend in Python. Swap parsers by changing one import. | Node (native LiteParse but locks us into one parser, fragments the stack) |
| 5 | LiteParse for PDF parsing | Local execution, zero API dependency, bounding boxes for citations, OCR built-in, free | LlamaParse (external API dependency, cost), PyPDF (no OCR, no layout, no bounding boxes) |
| 6 | Separate Document + Extraction workers | CPU-bound parsing vs IO-bound LLM calls — different scaling profiles, resource isolation | Single worker (CPU-intensive OCR starves LLM connection management) |
| 7 | No manual cell editing | Answer + reasoning + source are a bonded triad. Editing answer while reasoning references different text breaks trust. | Allow editing (destroys citation integrity, undermines verification UX) |
| 8 | pgvector (not separate vector DB) | One fewer infrastructure dependency. Sufficient for V1 scale (5M vectors). Same Postgres instance. | Qdrant/Pinecone (overkill, additional operational burden) |
| 9 | Chunks stored only in vector DB | Only consumer is RAG search. Duplicating in Postgres wastes storage and serves no query pattern. | Also in Postgres (redundant, 15-30GB wasted at 100K docs) |
| 10 | SSE over WebSocket | Unidirectional push is all we need. Built-in browser reconnection. Works through all proxies. Simpler. | WebSocket (bidirectional not needed, awkward auth, manual reconnection) |
| 11 | Presigned URLs for upload | API Server never touches file bytes. S3 handles bandwidth. Multiple users uploading don't affect API performance. | Upload through API Server (becomes bottleneck, memory spikes) |
| 12 | Taskfile for monorepo | Language-agnostic YAML, checksum-based change detection, no framework lock-in, 15-minute learning curve | Turborepo (JS-only), Nx (overkill config), Make (arcane syntax) |
| 13 | Monorepo | Atomic cross-service changes, shared types, single docker-compose, one CI pipeline | Polyrepo (4 coordinated PRs for one feature, wiring overhead) |
| 14 | Two document states in UI | User cares about ready or not ready. Upload/queued/parsing/embedding are internal plumbing. | Five states (unnecessary cognitive load, noisy UI) |
| 15 | JSON parsing with bounding boxes | Citations need (x, y, width, height) coordinates to highlight exact text in rendered PDF | Text-only parsing (can cite page but can't highlight specific text) |

---

## Scale Estimates

### Assumptions

Average PDF: 2MB, 40 pages, ~50 chunks. LiteParse parse time: ~20s/doc. LLM call: ~10s/cell. Embedding batch: ~2s per doc.

### Projections

| Scale | Docs | Columns | Cells | Parse (5 workers) | Extract (5 workers) | S3 Storage | Vector Count |
|-------|------|---------|-------|--------------------|---------------------|------------|-------------|
| Small | 50 | 5 | 250 | ~3 min | ~8 min | 100 MB | 2,500 |
| Medium | 1K | 10 | 10K | ~1 hr | ~30 min | 2 GB | 50K |
| Large | 10K | 15 | 150K | ~10 hr | ~8 hr | 20 GB | 500K |
| Extreme | 100K | 20 | 2M | ~100 hr* | ~55 hr* | 200 GB | 5M |

*At 50 workers: ~10 hr parse, ~5.5 hr extract.

### Bottleneck Progression

| Scale | Bottleneck | Mitigation |
|-------|-----------|------------|
| <1K docs | Nothing — everything is fast | — |
| 1K–10K | Parsing time | Add Document Worker instances |
| 10K–50K | Extraction time + LLM API rate limits | Add Extraction Worker instances, request rate limit increases |
| 50K–100K | pgvector query latency, frontend rendering | Migrate to Qdrant, add pagination to API, virtualize table rows |
| 100K+ | LLM API cost (~$0.01-0.05/cell × 2M cells = $20K-100K) | Self-host models, batch pricing, selective extraction |

---

## Containers

| Container | Image Base | Purpose |
|-----------|-----------|---------|
| api-server | python:3.12-slim | All CRUD + queue publishing |
| extraction-worker | python:3.12-slim | LLM calls + RAG pipeline |
| document-worker | python:3.12-slim + node:18 | LiteParse + embeddings |
| sse-service | golang:1.22-alpine → scratch | SSE connections + Redis sub |
| frontend | node:18 → nginx | React SPA static files |
| postgres | postgres:16 + pgvector | Relational + vector data |
| redis | redis:7 | Queues + pub/sub |
| minio | minio/minio | S3-compatible object storage |

**Total: 5 application + 3 infrastructure = 8 containers.**
````

## File: DESIGN.md/DESIGN.md
````markdown
# Design System — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## Product Context

- **What this is:** AI-powered document review tool that extracts structured answers from PDFs with citation-backed reasoning
- **Who it's for:** Legal professionals — in-house counsel, law firm associates, contract analysts
- **Space/industry:** Legal tech, document intelligence, contract review
- **Project type:** Data-heavy web application (table-centric, document viewer, drawer panels)

---

## Aesthetic Direction

- **Direction:** Refined Professional — sophisticated but not cold, trustworthy but not boring
- **Decoration level:** Minimal — typography and spacing do the work, no decorative elements
- **Mood:** A senior associate's well-organized desk. Calm confidence. Everything has a place. The tool disappears, the work stays in focus.

---

## Typography

| Role | Font | Weight | Rationale |
|------|------|--------|-----------|
| Display/Hero | EB Garamond | 500-600 | Elegant serif signals legal, considered, trustworthy. Used sparingly for character. |
| Body | Source Serif 4 | 400, 600 | Coheres with EB Garamond. Legal professionals read documents all day — a serif body feels native to their work. |
| UI/Labels | Inter | 400, 500, 600 | Clean sans for interface elements, buttons, metadata. Stays out of the way. |
| Data/Tables | Inter | 400 | With `font-variant-numeric: tabular-nums` for aligned columns. |
| Code/Monospace | JetBrains Mono | 400 | For any code blocks, chunk IDs, or technical metadata. |

**Loading:**
```html
<link rel="preconnect" href="https://fonts.bunny.net">
<link href="https://fonts.bunny.net/css?family=eb-garamond:500,600|source-serif-4:400,600|inter:400,500,600" rel="stylesheet">
```

**Scale:**
```css
--text-xs: 0.75rem;    /* 12px — metadata, timestamps */
--text-sm: 0.875rem;   /* 14px — table cells, labels */
--text-base: 1rem;     /* 16px — body text */
--text-lg: 1.125rem;   /* 18px — drawer headings */
--text-xl: 1.25rem;    /* 20px — section titles */
--text-2xl: 1.5rem;    /* 24px — page titles */
--text-3xl: 2rem;      /* 32px — hero/table name */
```

---

## Color

**Approach:** Restrained — one accent, warm neutrals, color is rare and meaningful.

### Core Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--background` | `oklch(0.98 0.003 90)` · #faf9f7 | Page background, warm off-white |
| `--surface` | `oklch(1 0 0)` · #ffffff | Cards, table cells, elevated surfaces |
| `--surface-muted` | `oklch(0.96 0.003 90)` · #f5f3f0 | Hover states, secondary surfaces |
| `--foreground` | `oklch(0.145 0 0)` · #1a1a1a | Primary text |
| `--foreground-muted` | `oklch(0.556 0 0)` · #777777 | Secondary text, placeholders |
| `--border` | `oklch(0.922 0.003 90)` | Subtle dividers, card borders |
| `--border-strong` | `oklch(0.85 0.003 90)` | Emphasized borders, table headers |

### Action Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--primary` | `oklch(0 0 0)` · #000000 | Primary buttons, strong text |
| `--primary-foreground` | `oklch(1 0 0)` · #ffffff | Text on primary buttons |
| `--accent` | `oklch(0.55 0.15 55)` · #b45309 | Warm amber — Run button, key CTAs, active states |
| `--accent-foreground` | `oklch(1 0 0)` · #ffffff | Text on accent buttons |

### Semantic Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--success` | `oklch(0.55 0.15 145)` · #16a34a | Completed states, success messages |
| `--warning` | `oklch(0.7 0.15 85)` · #ca8a04 | Stale cells, attention needed |
| `--error` | `oklch(0.55 0.2 25)` · #dc2626 | Errors, failed states |
| `--info` | `oklch(0.55 0.12 250)` · #2563eb | Informational, links |

### Dark Mode Strategy

Invert surfaces (not hues). Reduce accent saturation by 15%. Keep contrast ratios above 4.5:1.

```css
[data-theme="dark"] {
  --background: oklch(0.13 0.003 90);
  --surface: oklch(0.18 0.003 90);
  --foreground: oklch(0.93 0 0);
  --foreground-muted: oklch(0.65 0 0);
  --accent: oklch(0.6 0.12 55);
}
```

---

## Spacing

- **Base unit:** 4px
- **Density:** Comfortable — data-heavy but not cramped

**Scale:**
```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

**Component spacing:**
- Table cell padding: `--space-3` vertical, `--space-4` horizontal
- Card padding: `--space-4` to `--space-6`
- Section gaps: `--space-6` to `--space-8`
- Page margins: `--space-6` mobile, `--space-8` desktop

---

## Layout

- **Approach:** Grid-disciplined — strict alignment for data-heavy interface
- **Max content width:** None for table view (full width), 1280px for settings/forms

**Layout States:**
```
TABLE_ONLY:           100% table
TABLE_AND_DRAWER:     60% table | 40% drawer (400px fixed)
DRAWER_AND_VIEWER:    30% drawer (320px) | 70% viewer
```

**Transitions:**
```css
transition: grid-template-columns 300ms ease-out;
```

**Border Radius:**
```css
--radius-sm: 4px;    /* inputs, chips, small elements */
--radius-md: 8px;    /* buttons, badges */
--radius-lg: 12px;   /* cards, panels, modals */
--radius-xl: 16px;   /* large containers */
--radius-full: 9999px; /* avatars, pills */
```

---

## Motion

- **Approach:** Minimal-functional — motion aids comprehension, never decorates

**Easing:**
```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);   /* enter, expand */
--ease-in: cubic-bezier(0.7, 0, 0.84, 0);    /* exit, collapse */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1); /* move, resize */
```

**Duration:**
```css
--duration-fast: 100ms;    /* micro-interactions, button press */
--duration-normal: 200ms;  /* hovers, state changes */
--duration-slow: 300ms;    /* panel transitions */
--duration-slower: 500ms;  /* row fade-in on doc ready */
```

**State Animations:**

| State | Animation |
|-------|-----------|
| Document parsing | `opacity: 0.4` + `animate-pulse` (gentle breathing) |
| Document ready | `transition: opacity 500ms ease-in` to `opacity: 1` |
| Cell extracting | `animate-pulse` with `bg-muted/50` (shimmer) |
| Cell completed | Fade-in answer text, 200ms |
| Panel open | Slide from right, 300ms ease-out |

---

## Component Patterns

### Buttons

| Variant | Background | Border | Text |
|---------|------------|--------|------|
| Primary | `--primary` | none | `--primary-foreground` |
| Accent | `--accent` | none | `--accent-foreground` |
| Secondary | `--surface` | `--border` | `--foreground` |
| Ghost | transparent | none | `--foreground-muted` |
| Destructive | `--error` | none | white |

### Cell States

| Status | Background | Border | Text | Other |
|--------|------------|--------|------|-------|
| `empty` | `--surface-muted` at 30% | dashed `--border` | — | — |
| `extracting` | `--surface-muted` at 50% | none | — | `animate-pulse` |
| `completed` | `--surface` | none | `--foreground` | — |
| `stale` | `--surface` | none | `--foreground` at 50% | "outdated" badge |
| `error` | `--error` at 10% | none | `--error` | — |

### Document Row States

| Status | Opacity | Animation |
|--------|---------|-----------|
| `not_ready` | 0.4 | `animate-pulse` |
| `ready` | 1.0 | `transition: opacity 500ms` |
| `error` | 0.4 | none, warning icon on hover |

---

## Shadows

Minimal shadow usage. Elevation through background color, not depth.

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.03);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.05);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.05);
```

Use shadows only for:
- Modals/dialogs (`--shadow-lg`)
- Dropdowns (`--shadow-md`)
- Sticky headers (`--shadow-sm`)

Cards and panels use border, not shadow.

---

## Icons

- **Library:** Lucide (consistent with shadcn/ui)
- **Size:** 16px default, 20px for emphasis, 24px for navigation
- **Stroke:** 1.5px (matches Inter's weight)
- **Color:** Inherit from text color

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-07-01 | EB Garamond for display | Serif signals legal/professional without being stuffy |
| 2025-07-01 | Source Serif 4 for body | Coheres with EB Garamond, native to document-heavy work |
| 2025-07-01 | Warm off-white background | Softer than pure white, reduces eye strain for long sessions |
| 2025-07-01 | Warm amber accent | One focal point for CTAs, restrained but distinctive |
| 2025-07-01 | 12px base border radius | Soft but not bubbly, appropriate for data-dense UI |
| 2025-07-01 | Minimal shadows | Elevation through color, not depth — cleaner for tables |
| 2025-07-01 | 500ms doc-ready transition | Gentle materialization, not jarring pop |

----

Save this as `docs/DESIGN.md` or root `DESIGN.md` — your call on where design docs live.

Two things I changed from frontend.md:
1. **Source Serif 4 for body** — coheres with EB Garamond, distinctive
2. **Warm amber accent** (`#b45309`) — one focal color for "Run" and primary CTAs

If you prefer to keep Inter for body and no accent (pure black/white), let me know and I'll revert those. The rest is your existing system, just structured and documented.
````

## File: frontend.md/frontend.md
````markdown
# Frontend — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## Responsibility

Single-page application. Renders the review table, memory drawer, and document viewer. Manages all client-side state. Connects to the API Server via REST and the SSE Service for real-time updates. No server-side rendering — static files served by Nginx.

## Tech Stack

- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **Package Manager:** pnpm
- **State:** Zustand
- **Table:** TanStack Table (headless, virtualized)
- **UI Components:** shadcn/ui (customized with June design system)
- **PDF Viewer:** react-pdf (pdf.js wrapper)
- **SSE Client:** Native browser `EventSource` API
- **HTTP Client:** Native `fetch` (no axios — unnecessary dependency)
- **Styling:** Tailwind CSS v4 (via shadcn)
- **Fonts:** EB Garamond (serif headings), Inter (sans body)

## Folder Structure

```
frontend/
├── Dockerfile
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── vite.config.ts
├── index.html
├── public/
└── src/
    ├── main.tsx                    ← React root, providers
    ├── App.tsx                     ← Router setup
    │
    ├── pages/
    │   ├── login.tsx               ← Sign in page
    │   ├── tables.tsx              ← Table list (home)
    │   └── table.tsx               ← Single table workspace (hero page)
    │
    ├── components/
    │   ├── ui/                     ← shadcn components (button, input, dialog, etc.)
    │   │
    │   ├── table/
    │   │   ├── table-header.tsx    ← Title, +Document, +Column, Run, save indicator
    │   │   ├── table-grid.tsx      ← TanStack Table wrapper
    │   │   ├── column-header.tsx   ← Title, type badge, edit/delete menu
    │   │   ├── document-cell.tsx   ← File name, icon, faded/solid states
    │   │   └── data-cell.tsx       ← Answer text, click handler, state styling
    │   │
    │   ├── drawer/
    │   │   ├── memory-drawer.tsx   ← Right panel, row-level column accordion
    │   │   ├── column-section.tsx  ← Answer + reasoning + source chips
    │   │   └── source-chip.tsx     ← Clickable citation badge
    │   │
    │   ├── viewer/
    │   │   ├── document-viewer.tsx ← PDF renderer + page nav + close
    │   │   └── highlight-overlay.tsx ← Positioned div for bbox highlighting
    │   │
    │   ├── forms/
    │   │   ├── column-form.tsx     ← Add/edit column (title + prompt + type)
    │   │   └── upload-button.tsx   ← File picker + upload orchestration
    │   │
    │   └── shared/
    │       ├── delete-dialog.tsx   ← Confirmation dialog for destructive actions
    │       └── save-indicator.tsx  ← "Saved" / "Saving..." subtle text
    │
    ├── stores/
    │   ├── table-store.ts          ← Table metadata, documents, columns, cells
    │   ├── ui-store.ts             ← Layout state, selected row/column, viewer state
    │   └── upload-store.ts         ← Upload queue, progress, concurrency management
    │
    ├── api/
    │   ├── client.ts               ← Base fetch wrapper (auth headers, error handling)
    │   ├── tables.ts               ← Table CRUD calls
    │   ├── documents.ts            ← Upload URL, confirm, file URL, chunks
    │   ├── columns.ts              ← Column CRUD calls
    │   ├── extraction.ts           ← Run, rerun calls
    │   └── jobs.ts                 ← Job status calls
    │
    ├── hooks/
    │   ├── use-sse.ts              ← SSE connection lifecycle + event routing
    │   ├── use-table.ts            ← Load table data, combines store + API
    │   └── use-upload.ts           ← Upload orchestration with concurrency control
    │
    ├── types/
    │   ├── api.ts                  ← API request/response types
    │   ├── models.ts               ← Table, Column, Cell, Document types
    │   └── events.ts               ← SSE event payload types
    │
    └── lib/
        ├── constants.ts            ← Column types, cell statuses, limits
        └── utils.ts                ← Formatters, key generators
```

## Component Tree

```
<App>
├── <LoginPage>                         ← /login
├── <TablesPage>                        ← / (table list)
│   ├── <TableCard>                     ← Each table in list
│   └── <CreateTableButton>
│
└── <TablePage>                         ← /tables/:id (hero page)
    │
    ├── <TableHeader>
    │   ├── <TableTitle>                ← Editable inline, auto-save on blur
    │   ├── <UploadButton>              ← File picker, multi-select
    │   ├── <AddColumnButton>           ← Opens <ColumnForm>
    │   ├── <RunButton>                 ← Disabled when nothing to run
    │   └── <SaveIndicator>
    │
    ├── <TableGrid>                     ← TanStack Table
    │   ├── <ColumnHeader>              ← Per column: title, type, menu
    │   └── <TableRow>                  ← Per document (virtualized)
    │       ├── <DocumentCell>          ← File name, faded/solid
    │       └── <DataCell>              ← Per column: answer or state
    │
    ├── <MemoryDrawer>                  ← Conditional: ui.layout !== "table_only"
    │   ├── <DrawerHeader>              ← Document name, close button
    │   └── <ColumnSection>             ← Per column, accordion
    │       ├── <Answer>
    │       ├── <Reasoning>
    │       └── <SourceChip>            ← Clickable → opens viewer
    │
    ├── <DocumentViewer>                ← Conditional: ui.layout === "drawer_and_viewer"
    │   ├── <ViewerHeader>              ← File name, page N/M, close
    │   ├── <PDFRenderer>               ← react-pdf canvas
    │   │   └── <HighlightOverlay>      ← Absolutely positioned divs on cited text
    │   └── <PageNavigation>            ← Prev / Next
    │
    ├── <ColumnForm>                    ← Modal: add or edit column
    └── <DeleteDialog>                  ← Modal: confirm destructive actions
```

## State Management

Three Zustand stores. Separated by concern and update frequency.

### table-store.ts — Data

```typescript
interface TableStore {
  // Table metadata
  table: {
    id: string
    name: string
    created_at: string
    updated_at: string
  } | null

  // Documents (rows) — ordered map
  documents: {
    order: string[]
    byId: Record<string, {
      id: string
      file_name: string
      file_type: string
      file_size: number
      page_count: number | null
      parse_status: "not_ready" | "ready" | "error"
    }>
  }

  // Columns — ordered map
  columns: {
    order: string[]
    byId: Record<string, {
      id: string
      title: string
      prompt: string
      type: "free_response" | "yes_no" | "date" | "currency" | "verbatim"
      order: number
    }>
  }

  // Cells — flat map keyed by "doc_id::col_id"
  cells: Record<string, {
    id: string
    document_id: string
    column_id: string
    status: "empty" | "extracting" | "completed" | "stale" | "error"
    answer: string | null
    reasoning: string | null
    source_references: {
      chunk_id: string
      page: number
      section: string
      quote: string
    }[] | null
    error_message: string | null
  }>

  // Save status
  saveStatus: "saved" | "saving" | "error"

  // Actions
  loadTable: (tableId: string) => Promise<void>
  renameTable: (name: string) => Promise<void>
  addDocument: (doc: Document) => void
  updateDocumentStatus: (docId: string, status: string, pageCount?: number) => void
  addColumn: (column: Column) => Promise<void>
  updateColumn: (colId: string, updates: Partial<Column>) => Promise<void>
  deleteColumn: (colId: string) => Promise<void>
  deleteDocument: (docId: string) => Promise<void>
  updateCell: (docId: string, colId: string, cellData: CellData) => void
  setCellsExtracting: (cellKeys: string[]) => void
  markColumnStale: (colId: string) => void
}
```

**Cell key pattern:** `"doc_001::col_003"` — O(1) lookup. When SSE delivers a `cell_completed` event, the handler does `cells[`${doc_id}::${col_id}`] = newData`. When the Memory Drawer needs all cells for a document, it filters by prefix — fast enough for hundreds of cells.

**Why ordered maps:** `documents.order` and `columns.order` are arrays of IDs that define display order. `byId` is a record for O(1) lookup by ID. This lets us reorder (V1.1) by swapping array elements without touching the data records.

### ui-store.ts — View State

```typescript
interface UIStore {
  // Layout state machine
  layout: "table_only" | "table_and_drawer" | "drawer_and_viewer"

  // Selection
  selectedRow: string | null       // document_id
  selectedColumn: string | null    // column_id

  // Document viewer
  viewerDocumentId: string | null
  viewerPage: number | null
  viewerHighlight: {
    chunkId: string
    page: number
    quote: string
  } | null

  // Run status
  runStatus: "idle" | "running" | "completed"
  runProgress: { completed: number; total: number } | null

  // Actions
  selectCell: (docId: string, colId: string) => void
  openViewer: (docId: string, chunkId: string, page: number, quote: string) => void
  closeViewer: () => void
  closeDrawer: () => void
}
```

**State transitions:**

```
selectCell(docId, colId):
  if layout === "table_only" → set layout to "table_and_drawer"
  if layout === "table_and_drawer" → stay (update selected row/col)
  if layout === "drawer_and_viewer" → close viewer, stay in "table_and_drawer"
  set selectedRow = docId, selectedColumn = colId

openViewer(docId, chunkId, page, quote):
  set layout to "drawer_and_viewer"
  set viewerDocumentId, viewerPage, viewerHighlight

closeViewer():
  set layout to "table_and_drawer"
  clear viewer state

closeDrawer():
  set layout to "table_only"
  clear selectedRow, selectedColumn
```

### upload-store.ts — Upload Queue

```typescript
interface UploadStore {
  // Queue
  pendingFiles: File[]
  activeUploads: Map<string, {
    file: File
    docId: string | null
    progress: number
  }>

  // Config
  maxConcurrent: 5

  // Actions
  startUpload: (files: File[], tableId: string) => void
  onProgress: (docId: string, progress: number) => void
  onComplete: (docId: string) => void
  onError: (docId: string, error: string) => void
}
```

Upload flow per file:
1. `POST /api/documents/upload-url` → get presigned URL + doc_id
2. `PUT` file to presigned URL (track progress via XMLHttpRequest)
3. `POST /api/documents/{doc_id}/confirm` → enqueues parsing
4. Remove from activeUploads, pull next from pendingFiles
5. Row is already in table-store (added at step 1), faded until SSE `doc_ready`

Max 5 concurrent uploads. Files beyond 5 wait in `pendingFiles`.

## SSE Hook

```typescript
// hooks/use-sse.ts

function useSSE(tableId: string) {
  useEffect(() => {
    const source = new EventSource(`/api/tables/${tableId}/events`)

    source.addEventListener("doc_ready", (e) => {
      const data = JSON.parse(e.data)
      tableStore.updateDocumentStatus(data.document_id, "ready", data.page_count)
    })

    source.addEventListener("doc_error", (e) => {
      const data = JSON.parse(e.data)
      tableStore.updateDocumentStatus(data.document_id, "error")
    })

    source.addEventListener("cell_completed", (e) => {
      const data = JSON.parse(e.data)
      tableStore.updateCell(data.document_id, data.column_id, {
        id: data.cell_id,
        status: "completed",
        answer: data.answer,
        reasoning: data.reasoning,
        source_references: data.source_references,
      })
    })

    source.addEventListener("cell_error", (e) => {
      const data = JSON.parse(e.data)
      tableStore.updateCell(data.document_id, data.column_id, {
        id: data.cell_id,
        status: "error",
        error_message: data.error,
      })
    })

    source.addEventListener("run_completed", (e) => {
      const data = JSON.parse(e.data)
      uiStore.setRunStatus("completed", data)
    })

    return () => source.close()
  }, [tableId])
}
```

`EventSource` auto-reconnects on connection drop. On reconnect, the frontend should call `GET /api/tables/{id}` to hydrate any events missed during downtime.

## Layout System

CSS Grid with conditional templates controlled by `ui.layout`:

```
table_only:
┌──────────────────────────────────┐
│           TABLE (100%)           │
└──────────────────────────────────┘
grid-template-columns: 1fr

table_and_drawer:
┌────────────────────┬─────────────┐
│    TABLE (60%)     │ DRAWER (40%)│
└────────────────────┴─────────────┘
grid-template-columns: 1fr 400px

drawer_and_viewer:
┌───────────┬──────────────────────┐
│DRAWER(30%)│    VIEWER (70%)      │
└───────────┴──────────────────────┘
grid-template-columns: 320px 1fr
Table is hidden (display: none on the grid item)
```

Transitions: `transition: grid-template-columns 300ms ease-out` for smooth resizing. Drawer slides in from right. Viewer slides in from right while table slides out.

## Document Viewer — Bounding Box Highlighting

When user clicks a source chip:

```
1. Get chunk bounding box data:
   GET /api/documents/{doc_id}/chunks/{chunk_id}
   → { bbox: { page_width, page_height, items: [...] } }

2. Load PDF (if not cached):
   GET /api/documents/{doc_id}/file → presigned URL
   → fetch PDF, cache blob in memory

3. Render page with react-pdf:
   <Page pageNumber={viewerPage} width={containerWidth} />

4. Calculate scale factor:
   scale = renderedWidth / bbox.page_width

5. For each bbox item, render highlight overlay:
   <div style={{
     position: "absolute",
     left: item.x * scale,
     top: item.y * scale,
     width: item.width * scale,
     height: item.height * scale,
     backgroundColor: "rgba(255, 200, 50, 0.25)",
     borderRadius: 2,
     pointerEvents: "none"
   }} />
```

PDF blobs are cached in a `Map<string, Blob>` in memory. Clicking a source from the same document reuses the cached blob — instant page navigation. Clicking a source from a different document fetches a new blob.

## Design System

Theme applied via shadcn CSS variables in `globals.css`. Full theme definition is in the codebase — key mappings:

| Design Token | Tailwind Class | Value |
|-------------|----------------|-------|
| Text primary (#1a1a1a) | `text-foreground` | oklch(0.145 0 0) |
| Text muted (#999999) | `text-muted-foreground` | oklch(0.645 0 0) |
| Background (#faf9f7) | `bg-background` | oklch(0.98 0.003 90) |
| Card surface (#ffffff) | `bg-card` | oklch(1 0 0) |
| Primary action (#000000) | `bg-primary` | oklch(0 0 0) |
| Subtle surface (#f5f3f0) | `bg-secondary` | oklch(0.96 0.003 90) |
| Border (rgba(0,0,0,0.08)) | `border-border` | oklch(0.922 0.003 90) |
| Radius base (12px) | `rounded-lg` | --radius: 0.75rem |

**Font usage:** `font-serif` (EB Garamond) for table title and drawer document name. `font-sans` (Inter) for everything else.

**Cell state styling:**

| Status | Visual |
|--------|--------|
| `empty` | `bg-muted/30 border-dashed border-border` — faded dashed outline |
| `extracting` | `animate-pulse bg-muted/50` — gentle shimmer |
| `completed` | `bg-card text-foreground` — full color, answer text visible |
| `stale` | `opacity-50` + small "outdated" badge — dimmed previous answer |
| `error` | `bg-destructive/10 text-destructive` — light red tint |

**Document row states:**

| Status | Visual |
|--------|--------|
| `not_ready` | `opacity-40 animate-pulse` — faded with subtle breathing |
| `ready` | `opacity-100 transition-opacity duration-500` — smooth fade to solid |
| `error` | `opacity-40` + `⚠️` icon — faded, pulse stops, warning on hover |

Transition from not_ready to ready: `transition: opacity 500ms ease-in`. No jarring pop. The row gently materializes.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Escape` | Close viewer → close drawer → deselect (cascading) |
| `↑` / `↓` | Navigate rows (move selected row up/down) |
| `←` / `→` | Navigate columns (move selected column, scroll drawer) |
| `Enter` | On selected cell: open source if available |

## Performance Considerations

- **Table virtualization.** TanStack Table with virtualized rows. Only renders visible rows + buffer. Handles 10,000 rows without DOM bloat.
- **Cell lookup is O(1).** Flat map keyed by `"doc_id::col_id"`. No nested loops to find a cell.
- **Memory Drawer reads from local state.** Zero API calls on cell click. Zero API calls on row change. Data is already in the Zustand store.
- **PDF caching.** Loaded PDFs stay in memory as blobs. Switching between sources from the same document is instant.
- **SSE updates are surgical.** Each event updates exactly one cell or one document status. No full table re-fetch. React re-renders only the affected component via Zustand selector subscriptions.
- **Optimistic updates.** Column add, document add, rename — UI updates immediately, API call in background. Revert on error (rare).
````

## File: infrastructure.md/infrastructure.md
````markdown
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

    location /api/jobs/ {
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

Published by API Server when user clicks Run or Re-run. Consumed by Extraction Worker.

```json
{
  "task_id": "task_002",
  "job_id": "job_xyz",
  "table_id": "tbl_abc123",
  "cell_id": "cell_xyz",
  "document_id": "doc_001",
  "column_id": "col_003",
  "column_title": "Liability Cap",
  "column_prompt": "What is the aggregate liability cap?",
  "column_type": "currency",
  "retry_count": 0
}
```

Column details embedded in task so worker never queries column metadata.

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
| `run_completed` | API Server | `table:{table_id}` | `{ type, job_id, table_id, total, completed, failed }` |

`run_completed` is published by the API Server when it detects `completed_cells + failed_cells = total_cells` during a cell save callback.

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
````

## File: local-setup.md/local-setup.md
````markdown
# Local Setup — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Docker + Compose | 24+ | [docker.com](https://docs.docker.com/get-docker/) |
| Node.js | 18+ | `brew install node` |
| Python | 3.12+ | `brew install python@3.12` |
| Go | 1.22+ | `brew install go` |
| pnpm | 9+ | `npm install -g pnpm` |
| Task | 3+ | `brew install go-task` |

## Setup

```bash
git clone https://github.com/june-legal/review-table.git
cd review-table
cp .env.example .env
# Add your OpenAI API key to .env:  OPENAI_API_KEY=sk-...
task dev
```

This starts all 8 containers. First run pulls images and builds — takes 2-3 minutes. Subsequent runs start in seconds.

## Verify

| Service | URL | What You Should See |
|---------|-----|---------------------|
| App | http://localhost:3000 | Login page |
| API | http://localhost:8000/docs | FastAPI Swagger UI |
| MinIO Console | http://localhost:9001 | Storage browser (minioadmin/minioadmin) |

## Seed Test Data

```bash
task seed
```

Creates a test workspace, a test user (test@june-legal.com / password), a sample table with 3 PDFs and 2 columns. Useful for frontend development without manually uploading files.

## Useful Commands

```bash
task dev              # Start everything
task dev:stop         # Stop everything
task api:dev          # Run API server only (with hot reload)
task api:test         # Run API server tests
task api:migrate      # Run database migrations
task ext:test         # Run extraction worker tests
task doc:test         # Run document worker tests
task sse:test         # Run SSE service tests
task frontend:dev     # Run frontend dev server only
task frontend:test    # Run frontend tests
task build            # Build all Docker images
task seed             # Seed test data
task db:reset         # Drop and recreate database
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 5432 already in use | Local Postgres running. Stop it: `brew services stop postgresql` |
| MinIO bucket not found | Run `task seed` or create manually: `mc mb local/june-documents` |
| LiteParse not found | Ensure Node.js is installed in document-worker container. Rebuild: `task build` |
| SSE events not arriving | Check Redis is running: `docker compose logs redis`. Check SSE service: `docker compose logs sse-service` |
| Migrations not applied | Run `task api:migrate`. If stuck, `task db:reset` then `task api:migrate` |
````

## File: product.md/product.md
````markdown
# Product — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## What

June Review Table is an AI-powered document review tool for legal professionals. Users upload PDFs, define questions as columns, and the AI extracts answers from every document — each answer backed by reasoning and exact source citations with highlighted text in the original PDF.

## Who

In-house legal teams, law firm associates, and contract analysts who review large sets of documents under time pressure — M&A due diligence, lease audits, NDA reviews, regulatory filings.

## Principles

- **Every cell is a triad:** answer + reasoning + source reference. All three or nothing.
- **No manual cell editing.** If the AI is wrong, re-run. The trust chain stays intact.
- **Auto-save always.** No save button. Every action persists immediately.
- **Progressive results.** Cells fill in as they complete. No waiting for "all done."
- **Agent-ready APIs.** Every action the UI does, an AI agent can do via the same endpoint.

---

## User Journey

User creates a table → uploads PDFs (rows appear faded with a subtle pulse, become solid when parsed) → adds columns by writing a title, a natural language prompt, and selecting a type (free response, yes/no, date, currency, verbatim) → clicks Run → cells fill in progressively as extraction completes, each with a shimmer-to-content transition → clicks any cell to open the Memory Drawer showing answer, reasoning, and source chips for every column of that document → clicks a source chip to open the Document Viewer with the PDF scrolled to the exact page and the cited text highlighted with bounding-box precision → presses Escape to return to the table.

### Layout States

```
TABLE ONLY ──click cell──▶ TABLE + MEMORY DRAWER ──click source──▶ MEMORY DRAWER + DOC VIEWER
   (100%)                     (60%)    (40%)                          (30%)         (70%)
                                  │                                       │
                          click [✕]│                               Esc / [✕]
                                  ▼                                       ▼
                             TABLE ONLY ◄──────────────────── TABLE + MEMORY DRAWER
```

---

## Workspace Model

All data — tables, documents, cells — is scoped to a workspace, not a user. Each user belongs to a workspace created on first sign-in. Multi-workspace support and team invites are V2.

**Auth flow:** `june-legal.com` (landing page) → sign in → `app.june-legal.com` → workspace.

---

## V1 Scope

### In

```
Tables:       Create, rename, delete, list, auto-save
Documents:    Multi-file upload, delete (confirmation), two UI states (faded → solid)
Columns:      Add (title + prompt + type), edit (marks cells stale), delete
Extraction:   Global Run, progressive cell population via SSE, cell re-run, column re-run
Cell:         Click → Memory Drawer (answer + reasoning + sources), row-level, accordion
Doc Viewer:   Load PDF from S3, scroll to page, highlight cited text via bounding boxes
Column Types: Free Response, Yes/No, Date, Currency, Verbatim
```

### Out (designed for, not building now)

```
AI Column Builder          Library / Vault             Templates
Chat over table            Collaboration               Risk scoring
Export                     Workflows                   Portal / sharing
Filter / Sort              Column reorder              Manual cell editing
```

### V1.1 (fast-follow)

```
Filter by column value     Sort by column
Export to CSV              Column drag-and-drop reorder
```

---

## Future

Chat over table data with citations back to cells and documents. Document editor with AI suggestions and playbook-based redlining. Visual workflow builder for repeatable multi-step processes. Collaboration with assignments, flags, and comments. Library/Vault for persistent document storage across tables.

---

## Key Product Decisions

| Decision | Rule | Reasoning |
|----------|------|-----------|
| No cell editing | Users re-run, never manually edit | Answer + reasoning + source are bonded. Editing one breaks the others. |
| Two document states | Faded (not ready) → solid (ready) | Users don't care about upload/parse/embed internals. Ready or not. |
| Column edit → stale | Editing a prompt dims all cells in that column | Old answers don't match new prompt. Visual signal prevents confusion. |
| Row-level Memory Drawer | Clicking any cell shows all columns for that document | Avoids repeated open/close. One click gives full document context. |
| Table hides in doc viewer | State 3 is Memory Drawer + Doc Viewer only | Three panels is too cramped. Two-panel max for comfortable reading. |
| Auto-save only | No save button exists anywhere | Eliminates "did I save?" anxiety. Every mutation persists immediately. |
| Soft delete backend | UI treats delete as permanent, DB uses deleted_at | Recovery capability without confusing the user with undo complexity. |
````

## File: README.md/README.md
````markdown
# June — Review Table

AI-powered document review with verifiable citations. Upload PDFs, define extraction columns, and let AI populate every cell with answers, reasoning, and exact source references — all auto-saved, all verifiable, all agent-ready.

![alt text](docs/image.png)
## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API Server | Python / FastAPI | Best CRUD framework, Pydantic validation, AI ecosystem |
| Extraction Worker | Python | OpenAI/Anthropic SDKs, RAG pipeline, IO-bound |
| Document Worker | Python + LiteParse | Local PDF parsing with OCR + bounding boxes for citations |
| SSE Service | Go | Goroutines, 2KB/connection, purpose-built for long-lived connections |
| Frontend | React / TypeScript / shadcn | Type safety, component library, Zustand state |
| Database | PostgreSQL + pgvector | Relational data + vector similarity search in one |
| Queue / Events | Redis | Task queues + pub/sub for real-time events |
| Storage | S3 / MinIO | PDF storage, presigned URL uploads |
| Monorepo | Taskfile | Language-agnostic task runner, no framework lock-in |

## Docs

| Document | Description |
|----------|-------------|
| [Product](docs/product.md) | What we're building, for whom, scope, user journey |
| [Architecture](docs/architecture.md) | System design, data flows, decisions, scale estimates |
| [API Reference](docs/api.md) | Every endpoint — request, response, status codes |
| [Database Schema](docs/schema.md) | Tables, columns, types, indexes, relationships |
| [API Server](docs/services/api-server.md) | FastAPI internals, route organization, config |
| [Document Worker](docs/services/document-worker.md) | LiteParse pipeline, chunking, embeddings |
| [Extraction Worker](docs/services/extraction-worker.md) | RAG pipeline, LLM prompts, cell extraction |
| [SSE Service](docs/services/sse-service.md) | Go service, connection management, event routing |
| [Frontend](docs/frontend.md) | Components, state, layout system, design system |
| [Infrastructure](docs/infrastructure.md) | Docker, Redis queues, S3, event catalog |
| [Local Setup](docs/guides/local-setup.md) | Clone to running in 5 minutes |

## Quick Start

```bash
git clone https://github.com/june-legal/review-table.git
cd review-table
cp .env.example .env
task dev
# Open http://localhost:3000
```
````

## File: schema.md/schema.md
````markdown
# Database Schema — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

PostgreSQL 16 with pgvector extension. Single database, schema ownership split between API Server (relational tables) and Document Worker (vector data).

---

## Entity Relationships

```
workspaces
    │
    ├──< tables
    │       │
    │       ├──< columns
    │       │
    │       ├──< table_documents >── documents
    │       │                            │
    │       └──< cells                   └──< document_chunks (pgvector)
    │              │
    │              └── references: documents, columns
    │
    └──< users

jobs ── references: tables

Legend: ──< = one-to-many    >── = many-to-many join table
```

---

## Tables

### workspaces

```
| Column      | Type        | Constraints              |
|-------------|-------------|--------------------------|
| id          | UUID        | PK, DEFAULT gen_random_uuid() |
| name        | VARCHAR(255)| NOT NULL                 |
| created_at  | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| updated_at  | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
```

No soft delete — workspaces are permanent in V1.

---

### users

```
| Column        | Type        | Constraints              |
|---------------|-------------|--------------------------|
| id            | UUID        | PK, DEFAULT gen_random_uuid() |
| workspace_id  | UUID        | FK → workspaces.id, NOT NULL |
| email         | VARCHAR(255)| NOT NULL, UNIQUE         |
| name          | VARCHAR(255)| NOT NULL                 |
| password_hash | VARCHAR(255)| NOT NULL                 |
| created_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| updated_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |

Indexes:
  (workspace_id)
  (email) UNIQUE
```

Auth is minimal in V1. Password hash via bcrypt. JWT or session-based auth can be swapped in later without schema changes.

---

### tables

```
| Column       | Type        | Constraints              |
|--------------|-------------|--------------------------|
| id           | UUID        | PK, DEFAULT gen_random_uuid() |
| workspace_id | UUID        | FK → workspaces.id, NOT NULL |
| name         | VARCHAR(255)| NOT NULL                 |
| created_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| updated_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| deleted_at   | TIMESTAMPTZ | nullable                 |

Indexes:
  (workspace_id, deleted_at)  — list tables for a workspace, exclude deleted
```

Soft delete via `deleted_at`. All queries filter `WHERE deleted_at IS NULL`.

---

### columns

```
| Column     | Type        | Constraints              |
|------------|-------------|--------------------------|
| id         | UUID        | PK, DEFAULT gen_random_uuid() |
| table_id   | UUID        | FK → tables.id, NOT NULL |
| title      | VARCHAR(255)| NOT NULL                 |
| prompt     | TEXT        | NOT NULL                 |
| type       | VARCHAR(50) | NOT NULL                 |
| "order"    | INTEGER     | NOT NULL                 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |

Indexes:
  (table_id, "order")  — fetch columns for a table in display order

CHECK constraint on type:
  type IN ('free_response', 'yes_no', 'date', 'currency', 'verbatim')
```

`"order"` is quoted because it's a reserved word. Auto-assigned as `max(order) + 1` on insert. Column reorder (V1.1) updates these values.

---

### documents

```
| Column       | Type        | Constraints              |
|--------------|-------------|--------------------------|
| id           | UUID        | PK, DEFAULT gen_random_uuid() |
| workspace_id | UUID        | FK → workspaces.id, NOT NULL |
| file_name    | VARCHAR(255)| NOT NULL                 |
| file_type    | VARCHAR(50) | NOT NULL                 |
| file_key     | VARCHAR(500)| NOT NULL                 |
| file_size    | BIGINT      | NOT NULL                 |
| page_count   | INTEGER     | nullable                 |
| parse_status | VARCHAR(20) | NOT NULL, DEFAULT 'not_ready' |
| error_message| TEXT        | nullable                 |
| created_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| updated_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| deleted_at   | TIMESTAMPTZ | nullable                 |

Indexes:
  (workspace_id, deleted_at)  — list documents, exclude deleted
  (parse_status)              — find documents needing processing

CHECK constraint on parse_status:
  parse_status IN ('not_ready', 'ready', 'error')
```

`file_key` is the S3 object key: `documents/{doc_id}/{file_name}`.

`page_count` is null until parsing completes, then set by the Document Worker.

Documents are workspace-scoped so they can be shared across tables in the future (Library/Vault feature).

---

### table_documents

Join table — which documents are in which tables.

```
| Column      | Type        | Constraints              |
|-------------|-------------|--------------------------|
| id          | UUID        | PK, DEFAULT gen_random_uuid() |
| table_id    | UUID        | FK → tables.id, NOT NULL |
| document_id | UUID        | FK → documents.id, NOT NULL |
| row_order   | INTEGER     | NOT NULL                 |
| added_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |

Indexes:
  (table_id, row_order)               — fetch docs for a table in order
  (table_id, document_id) UNIQUE      — prevent duplicate association
  (document_id)                       — find all tables containing a document
```

`row_order` determines the row position in the table. Auto-assigned as `max(row_order) + 1` on insert.

---

### cells

```
| Column           | Type        | Constraints              |
|------------------|-------------|--------------------------|
| id               | UUID        | PK, DEFAULT gen_random_uuid() |
| table_id         | UUID        | FK → tables.id, NOT NULL |
| document_id      | UUID        | FK → documents.id, NOT NULL |
| column_id        | UUID        | FK → columns.id, NOT NULL |
| status           | VARCHAR(20) | NOT NULL, DEFAULT 'empty' |
| answer           | TEXT        | nullable                 |
| reasoning        | TEXT        | nullable                 |
| source_references| JSONB       | nullable                 |
| error_message    | TEXT        | nullable                 |
| created_at       | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| updated_at       | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |

Indexes:
  (table_id, document_id, column_id) UNIQUE  — one cell per doc×column
  (table_id, status)                         — find empty/stale cells for Run
  (document_id)                              — get all cells for a document (Memory Drawer)
  (column_id)                                — get all cells for a column (column re-run)

CHECK constraint on status:
  status IN ('empty', 'extracting', 'completed', 'stale', 'error')
```

`source_references` JSONB shape:

```json
[
  {
    "chunk_id": "chunk_abc",
    "page": 1,
    "section": "Preamble",
    "quote": "This Master Services Agreement is entered into between..."
  }
]
```

Cell lifecycle: `empty` → `extracting` → `completed` / `error`. On column edit: `completed` → `stale`. On re-run: `stale` → `extracting` → `completed` / `error`.

When a column is added, empty cell records are batch-inserted for every document in the table. When a document is added, empty cell records are batch-inserted for every column in the table. This ensures the cell matrix is always complete.

---

### jobs

```
| Column          | Type        | Constraints              |
|-----------------|-------------|--------------------------|
| id              | UUID        | PK, DEFAULT gen_random_uuid() |
| table_id        | UUID        | FK → tables.id, NOT NULL |
| total_cells     | INTEGER     | NOT NULL                 |
| completed_cells | INTEGER     | NOT NULL, DEFAULT 0      |
| failed_cells    | INTEGER     | NOT NULL, DEFAULT 0      |
| status          | VARCHAR(20) | NOT NULL, DEFAULT 'running' |
| created_at      | TIMESTAMPTZ | NOT NULL, DEFAULT now()  |
| completed_at    | TIMESTAMPTZ | nullable                 |

Indexes:
  (table_id, status)  — find active jobs for a table

CHECK constraint on status:
  status IN ('running', 'completed', 'failed')
```

Job is marked `completed` when `completed_cells + failed_cells = total_cells`. Updated atomically by the API Server as each cell result is saved.

---

## Vector Data (pgvector)

### document_chunks

Stored in the same PostgreSQL database using the pgvector extension. This is the only table queried for RAG retrieval.

```
| Column       | Type          | Constraints              |
|--------------|---------------|--------------------------|
| id           | UUID          | PK, DEFAULT gen_random_uuid() |
| document_id  | UUID          | FK → documents.id, NOT NULL |
| chunk_index  | INTEGER       | NOT NULL                 |
| text_content | TEXT          | NOT NULL                 |
| page_number  | INTEGER       | NOT NULL                 |
| section      | VARCHAR(255)  | nullable                 |
| bbox         | JSONB         | NOT NULL                 |
| embedding    | VECTOR(1536)  | NOT NULL                 |
| created_at   | TIMESTAMPTZ   | NOT NULL, DEFAULT now()  |

Indexes:
  (document_id, chunk_index)                  — fetch chunks for a document in order
  HNSW on embedding (vector_cosine_ops)       — approximate nearest neighbor search
```

`bbox` JSONB shape:

```json
{
  "page_width": 612,
  "page_height": 792,
  "items": [
    { "text": "aggregate liability", "x": 72, "y": 485, "width": 120, "height": 12 },
    { "text": "shall not exceed", "x": 195, "y": 485, "width": 100, "height": 12 }
  ]
}
```

Coordinates are in PDF points (1 point = 1/72 inch). Origin is top-left. Frontend scales by `render_dpi / 72` for pixel positioning.

Embedding dimension is 1536 (OpenAI `text-embedding-3-small`). If embedding model changes, dimension changes — this requires re-embedding all chunks and updating the vector index.

RAG query pattern:

```sql
SELECT id, chunk_index, text_content, page_number, section, bbox,
       1 - (embedding <=> $1) AS similarity_score
FROM document_chunks
WHERE document_id = $2
ORDER BY embedding <=> $1
LIMIT $3
```

`<=>` is the cosine distance operator. HNSW index makes this sub-100ms even at 500K vectors.

---

## Schema Initialization

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

---

## Migration Strategy

Alembic (Python) manages all migrations. Migration files live in `services/api-server/alembic/versions/`.

Naming convention: `{timestamp}_{description}.py` (e.g., `20250701_001_initial_schema.py`).

Rules:
- Every migration must be reversible (implement `upgrade()` and `downgrade()`).
- Never modify a published migration. Always create a new one.
- Data migrations separate from schema migrations.
- Run via `task migrate` (which calls `alembic upgrade head`).
````

## File: services/api-server.md/api-server.md
````markdown
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
````

## File: services/document-worker.md/document-worker.md
````markdown
# Document Worker — Service Design

*Last updated: 2025-07-01 · Status: Active*

---

## Responsibility

Background queue consumer that turns raw PDFs into searchable, citation-ready content. Downloads PDFs from S3, parses with LiteParse (local OCR + layout extraction), chunks text while preserving bounding box coordinates, generates vector embeddings, stores chunks in pgvector via the API Server, and publishes SSE events when done. Has no HTTP endpoints — it only consumes from Redis and calls other services.

## Tech Stack

- **Runtime:** Python 3.12
- **PDF Parsing:** LiteParse (Python wrapper over Node.js CLI)
- **Embeddings:** OpenAI `text-embedding-3-small` (abstracted for swap)
- **Queue:** Redis via aioredis (BRPOP consumer)
- **Events:** Redis pub/sub (PUBLISH)
- **HTTP Client:** httpx (async, calls API Server)
- **S3:** boto3 (download files)

## Folder Structure

```
services/document-worker/
├── Dockerfile
├── pyproject.toml
└── app/
    ├── main.py                 ← Entry point: start consumer loop
    ├── config.py               ← Settings from env vars
    ├── consumer.py             ← Redis queue consumer loop
    ├── handler.py              ← Orchestrates the full pipeline for one document
    │
    ├── parsing/
    │   ├── parser.py           ← LiteParse wrapper, abstracts parsing interface
    │   └── chunker.py          ← Split parsed pages into chunks with bbox mapping
    │
    ├── embedding/
    │   └── client.py           ← Embedding API abstraction (OpenAI / Cohere / internal)
    │
    └── clients/
        ├── api_client.py       ← HTTP client for API Server (store chunks, update status)
        ├── s3_client.py        ← Download files from S3
        └── redis_client.py     ← Redis connection, publish events
```

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `API_SERVER_URL` | API Server base URL | `http://api-server:8000` |
| `S3_ENDPOINT_URL` | MinIO/S3 endpoint | `http://minio:9000` |
| `S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `S3_SECRET_KEY` | S3 secret key | `minioadmin` |
| `S3_BUCKET_NAME` | Bucket name | `june-documents` |
| `EMBEDDING_PROVIDER` | Which embedding API to use | `openai` |
| `OPENAI_API_KEY` | OpenAI API key (if provider is openai) | `sk-...` |
| `EMBEDDING_MODEL` | Model name | `text-embedding-3-small` |
| `EMBEDDING_DIMENSION` | Vector dimension | `1536` |
| `MAX_CONCURRENT_PARSES` | Concurrent docs per instance | `1` |
| `MAX_CONCURRENT_EMBEDS` | Concurrent embedding API calls | `5` |
| `MAX_RETRIES` | Retry count before giving up | `3` |
| `QUEUE_NAME` | Redis queue to consume | `document_parsing` |

## Dockerfile

Requires both Python and Node.js since LiteParse Python wrapper calls the Node.js CLI:

```dockerfile
FROM python:3.12-slim

# Install Node.js for LiteParse CLI
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install LiteParse CLI globally
RUN npm install -g @llamaindex/liteparse

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app/ app/
CMD ["python", "-m", "app.main"]
```

## Key Implementation Notes

**Consumer loop.** The worker runs an infinite async loop using `BRPOP` on the `document_parsing` queue. When a task arrives, it calls the handler. On completion or failure, it loops back to wait for the next task.

```
while True:
    task = await redis.brpop("document_parsing")
    try:
        await handle_document(task)
    except Exception:
        await handle_failure(task)
```

**Concurrency control.** LiteParse is CPU-bound (OCR parallelizes across cores internally). Running multiple parses concurrently on the same instance causes CPU contention and slows everything down. Default is `MAX_CONCURRENT_PARSES=1` — one document at a time per instance. Scale by adding more instances, not more concurrency.

Embedding API calls are IO-bound and use a separate semaphore (`MAX_CONCURRENT_EMBEDS=5`) since they can safely overlap.

**The pipeline for one document:**

```
1. PUBLISH doc_processing event (frontend shows "Processing ⚙️")

2. Download PDF from S3
   s3_client.download(file_key) → bytes in memory
   (~1-5 seconds depending on file size)

3. Parse with LiteParse
   parser.parse(pdf_bytes, output_format="json", ocr_enabled=True, dpi=150)
   Returns: pages with text + text_items (bounding boxes)
   (~5-30 seconds, CPU-intensive)

4. Chunk parsed pages
   chunker.chunk(parsed_pages) → list of chunks
   Each chunk: { text, page_number, section, chunk_index, bbox }
   (~instant, <100ms)

5. Generate embeddings
   embedding_client.embed([chunk.text for chunk in chunks])
   Batched: up to 2048 texts per API call
   (~1-5 seconds)

6. Store chunks via API Server
   POST /api/documents/{doc_id}/chunks
   Body: chunks with text + bbox + embedding vectors
   (~100-500ms)

7. Update document status via API Server
   PATCH /api/documents/{doc_id}
   Body: { parse_status: "ready", page_count: N }
   (~50ms)

8. PUBLISH doc_ready event
   { type: "doc_ready", document_id, table_id, page_count }
   Frontend: row transitions from faded to solid
```

**Chunking strategy.** Page-based with paragraph splitting for long pages:

```
For each page in parsed document:
    if page text < 1000 tokens:
        → one chunk = entire page
        → chunk.bbox = all text_items from that page
    else:
        → split at paragraph boundaries (double newline)
        → each sub-chunk carries only the text_items 
          that fall within its text range
        → chunk.page_number stays the same (same page, multiple chunks)
```

Every chunk preserves its bounding box items so the frontend can highlight the exact text region when a citation references that chunk.

**Parser abstraction.** The `parser.py` wraps LiteParse behind an interface so swapping parsers requires changing one file:

```
class DocumentParser(ABC):
    async def parse(self, pdf_bytes: bytes) -> ParsedDocument

class LiteParseParser(DocumentParser):
    # Current implementation — calls LiteParse CLI via Python wrapper

class LlamaParseParser(DocumentParser):
    # Future option — calls LlamaParse API

class PyPDFParser(DocumentParser):
    # Fallback option — basic text extraction, no bounding boxes
```

Config `PARSER=liteparse` selects which implementation. Same pattern as the embedding client.

**Embedding abstraction.** Same pattern — abstract base, multiple implementations:

```
class EmbeddingClient(ABC):
    async def embed(self, texts: list[str]) -> list[list[float]]

class OpenAIEmbedding(EmbeddingClient):      # Current
class CohereEmbedding(EmbeddingClient):      # Alternative
class InternalEmbedding(EmbeddingClient):    # Future: self-hosted EmbeddingGemma
```

Config `EMBEDDING_PROVIDER=openai` selects which implementation. Switching to self-hosted model = change one env var.

**Retry logic.** If any step fails:

```
Retryable failures (network, API timeout, rate limit):
    → Re-enqueue task with incremented retry_count
    → Exponential backoff: 2^retry * 5 seconds delay
    → After MAX_RETRIES (3): mark document as error, stop retrying

Non-retryable failures (corrupted PDF, unsupported format):
    → Mark document as error immediately
    → Do not re-enqueue

On failure:
    → PATCH /api/documents/{doc_id} { parse_status: "error", error_message: "..." }
    → PUBLISH doc_error event
    → Frontend: row stays faded, shows warning icon on hover
```

**Graceful shutdown.** On SIGTERM (container stopping):
- Finish processing the current document (don't interrupt mid-parse)
- Stop consuming new tasks from the queue
- Close Redis and HTTP connections
- Exit cleanly

Tasks left in the queue are picked up by other instances or when this instance restarts.

## Error Handling

| Error | Retryable | Action |
|-------|-----------|--------|
| S3 download failure | Yes | Re-enqueue with backoff |
| LiteParse crash / timeout | Yes | Re-enqueue with backoff |
| LiteParse unsupported format | No | Mark error, publish doc_error |
| Corrupted PDF (zero pages) | No | Mark error, publish doc_error |
| Embedding API rate limit | Yes | Re-enqueue with backoff |
| Embedding API auth failure | No | Mark error, log critical alert |
| API Server unreachable | Yes | Re-enqueue with backoff |
| Chunk storage failure (DB) | Yes | Re-enqueue with backoff |

## Testing Strategy

- **Unit tests:** Chunker logic with known page text and bounding boxes. Parser abstraction with mocked LiteParse output. Embedding client with mocked API responses.
- **Integration tests:** Full pipeline with a real small PDF, real LiteParse, mocked embedding API, mocked API Server. Verify chunks are correctly formed with bounding boxes.
- **Run:** `task doc:test` → `pytest tests/ -v`
````

## File: services/extraction-worker.md/extraction-worker.md
````markdown
# Extraction Worker — Service Design

*Last updated: 2025-07-01 · Status: Active*

---

## Responsibility

Background queue consumer that populates cells with AI-extracted answers. For each cell task: retrieves relevant document chunks via semantic search (RAG), constructs a prompt with the column question and document context, calls the LLM, parses the structured response into answer + reasoning + source references, saves the result via API Server, and publishes an SSE event. Has no HTTP endpoints — it only consumes from Redis and calls other services.

## Tech Stack

- **Runtime:** Python 3.12
- **LLM Client:** OpenAI SDK / Anthropic SDK (abstracted for swap)
- **Queue:** Redis via aioredis (BRPOP consumer)
- **Events:** Redis pub/sub (PUBLISH)
- **HTTP Client:** httpx (async, calls API Server for RAG + save)

## Folder Structure

```
services/extraction-worker/
├── Dockerfile
├── pyproject.toml
└── app/
    ├── main.py                 ← Entry point: start consumer loop
    ├── config.py               ← Settings from env vars
    ├── consumer.py             ← Redis queue consumer loop
    ├── handler.py              ← Orchestrates the full pipeline for one cell
    │
    ├── rag/
    │   └── pipeline.py         ← Retrieve chunks, build context, rank
    │
    ├── llm/
    │   ├── client.py           ← LLM abstraction (OpenAI / Anthropic / internal)
    │   ├── prompts.py          ← System prompt, user prompt templates
    │   └── response_parser.py  ← Parse + validate structured LLM output
    │
    └── clients/
        ├── api_client.py       ← HTTP client for API Server (get chunks, save cells)
        └── redis_client.py     ← Redis connection, publish events
```

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `API_SERVER_URL` | API Server base URL | `http://api-server:8000` |
| `LLM_PROVIDER` | Which LLM to use | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `OPENAI_MODEL` | Model name | `gpt-4o` |
| `ANTHROPIC_API_KEY` | Anthropic API key (if provider is anthropic) | `sk-ant-...` |
| `ANTHROPIC_MODEL` | Model name | `claude-sonnet-4-20250514` |
| `LLM_TEMPERATURE` | Generation temperature | `0.0` |
| `LLM_MAX_TOKENS` | Max response tokens | `4096` |
| `MAX_CONCURRENT_EXTRACTIONS` | Concurrent LLM calls per instance | `20` |
| `RAG_TOP_K` | Number of chunks to retrieve | `10` |
| `MAX_RETRIES` | Retry count before giving up | `3` |
| `QUEUE_NAME` | Redis queue to consume | `extraction_tasks` |

## Key Implementation Notes

**Consumer loop.** Same pattern as Document Worker — infinite async loop with `BRPOP`. But critically different concurrency model: extraction is IO-bound (waiting on LLM responses), so we run many concurrent tasks.

```
semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXTRACTIONS)

async def consume():
    while True:
        task = await redis.brpop("extraction_tasks")
        asyncio.create_task(process_with_semaphore(task))

async def process_with_semaphore(task):
    async with semaphore:
        await handle_extraction(task)
```

Unlike the Document Worker (1-2 concurrent, CPU-bound), this worker runs 20-50 concurrent extractions because each one is just waiting on an HTTP response from the LLM. The semaphore prevents exceeding API rate limits.

**Task schema.** Each task from Redis contains everything the worker needs:

```json
{
  "task_id": "task_001",
  "job_id": "job_xyz",
  "table_id": "tbl_abc123",
  "cell_id": "cell_xyz",
  "document_id": "doc_001",
  "column_id": "col_003",
  "column_title": "Liability Cap",
  "column_prompt": "What is the aggregate liability cap?",
  "column_type": "currency"
}
```

Column details are embedded in the task so the worker never needs to query column metadata. The API Server includes them at enqueue time.

**The pipeline for one cell:**

```
1. Retrieve relevant chunks (RAG)
   GET /api/documents/{doc_id}/chunks?query={column_prompt}&top_k=10
   → Returns ranked chunks with text, page number, section, chunk_id
   (~50-200ms)

2. Build context from chunks
   Concatenate chunk texts with page markers:
   "[Page 1, Preamble] This Master Services Agreement..."
   "[Page 14, Section 8.2] The aggregate liability..."
   (~instant)

3. Construct prompt
   System prompt + document context + column question + response format
   (~instant)

4. Call LLM
   Send prompt, receive structured JSON response
   (~3-15 seconds, IO-bound)

5. Parse and validate response
   Extract answer, reasoning, source_references from JSON
   Validate source page numbers exist in provided chunks
   Type-check answer against column_type
   (~instant)

6. Save cell result via API Server
   PUT /api/tables/{table_id}/cells/{cell_id}
   Body: { status, answer, reasoning, source_references }
   (~50-100ms)

7. PUBLISH cell_completed event
   { type: "cell_completed", cell_id, table_id, doc_id, col_id,
     answer, reasoning, source_references }
   Frontend: cell transitions from shimmer to answer text
```

**Prompt design.** Two-part prompt — system prompt sets behavior, user prompt provides context and question:

```
SYSTEM PROMPT:
You are a legal document analyst. You extract specific information
from legal documents with precision. You always cite your sources.

You respond in JSON with exactly this structure:
{
  "answer": "...",
  "reasoning": "...",
  "source_references": [
    { "chunk_id": "...", "page": N, "section": "...", "quote": "..." }
  ]
}

Rules:
- answer: Direct answer to the question. Match the requested type.
- reasoning: Explain how you found this answer. Reference specific
  sections and clauses. If not found, explain what you searched for.
- source_references: Every claim must cite a chunk_id, page, section,
  and a verbatim quote (max 100 words) from the source text.
- If the document does not contain the requested information,
  answer with "Not found" and explain in reasoning.


USER PROMPT:
Document context:
---
[Page 1, Preamble] This Master Services Agreement is entered into...
[Page 14, Section 8.2] The aggregate liability of either party...
---

Question: {column_prompt}
Response type: {column_type}
```

**Column type enforcement.** The prompt includes the expected response type, and the response parser validates it:

| Column Type | Prompt Hint | Validation |
|-------------|-------------|------------|
| `free_response` | "Respond with a concise summary." | Any non-empty string |
| `yes_no` | "Respond with exactly 'Yes' or 'No', then explain." | Starts with Yes/No |
| `date` | "Respond with a date in YYYY-MM-DD format." | Valid date string |
| `currency` | "Respond with a dollar amount or formula." | Contains numeric value or "Not found" |
| `verbatim` | "Extract the exact text. Do not paraphrase." | Must be a substring of provided context |

**Response parsing.** The LLM response is expected as JSON. The parser handles:

```
1. Parse JSON from LLM response
   → If LLM returns markdown-wrapped JSON (```json...```), strip the wrapper
   → If JSON parse fails, retry LLM call once with "Respond in valid JSON"

2. Validate required fields
   → answer, reasoning, source_references must all be present
   → source_references must be a non-empty array (unless answer is "Not found")

3. Validate source references
   → Each chunk_id must match one of the chunks we provided
   → Each page number must match the chunk's actual page
   → If validation fails: keep the answer but flag source as unverified

4. Type-check answer
   → Apply column-type-specific validation (table above)
   → If type check fails: keep the raw answer, log warning
```

**LLM abstraction.** Same factory pattern as embedding client:

```
class LLMClient(ABC):
    async def complete(self, system_prompt, user_prompt, **kwargs) -> LLMResponse

class OpenAIClient(LLMClient):       # Current default
class AnthropicClient(LLMClient):    # Alternative
class InternalClient(LLMClient):     # Future: self-hosted model

def get_llm_client() -> LLMClient:
    provider = config.LLM_PROVIDER
    if provider == "openai": return OpenAIClient(...)
    elif provider == "anthropic": return AnthropicClient(...)
    elif provider == "internal": return InternalClient(base_url=config.LLM_SERVICE_URL)
```

Switching from OpenAI to Anthropic = change `LLM_PROVIDER=anthropic`. Switching to self-hosted = change `LLM_PROVIDER=internal` and `LLM_SERVICE_URL=http://llm-service:8080`. No code changes.

**RAG context building.** The pipeline retrieves top-K chunks by semantic similarity, then formats them as context:

```
1. Send column_prompt as the search query
2. API Server performs pgvector similarity search
3. Returns top-K chunks ordered by relevance
4. Worker concatenates into context string with page markers
5. If total context exceeds ~50K tokens:
   → Trim to top chunks that fit within context window
   → Prefer higher-similarity chunks
6. Include chunk_ids in context so LLM can reference them in citations
```

Context template per chunk:

```
[Chunk: {chunk_id} | Page {page_number}, {section}]
{text_content}
```

This format lets the LLM cite back to specific chunk IDs, which the frontend uses to fetch bounding boxes for highlighting.

**Retry logic.**

| Error | Retryable | Action |
|-------|-----------|--------|
| LLM API rate limit (429) | Yes | Re-enqueue with exponential backoff |
| LLM API timeout | Yes | Re-enqueue with backoff |
| LLM API auth failure (401) | No | Mark cell error, log critical alert |
| LLM returned invalid JSON | Yes | Retry once inline (re-prompt), then re-enqueue |
| LLM returned empty response | Yes | Re-enqueue with backoff |
| API Server unreachable | Yes | Re-enqueue with backoff |
| RAG returned zero chunks | No | Mark cell with answer "Not found — no relevant content" |
| All retries exhausted | — | Mark cell error, publish cell_error event |

On failure:

```
→ PUT /api/tables/{table_id}/cells/{cell_id}
  { status: "error", error_message: "..." }
→ PUBLISH cell_error event
→ Frontend: cell shows error state (light red background)
→ User can click "Retry" which calls POST /cells/{cell_id}/rerun
```

**Graceful shutdown.** On SIGTERM:
- Stop accepting new tasks from queue
- Wait for all in-flight LLM calls to complete (with timeout of 30 seconds)
- If calls don't complete in 30 seconds, let them be re-processed by another instance (tasks that weren't saved are still in `extracting` status — a recovery job can re-enqueue them)
- Close connections, exit

## Scaling Characteristics

```
CPU:          Low (almost all time spent waiting on LLM HTTP response)
Memory:       Moderate (LLM context strings in memory, ~50K tokens × 20 concurrent ≈ 200MB)
Concurrency:  High (20-50 concurrent per instance)
Bottleneck:   LLM API rate limits and latency

1 instance  × 20 concurrent = ~120 cells/minute (at 10s avg per LLM call)
5 instances × 20 concurrent = ~600 cells/minute
10 instances × 30 concurrent = ~1800 cells/minute

50 docs × 5 columns = 250 cells → ~2 min with 1 instance
1K docs × 10 columns = 10K cells → ~17 min with 5 instances
10K docs × 15 columns = 150K cells → ~83 min with 10 instances
```

## Testing Strategy

- **Unit tests:** Prompt construction with known column types. Response parser with valid/invalid LLM outputs. Type validation per column type. Context builder with known chunks.
- **Integration tests:** Full pipeline with mocked LLM (return canned JSON responses). Verify correct API Server calls, correct event publishing, correct error handling.
- **Prompt tests:** Run actual LLM calls against a small set of known documents with expected answers. Not automated in CI (cost + latency), but run manually before prompt changes.
- **Run:** `task ext:test` → `pytest tests/ -v`
````

## File: services/sse-service.md/sse-service.md
````markdown
# SSE Service — Service Design

*Last updated: 2025-07-01 · Status: Active*

---

## Responsibility

Holds long-lived SSE connections with frontends. Subscribes to Redis pub/sub channels. When a worker publishes an event (doc_ready, cell_completed, etc.), this service pushes it to every connected client viewing that table. Entire service is ~200-300 lines of Go. No database access. No business logic. Just event routing.

## Tech Stack

- **Language:** Go 1.22
- **HTTP:** Standard library `net/http` (no framework)
- **Redis:** `github.com/redis/go-redis/v9`
- **Config:** Environment variables via `os.Getenv`

## Folder Structure

```
services/sse-service/
├── Dockerfile
├── go.mod
├── go.sum
└── main.go             ← Entire service in one file
```

This service is small enough to live in a single file. If it grows beyond ~400 lines, split into `main.go`, `connections.go`, `redis.go`. For now, one file is clearer.

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `PORT` | HTTP server port | `8080` |
| `HEARTBEAT_INTERVAL` | Seconds between keepalive comments | `30` |
| `CHANNEL_PREFIX` | Redis pub/sub channel prefix | `table` |

## Dockerfile

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 go build -o sse-service .

FROM scratch
COPY --from=builder /app/sse-service /sse-service
CMD ["/sse-service"]
```

Final image is ~10MB. Starts in <50ms. No OS, no shell, no runtime — just the binary.

## Key Implementation Notes

**Connection registry.** A thread-safe map from `table_id` to a list of connected clients. Each client is a channel that receives event strings.

```
connections map[string][]chan string

"tbl_abc123" → [client_chan_1, client_chan_2]
"tbl_def456" → [client_chan_3]
```

Multiple users can view the same table — all receive the same events. Protected by a `sync.RWMutex`.

**SSE endpoint.** Single route: `GET /api/tables/{table_id}/events`

```
1. Parse table_id from URL path
2. Set response headers:
   Content-Type: text/event-stream
   Cache-Control: no-cache
   Connection: keep-alive
3. Create a channel for this client
4. Register channel in connections map under table_id
5. Start goroutine: heartbeat ticker (every 30s, send ": heartbeat\n\n")
6. Loop: read from client channel, write SSE-formatted event to response
7. On client disconnect: unregister channel, close it, exit goroutine
```

Each connection is one goroutine (~2KB stack) + one channel. 10,000 connections = ~20MB memory.

**Redis subscription.** On startup, the service subscribes to Redis pub/sub using a pattern subscription:

```
PSUBSCRIBE table:*
```

This catches all events for all tables. One Redis subscription for the entire service, not one per table.

When a message arrives on channel `table:tbl_abc123`:
1. Parse the event JSON
2. Look up `tbl_abc123` in the connections map
3. For each registered client channel, send the formatted SSE string
4. If a client channel is full (blocked), skip it (non-blocking send)

**Event format.** Workers publish JSON to Redis. SSE Service formats it as SSE protocol:

```
Worker publishes to Redis channel "table:tbl_abc123":
{
  "type": "cell_completed",
  "cell_id": "cell_xyz",
  "table_id": "tbl_abc123",
  "document_id": "doc_001",
  "column_id": "col_003",
  "answer": "12 months aggregate fees",
  "reasoning": "Section 8.2 limits...",
  "source_references": [...]
}

SSE Service sends to connected clients:
event: cell_completed
data: {"cell_id":"cell_xyz","table_id":"tbl_abc123","document_id":"doc_001","column_id":"col_003","answer":"12 months aggregate fees","reasoning":"Section 8.2 limits...","source_references":[...]}

```

The `event:` line maps to `EventSource.addEventListener()` in the browser. The `data:` line is the JSON payload. Blank line terminates the event.

**Heartbeat.** Every 30 seconds, each connection sends an SSE comment:

```
: heartbeat

```

This is not an event — the leading `:` makes it a comment, ignored by `EventSource`. But it keeps the HTTP connection alive through proxies, load balancers, and firewalls that kill idle connections (Nginx default: 60s, AWS ALB: 60s).

**Client disconnect detection.** Go's `http.ResponseWriter` implements `http.CloseNotifier` (deprecated) or better, the request `context.Done()` channel signals when the client disconnects. The goroutine selects on both the client channel and context cancellation:

```
select {
case event := <-clientChan:
    write event to response, flush
case <-ticker.C:
    write heartbeat comment, flush
case <-r.Context().Done():
    unregister client, return
}
```

**Flushing.** SSE requires immediate flushing — events must be sent to the client as soon as they're written, not buffered. The response writer is cast to `http.Flusher` and flushed after every write.

**No authentication in V1.** The SSE endpoint is behind the Nginx gateway which handles auth. The SSE Service trusts that if a request reaches it, the user is authenticated. In V2, the service can validate a JWT from the query string (`?token=...`) since `EventSource` doesn't support custom headers.

**Graceful shutdown.** On SIGTERM:
1. Stop accepting new connections (stop HTTP server)
2. Close all client channels (triggers client-side reconnection)
3. Unsubscribe from Redis
4. Exit

Clients using `EventSource` automatically reconnect. When the new instance is up, they reconnect and resume receiving events. Events published during the brief downtime are lost — this is acceptable because the frontend can always hydrate full state from `GET /api/tables/{id}`.

## Event Routing Flow

```
Worker (Python)                    Redis                   SSE Service (Go)              Browser
     │                               │                          │                           │
     │  PUBLISH table:tbl_abc123     │                          │                           │
     │  { type: "cell_completed",    │                          │                           │
     │    cell_id: "cell_xyz", ... } │                          │                           │
     │──────────────────────────────▶│                          │                           │
     │                               │  PSUBSCRIBE table:*      │                           │
     │                               │─────────────────────────▶│                           │
     │                               │                          │                           │
     │                               │  message on table:tbl_abc│                           │
     │                               │─────────────────────────▶│                           │
     │                               │                          │  lookup tbl_abc123        │
     │                               │                          │  → [client_1, client_2]   │
     │                               │                          │                           │
     │                               │                          │  event: cell_completed    │
     │                               │                          │  data: { cell_id: ... }   │
     │                               │                          │──────────────────────────▶│
     │                               │                          │                           │
     │                               │                          │  (same event to client_2) │
     │                               │                          │──────────────────────────▶│
```

## Scaling Characteristics

```
CPU:          Very low (just routing strings from Redis to HTTP connections)
Memory:       ~2KB per connection (goroutine stack)
              10K connections ≈ 20MB
              100K connections ≈ 200MB
Concurrency:  Very high (goroutines, no thread-per-connection limit)
Bottleneck:   File descriptor limit (ulimit -n), network bandwidth

One instance comfortably handles 10,000+ concurrent connections.
Unlikely to need more than one instance until thousands of
simultaneous users.
```

## Connection Lifecycle

```
Client connects
    │
    ▼
GET /api/tables/tbl_abc123/events
    │
    ▼
Create client channel (buffered, size 32)
Register in connections["tbl_abc123"]
    │
    ▼
┌──────────────────────────────┐
│  LOOP                         │
│                               │
│  select:                      │
│  ├── event from channel       │
│  │   → write SSE, flush       │
│  ├── heartbeat ticker (30s)   │
│  │   → write ": heartbeat"    │
│  └── context.Done()           │
│      → unregister, return     │
│                               │
└──────────────────────────────┘
    │
    ▼ (client navigates away or network drops)
    │
Unregister from connections["tbl_abc123"]
Close client channel
Goroutine exits
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Redis connection lost | Log error, attempt reconnection with backoff. During downtime, no events are delivered. Clients stay connected but receive only heartbeats. |
| Client channel full (slow consumer) | Non-blocking send. If channel buffer (32) is full, skip the event for that client. Client will hydrate full state on next page load. |
| Malformed event from Redis | Log warning, skip event. Do not crash. |
| Client sends data (POST to SSE endpoint) | Ignore. SSE is server-to-client only. |
| SSE Service restart | All connections drop. Browser `EventSource` auto-reconnects. Frontend calls `GET /api/tables/{id}` to hydrate missed state. |

## Testing Strategy

- **Unit tests:** Connection registry — register, unregister, concurrent access. Event formatting — JSON to SSE string conversion.
- **Integration tests:** Start service, connect SSE client, publish event to Redis, assert client receives correctly formatted SSE event. Test heartbeat timing. Test disconnect cleanup.
- **Load tests:** Open 1,000 concurrent SSE connections, publish 100 events/second, verify all clients receive all events with <100ms latency.
- **Run:** `task sse:test` → `go test ./... -v`
````
