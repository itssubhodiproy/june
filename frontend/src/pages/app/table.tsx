import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"

import { getTable } from "@/api/tables"
import { TableGrid } from "@/components/table/table-grid"
import { TableHeader } from "@/components/table/table-header"
import { Button } from "@/components/ui/button"
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
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-background">
      <TableHeader title={table.name} />
      <TableGrid documents={documents} columns={columns} cells={cells} />
    </div>
  )
}
