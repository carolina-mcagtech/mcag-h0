// apps/web/lib/api.ts  (server-only — imported only from Server Components / Route Handlers)
import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
} from "@aws-sdk/client-cognito-identity-provider"
import { cookies } from "next/headers"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type ApiFetchResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; data: null }

async function refreshIdToken(): Promise<string | null> {
  try {
    const refreshToken = cookies().get("refresh_token")?.value
    if (!refreshToken) return null

    const cognito = new CognitoIdentityProviderClient({
      region: process.env.COGNITO_REGION ?? "us-east-1",
    })
    const response = await cognito.send(
      new InitiateAuthCommand({
        AuthFlow: "REFRESH_TOKEN_AUTH",
        ClientId: process.env.COGNITO_CLIENT_ID!,
        AuthParameters: { REFRESH_TOKEN: refreshToken },
      }),
    )

    const newIdToken = response.AuthenticationResult?.IdToken
    if (!newIdToken) return null

    const expiresIn = response.AuthenticationResult?.ExpiresIn ?? 3600
    cookies().set("id_token", newIdToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: expiresIn,
      path: "/",
    })

    return newIdToken
  } catch {
    return null
  }
}

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

  if (!res.ok && res.status === 401) {
    const newToken = await refreshIdToken()
    if (newToken) {
      const retryRes = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: { ...headers, Authorization: `Bearer ${newToken}` },
        cache: "no-store",
      })
      if (!retryRes.ok) return { ok: false, status: retryRes.status, data: null }
      const retryData = (await retryRes.json()) as T
      return { ok: true, status: retryRes.status, data: retryData }
    }
  }

  if (!res.ok) return { ok: false, status: res.status, data: null }
  const data = (await res.json()) as T
  return { ok: true, status: res.status, data }
}
