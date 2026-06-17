// apps/web/lib/api.ts  (server-only — imported only from Server Components / Route Handlers)
import { cookies } from "next/headers"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type ApiFetchResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; data: null }

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<ApiFetchResult<T>> {
  const token = cookies().get("id_token")?.value
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> | undefined),
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  })

  if (!res.ok) return { ok: false, status: res.status, data: null }
  const data = (await res.json()) as T
  return { ok: true, status: res.status, data }
}
