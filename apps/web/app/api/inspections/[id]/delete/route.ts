// apps/web/app/api/inspections/[id]/delete/route.ts
import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

export const dynamic = "force-dynamic"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function POST(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  const token = cookies().get("id_token")?.value
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const res = await fetch(`${API_BASE}/inspections/${params.id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  })

  if (res.status === 204) return new NextResponse(null, { status: 204 })
  const data = await res.json().catch(() => null)
  return NextResponse.json(data, { status: res.status })
}
