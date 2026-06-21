// apps/web/app/login/login-form.tsx
"use client"

import { useState } from "react"
import { ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export function LoginForm() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setPending(true)

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })

      if (res.ok) {
        await new Promise(resolve => setTimeout(resolve, 100))
        window.location.href = "/inspections"
      } else {
        const body = (await res.json()) as { error?: string }
        setError(body.error ?? "Sign in failed. Please try again.")
      }
    } catch {
      setError("Network error. Check your connection and try again.")
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="w-full max-w-sm px-4">
      {/* Brand */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
          <ShieldCheck className="size-6" aria-hidden="true" />
        </div>
        <div className="text-center">
          <h1 className="text-xl font-semibold tracking-tight text-foreground">
            Inspect<span className="text-primary">IQ</span>
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Florida Home Inspection Reports
          </p>
        </div>
      </div>

      {/* Card */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="mb-5 text-base font-semibold text-foreground">Sign in to your account</h2>

        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="email"
              className="text-sm font-medium text-foreground"
            >
              Email
            </label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className={cn(error && "border-destructive")}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="password"
              className="text-sm font-medium text-foreground"
            >
              Password
            </label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className={cn(error && "border-destructive")}
            />
          </div>

          {error && (
            <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <Button type="submit" className="mt-1 w-full" disabled={pending}>
            {pending ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  )
}
