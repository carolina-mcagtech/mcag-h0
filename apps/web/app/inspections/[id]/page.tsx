// apps/web/app/inspections/[id]/page.tsx
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { apiFetch } from "@/lib/api"
import {
  type InspectionDetailData,
  type FindingsSummary,
  type InspectionStatus,
  type InspectionTypeValue,
  type PaymentTiming,
} from "@/lib/inspection-detail"
import { InspectionDetail } from "@/components/inspection-detail/inspection-detail"

// Raw shape returned by GET /inspections/{id}.
// total_fee is Decimal → Pydantic v2 serializes as string; Number() handles both.
interface ApiInspectionResponse {
  id: string
  tenant_id: string
  inspector_id: string | null
  status: InspectionStatus
  scheduled_at: string | null
  property_address: string
  inspection_types: InspectionTypeValue[]
  total_fee: string | number
  payment_timing: PaymentTiming | null
  full_report_number: string | null
  insurance_report_number: string | null
  year_built: number | null
  adj_sqft: number | null
  gate_code: string | null
  lockbox: string | null
  realtor_name: string | null
  realtor_cell: string | null
  owner_buyer_name: string | null
  owner_buyer_cell: string | null
  owner_buyer_email: string | null
  listing_agent_name: string | null
  listing_agent_cell: string | null
  additional_notes: string | null
  roof_permit_number: string | null
  roof_date: string | null
  roof_style: string | null
  roof_type: string | null
  water_heater_type: string | null
  water_heater_location: string | null
  water_heater_capacity: string | null
  electrical_brand: string | null
  electrical_amps: number | null
  electrical_location: string | null
  hvac_brand: string | null
  hvac_age: number | null
  hvac_model: string | null
  hvac_series: string | null
  wind_mit_doors_protected: boolean
  wind_mit_windows_protected: boolean
}

function mapInspection(api: ApiInspectionResponse): InspectionDetailData {
  return {
    id: api.id,
    property_address: api.property_address,
    status: api.status,
    inspector_id: api.inspector_id,
    scheduled_at: api.scheduled_at,
    inspection_types: api.inspection_types,
    total_fee: api.total_fee != null ? Number(api.total_fee) : null,
    payment_timing: api.payment_timing,
    full_report_number: api.full_report_number,
    insurance_report_number: api.insurance_report_number,
    year_built: api.year_built,
    adj_sqft: api.adj_sqft,
    gate_code: api.gate_code,
    lockbox: api.lockbox,
    realtor_name: api.realtor_name,
    realtor_cell: api.realtor_cell,
    owner_buyer_name: api.owner_buyer_name,
    owner_buyer_cell: api.owner_buyer_cell,
    owner_buyer_email: api.owner_buyer_email,
    listing_agent_name: api.listing_agent_name,
    listing_agent_cell: api.listing_agent_cell,
    additional_notes: api.additional_notes,
    roof_permit_number: api.roof_permit_number,
    roof_date: api.roof_date,
    roof_style: api.roof_style,
    roof_type: api.roof_type,
    water_heater_type: api.water_heater_type,
    water_heater_location: api.water_heater_location,
    water_heater_capacity: api.water_heater_capacity,
    electrical_brand: api.electrical_brand,
    electrical_amps: api.electrical_amps,
    electrical_location: api.electrical_location,
    hvac_brand: api.hvac_brand,
    hvac_age: api.hvac_age,
    hvac_model: api.hvac_model,
    hvac_series: api.hvac_series,
    wind_mit_doors_protected: api.wind_mit_doors_protected,
    wind_mit_windows_protected: api.wind_mit_windows_protected,
  }
}

export default async function InspectionDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const token = cookies().get("id_token")?.value
  if (!token) redirect("/login")

  const { id } = params

  const [inspectionResult, summaryResult] = await Promise.all([
    apiFetch<ApiInspectionResponse>(`/inspections/${id}`),
    apiFetch<FindingsSummary>(`/inspections/${id}/findings/summary`),
  ])

  if (inspectionResult.status === 401) redirect("/login")

  if (!inspectionResult.ok) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-foreground">
            Inspection not found
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            This inspection doesn&apos;t exist or you don&apos;t have access to it.
          </p>
        </div>
      </div>
    )
  }

  const inspection = mapInspection(inspectionResult.data)
  // Summary is soft-fail: empty {} renders "No findings recorded yet" in the widget.
  const findings: FindingsSummary = summaryResult.ok ? summaryResult.data : {}

  return (
    <div className="min-h-screen bg-background">
      <InspectionDetail inspection={inspection} findings={findings} />
    </div>
  )
}
