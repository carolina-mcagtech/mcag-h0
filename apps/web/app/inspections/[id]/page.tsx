// apps/web/app/inspections/[id]/page.tsx
import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { InspectionDetail } from "@/components/inspection-detail/inspection-detail"
import { MOCK_INSPECTION, MOCK_FINDINGS_SUMMARY } from "@/lib/inspection-detail"

export default async function InspectionDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const token = cookies().get("id_token")?.value
  if (!token) redirect("/login")

  // Use the actual URL id so "Edit Findings" navigates correctly.
  // Phase 3 will swap mock for a real GET /inspections/{id}.
  const inspection = { ...MOCK_INSPECTION, id: params.id }

  return (
    <div className="min-h-screen bg-background">
      <InspectionDetail
        inspection={inspection}
        findings={MOCK_FINDINGS_SUMMARY}
      />
    </div>
  )
}
