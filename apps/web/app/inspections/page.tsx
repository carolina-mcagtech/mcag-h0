// apps/web/app/inspections/page.tsx
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { apiFetch } from "@/lib/api"
import { type Inspection, type InspectionStatus, type InspectionType } from "@/lib/inspections"
import { type TenantResponse } from "@/lib/tenant"
import { DashboardHeader } from "@/components/inspections/dashboard-header"
import { InspectionsDashboard } from "@/components/inspections/inspections-dashboard"

// Shape returned by GET /inspections (InspectionListResponse from the API).
// total_fee is Decimal → Pydantic v2 serializes as string; Number() handles both.
interface ApiInspection {
  id: string
  property_address: string
  status: InspectionStatus
  scheduled_at: string
  inspection_types: InspectionType[]
  total_fee: string | number
}

export default async function InspectionsPage() {
  const token = cookies().get("id_token")?.value
  if (!token) redirect("/login")

  const [inspectionsResult, tenantResult] = await Promise.all([
    apiFetch<ApiInspection[]>("/inspections"),
    apiFetch<TenantResponse>("/tenants/me"),
  ])

  if (!inspectionsResult.ok) redirect("/login")

  const inspections: Inspection[] = inspectionsResult.data.map((item) => ({
    id: item.id,
    property_address: item.property_address,
    status: item.status,
    scheduled_at: item.scheduled_at,
    inspection_types: item.inspection_types,
    total_fee: Number(item.total_fee),
  }))

  const tenant: TenantResponse | null = tenantResult.ok ? tenantResult.data : null

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader tenant={tenant} />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <InspectionsDashboard initialInspections={inspections} />
      </main>
    </div>
  )
}
