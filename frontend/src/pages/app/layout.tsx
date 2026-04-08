import { Outlet, Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useAuthActions, useUser } from "@/stores/auth-store"

export function AppLayout() {
  const user = useUser()
  const { logout } = useAuthActions()

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <Link to="/app/tables" className="font-serif text-lg font-medium">
          June
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">{user?.email}</span>
          <Button variant="outline" size="sm" onClick={logout}>
            Sign out
          </Button>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
