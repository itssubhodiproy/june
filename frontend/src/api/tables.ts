import type { Table, TableDetail } from "@/types/models"
import { fetchWithAuth } from "./client"

export async function getTables(workspaceId: string): Promise<Table[]> {
  return fetchWithAuth<Table[]>(`/api/tables?workspace_id=${workspaceId}`)
}

export async function getTable(tableId: string): Promise<TableDetail> {
  return fetchWithAuth<TableDetail>(`/api/tables/${tableId}`)
}

export async function createTable(data: {
  workspace_id: string
  name: string
}): Promise<Table> {
  return fetchWithAuth<Table>("/api/tables", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export async function deleteTable(id: string): Promise<void> {
  return fetchWithAuth<void>(`/api/tables/${id}`, {
    method: "DELETE",
  })
}
