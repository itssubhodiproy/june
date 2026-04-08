"use client"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { AlertTriangle } from "lucide-react"
import type { Table } from "@/types/models"

interface DeleteTableDialogProps {
  table: Table | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  pending: boolean
}

export function DeleteTableDialog({
  table,
  open,
  onOpenChange,
  onConfirm,
  pending,
}: DeleteTableDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <div className="mb-4 flex size-10 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
            <AlertTriangle className="size-5" />
          </div>
          <DialogTitle>Delete "{table?.name}"?</DialogTitle>
          <DialogDescription>
            This will permanently delete the table and all its documents and extracted
            data. This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={pending}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={pending}>
            {pending ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
