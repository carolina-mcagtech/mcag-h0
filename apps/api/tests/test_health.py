# tests/test_health.py
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "local"}


@pytest.mark.asyncio
async def test_health_cors_headers() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_health_always_200_when_db_down() -> None:
    with patch("app.main.get_engine") as mock_get_engine:
        mock_get_engine.return_value.connect.side_effect = Exception("connection refused")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_ready_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok", "environment": "local"}


@pytest.mark.asyncio
async def test_health_ready_db_down() -> None:
    with patch("app.main.get_engine") as mock_get_engine:
        mock_get_engine.return_value.connect.side_effect = Exception("connection refused")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "db": "unavailable", "environment": "local"}
