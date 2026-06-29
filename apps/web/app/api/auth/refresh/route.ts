// apps/web/app/api/auth/refresh/route.ts
import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
} from "@aws-sdk/client-cognito-identity-provider"
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

const cognito = new CognitoIdentityProviderClient({
  region: process.env.COGNITO_REGION ?? "us-east-1",
})

export async function POST() {
  const refreshToken = cookies().get("refresh_token")?.value
  if (!refreshToken) {
    return NextResponse.json({ error: "No refresh token" }, { status: 401 })
  }

  try {
    const response = await cognito.send(
      new InitiateAuthCommand({
        AuthFlow: "REFRESH_TOKEN_AUTH",
        ClientId: process.env.COGNITO_CLIENT_ID!,
        AuthParameters: { REFRESH_TOKEN: refreshToken },
      }),
    )

    const newIdToken = response.AuthenticationResult?.IdToken
    if (!newIdToken) {
      return NextResponse.json({ error: "Refresh failed" }, { status: 401 })
    }

    const expiresIn = response.AuthenticationResult?.ExpiresIn ?? 3600
    cookies().set("id_token", newIdToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: expiresIn,
      path: "/",
    })

    return NextResponse.json({ ok: true })
  } catch {
    return NextResponse.json({ error: "Refresh token expired" }, { status: 401 })
  }
}
