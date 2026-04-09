import { useMemo } from "react"

import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table"
import { Plus } from "lucide-react"

import { ColumnHeader } from "@/components/table/column-header"
import { DataCell } from "@/components/table/data-cell"
import { DocumentCell } from "@/components/table/document-cell"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { TableCell, TableColumn, TableDocument } from "@/types/models"

interface OrderedItems<T> {
  order: string[]
  byId: Record<string, T>
}

interface TableGridProps {
  documents: OrderedItems<TableDocument>
  columns: OrderedItems<TableColumn>
  cells: Record<string, TableCell>
}

interface TableRow {
  id: string
  document: TableDocument
  cells: Record<string, TableCell | undefined>
}

const columnHelper = createColumnHelper<TableRow>()

function getCellKey(documentId: string, columnId: string) {
  return `${documentId}::${columnId}`
}

export function TableGrid({ documents, columns, cells }: TableGridProps) {
  const data = useMemo<TableRow[]>(
    () =>
      documents.order.map((documentId) => {
        const document = documents.byId[documentId]
        const rowCells = Object.fromEntries(
          columns.order.map((columnId) => [
            columnId,
            cells[getCellKey(documentId, columnId)],
          ])
        ) as Record<string, TableCell | undefined>

        return {
          id: documentId,
          document,
          cells: rowCells,
        }
      }),
    [cells, columns, documents]
  )

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tableColumns = useMemo<ColumnDef<TableRow, any>[]>(
    () => [
      columnHelper.display({
        id: "gutter",
        header: () => null,
        cell: () => null,
        size: 40,
      }),
      columnHelper.accessor("document", {
        id: "document",
        header: () => (
          <div className="flex items-center gap-2 text-muted-foreground">
            <span className="text-foreground">Document</span>
          </div>
        ),
        cell: ({ getValue }) => <DocumentCell document={getValue()} />,
        size: 288,
      }),
      ...columns.order.map((columnId) =>
        columnHelper.display({
          id: columnId,
          header: () => <ColumnHeader column={columns.byId[columnId]} />,
          cell: ({ row }) => <DataCell cell={row.original.cells[columnId]} />,
          size: 320,
        })
      ),
      columnHelper.display({
        id: "add-column",
        header: () => (
          <Button type="button" variant="ghost" size="sm" className="w-full justify-start" disabled>
            <Plus className="size-4" data-icon="inline-start" />
            Add Column
          </Button>
        ),
        cell: () => null,
        size: 156,
      }),
    ],
    [columns]
  )

  // TanStack Table is intentionally used here per docs/frontend.md.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
  })

  const hasRows = data.length > 0
  const columnCount = table.getAllColumns().length

  return (
    <div className="min-h-0 flex-1 overflow-hidden bg-secondary/30">
      <div className="h-full overflow-auto px-6 py-5">
        <div className="min-w-max rounded-[1.25rem] border bg-background shadow-sm">
          <table className="w-full border-collapse">
            <thead className="sticky top-0 z-10 bg-background">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} className="border-b">
                  {headerGroup.headers.map((header) => {
                    const isGutter = header.column.id === "gutter"
                    const isDocument = header.column.id === "document"

                    return (
                      <th
                        key={header.id}
                        className={cn(
                          "align-middle text-left",
                          isGutter
                            ? "w-10 min-w-10 border-r px-3 py-3"
                            : isDocument
                              ? "min-w-[260px] max-w-[320px] px-4 py-3 text-sm font-semibold"
                              : "min-w-[280px] max-w-[360px] border-l px-4 py-3"
                        )}
                        style={{ width: header.getSize() }}
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(header.column.columnDef.header, header.getContext())}
                      </th>
                    )
                  })}
                </tr>
              ))}
            </thead>
            <tbody>
              {hasRows ? (
                table.getRowModel().rows.map((row, rowIndex) => (
                  <tr
                    key={row.id}
                    className={cn("border-b last:border-b-0", rowIndex % 2 === 1 && "bg-secondary/20")}
                  >
                    {row.getVisibleCells().map((cell) => {
                      const isGutter = cell.column.id === "gutter"
                      const isDocument = cell.column.id === "document"
                      const isAddColumn = cell.column.id === "add-column"

                      return (
                        <td
                          key={cell.id}
                          className={cn(
                            "align-top",
                            isGutter
                              ? "border-r px-3 py-4"
                              : isDocument
                                ? "px-4 py-4"
                                : isAddColumn
                                  ? "border-l px-3 py-4"
                                  : "border-l px-4 py-4"
                          )}
                          style={{ width: cell.column.getSize() }}
                        >
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      )
                    })}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={columnCount} className="px-6 py-16 text-center">
                    <div className="mx-auto max-w-md">
                      <p className="text-sm font-medium text-foreground">No documents yet</p>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Upload documents to start populating rows in this table.
                      </p>
                      {columns.order.length === 0 ? (
                        <p className="mt-4 text-xs text-muted-foreground">
                          Columns will appear here once they are added.
                        </p>
                      ) : null}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
