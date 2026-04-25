import { useState, type ComponentType } from "react"
import { Outlet, NavLink } from "react-router-dom"
import {
  BookOpen,
  MessageSquare,
  Settings,
  User,
  LogOut,
  Table2,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuthActions, useUser } from "@/stores/auth-store"

export function AppLayout() {
  const [expanded, setExpanded] = useState(true)
  const user = useUser()
  const { logout } = useAuthActions()

  return (
    <div className="flex h-svh overflow-hidden bg-background">
      <aside
        className={cn(
          "flex h-svh flex-col overflow-hidden border-r bg-muted transition-[width] duration-200 ease-out",
          expanded ? "w-[210px]" : "w-[52px]"
        )}
      >
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="flex h-12 w-full flex-shrink-0 items-center gap-[10px] overflow-hidden border-b px-[10px] text-left transition-colors hover:bg-background/60 w-1 cursor-ew-resize"
          aria-label={expanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          <div className="size-8 shrink-0 overflow-hidden rounded-md">
            <img src="/logo-dark.png" alt="June" className="size-full object-contain dark:hidden" />
            <img src="/logo-light.png" alt="June" className="size-full object-contain hidden dark:block" />
          </div>
          <span
            className={cn(
              "whitespace-nowrap text-[15px] font-semibold tracking-[-0.02em] transition-all duration-150",
              expanded ? "translate-x-0 opacity-100" : "-translate-x-1 opacity-0"
            )}
          >
            June
          </span>
        </button>

        <nav className="flex flex-1 flex-col gap-px p-2">
          <SidebarLink to="/app/tables" expanded={expanded} icon={Table2} label="Tables" />
          <SidebarItem expanded={expanded} icon={BookOpen} label="Vault" soon disabled />
          <SidebarItem expanded={expanded} icon={MessageSquare} label="Assistant" soon disabled />
        </nav>

        <div className="border-t p-2">
          <SidebarItem expanded={expanded} icon={Settings} label="Settings" />
          <SidebarItem expanded={expanded} icon={User} label={user?.email ?? "Account"} subtle />
          <button
            type="button"
            onClick={logout}
            className="flex h-[34px] w-full items-center gap-[10px] overflow-hidden rounded-md px-2 text-left text-muted-foreground transition-colors hover:bg-background hover:text-foreground cursor-pointer"
          >
            <LogOut className="size-[18px] shrink-0" />
            <span
              className={cn(
                "whitespace-nowrap text-[13px] font-medium transition-all duration-150",
                expanded ? "translate-x-0 opacity-100" : "-translate-x-1 opacity-0"
              )}
            >
              Sign out
            </span>
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <main className="min-h-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

type SidebarIcon = ComponentType<{ className?: string }>

function SidebarLink({
  to,
  icon: Icon,
  label,
  expanded,
  end = false,
}: {
  to: string
  icon: SidebarIcon
  label: string
  expanded: boolean
  end?: boolean
}) {
  return (
    <NavLink to={to} end={end} className={({ isActive }) => sidebarItemClass(isActive)}>
      <Icon className="size-[18px] shrink-0" />
      <span className={sidebarLabelClass(expanded)}>{label}</span>
    </NavLink>
  )
}

function SidebarItem({
  icon: Icon,
  label,
  expanded,
  active = false,
  disabled = false,
  soon = false,
  subtle = false,
}: {
  icon: SidebarIcon
  label: string
  expanded: boolean
  active?: boolean
  disabled?: boolean
  soon?: boolean
  subtle?: boolean
}) {
  return (
    <div
      className={cn(
        sidebarItemClass(active),
        disabled && "cursor-default opacity-40",
        subtle && "text-muted-foreground"
      )}
    >
      <Icon className="size-[18px] shrink-0" />
      <span className={sidebarLabelClass(expanded)}>{label}</span>
      {soon && (
        <span
          className={cn(
            "shrink-0 rounded bg-border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-[0.02em] text-muted-foreground transition-all duration-150",
            expanded ? "translate-x-0 opacity-100" : "-translate-x-1 opacity-0"
          )}
        >
          Soon
        </span>
      )}
    </div>
  )
}

function sidebarItemClass(active: boolean) {
  return cn(
    "flex h-[34px] items-center gap-[10px] overflow-hidden rounded-md px-2 text-[13px] text-muted-foreground transition-colors",
    active
      ? "bg-background text-foreground shadow-sm"
      : "hover:bg-background/80 hover:text-foreground"
  )
}

function sidebarLabelClass(expanded: boolean) {
  return cn(
    "whitespace-nowrap text-[13px] font-medium transition-all duration-150",
    expanded ? "translate-x-0 opacity-100" : "-translate-x-1 opacity-0"
  )
}
