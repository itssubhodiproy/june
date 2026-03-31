

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