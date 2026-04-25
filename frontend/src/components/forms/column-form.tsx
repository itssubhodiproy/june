import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import type { TableColumn } from "@/types/models"

const COLUMN_TYPES = [
  { value: "free_response", label: "Free Response" },
  { value: "yes_no", label: "Yes / No" },
  { value: "date", label: "Date" },
  { value: "currency", label: "Currency" },
  { value: "verbatim", label: "Verbatim" },
] as const

interface ColumnFormData {
  title: string
  prompt: string
  type: TableColumn["type"]
}

interface ColumnFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: ColumnFormData) => void
  defaultValues?: TableColumn | null
}

export function ColumnForm({ open, onOpenChange, onSubmit, defaultValues }: ColumnFormProps) {
  const isEdit = defaultValues !== null && defaultValues !== undefined
  const [title, setTitle] = useState(defaultValues?.title ?? "")
  const [prompt, setPrompt] = useState(defaultValues?.prompt ?? "")
  const [type, setType] = useState<TableColumn["type"]>(defaultValues?.type ?? "free_response")

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()

    const trimmedTitle = title.trim()
    const trimmedPrompt = prompt.trim()

    if (!trimmedTitle || !trimmedPrompt) return

    onSubmit({ title: trimmedTitle, prompt: trimmedPrompt, type })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEdit ? "Edit Column" : "Add Column"}</DialogTitle>
            <DialogDescription>
              {isEdit
                ? "Update the column's title, prompt, or type."
                : "Define a question to extract from every document."}
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="column-title">Title</Label>
              <Input
                id="column-title"
                placeholder="e.g. Liability Cap"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                autoFocus
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="column-prompt">Prompt</Label>
              <Textarea
                id="column-prompt"
                placeholder="e.g. What is the aggregate liability cap?"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                rows={3}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="column-type">Type</Label>
              <Select value={type} onValueChange={(value) => setType(value as TableColumn["type"])}>
                <SelectTrigger id="column-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COLUMN_TYPES.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!title.trim() || !prompt.trim()}>
              {isEdit ? "Save Changes" : "Add Column"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
