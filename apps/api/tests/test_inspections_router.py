# tests/test_inspections_router.py
"""Integration tests for the ADR-024 inspections router (Tarea 4).

Covers: basic CRUD under tenant context, the transition_status FSM
endpoint, the PUBLISHED write-lock (PUT -> 409), and RLS isolation
across tenants.
"""
import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.shared.db.session import get_session, get_session_factory


def _session_override(tenant_id: uuid.UUID):
    async def _override():
        async with get_session_factory()() as session:
            async with session.begin():
                # db_engine connects as superuser, which bypasses RLS entirely.
                # Switch to app_role so RLS policies are actually enforced,
                # matching tests/shared/test_rls_transaction_scope.py.
                await session.execute(text("SET LOCAL ROLE app_role"))
                await session.execute(
                    text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'")
                )
                session.info["tenant_id"] = tenant_id
                yield session
    return _override


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def two_tenant_inspectors(db_engine):
    """Two tenants, each with one inspector_profiles row."""
    t1_id, t2_id = uuid.uuid4(), uuid.uuid4()
    i1_id, i2_id = uuid.uuid4(), uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO tenants (id, name, subdomain)
                VALUES (:t1, 'Router Alpha', 'router-alpha'),
                       (:t2, 'Router Beta',  'router-beta')
            """),
            {"t1": t1_id, "t2": t2_id},
        )
        await conn.execute(
            text("""
                INSERT INTO inspector_profiles
                    (id, tenant_id, cognito_sub, full_name, email, license_number, license_expiry_date)
                VALUES
                    (:i1, :t1, :sub1, 'Alpha Inspector', 'inspector@router-alpha.com', 'HI20001', '2028-01-01'),
                    (:i2, :t2, :sub2, 'Beta Inspector',  'inspector@router-beta.com',  'HI20002', '2028-01-01')
            """),
            {
                "i1": i1_id, "t1": t1_id, "sub1": uuid.uuid4(),
                "i2": i2_id, "t2": t2_id, "sub2": uuid.uuid4(),
            },
        )

    yield t1_id, t2_id, i1_id, i2_id

    async with db_engine.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id = ANY(:ids)"),
            {"ids": [t1_id, t2_id]},
        )


class TenantClient:
    """Wraps an AsyncClient and pins app.dependency_overrides[get_session]
    to the given tenant for the duration of each request.

    Necessary because app.dependency_overrides is a single global dict —
    two clients for two tenants can't both hold a static override at once.
    """

    def __init__(self, client: AsyncClient, tenant_id: uuid.UUID) -> None:
        self._client = client
        self._tenant_id = tenant_id

    def _activate(self) -> None:
        app.dependency_overrides[get_session] = _session_override(self._tenant_id)

    async def get(self, *args, **kwargs):
        self._activate()
        return await self._client.get(*args, **kwargs)

    async def post(self, *args, **kwargs):
        self._activate()
        return await self._client.post(*args, **kwargs)

    async def put(self, *args, **kwargs):
        self._activate()
        return await self._client.put(*args, **kwargs)


@pytest_asyncio.fixture
async def http_client_a(db_engine, two_tenant_inspectors):
    t1_id, _, _, _ = two_tenant_inspectors
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield TenantClient(client, t1_id)
    app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture
async def http_client_b(db_engine, two_tenant_inspectors):
    _, t2_id, _, _ = two_tenant_inspectors
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield TenantClient(client, t2_id)
    app.dependency_overrides.pop(get_session, None)


def _create_payload(inspector_id: uuid.UUID, **overrides) -> dict:
    return {
        "inspector_id": str(inspector_id),
        "scheduled_at": "2026-08-15T09:00:00Z",
        "property_address": "10 Router Ln, Tampa, FL 33601",
        "inspection_types": ["FULL_INSPECTION"],
        "total_fee": "150.00",
        **overrides,
    }


# ── CRUD básico ───────────────────────────────────────────────────────────────


async def test_create_inspection(http_client_a, two_tenant_inspectors):
    t1_id, _, i1_id, _ = two_tenant_inspectors

    resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    assert resp.status_code == 201
    body = resp.json()
    assert body["tenant_id"] == str(t1_id)
    assert body["inspector_id"] == str(i1_id)
    assert body["status"] == "DRAFT"
    assert body["inspection_types"] == ["FULL_INSPECTION"]
    assert float(body["total_fee"]) == 150.00
    # Single-record response includes sensitive fields.
    assert "gate_code" in body
    assert "lockbox" in body


async def test_get_inspection(http_client_a, two_tenant_inspectors):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    resp = await http_client_a.get(f"/inspections/{iid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == iid


async def test_get_inspection_not_found(http_client_a):
    resp = await http_client_a.get(f"/inspections/{uuid.uuid4()}")
    assert resp.status_code == 404


async def test_list_inspections(http_client_a, two_tenant_inspectors):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    list_resp = await http_client_a.get("/inspections")
    assert list_resp.status_code == 200
    ids = [i["id"] for i in list_resp.json()]
    assert iid in ids

    # List response must NOT include sensitive codes.
    item = next(i for i in list_resp.json() if i["id"] == iid)
    assert "gate_code" not in item
    assert "lockbox" not in item


async def test_list_inspections_filtered_by_status(http_client_a, two_tenant_inspectors):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    draft_resp = await http_client_a.get("/inspections?status=DRAFT")
    assert iid in [i["id"] for i in draft_resp.json()]

    in_field_resp = await http_client_a.get("/inspections?status=IN_FIELD")
    assert iid not in [i["id"] for i in in_field_resp.json()]


async def test_update_inspection(http_client_a, two_tenant_inspectors):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    update_resp = await http_client_a.put(
        f"/inspections/{iid}",
        json={"gate_code": "9876", "total_fee": "200.00"},
    )
    assert update_resp.status_code == 200
    body = update_resp.json()
    assert body["gate_code"] == "9876"
    assert float(body["total_fee"]) == 200.00


async def test_update_inspection_not_found(http_client_a):
    resp = await http_client_a.put(
        f"/inspections/{uuid.uuid4()}", json={"gate_code": "0000"}
    )
    assert resp.status_code == 404


# ── FSM: transition_status ───────────────────────────────────────────────────


async def test_transition_valid(http_client_a, two_tenant_inspectors):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    resp = await http_client_a.post(f"/inspections/{iid}/transition", json={"status": "IN_FIELD"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_FIELD"


async def test_transition_invalid_skip_returns_422(http_client_a, two_tenant_inspectors):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    # DRAFT -> PUBLISHED skips IN_FIELD and PENDING_REVIEW.
    resp = await http_client_a.post(f"/inspections/{iid}/transition", json={"status": "PUBLISHED"})
    assert resp.status_code == 422


async def test_transition_not_found(http_client_a):
    resp = await http_client_a.post(
        f"/inspections/{uuid.uuid4()}/transition", json={"status": "IN_FIELD"}
    )
    assert resp.status_code == 404


# ── Write-lock: PUT on a PUBLISHED inspection ────────────────────────────────


async def test_put_on_published_inspection_returns_409(http_client_a, two_tenant_inspectors):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    for status in ("IN_FIELD", "PENDING_REVIEW", "PUBLISHED"):
        t_resp = await http_client_a.post(f"/inspections/{iid}/transition", json={"status": status})
        assert t_resp.status_code == 200

    resp = await http_client_a.put(f"/inspections/{iid}", json={"gate_code": "0000"})
    assert resp.status_code == 409


# ── RLS: tenant B cannot see tenant A's inspections ──────────────────────────


async def test_rls_tenant_b_cannot_see_tenant_a_inspections(
    http_client_a, http_client_b, two_tenant_inspectors
):
    _, _, i1_id, _ = two_tenant_inspectors

    create_resp = await http_client_a.post("/inspections", json=_create_payload(i1_id))
    iid = create_resp.json()["id"]

    # Tenant B cannot fetch tenant A's inspection directly.
    get_resp = await http_client_b.get(f"/inspections/{iid}")
    assert get_resp.status_code == 404

    # Tenant B's list does not include tenant A's inspection.
    list_resp = await http_client_b.get("/inspections")
    assert iid not in [i["id"] for i in list_resp.json()]
