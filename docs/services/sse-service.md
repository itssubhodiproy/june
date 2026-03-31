

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