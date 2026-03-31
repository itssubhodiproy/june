

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
