import { getToken } from "./auth"
import type { Table } from "@/types/models"

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getToken()
  const headers: HeadersInit = {
    ...options.headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  const res = await fetch(url, { ...options, headers })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? "Request failed")
  }

  if (res.status === 204) return
  return res.json()
}

export async function getTables(workspaceId: string): Promise<Table[]> {
  return fetchWithAuth(`/api/tables?workspace_id=${workspaceId}`)
}

export async function createTable(data: {
  workspace_id: string
  name: string
}): Promise<Table> {
  return fetchWithAuth("/api/tables", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export async function deleteTable(id: string): Promise<void> {
  return fetchWithAuth(`/api/tables/${id}`, {
    method: "DELETE",
  })
}
