

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