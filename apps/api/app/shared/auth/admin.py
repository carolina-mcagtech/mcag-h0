# app/shared/auth/admin.py
import secrets

from fastapi import Header, HTTPException

from app.config import settings


async def admin_key_required(x_admin_api_key: str = Header(default="")) -> None:
    """Reject requests that don't present the correct ADMIN_API_KEY header.

    Uses secrets.compare_digest to prevent timing attacks.
    Raises HTTP 403 when the key is missing, wrong, or unconfigured in settings.
    """
    configured = settings.admin_api_key
    if not configured or not secrets.compare_digest(x_admin_api_key, configured):
        raise HTTPException(status_code=403, detail="invalid or missing admin key")
