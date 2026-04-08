const TOKEN_KEY = "token"

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  name: string
  password: string
}

export interface User {
  id: string
  email: string
  name: string
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
}

export async function login(data: LoginPayload): Promise<AuthResponse> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? "Login failed")
  }

  return res.json()
}

export async function register(data: RegisterPayload): Promise<User> {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? "Registration failed")
  }

  return res.json()
}

export async function getMe(): Promise<User> {
  const token = getToken()
  if (!token) throw new Error("No token")

  const res = await fetch("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!res.ok) throw new Error("Not authenticated")

  return res.json()
}
