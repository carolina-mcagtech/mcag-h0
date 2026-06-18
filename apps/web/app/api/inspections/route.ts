// apps/web/app/api/inspections/route.ts
import { cookies } from "next/headers"
import { NextRequest, NextResponse } from "next/server"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

function decodeJwtPayload(token: string): Record<string, unknown> {
  const segment = token.split(".")[1]
  if (!segment) throw new Error("Malformed token")
  const padded = segment.replace(/-/g, "+").replace(/_/g, "/")
  const json = Buffer.from(padded, "base64").toString("utf8")
  return JSON.parse(json)
}

export async function POST(req: NextRequest) {
  const token = cookies().get("id_token")?.value
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 })

  let claims: Record<string, unknown>
  try {
    claims = decodeJwtPayload(token)
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const inspectorId = claims["sub"] as string | undefined
  if (!inspectorId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  let body: {
    propertyAddress: string
    scheduledAt: string
    inspectionTypes: string[]
    totalFee: number
    paymentTiming: string
  }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 })
  }

  const apiBody = {
    inspector_id: inspectorId,
    property_address: body.propertyAddress,
    scheduled_at: body.scheduledAt,
    inspection_types: body.inspectionTypes,
    total_fee: String(body.totalFee),
    payment_timing: body.paymentTiming,
  }

  const res = await fetch(`${API_BASE}/inspections`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(apiBody),
  })

  const data = await res.json().catch(() => null)
  return NextResponse.json(data, { status: res.status })
}
