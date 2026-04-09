"use client"

import { useNavigate } from "react-router-dom"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { formatRelativeDate } from "@/lib/utils"
import { MoreHorizontal, Trash2, Table2 } from "lucide-react"
import type { Table } from "@/types/models"

interface TableCardProps {
  table: Table
  onDelete: (table: Table) => void
}

export function TableCard({ table, onDelete }: TableCardProps) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/app/tables/${table.id}`)}
      aria-label={`Open ${table.name}`}
      className="group relative rounded-xl border border-border bg-card p-4 transition-all hover:border-foreground/20 hover:shadow-md cursor-pointer"
    >
      <div className="relative mb-3 flex size-8 items-center justify-center rounded-lg bg-secondary">
        <Table2 className="size-4 text-muted-foreground" />
      </div>

      <h3 className="relative mb-1 truncate text-sm font-semibold leading-snug tracking-tight">
        {table.name}
      </h3>

      <div className="relative flex items-center gap-3 text-xs text-muted-foreground">
        <span>{table.document_count} docs</span>
        <span>{table.column_count} cols</span>
      </div>

      <div className="relative mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
        {formatRelativeDate(table.updated_at)}
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="icon-sm"
            className="absolute top-3 right-3 z-10 opacity-0 transition-opacity group-hover:opacity-100 data-[state=open]:opacity-100"
            aria-label="Table options"
          >
            <MoreHorizontal />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            variant="destructive"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(table)
            }}
          >
            <Trash2 />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
