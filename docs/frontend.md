

# Frontend — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## Responsibility

Single-page application. Renders the review table, memory drawer, and document viewer. Manages all client-side state. Connects to the API Server via REST and the SSE Service for real-time updates. No server-side rendering — static files served by Nginx.

## Tech Stack

- **Framework:** React 19 + TypeScript
- **Routing:** React Router
- **Build:** Vite
- **Package Manager:** pnpm
- **State:** Zustand
- **Table:** TanStack Table (headless, virtualized)
- **UI Components:** shadcn/ui using the existing frontend theme tokens and component styles already defined in the repo
- **PDF Viewer:** react-pdf (pdf.js wrapper)
- **SSE Client:** Native browser `EventSource` API
- **HTTP Client:** Native `fetch` (no axios — unnecessary dependency)
- **Styling:** Tailwind CSS v4 (via shadcn)
- **Fonts:** EB Garamond (serif headings), Inter (sans body)

## Routing

```
/                        → LandingPage (public)
/login                   → LoginPage (public, redirects to /app/tables if authenticated)
/app                     → AppLayout (protected, auth guard)
/app/tables              → TablesPage (table list)
/app/tables/:tableId     → TablePage (single table workspace)
```

**Auth flow:**

- `main.tsx` calls `checkAuth()` on app load — validates token via `GET /api/auth/me`, populates user state.
- `AuthGuard` wraps all `/app/*` routes — redirects to `/login` if not authenticated.
- `LoginPage` calls `login()` — stores JWT in `localStorage`, updates Zustand store, navigates to `/app/tables`.
- `AppLayout` shows user email + sign out button — sign out clears token and Zustand store.
- Landing page CTA checks token presence — shows "Go to App" or "Sign In" based on `isAuthenticated`.

**Dev proxy:** Vite proxies `/api/*` to `localhost:8000` (API server). In production, Nginx handles routing.

No new design system. The frontend should use the theme tokens, typography, spacing, and shadcn setup already present in the repo.

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
    ├── main.tsx                    ← React root, auth check, router provider
    ├── App.tsx                     ← Re-exports router
    ├── router.tsx                 ← Router config with routes and auth guard
    │
    ├── pages/
    │   ├── landing.tsx             ← Landing page (public)
    │   ├── login.tsx               ← Sign in page (public)
    │   └── app/
    │       ├── layout.tsx          ← App shell with nav, auth-protected
    │       ├── tables.tsx          ← Table list
    │       └── table.tsx           ← Single table workspace (hero page)
    │
    ├── components/
    │   ├── auth-guard.tsx         ← Auth redirect wrapper
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
    │   ├── auth-store.ts          ← Auth state: user, token, login/logout/checkAuth
    │   ├── table-store.ts          ← Normalized table data only
    │   └── ui-store.ts             ← Selection, viewer state, modal state
    │
    ├── api/
    │   ├── auth.ts                ← Login, register, getMe, token localStorage
    │   ├── client.ts               ← Base fetch wrapper (auth headers, error handling)
    │   ├── tables.ts               ← Table CRUD calls
    │   ├── documents.ts            ← Upload URL, confirm, file URL, chunks
    │   ├── columns.ts              ← Column CRUD calls
    │   ├── extraction.ts           ← Run, rerun calls
    │
    ├── hooks/
    │   ├── use-auth.ts            ← Convenience wrapper around auth-store
    │   ├── use-sse.ts              ← SSE connection lifecycle + event routing
    │   ├── use-table.ts            ← Load table data, route-bound orchestration
    │   └── use-upload.ts           ← Page-scoped upload orchestration with concurrency control
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
│   └── <RouterProvider>
│       ├── <LandingPage>                 ← / (public)
│       ├── <LoginPage>                   ← /login (public)
│       └── <AuthGuard>                   ← /app/* (protected, from components/)
│           └── <AppLayout>
│               ├── <header>
│               │   ├── <Link to="/app/tables">
│               │   ├── <user email>
│               │   └── <Sign out button>
│               └── <Outlet>
│                   ├── <TablesPage>      ← /app/tables
│                   │   ├── <TableCard>   ← Each table in list
│                   │   └── <CreateTableButton>
│                   └── <TablePage>       ← /app/tables/:tableId
│                       │   owns route params, initial hydrate, SSE, and mutations
│                       │
│                       ├── <TableHeader>
│                       │   ├── <TableTitle>              ← Editable inline, auto-save on blur
│                       │   ├── <UploadButton>             ← File picker, multi-select
│                       │   ├── <AddColumnButton>          ← Opens <ColumnForm>
│                       │   ├── <RunButton>                ← Disabled when nothing to run
│                       │   └── <SaveIndicator>
│                       │
│                       ├── <TableGrid>                    ← TanStack Table
│                       │   ├── <ColumnHeader>            ← Per column: title, type, menu
│                       │   └── <TableRow>                 ← Per document (virtualized)
│                       │       ├── <DocumentCell>         ← File name, faded/solid
│                       │       └── <DataCell>             ← Per column: answer or state
│                       │
│                       ├── <MemoryDrawer>                ← Conditional: selectedRow !== null
│                       │   ├── <DrawerHeader>             ← Document name, close button
│                       │   └── <ColumnSection>           ← Per column, accordion
│                       │       ├── <Answer>
│                       │       ├── <Reasoning>
│                       │       └── <SourceChip>          ← Clickable → opens viewer
│                       │
│                       ├── <DocumentViewer>              ← Conditional: viewerDocumentId !== null
│                       │   ├── <ViewerHeader>            ← File name, page N/M, close
│                       │   ├── <PDFRenderer>             ← react-pdf canvas
│                       │   │   └── <HighlightOverlay>    ← Absolutely positioned divs on cited text
│                       │   └── <PageNavigation>          ← Prev / Next
│                       │
│                       ├── <ColumnForm>                   ← Modal: add or edit column
│                       └── <DeleteDialog>                 ← Modal: confirm destructive actions
```

`TablePage` is the orchestration boundary. It owns route params, initial hydration, SSE setup, and mutation hooks. Child components should stay mostly presentational and receive plain data plus event handlers.

## State Management

Two Zustand stores. Separated by concern and update frequency.

Rule: stores hold app state and synchronous mutations. Network requests live in `api/*` and orchestration hooks. Avoid hiding async side effects inside Zustand actions.

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
  hydrateTable: (payload: TablePayload) => void
  renameTableOptimistic: (name: string) => void
  addDocument: (doc: Document) => void
  updateDocumentStatus: (docId: string, status: string, pageCount?: number) => void
  addColumn: (column: Column) => void
  updateColumn: (colId: string, updates: Partial<Column>) => void
  deleteColumn: (colId: string) => void
  deleteDocument: (docId: string) => void
  updateCell: (docId: string, colId: string, cellData: CellData) => void
  setCellsExtracting: (cellKeys: string[]) => void
  markColumnStale: (colId: string) => void
  setSaveStatus: (status: "saved" | "saving" | "error") => void
}
```

**Cell key pattern:** `"doc_001::col_003"` — O(1) lookup. When SSE delivers a `cell_completed` event, the handler does `cells[`${doc_id}::${col_id}`] = newData`. When the Memory Drawer needs all cells for a document, it filters by prefix — fast enough for hundreds of cells.

**Why ordered maps:** `documents.order` and `columns.order` are arrays of IDs that define display order. `byId` is a record for O(1) lookup by ID. This lets us reorder (V1.1) by swapping array elements without touching the data records.

**Derived data over duplicate state:** drawer rows, run eligibility, completed counts, and presentational row models should be derived with selectors from the normalized store, not stored separately.

### ui-store.ts — View State

```typescript
interface UIStore {
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

  // Dialog state
  isColumnFormOpen: boolean
  isDeleteDialogOpen: boolean

  // Actions
  selectCell: (docId: string, colId: string) => void
  openViewer: (docId: string, chunkId: string, page: number, quote: string) => void
  closeViewer: () => void
  closeDrawer: () => void
}
```

**Derived layout:**

```
layout =
  selectedRow === null
    ? "table_only"
    : viewerDocumentId === null
      ? "table_and_drawer"
      : "drawer_and_viewer"
```

**State transitions:**

```
selectCell(docId, colId):
  set selectedRow = docId, selectedColumn = colId
  if viewerDocumentId !== null and viewerDocumentId !== docId:
    clear viewer state

openViewer(docId, chunkId, page, quote):
  set viewerDocumentId, viewerPage, viewerHighlight

closeViewer():
  clear viewer state

closeDrawer():
  clear selectedRow, selectedColumn
  clear viewer state
```

### use-upload.ts — Page-Scoped Upload Queue

```typescript
interface UploadController {
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

Upload progress is ephemeral page state, not global app state. Keep it inside `useUpload` unless a later requirement forces cross-route persistence.

## Optimistic Updates

Every user-facing mutation is optimistic. The UI updates immediately, the API call fires in the background, and SSE events reconcile the final state.

**What is optimistic:**

| Action | Optimistic Update | Revert on Error |
|--------|-------------------|-----------------|
| Rename table | Update store immediately | Restore previous name |
| Upload document | Row appears faded at step 1 (upload-url response) | Remove row |
| Delete document | Remove row immediately | Restore row + cells |
| Add column | Column appears, empty cells created immediately | Remove column + cells |
| Edit column | Title/prompt update, cells go stale immediately | Restore column + un-stale cells |
| Delete column | Column + all cells removed immediately | Restore column + cells |
| Global Run | All empty/stale cells → `extracting` immediately | Revert cells to prior status |
| Column re-run | All cells in column → `extracting` immediately | Revert cells to prior status |
| Cell re-run | Single cell → `extracting` immediately | Revert cell to prior status |
| Template import | Columns appear, empty cells created | Remove imported columns |

**Revert pattern:** Snapshot affected store slices before mutation. On API error, restore. On success, discard — SSE delivers authoritative state anyway.

```typescript
// Example: delete column
function deleteColumn(colId: string) {
  const previous = {
    column: columns.byId[colId],
    cells: Object.fromEntries(
      Object.entries(cells).filter(([key]) => key.includes(`::${colId}`))
    ),
  }

  tableStore.deleteColumn(colId) // optimistic

  api.deleteColumn(table.id, colId).catch(() => {
    tableStore.addColumn(previous.column)
    Object.entries(previous.cells).forEach(([key, cell]) => {
      const [docId, cid] = key.split("::")
      tableStore.updateCell(docId, cid, cell)
    })
  })
}
```

**SSE as reconciler:** Optimistic cell states (`extracting`) are overwritten by `cell_completed` SSE events. No double-update logic needed — the SSE payload is the source of truth. Revert only on network/API errors, never on SSE timing.

**Save indicator:** Shows "Saving..." during the window between optimistic update and API confirmation. Transitions to "Saved" on success or "Error" on failure.

## SSE Hook

```typescript
// hooks/use-sse.ts

function useSSE(tableId: string) {
  const onDocReady = React.useEffectEvent((data: DocReadyEvent) => {
    tableStore.getState().updateDocumentStatus(data.document_id, "ready", data.page_count)
  })

  const onDocError = React.useEffectEvent((data: DocErrorEvent) => {
    tableStore.getState().updateDocumentStatus(data.document_id, "error")
  })

  const onCellCompleted = React.useEffectEvent((data: CellCompletedEvent) => {
    tableStore.getState().updateCell(data.document_id, data.column_id, {
      id: data.cell_id,
      status: "completed",
      answer: data.answer,
      reasoning: data.reasoning,
      source_references: data.source_references,
    })
  })

  const onCellError = React.useEffectEvent((data: CellErrorEvent) => {
    tableStore.getState().updateCell(data.document_id, data.column_id, {
      id: data.cell_id,
      status: "error",
      error_message: data.error,
    })
  })

  useEffect(() => {
    const source = new EventSource(`/api/tables/${tableId}/events`)

    source.addEventListener("doc_ready", onDocReady)
    source.addEventListener("doc_error", onDocError)
    source.addEventListener("cell_completed", onCellCompleted)
    source.addEventListener("cell_error", onCellError)

    source.onerror = () => {
      // EventSource auto-reconnects. On reconnect, hydrate to catch missed events.
      api.getTable(tableId).then((payload) => tableStore.hydrateTable(payload))
    }

    return () => source.close()
  }, [tableId])
}
```

`useEffectEvent` (React 19) gives event handlers fresh store access without re-subscribing the `EventSource` on every render. The effect dependency array stays `[tableId]` — stable, no churn.

## Layout System

CSS Grid with conditional templates controlled by derived layout state:

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

Transitions should stay simple: animate `transform` and `opacity`, not layout-heavy properties where avoidable. Honor `prefers-reduced-motion`. Do not use `transition: all`.

React View Transitions are not part of the V1 plan. The app only needs simple panel and content transitions, and native CSS transitions are the lower-risk choice for this Vite SPA.

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

## Performance Notes

- Virtualize table rows from the start.
- Use `content-visibility: auto` on heavy off-screen drawer/viewer sections where it helps and does not interfere with measurement.
- Keep selectors narrow so table cells do not all re-render on unrelated updates.
- Use `startTransition` for non-urgent UI updates triggered by high-frequency interactions.
- Use `useDeferredValue` only if search/filtering or other expensive derived renders are introduced.
- **Lazy-load DocumentViewer.** `react-pdf` + pdf.js worker is ~300KB. Use `React.lazy()` — only needed when a user clicks a source chip, never on initial page load.
- **No barrel imports.** Import directly from file paths (`import { getTable } from "@/api/tables"`), not index re-exports (`import { getTable } from "@/api"`). Prevents unnecessary bundle inclusion.

## Accessibility & Interaction Rules

- Icon-only buttons must have `aria-label`.
- Async status updates like save state and upload state should announce through `aria-live="polite"` where appropriate.
- Dialogs, drawers, and the document viewer must support keyboard dismissal and sensible focus management.
- Drawer and viewer containers should use `overscroll-behavior: contain`.
- Long document names, answers, and quotes must truncate or wrap intentionally.
- Numeric columns should use tabular numerals for scanability.
- If V1.1 adds filters, sort, or search, sync them to the URL instead of keeping them as local-only UI state.

## Design System

Theme applied via shadcn CSS variables in `index.css`. The project uses the shadcn `radix-luma` preset with `neutral` base color and HugeIcons as the icon library.

| Design Token | Tailwind Class | Value |
|-------------|----------------|-------|
| Text primary | `text-foreground` | oklch(0.145 0 0) |
| Text muted | `text-muted-foreground` | oklch(0.556 0 0) |
| Background | `bg-background` | oklch(1 0 0) |
| Card surface | `bg-card` | oklch(1 0 0) |
| Primary action | `bg-primary` | oklch(0.205 0 0) |
| Subtle surface | `bg-secondary` | oklch(0.97 0 0) |
| Border | `border-border` | oklch(0.922 0 0) |
| Radius base | `rounded-lg` | --radius: 0.45rem |

**Font usage:** EB Garamond (`font-serif`) for table title and Memory Drawer document name only. Inter Variable (`font-sans`) for everything else — table body, cells, forms, UI. Serif headings signal "document tool" without sacrificing scanability in dense data areas.

**Icon library:** HugeIcons (`@hugeicons/react`). Icons in buttons use `data-icon="inline-start"` or `data-icon="inline-end"`. Icon sizing is handled by the component — no `size-*` classes needed.

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

## shadcn Components

Already installed: `button`, `theme-provider` (custom)

Components to install as needed during implementation:

| Component | Used By | Why |
|-----------|---------|-----|
| `sheet` | Memory Drawer | Side panel with focus management, keyboard dismissal |
| `dialog` | Column Form, Delete Dialog | Modal overlays |
| `badge` | Column type badges, stale/outdated labels | Semantic status display |
| `skeleton` | Cell shimmer, loading states | Loading placeholders |
| `dropdown-menu` | Column header actions menu | Edit/delete per column |
| `tooltip` | Icon-only button labels | Accessibility |
| `separator` | Drawer section dividers | Visual separation |
| `scroll-area` | Drawer content, table container | Custom scrollbars |
| `input` | Column form, table rename | Text inputs |
| `textarea` | Column prompt field | Multi-line input |
| `select` | Column type picker | Dropdown selection |
| `accordion` | Drawer column sections | Expandable column content |
| `sonner` | Toast notifications | Upload/error feedback |
| `label` | Form labels | Accessible form labels |

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
