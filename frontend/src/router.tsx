import { createBrowserRouter, Navigate } from "react-router-dom"
import { LandingPage } from "@/pages/landing"
import { LoginPage } from "@/pages/login"
import { AppLayout } from "@/pages/app/layout"
import { TablesPage } from "@/pages/app/tables"
import { TablePage } from "@/pages/app/table"
import { AuthGuard } from "@/components/auth-guard"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/app",
    element: (
      <AuthGuard>
        <AppLayout />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/app/tables" replace />,
      },
      {
        path: "tables",
        element: <TablesPage />,
      },
      {
        path: "tables/:tableId",
        element: <TablePage />,
      },
    ],
  },
])
