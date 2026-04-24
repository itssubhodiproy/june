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
  addDocumentOptimistic: (document) => {
    set((state) => {
      if (state.documents.byId[document.id]) {
        return state
      }

      return {
        documents: {
          order: [...state.documents.order, document.id],
          byId: {
            ...state.documents.byId,
            [document.id]: document,
          },
        },
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

export function useAddDocumentOptimistic() {
  return useTableStore((state) => state.addDocumentOptimistic)
}

export function useUpdateDocumentStatus() {
  return useTableStore((state) => state.updateDocumentStatus)
}

export function useClearTable() {
  return useTableStore((state) => state.clearTable)
}
