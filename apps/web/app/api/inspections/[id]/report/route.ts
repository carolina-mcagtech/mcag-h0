// apps/web/app/api/inspections/[id]/report/route.ts
import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  const token = cookies().get("id_token")?.value
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const res = await fetch(`${API_BASE}/inspections/${params.id}/reports/pdf`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "PDF generation failed" }))
    return NextResponse.json(detail, { status: res.status })
  }

  const pdf = await res.arrayBuffer()
  const disposition = res.headers.get("Content-Disposition") ?? `attachment; filename="inspection-report-${params.id.slice(0, 8)}.pdf"`

  return new NextResponse(pdf, {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": disposition,
    },
  })
}
