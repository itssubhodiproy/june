import { useAuthActions, useIsAuthenticated, useUser, useIsCheckingAuth } from "@/stores/auth-store"

export function useAuth() {
  const user = useUser()
  const isAuthenticated = useIsAuthenticated()
  const isChecking = useIsCheckingAuth()
  const actions = useAuthActions()

  return {
    user,
    isAuthenticated,
    isChecking,
    ...actions,
  }
}
