# Extraction Worker — Service Design

*Last updated: 2026-04-29 · Status: Active*

---

## Responsibility

Background queue consumer that populates cells with AI-extracted answers. Consumes table-level tasks from Redis, fetches an extraction manifest from the API Server, then processes cells concurrently: for each cell, retrieves relevant document chunks via semantic search (RAG), constructs a prompt with the column question and document context, calls the LLM, parses the structured response into answer + reasoning + source references, publishes an SSE event per cell, and bulk-saves results via API Server. Has no HTTP endpoints — it only consumes from Redis and calls other services.

## Tech Stack

- **Runtime:** Python 3.13+
- **LLM Client:** OpenAI SDK / Anthropic SDK (abstracted for swap)
- **Queue:** Redis-native library (BRPOP consumer)
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
    ├── handler.py              ← Orchestrates the full pipeline for one table run
    ├── types.py                ← Pydantic models for tasks and events
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
| `INTERNAL_SERVICE_TOKEN` | Service-to-service auth token | `secret-token` |
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

**Consumer loop.** The worker runs an infinite async loop using `BRPOP` on the `extraction_tasks` queue. It follows the same `Consumer` class pattern as the document worker, with signal handling for graceful shutdown.

```python
class Consumer:
    async def run(self) -> None:
        # Initialize clients and handler
        redis = RedisClient()
        api = ApiClient()
        handler = ExtractionHandler(HandlerDependencies(redis=redis, api=api))

        while not self._shutdown.is_set():
            task = await redis.pop_extraction_task()
            if task:
                await self._process_task(task, redis, handler)
```

**Task handling.** The `ExtractionHandler` manages the table-level run. It maintains high concurrency internally (up to `MAX_CONCURRENT_EXTRACTIONS`) using `asyncio.Semaphore`.

```python
class ExtractionHandler:
    def __init__(self, deps: HandlerDependencies) -> None:
        self._deps = deps
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_EXTRACTIONS)

    async def handle(self, task: ExtractionTask) -> None:
        # 1. Fetch manifest
        manifest = await self._deps.api.get_extraction_manifest(task.table_id)
        
        # 2. Process all cells in the manifest concurrently
        tasks = [self._process_cell(cell) for cell in manifest.cells]
        await asyncio.gather(*tasks)

        # 3. Final bulk save and event
        await self._deps.api.bulk_update_cells(task.table_id, self._results_buffer)
        await self._deps.redis.publish_run_completed(task.table_id)
```

**Task schema.** The Redis task is a simple trigger. The worker fetches data from the API Server to ensure it has the freshest state.

```json
{
  "table_id": "tbl_abc123",
  "type": "run_all", // run_all or run_rerun
  "cell_id": "cell_xyz" // Optional filter for rerun
}
```

**The pipeline for a Table Run:**

1.  **Fetch Manifest**: `GET /api/tables/{table_id}/extraction-manifest?cell_id={cell_id}`
    Returns list of cells to extract, with their `document_id`, `column_prompt`, `column_type`, etc. Passing `cell_id` ensures workers only process intended targets during reruns.

2.  **Concurrency Management**: Use a global semaphore to process cells. Each cell task:
    a. **Retrieve chunks (RAG)**: `GET /api/documents/{doc_id}/chunks?query={prompt}`
    b. **Construct Prompt**: Context + Question + Output format.
    c. **Call LLM**: Get structured response.
    d. **Publish Real-time Event**: `PUBLISH cell_completed` (SSE Service).
    e. **Buffer Result**: Add to local results batch.

3.  **Bulk Save**: Once a batch of cells (or the whole run) is done, save to DB:
    `POST /api/tables/{table_id}/cells/bulk-update`
    Body: `[ { "cell_id": "...", "status": "completed", "answer": "...", ... }, ... ]`

4.  **Finalize**: Publish `run_completed` event.

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

```python
class LLMClient(ABC):
    async def complete(self, system_prompt, user_prompt, **kwargs) -> LLMResponse

class OpenAIClient(LLMClient):       # Current default
class AnthropicClient(LLMClient):    # Alternative
class InternalClient(LLMClient):     # Future: self-hosted model

def get_llm_client() -> LLMClient:
    provider = settings.LLM_PROVIDER
    if provider == "openai": return OpenAIClient(...)
    elif provider == "anthropic": return AnthropicClient(...)
```

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

**Retry logic.** If any step fails, it follows the same retry pattern as the document worker, re-enqueuing the task with an incremented retry count.

| Error | Retryable | Action |
|-------|-----------|--------|
| LLM API rate limit (429) | Yes | Re-enqueue task |
| LLM API timeout | Yes | Re-enqueue task |
| LLM API auth failure (401) | No | Mark cell error, log critical alert |
| LLM returned invalid JSON | Yes | Retry once inline (re-prompt), then re-enqueue |
| LLM returned empty response | Yes | Re-enqueue task |
| API Server unreachable | Yes | Re-enqueue task |
| RAG returned zero chunks | No | Mark cell with answer "Not found — no relevant content" |
| All retries exhausted | — | Mark cell error, publish cell_error event |

On failure:

```
→ PUBLISH cell_error event (immediate, so frontend shows error state)
→ Include in bulk-update batch: { cell_id, status: "error", error_message: "..." }
→ Frontend: cell shows error state (light red background)
→ User can click "Retry" which calls POST /tables/{table_id}/cells/{cell_id}/rerun
```

**Graceful shutdown.** On SIGTERM (container stopping):
- Finish processing the current table run if possible (or let it be re-picked by another worker)
- Stop consuming new tasks from the queue
- Close Redis and HTTP connections
- Exit cleanly

## Scaling Characteristics

```
CPU:          Low (almost all time spent waiting on LLM HTTP response)
Memory:       Moderate (LLM context strings in memory, ~50K tokens × 20 concurrent ≈ 200MB)
Concurrency:  High (20-50 concurrent per instance)
Bottleneck:   LLM API rate limits and latency
```

## Testing Strategy

- **Unit tests:** Prompt construction with known column types. Response parser with valid/invalid LLM outputs. Type validation per column type. Context builder with known chunks.
- **Integration tests:** Full pipeline with mocked LLM (return canned JSON responses). Verify correct API Server calls, correct event publishing, correct error handling.
- **Run:** `task ext:test` → `pytest tests/ -v`