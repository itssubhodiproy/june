# API Reference — June Review Table

*Last updated: 2025-07-03 · Status: Active*

---

All endpoints are prefixed with `/api`. All request/response bodies are JSON. All IDs are UUIDs. Timestamps are ISO 8601. Authentication is via session cookie or Bearer token (handled by API Gateway).

---

## Workspaces

### POST /api/workspaces

Create a new workspace. Also creates the `user_workspaces` row with `role: "owner"` for the requesting user.

```
Request:  { "name": "Acme Legal" }
Response: {
  "id": "ws_001",
  "name": "Acme Legal",
  "created_at": "2025-07-03T10:00:00Z"
}
Status: 201 Created
```

---

### GET /api/workspaces

List all workspaces the current user is a member of.

```
Response: {
  "workspaces": [
    {
      "id": "ws_001",
      "name": "Acme Legal",
      "role": "owner",
      "joined_at": "2025-07-03T10:00:00Z"
    }
  ]
}
Status: 200 OK
```

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

## Templates

### GET /api/templates

List all templates in the current workspace.

```
Response: {
  "templates": [
    {
      "id": "tpl_001",
      "name": "NDA Review",
      "column_count": 6,
      "created_by": "user_abc",
      "created_at": "2025-07-03T10:00:00Z"
    }
  ]
}
Status: 200 OK
```

---

### POST /api/templates

Save a snapshot of a table's columns as a new template ("Save as template").

```
Request: {
  "name": "NDA Review",
  "table_id": "tbl_abc123"
}
Response: {
  "id": "tpl_001",
  "name": "NDA Review",
  "column_count": 6,
  "created_at": "2025-07-03T10:00:00Z"
}
Status: 201 Created
```

Side effects:
- Creates one `templates` row.
- Copies all current `columns` for the given table into `template_columns` (title, prompt, type, order). Pure snapshot — no link back to the source table.

---

### DELETE /api/templates/{template_id}

Delete a template.

```
Response: { }
Status: 204 No Content
```

Backend soft-deletes (sets `deleted_at`). Does not affect any tables or columns.

---

### POST /api/templates/{template_id}/import

Import a template's columns into a table. One call, one transaction.

```
Request: {
  "table_id": "tbl_abc123"
}
Response: {
  "columns": [
    {
      "id": "col_007",
      "table_id": "tbl_abc123",
      "title": "Parties",
      "prompt": "Who are the parties to this agreement?",
      "type": "free_response",
      "order": 4
    },
    {
      "id": "col_008",
      "table_id": "tbl_abc123",
      "title": "Governing Law",
      "prompt": "What is the governing law and jurisdiction?",
      "type": "free_response",
      "order": 5
    }
  ]
}
Status: 201 Created
```

Side effects:
- Bulk inserts all `template_columns` as new rows in `columns`, with `order` continuing from the table's current max.
- Bulk inserts empty `cells` for each new column × every existing document in the table.
- Imported columns are independent — future edits do not affect the template.

Frontend receives the full column list in the response and merges into Zustand store. No subsequent fetch needed.

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
| 404 | NOT_FOUND | Table, document, column, cell, or template doesn't exist |
| 409 | CONFLICT | Document already associated with this table |
| 422 | INVALID_COLUMN_TYPE | Column type not in allowed enum |
| 500 | INTERNAL_ERROR | Unexpected server error |

---

## Rate Limits

Not enforced in V1. API Gateway (Nginx) can add rate limiting per-IP if needed. Designed for single-tenant workspace usage — not a public API.