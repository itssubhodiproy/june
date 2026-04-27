import { StrictMode, useEffect } from "react"
import { createRoot } from "react-dom/client"
import { RouterProvider } from "react-router-dom"

import "./index.css"
import { router } from "./router"
import { ThemeProvider } from "@/components/theme-provider.tsx"
import { useAuthActions } from "@/stores/auth-store"

export function AppWithAuth() {
  const { checkAuth } = useAuthActions()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return <RouterProvider router={router} />
}

createRoot(document.getElementById("root")!).render(
  <ThemeProvider>
    <AppWithAuth />
  </ThemeProvider>
)
