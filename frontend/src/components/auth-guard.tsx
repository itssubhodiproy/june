import { Navigate } from "react-router-dom"
import { useIsCheckingAuth, useIsAuthenticated } from "@/stores/auth-store"

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const isChecking = useIsCheckingAuth()
  const isAuthenticated = useIsAuthenticated()

  if (isChecking) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}
