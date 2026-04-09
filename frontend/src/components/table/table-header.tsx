import { Play, Plus, Upload } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface TableHeaderProps {
  title: string
}

export function TableHeader({ title }: TableHeaderProps) {
  return (
    <header className="flex shrink-0 items-center gap-4 border-b bg-background px-6 py-3">
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
        <Button type="button" variant="outline" size="sm" disabled>
          <Upload className="size-4" data-icon="inline-start" />
          Upload
        </Button>
        <Button type="button" variant="outline" size="sm" disabled>
          <Plus className="size-4" data-icon="inline-start" />
          Column
        </Button>
        <Button type="button" size="sm" disabled>
          <Play className="size-4" data-icon="inline-start" />
          Run All
        </Button>
      </div>
    </header>
  )
}
