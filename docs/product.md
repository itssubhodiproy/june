

# Product — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## What

June Review Table is an AI-powered document review tool for legal professionals. Users upload PDFs, define questions as columns, and the AI extracts answers from every document — each answer backed by reasoning and exact source citations with highlighted text in the original PDF.

## Who

In-house legal teams, law firm associates, and contract analysts who review large sets of documents under time pressure — M&A due diligence, lease audits, NDA reviews, regulatory filings.

## Principles

- **Every cell is a triad:** answer + reasoning + source reference. All three or nothing.
- **No manual cell editing.** If the AI is wrong, re-run. The trust chain stays intact.
- **Auto-save always.** No save button. Every action persists immediately.
- **Progressive results.** Cells fill in as they complete. No waiting for "all done."
- **Agent-ready APIs.** Every action the UI does, an AI agent can do via the same endpoint.

---

## User Journey

User creates a table → uploads PDFs (rows appear faded with a subtle pulse, become solid when parsed) → adds columns by writing a title, a natural language prompt, and selecting a type (free response, yes/no, date, currency, verbatim) → clicks Run → a thin progress bar appears at the header’s bottom edge with a counter (e.g., "128 / 250") that updates in real-time as cells complete → cells fill in progressively as extraction completes, each with a shimmer-to-content transition → clicks any cell to open the Memory Drawer showing answer, reasoning, and source chips for every column of that document → clicks a source chip to open the Document Viewer with the PDF scrolled to the exact page and the cited text highlighted with bounding-box precision → presses Escape to return to the table.

### Layout States

```
TABLE ONLY ──click cell──▶ TABLE + MEMORY DRAWER ──click source──▶ MEMORY DRAWER + DOC VIEWER
   (100%)                     (60%)    (40%)                          (30%)         (70%)
                                  │                                       │
                          click [✕]│                               Esc / [✕]
                                  ▼                                       ▼
                             TABLE ONLY ◄──────────────────── TABLE + MEMORY DRAWER
```

---

## Workspace Model

All data — tables, documents, cells — is scoped to a workspace, not a user. Each user belongs to a workspace created on first sign-in. Multi-workspace support and team invites are V2.

**Auth flow:** `june-legal.com` (landing page) → sign in → `app.june-legal.com` → workspace.

---

## V1 Scope

### In

```
Tables:       Create, rename, delete, list, auto-save
Documents:    Multi-file upload, delete (confirmation), two UI states (faded → solid)
Columns:      Add (title + prompt + type), edit (marks cells stale), delete
Extraction:   Manual "Run" button (active when empty/stale cells exist), progressive cell population via SSE, cell re-run, column re-run, thin progress bar with counter
Cell:         Click → Memory Drawer (answer + reasoning + sources), row-level, accordion
Doc Viewer:   Load PDF from S3, scroll to page, highlight cited text via bounding boxes
Column Types: Free Response, Yes/No, Date, Currency, Verbatim
```

### Out (designed for, not building now)

```
AI Column Builder          Library / Vault             Templates
Chat over table            Collaboration               Risk scoring
Export                     Workflows                   Portal / sharing
Filter / Sort              Column reorder              Manual cell editing
```

### V1.1 (fast-follow)

```
Filter by column value     Sort by column
Export to CSV              Column drag-and-drop reorder
```

---

## Future

Chat over table data with citations back to cells and documents. Document editor with AI suggestions and playbook-based redlining. Visual workflow builder for repeatable multi-step processes. Collaboration with assignments, flags, and comments. Library/Vault for persistent document storage across tables.

---

## Key Product Decisions

| Decision | Rule | Reasoning |
|----------|------|-----------|
| No cell editing | Users re-run, never manually edit | Answer + reasoning + source are bonded. Editing one breaks the others. |
| Two document states | Faded (not ready) → solid (ready) | Users don't care about upload/parse/embed internals. Ready or not. |
| Column edit → stale | Editing a prompt dims all cells in that column | Old answers don't match new prompt. Visual signal prevents confusion. |
| Row-level Memory Drawer | Clicking any cell shows all columns for that document | Avoids repeated open/close. One click gives full document context. |
| Table hides in doc viewer | State 3 is Memory Drawer + Doc Viewer only | Three panels is too cramped. Two-panel max for comfortable reading. |
| Auto-save only | No save button exists anywhere | Eliminates "did I save?" anxiety. Every mutation persists immediately. |
| Soft delete backend | UI treats delete as permanent, DB uses deleted_at | Recovery capability without confusing the user with undo complexity. |
