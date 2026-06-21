// apps/web/app/inspections/[id]/findings/page.tsx
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { apiFetch } from "@/lib/api"
import {
  type FindingResponse,
  type InspectionMeta,
  mapFindingResponse,
} from "@/lib/findings"
import { type InspectionStatus } from "@/lib/inspections"
import { type SectionCatalog } from "@/lib/observations"
import { FindingsEntry } from "@/components/findings/findings-entry"

interface ApiInspection {
  id: string
  property_address: string
  status: InspectionStatus
  num_bedrooms: number
  num_bathrooms: number
}

export default async function FindingsPage({
  params,
}: {
  params: { id: string }
}) {
  const token = cookies().get("id_token")?.value
  if (!token) redirect("/login")

  const { id } = params

  const [inspectionResult, findingsResult, catalogResult] = await Promise.all([
    apiFetch<ApiInspection>(`/inspections/${id}`),
    apiFetch<FindingResponse[]>(`/inspections/${id}/findings?grouped=false`),
    apiFetch<Record<string, SectionCatalog>>(`/inspections/${id}/observations/catalog`),
  ])

  if (!inspectionResult.ok || !findingsResult.ok) redirect("/login")

  const inspection: InspectionMeta = {
    id: inspectionResult.data.id,
    address: inspectionResult.data.property_address,
    status: inspectionResult.data.status,
  }

  const initialFindings = findingsResult.data.map(mapFindingResponse)
  const catalogData = catalogResult.ok ? catalogResult.data : {}

  return (
    <FindingsEntry
      initialFindings={initialFindings}
      inspection={inspection}
      catalogData={catalogData}
      numBedrooms={inspectionResult.data.num_bedrooms ?? 0}
      numBathrooms={inspectionResult.data.num_bathrooms ?? 0}
    />
  )
}
