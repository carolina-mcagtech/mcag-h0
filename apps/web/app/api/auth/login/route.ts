// apps/web/app/api/auth/login/route.ts
import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
  NotAuthorizedException,
  UserNotFoundException,
} from "@aws-sdk/client-cognito-identity-provider"
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

const cognito = new CognitoIdentityProviderClient({
  region: process.env.COGNITO_REGION ?? "us-east-1",
})

export async function POST(request: Request) {
  let email: string
  let password: string

  try {
    const body = (await request.json()) as { email?: unknown; password?: unknown }
    if (typeof body.email !== "string" || typeof body.password !== "string") {
      return NextResponse.json({ error: "email and password are required" }, { status: 400 })
    }
    email = body.email
    password = body.password
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 })
  }

  try {
    const command = new InitiateAuthCommand({
      AuthFlow: "USER_PASSWORD_AUTH",
      ClientId: process.env.COGNITO_CLIENT_ID!,
      AuthParameters: {
        USERNAME: email,
        PASSWORD: password,
      },
    })

    const response = await cognito.send(command)
    const idToken = response.AuthenticationResult?.IdToken
    const expiresIn = response.AuthenticationResult?.ExpiresIn ?? 3600

    if (!idToken) {
      return NextResponse.json({ error: "Authentication failed" }, { status: 401 })
    }

    cookies().set("id_token", idToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: expiresIn,
      path: "/",
    })

    return NextResponse.json({ ok: true })
  } catch (err) {
    if (err instanceof NotAuthorizedException || err instanceof UserNotFoundException) {
      return NextResponse.json({ error: "Invalid email or password" }, { status: 401 })
    }
    console.error("[auth/login]", err)
    return NextResponse.json({ error: "Authentication service unavailable" }, { status: 503 })
  }
}
