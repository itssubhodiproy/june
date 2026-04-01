## Initialization

You can still init, but be careful:

```bash
# Frontend - this works in existing directory
cd frontend
pnpm create vite . --template react-ts
# It will ask "Current directory is not empty. Remove existing files and continue?"
# Say NO, then manually merge what it creates

# Python services - just write pyproject.toml directly
# uv init creates minimal structure, but you already have your structure
# Better to manually write pyproject.toml with your deps
```

**My recommendation:** Skip init commands. Manually write `package.json` and `pyproject.toml` with exactly what you need. You know your dependencies from the docs.

---

## Build Order

**Phase 1: Infrastructure runs (2 hours)**
```
docker-compose.yml  (postgres, redis, minio only)
infra/postgres/init.sql
.env.example → .env

Goal: `docker compose up` gives you working postgres with pgvector, redis, minio
```

**Phase 2: API Server - minimal vertical (1 day)**
```
pyproject.toml (dependencies)
config.py
dependencies.py
models/base.py, workspace.py, table.py
schemas/table.py
routes/tables.py
main.py

Goal: POST /api/tables and GET /api/tables work via curl
```

**Phase 3: Frontend - minimal vertical (1 day)**
```
package.json (dependencies)
vite.config.ts, tsconfig.json
main.tsx, App.tsx
pages/tables.tsx (just list tables)
api/client.ts, api/tables.ts
stores/table-store.ts (minimal)

Goal: Browser shows list of tables from API
```

**Phase 4: First full flow - Document Upload (2 days)**
```
API: documents routes, storage_service (presigned URLs)
API: models for document, table_documents
Frontend: upload-button.tsx, document appears in table (faded)
Document Worker: consumer, handler, parser, chunker
SSE Service: main.go (full implementation, it's small)
Frontend: use-sse.ts, document goes solid on doc_ready

Goal: Upload PDF → see it appear faded → see it go solid when parsed
```

**Phase 5: Extraction flow (2 days)**
```
API: columns routes, cells routes, extraction routes
Frontend: column-header, add column form, data-cell (empty state)
Extraction Worker: full implementation
Frontend: cells show shimmer → answer appears via SSE

Goal: Add column → Run → watch cells fill in
```

**Phase 6: Memory Drawer + Document Viewer (2 days)**
```
Frontend: memory-drawer, column-section, source-chip
Frontend: document-viewer, highlight-overlay
API: chunks endpoint for bbox data
stores/ui-store.ts (layout state machine)

Goal: Click cell → drawer opens → click source → PDF with highlight
```

**Phase 7: Polish + Gateway (1 day)**
```
Gateway nginx.conf
All Dockerfiles
Error handling, loading states
Taskfile.yml commands
```

---

## The Key Principle

**Build vertically, not horizontally.**

Wrong: "I'll finish all API routes, then all frontend pages, then workers"
Right: "I'll build upload→parse→display end-to-end, then add extraction end-to-end"

Vertical slices force integration early. You discover problems at day 4, not day 14.

---

## Suggested First Session

Start here:

```bash
# 1. Write docker-compose.yml (just infra services)
# 2. Write init.sql
# 3. docker compose up -d postgres redis minio
# 4. Verify: psql connects, redis-cli pings, minio console loads
# 5. Write api-server/pyproject.toml
# 6. Write config.py, main.py, one route
# 7. Run API server, hit it with curl
```

Stop when you can create a table via API. That's your foundation.