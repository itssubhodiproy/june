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
  addDocumentOptimistic: (document: TableDocument) => void
  updateDocumentStatus: (
    documentId: string,
    status: TableDocument["parse_status"],
    pageCount?: number | null
  ) => void
  deleteDocument: (documentId: string) => void
  addColumn: (column: TableColumn) => void
  updateColumn: (columnId: string, updates: Partial<TableColumn>) => void
  deleteColumn: (columnId: string) => void
  clearTable: () => void
  restoreCells: (cells: Record<string, TableCell>) => void
  restoreDocumentsOrder: (order: string[]) => void
  restoreColumnsOrder: (order: string[]) => void
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
  addDocumentOptimistic: (document) => {
    set((state) => {
      if (state.documents.byId[document.id]) {
        return state
      }

      // Create empty cells for every existing column
      const newCells = { ...state.cells }
      for (const colId of state.columns.order) {
        const key = getCellKey(document.id, colId)
        newCells[key] = {
          id: `temp_${key}`,
          document_id: document.id,
          column_id: colId,
          status: "empty",
          answer: null,
          reasoning: null,
          source_references: [],
        }
      }

      return {
        documents: {
          order: [...state.documents.order, document.id],
          byId: {
            ...state.documents.byId,
            [document.id]: document,
          },
        },
        cells: newCells,
      }
    })
  },
  updateDocumentStatus: (documentId, status, pageCount) => {
    set((state) => {
      const document = state.documents.byId[documentId]

      if (!document) {
        return state
      }

      return {
        documents: {
          order: state.documents.order,
          byId: {
            ...state.documents.byId,
            [documentId]: {
              ...document,
              parse_status: status,
              page_count: pageCount ?? document.page_count,
            },
          },
        },
      }
    })
  },
  deleteDocument: (documentId) => {
    set((state) => {
      const newCells: Record<string, TableCell> = {}
      for (const [key, cell] of Object.entries(state.cells)) {
        if (cell.document_id !== documentId) {
          newCells[key] = cell
        }
      }

      const remainingById = { ...state.documents.byId }
      delete remainingById[documentId]

      return {
        documents: {
          order: state.documents.order.filter((id) => id !== documentId),
          byId: remainingById,
        },
        cells: newCells,
      }
    })
  },
  addColumn: (column) => {
    set((state) => {
      if (state.columns.byId[column.id]) {
        return state
      }

      // Create empty cells for every existing document
      const newCells = { ...state.cells }
      for (const docId of state.documents.order) {
        const key = getCellKey(docId, column.id)
        newCells[key] = {
          id: `temp_${key}`,
          document_id: docId,
          column_id: column.id,
          status: "empty",
          answer: null,
          reasoning: null,
          source_references: [],
        }
      }

      return {
        columns: {
          order: [...state.columns.order, column.id],
          byId: { ...state.columns.byId, [column.id]: column },
        },
        cells: newCells,
      }
    })
  },
  updateColumn: (columnId, updates) => {
    set((state) => {
      const column = state.columns.byId[columnId]
      if (!column) return state

      const promptChanged = updates.prompt !== undefined && updates.prompt !== column.prompt
      const typeChanged = updates.type !== undefined && updates.type !== column.type

      const updatedColumn = { ...column, ...updates }

      let newCells = state.cells
      if (promptChanged || typeChanged) {
        newCells = { ...state.cells }
        for (const key of Object.keys(newCells)) {
          const cell = newCells[key]
          if (cell.column_id === columnId && cell.status === "completed") {
            newCells[key] = { ...cell, status: "stale" }
          }
        }
      }

      return {
        columns: {
          order: state.columns.order,
          byId: { ...state.columns.byId, [columnId]: updatedColumn },
        },
        cells: newCells,
      }
    })
  },
  deleteColumn: (columnId) => {
    set((state) => {
      const newCells: Record<string, TableCell> = {}
      for (const [key, cell] of Object.entries(state.cells)) {
        if (cell.column_id !== columnId) {
          newCells[key] = cell
        }
      }

      const remainingById = { ...state.columns.byId }
      delete remainingById[columnId]

      return {
        columns: {
          order: state.columns.order.filter((id) => id !== columnId),
          byId: remainingById,
        },
        cells: newCells,
      }
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
  restoreCells: (cells) => {
    set({ cells })
  },
  restoreDocumentsOrder: (order) => {
    set((state) => ({ documents: { ...state.documents, order } }))
  },
  restoreColumnsOrder: (order) => {
    set((state) => ({ columns: { ...state.columns, order } }))
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

export function useAddDocumentOptimistic() {
  return useTableStore((state) => state.addDocumentOptimistic)
}

export function useUpdateDocumentStatus() {
  return useTableStore((state) => state.updateDocumentStatus)
}

export function useAddColumn() {
  return useTableStore((state) => state.addColumn)
}

export function useUpdateColumn() {
  return useTableStore((state) => state.updateColumn)
}

export function useDeleteColumn() {
  return useTableStore((state) => state.deleteColumn)
}

export function useDeleteDocument() {
  return useTableStore((state) => state.deleteDocument)
}

export function useRestoreDocumentsOrder() {
  return useTableStore((state) => state.restoreDocumentsOrder)
}

export function useRestoreColumnsOrder() {
  return useTableStore((state) => state.restoreColumnsOrder)
}

export function useClearTable() {
  return useTableStore((state) => state.clearTable)
}

export function useRestoreCells() {
  return useTableStore((state) => state.restoreCells)
}
