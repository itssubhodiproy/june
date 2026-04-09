import { create } from "zustand"

import type { TableCell, TableColumn, TableDetail, TableDocument } from "@/types/models"

interface OrderedItems<T> {
  order: string[]
  byId: Record<string, T>
}

interface TableMeta {
  id: string
  workspace_id: string
  name: string
  created_at: string
  updated_at: string
}

interface TableStore {
  table: TableMeta | null
  documents: OrderedItems<TableDocument>
  columns: OrderedItems<TableColumn>
  cells: Record<string, TableCell>
  hydrateTable: (payload: TableDetail) => void
  clearTable: () => void
}

function emptyOrderedItems<T>(): OrderedItems<T> {
  return { order: [], byId: {} }
}

function getCellKey(documentId: string, columnId: string) {
  return `${documentId}::${columnId}`
}

export const useTableStore = create<TableStore>()((set) => ({
  table: null,
  documents: emptyOrderedItems<TableDocument>(),
  columns: emptyOrderedItems<TableColumn>(),
  cells: {},
  hydrateTable: (payload) => {
    const documents = payload.documents.reduce<OrderedItems<TableDocument>>(
      (acc, document) => {
        acc.order.push(document.id)
        acc.byId[document.id] = document
        return acc
      },
      emptyOrderedItems<TableDocument>()
    )

    const columns = payload.columns.reduce<OrderedItems<TableColumn>>(
      (acc, column) => {
        acc.order.push(column.id)
        acc.byId[column.id] = column
        return acc
      },
      emptyOrderedItems<TableColumn>()
    )

    const cells = payload.cells.reduce<Record<string, TableCell>>((acc, cell) => {
      acc[getCellKey(cell.document_id, cell.column_id)] = cell
      return acc
    }, {})

    set({
      table: {
        id: payload.id,
        workspace_id: payload.workspace_id,
        name: payload.name,
        created_at: payload.created_at,
        updated_at: payload.updated_at,
      },
      documents,
      columns,
      cells,
    })
  },
  clearTable: () => {
    set({
      table: null,
      documents: emptyOrderedItems<TableDocument>(),
      columns: emptyOrderedItems<TableColumn>(),
      cells: {},
    })
  },
}))

export function useTableMeta() {
  return useTableStore((state) => state.table)
}

export function useTableDocuments() {
  return useTableStore((state) => state.documents)
}

export function useTableColumns() {
  return useTableStore((state) => state.columns)
}

export function useTableCells() {
  return useTableStore((state) => state.cells)
}

export function useHydrateTable() {
  return useTableStore((state) => state.hydrateTable)
}

export function useClearTable() {
  return useTableStore((state) => state.clearTable)
}
