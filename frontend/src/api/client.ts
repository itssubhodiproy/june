import { getToken } from "./auth"
import { forceLogout } from "@/stores/auth-store"

export async function fetchWithAuth<T = unknown>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()

  if (!token) {
    forceLogout()
    throw new Error("Not authenticated")
  }

  const headers: HeadersInit = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  }

  const res = await fetch(url, { ...options, headers })

  if (res.status === 401) {
    forceLogout()
    throw new Error("Not authenticated")
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? "Request failed")
  }

  if (res.status === 204) {
    return undefined as T
  }

  return res.json()
}
