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
  useTableCells,
  useTableColumns,
  useUpdateColumn,
  useRestoreCells,
  useRestoreColumnsOrder,
} from "@/stores/table-store"
import type { TableColumn } from "@/types/models"

export function useColumns(tableId?: string) {
  const columns = useTableColumns()
  const cells = useTableCells()
  const storeAddColumn = useAddColumn()
  const storeUpdateColumn = useUpdateColumn()
  const storeDeleteColumn = useDeleteColumn()
  const storeRestoreCells = useRestoreCells()
  const restoreColumnsOrder = useRestoreColumnsOrder()
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
        const cellsSnapshot = { ...cells }
        storeUpdateColumn(editingColumn.id, data)

        try {
          await apiUpdateColumn(tableId, editingColumn.id, data)
        } catch {
          storeUpdateColumn(snapshot.id, snapshot)
          storeRestoreCells(cellsSnapshot)
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
    [tableId, editingColumn, cells, storeAddColumn, storeUpdateColumn, storeRestoreCells]
  )

  const handleDeleteColumn = useCallback(
    async (columnId: string) => {
      if (!tableId) return
      if (!window.confirm("Delete this column and all its cells?")) return

      // Optimistic delete with snapshot for revert
      const columnSnapshot = columns.byId[columnId]
      const cellsSnapshot = { ...cells }
      const orderSnapshot = [...columns.order]
      
      storeDeleteColumn(columnId)

      try {
        await apiDeleteColumn(tableId, columnId)
      } catch {
        if (columnSnapshot) {
          storeAddColumn(columnSnapshot)
          storeRestoreCells(cellsSnapshot)
          restoreColumnsOrder(orderSnapshot)
        }
        try {
          const payload = await getTable(tableId)
          hydrateTable(payload)
        } catch {
          // Silently fail — table will be inconsistent until next load
        }
      }
    },
    [tableId, columns, cells, storeDeleteColumn, storeAddColumn, storeRestoreCells, restoreColumnsOrder, hydrateTable]
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
