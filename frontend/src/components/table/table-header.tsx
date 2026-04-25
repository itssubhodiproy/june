import { Play, Plus } from "lucide-react"

import { UploadButton } from "@/components/forms/upload-button"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface TableHeaderProps {
  title: string
  isUploading?: boolean
  uploadError?: string | null
  onSelectFiles: (files: File[] | FileList) => void
  onAddColumn: () => void
}

export function TableHeader({
  title,
  isUploading = false,
  uploadError = null,
  onSelectFiles,
  onAddColumn,
}: TableHeaderProps) {
  return (
    <header className="flex shrink-0 flex-col gap-2 border-b bg-background px-6 py-3">
      <div className="flex items-center gap-4">
        <div className="min-w-0 flex-1">
          <Input
            value={title}
            readOnly
            name="table_name"
            aria-label="Table name"
            className="h-11 border-none bg-transparent px-0 text-lg font-semibold shadow-none ring-0 focus-visible:border-none focus-visible:ring-0"
          />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <UploadButton onSelectFiles={onSelectFiles} isUploading={isUploading} />
          <Button type="button" variant="outline" size="sm" onClick={onAddColumn}>
            <Plus className="size-4" data-icon="inline-start" />
            Column
          </Button>
          <Button type="button" size="sm" disabled>
            <Play className="size-4" data-icon="inline-start" />
            Run All
          </Button>
        </div>
      </div>
      {uploadError ? <p className="text-sm text-destructive">{uploadError}</p> : null}
    </header>
  )
}

