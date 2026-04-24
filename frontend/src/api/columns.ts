import type {
  ColumnCreateRequest,
  ColumnCreateResponse,
  ColumnUpdateRequest,
  ColumnUpdateResponse,
} from "@/types/api"

import { fetchWithAuth } from "./client"

export async function createColumn(
  tableId: string,
  data: ColumnCreateRequest
): Promise<ColumnCreateResponse> {
  return fetchWithAuth<ColumnCreateResponse>(`/api/tables/${tableId}/columns/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export async function updateColumn(
  tableId: string,
  columnId: string,
  data: ColumnUpdateRequest
): Promise<ColumnUpdateResponse> {
  return fetchWithAuth<ColumnUpdateResponse>(`/api/tables/${tableId}/columns/${columnId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export async function deleteColumn(tableId: string, columnId: string): Promise<void> {
  return fetchWithAuth<void>(`/api/tables/${tableId}/columns/${columnId}`, {
    method: "DELETE",
  })
}
