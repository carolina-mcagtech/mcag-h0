// apps/web/app/api/tenants/me/route.ts
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export async function GET() {
  const token = cookies().get("id_token")?.value
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  const res = await fetch(`${API_BASE}/tenants/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })

  const data = await res.json().catch(() => null)
  return NextResponse.json(data, { status: res.status })
}
