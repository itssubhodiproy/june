"use client"

import { Link } from "react-router-dom"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { formatRelativeDate } from "@/lib/utils"
import { MoreHorizontal, Trash2 } from "lucide-react"
import type { Table } from "@/types/models"

interface TableListRowProps {
  table: Table
  onDelete: (table: Table) => void
}

export function TableListRow({ table, onDelete }: TableListRowProps) {
  return (
    <div
      className="group relative grid grid-cols-[1fr_100px_100px_100px_40px] items-center border-b border-border px-4 py-3 transition-colors hover:bg-secondary/50"
    >
      <Link
        to={`/app/tables/${table.id}`}
        className="absolute inset-0"
        aria-label={`Open ${table.name}`}
      />

      <span className="relative truncate text-sm font-medium">{table.name}</span>
      <span className="relative text-sm text-muted-foreground">{table.document_count}</span>
      <span className="relative text-sm text-muted-foreground">{table.column_count}</span>
      <span className="relative text-sm text-muted-foreground">
        {formatRelativeDate(table.updated_at)}
      </span>
      <div className="relative z-10 flex justify-center opacity-0 transition-opacity group-hover:opacity-100">
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-muted-foreground hover:text-foreground"
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
    </div>
  )
}
