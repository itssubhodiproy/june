import { FileText, MoreHorizontal, Trash } from "lucide-react"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { TableDocument } from "@/types/models"

interface DocumentCellProps {
  document: TableDocument
  onDelete?: (documentId: string) => void
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

export function DocumentCell({ document, onDelete }: DocumentCellProps) {
  const isNotReady = document.parse_status === "not_ready" || document.parse_status === "queued"
  const isError = document.parse_status === "error"

  return (
    <div className="group relative flex w-full min-w-0 items-center justify-between">
      <div
        className={cn(
          "flex min-w-0 items-center gap-3",
          isNotReady && "opacity-50",
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
        </div>
      </div>

      {onDelete && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              className="ml-2 shrink-0 opacity-0 group-hover:opacity-100 data-[state=open]:opacity-100"
              aria-label="Document options"
            >
              <MoreHorizontal />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[160px]">
            <DropdownMenuItem
              className="text-destructive focus:bg-destructive focus:text-destructive-foreground"
              onClick={() => onDelete(document.id)}
            >
              <Trash />
              Delete document
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  )
}
