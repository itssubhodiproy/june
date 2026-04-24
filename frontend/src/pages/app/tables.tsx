"use client"

import { useState } from "react"

import { Button } from "@/components/ui/button"
import { TableCard } from "@/components/table/table-card"
import { TableListRow } from "@/components/table/table-list-row"
import { DeleteTableDialog } from "@/components/table/delete-table-dialog"
import { useTables } from "@/hooks/use-tables"
import type { Table } from "@/types/models"
import { Plus, Table2, List, LayoutGrid } from "lucide-react"

type ViewMode = "grid" | "list"

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-secondary">
        <Table2 className="size-6 text-muted-foreground" />
      </div>
      <h2 className="mb-2 text-lg font-semibold">No tables yet</h2>
      <p className="mb-6 max-w-sm text-sm text-muted-foreground">
        Create your first table to start extracting structured data from your documents.
      </p>
      <Button onClick={onCreate}>
        <Plus className="size-4" data-icon="inline-start" />
        New table
      </Button>
    </div>
  )
}

export function TablesPage() {
  const { tables, isLoading, error, isCreating, isDeleting, loadTables, handleCreate, handleDelete } = useTables()
  const [view, setView] = useState<ViewMode>("grid")
  const [deleteTarget, setDeleteTarget] = useState<Table | null>(null)

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    )
  }

  if (error && tables.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        <p className="mb-4 text-sm text-destructive">{error}</p>
        <Button variant="outline" onClick={loadTables}>
          Try again
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden h-full bg-secondary/30">
      <header className="flex shrink-0 items-center justify-between border-b px-6 py-3">
        <div className="text-lg font-semibold">Tables</div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setView(view === "grid" ? "list" : "grid")}
            aria-label="Toggle view"
          >
            {view === "grid" ? <LayoutGrid /> : <List />}
          </Button>
          <Button onClick={handleCreate} disabled={isCreating}>
            <Plus className="size-4" data-icon="inline-start" />
            {isCreating ? "Creating..." : "New table"}
          </Button>
        </div>
      </header>

      {tables.length === 0 ? (
        <EmptyState onCreate={handleCreate} />
      ) : view === "grid" ? (
        <div className="flex-1 overflow-y-auto p-5">
          <div className="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-3">
            {tables.map((table) => (
              <TableCard
                key={table.id}
                table={table}
                onDelete={setDeleteTarget}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto bg-card">
          <div className="border-b border-border bg-secondary/50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <div className="grid grid-cols-[1fr_100px_100px_100px_40px]">
              <span>Name</span>
              <span>Documents</span>
              <span>Columns</span>
              <span>Updated</span>
              <span />
            </div>
          </div>
          {tables.map((table) => (
            <TableListRow
              key={table.id}
              table={table}
              onDelete={setDeleteTarget}
            />
          ))}
        </div>
      )}

      <DeleteTableDialog
        table={deleteTarget}
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget) {
            void handleDelete(deleteTarget.id)
            setDeleteTarget(null)
          }
        }}
        pending={isDeleting}
      />
    </div>
  )
}
