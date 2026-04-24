import { useCallback, useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import { createTable, deleteTable, getTables } from "@/api/tables"
import { useUser } from "@/stores/auth-store"
import type { Table } from "@/types/models"

export function useTables() {
  const navigate = useNavigate()
  const user = useUser()
  const workspaceId = user?.last_selected_workspace_id
  const [tables, setTables] = useState<Table[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const loadTables = useCallback(async () => {
    if (!workspaceId) {
      setTables([])
      setError("No workspace selected")
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)
      const data = await getTables(workspaceId)
      setTables(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tables")
    } finally {
      setIsLoading(false)
    }
  }, [workspaceId])

  useEffect(() => {
    loadTables()
  }, [loadTables])

  async function handleCreate() {
    if (!workspaceId || isCreating) return
    setIsCreating(true)

    const optimisticTable: Table = {
      id: `temp_${Date.now()}`,
      workspace_id: workspaceId,
      name: `Untitled Table #${tables.length + 1}`,
      document_count: 0,
      column_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    setTables((prev) => [optimisticTable, ...prev])

    try {
      const newTable = await createTable({
        workspace_id: workspaceId,
        name: optimisticTable.name,
      })
      navigate(`/app/tables/${newTable.id}`)
    } catch (err) {
      setTables((prev) => prev.filter((t) => t.id !== optimisticTable.id))
      setError(err instanceof Error ? err.message : "Failed to create table")
    } finally {
      setIsCreating(false)
    }
  }

  async function handleDelete(tableId: string) {
    if (isDeleting) return
    setIsDeleting(true)

    const previousTables = tables
    setTables((prev) => prev.filter((t) => t.id !== tableId))

    try {
      await deleteTable(tableId)
    } catch (err) {
      setTables(previousTables)
      setError(err instanceof Error ? err.message : "Failed to delete table")
    } finally {
      setIsDeleting(false)
    }
  }

  return {
    tables,
    isLoading,
    error,
    isCreating,
    isDeleting,
    loadTables,
    handleCreate,
    handleDelete,
  }
}
