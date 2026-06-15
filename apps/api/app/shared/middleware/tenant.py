# app/shared/middleware/tenant.py
import asyncio
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# Holds the current request's tenant UUID as a string.
# Default is '' so any session without a tenant context
# gets SET LOCAL app.current_tenant_id = '' → RLS returns zero rows.
current_tenant_id: ContextVar[str] = ContextVar("current_tenant_id", default="")


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_str = await _extract_from_jwt(request)
        token = current_tenant_id.set(tenant_str)
        request.state.tenant_id = tenant_str
        try:
            return await call_next(request)
        finally:
            current_tenant_id.reset(token)


async def _extract_from_jwt(request: Request) -> str:
    """Extract custom:tenant_id from Bearer JWT. Returns '' on any failure.

    Dev: JWT is decoded without signature verification (any token works).
    Prod: RS256 + Cognito JWKS verification required.
    Fail-closed: any error → '' → RLS returns zero rows.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return ""
    try:
        from app.shared.auth.cognito import verify_token
        claims = await asyncio.to_thread(verify_token, auth[7:])
        raw = claims.get("custom:tenant_id", "")
        return str(uuid.UUID(str(raw))) if raw else ""
    except Exception:
        return ""
