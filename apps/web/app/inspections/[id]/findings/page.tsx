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
import { FindingsEntry } from "@/components/findings/findings-entry"

interface ApiInspection {
  id: string
  property_address: string
  status: InspectionStatus
}

export default async function FindingsPage({
  params,
}: {
  params: { id: string }
}) {
  const token = cookies().get("id_token")?.value
  if (!token) redirect("/login")

  const { id } = params

  const [inspectionResult, findingsResult] = await Promise.all([
    apiFetch<ApiInspection>(`/inspections/${id}`),
    apiFetch<FindingResponse[]>(`/inspections/${id}/findings?grouped=false`),
  ])

  if (!inspectionResult.ok || !findingsResult.ok) redirect("/login")

  const inspection: InspectionMeta = {
    id: inspectionResult.data.id,
    address: inspectionResult.data.property_address,
    status: inspectionResult.data.status,
  }

  const initialFindings = findingsResult.data.map(mapFindingResponse)

  return <FindingsEntry initialFindings={initialFindings} inspection={inspection} />
}
