// apps/web/app/settings/page.tsx
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"
import { apiFetch } from "@/lib/api"
import { type TenantResponse } from "@/lib/tenant"
import { DashboardHeader } from "@/components/inspections/dashboard-header"
import { SettingsForm } from "@/components/settings/settings-form"

export default async function SettingsPage() {
  const token = cookies().get("id_token")?.value
  if (!token) redirect("/login")

  const result = await apiFetch<TenantResponse>("/tenants/me")
  if (!result.ok) redirect("/login")

  const tenant = result.data

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader tenant={tenant} />
      <main className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <Link
            href="/inspections"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="size-4" />
            Back to Inspections
          </Link>
        </div>
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Settings
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Customize your brand as it appears on reports and the portal.
          </p>
        </div>
        <SettingsForm initialTheme={tenant.theme_config} />
      </main>
    </div>
  )
}
