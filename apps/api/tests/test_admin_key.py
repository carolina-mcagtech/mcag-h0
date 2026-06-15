# tests/test_admin_key.py
#
# Unit tests for the admin_key_required dependency.
# These call the dependency function directly — no HTTP round-trip needed.
import pytest
from fastapi import HTTPException
from unittest.mock import patch

from app.shared.auth.admin import admin_key_required


async def test_valid_key_passes():
    with patch("app.shared.auth.admin.settings") as mock_cfg:
        mock_cfg.admin_api_key = "secret-key"
        await admin_key_required(x_admin_api_key="secret-key")  # must not raise


async def test_wrong_key_raises_403():
    with patch("app.shared.auth.admin.settings") as mock_cfg:
        mock_cfg.admin_api_key = "secret-key"
        with pytest.raises(HTTPException) as exc:
            await admin_key_required(x_admin_api_key="wrong-key")
        assert exc.value.status_code == 403


async def test_empty_key_raises_403():
    with patch("app.shared.auth.admin.settings") as mock_cfg:
        mock_cfg.admin_api_key = "secret-key"
        with pytest.raises(HTTPException) as exc:
            await admin_key_required(x_admin_api_key="")
        assert exc.value.status_code == 403


async def test_unconfigured_key_always_raises_403():
    """When ADMIN_API_KEY is not set, all requests must be rejected."""
    with patch("app.shared.auth.admin.settings") as mock_cfg:
        mock_cfg.admin_api_key = ""
        with pytest.raises(HTTPException) as exc:
            await admin_key_required(x_admin_api_key="anything")
        assert exc.value.status_code == 403
