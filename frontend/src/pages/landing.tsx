import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useIsAuthenticated } from "@/stores/auth-store"

export function LandingPage() {
  const isAuthenticated = useIsAuthenticated()

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between px-6 py-4">
        <span className="font-serif text-lg font-medium">June</span>
        <Link to={isAuthenticated ? "/app/tables" : "/login"}>
          <Button variant="outline">{isAuthenticated ? "Go to App" : "Sign In"}</Button>
        </Link>
      </header>
      <main className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <h1 className="font-serif text-4xl font-medium tracking-tight">
          AI-powered document review
        </h1>
        <p className="mt-4 max-w-md text-muted-foreground">
          Upload PDFs, define your questions, and let AI extract answers with reasoning and
          exact source citations.
        </p>
        <Link to={isAuthenticated ? "/app/tables" : "/login"} className="mt-8">
          <Button size="lg">
            {isAuthenticated ? "Open Workspace" : "Get Started"}
          </Button>
        </Link>
      </main>
    </div>
  )
}
