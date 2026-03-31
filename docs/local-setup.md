

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