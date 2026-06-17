// apps/web/app/api/inspections/[id]/findings/[fid]/route.ts
import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string; fid: string } },
) {
  const token = cookies().get("id_token")?.value
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 })
  }

  const res = await fetch(
    `${API_BASE}/inspections/${params.id}/findings/${params.fid}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    },
  )

  const data = await res.json().catch(() => null)
  return NextResponse.json(data, { status: res.status })
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string; fid: string } },
) {
  const token = cookies().get("id_token")?.value
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const res = await fetch(
    `${API_BASE}/inspections/${params.id}/findings/${params.fid}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  )

  if (res.status === 204) return new NextResponse(null, { status: 204 })
  const data = await res.json().catch(() => null)
  return NextResponse.json(data, { status: res.status })
}
