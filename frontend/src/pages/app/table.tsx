import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"

import { getTable } from "@/api/tables"
import { ColumnForm } from "@/components/forms/column-form"
import { TableGrid } from "@/components/table/table-grid"
import { TableHeader } from "@/components/table/table-header"
import { Button } from "@/components/ui/button"
import { useColumns } from "@/hooks/use-columns"
import { useUpload } from "@/hooks/use-upload"
import { cn } from "@/lib/utils"
import {
  useClearTable,
  useTableCells,
  useTableColumns,
  useTableDocuments,
  useHydrateTable,
  useTableMeta,
} from "@/stores/table-store"

export function TablePage() {
  const { tableId } = useParams<{ tableId: string }>()
  const table = useTableMeta()
  const documents = useTableDocuments()
  const columns = useTableColumns()
  const cells = useTableCells()
  const hydrateTable = useHydrateTable()
  const clearTable = useClearTable()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryKey, setRetryKey] = useState(0)
  const { isUploading, isDragActive, lastError, clearLastError, startUpload, dragHandlers, handleDeleteDocument } = useUpload(tableId)
  const {
    columnFormOpen,
    setColumnFormOpen,
    columnFormVersion,
    editingColumn,
    openAddColumn,
    openEditColumn,
    handleColumnFormSubmit,
    handleDeleteColumn,
  } = useColumns(tableId)

  useEffect(() => {
    let cancelled = false

    async function loadTable() {
      if (!tableId) {
        setError("Missing table id")
        setIsLoading(false)
        clearTable()
        return
      }

      try {
        setIsLoading(true)
        setError(null)
        const payload = await getTable(tableId)
        if (cancelled) return
        hydrateTable(payload)
      } catch (err) {
        if (cancelled) return
        clearTable()
        setError(err instanceof Error ? err.message : "Failed to load table")
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    loadTable()

    return () => {
      cancelled = true
      clearTable()
    }
  }, [clearTable, hydrateTable, retryKey, tableId])

  if (isLoading) {
    return (
      <div className="flex h-full min-h-0 flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    )
  }

  if (error || !table) {
    return (
      <div className="flex h-full min-h-0 flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        <p className="mb-4 text-sm text-destructive">{error ?? "Table not found"}</p>
        <Button type="button" variant="outline" onClick={() => setRetryKey((value) => value + 1)}>
          Try again
        </Button>
      </div>
    )
  }

  return (
    <div
      className="relative flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-background"
      {...dragHandlers}
    >
      <TableHeader
        title={table.name}
        isUploading={isUploading}
        uploadError={lastError}
        onSelectFiles={(files) => {
          clearLastError()
          void startUpload(files)
        }}
        onAddColumn={openAddColumn}
      />
      <div className="relative flex min-h-0 flex-1 flex-col">
        <TableGrid
          documents={documents}
          columns={columns}
          cells={cells}
          onAddColumn={openAddColumn}
          onEditColumn={openEditColumn}
          onDeleteColumn={handleDeleteColumn}
          onDeleteDocument={handleDeleteDocument}
        />
        <div
          className={cn(
            "pointer-events-none absolute inset-5 z-20 hidden rounded-[1.5rem] border-2 border-dashed border-primary/30 bg-background/90 p-6 backdrop-blur-sm",
            isDragActive && "flex items-center justify-center"
          )}
        >
          <div className="flex max-w-sm flex-col items-center gap-2 text-center">
            <p className="text-base font-medium text-foreground">Drop PDFs to upload</p>
            <p className="text-sm text-muted-foreground">
              Files will appear in the table immediately and stay muted until they are ready.
            </p>
          </div>
        </div>
      </div>
      <ColumnForm
        key={`${editingColumn?.id ?? "new"}:${columnFormVersion}`}
        open={columnFormOpen}
        onOpenChange={setColumnFormOpen}
        onSubmit={handleColumnFormSubmit}
        defaultValues={editingColumn}
      />
    </div>
  )
}
