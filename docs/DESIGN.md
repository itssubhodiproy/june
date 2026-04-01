
# Design System — June Review Table

*Last updated: 2025-07-01 · Status: Active*

---

## Product Context

- **What this is:** AI-powered document review tool that extracts structured answers from PDFs with citation-backed reasoning
- **Who it's for:** Legal professionals — in-house counsel, law firm associates, contract analysts
- **Space/industry:** Legal tech, document intelligence, contract review
- **Project type:** Data-heavy web application (table-centric, document viewer, drawer panels)

---

## Aesthetic Direction

- **Direction:** Refined Professional — sophisticated but not cold, trustworthy but not boring
- **Decoration level:** Minimal — typography and spacing do the work, no decorative elements
- **Mood:** A senior associate's well-organized desk. Calm confidence. Everything has a place. The tool disappears, the work stays in focus.

---

## Typography

| Role | Font | Weight | Rationale |
|------|------|--------|-----------|
| Display/Hero | EB Garamond | 500-600 | Elegant serif signals legal, considered, trustworthy. Used sparingly for character. |
| Body | Source Serif 4 | 400, 600 | Coheres with EB Garamond. Legal professionals read documents all day — a serif body feels native to their work. |
| UI/Labels | Inter | 400, 500, 600 | Clean sans for interface elements, buttons, metadata. Stays out of the way. |
| Data/Tables | Inter | 400 | With `font-variant-numeric: tabular-nums` for aligned columns. |
| Code/Monospace | JetBrains Mono | 400 | For any code blocks, chunk IDs, or technical metadata. |

**Loading:**
```html
<link rel="preconnect" href="https://fonts.bunny.net">
<link href="https://fonts.bunny.net/css?family=eb-garamond:500,600|source-serif-4:400,600|inter:400,500,600" rel="stylesheet">
```

**Scale:**
```css
--text-xs: 0.75rem;    /* 12px — metadata, timestamps */
--text-sm: 0.875rem;   /* 14px — table cells, labels */
--text-base: 1rem;     /* 16px — body text */
--text-lg: 1.125rem;   /* 18px — drawer headings */
--text-xl: 1.25rem;    /* 20px — section titles */
--text-2xl: 1.5rem;    /* 24px — page titles */
--text-3xl: 2rem;      /* 32px — hero/table name */
```

---

## Color

**Approach:** Restrained — one accent, warm neutrals, color is rare and meaningful.

### Core Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--background` | `oklch(0.98 0.003 90)` · #faf9f7 | Page background, warm off-white |
| `--surface` | `oklch(1 0 0)` · #ffffff | Cards, table cells, elevated surfaces |
| `--surface-muted` | `oklch(0.96 0.003 90)` · #f5f3f0 | Hover states, secondary surfaces |
| `--foreground` | `oklch(0.145 0 0)` · #1a1a1a | Primary text |
| `--foreground-muted` | `oklch(0.556 0 0)` · #777777 | Secondary text, placeholders |
| `--border` | `oklch(0.922 0.003 90)` | Subtle dividers, card borders |
| `--border-strong` | `oklch(0.85 0.003 90)` | Emphasized borders, table headers |

### Action Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--primary` | `oklch(0 0 0)` · #000000 | Primary buttons, strong text |
| `--primary-foreground` | `oklch(1 0 0)` · #ffffff | Text on primary buttons |
| `--accent` | `oklch(0.55 0.15 55)` · #b45309 | Warm amber — Run button, key CTAs, active states |
| `--accent-foreground` | `oklch(1 0 0)` · #ffffff | Text on accent buttons |

### Semantic Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--success` | `oklch(0.55 0.15 145)` · #16a34a | Completed states, success messages |
| `--warning` | `oklch(0.7 0.15 85)` · #ca8a04 | Stale cells, attention needed |
| `--error` | `oklch(0.55 0.2 25)` · #dc2626 | Errors, failed states |
| `--info` | `oklch(0.55 0.12 250)` · #2563eb | Informational, links |

### Dark Mode Strategy

Invert surfaces (not hues). Reduce accent saturation by 15%. Keep contrast ratios above 4.5:1.

```css
[data-theme="dark"] {
  --background: oklch(0.13 0.003 90);
  --surface: oklch(0.18 0.003 90);
  --foreground: oklch(0.93 0 0);
  --foreground-muted: oklch(0.65 0 0);
  --accent: oklch(0.6 0.12 55);
}
```

---

## Spacing

- **Base unit:** 4px
- **Density:** Comfortable — data-heavy but not cramped

**Scale:**
```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

**Component spacing:**
- Table cell padding: `--space-3` vertical, `--space-4` horizontal
- Card padding: `--space-4` to `--space-6`
- Section gaps: `--space-6` to `--space-8`
- Page margins: `--space-6` mobile, `--space-8` desktop

---

## Layout

- **Approach:** Grid-disciplined — strict alignment for data-heavy interface
- **Max content width:** None for table view (full width), 1280px for settings/forms

**Layout States:**
```
TABLE_ONLY:           100% table
TABLE_AND_DRAWER:     60% table | 40% drawer (400px fixed)
DRAWER_AND_VIEWER:    30% drawer (320px) | 70% viewer
```

**Transitions:**
```css
transition: grid-template-columns 300ms ease-out;
```

**Border Radius:**
```css
--radius-sm: 4px;    /* inputs, chips, small elements */
--radius-md: 8px;    /* buttons, badges */
--radius-lg: 12px;   /* cards, panels, modals */
--radius-xl: 16px;   /* large containers */
--radius-full: 9999px; /* avatars, pills */
```

---

## Motion

- **Approach:** Minimal-functional — motion aids comprehension, never decorates

**Easing:**
```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);   /* enter, expand */
--ease-in: cubic-bezier(0.7, 0, 0.84, 0);    /* exit, collapse */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1); /* move, resize */
```

**Duration:**
```css
--duration-fast: 100ms;    /* micro-interactions, button press */
--duration-normal: 200ms;  /* hovers, state changes */
--duration-slow: 300ms;    /* panel transitions */
--duration-slower: 500ms;  /* row fade-in on doc ready */
```

**State Animations:**

| State | Animation |
|-------|-----------|
| Document parsing | `opacity: 0.4` + `animate-pulse` (gentle breathing) |
| Document ready | `transition: opacity 500ms ease-in` to `opacity: 1` |
| Cell extracting | `animate-pulse` with `bg-muted/50` (shimmer) |
| Cell completed | Fade-in answer text, 200ms |
| Panel open | Slide from right, 300ms ease-out |

---

## Component Patterns

### Buttons

| Variant | Background | Border | Text |
|---------|------------|--------|------|
| Primary | `--primary` | none | `--primary-foreground` |
| Accent | `--accent` | none | `--accent-foreground` |
| Secondary | `--surface` | `--border` | `--foreground` |
| Ghost | transparent | none | `--foreground-muted` |
| Destructive | `--error` | none | white |

### Cell States

| Status | Background | Border | Text | Other |
|--------|------------|--------|------|-------|
| `empty` | `--surface-muted` at 30% | dashed `--border` | — | — |
| `extracting` | `--surface-muted` at 50% | none | — | `animate-pulse` |
| `completed` | `--surface` | none | `--foreground` | — |
| `stale` | `--surface` | none | `--foreground` at 50% | "outdated" badge |
| `error` | `--error` at 10% | none | `--error` | — |

### Document Row States

| Status | Opacity | Animation |
|--------|---------|-----------|
| `not_ready` | 0.4 | `animate-pulse` |
| `ready` | 1.0 | `transition: opacity 500ms` |
| `error` | 0.4 | none, warning icon on hover |

---

## Shadows

Minimal shadow usage. Elevation through background color, not depth.

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.03);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.05);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.05);
```

Use shadows only for:
- Modals/dialogs (`--shadow-lg`)
- Dropdowns (`--shadow-md`)
- Sticky headers (`--shadow-sm`)

Cards and panels use border, not shadow.

---

## Icons

- **Library:** Lucide (consistent with shadcn/ui)
- **Size:** 16px default, 20px for emphasis, 24px for navigation
- **Stroke:** 1.5px (matches Inter's weight)
- **Color:** Inherit from text color

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-07-01 | EB Garamond for display | Serif signals legal/professional without being stuffy |
| 2025-07-01 | Source Serif 4 for body | Coheres with EB Garamond, native to document-heavy work |
| 2025-07-01 | Warm off-white background | Softer than pure white, reduces eye strain for long sessions |
| 2025-07-01 | Warm amber accent | One focal point for CTAs, restrained but distinctive |
| 2025-07-01 | 12px base border radius | Soft but not bubbly, appropriate for data-dense UI |
| 2025-07-01 | Minimal shadows | Elevation through color, not depth — cleaner for tables |
| 2025-07-01 | 500ms doc-ready transition | Gentle materialization, not jarring pop |

----

Save this as `docs/DESIGN.md` or root `DESIGN.md` — your call on where design docs live.

Two things I changed from frontend.md:
1. **Source Serif 4 for body** — coheres with EB Garamond, distinctive
2. **Warm amber accent** (`#b45309`) — one focal color for "Run" and primary CTAs

If you prefer to keep Inter for body and no accent (pure black/white), let me know and I'll revert those. The rest is your existing system, just structured and documented.