import { cn } from "@/lib/utils"
import type { TableCell } from "@/types/models"

interface DataCellProps {
  cell: TableCell | undefined
}

const statusLabel: Record<TableCell["status"], string> = {
  empty: "Empty",
  extracting: "Running…",
  completed: "Completed",
  stale: "Stale",
  error: "Error",
}

export function DataCell({ cell }: DataCellProps) {
  if (!cell) {
    return <span className="text-sm text-muted-foreground">—</span>
  }

  if (!cell.answer) {
    return (
      <span
        className={cn(
          "text-xs font-medium",
          cell.status === "error" ? "text-destructive" : "text-muted-foreground"
        )}
      >
        {statusLabel[cell.status]}
      </span>
    )
  }

  return (
    <div className="min-w-0">
      <p className="line-clamp-3 break-words text-sm leading-5 text-foreground">{cell.answer}</p>
    </div>
  )
}
