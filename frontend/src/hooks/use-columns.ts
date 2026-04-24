import { useCallback, useState } from "react"

import {
  createColumn as apiCreateColumn,
  updateColumn as apiUpdateColumn,
  deleteColumn as apiDeleteColumn,
} from "@/api/columns"
import { getTable } from "@/api/tables"
import {
  useAddColumn,
  useDeleteColumn,
  useHydrateTable,
  useTableColumns,
  useUpdateColumn,
} from "@/stores/table-store"
import type { TableColumn } from "@/types/models"

export function useColumns(tableId?: string) {
  const columns = useTableColumns()
  const storeAddColumn = useAddColumn()
  const storeUpdateColumn = useUpdateColumn()
  const storeDeleteColumn = useDeleteColumn()
  const hydrateTable = useHydrateTable()
  const [columnFormOpen, setColumnFormOpen] = useState(false)
  const [editingColumn, setEditingColumn] = useState<TableColumn | null>(null)
  const [columnFormVersion, setColumnFormVersion] = useState(0)

  function openAddColumn() {
    setEditingColumn(null)
    setColumnFormVersion((value) => value + 1)
    setColumnFormOpen(true)
  }

  function openEditColumn(column: TableColumn) {
    setEditingColumn(column)
    setColumnFormVersion((value) => value + 1)
    setColumnFormOpen(true)
  }

  const handleColumnFormSubmit = useCallback(
    async (data: { title: string; prompt: string; type: TableColumn["type"] }) => {
      if (!tableId) return

      if (editingColumn) {
        // Optimistic update for edit
        const snapshot = { ...editingColumn }
        storeUpdateColumn(editingColumn.id, data)

        try {
          await apiUpdateColumn(tableId, editingColumn.id, data)
        } catch {
          storeUpdateColumn(snapshot.id, snapshot)
        }
      } else {
        // Add: not optimistic — need server id + order
        try {
          const created = await apiCreateColumn(tableId, data)
          storeAddColumn({
            id: created.id,
            title: created.title,
            prompt: created.prompt,
            type: created.type,
            order: created.order,
          })
        } catch (err) {
          console.error(err)
        }
      }
    },
    [tableId, editingColumn, storeAddColumn, storeUpdateColumn]
  )

  const handleDeleteColumn = useCallback(
    async (columnId: string) => {
      if (!tableId) return
      if (!window.confirm("Delete this column and all its cells?")) return

      // Optimistic delete with snapshot for revert
      const columnSnapshot = columns.byId[columnId]
      storeDeleteColumn(columnId)

      try {
        await apiDeleteColumn(tableId, columnId)
      } catch {
        if (columnSnapshot) {
          storeAddColumn(columnSnapshot)
        }
        try {
          const payload = await getTable(tableId)
          hydrateTable(payload)
        } catch {
          // Silently fail — table will be inconsistent until next load
        }
      }
    },
    [tableId, columns, storeDeleteColumn, storeAddColumn, hydrateTable]
  )

  return {
    columnFormOpen,
    setColumnFormOpen,
    columnFormVersion,
    editingColumn,
    openAddColumn,
    openEditColumn,
    handleColumnFormSubmit,
    handleDeleteColumn,
  }
}
