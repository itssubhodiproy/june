import { FileText } from "lucide-react"

import { cn } from "@/lib/utils"
import type { TableDocument } from "@/types/models"

interface DocumentCellProps {
  document: TableDocument
}

function getParseStatusLabel(status: TableDocument["parse_status"]) {
  switch (status) {
    case "ready":
      return "Ready"
    case "error":
      return "Error"
    default:
      return "Parsing"
  }
}

export function DocumentCell({ document }: DocumentCellProps) {
  return (
    <div
      className={cn(
        "flex min-w-0 items-center gap-3",
        document.parse_status !== "ready" && "opacity-70"
      )}
    >
      <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-secondary text-muted-foreground">
        <FileText className="size-4" aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <div className="truncate text-sm font-medium">{document.file_name}</div>
        <div className="text-xs text-muted-foreground">
          {getParseStatusLabel(document.parse_status)}
          {document.page_count !== null ? ` • ${document.page_count} pages` : ""}
        </div>
      </div>
    </div>
  )
}
