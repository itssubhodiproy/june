import { FileText } from "lucide-react"

import { cn } from "@/lib/utils"
import type { TableDocument } from "@/types/models"

interface DocumentCellProps {
  document: TableDocument
}

const MAX_VISIBLE_FILE_NAME_LENGTH = 38

function truncateDocumentName(fileName: string) {
  if (fileName.length <= MAX_VISIBLE_FILE_NAME_LENGTH) {
    return fileName
  }

  const extensionStart = fileName.lastIndexOf(".")

  if (extensionStart <= 0 || extensionStart === fileName.length - 1) {
    return `${fileName.slice(0, MAX_VISIBLE_FILE_NAME_LENGTH - 1)}…`
  }

  const extension = fileName.slice(extensionStart)
  const baseName = fileName.slice(0, extensionStart)
  const availableBaseLength = Math.max(12, MAX_VISIBLE_FILE_NAME_LENGTH - extension.length - 1)
  const prefixLength = Math.ceil(availableBaseLength * 0.7)
  const suffixLength = Math.max(4, availableBaseLength - prefixLength)

  return `${baseName.slice(0, prefixLength)}…${baseName.slice(-suffixLength)}${extension}`
}

function getParseStatusLabel(status: TableDocument["parse_status"]) {
  switch (status) {
    case "ready":
      return "Ready"
    case "error":
      return "Error"
    case "queued":
      return "Not ready"
    default:
      return "Not ready"
  }
}

export function DocumentCell({ document }: DocumentCellProps) {
  const isNotReady = document.parse_status === "not_ready" || document.parse_status === "queued"
  const isError = document.parse_status === "error"

  return (
    <div
      className={cn(
        "flex min-w-0 items-center gap-3",
        isNotReady && "opacity-65",
        isError && "opacity-100"
      )}
    >
      <div
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-xl bg-secondary text-muted-foreground",
          isError && "bg-destructive/10 text-destructive"
        )}
      >
        <FileText className="size-4" aria-hidden="true" />
      </div>
      <div className="min-w-0">
        <div className="truncate text-sm font-medium" title={document.file_name}>
          {truncateDocumentName(document.file_name)}
        </div>
        <div
          className={cn(
            "text-xs text-muted-foreground",
            isError && "text-destructive"
          )}
        >
          {getParseStatusLabel(document.parse_status)}
          {document.page_count !== null ? ` • ${document.page_count} pages` : ""}
        </div>
      </div>
    </div>
  )
}
