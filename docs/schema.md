

# Database Schema — June Review Table

*Last updated: 2025-07-03 · Status: Active*

---

PostgreSQL 16 with pgvector extension. Single database, schema ownership split between API Server (relational tables) and Document Worker (vector data).

---

## Entity Relationships

```
users
  │
  └──< user_workspaces >──── workspaces
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
                             └──< templates
                                      │
                                      └──< template_columns


Legend: ──< = one-to-many    >── = many-to-many join table
```

---

## Tables

### users

```
| Column        | Type        | Constraints                   |
|---------------|-------------|-------------------------------|
| id            | UUID        | PK, DEFAULT gen_random_uuid() |
| email         | VARCHAR(255)| NOT NULL, UNIQUE              |
| name          | VARCHAR(255)| NOT NULL                      |
| password_hash | VARCHAR(255)| NOT NULL                      |
| created_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| updated_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |

Indexes:
  (email) UNIQUE
```

User is a standalone entity — not tied to a workspace at the row level. Workspace membership is tracked via `user_workspaces`.

Auth is minimal in V1. Password hash via bcrypt. JWT or session-based auth can be swapped in later without schema changes.

---

### workspaces

```
| Column      | Type        | Constraints                   |
|-------------|-------------|-------------------------------|
| id          | UUID        | PK, DEFAULT gen_random_uuid() |
| name        | VARCHAR(255)| NOT NULL                      |
| created_at  | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| updated_at  | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
```

No soft delete — workspaces are permanent in V1.

---

### user_workspaces

Join table — which users belong to which workspaces. A user can be a member of multiple workspaces; a workspace can have multiple users.

```
| Column       | Type        | Constraints                        |
|--------------|-------------|------------------------------------|
| id           | UUID        | PK, DEFAULT gen_random_uuid()      |
| user_id      | UUID        | FK → users.id, NOT NULL            |
| workspace_id | UUID        | FK → workspaces.id, NOT NULL       |
| role         | VARCHAR(50) | NOT NULL, DEFAULT 'member'         |
| joined_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()            |

Indexes:
  (user_id, workspace_id) UNIQUE   — one membership per user per workspace
  (workspace_id)                   — list all members of a workspace
  (user_id)                        — list all workspaces for a user

CHECK constraint on role:
  role IN ('owner', 'member')
```

`role` is scoped for future use — invitations, permissions, etc. Not enforced beyond storage in V1.

---

### tables

```
| Column       | Type        | Constraints                   |
|--------------|-------------|-------------------------------|
| id           | UUID        | PK, DEFAULT gen_random_uuid() |
| workspace_id | UUID        | FK → workspaces.id, NOT NULL  |
| name         | VARCHAR(255)| NOT NULL                      |
| created_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| updated_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| deleted_at   | TIMESTAMPTZ | nullable                      |

Indexes:
  (workspace_id, deleted_at)  — list tables for a workspace, exclude deleted
```

Soft delete via `deleted_at`. All queries filter `WHERE deleted_at IS NULL`.

---

### columns

```
| Column     | Type        | Constraints                   |
|------------|-------------|-------------------------------|
| id         | UUID        | PK, DEFAULT gen_random_uuid() |
| table_id   | UUID        | FK → tables.id, NOT NULL      |
| title      | VARCHAR(255)| NOT NULL                      |
| prompt     | TEXT        | NOT NULL                      |
| type       | VARCHAR(50) | NOT NULL                      |
| "order"    | INTEGER     | NOT NULL                      |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |

Indexes:
  (table_id, "order")  — fetch columns for a table in display order

CHECK constraint on type:
  type IN ('free_response', 'yes_no', 'date', 'currency', 'verbatim')
```

`"order"` is quoted because it's a reserved word. Auto-assigned as `max(order) + 1` on insert. Column reorder (V1.1) updates these values.

Columns are always table-owned. When a template is imported, its `template_columns` are copied into this table as independent rows — edits to these columns never affect the source template.

---

### documents

```
| Column        | Type        | Constraints                   |
|---------------|-------------|-------------------------------|
| id            | UUID        | PK, DEFAULT gen_random_uuid() |
| workspace_id  | UUID        | FK → workspaces.id, NOT NULL  |
| file_name     | VARCHAR(255)| NOT NULL                      |
| file_type     | VARCHAR(50) | NOT NULL                      |
| file_key      | VARCHAR(500)| NOT NULL                      |
| file_size     | BIGINT      | NOT NULL                      |
| page_count    | INTEGER     | nullable                      |
| parse_status  | VARCHAR(20) | NOT NULL, DEFAULT 'not_ready' |
| error_message | TEXT        | nullable                      |
| created_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| updated_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| deleted_at    | TIMESTAMPTZ | nullable                      |

Indexes:
  (workspace_id, deleted_at)  — list documents, exclude deleted
  (parse_status)              — find documents needing processing

CHECK constraint on parse_status:
  parse_status IN ('not_ready', 'ready', 'error')
```

`file_key` is the S3 object key: `documents/{doc_id}/{file_name}`.

`page_count` is null until parsing completes, then set by the Document Worker.

Documents are workspace-scoped so the same document can be associated with multiple tables (Library/Vault feature). The physical file in S3 is stored once; `table_documents` tracks which tables use it.

---

### table_documents

Join table — which documents are in which tables.

```
| Column      | Type        | Constraints                        |
|-------------|-------------|------------------------------------|
| id          | UUID        | PK, DEFAULT gen_random_uuid()      |
| table_id    | UUID        | FK → tables.id, NOT NULL           |
| document_id | UUID        | FK → documents.id, NOT NULL        |
| row_order   | INTEGER     | NOT NULL                           |
| added_at    | TIMESTAMPTZ | NOT NULL, DEFAULT now()            |

Indexes:
  (table_id, row_order)               — fetch docs for a table in order
  (table_id, document_id) UNIQUE      — prevent duplicate association
  (document_id)                       — find all tables containing a document
```

`row_order` determines the row position in the table. Auto-assigned as `max(row_order) + 1` on insert.

When a document is removed from a table, the `table_documents` row is soft-deleted (add `deleted_at` if needed) and all cells for that document in that table are deleted. If the document has no remaining `table_documents` associations, the document itself is soft-deleted.

---

### cells

```
| Column            | Type        | Constraints                   |
|-------------------|-------------|-------------------------------|
| id                | UUID        | PK, DEFAULT gen_random_uuid() |
| table_id          | UUID        | FK → tables.id, NOT NULL      |
| document_id       | UUID        | FK → documents.id, NOT NULL   |
| column_id         | UUID        | FK → columns.id, NOT NULL     |
| status            | VARCHAR(20) | NOT NULL, DEFAULT 'empty'     |
| answer            | TEXT        | nullable                      |
| reasoning         | TEXT        | nullable                      |
| source_references | JSONB       | nullable                      |
| error_message     | TEXT        | nullable                      |
| created_at        | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| updated_at        | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |

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

### templates

```
| Column       | Type        | Constraints                   |
|--------------|-------------|-------------------------------|
| id           | UUID        | PK, DEFAULT gen_random_uuid() |
| workspace_id | UUID        | FK → workspaces.id, NOT NULL  |
| name         | VARCHAR(255)| NOT NULL                      |
| created_by   | UUID        | FK → users.id, NOT NULL       |
| created_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| updated_at   | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |
| deleted_at   | TIMESTAMPTZ | nullable                      |

Indexes:
  (workspace_id, deleted_at)  — list templates for a workspace, exclude deleted
```

Templates are workspace-scoped — visible to all members of the workspace. `created_by` tracks authorship for display purposes; it does not gate access in V1.

Soft delete via `deleted_at`.

---

### template_columns

The column definitions captured in a template. Mirrors the shape of `columns` exactly, but is owned by a template rather than a table.

```
| Column      | Type        | Constraints                   |
|-------------|-------------|-------------------------------|
| id          | UUID        | PK, DEFAULT gen_random_uuid() |
| template_id | UUID        | FK → templates.id, NOT NULL   |
| title       | VARCHAR(255)| NOT NULL                      |
| prompt      | TEXT        | NOT NULL                      |
| type        | VARCHAR(50) | NOT NULL                      |
| "order"     | INTEGER     | NOT NULL                      |
| created_at  | TIMESTAMPTZ | NOT NULL, DEFAULT now()       |

Indexes:
  (template_id, "order")  — fetch template columns in display order

CHECK constraint on type:
  type IN ('free_response', 'yes_no', 'date', 'currency', 'verbatim')
```

**Template lifecycle:**

"Save as template" — snapshot the current columns of a table:
1. Create one `templates` row.
2. Copy every `columns` row for that table into `template_columns` (title, prompt, type, order). No FK back to the source table — this is a pure snapshot.

"Import template" into a table:
1. Read all `template_columns` for the chosen template.
2. Insert them as new rows into `columns` with `table_id` set to the target table, re-assigning `order` to continue from the table's current max.
3. Batch-insert empty `cells` for each new column × every existing document in the table.

After import, the new `columns` rows are fully independent. Edits to them do not affect the template.

---

## Vector Data (pgvector)

### document_chunks

Stored in the same PostgreSQL database using the pgvector extension. This is the only table queried for RAG retrieval.

```
| Column       | Type          | Constraints                   |
|--------------|---------------|-------------------------------|
| id           | UUID          | PK, DEFAULT gen_random_uuid() |
| document_id  | UUID          | FK → documents.id, NOT NULL   |
| chunk_index  | INTEGER       | NOT NULL                      |
| text_content | TEXT          | NOT NULL                      |
| page_number  | INTEGER       | NOT NULL                      |
| section      | VARCHAR(255)  | nullable                      |
| bbox         | JSONB         | NOT NULL                      |
| embedding    | VECTOR(1536)  | NOT NULL                      |
| created_at   | TIMESTAMPTZ   | NOT NULL, DEFAULT now()       |

Indexes:
  (document_id, chunk_index)             — fetch chunks for a document in order
  HNSW on embedding (vector_cosine_ops)  — approximate nearest neighbor search
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

### Change log

| Migration | Description |
|-----------|-------------|
| 20250701_001 | Initial schema — workspaces, users, tables, columns, documents, table_documents, cells, document_chunks |
| 20250703_002 | User-workspace many-to-many — drop `workspace_id` from `users`, create `user_workspaces` join table |
| 20250703_003 | Templates — create `templates` and `template_columns` tables |