// apps/web/app/login/page.tsx
import type { Metadata } from "next"
import { LoginForm } from "./login-form"

export const metadata: Metadata = {
  title: "Sign In — InspectIQ",
}

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background">
      <LoginForm />
    </main>
  )
}
