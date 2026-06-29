// apps/web/app/api/auth/logout/route.ts
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

export async function POST() {
  cookies().set("id_token", "", { maxAge: 0, path: "/" })
  cookies().set("refresh_token", "", { maxAge: 0, path: "/" })
  return NextResponse.json({ ok: true })
}
