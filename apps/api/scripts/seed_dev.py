#!/usr/bin/env python3
# scripts/seed_dev.py
"""
Development E2E seed — ADR-018 stack verification.

Creates 2 tenants + 2 Cognito inspector users, seeds data under tenant A,
then verifies tenant B cannot see tenant A's inspections (RLS isolation).

Required env vars:
  ADMIN_API_KEY                  — matches ADMIN_API_KEY configured on the API server
  COGNITO_USER_POOL_ID           — e.g. us-east-1_XXXXXXXXX
  COGNITO_DEV_SCRIPTS_CLIENT_ID  — dev-only app client (must allow ADMIN_USER_PASSWORD_AUTH)

Optional env vars:
  ALB_URL                — default: http://mcag-dev-alb-488893763.us-east-1.elb.amazonaws.com
  AWS_REGION             — default: us-east-1
  COGNITO_CLIENT_SECRET  — only if the app client has a secret configured

Usage:
  python seed_dev.py                          # full seed + RLS check
  python seed_dev.py --cleanup user-a user-b  # remove Cognito users
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import sys
import uuid
from datetime import datetime, timedelta

import boto3
import httpx


# ── Config ────────────────────────────────────────────────────────────────────

ALB_URL = os.environ.get(
    "ALB_URL",
    "http://mcag-dev-alb-488893763.us-east-1.elb.amazonaws.com",
).rstrip("/")

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
# Dev-only client — supports ADMIN_USER_PASSWORD_AUTH
# NEVER use COGNITO_APP_CLIENT_ID (production client) here
# Per ADR-019
COGNITO_DEV_SCRIPTS_CLIENT_ID = os.environ.get("COGNITO_DEV_SCRIPTS_CLIENT_ID", "")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

SEED_PASSWORD = "SeedDev2024!Mcag"

_cognito_client = None


def _cognito() -> "boto3.client":
    global _cognito_client
    if _cognito_client is None:
        _cognito_client = boto3.client("cognito-idp", region_name=AWS_REGION)
    return _cognito_client


# ── Output helpers ────────────────────────────────────────────────────────────

def ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def fail(msg: str) -> None:
    print(f"  ❌  {msg}", file=sys.stderr)


def section(title: str) -> None:
    print(f"\n{'─' * 62}")
    print(f"  {title}")
    print(f"{'─' * 62}")


# ── Validation ────────────────────────────────────────────────────────────────

def _require_env() -> None:
    missing = [
        k for k in ("ADMIN_API_KEY", "COGNITO_USER_POOL_ID", "COGNITO_DEV_SCRIPTS_CLIENT_ID")
        if not os.environ.get(k)
    ]
    if missing:
        fail(f"Missing required env vars: {', '.join(missing)}")
        sys.exit(1)


# ── Cognito helpers ───────────────────────────────────────────────────────────

def _secret_hash(username: str) -> str | None:
    """Compute SECRET_HASH if the app client has a client secret."""
    if not COGNITO_CLIENT_SECRET:
        return None
    msg = (username + COGNITO_DEV_SCRIPTS_CLIENT_ID).encode()
    digest = hmac.new(
        COGNITO_CLIENT_SECRET.encode(), msg, hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode()


def _create_cognito_user(username: str, email: str, tenant_id: str) -> str:
    """Create inspector user in Cognito, set permanent password, return IdToken."""
    c = _cognito()

    c.admin_create_user(
        UserPoolId=COGNITO_USER_POOL_ID,
        Username=username,
        TemporaryPassword=f"Tmp!{uuid.uuid4().hex[:8]}A",
        UserAttributes=[
            {"Name": "email", "Value": email},
            {"Name": "email_verified", "Value": "true"},
            {"Name": "custom:tenant_id", "Value": tenant_id},
        ],
        MessageAction="SUPPRESS",
    )

    c.admin_set_user_password(
        UserPoolId=COGNITO_USER_POOL_ID,
        Username=username,
        Password=SEED_PASSWORD,
        Permanent=True,
    )

    auth_params: dict = {"USERNAME": username, "PASSWORD": SEED_PASSWORD}
    secret_hash = _secret_hash(username)
    if secret_hash:
        auth_params["SECRET_HASH"] = secret_hash

    resp = c.admin_initiate_auth(
        UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_DEV_SCRIPTS_CLIENT_ID,
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters=auth_params,
    )
    return resp["AuthenticationResult"]["IdToken"]


def _jwt_sub(token: str) -> str:
    """Decode the 'sub' claim from a JWT without verifying its signature (dev seed only)."""
    payload_b64 = token.split(".")[1]
    padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))
    return payload["sub"]


def _delete_cognito_user(username: str) -> None:
    try:
        _cognito().admin_delete_user(UserPoolId=COGNITO_USER_POOL_ID, Username=username)
    except Exception:
        pass


# ── API helpers ───────────────────────────────────────────────────────────────

def _admin_headers() -> dict:
    return {"X-Admin-Api-Key": ADMIN_API_KEY}


def _bearer_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def post_tenant(client: httpx.AsyncClient, name: str, subdomain: str) -> dict:
    r = await client.post(
        f"{ALB_URL}/tenants",
        json={"name": name, "subdomain": subdomain},
        headers=_admin_headers(),
    )
    r.raise_for_status()
    return r.json()


async def post_inspector_profile(client: httpx.AsyncClient, token: str) -> dict:
    r = await client.post(
        f"{ALB_URL}/inspector-profiles",
        json={
            "full_name": "Seed Inspector",
            "email": "seed-inspector@mcagtech-dev.internal",
            "license_number": "HI00000",
            "license_expiry_date": "2030-01-01",
        },
        headers=_bearer_headers(token),
    )
    r.raise_for_status()
    return r.json()


async def post_property(client: httpx.AsyncClient, token: str) -> dict:
    r = await client.post(
        f"{ALB_URL}/properties",
        json={"street": "123 Seed St", "city": "Miami", "zip_code": "33101"},
        headers=_bearer_headers(token),
    )
    r.raise_for_status()
    return r.json()


async def post_inspection(
    client: httpx.AsyncClient, token: str, inspector_id: str
) -> dict:
    scheduled_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    r = await client.post(
        f"{ALB_URL}/inspections",
        json={
            "inspector_id": inspector_id,
            "scheduled_at": scheduled_at,
            "property_address": "123 Seed St, Miami, FL 33101",
            "inspection_types": ["FULL_INSPECTION"],
            "total_fee": "350.00",
        },
        headers=_bearer_headers(token),
    )
    r.raise_for_status()
    return r.json()


async def get_inspections(client: httpx.AsyncClient, token: str) -> list:
    r = await client.get(
        f"{ALB_URL}/inspections",
        headers=_bearer_headers(token),
    )
    r.raise_for_status()
    return r.json()


# ── Main flow ─────────────────────────────────────────────────────────────────

async def main() -> None:
    _require_env()

    suffix = uuid.uuid4().hex[:6]
    sub_a, sub_b = f"seed-alpha-{suffix}", f"seed-beta-{suffix}"
    user_a = f"seed-insp-a-{suffix}@mcagtech-dev.internal"
    user_b = f"seed-insp-b-{suffix}@mcagtech-dev.internal"

    print(f"\n  ALB     : {ALB_URL}")
    print(f"  Pool    : {COGNITO_USER_POOL_ID}")

    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── Step 1: tenants ────────────────────────────────────────────────
        section("1 — Create tenants via POST /tenants")

        try:
            tenant_a = await post_tenant(client, "Seed Alpha Inspections", sub_a)
            ok(f"Tenant A  id={tenant_a['id']}  subdomain={sub_a}")
        except Exception as exc:
            fail(f"Tenant A: {exc}")
            sys.exit(1)

        try:
            tenant_b = await post_tenant(client, "Seed Beta Inspections", sub_b)
            ok(f"Tenant B  id={tenant_b['id']}  subdomain={sub_b}")
        except Exception as exc:
            fail(f"Tenant B: {exc}")
            sys.exit(1)

        # ── Step 2: Cognito users ──────────────────────────────────────────
        section("2 — Create inspector users in Cognito")

        try:
            token_a = await asyncio.to_thread(
                _create_cognito_user,
                user_a, user_a, tenant_a["id"],
            )
            ok(f"Inspector A  username={user_a}")
        except Exception as exc:
            fail(f"Cognito user A: {exc}")
            sys.exit(1)

        try:
            token_b = await asyncio.to_thread(
                _create_cognito_user,
                user_b, user_b, tenant_b["id"],
            )
            ok(f"Inspector B  username={user_b}")
        except Exception as exc:
            fail(f"Cognito user B: {exc}")
            sys.exit(1)

        # ── Step 2.5: inspector profiles ───────────────────────────────────
        section("2.5 — Create inspector profile for tenant A")

        try:
            profile_a = await post_inspector_profile(client, token_a)
            ok(f"InspectorProfile  id={profile_a['id']}")
        except Exception as exc:
            fail(f"POST /inspector-profiles: {exc}")
            sys.exit(1)

        # ── Step 3: seed data under tenant A ──────────────────────────────
        section("3 — Seed property + inspection for tenant A")

        try:
            prop_a = await post_property(client, token_a)
            ok(f"Property  id={prop_a['id']}")
        except Exception as exc:
            fail(f"POST /properties: {exc}")
            sys.exit(1)

        try:
            inspector_id_a = _jwt_sub(token_a)
            insp_a = await post_inspection(client, token_a, inspector_id_a)
            ok(f"Inspection  id={insp_a['id']}")
        except Exception as exc:
            fail(f"POST /inspections: {exc}")
            sys.exit(1)

        # ── Step 4: RLS isolation check ────────────────────────────────────
        section("4 — RLS isolation: tenant A vs tenant B")

        errors = 0

        # Tenant A must see its own inspection.
        try:
            records_a = await get_inspections(client, token_a)
            if any(r["id"] == insp_a["id"] for r in records_a):
                ok(f"Tenant A sees its own inspection  ({len(records_a)} record(s))")
            else:
                fail("Tenant A cannot see its own inspection — RLS misconfigured")
                errors += 1
        except Exception as exc:
            fail(f"GET /inspections as tenant A: {exc}")
            errors += 1

        # Tenant B must see zero records (tenant A's inspection is invisible).
        try:
            records_b = await get_inspections(client, token_b)
            if not records_b:
                ok("Tenant B sees 0 inspections — RLS isolation confirmed")
            else:
                leaked = [r["id"] for r in records_b]
                fail(
                    f"RLS BREACH — tenant B can see {len(leaked)} record(s):\n"
                    + "\n".join(f"    {id_}" for id_ in leaked)
                )
                errors += 1
        except Exception as exc:
            fail(f"GET /inspections as tenant B: {exc}")
            errors += 1

        # ── Summary ────────────────────────────────────────────────────────
        print(f"\n{'═' * 62}")
        if errors == 0:
            print("  ✅  All checks passed")
        else:
            print(f"  ❌  {errors} check(s) failed — see output above")
        print(f"{'═' * 62}")

        print(f"""
  Resources created (not auto-cleaned):
    Tenant A    {tenant_a['id']}
    Tenant B    {tenant_b['id']}
    Cognito     {user_a}
                {user_b}

  Delete Cognito users:
    python seed_dev.py --cleanup {user_a} {user_b}

  Delete tenants (psql):
    DELETE FROM tenants WHERE subdomain LIKE 'seed-%';
""")
        if errors:
            sys.exit(1)


async def cleanup(usernames: list[str]) -> None:
    _require_env()
    print(f"\nCleaning up {len(usernames)} Cognito user(s)…")
    for username in usernames:
        try:
            await asyncio.to_thread(_delete_cognito_user, username)
            ok(f"Deleted  {username}")
        except Exception as exc:
            fail(f"Delete {username}: {exc}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        asyncio.run(cleanup(sys.argv[2:]))
    else:
        asyncio.run(main())
