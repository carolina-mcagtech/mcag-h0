# app/shared/auth/cognito.py
import asyncio
import base64
import json
import uuid
from functools import lru_cache

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, Request

from app.config import settings


@lru_cache(maxsize=1)
def _fetch_jwks_sync() -> dict:
    """Fetch Cognito JWKS. Cached in-process; clear with _fetch_jwks_sync.cache_clear()."""
    resp = httpx.get(settings.jwks_url, timeout=5.0)
    resp.raise_for_status()
    return resp.json()


def _get_public_key(jwks: dict, kid: str):
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return RSAAlgorithm.from_jwk(key)
    raise HTTPException(status_code=401, detail="Unknown signing key")


def _decode_unverified(token: str) -> dict:
    """Decode JWT payload without signature verification (dev mode only)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Not a valid JWT")
        padding = -len(parts[1]) % 4
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "=" * padding)
        return json.loads(payload_bytes)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token format") from exc


def verify_token(token: str) -> dict:
    """Verify a JWT. Dev: decode only (no sig check). Prod: RS256 + Cognito JWKS."""
    if settings.app_env != "production":
        return _decode_unverified(token)

    try:
        header = jwt.get_unverified_header(token)
        jwks = _fetch_jwks_sync()
        public_key = _get_public_key(jwks, header["kid"])
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.cognito_client_id,
        )
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def extract_tenant_id(claims: dict) -> str:
    """Extract and validate custom:tenant_id UUID from JWT claims."""
    raw = claims.get("custom:tenant_id", "")
    try:
        return str(uuid.UUID(str(raw)))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=401, detail="Missing or invalid tenant_id claim"
        )


async def get_current_tenant_id(request: Request) -> str:
    """FastAPI dependency: resolve tenant_id from Bearer JWT. Raises HTTP 401 on failure.

    Both dev and prod require a Bearer token. Dev skips signature verification;
    prod validates RS256 against Cognito JWKS.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    claims = await asyncio.to_thread(verify_token, auth_header[7:])
    return extract_tenant_id(claims)


async def get_current_cognito_sub(request: Request) -> uuid.UUID:
    """FastAPI dependency: resolve the Cognito 'sub' claim from Bearer JWT.

    Raises HTTP 401 on a missing/invalid token or a missing/malformed sub claim.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    claims = await asyncio.to_thread(verify_token, auth_header[7:])
    try:
        return uuid.UUID(str(claims["sub"]))
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Missing or invalid sub claim")
