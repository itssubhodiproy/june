import { create } from "zustand"
import { login as loginApi, register as registerApi, getMe, type User } from "@/api/auth"
import { setToken, clearToken, getToken } from "@/api/auth"

interface AuthState {
  user: User | null
  token: string | null
  isChecking: boolean
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  register: (email: string, name: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

const useAuthStore = create<AuthState & { actions: AuthActions }>()((set) => ({
  user: null,
  token: getToken(),
  isChecking: true,

  actions: {
    login: async (email: string, password: string) => {
      const { access_token } = await loginApi({ email, password })
      setToken(access_token)
      set({ token: access_token })
      const user = await getMe()
      set({ user })
    },

    register: async (email: string, name: string, password: string) => {
      await registerApi({ email, name, password })
    },

    logout: () => {
      clearToken()
      set({ user: null, token: null })
    },

    checkAuth: async () => {
      const token = getToken()
      if (!token) {
        set({ isChecking: false })
        return
      }
      try {
        const user = await getMe()
        set({ user, token, isChecking: false })
      } catch {
        clearToken()
        set({ user: null, token: null, isChecking: false })
      }
    },
  },
}))

export function useUser() {
  return useAuthStore((s) => s.user)
}

export function useIsAuthenticated() {
  return useAuthStore((s) => s.token !== null)
}

export function useIsCheckingAuth() {
  return useAuthStore((s) => s.isChecking)
}

export function useAuthActions() {
  return useAuthStore((s) => s.actions)
}
