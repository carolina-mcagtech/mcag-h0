// apps/web/app/api/inspections/[id]/findings/[fid]/photos/route.ts
import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

export const dynamic = "force-dynamic"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function POST(
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
    `${API_BASE}/inspections/${params.id}/findings/${params.fid}/photos/upload-url`,
    {
      method: "POST",
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
