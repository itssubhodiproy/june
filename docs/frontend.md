

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