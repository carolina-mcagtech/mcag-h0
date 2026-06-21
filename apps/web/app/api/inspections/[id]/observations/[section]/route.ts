import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string; section: string } },
) {
  const token = cookies().get("id_token")?.value
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const res = await fetch(
    `${API_BASE}/inspections/${params.id}/observations/${params.section}`,
    { headers: { Authorization: `Bearer ${token}` } },
  )

  const data = await res.json().catch(() => null)
  return NextResponse.json(data, { status: res.status })
}
