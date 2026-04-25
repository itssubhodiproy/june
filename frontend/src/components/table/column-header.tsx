import { MoreHorizontal, Pencil, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import type { TableColumn } from "@/types/models"

const typeBadgeLabel: Record<TableColumn["type"], string> = {
  free_response: "T",
  yes_no: "Y/N",
  date: "DATE",
  currency: "$",
  verbatim: "TXT",
}

interface ColumnHeaderProps {
  column: TableColumn
  onEdit: (column: TableColumn) => void
  onDelete: (columnId: string) => void
}

export function ColumnHeader({ column, onEdit, onDelete }: ColumnHeaderProps) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <span
        className={cn(
          "inline-flex h-5 shrink-0 items-center rounded-full border border-border bg-secondary px-1.5 text-[10px] font-semibold tracking-[0.08em] text-muted-foreground uppercase",
          column.type === "currency" && "px-2 tracking-[0.02em]"
        )}
      >
        {typeBadgeLabel[column.type]}
      </span>
      <span className="min-w-0 truncate text-sm font-medium">{column.title}</span>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon-xs"
            className="ml-auto shrink-0 text-muted-foreground"
            aria-label={`Column options for ${column.title}`}
          >
            <MoreHorizontal />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => onEdit(column)}>
            <Pencil data-icon="inline-start" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem
            className="text-destructive focus:text-destructive"
            onClick={() => onDelete(column.id)}
          >
            <Trash2 data-icon="inline-start" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
